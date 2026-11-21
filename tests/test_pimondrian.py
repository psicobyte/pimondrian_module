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
Test suite for the pimondrian module and its command line.

Run with:   python3 -m unittest discover tests
        or: python3 -m pytest tests
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pimondrian as pm

SIZE = (120, 80)
# ten colours, none of them the black used as background and border, so that
# a rectangle that is not painted cannot pass for a painted one
COLORS = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff',
          '#00ffff', '#ffffff', '#800000', '#008000', '#000080']


class TestFromFileGenerator(unittest.TestCase):
    """from_file_generator()"""

    def test_yields_the_digits_of_the_file(self):
        gen = pm.from_file_generator(io.StringIO("314"))
        self.assertEqual([3, 1, 4], list(gen))

    def test_non_numeric_characters_become_zero(self):
        gen = pm.from_file_generator(io.StringIO("3a1\n4"))
        self.assertEqual([3, 0, 1, 0, 4], list(gen))

    def test_empty_file_yields_nothing(self):
        self.assertEqual([], list(pm.from_file_generator(io.StringIO(""))))


class TestColors(unittest.TestCase):
    """from_file_colors() and default_colors()"""

    def test_reads_the_colors_of_the_file(self):
        colors = pm.from_file_colors(io.StringIO("#ff0000\n#00ff00\n"))
        self.assertEqual(['#ff0000\n', '#00ff00\n'], colors)

    def test_ignores_the_rows_after_the_tenth(self):
        colors = pm.from_file_colors(io.StringIO("#ff0000\n" * 15))
        self.assertEqual(10, len(colors))

    def test_default_colors_returns_ten_usable_colors(self):
        colors = pm.default_colors()
        self.assertEqual(10, len(colors))
        pm.Painting(2, pm.pi_generator()).draw(4, colors, SIZE)


class TestGenerators(unittest.TestCase):
    """pi_generator() and random_generator()"""

    def test_pi_generator_starts_with_the_digits_of_pi(self):
        gen = pm.pi_generator()
        self.assertEqual([3, 1, 4, 1, 5, 9, 2, 6, 5, 3],
                         [next(gen) for _ in range(10)])

    def test_random_generator_only_yields_digits(self):
        gen = pm.random_generator()
        digits = [next(gen) for _ in range(200)]
        self.assertTrue(all(0 <= d <= 9 for d in digits))


class TestPainting(unittest.TestCase):
    """Painting()"""

    def test_builds_the_expected_number_of_rectangles(self):
        # a full binary tree of 'iterations' levels, root included
        for iterations in range(6):
            painting = pm.Painting(iterations, pm.random_generator())
            self.assertEqual(2 ** (iterations + 1) - 1,
                             len(painting._rectangles))

    def test_accepts_any_iterable_not_only_generators(self):
        for iterable in ([5] * 9, (5,) * 9, range(1, 10), pm.pi_generator()):
            painting = pm.Painting(2, iterable)
            self.assertEqual(4, len(list(painting._get_generation())))

    def test_rejects_a_non_iterable(self):
        with self.assertRaises(SystemExit):
            pm.Painting(2, 42)

    def test_draw_returns_an_image_of_the_requested_size(self):
        img = pm.Painting(3, pm.pi_generator()).draw(4, COLORS, SIZE)
        self.assertEqual(SIZE, img.size)


class TestGetGeneration(unittest.TestCase):
    """Painting._get_generation() -- regression: gen=0 was falsy"""

    def setUp(self):
        self.painting = pm.Painting(3, pm.pi_generator())

    def test_generation_zero_returns_only_the_root_rectangle(self):
        rectangles = list(self.painting._get_generation(0))
        self.assertEqual(1, len(rectangles))
        self.assertEqual(0, rectangles[0].generation)
        self.assertIsNone(rectangles[0].parent)

    def test_each_generation_returns_its_own_rectangles(self):
        for gen in range(4):
            rectangles = list(self.painting._get_generation(gen))
            self.assertEqual(2 ** gen, len(rectangles))
            self.assertTrue(all(r.generation == gen for r in rectangles))

    def test_no_argument_returns_the_last_generation(self):
        rectangles = list(self.painting._get_generation())
        self.assertEqual(8, len(rectangles))
        self.assertTrue(all(r.generation == 3 for r in rectangles))

    def test_drawing_generation_zero_shows_only_the_root_colour(self):
        # the root rectangle uses colour 0, so apart from the black border
        # there is a single colour on the canvas
        img = self.painting.draw(4, COLORS, SIZE, gen=0)
        self.assertEqual({(255, 0, 0)}, self.fills(img))

    def test_drawing_the_last_generation_shows_several_colours(self):
        img = self.painting.draw(4, COLORS, SIZE)
        self.assertGreater(len(self.fills(img)), 1)

    @staticmethod
    def fills(img):
        """Colours on the canvas other than the black of the border"""
        return {colour for _, colour in img.getcolors()} - {(0, 0, 0)}


