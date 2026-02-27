
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from textblob import TextBlob
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------- DATABASE MODELS ---------------- #

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500))
    answer = db.Column(db.String(1000))

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(1000))
    response = db.Column(db.String(1000))
    sentiment = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'],
                    password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'],
                                     password=request.form['password']).first()
        if user:
            login_user(user)
            return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@app.route('/get_response', methods=['POST'])
@login_required
def get_response():
    user_message = request.json['message']
    sentiment = analyze_sentiment(user_message)

    faqs = FAQ.query.all()

    if not faqs:
        response = "No information available. Please contact admin."
    else:
        questions = [faq.question for faq in faqs]
        answers = [faq.answer for faq in faqs]

        # Add user message to question list
        questions.append(user_message)

        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform(questions)

        similarity = cosine_similarity(tfidf[-1], tfidf[:-1])
        best_match_index = similarity.argmax()

        if similarity[0][best_match_index] < 0.2:
            response = "Sorry, I couldn't understand. Please ask about admissions, courses, fees or placements."
        else:
            response = answers[best_match_index]

    chat_entry = ChatHistory(
        user_id=current_user.id,
        message=user_message,
        response=response,
        sentiment=sentiment
    )

    db.session.add(chat_entry)
    db.session.commit()

    return jsonify({
        "response": response,
        "sentiment": sentiment
    })

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        faq = FAQ(question=request.form['question'],
                  answer=request.form['answer'])
        db.session.add(faq)
        db.session.commit()
    faqs = FAQ.query.all()
    return render_template('admin.html', faqs=faqs)

# ---------------- SENTIMENT ---------------- #

def analyze_sentiment(text):
    blob = TextBlob(text)
    if blob.sentiment.polarity > 0:
        return "Positive 😊"
    elif blob.sentiment.polarity < 0:
        return "Negative 😡"
    else:
        return "Neutral 😐"

# ---------------- RUN ---------------- #

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)