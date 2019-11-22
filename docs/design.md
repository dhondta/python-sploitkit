Sploitkit provides an API for conveniently defining CLI frameworks in an Object-Oriented fashion. It allows to define *consoles* that have sets of *commands* and that can be associated with different *modules* handling separated contexts while saving data to a datastore according to *models* eventually using *store extensions*. It also allows to handle *projects*, *files*, *jobs* and *sessions* so that organizing work and reports becomes easier. Briefly, it aims to be highly customizable while keeping the same CLI philosophy as Metasploit but leveraging Python and the power of [`prompt_toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit) in order to enhance the user experience (through a lot of completion and validation).

## Main architecture

This library is designed around a central class called [*entity*](classes/entity.html) that gathers common features like class registry for keeping track of relevant entities like *consoles*, *commands* and *modules*. So, every entity class inherits from this main class and then defines its own additional features for its purpose.

Basically, five different main entity classes are defined :

- [`Console`](classes/console.html) : for defining CLI console levels
- [`Command`](classes/command.html) : for defining console commands, accessible from console levels
- [`Module`](classes/module.html) : for declaring modules with specific functionalities like in Metasploit
- [`Model`](classes/datastore.html) : for describing data schemas to be recorded in the datastore
- [`StoreExtension`](classes/datastore.html) : for defining mixins to be used with the datastore

At startup, Sploitkit loads every entity it finds in the user-defined sources, also loading a pre-defined set of generic commands (like in Metasploit or Recon-ng), which can eventually be disabled if not required. The point here is that everything starts from the instantiation of a `Console`, that triggers entities loading. For convenience, a `FrameworkConsole` holding some base functionalities allows to quickly start an application.

!!! note "Back-referencing"
    
    For easilly calling objects of a type from bound objects of another type, back-referencing is extensively used. For instance,
    
    - from a module, its parent console is reachable by simply using `self.console` in a method
    - from an option, its config can be called by using `self.config` which has itself a back-reference to its parent console, therefore allowing to reach `self.config.console` (this makes triggers from an option possible into the parent console)

## Project structure

The package is structured as follows :

- `base` : This contains base entities to be included by default in any application. Note that if some base commands are not required, they can be disabled (see section *Classes*/`Command`).
- `core` : This holds the core functionalities of Sploitkit with the class definitions for `Entity` and the main entity classes but also components for the main console.
- `utils` : This contains utility modules that are not specifically part of the `base` and `core` subpackages.
