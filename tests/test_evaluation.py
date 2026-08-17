import unittest
from evaluation import compute_achievement_rate, qualitative_check, validate_difficulty_change, time_lag_check

class TestEvaluation(unittest.TestCase):
    def test_increase_goal_achievement(self):
        # baseline 50 -> target 100, actual 75 -> 50%
        rate = compute_achievement_rate(50, 100, 75, 'increase')
        self.assertAlmostEqual(rate, 50.0)

    def test_decrease_goal_achievement(self):
        # baseline 200 -> target 100, actual 150 -> 50%
        rate = compute_achievement_rate(200, 100, 150, 'decrease')
        self.assertAlmostEqual(rate, 50.0)

    def test_zero_division_and_missing(self):
        # baseline == target -> None
        self.assertIsNone(compute_achievement_rate(100, 100, 110, 'increase'))
        # missing values -> None
        self.assertIsNone(compute_achievement_rate(None, 100, 110, 'increase'))

    def test_qualitative_evidence_insufficient(self):
        ok, score = qualitative_check('')
        self.assertFalse(ok)
        ok2, score2 = qualitative_check('Deployed guide')
        # short evidence should be considered present but low specificity
        self.assertTrue(ok2)
        self.assertLess(score2, 0.2)

    def test_difficulty_change_requires_reason(self):
        planned = {'technical_uncertainty':3}
        actual = {'technical_uncertainty':4}
        # missing reason/evidence -> invalid
        self.assertFalse(validate_difficulty_change(planned, actual, '', ''))
        # with reason/evidence -> valid
        self.assertTrue(validate_difficulty_change(planned, actual, 'Scope changed', 'See notes'))

    def test_time_lag_and_movement_checks(self):
        # contribution on Jan, evaluation on Jun -> >3 months
        self.assertTrue(time_lag_check('2025-01-01', '2025-06-01', threshold_months=3))
        # within threshold
        self.assertFalse(time_lag_check('2025-03-01', '2025-04-01', threshold_months=3))

if __name__ == '__main__':
    unittest.main()
