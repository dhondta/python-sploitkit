In order to provide a convenient API, Sploitkit defines a central class aimed to declare everything that can be tuned and imported to make a new CLI framework. As explained previously, this central class is called `Entity`. This holds the generic logic, namely for :

- registering entity classes (see hereafter: `Console`, `Command`, ...)
- handling requirements, dynamically enabling/disabling entities
- handling metadata (formatting them for display in the CLI)

### Requirements handling

Requirements can be defined in order to dynamically enable/disable entities. These are managed through the `requirements` class attribute. Currently, a few requirement types exist :

- `config` : Dictionary of `Config`/`Option` values to be set (see hereafter).
- `file` : List of files that must exist in the current workspace.
- `python` : List of Python packages required to be installed in the environment.
- `state` : State variables to be set in the *Global State* (see section *Console*) ; can be defined in three ways :

    1. List of existing keys, e.g. `['VAR1', 'VAR2']`.
    2. Dictionary of state variables (exact match), e.g. `{'VAR1': {'key1':'myval1', 'key2':'myval2'}}`.
    3. Dictionary of state values, regardless of the key, e.g. `{'VAR1': {None:'myval1'}}`.

- `system` : List of system tools and/or packages to be installed ; can be defined in two ways :

    1. `[tool]`, e.g. `ifconfig` ; if the system command is missing, it will only tell that this tool is not present.
    2. `[package]/[tool]`, e.g. `net-tools/ifconfig` ; this allows to be more precise regarding what is missing.

### Inheritance and aggregation

Entities can be defined in subclasses as a tree structure so that the leaves share some information from their proxy subclasses. The precedence goes bottom-up, that is, from the leaves to the entity classes. This is especially the case for :

- `config` attribute (applies to *consoles* and *modules*) : Configurations are agreggated (in a `ProxyConfig` instance) so that an option that is common to multiple entities can be defined only once and modified for all these entities at once during the execution.
- Metadata (especially useful for *modules*) : metadata is aggregated (during entity import only) so that, if multiple modules inheriting from a proxy class have, for instance, the same author, this data can be declared only once in the proxy class and applied to *modules*.

### `Config` and `Option`

A configuration object is an instance of the `Config` class subclassing the common type `dict` and refining its capabilities to handle special key-value objects called `Option`'s that also have a description and other attributes (e.g. `required`). This way, it is easier to associate more data than simply a value to a key, i.e. when it comes to providing help text about the option.

A configuration is declared by providing a dictionary as the only positional argument and/or key-values as keyword-arguments. It is important to note that, if options are defined with the keyword-arguments, they won't of course have any other data defined but they will be easilly accessible for further tuning.

??? example 

        :::python
        from sploitkit import Config, Option, ROption
        
        config = Config({
            Option(...),
            ROption(...),
        })

!!! note "`Option` and `ROption`"
    
    Two types of option exist (for a question of performance) : `Option` (the normal one) and `ROption` (aka *Resetting Option*) that triggers resetting the entity bindings (e.g. the commands applicability to the current console given the new option). So, beware that, when using the `Option` class, the modification of its value does not update bindings between entities.
    
    An example of use of the behavior of `ROption` is when a `config` requirement is used in another entity which is to be enabled/disabled according to option's value. This way, entity bindings are reset when tuning the option like when starting a console (for more details on this, see section *Console*).

A configuration option object is defined using multiple arguments :

- `name` : option's name, conventionally uppercase
- `description` (default: `None`) : help text for this option
- `required` (boolean, default: `False`) : whether it shall be defined or not
- `choices` (list of values or lambda function, default: `None`) : the possible values (as a list or lazily defined through a lambda function), used for validation ; can also be `bool` (the type, not as a string !) for setting choices to false and true
- `set_callback` (lambda function, default: `None`) : a function that is triggered after setting the value
- `unset_callback` (lambda function, default: `None`) : a function that is triggered after unsetting the value
- `transform` (lambda function, default: `None`) : a function transforming the value input as for any dictionary, but for computing a new value
- `validate` (lambda function, default: `None`) : by default, a lambda function that checks for the given `choices` if defined, but can be tuned accordingly

Each lambda function takes `self` as the first argument. `transform` and `validate` also takes option's value as the second argument.

??? example

    This comes from the `FrameworkConsole` class :

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
