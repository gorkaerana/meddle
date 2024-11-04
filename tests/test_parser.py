# TODO: test 'alter_subcommand' and 'alter_subcommands' rules
# TODO: test all grammar rules
import json
from pathlib import Path

import pytest
import msgspec

from mdl.parser import Attribute, Component, Command, get_parser


@pytest.fixture
def here():
    return Path(__file__).parent


@pytest.fixture
def mdl_examples_dir(here):
    return here / "mdl_examples"


@pytest.fixture
def component_metadata(here):
    return json.loads((here.parent / "src" / "mdl" / "validation.json").read_text())


@pytest.fixture
def attribute_value_parser():
    return get_parser("attribute_value").parse


@pytest.fixture
def attribute_parser():
    return get_parser("attribute").parse


@pytest.fixture
def attributes_parser():
    return get_parser("attributes").parse


@pytest.fixture
def component_parser():
    return get_parser("component").parse


@pytest.fixture
def components_parser():
    return get_parser("components").parse


@pytest.fixture
def logical_operator_parser():
    return get_parser("logical_operator").parse


@pytest.fixture
def create_command_parser():
    return get_parser("create_command").parse


@pytest.fixture
def create_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "create.mdl").read_text()


@pytest.fixture
def create_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "create.json").read_text()


@pytest.fixture
def recreate_command_parser():
    return get_parser("recreate_command").parse


@pytest.fixture
def recreate_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "recreate.mdl").read_text()


@pytest.fixture
def recreate_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "recreate.json").read_text()


@pytest.fixture
def drop_command_parser():
    return get_parser("drop_command").parse


@pytest.fixture
def drop_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "drop.mdl").read_text()


@pytest.fixture
def drop_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "drop.json").read_text()


@pytest.fixture
def rename_command_parser():
    return get_parser("rename_command").parse


@pytest.fixture
def rename_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "rename.mdl").read_text()


@pytest.fixture
def rename_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "rename.json").read_text()


@pytest.fixture
def alter_command_parser():
    return get_parser("alter_command").parse


@pytest.fixture
def alter_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "alter.mdl").read_text()


@pytest.fixture
def alter_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "alter.json").read_text()


@pytest.fixture
def add_command_parser():
    return get_parser("add_command").parse


@pytest.fixture
def add_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "add.mdl").read_text()


@pytest.fixture
def add_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "add.json").read_text()


@pytest.fixture
def modify_command_parser():
    return get_parser("modify_command").parse


@pytest.fixture
def modify_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "modify.mdl").read_text()


@pytest.fixture
def modify_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "modify.json").read_text()


@pytest.fixture
def mdl_command_parser():
    return get_parser("mdl_command").parse


@pytest.fixture
def logical_operator1_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "logical_operator1.mdl").read_text()


@pytest.fixture
def logical_operator1_json(mdl_examples_dir):
    return (mdl_examples_dir / "logical_operator1.json").read_text()


@pytest.fixture
def logical_operator2_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "logical_operator2.mdl").read_text()


@pytest.fixture
def logical_operator2_json(mdl_examples_dir):
    return (mdl_examples_dir / "logical_operator2.json").read_text()


@pytest.fixture
def logical_operator3_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "logical_operator3.mdl").read_text()


@pytest.fixture
def logical_operator3_json(mdl_examples_dir):
    return (mdl_examples_dir / "logical_operator3.json").read_text()


@pytest.fixture
def validation1_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "validation.mdl").read_text()


@pytest.fixture
def validation2_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "validation2.mdl").read_text()


def test_string_attribute_value(attribute_value_parser):
    assert (
        attribute_value_parser("'This is a string, with numbers 123'")
        == "This is a string, with numbers 123"
    )


def test_empty_string_attribute_value(attribute_value_parser):
    assert attribute_value_parser("''") == ""


def test_empty_attribute_value(attribute_value_parser):
    assert attribute_value_parser("") is None


def test_boolean_attribute_value(attribute_value_parser):
    assert attribute_value_parser("true")
    assert not attribute_value_parser("false")


def test_integer_attribute_value(attribute_value_parser):
    assert attribute_value_parser("1") == 1


def test_float_attribute_value(attribute_value_parser):
    assert attribute_value_parser("1.1") == 1.1


def test_string_multi_value_attribute_value(attribute_value_parser):
    assert attribute_value_parser("'one string', 'two strings'") == [
        "one string",
        "two strings",
    ]


def test_integer_multi_value_attribute_value(attribute_value_parser):
    assert attribute_value_parser("5, 6") == [5, 6]


