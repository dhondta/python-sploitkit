from os.path import dirname, join

from .misc import *
from .misc import __all__ as _misc
from .peewee_ext import *
from .peewee_ext import __all__ as _peewee_ext


__all__ = _misc + _peewee_ext + ["PROJECT_STRUCTURE"]


PROJECT_STRUCTURE = {
    'README': "# {}\n\n#TODO: Fill in the README",
    'requirements.txt': None,
    'banner': {},
    'commands': {},
    'modules': {},
}
__templ = join(dirname(__file__), "templates"
with open(join(__templ, "main.py") as f:
    PROJECT_STRUCTURE['main.py'] = f.read()
with open(join(__templ, "commands.py") as f:
    PROJECT_STRUCTURE['commands']['template.py'] = f.read()
with open(join(__templ, "modules.py") as f:
    PROJECT_STRUCTURE['modules']['template.py'] = f.read()

