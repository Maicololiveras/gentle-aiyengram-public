import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from binary_ascii import convert_image, inspect_image, remove_background, render_ansi, render_png, render_svg, render_text
from binary_ascii.presentation import build_presentation


class BinaryAsciiTest(unittest.TestCase):
    def test_transparent_shape_and_exports(self):
        source = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
        ImageDraw.Draw(source).ellipse((4, 3, 16, 17), fill=(230, 55, 100, 255))
        frame = convert_image(source, columns=20, rows=20, cell_aspect=1)
        self.assertIsNone(frame.at(0, 0))
        self.assertIsNotNone(frame.at(10, 10))
        self.assertEqual(set(render_text(frame).replace(" ", "").replace("\n", "")), {"0", "1"})
        self.assertIn("\x1b[38;2;", render_ansi(frame))
        self.assertIn("<svg", render_svg(frame))
        self.assertEqual(render_png(frame).size, (160, 240))
        self.assertEqual(frame.records()[0][2] in ("0", "1"), True)

    def test_editable_presentation_and_safe_embedded_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGBA", (12, 12), "#ff80aa").save(root / "shape.png")
            manifest = {"title": "Hello </script>", "scenes": [{"image": "shape.png", "title": "First\\nSecond"}]}
            (root / "input.json").write_text(json.dumps(manifest))
            result = build_presentation(root / "input.json", root / "deck")
            html = (result / "index.html").read_text()
            self.assertIn("\\u003c/script\\u003e", html)
            self.assertIn("scene.title.split('\\n')", html)
            self.assertNotIn("drawImage(source", html)
            self.assertTrue((result / "sources/01-shape.png").is_file())
            self.assertEqual(json.loads((result / "manifest.json").read_text())["scenes"][0]["image"], "sources/01-shape.png")
            with self.assertRaisesRegex(ValueError, "not empty"):
                build_presentation(root / "input.json", root / "deck")

    def test_saturation_retains_hue_and_can_make_glyphs_more_vivid(self):
        source = Image.new("RGB", (8, 8), (145, 80, 75))
        natural = convert_image(source, columns=8, rows=8).at(3, 3)
        vivid = convert_image(source, columns=8, rows=8, saturation=1.25).at(3, 3)
        self.assertGreater(vivid.rgb[0] - vivid.rgb[1], natural.rgb[0] - natural.rgb[1])
        with self.assertRaisesRegex(ValueError, "saturation"):
            convert_image(source, saturation=5)

    def test_terminal_cells_keep_image_proportions_without_side_margins(self):
        source = Image.new("RGB", (20, 20), (220, 40, 30))
        fitted = convert_image(source, columns=20, cell_aspect=.5)
        self.assertEqual((fitted.columns, fitted.rows), (20, 10))
        self.assertIsNotNone(fitted.at(0, 0))
        self.assertIsNotNone(fitted.at(19, 9))
        letterboxed = convert_image(source, columns=20, rows=20, cell_aspect=.5)
        self.assertIsNone(letterboxed.at(10, 0))
        self.assertIsNotNone(letterboxed.at(10, 10))

    def test_remove_background_keeps_enclosed_light_detail_and_original_colors(self):
        image = Image.new("RGB", (90, 90))
        draw = ImageDraw.Draw(image)
        for y in range(90):
            gray = 195 + y // 6
            draw.line((0, y, 89, y), fill=(gray, gray, gray))
        draw.ellipse((20, 16, 70, 66), fill=(240, 240, 240), outline=(40, 45, 50), width=5)
        draw.rectangle((28, 64, 63, 86), fill=(185, 32, 50))
        cut = remove_background(image)
        self.assertLess(cut.getpixel((5, 5))[3], 40)
        self.assertGreater(cut.getpixel((45, 40))[3], 180)
        self.assertGreater(cut.getpixel((40, 75))[3], 210)
        self.assertEqual(cut.getpixel((40, 75))[:3], image.getpixel((40, 75)))
        isolated = convert_image(image, columns=60, cell_aspect=1, remove_background=True)
        preview = render_png(isolated, background=None)
        self.assertEqual(preview.mode, "RGBA")
        self.assertEqual(preview.getpixel((1, 1))[3], 0)
        self.assertGreater(preview.getchannel("A").getextrema()[1], 200)
        self.assertNotIn('<rect', render_svg(isolated, background=None))
        self.assertEqual(inspect_image(image)["suggested_theme"], "light")

        colored = Image.new("RGB", (80, 80), (30, 85, 160))
        ImageDraw.Draw(colored).ellipse((20, 20, 60, 60), fill=(240, 195, 40))
        colored_cut = remove_background(colored)
        self.assertLess(colored_cut.getpixel((4, 4))[3], 40)
        self.assertGreater(colored_cut.getpixel((40, 40))[3], 220)

        transparent = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        transparent.putpixel((4, 4), (255, 50, 30, 255))
        self.assertEqual(remove_background(transparent).getpixel((0, 0))[3], 0)
        self.assertEqual(remove_background(transparent).getpixel((4, 4))[3], 255)


if __name__ == "__main__":
    unittest.main()
