"""
Country Shapes 101 – HW10 "technical prototype"
Run with:  python app.py
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, abort, flash
)
import json, os, random
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "replace-this-before-prod"
app.debug = True  # Ensure debug mode is on

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
        logger.debug(f"Processing POST for question {qid}")
        # What was just answered? (that's qid in the URL)
        qtype = qdata["type"]

        # Initialize answers dict if it doesn't exist
        if "answers" not in session:
            session["answers"] = {}

        if qtype == "mc":
            user_answer = request.form.get("choice")
            correct = user_answer == qdata["answer"]
            logger.debug(f"MC Question {qid}: User answer={user_answer}, Correct={correct}")
            feedback = {
                "correct": correct,
                "user_answer": user_answer,
                "correct_answer": qdata.get("answer", "all matched")
            }
            # Store both the answer and whether it was correct
            session["answers"][str(qid)] = {
                "type": "mc",
                "answer": user_answer,
                "correct": correct
            }
            logger.debug(f"Stored MC answer in session: {session['answers'][str(qid)]}")
        elif qtype == "match":
            user_answer = "matched" if request.form.get("match_done") == "done" else "incomplete"
            correct = (user_answer == "matched")
            
            # Get the number of outlines that need to be matched
            total_outlines = len(qdata["outlines"])
            
            # Count how many matches were made
            matched_count = sum(1 for o in qdata["outlines"] 
                              if f"match_{o['id']}" in request.form)
            
            logger.debug(f"Match Question {qid}: Matched={matched_count}/{total_outlines}, Correct={correct}")
            
            if correct:
                feedback = {
                    "correct": True,
                    "user_answer": f"All {total_outlines} countries matched correctly",
                    "correct_answer": f"All {total_outlines} countries matched correctly"
                }
            else:
                feedback = {
                    "correct": False,
                    "user_answer": f"Only {matched_count} out of {total_outlines} countries were matched",
                    "correct_answer": f"All {total_outlines} countries need to be matched correctly"
                }
            # Store both the answer and whether it was correct
            session["answers"][str(qid)] = {
                "type": "match",
                "answer": user_answer,
                "correct": correct
            }
            logger.debug(f"Stored match answer in session: {session['answers'][str(qid)]}")
        else:
            abort(400, f"Unknown question type: {qtype}")

        # Force session update
        session.modified = True
        logger.debug(f"Current session answers: {session['answers']}")

        # If this was the last question, redirect to results
        if qid == TOTAL_QUIZ:
            logger.debug("Last question completed, redirecting to results")
            return redirect(url_for("result"))

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
    total_questions = len(answers)  # Use actual number of questions answered
    
    logger.debug("=== Calculating Final Score ===")
    logger.debug(f"Total questions answered: {total_questions}")
    logger.debug(f"Answers in session: {answers}")
    
    # First, verify we have answers for all questions
    for qid in range(1, TOTAL_QUIZ + 1):
        if str(qid) not in answers:
            logger.debug(f"Warning: No answer found for question {qid}")
    
    # Calculate score
    for qid_str, ans_data in answers.items():
        qid = int(qid_str)
        logger.debug(f"\nProcessing question {qid}:")
        logger.debug(f"Answer data: {ans_data}")
        
        if isinstance(ans_data, dict):
            if ans_data.get("correct", False):
                score += 1
                logger.debug(f"Question {qid} marked correct (new format)")
            else:
                logger.debug(f"Question {qid} marked incorrect (new format)")
        else:
            # Old format - check against the question
            q = QUIZ[qid]
            if q["type"] == "mc" and ans_data == q["answer"]:
                score += 1
                logger.debug(f"Question {qid} marked correct (old format)")
            elif q["type"] == "match" and ans_data == "matched":
                score += 1
                logger.debug(f"Question {qid} marked correct (old format)")
            else:
                logger.debug(f"Question {qid} marked incorrect (old format)")
    
    logger.debug(f"\nFinal calculation:")
    logger.debug(f"Total questions answered: {total_questions}")
    logger.debug(f"Total correct answers: {score}")
    logger.debug(f"Final score: {score}/{TOTAL_QUIZ}")
    
    # Ensure we're using TOTAL_QUIZ for the total
    return render_template("result.html", score=score, total=TOTAL_QUIZ)

# ────────── Dev runner ──────────
if __name__ == "__main__":
    # bind to 0.0.0.0 if you need phone/tablet access on LAN
    app.run(debug=True, host="127.0.0.1", port=5000)
