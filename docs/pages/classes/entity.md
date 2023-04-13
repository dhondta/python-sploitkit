In order to provide a convenient API, Sploitkit defines a central class aimed to declare everything that can be tuned and imported to make a new CLI framework. As explained previously, this central class is called `Entity`. This holds the generic logic, namely for :

- registering entity classes (see hereafter: `Console`, `Command`, ...)
- handling requirements, dynamically enabling/disabling entities
- handling metadata (formatting them for display in the CLI)

## Requirements and applicability

Requirements can be defined in order to dynamically enable/disable entities. These are managed through the `requirements` class attribute. Currently, a few requirement types exist :

**Key** | **Description**
--- | ---
`config` | Dictionary of `Config`/`Option` values to be set (see hereafter).
`file` | List of files that must exist in the current workspace.
`python` | List of Python packages required to be installed in the environment.
`state` | State variables to be set in the *Global State* (see section *Console*) ; can be defined in three ways : <br><ol><li>List of existing keys, e.g. `['VAR1', 'VAR2']`.</li><li>Dictionary of state variables (exact match), e.g. `{'VAR1': {'key1':'myval1', 'key2':'myval2'}}`.</li><li>Dictionary of state values, regardless of the key, e.g. `{'VAR1': {None:'myval1'}}`.</li></ol>
`system` | List of system tools and/or packages to be installed ; can be defined in two ways : <br><ol><li>`[tool]`, e.g. `ifconfig` ; if the system command is missing, it will only tell that this tool is not present.</li><li>`[package]/[tool]`, e.g. `net-tools/ifconfig` ; this allows to be more precise regarding what is missing.</li></ol>

In parallel with the requirements, the applicability is checked, that is, if the entity has a reference with a value that exactly matches the expected one.

??? example "**Example**: Setting a *command* as applicable only for *modules* named '`do_something`'"

    Let us consider defining a *command* that only applies to any *module* whose name is "`do_something`". Then defining the `applies_to` attribute like hereafter allows to limit the scope of the *command* to only *modules* named so.

        :::python
        class DoIt(Command):
            applies_to = [("console", "module", "name", "do_something")]
            [...]
            def run(self):
                [...]

<br>

## Inheritance and aggregation

Entities can be defined in subclasses as a tree structure so that the leaves share some information from their proxy subclasses. The precedence goes bottom-up, that is, from the leaves to the entity classes. This is especially the case for :

- `config` attribute (applies to *consoles* and *modules*) : Configurations are agreggated (in a `ProxyConfig` instance) so that an option that is common to multiple entities can be defined only once and modified for all these entities at once during the execution.
- Metadata (especially useful for *modules*) : metadata is aggregated (during entity import only) so that, if multiple modules inheriting from a proxy class have, for instance, the same author, this data can be declared only once in the proxy class and applied to *modules*.

## Metadata parsing

Metadata of entities can be defined in three different ways (can be combined, listed hereafter in inverse order of precedence) :

1. Docstring : By default, Sploitkit provides a parsing function that follows the convention presented hereafter, resulting in a dictionary of metadata key-values. However, a custom parsing function can be input as an argument when instantiating a parent `Console`.
2. `meta` attribute : A dictionary of metadata key-values that will update the final metadata dictionary.
3. `metadata` attribute : Same as for `meta` (exists for a question of cross-compatibility with plugins of other frameworks).

This leads to a `_metadata` class attribute holding the metadata dictionary. Note that, when `meta` and `metadata` class attributes are use to update `_metadata`, they are removed to only hold this last one. This is mostly a question of compatibility with modules of other frameworks (e.g. Recon-ng).

Options can even be defined through the `meta` and/or `metadata` class attributes (but NOT directly `_metadata` as it is created/overwritten when parsing the docstring). Their format follows this convention : (*name*, *default_value*, *required*, *description*). It contains less fields than what is really supported (see the `Option` class in the next subsection) but, once again, it is mostly a question of compatibility with modules from other frameworks.

