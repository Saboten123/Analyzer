# ♟️ Chess Analyzer

A Flask-based web application that analyzes chess games from PGN files using the Stockfish chess engine. The application evaluates every move, classifies mistakes, visualizes evaluation changes, and generates a detailed analysis report.

---

## Features

- Upload and analyze PGN chess games
- Powered by the Stockfish chess engine
- Interactive chessboard for move-by-move navigation
- Move classifications:
  - Brilliant
  - Great
  - Best
  - Excellent
  - Good
  - Inaccuracy
  - Mistake
  - Blunder
  - Miss
  - Forced
  - Book
- Engine evaluation graph
- Mini evaluation graph while browsing moves
- Analysis table with move-by-move details
- Dark mode support
- Downloadable PDF analysis report
- Responsive user interface

---

## Tech Stack

### Backend
- Python
- Flask
- python-chess
- Stockfish

### Frontend
- HTML
- CSS
- JavaScript
- Chessboard.js
- Chart.js

### Report Generation
- ReportLab

---

## Project Structure

```
Chess-Analyzer/
│
├── app.py
├── analyzer.py
├── engine.py
├── report.py
├── requirements.txt
├── Dockerfile
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── README.md
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/<your-username>/<repository-name>.git

cd <repository-name>
```

### Create a virtual environment

```bash
python -m venv venv
```

### Activate the environment

Windows

```bash
venv\Scripts\activate
```

Linux/macOS

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Stockfish Setup

Download the Stockfish executable from:

https://stockfishchess.org/download/

Place the executable inside:

```
Stockfish/
    stockfish.exe
```

Or specify its location using an environment variable:

```bash
STOCKFISH_PATH=/path/to/stockfish
```

---

## Running the Application

```bash
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

## Docker

Build the image:

```bash
docker build -t chess-analyzer .
```

Run the container:

```bash
docker run -p 10000:10000 chess-analyzer
```

---

## Deployment

The project can be deployed using:

- Render (Docker)
- AWS EC2
- Railway
- Any Docker-compatible cloud platform

---

## Screenshots


### Home Page

```
images/home.png
```

### Analysis Page

```
images/analysis1.png
images/analysis2.png
```

### Evaluation Graph

```
images/graph.png
```

---

<!--## Author

**Manashish Dhar**-->


## Live Demo

https://analyzer-1-4bbw.onrender.com
