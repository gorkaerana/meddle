# TODO: note that "ADD" and "MODIFY" commands in the Veeva MDL documentation
# example have wrong ending delimiter comma instead of semicolon
# TODO: test 'alter_subcommand' and 'alter_subcommands' rules
# TODO: test all grammar rules
from pathlib import Path

from lark import Lark
import pytest

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
def recreate_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="recreate_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def drop_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="drop_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def rename_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="rename_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def alter_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="alter_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def add_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="add_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


@pytest.fixture
def modify_command_parser(mdl_grammar):
    return Lark(
        grammar=mdl_grammar,
        start="modify_command",
        parser="lalr",
        transformer=MdlTreeTransformer(visit_tokens=True),
    )


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


def test_create_command(create_command_parser):
    assert create_command_parser.parse("""CREATE Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),

  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )
)""") == Command(
        command="CREATE",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
        ],
        components=[
            Component(
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
            )
        ],
        commands=None,
        to_component_name=None,
    )


def test_create_command_optional_semicolon_in_the_end(create_command_parser):
    assert create_command_parser.parse("""CREATE Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),

  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )
);""") == Command(
        command="CREATE",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
        ],
        components=[
            Component(
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
            )
        ],
        commands=None,
        to_component_name=None,
    )


def test_recreate_command(recreate_command_parser):
    assert recreate_command_parser.parse("""RECREATE Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),

  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )
)""") == Command(
        command="RECREATE",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
        ],
        components=[
            Component(
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
            )
        ],
        commands=None,
        to_component_name=None,
    )


def test_recreate_command_optional_semicolon_in_the_end(recreate_command_parser):
    assert recreate_command_parser.parse("""RECREATE Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),

  Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )
);""") == Command(
        command="RECREATE",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
        ],
        components=[
            Component(
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
            )
        ],
        commands=None,
        to_component_name=None,
    )


def test_drop_command(drop_command_parser):
    assert drop_command_parser.parse("DROP Mycomponent my_comp__c") == Command(
        command="DROP",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=None,
        components=None,
        commands=None,
        to_component_name=None,
    )


def test_drop_command_optional_semicolon_in_the_end(drop_command_parser):
    assert drop_command_parser.parse("DROP Mycomponent my_comp__c;") == Command(
        command="DROP",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=None,
        components=None,
        commands=None,
        to_component_name=None,
    )


def test_rename_command(rename_command_parser):
    assert rename_command_parser.parse(
        "RENAME Mycomponent my_comp__c TO my_new_comp__c"
    ) == Command(
        command="RENAME",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=None,
        components=None,
        commands=None,
        to_component_name="my_new_comp__c",
    )


def test_rename_command_optional_semicolon_in_the_end(rename_command_parser):
    assert rename_command_parser.parse(
        "RENAME Mycomponent my_comp__c TO my_new_comp__c;"
    ) == Command(
        command="RENAME",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=None,
        components=None,
        commands=None,
        to_component_name="my_new_comp__c",
    )


def test_alter_command(alter_command_parser):
    assert alter_command_parser.parse("""ALTER Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),
  my_multi_value_attribute ADD (5, 6),
  my_multi_value_attribute DROP (8),

  ADD Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );
  DROP Mysubcomponent my_subcomp2__c;

MODIFY Mysubcomponent my_subcomp3__c (
    my_bool_attribute(true),
    my_num_attribute(7)
  );

  RENAME Mysubcomponent my_subcomp4__c TO my_subcomp5__c;
);
""") == Command(
        command="ALTER",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
            Attribute(name="my_multi_value_attribute", value=[5, 6], command="ADD"),
            Attribute(name="my_multi_value_attribute", value=8, command="DROP"),
        ],
        components=None,
        commands=[
            Command(
                command="ADD",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="DROP",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp2__c",
                attributes=None,
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="MODIFY",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp3__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=7, command=None),
                ],
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="RENAME",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp4__c",
                attributes=None,
                components=None,
                commands=None,
                to_component_name="my_subcomp5__c",
            ),
        ],
        to_component_name=None,
    )


