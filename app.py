"""
Country Shapes 101 – HW10 "technical prototype"
Run with:  python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
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
        
    # Calculate progress percentage for the progress bar
    # Skip the introduction (lid==1) and start from South America overview (lid==2)
    total_content_lessons = len(LESSONS) - 1
    
    # For introduction page, set progress to 0
    if lid == 1:
        progress_percent = 0
        position = 0
    else:
        # For content lessons, calculate based on position after introduction
        position = lid - 1
        progress_percent = int((position / total_content_lessons) * 100)
    
    return render_template(
        "learn.html",
        data=page, 
        last=(lid == len(LESSONS)),
        lnum=lid,
        position=position,
        total=total_content_lessons,
        progress_percent=progress_percent,
        is_intro=(lid == 1)
    )

# ---------------- quiz screens -------------------
@app.route("/quiz_intro")
def quiz_intro():
    return render_template("quiz_intro.html")

@app.route("/quiz/<int:qid>", methods=["GET", "POST"])
def quiz(qid: int):
    feedback = None
    
    if request.method == "POST":
        prev_qid = qid
        choice = request.form["choice"]
        session.setdefault("answers", {})[str(prev_qid)] = choice
        correct = choice == QUIZ[prev_qid]["answer"]
        
        # Store feedback in session
        session["feedback"] = {
            "correct": correct,
            "user_answer": choice,
            "correct_answer": QUIZ[prev_qid]["answer"],
            "prev_qid": prev_qid
        }
        
        nxt = qid + 1
        return redirect(url_for("quiz", qid=nxt) if nxt <= len(QUIZ) else url_for("result"))
    
    # Check if there's feedback from previous question
    feedback = session.pop("feedback", None)
    
    q = QUIZ.get(qid)
    if not q:
        return redirect(url_for("home"))
    
    # Only show feedback if it's for the previous question (qid-1)
    if feedback and int(feedback.get("prev_qid", 0)) != qid - 1:
        feedback = None
    
    # Calculate progress percentage for the progress bar
    progress_percent = int((qid / len(QUIZ)) * 100)
    
    return render_template(
        "quiz.html", 
        data=q, 
        qnum=qid, 
        total=len(QUIZ), 
        feedback=feedback,
        progress_percent=progress_percent
    )

# ---------------- results ------------------------
@app.route("/result")
def result():
    answers = session.get("answers", {})
    score = sum(1 for qid, ans in answers.items() if QUIZ[int(qid)]["answer"] == ans)
    return render_template("result.html", score=score, total=len(QUIZ))

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
