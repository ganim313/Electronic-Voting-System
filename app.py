from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/results.html')
def serve_results():
    return send_from_directory('.', 'results.html')

if __name__ == '__main__':
    app.run(host='192.168.113.28',port=8080, ssl_context=('crypto/elections/client-server.crt','/crypto/elections/client-server.key'),debug=True)