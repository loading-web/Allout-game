import contextlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('importer', Path(__file__).resolve().parents[1] / 'tools/import_game_player.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.res = Path(self.temp.name)
        self.folder = self.res / 'game_player'
        self.folder.mkdir()
        # Only PNG metadata is read by the importer. No raster decoding is needed.
        (self.folder / 'character.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'\0'*8 + struct.pack('>II', 256, 256))
        self.xml = self.folder / 'character.xml'

    def parse(self, body):
        self.xml.write_text('<TextureAtlas imagePath="character.png">' + body + '</TextureAtlas>')
        return importer.parse_atlas(self.xml, self.res)

    def test_numeric_order_and_arbitrary_names(self):
        body = ''.join(f'<SubTexture name="{name}" x="0" y="0" width="10" height="10"/>' for name in ['Jump0010', 'Idle0001', 'Jump0002', 'Jump0000', 'Dance &amp; Wave0001'])
        _, _, _, groups = self.parse(body)
        self.assertEqual([f[0] for f in groups['Jump']], [0, 2, 10])
        self.assertEqual(len(groups['Idle']), 1)
        self.assertIn('Dance & Wave', groups)

    def test_trim_fields(self):
        _, _, _, groups = self.parse('<SubTexture name="Idle0000" x="1" y="2" width="20" height="30" frameX="-5" frameY="-6" frameWidth="40" frameHeight="50"/>')
        self.assertEqual(groups['Idle'][0][2], (1, 2, 20, 30, -5, -6, 40, 50))

    def test_defaults_and_unnumbered(self):
        _, _, _, groups = self.parse('<SubTexture name="Still" x="0" y="0" width="20" height="30"/>')
        self.assertEqual(groups['Still'][0][2][-4:], (0, 0, 20, 30))

    def test_missing_texture(self):
        (self.folder / 'character.png').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing texture'):
            self.parse('')

    def test_invalid_xml(self):
        with self.assertRaises(importer.ET.ParseError):
            self.parse('<SubTexture')

    def test_invalid_bounds(self):
        with self.assertRaisesRegex(ValueError, 'out-of-bounds'):
            self.parse('<SubTexture name="Idle0" x="250" y="0" width="20" height="30"/>')

    def test_duplicate_names(self):
        node = '<SubTexture name="Idle0" x="0" y="0" width="20" height="30"/>'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.parse(node*2)

    def test_spine_precedence(self):
        self.xml.write_text('broken XML must not be parsed when Spine exists')
        (self.folder / 'character.spine').write_text('{}')
        output = self.res / 'generated.csl'
        importer.generate(self.res, output)
        self.assertIn('game_player/character.spine', output.read_text())

    def test_generated_atlas_code_and_logging(self):
        self.parse('<SubTexture name="Jump0000" x="0" y="0" width="20" height="30"/>')
        output = self.res / 'generated.csl'
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            importer.generate(self.res, output)
        self.assertIn("Animation 'Jump': 1 frames", log.getvalue())
        self.assertIn('d.texture_path = "game_player/character.png"', output.read_text())
        self.assertIn('Game_Player_Frame{', output.read_text())


if __name__ == '__main__':
    unittest.main()
