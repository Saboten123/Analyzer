"""Generate persistent evaluation charts for analyzed games."""

from pathlib import Path
from uuid import uuid4
import os


def evaluation_graph(points: list[dict], static_directory: Path | None = None) -> str | None:
    """Save a White-centric evaluation chart and return its static-relative path.

    Every point represents the evaluation after a played half-move. Positive
    values favor White and negative values favor Black. A unique filename keeps
    simultaneous analyses from overwriting one another.
    """
    if not points:
        return None
    try:
        os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).parent / ".matplotlib"))
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib import pyplot as plt
    except ImportError:
        return None

    project_directory = Path(__file__).parent
    static_directory = static_directory or project_directory / "static"
    output_directory = static_directory / "graphs"
    output_directory.mkdir(parents=True, exist_ok=True)

    x_values = [point["ply"] for point in points]
    y_values = [point["evaluation"] for point in points]
    figure, axis = plt.subplots(figsize=(10, 3.2))
    axis.plot(x_values, y_values, color="#4f46e5", linewidth=2)
    axis.axhline(0, color="#64748b", linewidth=1)
    axis.fill_between(
        x_values, y_values, 0,
        where=[value >= 0 for value in y_values],
        color="#dbeafe", alpha=.8, label="White advantage",
    )
    axis.fill_between(
        x_values, y_values, 0,
        where=[value < 0 for value in y_values],
        color="#fee2e2", alpha=.8, label="Black advantage",
    )
    axis.set(xlabel="Half-move", ylabel="Evaluation (pawns)", title="Evaluation after every move")
    axis.grid(alpha=.2)
    figure.tight_layout()

    filename = f"evaluation-{uuid4().hex}.png"
    figure.savefig(output_directory / filename, format="png", dpi=140)
    plt.close(figure)
    return (Path("graphs") / filename).as_posix()