def test_alter_command_optional_semicolon_in_the_end(alter_command_parser):
    assert alter_command_parser.parse("""ALTER Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),
  my_multi_value_attribute ADD (5, 6),
  my_multi_value_attribute DROP (8),

  ADD Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );
  DROP Mysubcomponent my_subcomp2__c;

MODIFY Mysubcomponent my_subcomp3__c (
    my_bool_attribute(true),
    my_num_attribute(7)
  );

  RENAME Mysubcomponent my_subcomp4__c TO my_subcomp5__c;
);
""") == Command(
        command="ALTER",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
            Attribute(name="my_multi_value_attribute", value=[5, 6], command="ADD"),
            Attribute(name="my_multi_value_attribute", value=8, command="DROP"),
        ],
        components=None,
        commands=[
            Command(
                command="ADD",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="DROP",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp2__c",
                attributes=None,
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="MODIFY",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp3__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=7, command=None),
                ],
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="RENAME",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp4__c",
                attributes=None,
                components=None,
                commands=None,
                to_component_name="my_subcomp5__c",
            ),
        ],
        to_component_name=None,
    )


def test_add_command(add_command_parser):
    assert add_command_parser.parse("""ADD Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  )""") == Command(
        command="ADD",
        component_type_name="Mysubcomponent",
        component_name="my_subcomp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
        ],
        components=None,
        commands=None,
        to_component_name=None,
    )


def test_add_command_optional_semicolon_in_the_end(add_command_parser):
    assert add_command_parser.parse("""ADD Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );""") == Command(
        command="ADD",
        component_type_name="Mysubcomponent",
        component_name="my_subcomp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
        ],
        components=None,
        commands=None,
        to_component_name=None,
    )


def test_modify_command(modify_command_parser):
    assert modify_command_parser.parse("""MODIFY Mysubcomponent my_subcomp3__c (
    my_bool_attribute(true),
    my_num_attribute(7)
  )""") == Command(
        command="MODIFY",
        component_type_name="Mysubcomponent",
        component_name="my_subcomp3__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=7, command=None),
        ],
        components=None,
        commands=None,
        to_component_name=None,
    )


def test_modify_command_optional_semicolon_in_the_end(modify_command_parser):
    assert modify_command_parser.parse("""MODIFY Mysubcomponent my_subcomp3__c (
    my_bool_attribute(true),
    my_num_attribute(7)
  );""") == Command(
        command="MODIFY",
        component_type_name="Mysubcomponent",
        component_name="my_subcomp3__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=7, command=None),
        ],
        components=None,
        commands=None,
        to_component_name=None,
    )


def test_mdl_command(mdl_command_parser):
    assert mdl_command_parser.parse("""ALTER Mycomponent my_comp__c (
  my_bool_attribute(true),
  my_num_attribute(5),
  my_multi_value_attribute ADD (5, 6),
  my_multi_value_attribute DROP (8),

  ADD Mysubcomponent my_subcomp__c (
    my_bool_attribute(true),
    my_num_attribute(5)
  );
  DROP Mysubcomponent my_subcomp2__c;

MODIFY Mysubcomponent my_subcomp3__c (
    my_bool_attribute(true),
    my_num_attribute(7)
  );

  RENAME Mysubcomponent my_subcomp4__c TO my_subcomp5__c;
);
""") == Command(
        command="ALTER",
        component_type_name="Mycomponent",
        component_name="my_comp__c",
        attributes=[
            Attribute(name="my_bool_attribute", value=True, command=None),
            Attribute(name="my_num_attribute", value=5, command=None),
            Attribute(name="my_multi_value_attribute", value=[5, 6], command="ADD"),
            Attribute(name="my_multi_value_attribute", value=8, command="DROP"),
        ],
        components=None,
        commands=[
            Command(
                command="ADD",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=5, command=None),
                ],
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="DROP",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp2__c",
                attributes=None,
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="MODIFY",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp3__c",
                attributes=[
                    Attribute(name="my_bool_attribute", value=True, command=None),
                    Attribute(name="my_num_attribute", value=7, command=None),
                ],
                components=None,
                commands=None,
                to_component_name=None,
            ),
            Command(
                command="RENAME",
                component_type_name="Mysubcomponent",
                component_name="my_subcomp4__c",
                attributes=None,
                components=None,
                commands=None,
                to_component_name="my_subcomp5__c",
            ),
        ],
        to_component_name=None,
    )
