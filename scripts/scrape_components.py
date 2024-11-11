"""
Scrape metadata used for MDL validation from
https://developer.veevavault.com/mdl/components/.

Usage: `python3 scrape_components.py`
"""

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


URL = "https://developer.veevavault.com/mdl/components/"
COMPONENT_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+$")


def table_to_records(tag: Tag) -> list[Record]:
    assert tag.name == "table"
    column_names = [
        t.text for t in tag.findChild("thead").findChild("tr").findChildren("th")
    ]
    records: list[Record] = []
    # Rows
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


class ComponentMetadata(msgspec.Struct):
    """A struct holding component metadata scrapped from
    https://developer.veevavault.com/mdl/components/.

    `name`: component name.
    `table`: is the parsed table with the attribute metadata.
    `children`: are the children components in the subsections of the parent
    component.
    """

    name: str
    table: list[Record]
    children: list[ComponentMetadata] = []

    def convert(self):
        """Massage the component metadata into a more dumpable and easily
        understandable format
        """
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


def main():
    response = httpx.get(URL)
    soup = BeautifulSoup(response.content, "html.parser")

    components = []
    # In summary:
    # - component names are contained in `h1` headers;
    # - the metadata of the attributes associated with a given component are
    # within a table under the `h1` header;
    # - subcomponents of the main component are contained `h3` headers, under
    # which one can also find tables with the metadata of the attributes
    # allowed under the subcomponent.

    # Algorithmically, we proceed as follows:
    # 1. Iterate over all `h1` headers the text of which start with one capital
    # letter.
    # 2. Find the first table after the `h1` header
    # 3. Iterate over all `h3` headers before the next `h1` header
    # 4. Gather the tables following the an `h3` header and before the next `h3`
    # header
    for tag in soup.find_all("h1"):
        # Step 1
        if not COMPONENT_NAME_PATTERN.match(tag.text):
            continue
        # Start gathering data to be put in a `ComponentMetadata` struct
        component = {"name": tag.text}
        # Step 2
        table_tag = next(
            find_in_siblings_until(
                tag, lambda t: t.name == "table", lambda t: t.name == "h3"
            )
        )
        component["table"] = table_to_records(table_tag)
        component["children"] = []
        # Step 3
        for heading3_tag in find_in_siblings_until(
            tag, lambda t: t.name == "h3", lambda t: (t is None) or (t.name == "h1")
        ):
            subcomponent = {"name": heading3_tag.text}
            # Step 4
            subtable_tag = next(
                find_in_siblings_until(
                    heading3_tag,
                    lambda t: t.name == "table",
                    lambda t: t.name == "h3",
                )
            )
            subcomponent["table"] = table_to_records(subtable_tag)
            component["children"].append(subcomponent)
        components.append(component)

    # Poor man's validation
    validated = msgspec.convert(components, type=list[ComponentMetadata])

    # Aaaaaand out it goes
    dumpable = {k: v for k, v in [c.convert() for c in validated]}
    out_path = Path(__file__).parent.parent / "src" / "mdl" / "validation.json"
    out_path.write_text(json.dumps(dumpable, indent=4))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
