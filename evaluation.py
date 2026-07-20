"""CPL, accuracy, and outcome-aware move classification."""

from dataclasses import dataclass
from math import exp, log
import chess
import chess.engine


@dataclass(frozen=True)
class MoveQuality:
    cpl: int
    accuracy: float
    classification: str


@dataclass(frozen=True)
class ClassificationContext:
    """The engine evidence used by the ordered classification rule set."""

    cpl: int
    player: chess.Color
    ply: int
    best_white_score: int
    played_white_score: int
    second_best_white_score: int | None = None
    is_engine_choice: bool = False
    is_book: bool = False
    is_sound_sacrifice: bool = False


@dataclass(frozen=True)
class AccuracySample:
    """One player's best and played continuation evaluations for one ply."""

    best_white_score: int
    played_white_score: int
    player: chess.Color
    ply: int


def score_for_player(white_score: int, player: chess.Color) -> int:
    """Convert a White-centric score to the perspective of ``player``."""
    return white_score if player == chess.WHITE else -white_score


def centipawn_loss(best_continuation_white_score: int, played_continuation_white_score: int, player: chess.Color) -> int:
    """Return loss between best and played continuations of one position."""
    best = score_for_player(best_continuation_white_score, player)
    played = score_for_player(played_continuation_white_score, player)
    return max(0, best - played)


def move_accuracy(cpl: int) -> float:
    """Smooth local accuracy metric; separate from the classification rules."""
    return round(max(0.0, min(100.0, 103.1668 * exp(-0.04354 * cpl) - 3.1669)), 2)


def _wdl(score: int, player: chess.Color, ply: int) -> chess.engine.Wdl:
    """Convert a score to Stockfish's mover-centric WDL expectation."""
    return chess.engine.PovScore(chess.engine.Cp(score), player).wdl(model="sf", ply=ply).relative


def _expected_score(score: int, player: chess.Color, ply: int) -> float:
    """Return Stockfish WDL expected score in the range 0.0 to 1.0."""
    wdl = _wdl(score, player, ply)
    return (wdl.wins + 0.5 * wdl.draws) / 1000


def player_accuracy(samples: list[AccuracySample]) -> float:
    """Calculate game accuracy from retained Stockfish expected score.

    For each move, ``retention = played_expected_score / best_expected_score``.
    The game result is the geometric mean of these retentions, multiplied by
    100. Unlike averaging per-move percentages, this compounds independent
    losses of winning/drawing chances and prevents many small errors from being
    hidden by a few perfect moves. Positions with no remaining expected score
    contribute neutral retention because there is no practical result left to
    preserve.

    The WDL conversion follows Stockfish's model; the aggregation is an
    explainable local approximation inspired by public engine-analysis sites,
    not a claim to reproduce Chess.com's proprietary formula.
    """
    log_retentions = []
    for sample in samples:
        best = _expected_score(sample.best_white_score, sample.player, sample.ply)
        played = _expected_score(sample.played_white_score, sample.player, sample.ply)
        if best == 0:
            continue
        retention = max(0.0, min(1.0, played / best))
        # A zero retention has a well-defined 0% result; do not take log(0).
        if retention == 0:
            return 0.0
        log_retentions.append(log(retention))
    return round(100 * exp(sum(log_retentions) / len(log_retentions)), 2) if log_retentions else 100.0


def _dominant_outcome(wdl: chess.engine.Wdl) -> str:
    """Return the engine's most likely practical result."""
    outcomes = {"win": wdl.wins, "draw": wdl.draws, "loss": wdl.losses}
    return max(outcomes, key=outcomes.get)


def classify_move(context: ClassificationContext) -> str:
    """Classify by Stockfish WDL outcome changes, not fixed CPL buckets.

    CPL remains the precise numeric loss. The label instead reflects whether a
    move loses a win, a draw, or merely practical chances in this position.
    New rules can be inserted above the general WDL rules without changing the
    analysis pipeline.
    """
    if context.is_book:
        return "Book"
    if context.cpl == 0 and context.is_engine_choice and context.is_sound_sacrifice:
        return "Brilliant"

    best_wdl = _wdl(context.best_white_score, context.player, context.ply)
    played_wdl = _wdl(context.played_white_score, context.player, context.ply)
    best_outcome = _dominant_outcome(best_wdl)
    played_outcome = _dominant_outcome(played_wdl)

    if context.second_best_white_score is not None:
        second_wdl = _wdl(context.second_best_white_score, context.player, context.ply)
        if context.is_engine_choice and _dominant_outcome(second_wdl) != best_outcome:
            return "Great"
    if context.cpl == 0:
        return "Best"
    if played_wdl == best_wdl:
        return "Excellent"
    if played_outcome == best_outcome:
        return "Good" if played_wdl.losses <= best_wdl.losses else "Inaccuracy"
    if best_outcome == "win" and played_outcome == "draw":
        return "Mistake"
    if best_outcome in {"win", "draw"} and played_outcome == "loss":
        return "Blunder"
    if best_outcome == "loss" and played_outcome in {"draw", "win"}:
        return "Great"
    return "Inaccuracy"


def quality_for_move(context: ClassificationContext) -> MoveQuality:
    return MoveQuality(context.cpl, move_accuracy(context.cpl), classify_move(context))


def average(values: list[float | int]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0
