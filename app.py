from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os, requests

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foo.db'
db = SQLAlchemy(app)

translate_key = os.environ["TRANSLATE_KEY"]

class Vocab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(100), nullable=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        word = request.form['word']
        language = request.form.get("language", "en")
        meaning = translate_text(word, "en", translate_key)
        new_word = Vocab(word=word, meaning=meaning)
        try:
            db.session.add(new_word)
            db.session.commit()
            return redirect('/')
        except:
            return 'Error. Please try again.'
    else:
        language = "en"
        words = Vocab.query.order_by(Vocab.id).all()
        return render_template("index.html", words=words, language=language)

@app.route("/delete/<int:id>")
def delete(id):
    word = Vocab.query.get_or_404(id)
    try:
        db.session.delete(word)
        db.session.commit()
        return redirect('/')
    except:
        return 'Error. Please try again.'

def translate_text(word, language, key):
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
