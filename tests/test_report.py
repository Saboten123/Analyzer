from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from report import build_pdf_report


class PdfReportTests(unittest.TestCase):
    def test_builds_a_pdf_from_analysis_data(self):
        analysis = {
            "opening_name": "Ruy Lopez", "ECO_code": "C60", "white_accuracy": 95.0,
            "black_accuracy": 92.0, "white_average_cpl": 12.0, "black_average_cpl": 18.0,
            "average_cpl": 15.0, "engine_depth": 15, "evaluation_graph": None,
            "moves": [{"move_number": 1, "side": "White", "played_move": "e4", "best_move": "e4", "played_evaluation": 0.2, "cpl": 0, "classification": "Best"}],
        }
        with TemporaryDirectory() as directory:
            pdf = build_pdf_report(analysis, Path(directory))
        self.assertTrue(pdf.read(4).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
