"""Opening identification from a PGN main line using an embedded ECO book."""

from dataclasses import dataclass
import chess


@dataclass(frozen=True)
class OpeningLine:
    moves: tuple[str, ...]
    eco_code: str
    opening_name: str


# python-chess parses and validates PGN but intentionally does not ship a
# large ECO database. This small, easily extensible book uses UCI prefixes;
# the longest matching line always wins.
OPENING_BOOK: tuple[OpeningLine, ...] = (
    OpeningLine(("e2e4", "c7c5"), "B20", "Sicilian Defense"),
    OpeningLine(("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6"), "B50", "Sicilian Defense, Classical Variation"),
    OpeningLine(("e2e4", "e7e5", "g1f3", "b8c6", "f1b5"), "C60", "Ruy Lopez"),
    OpeningLine(("e2e4", "e7e5", "g1f3", "b8c6", "f1c4"), "C50", "Italian Game"),
    OpeningLine(("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7"), "E60", "King's Indian Defense"),
    OpeningLine(("d2d4", "d7d5", "c2c4", "e7e6"), "D30", "Queen's Gambit Declined"),
    OpeningLine(("d2d4", "d7d5", "c2c4"), "D06", "Queen's Gambit"),
    OpeningLine(("e2e4", "e7e5"), "C20", "King's Pawn Game"),
    OpeningLine(("d2d4", "d7d5"), "D00", "Queen's Pawn Game"),
)


def detect_opening(moves: list[chess.Move]) -> dict[str, str]:
    prefix = tuple(move.uci() for move in moves)
    matches = [opening for opening in OPENING_BOOK if prefix[:len(opening.moves)] == opening.moves]
    if not matches:
        return {"ECO_code": "", "opening_name": "Unknown opening", "book_plies": 0}
    opening = max(matches, key=lambda item: len(item.moves))
    return {
        "ECO_code": opening.eco_code,
        "opening_name": opening.opening_name,
        "book_plies": len(opening.moves),
    }