def test_attribute(attribute_parser):
    assert attribute_parser("my_bool_attribute(true)") == Attribute(
        "my_bool_attribute", True
    )


def test_attributes(attributes_parser):
    assert attributes_parser("my_bool_attribute(true), my_num_attribute(5)") == [
        Attribute("my_bool_attribute", True),
        Attribute("my_num_attribute", 5),
    ]


def test_attributes_comma_in_the_end(attributes_parser):
    assert attributes_parser("my_bool_attribute(true), my_num_attribute(5),") == [
        Attribute("my_bool_attribute", True),
        Attribute("my_num_attribute", 5),
    ]


def test_component(component_parser):
    assert component_parser("""Mysubcomponent my_subcomp__c (
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


@pytest.mark.parametrize("s", ["IF EXISTS", "IF NOT EXISTS"])
def test_logical_operator(s, logical_operator_parser):
    assert logical_operator_parser(s) == s


def test_components(components_parser):
    assert components_parser("""  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  ),
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
    assert components_parser("""  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  ),
        Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  ),""") == [
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
    assert create_command_parser(
        create_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(create_command_json, type=Command)


def test_create_command_optional_semicolon_in_the_end(
    create_command_parser, create_command_mdl, create_command_json
):
    assert create_command_parser(create_command_mdl) == msgspec.json.decode(
        create_command_json, type=Command
    )


def test_recreate_command(
    recreate_command_parser, recreate_command_mdl, recreate_command_json
):
    assert recreate_command_parser(
        recreate_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(recreate_command_json, type=Command)


def test_recreate_command_optional_semicolon_in_the_end(
    recreate_command_parser, recreate_command_mdl, recreate_command_json
):
    assert recreate_command_parser(recreate_command_mdl) == msgspec.json.decode(
        recreate_command_json, type=Command
    )


def test_drop_command(drop_command_parser, drop_command_mdl, drop_command_json):
    assert drop_command_parser(
        drop_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(drop_command_json, type=Command)


def test_drop_command_optional_semicolon_in_the_end(
    drop_command_parser, drop_command_mdl, drop_command_json
):
    assert drop_command_parser(drop_command_mdl) == msgspec.json.decode(
        drop_command_json, type=Command
    )


def test_rename_command(rename_command_parser, rename_command_mdl, rename_command_json):
    assert rename_command_parser(
        rename_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(rename_command_json, type=Command)


def test_rename_command_optional_semicolon_in_the_end(
    rename_command_parser, rename_command_mdl, rename_command_json
):
    assert rename_command_parser(rename_command_mdl) == msgspec.json.decode(
        rename_command_json, type=Command
    )


def test_alter_command(alter_command_parser, alter_command_mdl, alter_command_json):
    assert alter_command_parser(
        alter_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(alter_command_json, type=Command)


def test_alter_command_optional_semicolon_in_the_end(
    alter_command_parser, alter_command_mdl, alter_command_json
):
    assert alter_command_parser(alter_command_mdl) == msgspec.json.decode(
        alter_command_json, type=Command
    )


def test_add_command(add_command_parser, add_command_mdl, add_command_json):
    assert add_command_parser(add_command_mdl.removesuffix(";")) == msgspec.json.decode(
        add_command_json, type=Command
    )


def test_add_command_optional_semicolon_in_the_end(
    add_command_parser, add_command_mdl, add_command_json
):
    assert add_command_parser(add_command_mdl) == msgspec.json.decode(
        add_command_json, type=Command
    )


def test_modify_command(modify_command_parser, modify_command_mdl, modify_command_json):
    assert modify_command_parser(
        modify_command_mdl.removesuffix(";")
    ) == msgspec.json.decode(modify_command_json, type=Command)


def test_modify_command_optional_semicolon_in_the_end(
    modify_command_parser, modify_command_mdl, modify_command_json
):
    assert modify_command_parser(modify_command_mdl) == msgspec.json.decode(
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
        ("logical_operator1_mdl", "logical_operator1_json"),
        ("logical_operator2_mdl", "logical_operator2_json"),
        ("logical_operator3_mdl", "logical_operator3_json"),
    ],
)
def test_mdl_command(mdl, json, request, mdl_command_parser):
    assert mdl_command_parser(request.getfixturevalue(mdl)) == msgspec.json.decode(
        request.getfixturevalue(json), type=Command
    )


@pytest.mark.parametrize("mdl", ["validation1_mdl", "validation2_mdl"])
def test_validation(mdl, mdl_command_parser, component_metadata, request):
    assert mdl_command_parser(request.getfixturevalue(mdl)).validate(component_metadata)
