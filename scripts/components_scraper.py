from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any, Callable, Generator, TypeAlias

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
            # <br> tags get replaced with empty strings when calling `Tag.text`,
            # which we don't like
            for br_tag in td_tag.find_all("br"):
                br_tag.replace_with("\n")
            record[col_name] = td_tag.text
        records.append(record)
    return records


def advance_until(
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
                "table": {r["Attribute"]: "TODO" for r in self.table},
                "children": {k: v for k, v in [c.convert() for c in self.children]},
            },
        )


components = []
for tag in soup.find_all("h1"):
    if COMPONENT_NAME_PATTERN.match(tag.text):
        component = {"name": tag.text}
        table_tag = next(
            advance_until(tag, lambda t: t.name == "table", lambda t: t.name == "h3")
        )
        component["table"] = table_to_records(table_tag)
        component["children"] = []
        for heading3_tag in advance_until(
            tag, lambda t: t.name == "h3", lambda t: (t is None) or (t.name == "h1")
        ):
            subcomponent = {"name": heading3_tag.text}
            subtable_tag = next(
                advance_until(
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
