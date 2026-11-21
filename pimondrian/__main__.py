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
This module is the Pi Mondrian command line
"""

import argparse
import contextlib
import sys
import pimondrian as pm

DEFAULT_PAINT_NAME = "PiMondrian"
DEFAULT_LINE_SIZE = 4
DEFAULT_ITERATIONS = 5
DEFAULT_SIZE = (1200, 800)
DEFAULT_COLORS_FILE = pm.COLORS_FILE
DEFAULT_NUMBERS_FILE = pm.PI_DIGITS_FILE


def open_numbers_file(filename):
    """
    Open the file with the numbers, or abort with an error message.
    @param filename: path of the file
    @return: file object
    """
    try:
        return open(filename)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        sys.exit("error opening numbers file")


def main():
    """
    CLI function
    """
    help_txt = """
Program that draws pictures in the style of Piet Mondrian.
This program creates a PNG file with a painting from the digits of the
umber Pi. Optionally, you can indicate a file with numbers or send the
numbers through a pipe to the standard input.
"""
    epilog_txt = """
This program works recursively, first dividing the canvas into two
rectangles, then dividing each of them into two others, and so on, as many
times as indicated with the flag --iterations.
"""

    parser = argparse.ArgumentParser(prog="pimondrian",
                                     description=help_txt,
                                     epilog=epilog_txt)
    parser.add_argument('-f', '--file', type=str, dest='file',
                        help='path of the file containing the numbers. If not \
                        specified, the first 10000 digits of Pi will be used')

    parser.add_argument('-c', '--colors', type=str, dest='colors',
                        help='path of the file containing the colors')

    parser.add_argument('-n', '--name', type=str, dest='name',
                        help='painting name. The default value is {}'.format(
                            DEFAULT_PAINT_NAME))

    parser.add_argument('-g', '--gallery', type=int, dest='gallery',
                        help='number of generated paintings')

    parser.add_argument('-y', '--ysize', type=int, dest='y_size',
                        help='painting height. The default value is {}'.format(
                            DEFAULT_SIZE[1]))

    parser.add_argument('-x', '--xsize', type=int, dest='x_size',
                        help='painting width. The default value is {}'.format(
                            DEFAULT_SIZE[0]))

    parser.add_argument('-i', '--iterations', type=int, dest='iterations',
                        help='number of iterations in the creation of the \
                        painting. The more iterations, the more rectangles. \
                        The default value is {}'.format(DEFAULT_ITERATIONS))

    parser.add_argument('-l', '--line', type=int, dest='line',
                        help='line thickness. The default value is {}'.format(
                            DEFAULT_LINE_SIZE))

    parser.add_argument('-r', '--random', action='count',
                        help='use random numbers instead of a file')

    args = parser.parse_args()

    paint_name = args.name if args.name else DEFAULT_PAINT_NAME

    size = (args.x_size if args.x_size else DEFAULT_SIZE[0],
            args.y_size if args.y_size else DEFAULT_SIZE[1])

    iterations = args.iterations if args.iterations else DEFAULT_ITERATIONS

    line = args.line if args.line else DEFAULT_LINE_SIZE

    c_filename = args.colors if args.colors else DEFAULT_COLORS_FILE
    try:
        with open(c_filename) as colors_file:
            colors = pm.from_file_colors(colors_file)
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        sys.exit("error opening colors file")

    # Any numbers file opened below is closed when the painting is done.
    with contextlib.ExitStack() as stack:
        # An explicitly requested source always wins over what is piped in, so
        # that --file and --random keep working when stdin is not a terminal.
        if args.file:
            generator = pm.from_file_generator(
                stack.enter_context(open_numbers_file(args.file)))
            print("Extracting digits from file")
        elif args.random:
            generator = pm.random_generator()
            print("Randomly generated")
        elif not sys.stdin.isatty():
            print("Reading from stdin")
            generator = pm.from_file_generator(sys.stdin)
        else:
            generator = pm.from_file_generator(
                stack.enter_context(open_numbers_file(DEFAULT_NUMBERS_FILE)))
            print("Extracting digits from file")

        if args.gallery:
            for number in range(args.gallery):
                print("Artist working... ({})".format(number))
                pm.Painting(iterations, generator).save_png(line,
                                                            colors,
                                                            size,
                                                            "{}_{}".format(
                                                                paint_name,
                                                                number))
        else:
            print("Artist working...")
            pm.Painting(iterations, generator).save_png(line,
                                                        colors,
                                                        size,
                                                        paint_name)


if __name__ == '__main__':
    main()
