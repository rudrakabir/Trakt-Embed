import contextlib
import io
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch
import embed


class AuthTests(unittest.TestCase):
    def test_refresh_refuses_before_rotating_without_output(self):
        with patch.dict(os.environ, {}, clear=True), patch('requests.post') as post, \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                runpy.run_path('refresh_trakt_token.py')
            post.assert_not_called()

    def test_refresh_outputs_masked_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'output'
            env = {'TRAKT_CLIENT_ID': 'id', 'TRAKT_CLIENT_SECRET': 'secret',
                   'TRAKT_REFRESH_TOKEN': 'old', 'GITHUB_OUTPUT': str(output)}
            response = Mock(status_code=200)
            response.json.return_value = {'access_token': 'new-access', 'refresh_token': 'new-refresh'}
            log = io.StringIO()
            with patch.dict(os.environ, env, clear=True), patch('requests.post', return_value=response), \
                 contextlib.redirect_stdout(log):
                runpy.run_path('refresh_trakt_token.py')
            self.assertIn('::add-mask::new-access', log.getvalue())
            self.assertNotIn('NEW_ACCESS_TOKEN=', log.getvalue())
            self.assertIn('refresh_token=new-refresh', output.read_text())

    def test_device_poll_respects_slowdown(self):
        device = Mock(status_code=200)
        device.json.return_value = {'expires_in': 100, 'interval': 2,
                                    'verification_url': 'https://trakt.tv/activate',
                                    'user_code': 'example', 'device_code': 'device'}
        log = io.StringIO()
        with patch.dict(os.environ, {'TRAKT_CLIENT_ID': 'id', 'TRAKT_CLIENT_SECRET': 'secret'}), \
             patch('embed.load_dotenv'), patch('embed.requests.post', side_effect=[device, Mock(status_code=429), Mock(status_code=403)]), \
             patch('embed.time.sleep') as sleep, patch('embed.time.monotonic', return_value=0), \
             contextlib.redirect_stdout(log):
            self.assertEqual(embed.main(), 1)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 7])


if __name__ == '__main__':
    unittest.main()