The default docstring format (parsed through a dedicated function within Sploitkit's utils) consists of sections separated by double newlines. Parsing occurs as follows :

1. The first section is always the *description*.
2. Next sections are handled this way :

    - If the first line of the section follows the convention hereafter, it is parsed as a separated field (saved in the metadata dictionary as lowercase) up to the next field-value OR section's end.
    
            [Field]: [value]
         
        That is, the field name capitalized with no whitespace before the colon and whatever value, multiline.
         
    - If the first line of the section does not follow the convention, it is parsed as a *comment* and saved into the *comments* list of the metadata dictionary. Note that using the field name *comments* append the value to the *comments* list of the metadata dictionary.

??? example "**Example**: Writing a docstring for an entity"
    
        :::python
        class Example(object):
            \"""
            This is a test multi-line long 
             description.

            This is a first comment.

            Author: John Doe
                     (john.doe@example.com)
            Version: 1.0
            Comments:
            - subcomment 1
            - subcomment 2

            Something: lorem ipsum
                        paragraph

            This is a second comment,
             a multi-line one.
            \"""
            [...]
        
        >>> parse_docstring(Example)
        {'author': 'John Doe (john.doe@example.com)',
         'comments': ['This is a first comment.',
                      ('subcomment 1', 'subcomment 2'),
                      'This is a second comment, a multi-line one.'],
         'description': 'This is a test multi-line long description.',
         'something': 'lorem ipsum paragraph',
         'version': '1.0'}

<br>

## `Config` and `Option`

A configuration object is an instance of the `Config` class subclassing the common type `dict` and refining its capabilities to handle special key-value objects called `Option`'s that also have a description and other attributes (e.g. `required`). This way, it is easier to associate more data than simply a value to a key, i.e. when it comes to providing help text about the option.

A configuration is declared by providing a dictionary as the only positional argument and/or key-values as keyword-arguments. It is important to note that, if options are defined with the keyword-arguments, they won't of course have any other data defined but they will be easilly accessible for further tuning.

??? example "**Example**: Declaring a configuration (entity class attribute)"

        :::python
        from sploitkit import Config, Option, ROption
        
        config = Config({
            Option(...),
            ROption(...),
        })

<br>

!!! note "`Option` and `ROption`"
    
    Two types of option exist (for a question of performance) : `Option` (the normal one) and `ROption` (aka *Resetting Option*) that triggers resetting the entity bindings (e.g. the commands applicability to the current console given the new option). So, beware that, when using the `Option` class, the modification of its value does not update bindings between entities.
    
    An example of use of the behavior of `ROption` is when a `config` requirement is used in another entity which is to be enabled/disabled according to option's value. This way, entity bindings are reset when tuning the option like when starting a console (for more details on this, see section *Console*).

A configuration option object, that is, an instance of the `Option` or `ROption` class, is defined using multiple arguments :

**Argument** | **Type** | **Default** | **Description**
--- | :---: | :---: | ---
`name` | `str` |  | option's name, conventionally uppercase
`description` | `str` | `None` | help text for this option
`required` | `bool` | `False` | whether it shall be defined or not
`choices` | `list`/`lambda` | `None` | the possible values (as a list or lazily defined through a lambda function that outputs a list), used for validation ; its value can also be `bool` (the type, not as a string !) for setting choices to false and true
`set_callback` | `lambda` | `None` | a function that is triggered after setting the value
`unset_callback` | `lambda` | `None` | a function that is triggered after unsetting the value
`transform` | `lambda` | `None` | a function transforming the value input as for any dictionary, but for computing a new value
`validate` | `lambda` | `None` | by default, a lambda function that checks for the given `choices` if defined, but can be tuned accordingly

Each lambda function takes `self` as the first argument. `transform` and `validate` also takes option's value as the second argument.

??? example "Config declaration (extract from the `FrameworkConsole` class)"

        :::python
        config = Config({
            ...,
            ROption(
                'DEBUG',
                "debug mode",
                False,
                bool,
                set_callback=lambda o: o.config.console._set_logging(o.value),
            ): "false",
            ...,
            Option(
                'WORKSPACE',
                "folder where results are saved",
                True,
            ): "~/Notes",
        })

<br>

## Utility class methods


