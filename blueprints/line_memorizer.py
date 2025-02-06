from flask import Flask, request, redirect, url_for, send_file, render_template, jsonify, Blueprint
import json
from fuzzywuzzy import fuzz

with open('taming_of_the_shrew.json', 'r') as f:
    script_data = json.load(f)


line_memorizer = Blueprint('line_memorizer', __name__)

@line_memorizer.route('/line_memorizer')
def memorizer():
    characters = sorted(set(line['speaker'] for act in script_data["acts"] for scene in act["scenes"] for line in scene["lines"]))
    return render_template('line_memorizer.html', characters=characters)

@line_memorizer.route('/get_script', methods=['POST'])
def get_script():
    return jsonify(script_data)

@line_memorizer.route('/toggle_lines', methods=['POST'])
def toggle_lines():
    selected_character = request.json.get('character')
    return jsonify({"character": selected_character})

@line_memorizer.route('/check_speech', methods=['POST'])
def check_speech():
    data = request.get_json()
    spoken_text = data.get("spoken_text")
    correct_text = data.get("correct_text")

    print(f"Spoken: {spoken_text}")
    print(f"Correct: {correct_text}")

    if not spoken_text or not correct_text:
        return jsonify({"result": "Error: Missing data", "correct": False})

    # Simple case-insensitive comparison (can improve with NLP)
    ratio = fuzz.ratio(spoken_text.strip().lower(), correct_text.strip().lower())
    if ratio > 80:
        return jsonify({"result": "Correct!", "correct": True})
    return jsonify({"result": "Try again!", "correct": False})