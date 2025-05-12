"""
Country Shapes 101 – HW10 "technical prototype"
Run with:  python app.py
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, abort, flash
)
import json, os, random

app = Flask(__name__)
app.secret_key = "replace-this-before-prod"

import random

@app.template_filter("shuffle")
def shuffle_filter(seq):
    """Return a new shuffled list so Jinja can do {{ list|shuffle }}."""
    seq = list(seq)          # copy so original isn't modified
    random.shuffle(seq)
    return seq
# ────────── Load data ──────────
with open("data/lessons.json", encoding="utf-8") as fp:
    LESSONS = {item["id"]: item for item in json.load(fp)}

with open("data/quiz.json", encoding="utf-8") as fp:
    QUIZ = {item["id"]: item for item in json.load(fp)}

TOTAL_LESSONS = len(LESSONS)
TOTAL_QUIZ    = len(QUIZ)

# ────────── Home / landing ──────────
@app.route("/")
def home():
    """Introduction page – clears session so a new run starts fresh."""
    session.clear()
    return render_template("home.html")

# ────────── Learning flow ──────────
@app.route("/learn/<int:lid>", methods=["GET", "POST"])
def learn(lid: int):
    if lid not in LESSONS:
        return redirect(url_for("home"))

    if request.method == "POST":                 # "Next" button
        nxt = lid + 1 if lid < TOTAL_LESSONS else 1
        return redirect(url_for("learn", lid=nxt))

    # progress: treat lesson 1 as intro → not counted
    total_content = TOTAL_LESSONS - 1
    position = max(lid - 1, 0)
    progress_percent = int((position / total_content) * 100) if total_content else 0

    return render_template(
        "learn.html",
        data=LESSONS[lid],
        lnum=lid,
        total=total_content,
        position=position,
        progress_percent=progress_percent,
        is_intro=(lid == 1),
        last=(lid == TOTAL_LESSONS)
    )

# ────────── Quiz intro ──────────
@app.route("/quiz_intro")
def quiz_intro():
    return render_template("quiz_intro.html")

# ────────── Quiz Q/A ──────────
@app.route("/quiz/<int:qid>", methods=["GET", "POST"])
def quiz(qid: int):
    if qid not in QUIZ:
        return redirect(url_for("home"))

    qdata = QUIZ[qid]              # current question dict
    feedback = None

    # ===== handle POST from previous screen =====
    if request.method == "POST":
        # What was just answered? (that's qid in the URL)
        qtype = qdata["type"]

        if qtype == "mc":
            user_answer = request.form.get("choice")
            correct = user_answer == qdata["answer"]
        elif qtype == "match":
            user_answer = "matched" if request.form.get("match_done") == "done" else "incomplete"
            correct = (user_answer == "matched")
        else:
            abort(400, f"Unknown question type: {qtype}")

        # persist per‑question record
        session.setdefault("answers", {})[str(qid)] = user_answer
        # store feedback for current question
        feedback = {
            "correct": correct,
            "user_answer": user_answer,
            "correct_answer": qdata.get("answer", "all matched")
        }

    # ===== GET: show question screen =====
    progress_percent = int((qid / TOTAL_QUIZ) * 100)

    return render_template(
        "quiz.html",
        data=qdata,
        qnum=qid,
        total=TOTAL_QUIZ,
        feedback=feedback,
        progress_percent=progress_percent
    )

# ────────── Results summary ──────────
@app.route("/result")
def result():
    answers = session.get("answers", {})
    score = 0
    for qid_str, ans in answers.items():
        q = QUIZ[int(qid_str)]
        if q["type"] == "mc" and ans == q["answer"]:
            score += 1
        elif q["type"] == "match" and ans == "matched":
            score += 1
    return render_template("result.html", score=score, total=TOTAL_QUIZ)

# ────────── Dev runner ──────────
if __name__ == "__main__":
    # bind to 0.0.0.0 if you need phone/tablet access on LAN
    app.run(debug=True, host="127.0.0.1", port=5000)
