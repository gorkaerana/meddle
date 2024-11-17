from __future__ import annotations
from collections import deque
from pathlib import Path
from typing import Any, Callable, Generator, Iterable, Literal, TypeAlias, overload

from lark import Lark, Transformer, Tree, Token
import msgspec

from mdl.validation import (
    ValidationError,
    component_type_metadata,
    type_check_attribute,
)


INDENT = " " * 4


class Unreachable(Exception):
    pass


here = Path(__file__).parent
mdl_grammar = (here / "mdl_grammar.lark").read_text()


def first_child_is_token(tree: Tree) -> bool:
    return (len(tree.children) > 0) and isinstance(tree.children[0], Token)


def mark_first_and_last(
    iterable: Iterable,
) -> Generator[tuple[bool, bool, Any], None, None]:
    """Given an `iterable`, flag its first and last elements. E.g.
    >>> list(mark_first_and_last(range(3)))
    >>> [(True, False, 0), (False, False, 1), (False, True, 2)]
    """
    iterable = iter(iterable)
    buffer_ = deque([(True, False, next(iterable))], maxlen=1)
    while True:
        try:
            next_value = next(iterable)
            yield buffer_.pop()
            buffer_.append((False, False, next_value))
        except StopIteration:
            *_, value = buffer_.pop()
            yield (False, True, value)
            break


@overload
def parse_and_transform(start: Literal["attribute"], source: str) -> "Attribute": ...


@overload
def parse_and_transform(start: Literal["component"], source: str) -> "Component": ...


@overload
def parse_and_transform(start: Literal["mdl_command"], source: str) -> "Command": ...


def parse_and_transform(start: str, source: str):
    parser = Lark(grammar=mdl_grammar, start=start, parser="lalr")
    parsed = parser.parse(source)
    transformer = MdlTreeTransformer(visit_tokens=True)
    transformed = transformer.transform(parsed)
    return transformed


AttributeValue: TypeAlias = bool | int | float | str


class Attribute(msgspec.Struct):
    name: str
    value: AttributeValue | list[AttributeValue] | None = None
    command: str | None = None

    @classmethod
    def loads(cls, source: str) -> Attribute:
        return parse_and_transform("attribute", source)

    def __parts__(self, indent_level: int = 0) -> Generator[str]:
        yield (INDENT * indent_level)
        yield self.name
        if self.command is not None:
            yield " "
            yield self.command.upper()
            yield " "
        yield "("
        if self.value is None:
            yield ""
        elif isinstance(self.value, bool):
            yield str(self.value).lower()
        elif isinstance(self.value, list):
            yield repr(self.value)[1:-1]
        elif isinstance(self.value, float | int):
            yield repr(self.value)
        else:
            string_lines = self.value.splitlines()
            if len(string_lines) == 1:
                yield repr(self.value)
            else:
                for first, last, line in mark_first_and_last(string_lines):
                    yield f"{'\'' * first}{line}{'\'' * last}{'\n' * (not last)}"
        yield ")"

    def dumps(self):
        return "".join(self.__parts__())

    def validate(
        self,
        metadata: dict,
        parent_component_type_name: str,
    ) -> bool:
        attribute_metadata = metadata["attributes"].get(self.name)
        if attribute_metadata is None:
            options = ", ".join(repr(n) for n in metadata["attributes"].keys())
            raise ValidationError(
                f"Attribute name {repr(self.name)} is not allowed under component type "
                f"{repr(parent_component_type_name)}. Options are: {options}."
            )
        return type_check_attribute(
            self.name, self.value, attribute_metadata["type_data"]
        )


class Component(msgspec.Struct):
    component_type_name: str
    component_name: str
    attributes: list[Attribute] | None = None

    @classmethod
    def loads(cls, source: str) -> Component:
        return parse_and_transform("component", source)

    def __parts__(self, indent_level: int = 0) -> Generator[str]:
        yield f"{INDENT*indent_level}{self.component_type_name} {self.component_name} ("
        for a in self.attributes or []:
            yield "".join(a.__parts__(indent_level + 1))
        yield f"{INDENT*indent_level});"

    def dumps(self):
        return "\n".join(self.__parts__())

    def validate(self, metadata: dict, parent_component_type_name: str) -> bool:
        ctn = self.component_type_name
        component_metadata = metadata["subcomponents"].get(ctn)
        if component_metadata is None:
            options = ", ".join(repr(k) for k in metadata["subcomponents"].keys())
            raise ValidationError(
                f"Component type {repr(ctn)} is not allowed under component type "
                f"{repr(parent_component_type_name)}. Options are: {options}."
            )
        return all(a.validate(component_metadata, ctn) for a in self.attributes or [])


