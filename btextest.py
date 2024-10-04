import unittest

import btex
# from btex import hi

class TestBtex(unittest.TestCase):
    def test_get_show_name_and_episode_and_path(self):
        tests = [
            {
                'file': 'me and you S9999E888888 some suffix.torrent',
                'name': 'me and you',
                'episode': 'S9999E888888',
                'path': 'me and you S9999E888888 some suffix'
            },
            {
                'file': 'Stephen.Colbert.2024.10.02.Andrew.Garfield.1080p.HEVC.x265-MeGusta.torrent',
                'name': 'Stephen.Colbert',
                'episode': '2024.10.02',
                'path': 'Stephen.Colbert.2024.10.02.Andrew.Garfield.1080p.HEVC.x265-MeGusta'
            },
            {
                'file': 'The Lord of the Rings The Rings of Power S02E08 Shadow and Flame 2160p AMZN WEB-DL DDP5 1 HDR H 265-NTb.torrent',
                'name': 'The Lord of the Rings The Rings of Power',
                'episode': 'S02E08',
                'path': 'The Lord of the Rings The Rings of Power S02E08 Shadow and Flame 2160p AMZN WEB-DL DDP5 1 HDR H 265-NTb'
            },
            {
                'file': 'The Lord of the Rings The Rings of Power S02E08 Shadow and Flame 2160p AMZN WEB-DL DDP5 1 Atmos DV HDR H 265-FLUX [TD].torrent',
                'name': 'The Lord of the Rings The Rings of Power',
                'episode': 'S02E08',
                'path': 'The Lord of the Rings The Rings of Power S02E08 Shadow and Flame 2160p AMZN WEB-DL DDP5 1 Atmos DV HDR H 265-FLUX'
            }
        ]
        for test in tests:
            name, episode, path = btex.get_show_name_and_episode_and_path(test['file'])
            self.assertEqual(name, test['name'])
            self.assertEqual(episode, test['episode'])
            self.assertEqual(path, test['path'])
