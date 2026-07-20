"""Small, deterministic wrapper around the Stockfish UCI process."""

from pathlib import Path
from dataclasses import dataclass
import chess
import chess.engine
import os

MATE_SCORE = 100_000


@dataclass(frozen=True)
class PositionAnalysis:
    """Stockfish's score and principal variation move for one position.

    ``white_score`` is expressed in centipawns from White's perspective.
    Mate scores are converted to values around ``MATE_SCORE`` while retaining
    mate distance, which lets callers order mates correctly with normal scores.
    """

    white_score: int
    best_move: chess.Move


class StockfishEngine:
    """Own one Stockfish process for the duration of an analysis."""

    def __init__(self, path: str | Path | None = None, depth: int = 15):
        default_path = Path(os.getenv("STOCKFISH_PATH", str(Path(__file__).parent / "Stockfish" / "stockfish.exe"))
)
        self.path = str(path or default_path)
        self.depth = depth
        self._engine: chess.engine.SimpleEngine | None = None

    def __enter__(self):
        self._engine = chess.engine.SimpleEngine.popen_uci(self.path)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self) -> None:
        if self._engine is not None:
            self._engine.quit()
            self._engine = None

    def analyse(self, board: chess.Board) -> dict:
        if self._engine is None:
            raise RuntimeError("Stockfish has not been started.")
        # python-chess serializes a board asynchronously to the UCI process.
        # A private copy prevents a caller's push/pop from changing that board
        # while the command is still being finalized.
        return self._engine.analyse(board.copy(stack=False), chess.engine.Limit(depth=self.depth))

    def analyse_position(self, board: chess.Board) -> PositionAnalysis:
        """Evaluate ``board`` and return Stockfish's recommended first move."""
        info = self.analyse(board)
        if not info.get("pv"):
            raise RuntimeError("Stockfish returned no principal variation.")
        score = info["score"].pov(chess.WHITE).score(mate_score=MATE_SCORE)
        return PositionAnalysis(white_score=score, best_move=info["pv"][0])

    def analyse_candidates(self, board: chess.Board, count: int = 2) -> list[PositionAnalysis]:
        """Return Stockfish's top root candidates for a position.

        The second candidate is used only to identify an engine-proven
        "only move". CPL itself uses separately evaluated continuations.
        """
        if self._engine is None:
            raise RuntimeError("Stockfish has not been started.")
        infos = self._engine.analyse(
            board.copy(stack=False), chess.engine.Limit(depth=self.depth), multipv=count
        )
        candidates = []
        for info in infos:
            if info.get("pv"):
                score = info["score"].pov(chess.WHITE).score(mate_score=MATE_SCORE)
                candidates.append(PositionAnalysis(score, info["pv"][0]))
        return candidates

    def evaluate_after_move(self, board: chess.Board, move: chess.Move) -> int:
        """Evaluate a one-move continuation without changing the caller's board.

        The returned score is always White-centric. Therefore, the best-move
        and played-move continuations can be compared on the same scale.
        """
        board.push(move)
        try:
            return self.analyse_position(board).white_score
        finally:
            board.pop()
