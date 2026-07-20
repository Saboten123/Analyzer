"""Regression tests for mover-perspective CPL arithmetic."""

import chess
import unittest

from evaluation import AccuracySample, centipawn_loss, player_accuracy


class CentipawnLossTests(unittest.TestCase):
    def test_white_loss_uses_white_perspective(self):
        self.assertEqual(centipawn_loss(80, 25, chess.WHITE), 55)

    def test_black_loss_uses_black_perspective(self):
        # For Black, the more negative White score is the better continuation.
        self.assertEqual(centipawn_loss(-80, -25, chess.BLACK), 55)

    def test_mate_like_scores_remain_ordered(self):
        # MATE_SCORE conversion retains mate ordering in a large score range.
        self.assertEqual(centipawn_loss(99_995, -99_995, chess.WHITE), 199_990)
        self.assertEqual(centipawn_loss(-99_995, 99_995, chess.BLACK), 199_990)

    def test_game_accuracy_uses_expected_score_retention(self):
        perfect = [AccuracySample(50, 50, chess.WHITE, 1)]
        imperfect = [
            AccuracySample(100, 50, chess.WHITE, 1),
            AccuracySample(100, 50, chess.WHITE, 3),
        ]
        self.assertEqual(player_accuracy(perfect), 100.0)
        self.assertLess(player_accuracy(imperfect), 100.0)


if __name__ == "__main__":
    unittest.main()
