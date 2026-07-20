import chess
import unittest

from opening import detect_opening


class OpeningDetectionTests(unittest.TestCase):
    def test_prefers_the_most_specific_matching_line(self):
        board = chess.Board()
        moves = []
        for san in ("e4", "e5", "Nf3", "Nc6", "Bb5"):
            move = board.parse_san(san)
            moves.append(move)
            board.push(move)
        opening = detect_opening(moves)
        self.assertEqual(opening["opening_name"], "Ruy Lopez")
        self.assertEqual(opening["ECO_code"], "C60")


if __name__ == "__main__":
    unittest.main()
