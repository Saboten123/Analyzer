"""Professional PDF rendering for a completed chess analysis."""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_report(analysis: dict, static_directory: Path) -> BytesIO:
    """Return a PDF report for an already-computed analysis object.

    The function only formats existing data; it never invokes Stockfish. This
    keeps the download deterministic and avoids making users wait twice.
    """
    output = BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#1e293b"))
    subtitle = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], alignment=TA_CENTER, textColor=colors.HexColor("#475569"))
    opening_label = analysis["opening_name"]
    if analysis["ECO_code"]:
        opening_label += f" ({analysis['ECO_code']})"
    story = [
        Paragraph("Chess Analysis Report", title),
        Paragraph(opening_label, subtitle),
        Spacer(1, 16),
    ]

    summary = [
        ["White Accuracy", f"{analysis['white_accuracy']}%", "Black Accuracy", f"{analysis['black_accuracy']}%"],
        ["White Avg CPL", str(analysis['white_average_cpl']), "Black Avg CPL", str(analysis['black_average_cpl'])],
        ["Game Avg CPL", str(analysis['average_cpl']), "Engine Depth", str(analysis['engine_depth'])],
    ]
    summary_table = Table(summary, colWidths=[1.3 * inch, 1.0 * inch, 1.3 * inch, 1.0 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([Paragraph("Summary", styles["Heading2"]), summary_table, Spacer(1, 16)])

    graph_filename = analysis.get("evaluation_graph") or ""
    graph_path = static_directory / graph_filename
    if graph_filename and graph_path.is_file():
        graph = Image(str(graph_path), width=6.7 * inch, height=2.14 * inch)
        story.extend([Paragraph("Evaluation Graph", styles["Heading2"]), graph, Spacer(1, 16)])

    rows = [["Move", "Played", "Best", "Eval", "CPL", "Classification"]]
    for move in analysis["moves"]:
        move_label = f"{move['move_number']}{'.' if move['side'] == 'White' else '...'}"
        rows.append([
            move_label, move["played_move"], move["best_move"],
            f"{move['played_evaluation']:+.2f}", str(move["cpl"]), move["classification"],
        ])
    move_table = Table(rows, repeatRows=1, colWidths=[.55 * inch, .9 * inch, .9 * inch, .65 * inch, .5 * inch, 1.55 * inch])
    move_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#cbd5e1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.extend([Paragraph("Move Analysis", styles["Heading2"]), move_table])
    document.build(story)
    output.seek(0)
    return output
