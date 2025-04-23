"""
Country Shapes 101 – HW10 "technical prototype"
Run with:  python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, session
import json

app = Flask(__name__)
app.secret_key = "replace-this-before-prod"

# ---------- load lesson & quiz data ------------------------------------------
with open("data/lessons.json", encoding="utf-8") as fp:
    LESSONS = {item["id"]: item for item in json.load(fp)}

with open("data/quiz.json", encoding="utf-8") as fp:
    QUIZ = {item["id"]: item for item in json.load(fp)}

# ---------- routes -----------------------------------------------------------
@app.route("/")
def home():
    session.clear()
    return render_template("home.html")

# ---------------- learning screens ----------------
@app.route("/learn/<int:lid>", methods=["GET", "POST"])
def learn(lid: int):
    if request.method == "POST":          # "Next" clicked
        nxt = lid + 1 if lid < len(LESSONS) else 1   # wraps around for demo
        return redirect(url_for("learn", lid=nxt))
    page = LESSONS.get(lid)
    if not page:
        return redirect(url_for("home"))
    return render_template("learn.html", data=page, last=(lid == len(LESSONS)))

# ---------------- quiz screens -------------------
@app.route("/quiz/<int:qid>", methods=["GET", "POST"])
def quiz(qid: int):
    if request.method == "POST":
        choice = request.form["choice"]
        session.setdefault("answers", {})[qid] = choice
        correct = choice == QUIZ[qid]["answer"]
        nxt = qid + 1
        return redirect(url_for("quiz", qid=nxt) if nxt <= len(QUIZ) else url_for("result"))
    q = QUIZ.get(qid)
    if not q:
        return redirect(url_for("home"))
    return render_template("quiz.html", data=q, qnum=qid, total=len(QUIZ))

# ---------------- results ------------------------
@app.route("/result")
def result():
    answers = session.get("answers", {})
    score = sum(1 for qid, ans in answers.items() if QUIZ[int(qid)]["answer"] == ans)
    return render_template("result.html", score=score, total=len(QUIZ))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
