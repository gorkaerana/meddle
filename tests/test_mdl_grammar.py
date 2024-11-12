from lark.load_grammar import load_grammar, Grammar
import pytest


@pytest.fixture
def rule_definitions():
    return [
        "add",
        "add_command",
        "alter_attribute",
        "alter_attributes",
        "alter_command",
        "alter_subcommand",
        "alter_subcommands",
        "attribute",
        "attribute_name",
        "attribute_value",
        "attributes",
        "boolean",
        "component",
        "component_name",
        "component_type_name",
        "components",
        "create_command",
        "drop",
        "drop_command",
        "false",
        "if_exists",
        "if_not_exists",
        "logical_operator",
        "mdl_command",
        "modify_command",
        "number",
        "recreate_command",
        "rename_command",
        "string",
        "true",
        "value",
        "xml",
    ]


@pytest.fixture
def term_definitions():
    return ["DECIMAL", "INT", "WS", "WS_INLINE"]


@pytest.fixture
def mdl_grammar_path(root_test_dir):
    return root_test_dir.parent / "src" / "mdl" / "mdl_grammar.lark"


@pytest.fixture
def grammar(mdl_grammar_path) -> Grammar:
    return load_grammar(mdl_grammar_path.read_text(), "<?>", False, None)[0]


def test_rule_definitions(grammar, rule_definitions):
    assert sorted(td[0] for td in grammar.rule_defs) == rule_definitions


def test_term_definitions(grammar, term_definitions):
    assert sorted(td[0] for td in grammar.term_defs) == term_definitions
