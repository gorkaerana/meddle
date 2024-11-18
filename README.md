# meddle

`meddle` is a Python library to read, write, manipulate, manage, and validate [Veeva Vault MDL](https://developer.veevavault.com/mdl/#mdl-overview).

## Table of contents
- [Recipes](#recipes)
  - [Reading](#reading)
  - [Comparing](#comparing)
  - [Manipulating](#manipulating)
  - [Writing](#writing)
  - [Validating](#validating)
- [Limitations](#limitations)
  - [Unsupported data types](#unsupported-data-types)
  - [Validation](#validation)

## Recipes
### Reading
E.g., given a MDL command from [Veeva's own documentation](https://developer.veevavault.com/mdl/#step-1-create-a-picklist), we can load it into `meddle.Command` as below

```python
from rich.pretty import pprint as rpprint

from meddle import Command

# From https://developer.veevavault.com/mdl/#step-1-create-a-picklist
recreate_command = Command.loads(
    """RECREATE Picklist vmdl_options__c (
label('vMDL Options'),
active(true),
Picklistentry hello_world__c(
  value('hello world'),
  order(0),
  active(true)
)
);"""
)
rpprint(recreate_command)
```

which yields

```bash
Command(
│   command='RECREATE',
│   component_type_name='Picklist',
│   component_name='vmdl_options__c',
│   attributes=[Attribute(name='label', value='vMDL Options', command=None), Attribute(name='active', value=True, command=None)],
│   components=[
│   │   Component(
│   │   │   component_type_name='Picklistentry',
│   │   │   component_name='hello_world__c',
│   │   │   attributes=[Attribute(name='value', value='hello world', command=None), Attribute(name='order', value=0, command=None), Attribute(name='active', value=True, command=None)]
│   │   )
│   ],
│   commands=None,
│   to_component_name=None,
│   logical_operator=None
)
```

### Comparing

Building upon the previous example, load a second MDL command [from Veeva's documentation](https://developer.veevavault.com/mdl/#step-4-alter-the-object-and-picklist)

```python
# From https://developer.veevavault.com/mdl/#step-4-alter-the-object-and-picklist
# The closing comma of subcommand `MODIFY` had to be corrected to a semicolon, 
# since Veeva clashes with its own documentation.
alter_command = Command.loads(
    """ALTER Picklist vmdl_options__c (
label('vMDL Options'),
MODIFY Picklistentry hello_world__c(
  value('Hello World.'),
  order(0)
);
ADD Picklistentry hello_worldv2__c(
  value('ENTER ANY VALUE'),
  order(1),
  active(true)
)
);"""
)
```

and compare not only the `meddle.Command` objects but `meddle.Attribute`'s and `meddle.Component`'s too

```python
assert recreate_command != alter_command
assert (recreate_command == recreate_command) and (alter_command == alter_command)
assert recreate_command.attributes[0] == alter_command.attributes[0]
assert (
    recreate_command.components[0].attributes[2]
    == alter_command.commands[1].attributes[2]
)
```

### Manipulating
For the sake of not messing with any previous progress, let's copy `recreate_command` and `alter_command`.

```python
from copy import deepcopy

recreate_command_copy = deepcopy(recreate_command)
alter_command_copy = deepcopy(alter_command)
assert recreate_command_copy == recreate_command
assert alter_command_copy == alter_command
```

Say we are only interested in 

- Attribute `label` of `recreate_command`--the line containing `label('vMDL Options')`.
- Attribute `label` of `alter_command`--the line also containing `label('vMDL Options')`.
- attribute `value` within the `MODIFY` subcommand of `alter_command`--the line containing `value('Hello World.')`.

We can manually delete any entries we are not interested in
```python
del recreate_command_copy.components[0]
del recreate_command_copy.attributes[1]

del alter_command_copy.commands[0].attributes[-1]
del alter_command_copy.commands[-1]

assert recreate_command_copy != recreate_command
assert alter_command_copy != alter_command
```

Alternatively, and perhaps in a more programmable way

```python
recreate_command_copy.attributes = [
	attr for attr in recreate_command.attributes if attr.name == "label"
]
recreate_command_copy.components = []

alter_command_copy.commands = [
    cmd
    for cmd in alter_command.commands
    if cmd.command == "MODIFY" and cmd.component_type_name == "Picklistentry"
]
alter_command_copy.commands[0].attributes = [
    attr for attr in alter_command_copy.attributes if attr.name == "value"
]

assert recreate_command_copy != recreate_command
assert alter_command_copy != alter_command
```

### Writing
If we wanted to write our modified commands

```python
print(recreate_command_copy.dumps())
print()
print(alter_command_copy.dumps())
```

results in 

```bash
RECREATE Picklist vmdl_options__c (
    label('vMDL Options'),
);

ALTER Picklist vmdl_options__c (
    label('vMDL Options'),
    MODIFY Picklistentry hello_world__c (
        value('Hello World.'),
        order(0),
    );
    ADD Picklistentry hello_worldv2__c (
        value('ENTER ANY VALUE'),
        order(1),
    );
);
```

### Validating
Veeva has [very detailed documentation](https://developer.veevavault.com/mdl/components/) on the component types for Veeva MDL files, the attributes and other component types allowed within them; together with the attribute value data types and other restrictions. `meddle` scrapes this information and offers validation based on it via `Attribute.validate`, `Component.validate`, and `Command.validate`.

Building upon the above examples, every single one of our commands is valid

```python
assert recreate_command.validate()
assert alter_command.validate()
assert recreate_command_copy.validate()
assert alter_command_copy.validate()
```

Now if we were to were to create a invalid commands, this would be flagged. E.g. let's create two commands using the `Picklist` component's `label` attribute, the value of which ought to be a string of maximum length 40, [as per the Veeva documentation](https://developer.veevavault.com/mdl/components/#picklist). Now, we are not upstanding citizens of the Veeva platform, and so we craft two MDL commands:
- the first one provides a string for `label` under `Picklist` longer than 40 characters,
- the second one provides an integer for `label` under `Picklist`.

```python
from meddle import Attribute
from meddle.validation import ValidationError

# The command is not relevant for the purposes of this example, hence why it changes
# between the following two examples
try:
    Command(
        command="RECREATE",
        component_type_name="Picklist",
        component_name="vmdml_options__c",
        attributes=[
            Attribute(
                "label",
                "This is a long string longer than the maximum allowed length of 40",
            )
        ],
    ).validate()
except ValidationError as e:
	print(f"Ooopsie #1: {e}")

try:
    Command(
        command="ALTER",
        component_type_name="Picklist",
        component_name="vmdml_options__c",
        attributes=[Attribute("label", 1)],
    ).validate()
except ValidationError as e: 
	print(f"Ooopsie #2: {e}")
```

`meddle` conveniently raises this issues for us.

```bash
Ooopsie #1: Attribute 'label' is constrained to maximum length 40. Got 'This is a long string longer than the maximum allowed length of 40'.
Ooopsie #2: Attribute 'label' ought to be of type 'String'. Got 1 which is of type <class 'int'>.
```

## Limitations

### Unsupported data types
`meddle` does not support [`SdkCode` and `Expression` attribute data types](https://developer.veevavault.com/mdl/#attributes-data-types), since no meaningful real world examples against which to test the tool could be found. More specifically:

- The attributes (and corresponding components) with `SdkCode` data type are listed in the below table. No real world usage of any of them could be found.

| Component name | Attribute name |
|---|---|
| `Customwebapi` | `source_code` |
| `Documentaction` | `source_code` |
| `Emailprocessor` | `source_code` |
| `Messagedeliveryeventhandler` | `source_code` |
| `Messageprocessor` | `source_code` |
| `Recordaction` | `source_code` |
| `Recordmergeeventhandler` | `source_code` |
| `Recordroletrigger` | `source_code` |
| `Recordtrigger` | `source_code` |
| `Recordworkflowaction` | `source_code` |
| `Sdkjob` | `source_code` |
| `Userdefinedclass` | `source_code` |
| `Userdefinedmodel` | `source_code` |
| `Userdefinedservice` | `source_code` |

- The attributes (and corresponding components) with `Expression` data type are listed in the below table. Real world usage examples could be found for only two of them:
  - `formula` in [KANBAN-BOARD-CONFIG.vpk](https://github.com/veeva/Vault-Kanban-Board/blob/main/KANBAN-BOARD-CONFIG.vpk), which counters Veeva's documentation and does not enclose the attribute value in square brackets. See also [the scraped file](tests/mdl_examples/scrapped/KANBAN-BOARD-CONFIG/Object.access_request__c.mdl).
  - `relationship_criteria` which has plenty of usage (as a quick grep in `tests/mdl_examples/scrapped` will show) but the attribute value is empty for every case.

| Component name | Attribute name |
|---|---|
| `Docfield` | `formula` |
| `Queryobjectrule` | `filter_clause` |
| `Job` | `trigger_date` |
| `Field` | `relationship_criteria` |
| `Typefield` | `relationship_criteria` |
| `Sharingrule` | `criteria` |

### Validation
Some of the MDL examples available online disagree with Veeva's documentation, as per the below table. In such cases, `meddle.validation` follows the documentation.
| Source (in this repo) | Source (URL) | Reason |
|---|---|---|
| [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](tests/mdl_examples/scrapped/Base_vsdk-document-sample-components/Doclifecycle.vsdk_document_lifecycle__c.mdl) | [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](https://api.github.com/repos/veeva/vsdk-document-sample/git/blobs/15ccd5244ddf93a7dfa32e6828d1e06fbd235127) | Attribute name `overlay` is not allowed under component type `Doclifecyclestate`. Options are: `label`, `active`, `description`, `order`, `cancel_state`, `skip_cancel_state`, `entry_criteria`, `entry_action`, `user_action`, `security_settings`. |
| [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](tests/mdl_examples/scrapped/Clinical_vsdk-document-sample-components/Doclifecycle.vsdk_document_lifecycle__c.mdl) | [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](https://api.github.com/repos/veeva/vsdk-document-sample/git/blobs/01e842cb1e100da154151a117f655d66ceffb85a) | Attribute name `overlay` is not allowed under component type `Doclifecyclestate`. Options are: `label`, `active`, `description`, `order`, `cancel_state`, `skip_cancel_state`, `entry_criteria`, `entry_action`, `user_action`, `security_settings`. |
| [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](tests/mdl_examples/scrapped/Multichannel_vsdk-document-sample-components/Doclifecycle.vsdk_document_lifecycle__c.mdl) | [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](https://api.github.com/repos/veeva/vsdk-document-sample/git/blobs/8cff63bbf1050f8e1e58ef0a9f16acf9d98afb37) | Attribute name `overlay` is not allowed under component type `Doclifecyclestate`. Options are: `label`, `active`, `description`, `order`, `cancel_state`, `skip_cancel_state`, `entry_criteria`, `entry_action`, `user_action`, `security_settings`. |
| [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](tests/mdl_examples/scrapped/Quality_vsdk-document-sample-components/Doclifecycle.vsdk_document_lifecycle__c.mdl) | [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](https://api.github.com/repos/veeva/vsdk-document-sample/git/blobs/a67a32929015d2055f1ba9ade31aef4b53b80cad) | Attribute name `overlay` is not allowed under component type `Doclifecyclestate`. Options are: `label`, `active`, `description`, `order`, `cancel_state`, `skip_cancel_state`, `entry_criteria`, `entry_action`, `user_action`, `security_settings`. |
| [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](tests/mdl_examples/scrapped/RIM_vsdk-document-sample-components/Doclifecycle.vsdk_document_lifecycle__c.mdl) | [`Doclifecycle.vsdk_document_lifecycle__c.mdl`](https://api.github.com/repos/veeva/vsdk-document-sample/git/blobs/a77d8e0f82c21c6fd49f57e85fe4ec81566ea931) | Attribute name `overlay` is not allowed under component type `Doclifecyclestate`. Options are: `label`, `active`, `description`, `order`, `cancel_state`, `skip_cancel_state`, `entry_criteria`, `entry_action`, `user_action`, `security_settings`. |

| [`Object.vsdk_create_product_application__c.mdl`](tests/mdl_examples/scrapped/Vault-Java-SDK-Common-Services-Sample/Object.vsdk_create_product_application__c.mdl) | [`Object.vsdk_create_product_application__c.mdl`](https://api.github.com/repos/veeva/vsdk-common-services-sample/git/blobs/31ab1fbc19a6f5da946e5b4245b75c629e0c78f5) | Attribute `data_store` is an enum with allowed values `standard`, `raw`. Got `high_volume`. |
| [`Object.vsdk_product_application__c.mdl`](tests/mdl_examples/scrapped/Vault-Java-SDK-Common-Services-Sample/Object.vsdk_product_application__c.mdl) | [`Object.vsdk_product_application__c.mdl`](https://api.github.com/repos/veeva/vsdk-common-services-sample/git/blobs/31ab1fbc19a6f5da946e5b4245b75c629e0c78f5) | Attribute `data_store` is an enum with allowed values `standard`, `raw`. Got `high_volume`. |
| [`Object.vsdk_setting__c.mdl`](tests/mdl_examples/scrapped/vsdk-user-defined-model-sample-components/Object.vsdk_setting__c.mdl) | [`Object.vsdk_setting__c.mdl`](https://api.github.com/repos/veeva/vsdk-user-defined-model-sample/git/blobs/50fce60d9ccf40912b18dcd238baa2fe9bc9ef22) | Attribute `data_store` is an enum with allowed values `standard`, `raw`. Got `high_volume`. |
