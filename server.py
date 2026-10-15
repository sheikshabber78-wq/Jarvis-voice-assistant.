import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "JARVIS server is running"
    })

@app.route("/chat", methods=["POST"])
def chat():
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return jsonify({
            "error": "API key is not configured on the server"
        }), 500

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Please send a message"
        }), 400

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="gpt-5.5",
            instructions=(
                "You are JARVIS, a helpful personal assistant. "
                "Understand Telugu and reply in the language "
                "the user uses. Be clear and concise."
            ),
            input=message
        )

        return jsonify({
            "reply": response.output_text
        })

    except Exception:
        app.logger.exception("AI request failed")
        return jsonify({
            "error": "AI request failed. Check server configuration."
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(
        os.environ.get("PORT", "5000")
    ))