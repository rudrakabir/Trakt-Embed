from datetime import date
import unittest
from public_history import parse_history, as_history
from images import FetchError, render_card


class PublicHistoryTests(unittest.TestCase):
    def test_episode_relative_day(self):
        item = parse_history('Join Trakt\nHistory\nYesterday\nMalcolm in the Middle\nS5 • E17 - Polly in the Middle\n',
                             'episodes', date(2026, 9, 7))
        self.assertEqual(item['watched_at'], '2026-09-06')
        self.assertEqual((item['season'], item['number']), (5, 17))
        self.assertNotIn('UTC', render_card(as_history(item), 'episodes'))

    def test_movie_absolute_day(self):
        item = parse_history('History\nAugust 27th, 2026\nCoach Carter\nMovie\n', 'movies', date(2026,9,7))
        self.assertEqual(item['watched_at'], '2026-08-27')
        self.assertEqual(item['title'], 'Coach Carter')

    def test_incomplete_or_changed_page_fails(self):
        for text in ('Join Trakt', 'History\nNo history', 'History\nYesterday\nTitle\nSomething else',
                     'History\nUnknown date\nTitle\nMovie'):
            with self.subTest(text=text), self.assertRaises(FetchError):
                parse_history(text, 'movies')

    def test_first_entry_wins(self):
        item = parse_history('History\nToday\nNew film\nMovie\nYesterday\nOld film\nMovie', 'movies', date(2026,9,7))
        self.assertEqual(item['title'], 'New film')
