# meddle

`meddle` is a Python library to read, write, manipulate, manage, and validate [Veeva Vault MDL](https://developer.veevavault.com/mdl/#mdl-overview).

## Tutorial
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

yields

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
# since Veeva contradicts its own documentation.
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

- attribute `label` of `recreate_command`,
- attribute `label` of `alter_command`, and
- attribute `value` within the `MODIFY` subcommand of `alter_command`.

```python
del recreate_command_copy.components[0]
del recreate_command_copy.attributes[1]
rpprint(recreate_command_copy)

del alter_command_copy.commands[0].attributes[-1]
del alter_command_copy.commands[-1]
rpprint(recreate_command_copy)
```

### Writing
If we wanted to write our modified commands

```python
print(recreate_command_copy)
print()
print(alter_command_copy)
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
except ValidationError:
	print(f"Ooopsie #2: {e}")
```

`meddle` very raises this issues for us.

```bash
Ooopsie #1: Attribute 'label' is constrained to maximum length 40. Got 'This is a long string longer than the maximum allowed length of 40'.
Ooopsie #2: Attribute 'label' ought to be of type 'String'. Got 1 which is of type <class 'int'>.
```
