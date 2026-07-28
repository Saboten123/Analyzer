"""Coordinates PGN parsing, engine analysis, chess metrics, and display data."""

from io import StringIO
import chess
import chess.pgn

from engine import StockfishEngine
from evaluation import AccuracySample, ClassificationContext, average, centipawn_loss, player_accuracy, quality_for_move
from graph import evaluation_graph
from opening import detect_opening


def analyze_pgn(pgn_text: str, depth: int = 15) -> dict:
    game = chess.pgn.read_game(StringIO(pgn_text))
    if game is None:
        raise ValueError("No valid game was found in this PGN file.")

    moves = list(game.mainline_moves())
    board = game.board()
    initial_fen = board.fen()
    opening = detect_opening(moves)
    results, white_samples, black_samples = [], [], []
    # Each point is the engine evaluation after the corresponding played move.
    graph_points = []

    with StockfishEngine(depth=depth) as engine:
        for ply, played_move in enumerate(moves, start=1):
            player = board.turn
            played_san = board.san(played_move)
            # First analyse the current position to obtain Stockfish's move.
            # CPL is intentionally not derived from this position's score.
            candidates = engine.analyse_candidates(board, count=3)
            if not candidates:
                raise RuntimeError("Stockfish returned no legal candidate move.")
            best_move = candidates[0].best_move
            best_san = board.san(best_move)

            # Evaluate both one-ply continuations from the identical position.
            best_white_score = engine.evaluate_after_move(board, best_move)
            played_white_score = engine.evaluate_after_move(board, played_move)
            cpl = centipawn_loss(best_white_score, played_white_score, player)
            second_best_score = candidates[1].white_score if len(candidates) > 1 else None
            quality = quality_for_move(ClassificationContext(
                cpl=cpl,
                player=player,
                ply=ply,
                best_white_score=best_white_score,
                played_white_score=played_white_score,
                second_best_white_score=second_best_score,
                is_engine_choice=played_move == best_move,
                is_book=ply <= opening["book_plies"],
                is_sound_sacrifice=_is_sound_sacrifice(board, played_move, cpl),
            ))
            evaluation = round(played_white_score / 100, 2)

            row = {
                "ply": ply, "move_number": (ply + 1) // 2,
                "side": "White" if player == chess.WHITE else "Black",
                "fen_before": board.fen(),
                "played_uci": played_move.uci(), "best_uci": best_move.uci(),
                "played_move": played_san, "best_move": best_san,
                "principal_variation": [
                    {
                        "rank": rank,
                        "move": board.san(candidate.best_move),
                        "evaluation": round(candidate.white_score / 100, 2),
                    }
                    for rank, candidate in enumerate(candidates, start=1)
                ],
                # Scores are White-centric pawns; CPL is mover-centric.
                "evaluation": evaluation,
                "best_evaluation": round(best_white_score / 100, 2),
                "played_evaluation": evaluation,
                "cpl": quality.cpl,
                "classification": quality.classification, "accuracy": quality.accuracy,
            }
            # Advance the game only after both independent continuations have
            # been evaluated. ``evaluate_after_move`` itself always restores
            # the board it receives.
            board.push(played_move)
            row["fen_after"] = board.fen()
            results.append(row)
            graph_points.append({"ply": ply, "evaluation": evaluation})
            sample = AccuracySample(best_white_score, played_white_score, player, ply)
            (white_samples if player == chess.WHITE else black_samples).append(sample)

    white_rows = [row["cpl"] for row in results if row["side"] == "White"]
    black_rows = [row["cpl"] for row in results if row["side"] == "Black"]
    return {
        "analysis_type": "pgn",
        "moves": results,
        "engine_depth": depth,
        "initial_fen": initial_fen,
        "opening_name": opening["opening_name"],
        "ECO_code": opening["ECO_code"],
        "opening": opening,
        "white_accuracy": player_accuracy(white_samples),
        "black_accuracy": player_accuracy(black_samples),
        "white_average_cpl": average(white_rows),
        "black_average_cpl": average(black_rows),
        "average_cpl": average([row["cpl"] for row in results]),
        "evaluation_graph": evaluation_graph(graph_points),
    }
    
def analyze_fen(fen: str, depth: int = 15) -> dict:
    try:
        board = chess.Board(fen)
    except ValueError:
        raise ValueError("Invalid FEN position.")

    with StockfishEngine(depth=depth) as engine:
        candidates = engine.analyse_candidates(board, count=3)

        if not candidates:
            raise RuntimeError("Stockfish returned no legal moves.")

        best_move = candidates[0].best_move
        best_san = board.san(best_move)
        best_white_score = candidates[0].white_score

    evaluation = round(best_white_score / 100, 2)

    return {
        "analysis_type": "fen",
        "engine_depth": depth,
        "initial_fen": fen,
        "opening_name": "N/A",
        "ECO_code": "N/A",
        "opening": {
            "opening_name": "N/A",
            "ECO_code": "N/A",
            "book_plies": 0,
        },
        "moves": [],
        "white_accuracy": None,
        "black_accuracy": None,
        "white_average_cpl": None,
        "black_average_cpl": None,
        "average_cpl": None,
        "evaluation_graph": None,
        "best_move": best_san,
        "evaluation": evaluation,
        "principal_variation": [
            {
                "rank": rank,
                "move": board.san(candidate.best_move),
                "evaluation": round(candidate.white_score / 100, 2),
            }
            for rank, candidate in enumerate(candidates, start=1)
        ],
    }


def _is_sound_sacrifice(board: chess.Board, move: chess.Move, cpl: int) -> bool:
    """Conservatively identify a Stockfish-approved material sacrifice.

    A non-pawn must voluntarily move onto a square where a lower-value enemy
    piece can legally take it. Zero CPL means the engine still endorses it.
    This intentionally avoids calling ordinary attacked moves brilliant.
    """
    if cpl != 0 or board.is_capture(move):
        return False
    moved_piece = board.piece_at(move.from_square)
    if moved_piece is None or moved_piece.piece_type == chess.PAWN:
        return False
    values = {chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
    moved_value = values.get(moved_piece.piece_type, 0)
    board.push(move)
    try:
        for reply in board.legal_moves:
            if reply.to_square != move.to_square:
                continue
            attacker = board.piece_at(reply.from_square)
            if attacker and values.get(attacker.piece_type, 1) < moved_value:
                return True
        return False
    finally:
        board.pop()
