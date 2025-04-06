from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Güvenli değil ama test için uygun, sonra domain bazlı sınırları eklersin

DB_FILE = "erenai.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            question TEXT PRIMARY KEY,
            answer TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/ask')
def ask():
    question = request.args.get("q", "").strip()
    if not question:
        return jsonify({"error": "Soru eksik"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT answer FROM knowledge WHERE question = ?", (question,))
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({"answer": row[0]})
    else:
        return jsonify({"answer": None})

@app.route('/save', methods=["POST"])
def save():
    data = request.get_json()
    question = data.get("question", "").strip()
    answer = data.get("answer", "").strip()

    if not question or not answer:
        return jsonify({"error": "Eksik veri"}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO knowledge (question, answer) VALUES (?, ?)", (question, answer))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
