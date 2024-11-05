import re
from functools import reduce
from operator import or_
from typing import Annotated, Any, Literal, Type, TypeAlias

import msgspec


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
    # Based on some examples I found on Veeva's GitHub attribute values seems to be nullable
    if type_ is None:
        return Any | None
    if allow_multiple_vals_match is not None:
        type_ = list[type_] | None
    elif allowed_vals_match is not None:
        type_ = (
            Literal[*(s for s in allowed_vals_match.groups(0)[0].split("|") if s)]
            | None
        )
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
        type_ = Annotated[type_, msgspec.Meta(**annotation_metadata)] | None
    return type_


AttributeName: TypeAlias = str


def make_attribute_structs(
    attributes: dict[AttributeName, dict[Literal["type_data", "description"], str]],
) -> Type:
    structs = []
    for attribute_name, d in attributes.items():
        # TODO: inject description in `Annotated` via `msgspec.Meta`'s `description` argument
        s = msgspec.defstruct(
            "Attribute",
            [
                ("name", Literal[attribute_name]),
                ("value", comment_to_type(d["type_data"])),
            ],
            tag=f"attribute_{attribute_name}",
        )
        structs.append(s)
    return reduce(or_, structs)


ComponentName: TypeAlias = str


def make_component_structs(
    components: dict[ComponentName, dict[Literal["attributes", "subcomponents"], dict]],
) -> Type | None:
    structs = []
    for component_type_name, d in components.items():
        s = msgspec.defstruct(
            "Component",
            [
                ("component_type_name", Literal[component_type_name]),
                ("attributes", list[make_attribute_structs(d["attributes"])]),
            ],
            tag=f"component_{component_type_name}",
        )
        structs.append(s)
    return reduce(or_, structs) if structs else None


def make_command_structs(
    components: dict[ComponentName, dict[Literal["attributes", "subcomponents"], dict]],
) -> Type | None:
    structs = []
    for component_type_name, d in components.items():
        commands_type_annotation = make_command_structs(d["subcomponents"])
        s = msgspec.defstruct(
            "Command",
            [
                ("component_type_name", Literal[component_type_name]),
                ("attributes", list[make_attribute_structs(d["attributes"])]),
                ("components", list[make_component_structs(d["subcomponents"])]),
                (
                    "commands",
                    None
                    if commands_type_annotation is None
                    else list[commands_type_annotation],
                ),
            ],
            tag=f"command_{component_type_name}",
        )
        structs.append(s)
    return reduce(or_, structs) if structs else None
