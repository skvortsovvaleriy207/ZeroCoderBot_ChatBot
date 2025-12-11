import sqlite3
import os
from flask import Flask, render_template, g

app = Flask(__name__)

# Configuration
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'telethon', 'messages.db'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    db = get_db()
    
    # Total messages
    cur = db.execute('SELECT COUNT(*) FROM messages')
    total_messages = cur.fetchone()[0]
    
    # Analyzed messages
    cur = db.execute('SELECT COUNT(*) FROM messages WHERE is_summarized = 1')
    analyzed_messages = cur.fetchone()[0]
    
    # Last analyzed date
    cur = db.execute('SELECT MAX(date) FROM messages WHERE is_summarized = 1')
    last_analyzed_date = cur.fetchone()[0]
    
    return render_template('index.html', 
                           total_messages=total_messages, 
                           analyzed_messages=analyzed_messages, 
                           last_analyzed_date=last_analyzed_date)

@app.route('/messages')
def messages():
    db = get_db()
    cur = db.execute('SELECT * FROM messages ORDER BY date DESC')
    messages = cur.fetchall()
    return render_template('messages.html', messages=messages)

if __name__ == '__main__':
    app.run(debug=False, port=50013)
