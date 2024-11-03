from __future__ import annotations
from pathlib import Path
from typing import Callable, Self, TypeAlias

from lark import Lark, Transformer, Tree
from msgspec import Struct


class Unreachable(Exception):
    pass


mdl_grammar = (Path(__file__).parent / "mdl_grammar.lark").read_text()


def get_parser(start: str) -> Lark:
    return Lark(
        grammar=mdl_grammar,
        start=start,
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


AttributeValue: TypeAlias = bool | int | float | str


class Attribute(Struct):
    name: str
    value: AttributeValue | list[AttributeValue]
    command: str | None = None

    @classmethod
    def loads(self, source: str) -> Attribute:
        return get_parser("attribute").parse(source)


class Component(Struct):
    component_type_name: str
    component_name: str
    attributes: list[Attribute] | None = None

    @classmethod
    def loads(self, source: str) -> Component:
        return get_parser("component").parse(source)


class Command(Struct):
    command: str
    component_type_name: str
    component_name: str
    attributes: list[Attribute] | None = None
    components: list[Component] | None = None
    commands: list[Command] | None = None
    to_component_name: str | None = None

    @classmethod
    def loads(self, source: str) -> Component:
        return get_parser("mdl_command").parse(source)


def generic_command(
    command_name,
) -> Callable[
    [Self, list[Tree | list[Attribute] | list[Component] | list[Command]]], Command
]:
    def inner(
        self, forest: list[Tree | list[Attribute] | list[Component] | list[Command]]
    ) -> Command:
        component_type_name_tree, component_name_tree, *rest = forest
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
                (components,) = forest
            case [[Command(_), *_]]:
                (commands,) = forest
            case _:
                raise Unreachable(f"Got {rest} for {repr(command_name)}")
        return Command(
            command_name,
            component_type_name,
            component_name,
            attributes,
            components,
            commands,
        )

    return inner


class MdlTreeTransformer(Transformer):
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

    def attribute_value(self, children) -> AttributeValue | list[AttributeValue]:
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
