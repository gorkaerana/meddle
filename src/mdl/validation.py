import json
import re
from pathlib import Path
from typing import Annotated, Any, Literal, Type

import msgspec


class ImpossibleComponent(Exception):
    pass


component_type_metadata = json.loads(
    (Path(__file__).parent / "validation.json").read_text()
)


TYPE_PATTERN = re.compile(r"Type : (.*)")
ENUM_PATTERN = re.compile(r"Allowed values : (.*)", flags=re.MULTILINE)
MULTI_VALUE_PATTERN = re.compile(r"Allows multiple values")
MAX_LEN_PATTERN = re.compile(r"Maximum length : (.*)")
MIN_VAL_PATTERN = re.compile(r"Minimum value : (.*)")
MAX_VAL_PATTERN = re.compile(r"Maximum value : (.*)")


def is_enum(s: str) -> bool:
    return ENUM_PATTERN.search(s) is not None


def is_multi_value(s: str) -> bool:
    return MULTI_VALUE_PATTERN.search(s) is not None


def is_component_reference(matched_type_name: str) -> bool:
    return (
        # Is it a component type?
        (matched_type_name in component_type_metadata.keys())
        # Is it a subcomponent type?
        or any(
            matched_type_name in v["subcomponents"].keys()
            for v in component_type_metadata.values()
        )
    )


def comment_to_type(comment: str) -> Type:
    supported_types = {
        "String": str,
        "Boolean": bool,
        "Number": int,
        "LongString": str,
        "Enum": Literal,
        "XMLString": str,  # TODO: properly support
    }
    type_match = TYPE_PATTERN.search(comment)
    assert type_match is not None, "Type info should always be provided"
    matched_type_name = type_match.groups(0)[0]
    enum_match = ENUM_PATTERN.search(comment)
    allowed_values = (
        []
        if enum_match is None
        else [s for s in enum_match.groups(0)[0].split("|") if s]
    )
    type_ = supported_types.get(matched_type_name)
    is_type_supported = type_ is not None
    # I believe two things are worth pointing out:
    # 1. All attribute values seem to be nullable, hence the `None` at every return.
    # PLenty of examples under `tests/mdl_examples/scrapped`.
    # 2. If an attribute value "allows multiple values", and it contains one item;
    # the parser will parse it as a single value, hence the `list[a_type] | a_type`
    # pattern below.
    match (
        is_type_supported,
        is_component_reference(matched_type_name),
        is_enum(comment),
        is_multi_value(comment),
        (
            ("max_length", MAX_LEN_PATTERN.search(comment)),
            ("ge", MIN_VAL_PATTERN.search(comment)),
            ("le", MAX_VAL_PATTERN.search(comment)),
        ),
    ):
        case (True, True, True, True, _):
            raise ImpossibleComponent(repr((True, True, True, True)))
        case (True, True, True, False, _):
            raise ImpossibleComponent(repr((True, True, True, False)))
        case (True, True, False, True, _):
            raise ImpossibleComponent(repr((True, True, False, True)))
        case (True, True, False, False, _):
            raise ImpossibleComponent(repr((True, True, False, False)))
        # Multi-value enum
        case (True, False, True, True, _):
            return list[Literal[*allowed_values]] | Literal[*allowed_values] | None
        # Enum
        case (True, False, True, False, _):
            return Literal[*allowed_values] | None
        # Multi-value non-enum
        case (True, False, False, True, _):
            return list[type_] | type_ | None
        # Constraints
        case (True, False, False, False, constraints) if any(
            m is not None for _, m in constraints
        ):
            annotation_metadata = {
                k: int(m.groups(0)[0]) for k, m in constraints if m is not None
            }
            return Annotated[type_, msgspec.Meta(**annotation_metadata)] | None
        case (True, False, False, False, _):
            return type_ | None
        case (False, True, True, True, _):
            raise ImpossibleComponent(repr((False, True, True, True)))
        case (False, True, True, False, _):
            raise ImpossibleComponent(repr((False, True, True, False)))
        # Multi-value reference to other components
        case (False, True, False, True, _):
            # TODO: this current validation implementation does not allow to validate a list
            # of references, as Annotated[list[str], msgspec.Meta(pattern=rf"^{matched_type_name}\.")]
            # is not a valid msgspec type constraint
            return Any | None
        # Reference to other components
        case (False, True, False, False, _):
            return (
                Annotated[str, msgspec.Meta(pattern=rf"^{matched_type_name}\.")] | None
            )
        case (False, False, True, True, _):
            raise ImpossibleComponent(repr((False, False, True, True)))
        case (False, False, True, False, _):
            raise ImpossibleComponent(repr((False, False, True, False)))
        case (False, False, False, True, _):
            raise ImpossibleComponent(repr((False, False, False, True)))
        case (False, False, False, False, _):
            raise ImpossibleComponent(repr((False, False, False, False)))
