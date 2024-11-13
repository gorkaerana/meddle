import json
import re
from pathlib import Path
from typing import Annotated, Any, Literal, Type

import msgspec


component_type_metadata = json.loads(
    (Path(__file__).parent / "validation.json").read_text()
)


def comment_to_type(comment: str) -> Type:
    supported_types = {
        "String": str,
        "Boolean": bool,
        "Number": int,
        "LongString": str,
        "Enum": Literal,
        "XMLString": str,  # TODO: properly support
        # "Expression": ET.Element,  # TODO: properly support
    }
    type_match = re.search(r"Type : (.*)", comment)
    matched_type_name = type_match.groups(0)[0]
    max_len_match = re.search(r"Maximum length : (.*)", comment)
    min_val_match = re.search(r"Minimum value : (.*)", comment)
    max_val_match = re.search(r"Maximum value : (.*)", comment)
    allowed_vals_match = re.search(r"Allowed values : (.*)", comment, re.MULTILINE)
    allow_multiple_vals_match = re.search(r"Allows multiple values", comment)
    type_ = supported_types.get(matched_type_name)
    # `matched_type_name` might not map to any Python built-in type, but it might
    # be a component type
    if type_ is None and (
        # Is it a component type?
        (matched_type_name in component_type_metadata.keys())
        # If it a subcomponent type?
        or any(matched_type_name in v.keys() for v in component_type_metadata.values())
    ):
        return Annotated[str, msgspec.Meta(pattern=rf"^{matched_type_name}\.")] | None
    if (allow_multiple_vals_match is not None) and (allowed_vals_match is not None):
        return (
            list[Literal[*(s for s in allowed_vals_match.groups(0)[0].split("|") if s)]]
            | None
        )
    elif allow_multiple_vals_match is not None:
        return list[type_] | None
    elif allowed_vals_match is not None:
        return (
            Literal[*(s for s in allowed_vals_match.groups(0)[0].split("|") if s)]
            | None
        )
    if any(m is not None for m in [max_len_match, min_val_match, max_val_match]) and (
        type_ is not None
    ):
        annotation_metadata = {
            k: int(m.groups(0)[0])
            for k, m in [
                ("max_length", max_len_match),
                ("ge", min_val_match),
                ("le", max_val_match),
            ]
            if m is not None
        }
        return Annotated[type_, msgspec.Meta(**annotation_metadata)] | None
    # Based on some examples I found on Veeva's GitHub, attribute values seem to be
    # nullable. See `tests/mdl_examples/scrapped` for plenty of examples
    return Any | None
