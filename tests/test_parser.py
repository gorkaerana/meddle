# TODO: test 'alter_subcommand' and 'alter_subcommands' rules
# TODO: test all grammar rules
from pathlib import Path

from lark import Lark
import pytest
import msgspec

from mdl.parser import MdlTreeTransformer, Attribute, Component, Command


@pytest.fixture
def here():
    return Path(__file__).parent


@pytest.fixture
def project_root(here):
    return here.parent


@pytest.fixture
def mdl_grammar(project_root):
    return (project_root / "src" / "mdl" / "mdl_grammar.lark").read_text()


@pytest.fixture
def attribute_value_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="attribute_value",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def attribute_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="attribute",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def attributes_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="attributes",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def component_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="component",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def components_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="components",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def create_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="create_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def create_command_mdl(here):
    return (here / "mdl_examples" / "create.mdl").read_text()


@pytest.fixture
def create_command_json(here):
    return (here / "mdl_examples" / "create.json").read_text()


@pytest.fixture
def recreate_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="recreate_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def recreate_command_mdl(here):
    return (here / "mdl_examples" / "recreate.mdl").read_text()


@pytest.fixture
def recreate_command_json(here):
    return (here / "mdl_examples" / "recreate.json").read_text()


@pytest.fixture
def drop_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="drop_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def drop_command_mdl(here):
    return (here / "mdl_examples" / "drop.mdl").read_text()


@pytest.fixture
def drop_command_json(here):
    return (here / "mdl_examples" / "drop.json").read_text()


@pytest.fixture
def rename_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="rename_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def rename_command_mdl(here):
    return (here / "mdl_examples" / "rename.mdl").read_text()


@pytest.fixture
def rename_command_json(here):
    return (here / "mdl_examples" / "rename.json").read_text()


@pytest.fixture
def alter_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="alter_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def alter_command_mdl(here):
    return (here / "mdl_examples" / "alter.mdl").read_text()


@pytest.fixture
def alter_command_json(here):
    return (here / "mdl_examples" / "alter.json").read_text()


@pytest.fixture
def add_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="add_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def add_command_mdl(here):
    return (here / "mdl_examples" / "add.mdl").read_text()


@pytest.fixture
def add_command_json(here):
    return (here / "mdl_examples" / "add.json").read_text()


@pytest.fixture
def modify_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="modify_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def modify_command_mdl(here):
    return (here / "mdl_examples" / "modify.mdl").read_text()


@pytest.fixture
def modify_command_json(here):
    return (here / "mdl_examples" / "modify.json").read_text()


@pytest.fixture
def mdl_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="mdl_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


def test_string_attribute_value(attribute_value_parser):
    assert attribute_value_parser.parse("'This is a string'") == "This is a string"


def test_boolean_attribute_value(attribute_value_parser):
    assert attribute_value_parser.parse("true")
    assert not attribute_value_parser.parse("false")


def test_integer_attribute_value(attribute_value_parser):
    assert attribute_value_parser.parse("1") == 1


def test_float_attribute_value(attribute_value_parser):
    assert attribute_value_parser.parse("1.1") == 1.1


def test_string_multi_value_attribute_value(attribute_value_parser):
    assert attribute_value_parser.parse("'one string', 'two strings'") == [
        "one string",
        "two strings",
    ]


def test_integer_multi_value_attribute_value(attribute_value_parser):
    assert attribute_value_parser.parse("5, 6") == [5, 6]


def test_attribute(attribute_parser):
    assert attribute_parser.parse("my_bool_attribute(true)") == Attribute(
        "my_bool_attribute", True
    )


def test_attributes(attributes_parser):
    assert attributes_parser.parse("my_bool_attribute(true), my_num_attribute(5)") == [
        Attribute("my_bool_attribute", True),
        Attribute("my_num_attribute", 5),
    ]


def test_attributes_comma_in_the_end(attributes_parser):
    assert attributes_parser.parse("my_bool_attribute(true), my_num_attribute(5),") == [
        Attribute("my_bool_attribute", True),
        Attribute("my_num_attribute", 5),
    ]


def test_component(component_parser):
    assert component_parser.parse("""Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )""") == Component(
        component_type_name="Mysubcomponent",
        component_name="my_subcomp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True),
            Attribute(name="my_num_attribute", value=5),
        ],
    )


