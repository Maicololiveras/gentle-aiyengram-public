import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from binary_ascii import convert_image, render_ansi, render_png, render_svg, render_text
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


if __name__ == "__main__":
    unittest.main()
