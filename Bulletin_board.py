from flask import Flask, request, jsonify
from flask_cors import CORS
from Cryptodome.Math.Numbers import Integer
import sqlite3
import requests
import hashlib
import logging
import string

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/submit_ballot": {"origins": "https://192.168.113.28:8080"}})
logging.basicConfig(level=logging.DEBUG)

# Database and cryptographic parameters
DATABASE = 'bulletin_board.db'
PUBLIC_KEY = None

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ballots 
                 (id INTEGER PRIMARY KEY, c1 TEXT, c2 TEXT, proof TEXT)''')
    conn.commit()
    conn.close()

def fetch_public_key():
    global PUBLIC_KEY
    try:
        import requests
        response = requests.get('https://13.233.201.244:5002/public_key', verify='/home/md-ganim/Desktop/ca.crt')
        if response.ok:
            pk_data = response.json()
            hex_fields = ['g' ,'h', 'p','q']
            for field in hex_fields:
                if not all(c in string.hexdigits for c in pk_data[field]):
                      raise ValueError(f"Invalid hex value in {field}")
            PUBLIC_KEY = {
                'g': Integer(int(pk_data['g'],16)),
                'h': Integer(int(pk_data['h'],16)),
                'p': Integer(int(pk_data['p'],16)),
                'q': Integer(int(pk_data['q'],16))
                #'q': Integer(pk_data.get('q', (pk_data['p'] - 1)))
            }
            app.logger.info("Public key fetched successfully")
        else:
            app.logger.error("Failed to fetch public key")
    except Exception as e:
        app.logger.error(f"Public key fetch error: {str(e)}")
        PUBLIC_KEY = None

def verify_proof(c1, c2, proof, public_key):
    try:
        # Parse hex strings as UNSIGNED integers
        a1 = Integer(int(proof['a1'], 16))  # Force 256-bit
        a2 = Integer(int(proof['a2'], 16))
        challenge = Integer(int(proof['challenge'], 16))
        response = Integer(int(proof['response'], 16))
        c1_val = int(c1, 16) if isinstance(c1, str) else int(c1)
        c2_val = int(c2, 16) if isinstance(c2, str) else int(c2)

        # Convert Integer objects to Python integers before formatting
        a1_int = int(a1)
        a2_int = int(a2)
        c1_int = int(c1_val)
        c2_int = int(c2_val)
        def pad_hex(value):
            positive_value = value if value >=0 else value + public_key['q']
            return format(positive_value,'064x')

        # Pad to 64 lowercase hex (client-server consistency)
        a1_hex = format(a1_int, '064x')
        a2_hex = format(a2_int, '064x')
        c1_hex = format(c1_int, '064x')
        c2_hex = format(c2_int, '064x')

        # Recompute challenge
        challenge_input = (a1_hex + a2_hex + c1_hex + c2_hex).encode()
        challenge_recomputed = Integer(int(hashlib.sha256(challenge_input).hexdigest(), 16)) % public_key['q']

        if challenge != challenge_recomputed:
            app.logger.error(f"Challenge mismatch: {challenge} vs {challenge_recomputed}")
            return False

        # Verify equations (Section 4.4.3)
        g = public_key['g']
        h_pk = public_key['h']
        p = public_key['p']

        term1 = (c2_val * pow(g, -1, p)) % p  # Case 1: vote = 1
        term2 = (c2_val * g) % p              # Case 2: vote = -1

        valid1 = (
            (pow(g, response, p) * pow(c1_val, challenge, p) % p == a1) and
            (pow(h_pk, response, p) * pow(term1, challenge, p) % p == a2)
        )

        valid2 = (
            (pow(g, response, p) * pow(c1_val, challenge, p) % p == a1) and
            (pow(h_pk, response, p) * pow(term2, challenge, p) % p == a2)
        )

        return valid1 or valid2  # Accept if either is valid

    except Exception as e:
        app.logger.error(f"Proof validation failed: {str(e)}")
        return False
@app.route('/submit_ballot', methods=['POST'])
def submit_ballot():
    global PUBLIC_KEY
    try:
        data = request.json
        app.logger.debug(f"Received ballot: {data}")

        if not PUBLIC_KEY:
            fetch_public_key()
            if not PUBLIC_KEY:
                return jsonify({"status": "error", "message": "Public key not available"}), 500

        # Convert hex strings to Integer
        c1 = Integer(int(data['c1'], 16))
        c2 = Integer(int(data['c2'], 16))

        if verify_proof(c1, c2, data['proof'], PUBLIC_KEY):
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO ballots (c1, c2, proof) VALUES (?, ?, ?)",
                     (hex(c1), hex(c2), json.dumps(data['proof'])))
            conn.commit()
            conn.close()
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "invalid proof"}), 400

    except Exception as e:
        app.logger.error(f"Ballot submission error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/tally_votes', methods=['GET'])
def tally_votes():
    global PUBLIC_KEY
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Homomorphic aggregation of all votes
    c.execute("SELECT c1, c2 FROM ballots")
    c1_product = Integer(1)
    c2_product = Integer(1)
    p = Integer(PUBLIC_KEY['p'])
    
    for row in c.fetchall():
        c1 = Integer(row[0])
        c2 = Integer(row[1])
        c1_product = (c1_product * c1) % p
        c2_product = (c2_product * c2) % p
    
    # Get total number of ballots
    c.execute("SELECT COUNT(*) FROM ballots")
    total_votes = c.fetchone()[0]
    conn.close()
    
    # Collect decryption shares from tally servers (t=2)
    shares = []
    tally_servers = [
        {"url": "https://13.235.82.184:5003/decrypt_share", "id": 1},
        {"url": "https://13.201.132.148:5003/decrypt_share", "id": 2},
        {"url": "https://43.204.237.162:5003/decrypt_share", "id": 3}
    ]
    
    try:
        for server in tally_servers[:2]:  # Threshold t=2
            response = requests.post(server['url'], json={"c1": str(c1_product)})
            response.raise_for_status()
            shares.append((server['id'], Integer(response.json()['share'])))
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Tally server error: {str(e)}"}), 500
    
    # Lagrange interpolation to combine shares
    secret = Integer(1)
    indices = [s[0] for s in shares]
    for idx, share in shares:
        λ = lagrange_coefficient(indices, idx, p)
        secret = (secret * pow(share, λ, p)) % p
    
    # Decrypt: m = c2 * secret^{-1} mod p
    m = (c2_product * pow(secret, -1, p)) % p
    
    # Compute d where g^d = m (via brute-force search)
    d = 0
    g = Integer(PUBLIC_KEY['g'])
    while pow(g, d, p) != m and d <= total_votes:
        d += 1
    
    # Final tally calculation
    party_a = (d + total_votes) // 2
    party_b = total_votes - party_a
    
    return jsonify({
        "result": {
            "Party A": party_a,
            "Party B": party_b
        },
        "audit_data": {
            "encrypted_votes": c1_product, 
            "combined_decryption": secret,
            "decrypted_result": m,
            "discrete_log": d
        }
    })
if __name__ == '__main__':
    init_db()
    fetch_public_key()  # Fetch key on startup
    app.run(host='192.168.113.92', port=5001,debug=True, ssl_context=('/home/md-ganim/Desktop/bulletin1.crt', '/home/md-ganim/Desktop/bulletin1.key'))

