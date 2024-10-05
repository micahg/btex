import unittest
import unittest.mock as mock
from unittest.mock import MagicMock


import btex

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

    @mock.patch('os.listdir', MagicMock(return_value=['The Late Show with Stephen Colbert']))
    @mock.patch('os.path.isdir', MagicMock(return_value=True))
    @mock.patch('btex.send_email', MagicMock(return_value=None))
    @mock.patch('btex.process_mkv_folder', MagicMock(return_value=True))
    def test_process_params(self):
        tests = [
            {
                'name': 'Stephen.Colbert',
                'episode': '2024.10.03',
                'dirs': ['The Late Show with Stephen Colbert'],
                'path': 'Stephen.Colbert.2024.10.03.Chris.Wallace.720p.HEVC.x265-MeGusta',
            },
        ]
        for test in tests:
            btex.process_params(test['name'], test['episode'], test['path'])

    @mock.patch('builtins.open', mock.mock_open(read_data='{"smtphost": "SMTPHOST","username": "USER","password": "PASSWORD","sender": "SENDER","recipient": "RECIPIENT"}'))
    def test_send_email(self):
        with mock.patch('smtplib.SMTP', autospec=True) as mock_smtplib:
            btex.send_email('SUBJ', 'BODY')

            mock_smtplib.assert_called_once_with('SMTPHOST', 587)
            mock_smtp = mock_smtplib.return_value #.__enter__.return_value
            mock_smtp.ehlo.assert_called_once()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with('USER', 'PASSWORD')
            mock_smtp.sendmail.assert_called_once_with('SENDER', 'RECIPIENT', 'Subject: SUBJ\nBODY')
            mock_smtp.quit.assert_called_once()