# -*- coding: UTF-8 -*-
"""
Module for transforming an instance's docstring to a metadata dictionary as
 shown in the following example:

    class Example(object):
        \"""
        This is a test multi-line long 
         description.

        This is a first comment.

        Author: John Doe
                 (john.doe@example.com)
        Version: 1.0
        Comments:
        - subcomment 1
        - subcomment 2

        Something: lorem ipsum
                    paragraph

        This is a second comment,
         a multi-line one.
        \"""
        [...]
        
    >>> parse_docstring(Example)
    {'author': 'John Doe (john.doe@example.com)',
     'comments': ['This is a first comment.',
                  ('subcomment 1', 'subcomment 2'),
                  'This is a second comment, a multi-line one.'],
     'description': 'This is a test multi-line long description.',
     'something': 'lorem ipsum paragraph',
     'version': '1.0'}
"""
import re


__all__ = ["parse_docstring"]


def parse_docstring(something):
    """ Parse the docstring of the given object. """
    metadata = {}
    if not isinstance(something, str):
        if not hasattr(something, "__doc__") or something.__doc__ is None:
            return metadata
        something = something.__doc__
    # function for registering the key-value pair in the dictionary of metadata
    def setkv(key, value):
        if key is not None:
            key = key.lower().replace(" ", "_")
        if value == "":
            return
        else:
            if value.startswith("-"):  # do not consider '*'
                value = tuple(map(lambda s: s.strip(), value.split("-")[1:]))
        # free text (either the description or a comment)
        if key is None:
            metadata.setdefault("comments", [])
            if metadata.get("description") is None:
                metadata["description"] = value
            else:
                metadata["comments"].append(value)
        # when comments field is explicitely set
        elif key == "comments":
            metadata["comments"].append(value)
        # ensure options field is a list and convert each option to a tuple
        elif key == "options":
            metadata.setdefault("options", [])
            metadata["comments"].append(tuple(map(lambda s: s.strip(),
                                                  value.split("|"))))
        # key-value pair
        else:
            metadata[key] = value
    # parse trying to get key-values first, then full text
    for p in re.split(r"\n\s*\n", something):
        field, text = None, ""
        for l in p.splitlines():
            kv = list(map(lambda s: s.strip(), l.split(":", 1)))
            if len(kv) == 1:
                # unwrap and unindent lines of the text
                text = (text + " " + kv[0]).strip()
            else:
                # a key-value pair is present
                if kv[0] != field:
                    setkv(field, text)
                field, text = kv
        setkv(field, text)
    return metadata
