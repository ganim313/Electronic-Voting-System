from flask import Flask, request, jsonify
from Cryptodome.Math.Numbers import Integer
from Cryptodome.Util import number
import sqlite3
import json
from flask_cors import CORS
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

DATABASE = 'trusted_authority.db'
g = 2  # Generator
p = 2666663  # Prime (small for testing)
q = (p - 1) // 2  # Order of g

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS shares 
                 (id INTEGER PRIMARY KEY, tally_server_id INTEGER, share TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS election_params 
                (id INTEGER PRIMARY KEY, public_key TEXT, secret_key TEXT)''')
    conn.commit()
    conn.close()

def generate_shamir_shares(secret, threshold=2, num_shares=3):
    coefficients = [Integer(secret)] + [
        Integer.random_range(min_inclusive=1, max_exclusive=q)  # ✅ Fixed parameter name
        for _ in range(threshold-1)
    ]
    shares = []
    for i in range(1, num_shares + 1):
        # Initialize share as Cryptodome Integer
        share = Integer(0)
        for j, coeff in enumerate(coefficients):
            share += coeff * (i ** j)  # ✅ Use Cryptodome Integer arithmetic
        share = share % q  # Modulo with q (which is an int)
        shares.append((i, share))
    return shares

@app.route('/setup_election', methods=['POST'])
def setup_election():
    try:
        secret_key = Integer.random_range(min_inclusive=1, max_exclusive=q)
        public_key = pow(g, int(secret_key), p)

        public_key_data = {
            'g' : f"{g:x}",
            'h' : f"{public_key:x}",
            'p' : f"{p:x}",
            'q' : f"{q:x}",
            
        }

        shares = generate_shamir_shares(secret_key)
        shares_converted = [(s[0], int(s[1])) for s in shares]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO election_params VALUES (1, ?, ?)", 
            (json.dumps(public_key_data, ensure_ascii=False, str(secret_key))
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "public_key": {"g": g, "h": public_key, "p": p, "q": q},
            "shares": [{"tally_server_id": s[0], "share": s[1]} for s in shares_converted]
        })
    except Exception as e:
        logging.error(f"Error in /setup_election: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/public_key', methods=['GET'])
def get_public_key():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT public_key FROM election_params WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Election not initialized"}), 404
    return jsonify(json.loads(row[0]))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5002, ssl_context=('server.crt', 'server.key'), debug=True)