class Command(msgspec.Struct):
    command: str
    component_type_name: str
    component_name: str
    attributes: list[Attribute] | None = None
    components: list[Component] | None = None
    commands: list[Command] | None = None
    to_component_name: str | None = None
    logical_operator: str | None = None

    @classmethod
    def loads(cls, source: str) -> Command:
        return parse_and_transform("mdl_command", source)

    def __parts__(self, indent_level: int = 0) -> Generator[str]:
        first_line_start = (
            f"{INDENT * indent_level}"
            f"{self.command.upper()} "
            f"{self.component_type_name} "
            f"{self.component_name}"
        )
        if self.command.lower() == "drop":
            yield f"{first_line_start};"
        elif self.command.lower() == "rename":
            yield f"{first_line_start} TO {self.to_component_name};"
        else:
            yield f"{first_line_start} ("
            for a in self.attributes or []:
                yield "".join(a.__parts__(indent_level + 1)) + ","
            for comp in self.components or []:
                yield "\n".join(comp.__parts__(indent_level + 1))
            for com in self.commands or []:
                yield (
                    f"{INDENT * indent_level}"
                    f"{'\n'.join(com.__parts__(indent_level + 1))}"
                )
            yield f"{INDENT * indent_level});"

    def dumps(self):
        return "\n".join(self.__parts__())

    def validate(
        self,
        metadata: dict | None = None,
        parent_component_type_name: str | None = None,
    ) -> bool:
        ctn = self.component_type_name
        metadata_: dict = component_type_metadata if metadata is None else metadata
        # Top-level command
        if parent_component_type_name is None:
            ctm = metadata_.get(ctn)
            if ctm is None:
                raise ValidationError(f"Component type {repr(ctm)} does not exist.")
        # We are below another command
        else:
            ctm = metadata_["subcomponents"].get(ctn)
            if ctm is None:
                options = ", ".join(repr(k) for k in metadata_["subcomponents"].keys())
                raise ValidationError(
                    f"Component type {repr(ctn)} is not allowed under component type "
                    f"{repr(parent_component_type_name)}. Options are: {options}."
                )
        return all(
            e.validate(ctm, ctn)
            for f in [self.attributes, self.components, self.commands]
            for e in f or []
        )


def generic_command(command_name: str) -> Callable[[MdlTreeTransformer, Any], Command]:
    def inner(self, children: Any) -> Command:
        component_type_name_tree: Tree[Token]
        logical_operator: str | None
        component_name_tree: Tree[Token]
        component_type_name: str
        component_name: str
        attributes: list[Attribute] | None
        components: list[Component] | None
        commands: list[Command] | None
        match children:
            case (
                component_type_name_tree,
                logical_operator,
                component_name_tree,
                *rest,
            ) if (
                (logical_operator in {"IF EXISTS", "IF NOT EXISTS"})
                and first_child_is_token(component_type_name_tree)
                and first_child_is_token(component_name_tree)
            ):
                (
                    component_type_name_tree,
                    logical_operator,
                    component_name_tree,
                    *rest,
                ) = children
            case (component_type_name_tree, component_name_tree, *rest) if (
                first_child_is_token(component_type_name_tree)
                and first_child_is_token(component_name_tree)
            ):
                component_type_name_tree, component_name_tree, *rest = children
                logical_operator = None
            case _:
                raise Unreachable(f"Got children {children}")
        # This assertion only exists to please `pyright`, notice how this is
        # checked for in both `match` cases above, via `first_child_is_token`.
        # For whichever reason `pyright` can't:
        # 1. Figure that out.
        # 2. Figure out that `first_child_is_token` does exactly that in this context
        assert isinstance(component_type_name_tree.children[0], Token) and isinstance(
            component_name_tree.children[0], Token
        )
        component_type_name = component_type_name_tree.children[0].value
        component_name = component_name_tree.children[0].value
        attributes, components, commands = None, None, None
        match rest:
            case [[Attribute(_), *_], [Component(_), *_], [Command(_), *_]]:
                attributes, components, commands = rest
            case [[Attribute(_), *_], [Component(_), *_]]:
                attributes, components = rest
            case [[Attribute(_), *_], [Command(_), *_]]:
                attributes, commands = rest
            case [[Component(_), *_], [Command(_), *_]]:
                components, commands = rest
            case [[Attribute(_), *_]]:
                (attributes,) = rest
            case [[Component(_, _), *_]]:
                (components,) = rest
            case [[Command(_), *_]]:
                (commands,) = rest
            case _:
                raise Unreachable(f"Got {rest} for {repr(command_name)}")
        return Command(
            command=command_name,
            component_type_name=component_type_name,
            component_name=component_name,
            attributes=attributes,
            components=components,
            commands=commands,
            logical_operator=logical_operator,
        )

    return inner


