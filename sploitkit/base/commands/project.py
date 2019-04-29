from __future__ import unicode_literals, print_function

from sploitkit import *
from sploitkit.utils.archive import load_from_archive, save_to_archive


projects = lambda c: [x.stem for x in Path(c.console.config['WORKSPACE'])\
                      .expanduser().iterpubdir()]


# ----------------------------- SUBCONSOLE DEFINITION --------------------------
class ProjectConsole(Console):
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
    config = Config({
        Option('WORKSPACE', "folder where results are saved"): None,
        Option('RECORD', "whether results should be saved or not"): True,
    })
    
    def __init__(self, parent):
        self.message[1] = ('class:project', self.name)
        self.config['WORKSPACE'] = str(Path(parent.config['WORKSPACE']) \
                                       .joinpath(self.name))
        super(ProjectConsole, self).__init__(parent)


# ------------------------------ ROOT-LEVEL COMMANDS ---------------------------
class RootCommand(Command):
    """ Proxy class for setting the level attribute. """
    level = "root"


class Archive(RootCommand):
    """ Archive a project to a ZIP file (it removes the project folder) """
    def complete_values(self):
        # this returns the list of *.zip in the workspace folder
        return [str(x) for x in Path(Console.parent.config['WORKSPACE']) \
                .expanduser().iterfiles(".zip")]
    
    def run(self, project):
        self.logger.debug("Archiving project '{}'...".format(project))
        save_to_archive(project, project + ".zip", ask=True, remove=True)
        self.logger.success("'{}' archived".format(project))


class Create(RootCommand):
    """ Create a project """
    def complete_values(self, option):
        return projects(self)
    
    def run(self, project):
        self.logger.debug("Creating project '{}'...".format(project))
        Path(Console.parent.config['WORKSPACE']).joinpath(project).mkdir()
        self.logger.success("'{}' created".format(project))


class Delete(RootCommand):
    """ Delete a project """
    def complete_values(self, option):
        return projects(self)
    
    def run(self, project):
        self.logger.debug("Deleting project '{}'...".format(project))
        Path(Console.parent.config['WORKSPACE']).joinpath(project).rmtree()
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
        self.logger.debug("Starting subconsole '{}'".format(project))
        ProjectConsole.name = project
        ProjectConsole(Console.parent).start()


class Show(RootCommand):
    """ Show options, projects or modules """
    values = ["options", "projects"]
    
    def __init__(self):
        self.categories = Console.parent.modules.keys()
        self.values += self.categories
        self.values = sorted(list(set(self.values)))
    
    def run(self, category):
        if category == "options":
            data = [["Name", "Value", "Description"]]
            for k, d, v, r in sorted(self.config.items(), key=lambda x: x[0]):
                data.append([k, v, d])
            print_formatted_text(BorderlessTable(data, "Console options"))
        elif category == "projects":
            data = [["Name"]]
            for p in projects(self):
                data.append([p])
            print_formatted_text(BorderlessTable(data, "Existing projects"))
        elif category in self.categories:
            data = [["Name", "Path", "Description"]]
            for m in sorted(Module._subclasses, key=lambda x: x.name):
                data.append([m.name, m.path, m.description])
