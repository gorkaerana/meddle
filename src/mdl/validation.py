import json
import re
from pathlib import Path
from typing import Any, Callable, Literal


class ValidationError(Exception):
    pass


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


CONSTRAINT_FUNCTIONS: dict[
    Literal["maximum length", "minimum value", "maximum value"],
    Callable[[int], Callable[[int | list], bool]],
] = {
    "maximum length": lambda bound: lambda list_: len(list_) <= bound,
    "minimum value": lambda bound: lambda value: value >= bound,
    "maximum value": lambda bound: lambda value: value <= bound,
}


def is_enum(s: str) -> bool:
    return ENUM_PATTERN.search(s) is not None


def is_multi_value(s: str) -> bool:
    return MULTI_VALUE_PATTERN.search(s) is not None


def is_generic_component_reference(matched_type_name: str) -> bool:
    return (matched_type_name == "ComponentReference") or (
        matched_type_name == "SubcomponentReference"
    )


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


VEEVA_DOC_TO_PYTHON_TYPE = {
    "String": str,
    "Boolean": bool,
    "Number": int,
    "LongString": str,
    "Enum": Literal,
    "XMLString": str,  # TODO: properly support
}


# Ideally we would pass the whole attribute, but type hinting it would cause
# a circular import
def type_check_attribute(name: str, value: Any, type_data: str):
    if value is None:
        # All attribute values seem to be nullable.
        # Plenty of examples under `tests/mdl_examples/scrapped`.
        return True
    type_match = TYPE_PATTERN.search(type_data)
    assert (
        type_match is not None
    ), "Attribute value type info should always be provided in Veeva documentation"
    matched_type_name = type_match.groups(0)[0]
    enum_match = ENUM_PATTERN.search(type_data)
    allowed_values = (
        set()
        if enum_match is None
        else {s for s in enum_match.groups(0)[0].split("|") if s}
    )
    type_ = VEEVA_DOC_TO_PYTHON_TYPE.get(matched_type_name)
    is_type_supported = type_ is not None
    match (
        is_type_supported,
        is_generic_component_reference(matched_type_name),
        is_component_reference(matched_type_name),
        is_enum(type_data),
        is_multi_value(type_data),
        (
            ("maximum length", MAX_LEN_PATTERN.search(type_data)),
            ("minimum value", MIN_VAL_PATTERN.search(type_data)),
            ("maximum value", MAX_VAL_PATTERN.search(type_data)),
        ),
    ):
        # Multi-value enum
        case (True, False, False, True, True, _):
            for e in value if isinstance(value, list) else [value]:
                if e not in allowed_values:
                    raise ValidationError(
                        f"Attribute {repr(name)} is a multi-value enum with allowed values {', '.join(repr(v) for v in allowed_values)}. Got {repr(e)}"
                    )
        # Enum
        case (True, False, False, True, False, _):
            if value not in allowed_values:
                raise ValidationError(
                    f"Attribute {repr(name)} is an enum with allowed values {', '.join(repr(v) for v in allowed_values)}. Got {repr(value)}"
                )
        # Multi-value non-enum
        case (True, False, False, False, True, _):
            for e in value if isinstance(value, list) else [value]:
                if not isinstance(e, type_):
                    raise ValidationError(
                        f"Attribute {repr(name)} is a multi-value and ought to be of type {repr(matched_type_name)}. Got {repr(e)} which is of type {repr(type(e))}"
                    )
        # Constraints
        case (True, False, False, False, False, constraints) if any(
            m is not None for _, m in constraints
        ):
            for k, match_ in (t for t in constraints if t[1] is not None):
                bound = int(match_.groups(0)[0])
                f = CONSTRAINT_FUNCTIONS[k](bound)
                if not f(value):
                    raise ValidationError(
                        f"Attribute {repr(name)} is constrained to {k} {bound}. Got {repr(value)}."
                    )
        case (True, False, False, False, False, _):
            if not isinstance(value, type_):
                raise ValidationError(
                    f"Attribute {repr(name)} ought to be of type {repr(matched_type_name)}. Got {repr(value)} which is of type {repr(type(value))}"
                )
        # Multi-value reference to other components
        case (False, False, True, False, True, _):
            for e in value if isinstance(value, list) else [value]:
                if re.match(rf"^{matched_type_name}\.", e) is None:
                    raise ValidationError(
                        f"Attribute {repr(name)} is multi-value and ought to be a reference to component {repr(matched_type_name)}. Got {repr(e)}"
                    )
        # Reference to other components
        case (False, False, True, False, False, _):
            if re.match(rf"^{matched_type_name}\.", value) is None:
                raise ValidationError(
                    f"Attribute {repr(name)} ought to be a reference to component {repr(matched_type_name)}. Got {repr(value)}"
                )
        # Reference to other components
        case (False, True, False, False, False, _):
            # TODO: try to improve error message by pointing to specific component
            # it should refer to. That info is most often available in the
            # `Description` field
            if not re.match(r"^[A-Z][a-z]+\.", value):
                raise ValidationError(
                    f"Attribute {repr(name)} ought to be a reference to a component (`ComponentReference` of `SubcomponentReference`). Got {repr(value)}"
                )
        case _ as wildcard_value:
            raise ImpossibleComponent(
                f"{repr(wildcard_value[:-1])}. Attribute name: {repr(name)}. Attribute value: {repr(value)}"
            )
    # We gucci if no error was raised
    return True
