from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from graph import evaluation_graph


class EvaluationGraphTests(unittest.TestCase):
    def test_writes_a_png_under_static_graphs(self):
        with TemporaryDirectory() as directory:
            static_directory = Path(directory)
            relative_path = evaluation_graph(
                [{"ply": 1, "evaluation": 0.4}, {"ply": 2, "evaluation": -0.2}],
                static_directory,
            )
            self.assertIsNotNone(relative_path)
            self.assertTrue((static_directory / relative_path).is_file())


if __name__ == "__main__":
    unittest.main()
