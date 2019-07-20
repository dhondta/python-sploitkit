from __future__ import unicode_literals


ROOT_LEVEL = "root"  # console root level's name


# list of folders from which related items are to be loaded
SOURCES = {
    'banners':  None,
    'entities': ["commands", "modules"],
}


# dictionary of back-references to be made on entities
BACK_REFERENCES = {
    'commmand': [("", "console")],
    'console':  [("config", "console")],
    'module':   [("", "console")],
}


# prompt message format
PROMPT_FORMAT = [
    ('class:prompt', " > "),
]


# prompt message style
PROMPT_STYLE = {
    '':        "#30b06f",  # text after the prompt
    'prompt':  "#eeeeee",  # prompt message
    'appname': "#eeeeee underline",  # application name
}
