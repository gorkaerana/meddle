import json

import pytest
import msgspec

from meddle import Attribute, Component, Command
from meddle.parser import parse_and_transform, ValidationError

from conftest import path_name, scrapped_mdl_files, error_on_validation_mdl_files


@pytest.fixture
def component_metadata(root_test_dir):
    return json.loads(
        (root_test_dir.parent / "src" / "mdl" / "validation.json").read_text()
    )


@pytest.fixture
def attribute_value_parser():
    return lambda source: parse_and_transform("attribute_value", source)


@pytest.fixture
def attribute_parser():
    return lambda source: parse_and_transform("attribute", source)


@pytest.fixture
def attributes_parser():
    return lambda source: parse_and_transform("attributes", source)


@pytest.fixture
def component_parser():
    return lambda source: parse_and_transform("component", source)


@pytest.fixture
def components_parser():
    return lambda source: parse_and_transform("components", source)


@pytest.fixture
def logical_operator_parser():
    return lambda source: parse_and_transform("logical_operator", source)


@pytest.fixture
def create_command_parser():
    return lambda source: parse_and_transform("create_command", source)


@pytest.fixture
def create_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "create.mdl").read_text()


@pytest.fixture
def create_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "create.json").read_text()


@pytest.fixture
def recreate_command_parser():
    return lambda source: parse_and_transform("recreate_command", source)


@pytest.fixture
def recreate_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "recreate.mdl").read_text()


@pytest.fixture
def recreate_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "recreate.json").read_text()


@pytest.fixture
def drop_command_parser():
    return lambda source: parse_and_transform("drop_command", source)


@pytest.fixture
def drop_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "drop.mdl").read_text()


@pytest.fixture
def drop_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "drop.json").read_text()


@pytest.fixture
def rename_command_parser():
    return lambda source: parse_and_transform("rename_command", source)


@pytest.fixture
def rename_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "rename.mdl").read_text()


@pytest.fixture
def rename_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "rename.json").read_text()


@pytest.fixture
def alter_command_parser():
    return lambda source: parse_and_transform("alter_command", source)


@pytest.fixture
def alter_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "alter.mdl").read_text()


@pytest.fixture
def alter_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "alter.json").read_text()


@pytest.fixture
def add_command_parser():
    return lambda source: parse_and_transform("add_command", source)


@pytest.fixture
def add_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "add.mdl").read_text()


@pytest.fixture
def add_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "add.json").read_text()


@pytest.fixture
def modify_command_parser():
    return lambda source: parse_and_transform("modify_command", source)


@pytest.fixture
def modify_command_mdl(mdl_examples_dir):
    return (mdl_examples_dir / "modify.mdl").read_text()


@pytest.fixture
def modify_command_json(mdl_examples_dir):
    return (mdl_examples_dir / "modify.json").read_text()


@pytest.fixture
def mdl_command_parser():
    return lambda source: parse_and_transform("mdl_command", source)


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


@pytest.mark.parametrize("path", scrapped_mdl_files, ids=path_name)
def test_loads(path):
    Command.loads(path.read_text())
    assert True


@pytest.mark.parametrize(
    "path", scrapped_mdl_files - error_on_validation_mdl_files, ids=path_name
)
def test_validation(path):
    command = Command.loads(path.read_text())
    assert command.validate()


@pytest.mark.parametrize("path", error_on_validation_mdl_files, ids=path_name)
def test_error_on_validaton(path):
    with pytest.raises(ValidationError):
        Command.loads(path.read_text()).validate()


@pytest.mark.parametrize(
    "value,attribute",
    [
        (True, Attribute("active", True)),
        ("field1", Attribute("fields", ["field1", "field2"])),
        (["field1", "field2"], Attribute("fields", ["field1", "field2"])),
        (["field1", "field2"], Attribute("fields", ["field1", "field2"])),
    ],
)
def test_Attribute___contains__(value, attribute):
    assert value in attribute


@pytest.mark.parametrize(
    "value,attribute",
    [
        (["field1", "field2"], Attribute("fields", ["field1", "field2", "field3"])),
    ],
)
def test_Attribute___contains___negative(value, attribute):
    assert value not in attribute


@pytest.mark.parametrize(
    "value,component",
    [
        (
            Attribute("active", True),
            Component(
                "Accountmessage", "my_acount_message__c", [Attribute("active", True)]
            ),
        ),
        (
            Attribute("fields", ["field1", "field2"]),
            Component(
                "Accountmessage",
                "my_acount_message__c",
                [Attribute("fields", ["field1", "field2"])],
            ),
        ),
    ],
)
def test_Component___contains__(value, component):
    assert value in component


@pytest.mark.parametrize(
    "value,component",
    [
        (
            True,
            Component(
                "Accountmessage", "my_acount_message__c", [Attribute("active", True)]
            ),
        ),
        (
            1,
            Component(
                "Accountmessage", "my_acount_message__c", [Attribute("active", True)]
            ),
        ),
        (
            None,
            Component(
                "Accountmessage",
                "my_acount_message__c",
                [Attribute("fields", ["field1", "field2"])],
            ),
        ),
    ],
)
def test_Component___contains___negative(value, component):
    assert value not in component


@pytest.mark.parametrize(
    "value,component",
    [
        (
            Attribute("active", True),
            Command(
                "ALTER",
                "Accountmessage",
                "my_acount_message__c",
                [Attribute("active", True)],
                [
                    Component(
                        "Accountmessage",
                        "my_acount_message__c",
                        [Attribute("active", True)],
                    )
                ],
                [
                    Command(
                        "RENAME",
                        "Accountmessage",
                        "my_account_message__c",
                        to_component_name="your_account_message__c",
                    )
                ],
            ),
        ),
        (
            Component(
                "Accountmessage", "my_acount_message__c", [Attribute("active", True)]
            ),
            Command(
                "ALTER",
                "Accountmessage",
                "my_acount_message__c",
                [Attribute("active", True)],
                [
                    Component(
                        "Accountmessage",
                        "my_acount_message__c",
                        [Attribute("active", True)],
                    )
                ],
                [
                    Command(
                        "RENAME",
                        "Accountmessage",
                        "my_account_message__c",
                        to_component_name="your_account_message__c",
                    )
                ],
            ),
        ),
        (
            Command(
                "RENAME",
                "Accountmessage",
                "my_account_message__c",
                to_component_name="your_account_message__c",
            ),
            Command(
                "ALTER",
                "Accountmessage",
                "my_acount_message__c",
                [Attribute("active", True)],
                [
                    Component(
                        "Accountmessage",
                        "my_acount_message__c",
                        [Attribute("active", True)],
                    )
                ],
                [
                    Command(
                        "RENAME",
                        "Accountmessage",
                        "my_account_message__c",
                        to_component_name="your_account_message__c",
                    )
                ],
            ),
        ),
    ],
)
def test_Command___contains__(value, component):
    assert value in component


@pytest.mark.parametrize(
    "value,component",
    [
        (
            True,
            Component(
                "Accountmessage", "my_acount_message__c", [Attribute("active", True)]
            ),
        ),
        (
            1,
            Component(
                "Accountmessage", "my_acount_message__c", [Attribute("active", True)]
            ),
        ),
        (
            None,
            Component(
                "Accountmessage",
                "my_acount_message__c",
                [Attribute("fields", ["field1", "field2"])],
            ),
        ),
    ],
)
def test_Command___contains___negative(value, component):
    assert value not in component
