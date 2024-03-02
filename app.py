from flask import Flask, render_template, request, session, redirect, flash
import sqlite3
import bcrypt
import openai

app = Flask(__name__)
app.secret_key = 'secret'
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()
openai.api_key = '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'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/activities', methods=['GET', 'POST'])
def add_activity():
    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        description = request.form['description']
        
        # Save the activity to the user's database
        username = session['UNAME']
        c.execute(f"INSERT INTO {username} (category, name, description) VALUES (?, ?, ?)", (category, name, description))
        conn.commit()
        
        return redirect('/activities')
    
    try:
        username = session['UNAME']
    except:
        flash('You need to be logged in to access this page')
        return redirect('/login')
    lis = c.execute(f'SELECT * FROM {username}').fetchall()
    
    return render_template('activities.html', lis = lis)

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
        c.execute(f"INSERT INTO users VALUES (?, ?, ?)", (username, hashed_password, email))
        conn.commit()

        return redirect('/')
    
    return render_template('signup.html')

@app.route('/delete-activity/<int:id>')
def delete_activity(id):
    username = session['UNAME']
    c.execute(f'DELETE FROM {username} WHERE id = {id}')
    conn.commit()
    return redirect('/activities')

@app.route('/recommend-activity')
def recommend_activity():
    username = session['UNAME']
    lis = [i[0] for i in c.execute(f'SELECT description FROM {username}').fetchall()]
    if not lis:
        r = 'As of now, you do not have any activities in your list. I suggest you start with something you find interesting to begin your extracurricular journey.'
    else:
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{'role' : 'system', 'content' : "You are a college counselor reviewing extracurricullars and strengthening users' profile. Reply in conscise words."}, {'role' : 'user', 'content' : '\n'.join(lis)}],
            max_tokens=150
        )
    return render_template('suggestions.html', r = r['choices'][0]['message']['content'])

if __name__ == '__main__':
    app.run(debug=True)