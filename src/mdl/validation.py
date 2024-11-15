import json
import re
from pathlib import Path
from typing import Any, Callable, Literal, TypeAlias, TypedDict


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


MatchTuple: TypeAlias = tuple[
    bool,
    bool,
    bool,
    bool,
    bool,
    tuple[
        tuple[Literal["maximum length"], re.Match | None],
        tuple[Literal["minimum value"], re.Match | None],
        tuple[Literal["maximum value"], re.Match | None],
    ],
]

ConstraintFunctions = TypedDict(
    "ConstraintFunctions",
    {
        "maximum length": Callable[[int], Callable[[list], bool]],
        "minimum value": Callable[[int], Callable[[int], bool]],
        "maximum value": Callable[[int], Callable[[int], bool]],
    },
)


VEEVA_DOC_TO_PYTHON_TYPE = {
    "String": str,
    "Boolean": bool,
    "Number": int,
    "LongString": str,
    "Enum": Literal,
    "XMLString": str,  # TODO: properly support
}


def max_len_factory(bound: int) -> Callable[[list], bool]:
    def inner(list_: list) -> bool:
        return len(list_) <= bound

    return inner


def min_val_factory(bound: int) -> Callable[[int], bool]:
    def inner(value: int) -> bool:
        return value >= bound

    return inner


def max_val_factory(bound: int) -> Callable[[int], bool]:
    def inner(value: int) -> bool:
        return value <= bound

    return inner


CONSTRAINT_FUNCTIONS: ConstraintFunctions = {
    "maximum length": max_len_factory,
    "minimum value": min_val_factory,
    "maximum value": max_val_factory,
}


def is_enum(s: str | int) -> bool:
    return ENUM_PATTERN.search(str(s)) is not None


def is_multi_value(s: str | int) -> bool:
    return MULTI_VALUE_PATTERN.search(str(s)) is not None


def is_generic_component_reference(matched_type_name: str | int) -> bool:
    return (matched_type_name == "ComponentReference") or (
        matched_type_name == "SubcomponentReference"
    )


def is_component_reference(matched_type_name: str | int) -> bool:
    return (
        # Is it a component type?
        (matched_type_name in component_type_metadata.keys())
        # Is it a subcomponent type?
        or any(
            matched_type_name in v["subcomponents"].keys()
            for v in component_type_metadata.values()
        )
    )


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
    matched_type_name = str(type_match.groups(0)[0])
    enum_match = ENUM_PATTERN.search(type_data)
    allowed_values = (
        set()
        if enum_match is None
        else {s for s in str(enum_match.groups(0)[0]).split("|") if s}
    )
    type_ = VEEVA_DOC_TO_PYTHON_TYPE.get(matched_type_name)
    is_type_supported = type_ is not None
    match_tuple: MatchTuple = (
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
    )
    match match_tuple:
        # Enum: single and multi-value
        case (True, False, False, True, multi_value, _):
            for e in value if isinstance(value, list) else [value]:
                if e not in allowed_values:
                    raise ValidationError(
                        f"Attribute {repr(name)} is {'a multi-value' if multi_value else 'an'} enum with allowed values {', '.join(repr(v) for v in allowed_values)}. Got {repr(e)}."
                    )
        # Generic non-enum: single and multi-value
        case (True, False, False, False, multi_value, _):
            for e in value if isinstance(value, list) else [value]:
                if type(e) is not type_:
                    raise ValidationError(
                        f"Attribute {repr(name)} {'is a multi-value and' if multi_value else ''} ought to be of type {repr(matched_type_name)}. Got {repr(e)} which is of type {repr(type(e))}."
                    )
        # Constraints
        case (True, False, False, False, False, constraints) if any(
            m is not None for _, m in constraints
        ):
            for k, match_ in constraints:
                if match_ is None:
                    continue
                bound = int(match_.groups(0)[0])
                f = CONSTRAINT_FUNCTIONS[k](bound)
                if not f(value):
                    raise ValidationError(
                        f"Attribute {repr(name)} is constrained to {k} {bound}. Got {repr(value)}."
                    )
        # Multi-value reference to other components
        case (False, False, True, False, True, _):
            for e in value if isinstance(value, list) else [value]:
                if re.match(rf"^{matched_type_name}\.", e) is None:
                    raise ValidationError(
                        f"Attribute {repr(name)} is multi-value and ought to be a reference to component {repr(matched_type_name)}. Got {repr(e)}."
                    )
        # Reference to other components
        case (False, False, True, False, False, _):
            if re.match(rf"^{matched_type_name}\.", value) is None:
                raise ValidationError(
                    f"Attribute {repr(name)} ought to be a reference to component {repr(matched_type_name)}. Got {repr(value)}."
                )
        # A generic reference to other components, i.e. the referenced component
        # is not explicitly mentioned
        case (False, True, False, False, False, _):
            # TODO: try to improve error message by pointing to specific component
            # it should refer to. That info is most often available in the
            # `Description` field
            if not re.match(r"^[A-Z][a-z]+\.", value):
                raise ValidationError(
                    f"Attribute {repr(name)} ought to be a reference to a component (`ComponentReference` of `SubcomponentReference`). Got {repr(value)}."
                )
        case _ as wildcard_value:
            raise ImpossibleComponent(
                f"{repr(wildcard_value[:-1])}. Attribute name: {repr(name)}. Attribute value: {repr(value)}."
            )
    # We gucci if no error was raised
    return True
