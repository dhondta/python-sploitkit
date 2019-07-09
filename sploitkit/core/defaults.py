from __future__ import unicode_literals


__all__ = ["PROMPT_FORMAT", "PROMPT_STYLE", "ROOT_LEVEL", "SOURCES"]


ROOT_LEVEL = "root"  # console root level's name


# list of folders from which related items are to be loaded
SOURCES = {
    'banners':  None,
    'commands': ["commands"],
    'modules':  ["modules"],
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
