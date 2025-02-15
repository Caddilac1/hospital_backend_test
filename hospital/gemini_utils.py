import google.generativeai as genai
import os

# Load API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY! Please set it in your .env file.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def extract_actionable_steps(note_text):
    """Use Gemini AI to extract actionable steps from a doctor's note."""
    prompt = f"""
    Extract actionable steps from the following doctor's note. 
    - Create a 'checklist' of immediate tasks (e.g., buy medicine, drink water).
    - Create a 'plan' for scheduled actions (e.g., take medicine for 7 days).

    Doctor's Note: {note_text}

    Response Format:
    {{
        "checklist": ["Task 1", "Task 2"],
        "plan": [
            {{"task": "Task name", "duration": "e.g., 7 days", "frequency": "e.g., once per day"}}
        ]
    }}
    """

    # Call Gemini AI
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)

    # Convert response to a dictionary
    try:
        actionable_steps = eval(response.text)  # Convert AI response to dict
        return actionable_steps
    except:
        return {"error": "Failed to parse Gemini response"}

