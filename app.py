from flask import Flask, render_template, request, session, redirect, flash
import sqlite3
import bcrypt
app = Flask(__name__)
app.secret_key = 'secret'
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-activity', methods=['GET', 'POST'])
def add_activity():
    if request.method == 'POST':
        category = request.form['category']
        name = request.form['name']
        description = request.form['description']
        
        # Save the activity to the user's database
        username = session['UNAME']
        c.execute(f"INSERT INTO {username} VALUES (?, ?, ?)", (category, name, description))
        conn.commit()
        
        return redirect('/')
    username = session['UNAME']
    lis = c.execute(f'SELECT * FROM {username}').fetchall()
    
    return render_template('activies.html', lis = lis)

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
        c.execute(f"CREATE TABLE IF NOT EXISTS {username} (category TEXT, name TEXT, description TEXT)")
        c.execute(f"INSERT INTO users VALUES (?, ?, ?)", (username, hashed_password, email))
        
        return redirect('/')
    
    return render_template('signup.html')

@app.route('/recommend_activity')
def recommend_activity():
    # Query OpenAI GPT-3.5 Turbo to get activity recommendations based on descriptions
    # Implement the logic to query the model here
    
    return render_template('suggestions.html', r = r)  # Replace with the recommended activity

if __name__ == '__main__':
    app.run(debug=True)