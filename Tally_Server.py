# tally_server.py
from flask import Flask, request, jsonify
from Cryptodome.PublicKey import ElGamal  # For ElGamal decryption
from Cryptodome.Math.Numbers import Integer  # For modular arithmetic

app = Flask(__name__)

# Partial decryption of an encrypted ballot
@app.route('/decrypt_share', methods=['POST'])
def decrypt_share():
    data = request.json
    encrypted_ballot = data['encrypted_share']
    c1, c2 = encrypted_ballot["c1"], encrypted_ballot["c2"]

    # Each Tally Server has a share of the private key
    private_key_share = 12345  # Replace with the actual private key share

    # Perform partial decryption
    s = pow(c1, private_key_share, private_key.p)  # s = c1^x_i mod p
    s_inv = pow(s, -1, private_key.p)  # s_inv = s^(-1) mod p
    decrypted_share = (c2 * s_inv) % private_key.p  # m_i = c2 * s_inv mod p

    return jsonify({"decrypted_share": decrypted_share})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)  # Change port for each Tally Server