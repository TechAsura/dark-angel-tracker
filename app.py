from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__, static_folder='static')
CORS(app)

DB_PATH = os.environ.get('DB_PATH', '/data/tracker.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                sleep REAL,
                weight REAL,
                bf REAL,
                mm REAL,
                water REAL,
                calories INTEGER,
                protein INTEGER,
                habits TEXT,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/entries', methods=['GET'])
def get_entries():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM entries ORDER BY date DESC').fetchall()
        entries = []
        for row in rows:
            e = dict(row)
            e['habits'] = json.loads(e['habits']) if e['habits'] else {}
            entries.append(e)
    return jsonify(entries)

@app.route('/api/entries', methods=['POST'])
def save_entry():
    data = request.json
    if not data or not data.get('date'):
        return jsonify({'error': 'Date required'}), 400

    with get_db() as conn:
        conn.execute('''
            INSERT INTO entries (date, sleep, weight, bf, mm, water, calories, protein, habits, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                sleep=excluded.sleep, weight=excluded.weight, bf=excluded.bf,
                mm=excluded.mm, water=excluded.water, calories=excluded.calories,
                protein=excluded.protein, habits=excluded.habits, note=excluded.note
        ''', (
            data.get('date'),
            data.get('sleep'),
            data.get('weight'),
            data.get('bf'),
            data.get('mm'),
            data.get('water'),
            data.get('calories'),
            data.get('protein'),
            json.dumps(data.get('habits', {})),
            data.get('note', '')
        ))
        conn.commit()
        row = conn.execute('SELECT * FROM entries WHERE date = ?', (data['date'],)).fetchone()
        e = dict(row)
        e['habits'] = json.loads(e['habits']) if e['habits'] else {}
    return jsonify(e), 201

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    with get_db() as conn:
        conn.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
        conn.commit()
    return jsonify({'deleted': entry_id})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM entries ORDER BY date ASC').fetchall()
        entries = [dict(r) for r in rows]

    total = len(entries)
    avg_sleep = None
    avg_habits = None

    sleeps = [e['sleep'] for e in entries if e['sleep']]
    if sleeps:
        avg_sleep = round(sum(sleeps) / len(sleeps), 1)

    habit_counts = []
    for e in entries:
        h = json.loads(e['habits']) if e['habits'] else {}
        habit_counts.append(sum(1 for v in h.values() if v))
    if habit_counts:
        avg_habits = round(sum(habit_counts) / len(habit_counts), 1)

    return jsonify({
        'total_logs': total,
        'avg_sleep': avg_sleep,
        'avg_habits': avg_habits,
        'latest': dict(entries[-1]) if entries else None,
        'previous': dict(entries[-2]) if len(entries) >= 2 else None,
    })

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
