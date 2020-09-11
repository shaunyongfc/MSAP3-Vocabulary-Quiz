from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os, requests, random

# initialization
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foo.db'
app.secret_key = "abcdefg"
db = SQLAlchemy(app)
translate_key = '211e5dad97af4405a855ca6f77032902' #os.environ['TRANSLATE_KEY']
language = 'en' # default value for translation

# db class to store words requested for translations
class Vocab(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    meaning = db.Column(db.String(100), nullable=False)

# index page
@app.route('/', methods=['GET', 'POST'])
def index():
    global language
    global new_quiz
    new_quiz = True # boolean to determine whether new quiz should be generated when called
    if request.method == 'POST':
        if 'Translate' in request.form:
            word = request.form['word']
            language = request.form['language']
            meaning = translate_text(word, translate_key)
            flash(f'The word "{word}" means {meaning}!') # return the meaning as a flash message
            new_vocab = Vocab(word=word, meaning=meaning) # add to the db
            try:
                db.session.add(new_vocab)
                db.session.commit()
                return redirect('/')
            except:
                return 'Error. Please try again.'
        elif 'Quiz' in request.form:
            return redirect('/quiz/')
        else:
            return redirect('/')
    else:
        vocabs = Vocab.query.order_by(Vocab.id).all()
        return render_template('index.html', vocabs=vocabs, language=language)

# called to delete a vocab entry in index
@app.route('/delete/<int:id>')
def delete(id):
    vocab = Vocab.query.get_or_404(id)
    try:
        flash(f'The word "{vocab.word}" is deleted from the list!')
        db.session.delete(vocab)
        db.session.commit()
        return redirect('/')
    except:
        return 'Error. Please try again.'

# called to generate new quiz page
@app.route('/quiz/retry/', methods=['GET', 'POST'])
def quiz_retry():
    global new_quiz
    new_quiz = True
    return redirect('/quiz/')

# quiz page
@app.route('/quiz/', methods=['GET', 'POST'])
def quiz():
    global new_quiz
    global vocabs
    if new_quiz == True:
        new_quiz = False
        vocabs = Vocab.query.order_by(Vocab.id).all()
        random.shuffle(vocabs) # shuffle the order of the words
        meaning_shuffled = []
        for vocab in vocabs:
            meaning_shuffled.append(vocab.meaning)
        random.shuffle(meaning_shuffled) # shuffle the meanings of the words
        return render_template('quiz.html', vocabs=vocabs, meaning_shuffled=meaning_shuffled, answers=[], feedbacks = [])
    elif request.method == 'POST': # check answers and calculate score
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
                feedbacks.append('Correct!')
            else:
                feedbacks.append(f'Incorrect! The answer is {vocab.meaning}')
        score_perc = (scored / max_score) * 100
        feedbacks.append('')
        flash(f'You answered {scored} correctly out of {max_score}! Your score is {score_perc:.1f}%!')
        return render_template('quiz.html', vocabs=vocabs, answers=answers, feedbacks=feedbacks)
    else:
        return 'Error. Please try again.'

# function to translate words
def translate_text(word, key):
    uri = 'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=' + language
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-type': 'application/json'
    }
    json = [{ 'text': word}]
    try:
        response = requests.post(uri, headers=headers, json=json)
        response.raise_for_status()
        meaning = response.json()[0]['translations'][0]['text']
        return meaning
    except:
        return 'Error. Please try again.'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()
