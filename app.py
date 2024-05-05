from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from difflib import get_close_matches
import json
import secrets

app = Flask(__name__)
secret_key = secrets.token_hex(16)  # Generate a random 16-byte secret key
app.secret_key = secret_key

# Predefined users with roles
users = {
    'student@gmail.com': {'password': '123456789', 'role': 'student'},
    'teacher@gmail.com': {'password': 'Hassanebad9', 'role': 'teacher'}
}

# Load knowledge base
def load_knowledge_base(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_knowledge_base(knowledge_base, file_path):
    with open(file_path, 'w') as file:
        json.dump(knowledge_base, file, indent=2)

knowledge_base = load_knowledge_base("knowledge_base.json")

# Custom decorator to restrict access to teaching functionality
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session or users.get(session.get('email', ''))['role'] != 'teacher':
            return jsonify({'error': 'Unauthorized access! Only teachers can teach.'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Function to find best match for user question
def find_best_match(user_question, questions):
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.9)
    return matches[0] if matches else None

# Function to get answer for question
def get_answer_for_question(question, knowledge_base):
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]
    return "Sorry, I do not know the answer. You can ask a teacher to teach me."

@app.route('/')
def index():
    if 'email' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email]['password'] == password:
            session['email'] = email
            return redirect(url_for('index'))  # Redirect to the index page upon successful login
        else:
            return render_template('login.html', message='Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('user_input', '')
    if user_input.lower() == 'quit':
        return jsonify({'response': 'Goodbye!'})
    
    best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])
    if best_match:
        answer = get_answer_for_question(best_match, knowledge_base)
        return jsonify({'response': answer})
    else:
        return jsonify({'response': "Sorry, I do not know the answer. You can ask a teacher to teach me."})

@app.route('/teach', methods=['POST'])
@teacher_required
def teach():
    data = request.json
    question = data.get('question')
    answer = data.get('answer')
    knowledge_base["questions"].append({"question": question, "answer": answer})
    save_knowledge_base(knowledge_base, "knowledge_base.json")
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)