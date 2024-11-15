"""
Scrape metadata used for MDL validation from
https://developer.veevavault.com/mdl/components/.

Usage: `python3 scrape_components.py`
"""
# TODO: how worth it is it to make this into a standalone script as per `uv`'s
# documentation? See https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies

from __future__ import annotations
import json
import re
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Callable, Generator, NotRequired, TypeAlias, TypedDict

from bs4 import BeautifulSoup, NavigableString, Tag
import msgspec
import httpx

# Represents one row in a tabular data format
Record: TypeAlias = dict[str, Any]


URL = "https://developer.veevavault.com/mdl/components/"
COMPONENT_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+$")


def table_to_records(tag: Tag | NavigableString) -> list[Record]:
    """Convert a `bs4.element.Tag` into tabular data format."""

    # Pleasing mypy until new notice
    if not isinstance(tag, Tag):
        raise ValueError(
            f"Input variable 'tag' ought to be of type {repr(Tag)}. Got {repr(type(tag))}."
        )
    if (tn := tag.name) != "table":
        raise ValueError(
            f"Property 'name' of input variable 'tag' ought to be 'table'. Got {repr(tn)} from {tag}"
        )
    thead_child = tag.findChild("thead")
    if not isinstance(thead_child, Tag):
        raise ValueError(
            f"Input argument 'tag' ought to have at least one 'thead' child tag. Got parent {tag}, child {thead_child}."
        )
    tr_child = thead_child.findChild("tr")
    if not isinstance(tr_child, Tag):
        raise ValueError(
            f"Input argument 'tag' ought to have at least one 'tr' grandchild under 'thead. Got grandparent {tag}, child {thead_child}, grandkid {tr_child}."
        )
    tbody_child = tag.findChild("tbody")
    if not isinstance(tbody_child, Tag):
        raise ValueError(
            f"Input argument 'tag' ought to have at least one 'tbody' child tag. Got parent {tag}, child {tbody_child}."
        )
    # No longer pleasing mypy

    column_names = [t.text for t in tr_child.findChildren("th")]
    # Rows
    records: list[Record] = []
    for tr_tag in tbody_child.findChildren("tr"):
        record: Record = {}
        # Columns
        for col_name, td_tag in zip(column_names, tr_tag.findChildren("td")):
            # Replace <br> and <li> tags with more convenient characters to make
            # information parsing easier. Conversion is done in-place.
            for br_tag in td_tag.find_all("br"):
                br_tag.replace_with("\n")
            for li_tag in td_tag.find_all("li"):
                li_tag.replace_with(f"{li_tag.text}|")
            record[col_name] = td_tag.text
        records.append(record)
    return records


def find_in_siblings_until(
    tag: Tag | NavigableString,
    matcher: Callable[[Tag | NavigableString], bool],
    breaker: Callable[[Tag | NavigableString], bool] = lambda t: False,
) -> Generator[Tag | NavigableString]:
    """Iterate through siblings of `tag` (via its `find_next_sibling` method) and
    yield those flagged by `matcher`, until `breaker` signals an end.

    The input variable of `breaker` is optional cause `bs4.element.Tag.find_next_sibling`
    will return `None` when it cannot find any more siblings
    """
    next_tag = tag.find_next_sibling()
    while True:
        if (next_tag is None) or breaker(next_tag):
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


def cli() -> Path:
    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        "-o",
        "--out-path",
        help="Filepath in which to place scrapped component metadata.",
    )
    arguments = argument_parser.parse_args()
    out_path = (
        Path(__file__).parent.parent / "src" / "mdl" / "validation.json"
        if arguments.out_path is None
        else Path(arguments.out_path).resolve()
    )
    return out_path


class ComponentMetadataDict(TypedDict):
    name: str
    table: NotRequired[list[Record]]
    children: NotRequired[list["ComponentMetadataDict"]]


def main(out_path: Path):
    response = httpx.get(URL)
    soup = BeautifulSoup(response.content, "html.parser")

    components: list[ComponentMetadataDict] = []
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
        component: ComponentMetadataDict
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
            tag, lambda t: t.name == "h3", lambda t: t.name == "h1"
        ):
            subcomponent: ComponentMetadataDict
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
    out_path.write_text(json.dumps(dumpable, indent=4))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main(cli())