def test_components(components_parser):
    assert components_parser.parse("""  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );
        Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )""") == [
        Component(
            component_type_name="Mysubcomponent",
            component_name="my_subcomp__c",
            attributes=[
                Attribute(name="my_bool_attribute", value=True),
                Attribute(name="my_num_attribute", value=5),
            ],
        ),
        Component(
            component_type_name="Mysubcomponent",
            component_name="my_subcomp__c",
            attributes=[
                Attribute(name="my_bool_attribute", value=True),
                Attribute(name="my_num_attribute", value=5),
            ],
        ),
    ]


def test_components_optional_semicolon_in_the_end(components_parser):
    assert components_parser.parse("""  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );
        Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );""") == [
        Component(
            component_type_name="Mysubcomponent",
            component_name="my_subcomp__c",
            attributes=[
                Attribute(name="my_bool_attribute", value=True),
                Attribute(name="my_num_attribute", value=5),
            ],
        ),
        Component(
            component_type_name="Mysubcomponent",
            component_name="my_subcomp__c",
            attributes=[
                Attribute(name="my_bool_attribute", value=True),
                Attribute(name="my_num_attribute", value=5),
            ],
        ),
    ]


def test_create_command(create_command_parser, create_command_mdl, create_command_json):
    assert create_command_parser.parse(
        create_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(create_command_json, type=Command)


def test_create_command_optional_semicolon_in_the_end(
    create_command_parser, create_command_mdl, create_command_json
):
    assert create_command_parser.parse(create_command_mdl) == msgspec.json.decode(
        create_command_json, type=Command
    )


def test_recreate_command(
    recreate_command_parser, recreate_command_mdl, recreate_command_json
):
    assert recreate_command_parser.parse(
        recreate_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(recreate_command_json, type=Command)


def test_recreate_command_optional_semicolon_in_the_end(
    recreate_command_parser, recreate_command_mdl, recreate_command_json
):
    assert recreate_command_parser.parse(recreate_command_mdl) == msgspec.json.decode(
        recreate_command_json, type=Command
    )


def test_drop_command(drop_command_parser, drop_command_mdl, drop_command_json):
    assert drop_command_parser.parse(
        drop_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(drop_command_json, type=Command)


def test_drop_command_optional_semicolon_in_the_end(
    drop_command_parser, drop_command_mdl, drop_command_json
):
    assert drop_command_parser.parse(drop_command_mdl) == msgspec.json.decode(
        drop_command_json, type=Command
    )


def test_rename_command(rename_command_parser, rename_command_mdl, rename_command_json):
    assert rename_command_parser.parse(
        rename_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(rename_command_json, type=Command)


def test_rename_command_optional_semicolon_in_the_end(
    rename_command_parser, rename_command_mdl, rename_command_json
):
    assert rename_command_parser.parse(rename_command_mdl) == msgspec.json.decode(
        rename_command_json, type=Command
    )


def test_alter_command(alter_command_parser, alter_command_mdl, alter_command_json):
    assert alter_command_parser.parse(
        alter_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(alter_command_json, type=Command)


def test_alter_command_optional_semicolon_in_the_end(
    alter_command_parser, alter_command_mdl, alter_command_json
):
    assert alter_command_parser.parse(alter_command_mdl) == msgspec.json.decode(
        alter_command_json, type=Command
    )


def test_add_command(add_command_parser, add_command_mdl, add_command_json):
    assert add_command_parser.parse(
        add_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(add_command_json, type=Command)


def test_add_command_optional_semicolon_in_the_end(
    add_command_parser, add_command_mdl, add_command_json
):
    assert add_command_parser.parse(add_command_mdl) == msgspec.json.decode(
        add_command_json, type=Command
    )


def test_modify_command(modify_command_parser, modify_command_mdl, modify_command_json):
    assert modify_command_parser.parse(
        modify_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(modify_command_json, type=Command)


def test_modify_command_optional_semicolon_in_the_end(
    modify_command_parser, modify_command_mdl, modify_command_json
):
    assert modify_command_parser.parse(modify_command_mdl) == msgspec.json.decode(
        modify_command_json, type=Command
    )


@pytest.mark.parametrize(
    "mdl,json",
    [
        ("create_command_mdl", "create_command_json"),
        ("recreate_command_mdl", "recreate_command_json"),
        ("drop_command_mdl", "drop_command_json"),
        ("rename_command_mdl", "rename_command_json"),
        ("alter_command_mdl", "alter_command_json"),
    ],
)
def test_mdl_command(mdl, json, request, mdl_command_parser):
    assert mdl_command_parser.parse(
        request.getfixturevalue(mdl)
    ) == msgspec.json.decode(request.getfixturevalue(json), type=Command)
