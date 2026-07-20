import chess
import chess.engine

engine = chess.engine.SimpleEngine.popen_uci(
    "Stockfish/stockfish.exe"
)

board = chess.Board()

result = engine.play(board, chess.engine.Limit(depth=15))

print("Best Move:", result.move)

engine.quit()