from __future__ import annotations
from pathlib import Path
from typing import Callable, Generator, Literal, Self, TypeAlias

from lark import Lark, Transformer, Tree
from msgspec import Struct


INDENT = " " * 4


class Unreachable(Exception):
    pass


class ValidationError(Exception):
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
    value: AttributeValue | list[AttributeValue] | None = None
    command: str | None = None

    @classmethod
    def loads(self, source: str) -> Attribute:
        return get_parser("attribute").parse(source)

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
        else:
            yield repr(self.value)
        yield ")"

    def dumps(self):
        return "".join(self.__parts__())

    def validate(
        self,
        metadata: dict,
        parent_component_type_name: str,
    ) -> Literal[True]:
        attribute_metadata = metadata["attributes"].get(self.name)
        if attribute_metadata is None:
            raise ValidationError(
                f"Attribute name {repr(self.name)} is not allowed under component type "
                f"{repr(parent_component_type_name)}. Options are: "
                f"{', '.join(repr(n) for n in metadata['attributes'].keys())}."
            )
        # TODO: type checking, length check, enum check, etc.
        return True


class Component(Struct):
    component_type_name: str
    component_name: str
    attributes: list[Attribute] | None = None

    @classmethod
    def loads(self, source: str) -> Component:
        return get_parser("component").parse(source)

    def __parts__(self, indent_level: int = 0) -> Generator[str]:
        yield f"{INDENT*indent_level}{self.component_type_name} {self.component_name} ("
        for a in self.attributes or []:
            yield "".join(a.__parts__(indent_level + 1))
        yield f"{INDENT*indent_level});"

    def dumps(self):
        return "\n".join(self.__parts__())

    def validate(
        self, metadata: dict, parent_component_type_name: str
    ) -> Literal[True]:
        ctn = self.component_type_name
        component_metadata = metadata["subcomponents"].get(ctn)
        if component_metadata is None:
            raise ValidationError(
                f"Component type {repr(ctn)} is not allowed under component type "
                f"{repr(parent_component_type_name)}. Options are: "
                f"{', '.join(repr(k) for k in metadata['subcomponents'].keys())}."
            )
        return all(a.validate(component_metadata, ctn) for a in self.attributes or [])


class Command(Struct):
    command: str
    component_type_name: str
    component_name: str
    attributes: list[Attribute] | None = None
    components: list[Component] | None = None
    commands: list[Command] | None = None
    to_component_name: str | None = None
    logical_operator: str | None = None

    @classmethod
    def loads(self, source: str) -> Component:
        return get_parser("mdl_command").parse(source)

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
        self, metadata: dict, parent_component_type_name: str | None = None
    ) -> Literal[True]:
        # TODO: massage parsed info into whatever's best
        ctn = self.component_type_name
        if parent_component_type_name is None:
            ctm = metadata.get(ctn)
            if ctm is None:
                raise ValidationError(f"Component type {repr(ctm)} does not exist.")
        else:
            ctm = metadata["subcomponents"].get(ctn)
            if ctm is None:
                raise ValidationError(
                    f"Component type {repr(ctn)} is not allowed under component type "
                    f"{repr(parent_component_type_name)}. Options are: "
                    f"{', '.join(repr(k) for k in metadata['subcomponents'].keys())}."
                )
        return all(
            all(e.validate(ctm, ctn) for e in f or [])
            for f in [self.attributes, self.components, self.commands]
        )


def generic_command(
    command_name,
) -> Callable[
    [Self, list[Tree | list[Attribute] | list[Component] | list[Command]]], Command
]:
    def inner(
        self, children: list[Tree | list[Attribute] | list[Component] | list[Command]]
    ) -> Command:
        if (children[1] == "IF EXISTS") or (children[1] == "IF NOT EXISTS"):
            component_type_name_tree, logical_operator, component_name_tree, *rest = (
                children
            )
        else:
            component_type_name_tree, component_name_tree, *rest = children
            logical_operator = None
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
