from flask import Flask, render_template, request, session, redirect, flash
import sqlite3
import bcrypt
import openai
import os
from dotenv import load_dotenv

# Must include an API Key in a .env file in the same directory as app.py

app = Flask(__name__)
app.secret_key = 'secret'
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
openai.api_key = os.getenv('API_KEY')

@app.route('/')
def index():
    session['location'] = 'Generic'
    return render_template('index.html')

@app.route('/activities', methods=['GET', 'POST'])
def add_activity():
    try:
        username = session['UNAME']
    except:
        flash('You need to be logged in to access this page')
        return redirect('/login')
    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        description = request.form['description']
        
        username = session['UNAME']
        c.execute(f"INSERT INTO {username} (category, name, description) VALUES (?, ?, ?)", (category, name, description))
        conn.commit()
        
        return redirect('/activities')
    
    lis = c.execute(f'SELECT * FROM {username}').fetchall()

    cats = sorted(list(set([i[0] for i in lis])))
    
    return render_template('activities.html', lis = lis, cats = cats)

@app.route('/logout')
def logout():
    session.pop('UNAME', None)
    session.pop('suggestions', None)
    session.pop('schools', None)
    session.pop('location', None)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        c.execute(f"SELECT * FROM users WHERE (name = '{username}' OR email = '{username}')")
        user = c.fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1]):
            session['UNAME'] = user[0]
            return redirect('/')
        else:
            flash('Invalid username or password')
            return redirect('/login')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        gpa = request.form['gpa']

        if password != request.form['confirm_password']:
            flash('Passwords do not match')
            return redirect('/signup')
        
        existing_user = c.execute(f"SELECT * FROM users WHERE name = '{username}' OR email = '{email}'").fetchone()
        if existing_user:
            flash('Username already exists')
            return redirect('/signup')
        
        session['UNAME'] = username
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        c.execute(f"CREATE TABLE IF NOT EXISTS {username} (category TEXT, name TEXT, description TEXT, id INTEGER PRIMARY KEY AUTOINCREMENT)")
        c.execute(f"INSERT INTO users VALUES (?, ?, ?, ?)", (username, hashed_password, email, gpa))
        conn.commit()

        return redirect('/')
    
    return render_template('signup.html')

@app.route('/delete-activity/<int:id>')
def delete_activity(id):
    try:
        username = session['UNAME']
    except:
        flash('You need to be logged in to access this page')
        return redirect('/login')
    c.execute(f'DELETE FROM {username} WHERE id = {id}')
    conn.commit()
    return redirect('/activities')

@app.route('/recommend-activity/recommend')
def recommend_activityr():
    try:
        username = session['UNAME']
    except:
        flash('You need to be logged in to access this page')
        return redirect('/login')
    lis = [i[0] for i in c.execute(f'SELECT description FROM {username}').fetchall()]
    if not lis:
        r = 'As of now, you do not have any activities in your list. I suggest you start with something you find interesting to begin your extracurricular journey.'
    else:
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{'role' : 'system', 'content' : "You are a college counselor reviewing extracurriculars and suggesting others based on what would strengthen this user's profile. Reply in concise words. Expand on your points by including some pointers on what students can actually do (5 points). Expand as much as possible."}, {'role' : 'user', 'content' : '\n'.join(lis)}],
            temperature = 0.5
        )['choices'][0]['message']['content']
    session['suggestions'] = r
    return redirect('/recommend-activity')

@app.route('/recommend-activity')
def recommend_activity():
    try:
        username = session['UNAME']
    except:
        flash('You need to be logged in to access this page')
        return redirect('/login')
    r = session.get('suggestions', 'Generate suggestions')
    return render_template('suggestions.html', r = r)

@app.route('/recommend-schools/recommend', methods=['POST', 'GET'])
def recommend_schoolsr():
    try:
        username = session['UNAME']
    except:
        flash('You need to be logged in to access this page')
        return redirect('/login')
    if request.method == 'POST':
        gpa = request.form['gpa']
        location = request.form['location']
        session['location'] = location
        c.execute(f"UPDATE users SET gpa = ? WHERE name = ?", (gpa, username))
        conn.commit()
        
        return redirect('/recommend-schools')
    lis = [i[0] for i in c.execute(f'SELECT description FROM {username}').fetchall()]
    if not lis:
        r = 'As of now, you do not have any activities in your list. I suggest you start with something you find interesting to begin your extracurricular journey.'
    else:
        gpa = c.execute(f"SELECT gpa FROM users WHERE name = '{username}'").fetchone()[0]
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{'role' : 'system', 'content' : "Based on GPA, Extracurriculars, and area determine safeties, match, and reach schools. Also recommend majors and career options with salary."}, {'role' : 'user', 'content' : '\n'.join(lis) + '\nGPA: ' + gpa + '\nArea: ' + session['location'] + '\n'}],
            temperature = 0.5
        )['choices'][0]['message']['content']
    session['schools'] = r
    return redirect('/recommend-schools')

@app.route('/recommend-schools', methods=['POST', 'GET'])
def recommend_schools():
    try:
        username = session['UNAME']
    except:
        return redirect('/login')
    if request.method == 'POST':
        gpa = request.form['gpa']
        location = request.form['location']
        session['location'] = location
        c.execute(f"UPDATE users SET gpa = ? WHERE name = ?", (gpa, username))
        conn.commit()
        
        return redirect('/recommend-schools/recommend')
    r = session.get('schools', 'Generate recommendations')
    gpa = c.execute(f"SELECT gpa FROM users WHERE name = '{username}'").fetchone()[0]
    vals = (gpa, session.get('location', ''))
    return render_template('sug2.html', r = r, vals=vals)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)