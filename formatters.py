from discord.ext import commands
import database_connection as db
from io import BytesIO
import aiohttp
import config
import math
import pprint
p = pprint.PrettyPrinter(indent=4)


class BaseFormatter:

    @classmethod
    def from_single(cls, headings: list, lines: list):
        if lines and headings:
            # no idea where to put this, could be on the utils class
            def nest_level(obj):
                # Not a list? So the nest level will always be 0:
                if type(obj) != list:
                    return 0
                max_level = 0
                for item in obj:
                    # recursively get the max level
                    max_level = max(max_level, nest_level(item))
                # Adding 1, because 'obj' is a list (here is the recursion magic):
                return max_level + 1
            if nest_level(headings) == 1 and nest_level(lines) == 1:
                return cls(headings, [lines])
            else:
                raise ValueError('Nesting depth exceeded')

    def __init__(self, headings: list, lines: list):

        # lines and headings must not be empty lists ( printing nothing makes no sense )
        if lines and headings:

            # header line
            self.headings = [str(col) for col in headings]

            # maximum length per column
            self.lengths = list()
            headings_length = len(headings)

            # initial row: get length of headers
            for col in range(0, headings_length):
                self.lengths.append(len(headings[col]))

            # convert everything in the line to string
            lines = [[str(col) for col in line] for line in lines]

            # search through lines
            for line in lines:

                # contents must be uniform
                if len(line) != headings_length:
                    raise ValueError('Both the header line and the contents must have the same length')

                # go through all columns and compare the corresponding entries
                for col in range(0, headings_length):
                    self.lengths[col] = len(line[col]) if len(line[col]) > self.lengths[col] else self.lengths[col]

            self.lines = lines

        else:
            raise ValueError('Lists must not be empty')

    def get_output(self):
        pass

    def get_single(self, index: int = 0):
        pass


class TextFormatter(BaseFormatter):

    def __init__(self, headings: list, lines: list,
                 column_spacer=' ', first_line_separator=None,
                 repeat_header=False, opener_closer='```'):
        super().__init__(headings, lines)

        # how should columns be separated?
        self.column_spacer = column_spacer

        # repeat the header line
        self.repeat_header = repeat_header

        # If this is set, the header line will be separated from the rows by using the separator char as a spacer
        # to fill two lines
        self.heading_separator = first_line_separator

        # add all the lengths + ( amount of columns - 1 ) * the length of the spacer between them
        # adds one because \n is a character too
        self.line_size = sum(self.lengths) + (len(self.headings) - 1) * len(self.column_spacer) + 1

        self.opener_closer = opener_closer

        if self.line_size > config.DISCORD_MAX_LENGTH:
            raise ValueError('A line must not be longer '
                             'than {} characters, but {} were given'.format(config.DISCORD_MAX_LENGTH,
                                                                            self.line_size))

    # get a single entry as text output ( usable on things that expect 1 result only )
    def get_single(self, index: int = 0):
        pass

    def get_output(self):
        pages = list()
        page = str()

        # heading
        page += self._get_header_line()

        # lines
        for line in self.lines:
            # get the string for this line
            printed = self._get_line_string(line)

            # would appending this line go over the character limit?
            if len(page) + len(printed) > self._static_output_length(0):
                pages.append('{opcl}{page}{opcl}'.format(page=page, opcl=self.opener_closer))

                # should headers be repeated?
                if self.repeat_header:
                    page = self._get_header_line()
                else:
                    page = str()

                page += printed
            else:
                page += printed

        pages.append('{opcl}{page}{opcl}'.format(page=page, opcl=self.opener_closer))
        return pages

    def _get_line_string(self, line):
        page = str()
        for col in range(0, len(line)):
            if col != len(line)-1:
                page += '{sep: <{width}}{col_spacer}'.format(sep=line[col],
                                                             width=self.lengths[col],
                                                             col_spacer=self.column_spacer)
            else:
                page += '{sep: <{width}}{col_spacer}'.format(sep=line[col],
                                                             width=self.lengths[col],
                                                             col_spacer='\n')
        return page

    def _get_header_line(self):
        page = str()
        if self.heading_separator is not None:
            page = '\n{sep:{sep}<{width}}\n'.format(sep=self.heading_separator, width=self.line_size-1)
        page += self._get_line_string(self.headings)
        if self.heading_separator is not None:
            page += '{sep:{sep}<{width}}\n'.format(sep=self.heading_separator, width=self.line_size-1)
        return page

    # returns the amount of characters left to take in a line
    def _static_output_length(self, other_chars: int):
        return config.DISCORD_MAX_LENGTH - other_chars - len(self.opener_closer) * 2
