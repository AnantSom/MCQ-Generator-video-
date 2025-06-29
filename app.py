import os
import base64
import json
import re
from urllib.parse import urlparse, parse_qs

# Use waitress for a stable production-ready server
from waitress import serve
from dotenv import load_dotenv
from flask import Flask, render_template, request
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# --- App Initialization ---
app = Flask(__name__)
load_dotenv()

# --- Robust AI and API Setup ---
# We wrap this in a try/except block to provide clear errors instead of crashing
model = None
try:
    api_key = os.getenv("MY_API_KEY")
    if not api_key or "your_google_api_key_here" in api_key:
        print("Please set your real Google API Key to continue.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("[MCQ Video] Google AI SDK configured successfully.")

except Exception as e:
    print(f"FATAL ERROR during Google AI setup: {e}")

# --- Helper Functions ---
def clean_json_response(text):
    """Robustly finds and extracts a JSON array from a string."""
    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Find JSON array pattern
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match: 
        return match.group(0)
    return text.strip()

def get_video_id(youtube_url):
    """Extracts the video ID from various YouTube URL formats."""
    if not isinstance(youtube_url, str): 
        return None
    
    # Handle different YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    return None

def get_transcript(video_id):
    """Retrieves the transcript for a given video ID."""
    try:
        # Try to get transcript in different languages
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        return " ".join([entry["text"] for entry in transcript_list])
    except Exception as e:
        print(f"Transcript retrieval failed for video_id {video_id}: {e}")
        try:
            # Try to get any available transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry["text"] for entry in transcript_list])
        except Exception as e2:
            print(f"No transcript available for video_id {video_id}: {e2}")
            return None

# --- Flask Routes ---
@app.route("/", methods=["GET", "POST"])
def generate_mcqs():
    if model is None:
        return render_template("index.html", error="Application is not configured correctly. Please check the API key.")

    if request.method == "GET":
        return render_template('index.html')
    
    video_url = request.form.get("video_url", "").strip()
    mcq_count = request.form.get("mcq_count", "5")
    
    if not video_url:
        return render_template("index.html", error="Please provide a YouTube URL.")
    
    video_id = get_video_id(video_url)
    if not video_id:
        return render_template("index.html", error="Invalid YouTube URL provided. Please check the URL format.")

    try:
        # Validate mcq_count
        try:
            mcq_count = int(mcq_count)
            if mcq_count < 1 or mcq_count > 15:
                mcq_count = 5
        except ValueError:
            mcq_count = 5
            
        transcript = get_transcript(video_id)
        if not transcript:
            return render_template("index.html", error="Could not retrieve transcript. The video may have captions disabled, be private, or not available in supported languages.")
        
        # Truncate transcript if too long (to avoid API limits)
        if len(transcript) > 8000:
            transcript = transcript[:8000] + "..."
            
        prompt = f"""From the following transcript, generate exactly {mcq_count} multiple choice questions. 

IMPORTANT: Your response must be ONLY a valid JSON array with no additional text, explanations, or markdown formatting.

Each question object must have exactly these three keys:
- "question": A clear, specific question based on the content
- "options": An array of exactly 4 different answer choices
- "answer": The correct answer that exactly matches one of the options

Example format:
[
  {{
    "question": "What is the main topic discussed?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "answer": "Option A"
  }}
]

Transcript:
{transcript}"""
        
        response = model.generate_content(prompt)
        cleaned_text = clean_json_response(response.text)
        
        # Parse and validate JSON
        mcqs = json.loads(cleaned_text)
        
        # Validate structure
        if not isinstance(mcqs, list) or len(mcqs) == 0:
            raise ValueError("Invalid MCQ format received")
            
        for i, mcq in enumerate(mcqs):
            if not all(key in mcq for key in ['question', 'options', 'answer']):
                raise ValueError(f"Missing required keys in question {i+1}")
            if not isinstance(mcq['options'], list) or len(mcq['options']) != 4:
                raise ValueError(f"Invalid options format in question {i+1}")
            if mcq['answer'] not in mcq['options']:
                raise ValueError(f"Answer not found in options for question {i+1}")
        
        encoded_json = base64.b64encode(json.dumps(mcqs).encode()).decode()
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        
        return render_template("result.html", questions=mcqs, video_url=embed_url, answers_json=encoded_json)
        
    except json.JSONDecodeError as e:
        raw_response = response.text if 'response' in locals() else "No response from AI."
        print(f"--- JSON PARSE ERROR ---\n{raw_response}\n----------------------")
        return render_template("index.html", error="The AI returned an invalid format. Please try again with a different video or fewer questions.")
    except Exception as e:
        print(f"--- UNKNOWN ERROR ---\n{e}\n---------------------")
        return render_template("index.html", error=f"An unexpected error occurred: {str(e)}")

@app.route("/submit", methods=["POST"])
def submit_answers():
    try:
        encoded_json = request.form.get("answers_json")
        if not encoded_json:
            raise ValueError("Missing answers data")
            
        questions = json.loads(base64.b64decode(encoded_json).decode())
        
        user_answers, correctness = [], []
        for i in range(len(questions)):
            selected_option = request.form.get(f"q{i}", "")
            user_answers.append(selected_option)
            correctness.append(selected_option == questions[i]["answer"])
            
        total = len(questions)
        score = sum(correctness)
        percentage = round((score / total) * 100, 2) if total > 0 else 0
        
        return render_template("submission_result.html",
                               video_url=request.form.get("video_url"),
                               questions=questions,
                               user_answers=user_answers,
                               correctness=correctness,
                               score=score,
                               total=total,
                               percentage=percentage)
    except Exception as e:
        print(f"Error processing submission: {e}")
        return render_template("index.html", error="Error processing your answers. Please try again.")

@app.route("/health")
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {"status": "healthy", "model_configured": model is not None}

# --- Main Execution ---
if __name__ == '__main__':
    # Get port configuration
    public_port = int(os.getenv("PUBLIC_PORT", 5000))
    flask_port = int(os.getenv("FLASK_RUN_PORT", 10000))
    
    # Determine if running in Docker
    is_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_CONTAINER') == 'true'
    
    # Only try to serve the app if the model was configured correctly
    if model is not None:
        if is_docker:
            print(f"Running in Docker container")
            print(f"Open your web browser and go to: http://localhost:{public_port}")
        else:
            print(f"Running locally")
            print(f"Open your web browser and go to: http://localhost:{flask_port}")
        
        if is_docker:
            # In Docker, use waitress for production
            serve(app, host="0.0.0.0", port=flask_port)
        else:
            # For local development, you can choose between Flask dev server or waitress
            debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
            if debug_mode:
                print("🔧 Running in debug mode with Flask dev server")
                app.run(debug=True, host="0.0.0.0", port=flask_port)
            else:
                print("🔧 Running with waitress server")
                serve(app, host="0.0.0.0", port=flask_port)
    else:
        print("Application failed to start due to configuration error.")
        exit(1)