# -*- coding: UTF-8 -*-
from prompt_toolkit.widgets import FormattedTextToolbar, TextArea
#TODO: do not forget to remove unuseful imports


__all__ = ["CustomLayout"]


#TODO: determine if this module is still useful ; remove it if necessary

class AppToolbar(FormattedTextToolbar):
    pass


class CustomLayout(object):
    def __init__(self, console):
        self.layout = console._session.app.layout
        #self.layout.container.children = self.layout.container.children[:-1]
        #print(self.layout.container.children)

