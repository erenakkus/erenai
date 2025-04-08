from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "erenai.db"

# Veritabanını oluştur
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT UNIQUE,
            answer TEXT
        )
    """)
    conn.commit()
    conn.close()

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM qa WHERE question = ?", (question,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({"answer": result[0]})
    else:
        return jsonify({"answer": None})

@app.route("/save", methods=["POST"])
def save():
    data = request.get_json()
    question = data.get("question")
    answer = data.get("answer")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO qa (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
