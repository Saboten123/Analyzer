import io
import os
from pathlib import Path

import chess.pgn

from flask import Flask, abort, render_template, request, send_file
from analyzer import analyze_pgn
from report import build_pdf_report
from report_store import AnalysisStore

app = Flask(__name__)
app.config["STOCKFISH_DEPTH"] = int(os.environ.get("STOCKFISH_DEPTH", "15"))
analysis_store = AnalysisStore()


@app.route("/")
def home():
    return render_template("index.html", engine_depth=app.config["STOCKFISH_DEPTH"])


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("pgn")
    if file is None or not file.filename:
        return render_template("index.html", error="Please choose a PGN file.", engine_depth=app.config["STOCKFISH_DEPTH"]), 400
    try:
        depth = int(request.form.get("engine_depth", app.config["STOCKFISH_DEPTH"]))
        if not 1 <= depth <= 30:
            raise ValueError("Engine depth must be between 1 and 30.")
        pgn_text = file.read().decode("utf-8")

        analysis = analyze_pgn(pgn_text, depth=depth)

        game = chess.pgn.read_game(io.StringIO(pgn_text))

        moves = []

        if game:
            for move in game.mainline_moves():
                moves.append(move.uci())
    except (UnicodeDecodeError, ValueError, RuntimeError) as error:
        return render_template("index.html", error=str(error), engine_depth=app.config["STOCKFISH_DEPTH"]), 400
    report_token = analysis_store.put(analysis)
    evaluations = [move["played_evaluation"] for move in analysis["moves"]]
    return render_template("result.html", analysis=analysis, report_token=report_token,moves=moves,evaluations=evaluations)


@app.route("/report/<token>.pdf")
def download_report(token: str):
    analysis = analysis_store.get(token)
    if analysis is None:
        abort(404, "This analysis report has expired. Please analyze the PGN again.")
    pdf = build_pdf_report(analysis, Path(app.static_folder))
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name="chess-analysis-report.pdf")


if __name__ == "__main__":
    app.run(debug=True)
