*Commands* are associated to *consoles* through the `level` attribute and are evaluated in the REPL of a console using their `run(...)` method. Completion and validation can be tuned using appropriate methods like explained hereafter.

Note that they are two possible formats : `COMMAND VALUE` or `COMMAND KEY VALUE`.

## Styling

It is possible to define the style of *commands*, that is, how the class name is rendered when called in a *console*. Currently, four styles are supported :

**Name** | **Command class name** | **Rendered command name**
--- | :---: | :---:
*Lowercase* | `MyCommand` | `mycommand`
*Powershell* | `MyCommand` | `My-Command`
*Slugified* (default) | `MyCommand` | `my-command`
*Uppercase* | `MyCommand` | `MYCOMMAND`

Command styling can be set using the `set_style(...)` class method.

??? example "**Example**: Setting commands style"

        :::python
        from sploitkit import Command
        
        Command.set_style("powershell")

<br>

## Definition

A *command* always subclasses the `Command` generic entity class and can be dissected as follows :

1. **Docstring** : This will be used for command's description in help messages (callable through the `help()` method). Note that this docstring is parsed like for any entity (as it is a feature of the `Entity` class), meaning that metadata fields will be parsed and stored in a `_metadata` class attribute.
2. **Class attributes** : They tune the applicability and nature of the command.
3. **Instance methods** : They define the logic of the command, i.e. `run()`.

Here is the list of tunable class attributes :

**Attribute** | **Type** | **Default** | **Description**
--- | :---: | :---: | ---
`aliases` | `list`(`str`) | `[]` | the list of aliases for the command
`alias_only` | `bool` | `False` | whether only the aliases defined in the related list should be considered or also the converted command class name
`applies_to` | `list`(`str`) | `[]` | a list of *modules* this command applies to
`except_levels` | `list`(`str`) | `[]` | a list of non-applicable levels
`keys` | `list`(`str`) or `dict` | `[]` | a list of possible keys or a dictionary of keys and associated values (this implies the second format with key-value)
`level` | `str` | "`general`" | command's level ; "`general`" means that it applies to all console levels
`single_arg` | `bool` | `False` | handle everything after the command as a single argument
`values` | `list`(`str`) | 


??? example "**Example**: Making a command in Powershell style with an alias and applicable to the *module* level"
    
        :::python
        from sploitkit import Command
        
        Command.set_style("powershell")
        
        class GetSomething(Command):
            """ Get something """
            aliases = ["gs"]
            level   = "module"
            [...]
    
<br>

## Completion

Completion is defined according to the command format and the related method signature is adapted accordingly. So, if a command is value-only, it *can* own a `complete_values()` method with no argument. If a command has both a key and a value, it *can* own a `complete_keys()` method taking no argument and a `complete_values(key)` method that can be tuned according to the key entered in the incomplete command.

By default, the `Command` class has both `complete_keys` and `complete_values` methods implemented, relying on the signature of the `run(...)` method to determine command's format. Completion is handled according to the format :

- `COMMAND VALUE` : Then only `complete_values` is used, handling the `values` class attribute as a list.
- `COMMAND KEY VALUE` : This one uses 

    - `complete_keys`, handling the `keys` class attribute as a list in priority, otherwise the `values` class attribute as a dictionary whose keys are the equivalent to the `keys` class attribute
    - `complete_values`, handling the `values` class attribute as a dictionary whose values for the key given in argument (if not given, all the values aggregated from all the keys) give the completion list

??? example "**Example**: "

        :::python
        class DoSomething(Command):
            values = {"key1": ["1", "2", "3"],
                      "key2": ["4", "5", "6"],
                      "key3": ["7", "8", "9"]}
            
            def run(self, key=None, value=None):
                print(key, value)
    
    This command will yield a completion list of :

    - `["key1", "key2", "key3"]` when entering "`do-something `" and pressing the tab key twice
    - `["4", "5", "6"]`when entering "`do-something key2 `" and pressing the tab key twice

<br>

## Validation

Validation works using, by default, the `complete_keys` and `complete_values` methods and therefore also relies on the signature of the `run()` method. It also takes only a value (first format) or a key and a value (second format) as arguments and its signature must then be adapted accordingly.

By default, 
