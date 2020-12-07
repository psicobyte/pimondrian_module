#!/usr/bin/python3
# coding: utf-8

#       CopyRight 2020 Allan Psicobyte (psicobyte@gmail.com)
#
#       This program is free software: you can redistribute it and/or
#       modify it  under the terms of the GNU Affero General Public
#       License as published by the Free Software Foundation, either
#       version 3 of the License, or (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Module that generates paintings in the Mondrian style from a numerical
sequence.
"""
import os
from random import randint
import sys
from PIL import Image, ImageDraw

COLORS_FILE = os.path.join(os.path.dirname(__file__), 'colors.txt')
PI_DIGITS_FILE = os.path.join(os.path.dirname(__file__), '10000pi.txt')


def from_file_generator(file):
    """
    Return a generator that yield the characters in file if they are numbers.
    For each character that is not a number, returns zero instead.
    @param file:  file object
    @return: generator
    """
    while 1:
        character = file.read(1)
        if not character:
            return
        try:
            character = int(character)
        except ValueError:
            character = 0
        yield character


def pi_generator():
    """
    Return a generator that yield the digits of number Pi.
    @return: generator
    """
    try:
        pi_file = open(PI_DIGITS_FILE)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        sys.exit("error opening pi digits file")
    return from_file_generator(pi_file)


def random_generator():
    """
    Return a generator that yield random digits.
    @return: generator
    """
    while 1:
        yield randint(0, 9)


def from_file_colors(file):
    """
    The expected file format consists of ten lines, each containing a color
    in the form #RRGGBB
    @param file: file object
    @return: list
    """
    list_colors = file.readlines()
    return list_colors[:10]


def default_colors():
    """
    Return a a list with colors.
    @return: list
    """
    try:
        color_file = open(COLORS_FILE)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        sys.exit("error opening colors file")
    return from_file_colors(color_file)


class Painting:
    """
    A painting like those that Mondrian painted
    """

    def __init__(self, iterations, iterator):
        """
        @param iterations: number of iterations
        @param iterator: numbers iterator
        """
        self._max_gen = iterations
        self._iterator = iterator

        # root rectangle
        self._rectangles = [SubRectangle(1, 0, 0)]

        # rest of rectangles
        i = 0
        while i < iterations:
            for rectangle in self._rectangles:
                if rectangle.generation == i:
                    self._divide_rectangle(rectangle)
            i += 1

    def _get_generation(self, gen=None):
        """
        Returns the rectangles of the iteration indicated in gen. If gen is
        not provided, the last iteration is returned.
        @param gen: Generation
        @return: tuple of rectangles
        """
        if gen:
            return (x for x in self._rectangles if x.generation == gen)
        return (x for x in self._rectangles if x.generation == self._max_gen)

    def _divide_rectangle(self, parent):
        """Take the next three digits of the iterator, and divide the
        rectangle parent in two using the first of those three digits as a
        proportion. The other two digits determine the color of the resulting
        rectangles.
        @param parent: parent rectangle"""

        (cut_point, color1, color2) = (next(self._iterator, 0),
                                       next(self._iterator, 0),
                                       next(self._iterator, 0))

        self._rectangles.extend(
            (SubRectangle(0, cut_point, color1, parent),
             SubRectangle(1, cut_point, color2, parent))
        )

    def draw(self, line, colors, size, gen=None):
        """
        Draws a paint
        @param line: Line width.
        @param colors: List with the color table
        @param size: tuple (x,y) with de size in pixels
        @param gen: The iteration number of which the rectangles will be used.
        If not provided, the last iteration will be used.
        @return: PIL image object
        """

        img = Image.new("RGB", size, "#000000")
        draw = ImageDraw.Draw(img)
        line_w = round(line / 2, 0)

        for rect in self._get_generation(gen):
            zero = tuple(
                z1 * z2 / 100 + line_w for z1, z2 in zip(rect.zero, size))
            end = tuple(
                e1 * e2 / 100 - line_w for e1, e2 in zip(rect.end, size))

            draw.rectangle([zero, end], outline="#000000",
                           fill=colors[rect.color])
        return img

    def save_png(self, line, colors, size, name, gen=None):
        """
        Save PNG image
        @param name: File name. The PNG extension will be added.
        @param line: Line width.
        @param colors: List with the color table.
        @param size: tuple (x,y) with de size in pixels.
        @param gen: The iteration number of which the rectangles will be used.
        If not provided, the last iteration will be used.
        """
        img = self.draw(line, colors, size, gen)
        img.save(name + '.png', "PNG")


class SubRectangle:
    """
    Colored rectangle as a subdivision of a parent rectangle.
    """

    def __init__(self, position, cut_point, color, parent=None):
        """
        Create a rectangle with coordinates and color as a subdivision of a
        parent rectangle.
        @param position: 0 for the first rectangle. 1 for the second rectangle.
        @param cut_point: 0-10 number. Proportional position of the
        dividing line.
        @param color: color number 0-10.
        @param parent: parent rectangle Id or None.
        """
        self.parent = parent
        self.color = color

        if not parent:
            self._zero_x = 0
            self._zero_y = 0
            self._end_x = 100.0
            self._end_y = 100.0
            self.vert = True
            self.generation = 0

        else:
            self.generation = parent.generation + 1
            self.vert = not parent.vert

            p_z = parent.zero
            p_e = parent.end

            if self.vert:
                self._zero_x = p_z[0]
                self._end_x = p_e[0]

                if position == 0:
                    self._zero_y = p_z[1]
                    self._end_y = self._divide(p_z[1], p_e[1], cut_point)
                else:
                    self._zero_y = self._divide(p_z[1], p_e[1], cut_point)
                    self._end_y = p_e[1]

            else:
                self._zero_y = p_z[1]
                self._end_y = p_e[1]

                if position == 0:
                    self._zero_x = p_z[0]
                    self._end_x = self._divide(p_z[0], p_e[0], cut_point)
                else:
                    self._zero_x = self._divide(p_z[0], p_e[0], cut_point)
                    self._end_x = p_e[0]

    @property
    def zero(self):
        """
        Percentage coordinates of the point of origin of the rectangle
        @return: tuple
        """
        return self._zero_x, self._zero_y

    @property
    def end(self):
        """
        Percentage coordinates of the point of end of the rectangle
        @return: tuple
        """
        return self._end_x, self._end_y

    @staticmethod
    def _divide(short, long, factor):
        """
        return the point that corresponds to 'factor' tenths between 'short'
        and 'long'
        """

        if factor:
            return round(short + ((long - short) * factor / 10), 0)
        return long
