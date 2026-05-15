import unittest

from queue_analysis import simulate_batch, summarize_jobs
from sample_jobs import BATCH_END, BATCH_START, get_sample_job_requests


class QueueAnalysisTests(unittest.TestCase):
    def test_summary_counts_for_reference_batch(self):
        jobs = get_sample_job_requests(batch_date="2026-05-13")

        summary = summarize_jobs(jobs)

        self.assertEqual(summary["job_count"], 10)
        self.assertEqual(summary["exclusive_jobs"], 2)
        self.assertEqual(summary["high_priority_jobs"], 2)
        self.assertEqual(summary["window_counts"]["01:00"], 4)
        self.assertEqual(summary["window_counts"]["02:00"], 3)
        self.assertEqual(summary["window_counts"]["03:00"], 3)

    def test_overloaded_case_has_visible_overflow(self):
        jobs = get_sample_job_requests(batch_date="2026-05-14")

        simulation = simulate_batch(
            jobs, workers=2, batch_start=BATCH_START, batch_end=BATCH_END
        )

        self.assertGreater(simulation["average_wait_minutes"], 200.0)
        self.assertGreater(simulation["overflow_risk"], 0.70)
        self.assertEqual(simulation["max_queue_length"], 10)


if __name__ == "__main__":
    unittest.main()
