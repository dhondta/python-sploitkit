# -*- coding: UTF-8 -*-
from terminaltables import AsciiTable
from textwrap import wrap


__all__ = ["BorderlessTable", "NameDescription"]


class NoBorder(AsciiTable):
    """ AsciiTable with no border. """
    def __init__(self, *args, **kwargs):
        super(NoBorder, self).__init__(*args, **kwargs)
        self.outer_border = False
        self.inner_column_border = False
        self.inner_heading_row_border = False

    def __str__(self):
        t = self.table
        return "\n" + t + "\n" if len(t) > 0 else ""


class BorderlessTable(NoBorder):
    """ Custom table with no border. """
    def __init__(self, data, title=None, title_ul_char="=", header_ul_char="-",
                 header=True):
        self.data = data
        if data is None:
            return
        if header:
            # add a row with underlining for the header row
            underlines = [len(_) * header_ul_char for _ in data[0]]
            data.insert(1, underlines)
        # now insert an indentation column
        for row in data:
            row.insert(0, " ")
        # then initialize the AsciiTable
        super(BorderlessTable, self).__init__(data)
        # wrap the text of the last column
        max_w = self.column_max_width(-1)
        for row in self.table_data:
            row[-1] = "\n".join(wrap(row[-1], max_w))
        # configure the title
        self.title_ = title  # define another title to format it differently
        self.title_ul_char = title_ul_char
    
    def __str__(self):
        return self.table
    
    @property
    def table(self):
        if self.data is None:
            return ""
        t = self.title_
        s = ("\n{}\n{}\n".format(t, len(t) * self.title_ul_char) \
             if t is not None else "") + "\n{}\n"
        return s.format(super(BorderlessTable, self).table)


class NameDescription(NoBorder):
    """ Row for displaying a name-description pair, with details if given. """
    indent = 4
    
    def __init__(self, name, descr, details=None, nwidth=16):
        # compute the name column with to a defined width
        n = "{n: <{w}}".format(n=name, w=nwidth)
        # then initialize the AsciiTable, adding an empty column for indentation
        super(NameDescription, self).__init__([[" " * max(0, self.indent - 3),
                                                n, ""]])
        # now wrap the text of the last column
        max_w = self.column_max_width(-1)
        self.table_data[0][2] = "\n".join(wrap(descr, max_w))
        self._details = details
    
    def __str__(self):
        _ = super(NameDescription, self).__str__()
        if self._details:
            _ += str(NameDescription(" ", self._details, nwidth=self.indent-2))
        return _
