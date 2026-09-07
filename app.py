import os
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_version():
    version_file_path = os.path.join(os.path.dirname(__file__), 'VERSION')
    try:
        with open(version_file_path, 'r') as f:
            return f.read().strip()
    except Exception:
        return "unknown"

VERSION = get_version()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "application": "student-ml-api",
        "version": VERSION
    })

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    
    if data is None or 'value' not in data:
        return jsonify({"error": "Missing 'value' in request JSON"}), 400
        
    value = data['value']
    
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return jsonify({"error": "'value' must be a number"}), 400
        
    prediction = value * 2
    return jsonify({
        "input": value,
        "prediction": prediction
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
