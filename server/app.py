from flask import Flask, request, jsonify
from flask_cors import CORS
from engine.query_engine import query

app = Flask(__name__)
CORS(app)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("message", "").strip()

    if not question:
        return jsonify({"error": "Message is required."}), 400

    answer = query(question)
    return jsonify({"response": answer})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=8000)