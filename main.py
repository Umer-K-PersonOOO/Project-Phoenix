import ollama
from flask import Flask, request, jsonify, render_template, Response
import time

app = Flask(__name__, static_folder='static', template_folder='templates')

roles = {
    "waiter": "You are a waiter in a Spanish restaurant. Greet the customer and take their order.",
    "tour_guide": "You are a tour guide in Madrid. Describe the historical significance of Plaza Mayor.",
    "sports_fan": "You are a fan at a football game. Discuss the match with another fan."
}

def generate_role_play_stream(role, user_input, language):
    scenario = roles.get(role, "You are a conversational partner.")
    prompt = f"{scenario}\nUser: {user_input}\nAI (respond in {language}):"
    response = ollama.chat(
        model='llama3',  # Replace with the actual model name provided by Ollama
        messages=[{'role': 'user', 'content': prompt}]
    )
    if 'message' in response and 'content' in response['message']:
        content = response['message']['content']
        for char in content:
            yield f"data: {char}\n\n"
            time.sleep(0.05)  # Simulate delay
    else:
        yield "data: Error: 'message' or 'content' key not found in the response\n\n"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    if request.is_json:
        data = request.get_json()
        role = data.get('role')
        user_input = data.get('input')
        language = data.get('language', 'Spanish')  # Default to Spanish if not specified
        return Response(generate_role_play_stream(role, user_input, language), content_type='text/event-stream')
    else:
        return jsonify({"error": "Request must be JSON"}), 415

@app.route('/chat-stream')
def chat_stream():
    role = request.args.get('role')
    user_input = request.args.get('input')
    language = request.args.get('language', 'Spanish')  # Default to Spanish if not specified
    return Response(generate_role_play_stream(role, user_input, language), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
