from __future__ import annotations
import json
import re
from functools import reduce
from operator import or_
from pathlib import Path
from typing import Annotated, Any, Callable, Generator, Type, TypeAlias, Literal

from bs4 import BeautifulSoup
from bs4.element import Tag
import msgspec
import httpx

Record: TypeAlias = dict[str, Any]


def table_to_records(tag: Tag) -> list[Record]:
    assert tag.name == "table"
    column_names = [
        t.text for t in tag.findChild("thead").findChild("tr").findChildren("th")
    ]
    records: list[Record] = []
    # rows
    for tr_tag in tag.findChild("tbody").findChildren("tr"):
        record: Record = {}
        # Columns
        for col_name, td_tag in zip(column_names, tr_tag.findChildren("td")):
            # Replace <br> and <li> tags with more convenient characters to make
            # information parsing easier
            for br_tag in td_tag.find_all("br"):
                br_tag.replace_with("\n")
            for li_tag in td_tag.find_all("li"):
                li_tag.replace_with(f"{li_tag.text}|")
            record[col_name] = td_tag.text
        records.append(record)
    return records


def find_in_siblings_until(
    tag: Tag,
    matcher: Callable[[Tag], bool],
    breaker: Callable[[Tag], bool] = lambda t: False,
) -> Generator[Tag]:
    next_tag = tag.find_next_sibling()
    while True:
        if breaker(next_tag):
            return
        if matcher(next_tag):
            yield next_tag
        next_tag = next_tag.find_next_sibling()


URL = "https://developer.veevavault.com/mdl/components/"
response = httpx.get(URL)
soup = BeautifulSoup(response.content, "html.parser")

COMPONENT_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+$")


class Component(msgspec.Struct):
    name: str
    table: list[Record]
    children: list[Component] = []

    def convert(self):
        # TODO: parse type checking, etc.
        return (
            self.name,
            {
                "attributes": {
                    r["Attribute"]: {
                        "type_data": r[""],
                        "description": r["Description"],
                    }
                    for r in self.table
                },
                "subcomponents": {
                    k: v for k, v in [c.convert() for c in self.children]
                },
            },
        )


components = []
for tag in soup.find_all("h1"):
    if COMPONENT_NAME_PATTERN.match(tag.text):
        component = {"name": tag.text}
        table_tag = next(
            find_in_siblings_until(
                tag, lambda t: t.name == "table", lambda t: t.name == "h3"
            )
        )
        component["table"] = table_to_records(table_tag)
        component["children"] = []
        for heading3_tag in find_in_siblings_until(
            tag, lambda t: t.name == "h3", lambda t: (t is None) or (t.name == "h1")
        ):
            subcomponent = {"name": heading3_tag.text}
            subtable_tag = next(
                find_in_siblings_until(
                    heading3_tag, lambda t: t.name == "table", lambda t: t.name == "h3"
                )
            )
            subcomponent["table"] = table_to_records(subtable_tag)
            component["children"].append(subcomponent)
        components.append(component)

# Validation
validated = msgspec.convert(components, type=list[Component])

dumpable = {k: v for k, v in [c.convert() for c in validated]}
(Path(__file__).parent.parent / "src" / "mdl" / "validation.json").write_text(
    json.dumps(dumpable, indent=4)
)


def comment_to_type(comment: str) -> Type:
    supported_types = {
        "String": str,
        "Boolean": bool,
        "Number": int,
        "LongString": str,
        "Enum": Literal,
    }
    type_match = re.search(r"Type : (.*)", comment)
    max_len_match = re.search(r"Maximum length : (.*)", comment)
    min_val_match = re.search(r"Minimum value : (.*)", comment)
    max_val_match = re.search(r"Maximum value : (.*)", comment)
    allowed_vals_match = re.search(r"Allowed values : (.*)", comment, re.MULTILINE)
    allow_multiple_vals_match = re.search(r"Allows multiple values", comment)
    type_ = supported_types.get(type_match.groups(0)[0])
    if type_ is None:
        return Any
    if allow_multiple_vals_match is not None:
        type_ = list[type_]
    elif allowed_vals_match is not None:
        type_ = Literal[*(s for s in allowed_vals_match.groups(0)[0].split("|") if s)]
    if any(m is not None for m in [max_len_match, min_val_match, max_val_match]):
        annotation_metadata = {
            k: int(m.groups(0)[0])
            for k, m in [
                ("max_length", max_len_match),
                ("ge", min_val_match),
                ("le", max_val_match),
            ]
            if m is not None
        }
        type_ = Annotated[type_, msgspec.Meta(**annotation_metadata)]
    return type_


for component in validated:
    attribute_structs = []
    for row in component.table:
        attribute_name = row[""]
        s = msgspec.defstruct(
            "Attribute",
            [
                ("name", Literal[row["Attribute"]]),
                ("value", comment_to_type(attribute_name)),
            ],
            tag=f"{component.name}-{attribute_name}",
        )
        attribute_structs.append(s)
    big_s = msgspec.defstruct(
        "Component",
        [
            ("component_type_name", Literal[component.name]),
            ("component_name", str),
            ("attributes", list[reduce(or_, attribute_structs)]),
        ],
        tag=component.name,
    )