class TestDegenerateRectangles(unittest.TestCase):
    """draw() -- regression: zero area rectangles crashed Pillow"""

    def test_the_digits_of_pi_never_crash_the_drawing(self):
        for iterations in range(11):
            with self.subTest(iterations=iterations):
                painting = pm.Painting(iterations, pm.pi_generator())
                painting.draw(4, COLORS, SIZE)

    def test_an_exhausted_iterable_never_crashes_the_drawing(self):
        # every missing digit is replaced by a zero, and a zero cut point
        # leaves one of the two children with no area at all
        for iterations in range(11):
            with self.subTest(iterations=iterations):
                pm.Painting(iterations, []).draw(4, COLORS, SIZE)

    def test_a_line_wider_than_the_rectangles_never_crashes(self):
        painting = pm.Painting(6, pm.pi_generator())
        for line in (0, 1, 3, 4, 40, 400):
            with self.subTest(line=line):
                painting.draw(line, COLORS, SIZE)

    def test_every_generation_of_a_deep_painting_can_be_drawn(self):
        painting = pm.Painting(9, pm.pi_generator())
        for gen in range(10):
            with self.subTest(gen=gen):
                painting.draw(4, COLORS, SIZE, gen=gen)

    def test_random_digits_never_crash_the_drawing(self):
        for _ in range(20):
            pm.Painting(8, pm.random_generator()).draw(4, COLORS, SIZE)


class TestSubRectangle(unittest.TestCase):
    """SubRectangle()"""

    def test_the_root_covers_the_whole_canvas(self):
        root = pm.SubRectangle(1, 0, 0)
        self.assertEqual((0, 0), root.zero)
        self.assertEqual((100.0, 100.0), root.end)
        self.assertEqual(0, root.generation)

    def test_the_two_children_split_the_parent_without_overlapping(self):
        root = pm.SubRectangle(1, 0, 0)
        first = pm.SubRectangle(0, 3, 1, root)
        second = pm.SubRectangle(1, 3, 2, root)

        # the first cut is vertical, three tenths across the canvas
        self.assertEqual((0, 0), first.zero)
        self.assertEqual((30.0, 100.0), first.end)
        self.assertEqual((30.0, 0), second.zero)
        self.assertEqual((100.0, 100.0), second.end)

    def test_the_cut_direction_alternates_on_every_generation(self):
        rect = pm.SubRectangle(1, 0, 0)
        directions = []
        for _ in range(5):
            rect = pm.SubRectangle(0, 5, 0, rect)
            directions.append(rect.vert)
        self.assertEqual([False, True, False, True, False], directions)

    def test_a_zero_cut_point_gives_one_child_the_whole_parent(self):
        root = pm.SubRectangle(1, 0, 0)
        first = pm.SubRectangle(0, 0, 1, root)
        second = pm.SubRectangle(1, 0, 2, root)

        self.assertEqual(root.end[0], first.end[0])
        self.assertEqual(second.zero[0], second.end[0])  # no area left


class TestCommandLine(unittest.TestCase):
    """python3 -m pimondrian"""

    @classmethod
    def setUpClass(cls):
        cls.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def run_cli(self, *arguments, stdin=""):
        """Run the CLI in a temporary directory and return (result, dir)"""
        workdir = tempfile.mkdtemp()
        env = dict(os.environ, PYTHONPATH=self.root)
        result = subprocess.run(
            [sys.executable, "-m", "pimondrian"] + list(arguments),
            cwd=workdir, env=env, input=stdin, capture_output=True,
            text=True, timeout=120)
        return result, workdir

    def assertPainted(self, result, workdir, name):
        """The run succeeded and left the expected PNG behind"""
        self.assertEqual(0, result.returncode,
                         "the command failed:\n" + result.stderr)
        self.assertIn(name + ".png", os.listdir(workdir))

    def test_the_default_invocation_paints_a_png(self):
        # regression: five iterations over the digits of Pi used to crash
        result, workdir = self.run_cli("-n", "default")
        self.assertPainted(result, workdir, "default")

    def test_every_iteration_count_paints_a_png(self):
        for iterations in range(1, 11):
            with self.subTest(iterations=iterations):
                result, workdir = self.run_cli("-i", str(iterations),
                                               "-n", "deep")
                self.assertPainted(result, workdir, "deep")

    def test_random_is_honoured_when_stdin_is_not_a_terminal(self):
        # regression: the pipe detection used to swallow --random
        result, workdir = self.run_cli("-r", "-n", "random")
        self.assertPainted(result, workdir, "random")
        self.assertIn("Randomly generated", result.stdout)

    def test_file_is_honoured_when_stdin_is_not_a_terminal(self):
        # regression: the pipe detection used to swallow --file
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as numbers:
            numbers.write("1234567890" * 100)
        result, workdir = self.run_cli("-f", numbers.name, "-n", "fromfile")
        os.unlink(numbers.name)
        self.assertPainted(result, workdir, "fromfile")
        self.assertIn("Extracting digits from file", result.stdout)

    def test_stdin_is_used_when_no_source_is_requested(self):
        result, workdir = self.run_cli("-n", "stdin",
                                       stdin="1234567890" * 100)
        self.assertPainted(result, workdir, "stdin")
        self.assertIn("Reading from stdin", result.stdout)

    def test_a_gallery_paints_one_numbered_png_per_painting(self):
        result, workdir = self.run_cli("-r", "-g", "3", "-n", "gallery")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({"gallery_0.png", "gallery_1.png", "gallery_2.png"},
                         set(os.listdir(workdir)))

    def test_the_size_flags_are_respected(self):
        from PIL import Image
        result, workdir = self.run_cli("-r", "-x", "300", "-y", "200",
                                       "-n", "sized")
        self.assertPainted(result, workdir, "sized")
        with Image.open(os.path.join(workdir, "sized.png")) as img:
            self.assertEqual((300, 200), img.size)

    def test_a_missing_numbers_file_fails_with_a_message(self):
        result, _ = self.run_cli("-f", "/no/such/file.txt")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("error opening numbers file", result.stderr)

    def test_a_missing_colors_file_fails_with_a_message(self):
        result, _ = self.run_cli("-r", "-c", "/no/such/file.txt")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("error opening colors file", result.stderr)


if __name__ == '__main__':
    unittest.main()
