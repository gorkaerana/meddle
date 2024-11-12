import re
from typing import Annotated, Any, Literal, Type

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
