import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)
DATABASE = 'voting_system.db'

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS voters (
                    id INTEGER PRIMARY KEY,
                    unique_id TEXT UNIQUE,
                    name TEXT,
                    is_eligible BOOLEAN
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY,
                    unique_id TEXT UNIQUE
                )''')
    conn.commit()
    conn.close()
    logger.info("Database initialized.")

# Verify voter eligibility
@app.route('/verify_voter', methods=['GET'])
def verify_voter():
    unique_id = request.args.get('unique_id')
    logger.debug(f"Verifying voter with ID: {unique_id}")
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM voters WHERE unique_id = ?", (unique_id,))
    voter = c.fetchone()
    conn.close()
    if voter and voter[3]:  # Check if voter exists and is eligible
        logger.debug(f"Voter found: {voter[2]}")
        return jsonify({"status": "success", "name": voter[2]})
    else:
        logger.debug("Voter not eligible or not found.")
        return jsonify({"status": "failure", "message": "Voter not eligible"})

@app.route('/mark_voted', methods=['POST'])
def mark_voted():
    data = request.json
    unique_id = data['unique_id']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO votes (unique_id) VALUES (?)", (unique_id,))
        conn.commit()
        return jsonify({"status": "success"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Already voted"})
    finally:
        conn.close()
if __name__ == '__main__':
    init_db()
    #app.run(host='0.0.0.0', port=5000)  # Remove SSL for local testing
    app.run(host='192.168.113.101', port=5000, ssl_context=('C:/Users/Md Ganim/Desktop/Program/finalSecurity/registry.crt', 'C:/Users/Md Ganim/Desktop/Program/finalSecurity/registry.key'),debug=True)
