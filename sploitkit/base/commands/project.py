from __future__ import unicode_literals, print_function

from sploitkit import *
from sploitkit.utils.archive import load_from_archive, save_to_archive


projects = lambda c: [x.stem for x in Path(c.console.config['WORKSPACE'])\
                      .expanduser().iterpubdir()]


# ----------------------------- SUBCONSOLE DEFINITION --------------------------
class ProjectConsole(Console):
    """ Project subconsole definition. """
    level = "project"
    message = [
        ('class:prompt', "["),
        ('class:project', None),
        ('class:prompt', "]"),
    ]
    style = {
        'prompt':  "#eeeeee",
        'project': "#0000ff",
    }
    
    def __init__(self, parent, name):
        self.logname = name
        self.message[1] = ('class:project', name)
        self.config['WORKSPACE'] = str(Path(parent.config['WORKSPACE']) \
                                       .joinpath(name))
        super(ProjectConsole, self).__init__(parent)


# ------------------------------ ROOT-LEVEL COMMANDS ---------------------------
# These commands are available at the root level to reference a project
#  (archive|create|select|...)
class RootCommand(Command):
    """ Proxy class for setting the level attribute. """
    level = "root"


class Archive(RootCommand):
    """ Archive a project to a ZIP file (it removes the project folder) """
    def complete_values(self):
        # this returns the list of *.zip in the workspace folder
        return [str(x) for x in Path(self.console.config['WORKSPACE']) \
                .expanduser().iterfiles(".zip")]
    
    def run(self, project):
        self.logger.debug("Archiving project '{}'...".format(project))
        save_to_archive(project, project + ".zip", ask=True, remove=True)
        self.logger.success("'{}' archived".format(project))


class Create(RootCommand):
    """ Create a project """
    def complete_values(self, option=None):
        return projects(self)
    
    def run(self, project):
        self.logger.debug("Creating project '{}'...".format(project))
        Path(self.console.config['WORKSPACE']).joinpath(project).mkdir()
        self.logger.success("'{}' created".format(project))


class Delete(RootCommand):
    """ Delete a project """
    def complete_values(self, option=None):
        return projects(self)
    
    def run(self, project):
        self.logger.debug("Deleting project '{}'...".format(project))
        Path(self.console.config['WORKSPACE']).joinpath(project).rmtree()
        self.logger.success("'{}' deleted".format(project))


class Load(RootCommand):
    """ Load a project from a ZIP file (it removes the ZIP file) """
    def complete_values(self):
        return projects(self)
    
    def run(self, archive):
        self.logger.debug("Loading archive '{}'...".format(archive))
        project = Path(archive).stem
        load_from_archive(archive, project, ask=True, remove=True)
        self.logger.success("'{}' loaded".format(project))


class Select(RootCommand):
    """ Select a project """
    def complete_values(self):
        return projects(self)
    
    def run(self, project):
        ProjectConsole(self.console, project).start()


# ---------------------------- PROJECT-LEVEL COMMANDS --------------------------
class Show(Command):
    """ Show project-relevant options """
    level = "project"
    values = ["options"]
    
    def run(self, value):
        if value == "options":
            data = [["Name", "Value", "Required", "Description"]]
            for n, d, v, r in sorted(self.config.items(), key=lambda x: x[0]):
                data.append([n, v, ["N", "Y"][r], d])
            print_formatted_text(BorderlessTable(data, "Console options"))