class MdlTreeTransformer(Transformer):
    def xml(self, children) -> str:
        # TODO: support properly instead of just reading into a string
        assert len(children) == 1, "A 'xml' branch can only have a single children"
        return children[0].value

    def boolean(self, children) -> bool:
        assert len(children) == 1, "A 'boolean' branch can only have a single children"
        (child,) = children
        if child.data.value == "true":
            return True
        elif child.data.value == "false":
            return False
        else:
            raise Unreachable("A 'boolean' can only have values 'true' or 'false'")

    def string(self, children) -> str:
        return "".join(c.value for c in children)

    def number(self, children) -> float | int:
        assert len(children) == 1, "A 'number' branch can only have a single children"
        (child,) = children
        if child.type == "INT":
            return int(child.value)
        if child.type == "DECIMAL":
            return float(child.value)
        else:
            raise Unreachable("A 'number' can either be parsed as an int or a decimal")

    def attribute_value(self, children) -> AttributeValue | list[AttributeValue] | None:
        if len(children) == 0:
            return None
        if len(children) == 1:
            return children[0].children[0]
        return [c.children[0] for c in children]

    def attribute_name(self, children) -> str:
        return children[0].value

    def attribute(self, children) -> Attribute:
        return Attribute(children[0], children[1])

    def attributes(self, children) -> list[Attribute]:
        return children

    def alter_attribute(self, children) -> Attribute:
        if len(children) == 2:
            return self.attribute(children)
        elif len(children) == 3:
            return Attribute(children[0], children[-1], children[1].data.value.upper())
        else:
            raise Unreachable(
                "An 'alter_attribute' branch can only have 2 or 3 children"
            )

    def alter_attributes(self, children) -> list[Attribute]:
        return children

    def logical_operator(self, children):
        return children[0].data.value.replace("_", " ").upper()

    def component(self, children) -> Component:
        # TODO: account for no attributes
        component_type_name_tree, component_name_tree, attributes = children
        return Component(
            component_type_name_tree.children[0].value,
            component_name_tree.children[0].value,
            attributes,
        )

    def components(self, children) -> list[Component]:
        return children

    create_command = generic_command("CREATE")

    recreate_command = generic_command("RECREATE")

    def drop_command(self, children) -> Command:
        component_type_name_tree, component_name_tree = children
        return Command(
            "DROP",
            component_type_name_tree.children[0].value,
            component_name_tree.children[0].value,
        )

    def rename_command(self, children) -> Command:
        component_type_name_tree, component_name_tree, to_component_name_tree = children
        return Command(
            "RENAME",
            component_type_name_tree.children[0].value,
            component_name_tree.children[0].value,
            to_component_name=to_component_name_tree.children[0].value,
        )

    add_command = generic_command("ADD")

    modify_command = generic_command("MODIFY")

    alter_command = generic_command("ALTER")

    def alter_subcommands(self, children) -> list[Command]:
        return children

    def alter_subcommand(self, children) -> Command:
        return children[0]

    def mdl_command(self, children) -> Command:
        return children[0]
