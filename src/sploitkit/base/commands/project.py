# -*- coding: UTF-8 -*-
from tinyscript.helpers import confirm, Path, ProjectPath

from sploitkit import *


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
        self.config['WORKSPACE'] = str(Path(parent.config['WORKSPACE']).joinpath(name))
        super(ProjectConsole, self).__init__(parent)


# ------------------------------ ROOT-LEVEL COMMANDS ---------------------------
# These commands are available at the root level to reference a project (archive|create|select|...)
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
        projpath = Path(self.workspace).joinpath(project)
        folder = ProjectPath(projpath)
        self.logger.debug(f"Archiving project '{project}'...")
        ask = self.console.config.option("ENCRYPT_PROJECT").value
        try:
            folder.archive(ask=ask)
            self.logger.success(f"'{project}' archived")
        except OSError as e:
            self.logger.error(str(e))
            self.logger.failure(f"'{project}' not archived")


class Delete(ProjectRootCommand):
    """ Delete a project """
    def run(self, project):
        self.logger.debug(f"Deleting project '{project}'...")
        self.workspace.joinpath(project).remove()
        self.logger.success(f"'{project}' deleted")


class Load(ProjectRootCommand):
    """ Load a project from a ZIP file (it removes the ZIP file) """
    def complete_values(self):
        # this returns the list of *.zip in the workspace folder
        return [x.stem for x in self.workspace.iterfiles(".zip")]
    
    def run(self, project):
        self.logger.debug(f"Loading archive '{project}.zip'...")
        projpath = Path(self.workspace).joinpath(project)
        archive = ProjectPath(projpath.with_suffix(".zip"))
        ask = self.console.config.option("ENCRYPT_PROJECT").value
        try:
            archive.load(ask=ask)
            self.logger.success(f"'{project}' loaded")
        except Exception as e:
            self.logger.error("Bad password" if "error -3" in str(e) else str(e))
            self.logger.failure(f"'{project}' not loaded")
    
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
        if project in loader.complete_values() and confirm("An archive with this name already exists ; "
                                                           "do you want to load the archive instead ?"):
            loader.run(project)
        if not p.exists():
            self.logger.debug(f"Creating project '{project}'...")
            p.mkdir()
            self.logger.success(f"'{project}' created")
        ProjectConsole(self.console, project).start()
        self.config['WORKSPACE'] = str(Path(self.config['WORKSPACE']).parent)
    
    def validate(self, project):
        pass


# ---------------------------- PROJECT-LEVEL COMMANDS --------------------------
class Show(Command):
    """ Show project-relevant options """
    #FIXME
    level = "project"
    values = ["options"]
    
    def run(self, value):
        print_formatted_text(BorderlessTable(self.console.__class__.options, "Console options"))

