# -*- coding: UTF-8 -*-
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea
#TODO: do not forget to remove unuseful imports


__all__ = ["FrameworkApp"]


#TODO: find a way to embed the Console instance (started with .start()) into
#       FrameworkApp
class FrameworkApp(Application):
    def __init__(self, *args, **kwargs):
        console = kwargs.get('console')
        if console is None:
            raise Exception("No root console passed to the application")
        #console.__class__ = type("ConsoleTextArea",
        #                         (TextArea, console.__class__), {})
        #console.scrollbar = True
        root_container = HSplit([
            console,
        ])
        kwargs['layout'] = Layout(root_container, focused_element=console)
        super(FrameworkApp, self).__init__(*args, **kwargs)
