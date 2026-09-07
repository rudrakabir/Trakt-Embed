import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import requests
import images

MOVIE = {'movie': {'title': '<script>alert(1)</script>', 'year': 2024, 'ids': {}},
         'watched_at': '2026-06-01T14:00:00+02:00'}


class WidgetTests(unittest.TestCase):
    def test_public_history_needs_no_oauth_and_feed_contains_only_display_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, feed = Path(tmp) / 'widget.html', Path(tmp) / 'data.json'
            with patch.dict(os.environ, {'TRAKT_CLIENT_ID': 'test'}, clear=True), \
                 patch('images.load_dotenv'), \
                 patch('images.fetch_last_watched', side_effect=[None, MOVIE]) as fetch, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(images.main(['--username', 'rudrakabir', '--output', str(path),
                                              '--json-output', str(feed)]), 0)
            self.assertNotIn('Authorization', fetch.call_args.args[1])
            self.assertEqual(fetch.call_args.kwargs['username'], 'rudrakabir')
            data = json.loads(feed.read_text())
            self.assertEqual(data['version'], 1)
            self.assertEqual(data['items'][0]['title'], MOVIE['movie']['title'])
            self.assertNotIn('ids', data['items'][0])

    def test_failed_update_preserves_json_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, feed = Path(tmp) / 'widget.html', Path(tmp) / 'data.json'
            path.write_text('last good widget')
            feed.write_text('last good feed')
            with patch.dict(os.environ, {'TRAKT_CLIENT_ID': 'test'}), \
                 patch('images.fetch_last_watched', side_effect=images.FetchError('unavailable')), \
                 contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(images.main(['--username', 'rudrakabir', '--output', str(path),
                                              '--json-output', str(feed)]), 1)
            self.assertEqual(path.read_text(), 'last good widget')
            self.assertEqual(feed.read_text(), 'last good feed')

    def test_http_errors_are_not_empty_history(self):
        for status in (403, 429, 500, 503):
            with self.subTest(status=status):
                session = Mock()
                session.get.return_value.status_code = status
                with self.assertRaises(images.FetchError):
                    images.fetch_last_watched('movies', {}, session)

    def test_auth_error_is_distinct(self):
        session = Mock()
        session.get.return_value.status_code = 401
        with self.assertRaises(images.AuthError):
            images.fetch_last_watched('episodes', {}, session)

    def test_history_validation_and_empty_list(self):
        for data in ({}, [None], [{'movie': {}}]):
            session = Mock()
            session.get.return_value.status_code = 200
            session.get.return_value.json.return_value = data
            with self.assertRaises(images.FetchError):
                images.fetch_last_watched('movies', {}, session)
        session.get.return_value.json.return_value = []
        self.assertIsNone(images.fetch_last_watched('movies', {}, session))
        self.assertEqual(session.get.call_args.kwargs['params'], {'limit': 1})
        self.assertIn('timeout', session.get.call_args.kwargs)

    def test_escape_and_utc_and_missing_artwork(self):
        html = images.render_html(None, MOVIE)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('12:00 UTC', html)
        self.assertIn('placeholder', html)
        self.assertNotIn('/path/to/default', html)
        self.assertIn('No watch history yet.', html)

    def test_artwork_failure_is_optional(self):
        session = Mock()
        session.get.side_effect = requests.Timeout()
        self.assertIsNone(images.get_tmdb_image({'ids': {'tmdb': 1}}, 'movie', 'test', session))
        self.assertIsNone(images.get_tmdb_image({'ids': {}}, 'movie', 'test', session))

    def test_fragment_has_no_document_wrapper(self):
        html = images.render_html(None, MOVIE, fragment=True)
        self.assertNotIn('<html', html)
        self.assertIn('<section', html)

    def test_failed_update_preserves_previous_file(self):
        for error, code in [(images.FetchError('unavailable'), 1), (images.AuthError('expired'), 10)]:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'widget.html'
                path.write_text('last good widget')
                with patch.dict(os.environ, {'TRAKT_CLIENT_ID': 'test', 'TRAKT_ACCESS_TOKEN': 'test'}), \
                     patch('images.fetch_last_watched', side_effect=[None, error]), \
                     contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(images.main(['--output', str(path)]), code)
                self.assertEqual(path.read_text(), 'last good widget')

    def test_success_writes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'widget.html'
            with patch.dict(os.environ, {'TRAKT_CLIENT_ID': 'test', 'TRAKT_ACCESS_TOKEN': 'test'}), \
                 patch('images.fetch_last_watched', side_effect=[None, MOVIE]), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(images.main(['--output', str(path)]), 0)
            self.assertIn('Recently watched', path.read_text())


if __name__ == '__main__':
    unittest.main()
