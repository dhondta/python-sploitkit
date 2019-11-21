Sploitkit's API conveniently defines the CLI framework in 
an Object-Oriented fashion. *Consoles* have a set of *commands* and can
be associated with *modules*, which are capable of handling their
context in isolation and save/restore data from a *datastore*
according to user-defined *models*. Datastores can also be customized 
using *store extensions.

Thanks to compartmentalization in *projects*, *files*, *jobs* and 
*sessions*, it becomes easier to organize your work or generate
reports.
 
To sum it up, Sploitkit aims to be highly
customizable while keeping the same CLI philosophy as Metasploit, while
leveraging Python and the power of 
[`prompt_toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit) 
in order to enhance the user experience through command-line completion 
and validation.

## Main architecture

This library is designed around a central class called *entity*.
An entity centralizes features such as class registry, which keeps track
of relevant sub-entities like *consoles*, *commands* and *modules*. 
This means every entity class inherits from this main class and then 
defines additional features of its own.

Basically, five different "main" entity classes are defined :

- `Console` : defines CLI console levels
- `Command` : defines console commands, attached to console levels
- `Module` : creates modules with specific purpose (like in Metasploit)
- `Model` : describes the data schemas used to write in the datastore
- `StoreExtension` : allows for mixins to be used within the datastore

At startup, Sploitkit loads every entity it finds in the user-defined 
sources, as well as a pre-defined set of generic commands (like in 
Metasploit or Recon-ng). This behaviour can be disabled if so desired.
Instantiation begins with a `Console` and then proceeds with the loading
of all the other entities.  For convenience, a `FrameworkConsole` 
containing some some base functionalities is provided. It serves as a
good starting point for newcomers to Sploitkit.

!!! note "Back-referencing"
    
    Back-referencing is heavily used throughout Sploitkit:
    
    * `module.console` refers to the parent console of module
    * calling `self.config.console` within an `option` allows to
    "walk up" the chain up to the console, and to create triggers for
    it

## Project structure

The package is structured as follows :

- `base` : This contains base entities to be included by default in any 
application. Note that if some base commands are not required, they can 
be disabled (see section *Classes*/`Command`).
- `core` : This holds the core functionalities of Sploitkit with the 
class definitions for `Entity` and the main entity classes but also 
components for the main console.
- `utils` : This contains utility modules that are not specifically 
part of the `base` and `core` subpackages.
