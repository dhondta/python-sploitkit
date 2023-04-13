A *console* is a Read-Eval-Process-Loop (REPL) environment that holds a set of enabled commands, always starting from a root console. Each child console becomes bound to its parent when started so that it can also use its configuration settings.

## Components

Basically, a console holds the central logic of the CLI through multiple components :

- *Files Manager* : It manages files from the *WORKSPACE* (depending on the context, that is, the root level or another one setting the workspace elsewhere, e.g. as for a project).
- *Global State* : It holds the key-values to be shared amongst the console levels and modules and their associated commands.
- *Datastore* : It aims to persistently save data.
- *Jobs Pool* : It manages jobs to be run from the console.
- *Sessions Pool* : It manages the open sessions, obtained from the execution of *modules*.

In order to make a custom console, two classes exist :

- The generic `Console` class : for making child console levels.
- The specific `FrameworkConsole` class : to be used directly or subclassed to define the root console.

??? example "**Example**: Basic application running a `FrameworkConsole`"

        :::python
        from sploitkit import FrameworkConsole
        
        if __name__ == '__main__':
            FrameworkConsole("MySploit").start()

<br>

## Scope and prompt

A console can be tuned in the following way using some class attributes :

- `level` : the console level name, for use with *commands*
- `message` : a list of tokens with their styling, as of [`prompt_toolkit`](https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html#coloring-the-prompt-itself)
- `style` : the style definition as a dictionary for the prompt tokens

??? example "**Example**: A console subclass for defining a new level"

        :::python
        from sploitkit import Console
        
        class MyConsole(Console):
            level = "new_level"
            message = [
                ('class:prompt', "["),
                ('class:name', "console"),
                ('class:prompt', "]>> "),
            ]
            style = {
                'prompt': "#eeeeee",
                'name':   "#ff0000",
            }
    
    ![](/img/console-prompt.png "Prompt rendered")

<br>

## Entity sources

Another important attribute of the `Console` class is `sources`. It is only handled for the parent console and is defined as a dictionary with three possible keys :

- `banners` (default: `None`) : for customizing the startup application banner
- `entities` : a list of source folders to be parsed for importing entities
- `libraries` (default: "`.`") : a list of source folders to be added to `sys.path`

??? example "**Example**: Defining sources for banners, entities and libraries"

        :::python
        from sploitkit import FrameworkConsole

        class MyConsole(Console):
            ...
            sources = {
                'banners':   "banners",
                'libraries': "lib",
            }

<br>
