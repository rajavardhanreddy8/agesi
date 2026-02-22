import base64
s = """from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/health')
def health(): return jsonify({'status': 'bypass'})
@app.route('/')
def index(): return 'Hello Bypass'
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
"""
print(base64.b64encode(s.encode()).decode())
