from operator import attrgetter
from pathlib import Path

import pytest


path_name = attrgetter("name")

here = Path(__file__).parent
scrapped_mdl_dir = here / "mdl_examples" / "scrapped"
scrapped_mdl_files = set(sorted(scrapped_mdl_dir.rglob("*.mdl"), key=path_name))
error_on_validation_mdl_files = {
    p
    for p in scrapped_mdl_files
    if path_name(p)
    in {
        "Doclifecycle.vsdk_document_lifecycle__c.mdl",
        "Object.vsdk_create_product_application__c.mdl",
        "Object.vsdk_product_application__c.mdl",
        "Object.vsdk_setting__c.mdl",
    }
}


@pytest.fixture
def root_test_dir():
    return here


@pytest.fixture
def mdl_examples_dir(root_test_dir):
    return root_test_dir / "mdl_examples"
