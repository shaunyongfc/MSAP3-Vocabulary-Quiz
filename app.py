from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import os, requests, random

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foo.db'
db = SQLAlchemy(app)
language = "en"

translate_key = os.environ["TRANSLATE_KEY"]
app.secret_key = os.environ["SECRET_KEY"]

class Vocab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(100), nullable=False)

@app.route("/", methods=["GET", "POST"])
def index():
    global language
    global new_quiz
    new_quiz = True
    if request.method == "POST":
        if "Translate" in request.form:
            word = request.form['word']
            language = request.form["language"]
            meaning = translate_text(word, translate_key)
            flash(f'The word "{word}" means {meaning}!')
            new_vocab = Vocab(word=word, meaning=meaning)
            try:
                db.session.add(new_vocab)
                db.session.commit()
                return redirect('/')
            except:
                return 'Error. Please try again.'
        elif "Quiz" in request.form:
            return redirect('/quiz/')
        else:
            return 'Error. Please try again.'
    else:
        vocabs = Vocab.query.order_by(Vocab.id).all()
        return render_template("index.html", vocabs=vocabs, language=language)

@app.route("/delete/<int:id>")
def delete(id):
    vocab = Vocab.query.get_or_404(id)
    try:
        flash(f'The word "{vocab.word}" is deleted from the list!')
        db.session.delete(vocab)
        db.session.commit()
        return redirect('/')
    except:
        return 'Error. Please try again.'

@app.route("/quiz/retry/", methods=["GET", "POST"])
def quiz_retry():
    global new_quiz
    new_quiz = True
    return redirect('/quiz/')

@app.route("/quiz/", methods=["GET", "POST"])
def quiz():
    global new_quiz
    global vocabs
    if new_quiz == True:
        new_quiz = False
        vocabs = Vocab.query.order_by(Vocab.id).all()
        random.shuffle(vocabs)
        meaning_shuffled = []
        for vocab in vocabs:
            meaning_shuffled.append(vocab.meaning)
        random.shuffle(meaning_shuffled)
        return render_template("quiz.html", vocabs=vocabs, meaning_shuffled=meaning_shuffled, answers=[], feedbacks = [])
    elif request.method == "POST":
        answers = []
        feedbacks = []
        scored = 0
        max_score = 0
        for vocab in vocabs:
            max_score += 1
            answer = request.form[vocab.word]
            answers.append(answer)
            if answer == vocab.meaning:
                scored += 1
                feedbacks.append("Correct!")
            else:
                feedbacks.append(f"Incorrect! The answer is {vocab.meaning}")
        score_perc = (scored / max_score) * 100
        feedbacks.append("")
        flash(f'You answered {scored} correctly out of {max_score}! Your score is {score_perc:.1f}%!')
        return render_template("quiz.html", vocabs=vocabs, answers=answers, feedbacks=feedbacks)
    else:
        return 'Error. Please try again.'

def translate_text(word, key):
    uri = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=" + language
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-type': 'application/json'
    }
    json = [{ "text": word}]
    try:
        print("Translating", word)
        response = requests.post(uri, headers=headers, json=json)
        response.raise_for_status()
        meaning = response.json()[0]["translations"][0]["text"]
        return meaning
    except:
        return "Error calling the Translator Text API"

if __name__ == "__main__":
    app.run(debug=True)
