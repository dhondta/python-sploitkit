<p align="center" id="top"><img src="https://github.com/dhondta/python-sploitkit/raw/main/docs/pages/img/logo.png"></p>
<h1 align="center">SploitKit <a href="https://twitter.com/intent/tweet?text=SploitKit%20-%20Devkit%20for%20building%20Metasploit-like%20consoles.%0D%0APython%20library%20for%20easilly%20building%20framework%20consoles%20in%20a%20Metasploit-like%20style%20with%20a%20comprehensive%20API.%0D%0Ahttps%3a%2f%2fgithub%2ecom%2fdhondta%2fpython-sploitkit%0D%0A&hashtags=python,programming,devkit,framework,console,ctftools"><img src="https://img.shields.io/badge/Tweet--lightgrey?logo=twitter&style=social" alt="Tweet" height="20"/></a></h1>
<h3 align="center">Make a Metasploit-like console.</h3>

[![PyPi](https://img.shields.io/pypi/v/sploitkit.svg)](https://pypi.python.org/pypi/sploitkit/)
[![Read The Docs](https://readthedocs.org/projects/python-sploitkit/badge/?version=latest)](https://python-sploitkit.readthedocs.io/en/latest/?badge=latest)
[![Build Status](https://github.com/dhondta/python-sploitkit/actions/workflows/python-package.yml/badge.svg)](https://github.com/dhondta/python-sploitkit/actions/workflows/python-package.yml)
[![Coverage Status](https://raw.githubusercontent.com/dhondta/python-sploitkit/main/docs/coverage.svg)](#)
[![Python Versions](https://img.shields.io/pypi/pyversions/sploitkit.svg)](https://pypi.python.org/pypi/sploitkit/)
[![Known Vulnerabilities](https://snyk.io/test/github/dhondta/python-sploitkit/badge.svg?targetFile=requirements.txt)](https://snyk.io/test/github/dhondta/python-sploitkit?targetFile=requirements.txt)
[![License](https://img.shields.io/pypi/l/sploitkit.svg)](https://pypi.python.org/pypi/sploitkit/)


This toolkit is aimed to easilly build framework consoles in a Metasploit-like style. It provides a comprehensive interface to define CLI commands, modules and models for its storage database.

```
pip install sploitkit
```

## :sunglasses: Usage

From this point, `main.py` has the following code:

```python
#!/usr/bin/python3
from sploitkit import FrameworkConsole


class MySploitConsole(FrameworkConsole):
    #TODO: set your console attributes
    pass


if __name__ == '__main__':
    MySploitConsole(
        "MySploit",
        #TODO: configure your console settings
    ).start()
```

And you can run it from the terminal:

![](https://github.com/dhondta/python-sploitkit/tree/main/docs/pages/img/my-sploit-start.png)

## :ballot_box_with_check: Features

Sploitkit provides a base set of entities (consoles, commands, modules, models).

Multiple base console levels already exist (for detailed descriptions, see [the console section](../console/index.html)):

- [`FrameworkConsole`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/console.py): the root console, started through `main.py`
- [`ProjectConsole`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/project.py): the project console, for limiting the workspace to a single project, invoked through the `select [project]` command
- [`ModuleConsole`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/module.py): the module console, started when a module is invoked through the `use [module]` command

This framework provides more than 20 base commands, distributed in sets of functionalities (for detailed descriptions, see [the command section](../command/index.html)):

- [*general*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/general.py): commands for every level (e.g. `help`, `show`, `set`)
- [*module*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/module.py): base module-level commands (e.g. `use`, `run`, `show`)
- [*project*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/project.py): base project-level commands (e.g. `select`, `load`, `archive`)
- [*recording*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/recording.py): recording commands, for managing `.rc` files (`record`, `replay`)
- [*root*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/root.py): base root-level commands (`help`)
- [*utils*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/utils.py): utility commands (`shell`, `pydbg`, `memory`)

It also holds some base models for its storage:

- [*users*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/models/notes.py): for user-related data (`User`, `Email`, `Password`)
- [*systems*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/models/systems.py): for system-related data (`Host`, `Port`, `Service`)
- [*organization*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/models/organization.py): for organization-related data (`Organization`, `Unit`, `Employee`)
- [*notes*](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/models/notes.py): for linking notes to users, hosts or organizations

No module is provided with the framework as it is case-specific.

## :pencil2: Customization

Sploitkit defines multiple types of entities for various purposes. The following entities can be subclassed:

- [`Console`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/console.py): a new console for a new level of interaction (e.g. [`ProjectConsole`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/project.py)) ; the "`root`" level is owned by the [`FrameworkConsole`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/console.py), [`Console`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/console.py) shall be used to create new subconsoles, to be called by commands from the root console (see an example [here](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/module.py) for the module-level commands with [`ModuleConsole(Console)` and `Use(Command)`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/commands/module.py))
- [`Command`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/command.py): a new command associated with any or defined consoles using the `level` attribute
- [`Module`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/module.py): a new module associated to a console
- [`Model`, `BaseModel`, `StoreExtension`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/core/model.py): respectively for new models, their association tables and store additional methods (e.g. [`User(Model)`, `Email(Model)`, `UserEmail(BaseModel)`, `UsersStorage(StoreExtension)`](https://github.com/dhondta/python-sploitkit/blob/main/sploitkit/base/models/users.py))


## :clap:  Supporters

[![Stargazers repo roster for @dhondta/python-sploitkit](https://reporoster.com/stars/dark/dhondta/python-sploitkit)](https://github.com/dhondta/python-sploitkit/stargazers)

[![Forkers repo roster for @dhondta/python-sploitkit](https://reporoster.com/forks/dark/dhondta/python-sploitkit)](https://github.com/dhondta/python-sploitkit/network/members)

<p align="center"><a href="#top"><img src="https://img.shields.io/badge/Back%20to%20top--lightgrey?style=social" alt="Back to top" height="20"/></a></p>
