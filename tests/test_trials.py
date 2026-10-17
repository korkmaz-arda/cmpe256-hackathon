"""Standalone smoke and boundary tests for the local clinical trials tools."""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tools.trials import call_tool, dataset_stats, instrument_usage, search_trials


class TrialsTests(unittest.TestCase):
    def test_instrument_mentions(self):
        usage = instrument_usage('seahorse')
        self.assertGreaterEqual(usage['total'], 10)
        self.assertEqual(usage['total'], sum(usage['per_dataset'].values()))
        for trial in usage['trials']:
            self.assertNotIn('partisan', trial['measurement_sentence'].lower())
        artisan = instrument_usage('artisan')
        for trial in artisan['trials']:
            self.assertRegex(trial['measurement_sentence'].lower(), r'\bartisan\b')

    def test_search(self):
        results = search_trials('mitochondrial function PBMC', dataset='diabetes', k=3)
        self.assertGreater(len(results), 0)
        self.assertLessEqual(len(results), 3)
        for trial in results:
            self.assertRegex(trial['nct_id'], r'^NCT\d+$')
            self.assertLessEqual(len(trial['snippet']), 300)
        self.assertEqual(search_trials('anything', k=0), [])
        self.assertEqual(search_trials(''), [])
        self.assertEqual(search_trials('mitochondrial', status='NONEXISTENT'), [])

    def test_stats_and_dispatch(self):
        stats = dataset_stats()
        self.assertEqual(stats['total'], 32611)
        self.assertEqual(stats['total'], sum(stats['by_dataset'].values()))
        self.assertEqual(call_tool('search_trials', {'query': '', 'k': 1}), [])
        with self.assertRaises(ValueError):
            call_tool('unknown', {})
        with self.assertRaises(ValueError):
            search_trials('test', dataset='unknown')


if __name__ == '__main__':
    unittest.main(verbosity=2)
