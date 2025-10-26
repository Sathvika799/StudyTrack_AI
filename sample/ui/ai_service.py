# ui/ai_service.py

import os
import requests
import json
from django.conf import settings

def generate_quiz_from_ai(course_name, difficulty):
    """
    Calls the Google Gemini API to generate a 10-question MCQ quiz.
    """
    API_KEY = settings.GOOGLE_API_KEY
    if not API_KEY:
        print("Error: Google API Key not found in settings.")
        return None

    # Use the latest supported model (as of Oct 2025)
    MODEL_NAME = "gemini-2.5-flash" # Reverted to a more stable and widely available model
    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    prompt = f"""
    You are a quiz generation expert. Create a 10-question multiple-choice quiz on the topic of "{course_name}"
    with a difficulty level of "{difficulty}".
    
    Return the response as a single, minified JSON object with one key: "questions".
    The value of "questions" should be a list of 10 question objects.
    Each question object must have three keys:
    1. "text": The question text (string).
    2. "answers": A list of 4 possible answer strings.
    3. "correct_answer_index": The index (0-3) of the correct answer in the "answers" list.

    Do not include any other text or explanations outside of the JSON object.
    """

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7
        }
    }
    
    response = None # Define response here to use in exception blocks
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        ai_response_str = data['candidates'][0]['content']['parts'][0]['text']

        # --- THIS IS THE UPDATED PART TO CLEAN THE RESPONSE ---
        # If the AI wraps the response in a markdown block, remove it.
        if ai_response_str.startswith("```json"):
            ai_response_str = ai_response_str.strip("```json\n").strip("```")
        
        quiz_data = json.loads(ai_response_str)

        return quiz_data.get('questions')
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error while calling Gemini API: {http_err}")
        if response is not None:
            print("Full API Response:", response.text)
    except (json.JSONDecodeError, KeyError, IndexError) as parse_err:
        print(f"Error parsing AI response: {parse_err}")
        if response is not None:
            print("Full API Response:", response.text)
    except requests.exceptions.RequestException as req_err:
        print(f"Request error: {req_err}")

    return None