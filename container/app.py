from base import TradingAlgorithm
from flask import Flask, request, jsonify, g
import sqlite3, json
import signal, sys
import numpy as np

app = Flask(__name__)
trading_algorithm = TradingAlgorithm()
DATABASE = "results.db"

def _setup_signals():
    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

def _handle_sigterm(signum, frame):
    sys.exit(0)


def clear_db():
    # if "db" in g:
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM submissions")
    db.commit()
    close_db()

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        # Initialize the database schema if it hasn't been initialized yet
        cursor = g.db.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS submissions (roundNumber INTEGER PRIMARY KEY, submission TEXT)"
        )
        g.db.commit()
    return g.db


def close_db():
    db = g.pop("db", None)

    if db is not None:
        db.close()


@app.get("/")
def home():
    return "Working"


@app.post("/healthz")
def health_check():
    print("Health check")
    return "OK"


@app.post("/task/<roundNumber>")
def start_task(roundNumber):
    print("Task started for round: " + roundNumber)
    nav_data = trading_algorithm.run()
    nav_array = np.array(nav_data)
    returns = (nav_array[-1] / nav_array[0])
    nav_data.append(returns)

    nav_data_json = json.dumps(nav_data) 
    print("nav_data: ", nav_data_json)

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO submissions (roundNumber, submission) VALUES (?, ?)",
        (roundNumber, nav_data_json),
    )
    db.commit()
    close_db()
    return jsonify({"roundNumber": roundNumber, "status": "Task started"})


@app.get("/submission/<roundNumber>")
def fetch_submission(roundNumber):
    print("Fetching submission for round: " + roundNumber)
    db = get_db()
    cursor = db.cursor()
    query = cursor.execute(
        "SELECT * FROM submissions WHERE roundNumber = ?", (roundNumber,)
    )
    result = query.fetchone()
    close_db()

    if result:
        nav_data = json.loads(result["submission"])
        return jsonify({"message": nav_data})
    else:
        return "Submission not found", 404

@app.post("/audit")
def audit_submission():
    print("Auditing submission")
    data = request.get_json()
    submission_data = data["submission"]["message"]
    returns = submission_data[-1]
    calc_returns = submission_data[-2] / submission_data[0]
    audit_result = (calc_returns - returns < 0.01)
    # audit result must be a boolean
    return jsonify(audit_result)

if __name__ == "__main__":
    _setup_signals()
    with app.app_context():
        clear_db()
    app.run(host="0.0.0.0", port=8080, threaded=False)
