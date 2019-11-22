# -*- coding: UTF-8 -*-
from sploitkit import *
from sploitkit.utils.archive import load_from_archive, save_to_archive


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


class ProjectRootCommand(RootCommand):
    """ Proxy class for defining the complete_values method. """
    single_arg = True
    
    def complete_values(self):
        return [x.filename for x in self.workspace.iterpubdir()]


class Archive(ProjectRootCommand):
    """ Archive a project to a ZIP file (it removes the project folder) """
    def run(self, project):
        p = Path(self.workspace).joinpath(project)
        self.logger.debug("Archiving project '{}'...".format(project))
        ask = self.console.config.option("ENCRYPT_PROJECT").value
        if save_to_archive(str(p), str(p) + ".zip", ask=ask, remove=True,
                           logger=self.logger):
            self.logger.success("'{}' archived".format(project))
        else:
            self.logger.failure("'{}' not archived".format(project))


class Delete(ProjectRootCommand):
    """ Delete a project """
    def run(self, project):
        self.logger.debug("Deleting project '{}'...".format(project))
        self.workspace.joinpath(project).rmtree()
        self.logger.success("'{}' deleted".format(project))


class Load(ProjectRootCommand):
    """ Load a project from a ZIP file (it removes the ZIP file) """
    def complete_values(self):
        # this returns the list of *.zip in the workspace folder
        return [x.stem for x in self.workspace.iterfiles(".zip")]
    
    def run(self, project):
        self.logger.debug("Loading archive '{}'...".format(project + ".zip"))
        archive = self.workspace.joinpath(project).with_suffix(".zip")
        ask = self.console.config.option("ENCRYPT_PROJECT").value
        if load_from_archive(str(archive), str(self.workspace), ask=ask,
                             remove=True, logger=self.logger):
            self.logger.success("'{}' loaded".format(project))
        else:
            self.logger.failure("'{}' not loaded".format(project))
    
    def validate(self, project):
        if project not in self.complete_values():
            raise ValueError("no project archive for this name")
        elif project in super(Load, self).complete_values():
            raise ValueError("a project with the same name already exists")


class Select(ProjectRootCommand):
    """ Select a project (create if it does not exist) """
    def complete_values(self):
        return Load().complete_values() + super(Select, self).complete_values()
    
    def run(self, project):
        p = self.workspace.joinpath(project)
        loader = Load()
        if project in loader.complete_values() and \
            confirm("An archive exists with this name ; load the archive "
                    "instead ?"):
            loader.run(project)
        if not p.exists():
            self.logger.debug("Creating project '{}'...".format(project))
            p.mkdir()
            self.logger.success("'{}' created".format(project))
        ProjectConsole(self.console, project).start()
        self.config['WORKSPACE'] = str(Path(self.config['WORKSPACE']).parent)


# ---------------------------- PROJECT-LEVEL COMMANDS --------------------------
class Show(Command):
    """ Show project-relevant options """
    level = "project"
    values = ["options"]
    
    def run(self, value):
        print_formatted_text(BorderlessTable(self.console.__class__.options,
                                             "Console options"))
