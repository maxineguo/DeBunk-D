from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv, find_dotenv

# --- Explicitly load environment variables from .env file ---
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=True) # Keep override=True for robustness
    print(f"DEBUG: .env file loaded from: {dotenv_path}")
else:
    print("DEBUG: .env file not found. Ensure it's in the project root.")


# --- API Keys (will be loaded from environment variables) ---
# Your developer keys
# FIX: Changed NEWS_API_KEY to NEWSAPI_API_KEY to match your .env file
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY") # <--- THIS LINE IS CHANGED
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not NEWSAPI_API_KEY or not GEMINI_API_KEY: # <--- ALSO CHANGE HERE FOR THE CHECK
    print("WARNING: NEWSAPI_API_KEY or GEMINI_API_KEY environment variable not set. API features may not work.")
else:
    print(f"DEBUG: NEWSAPI_API_KEY: {'Loaded' if NEWSAPI_API_KEY else 'Not Loaded'}") # <--- AND HERE
    print(f"DEBUG: GEMINI_API_KEY: {'Loaded' if GEMINI_API_KEY else 'Not Loaded'}")


# --- Your backend logic from debunked.py is imported here ---
from news_backend.debunked import (
    learn_chat,
    search_debunked,
    news_creation,
    misconception_creation,
    issue_creation
)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# --- API Keys (will be loaded from environment variables) ---
# Your developer keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not NEWS_API_KEY or not GEMINI_API_KEY:
    # In a real app, you might raise a more specific error or log a warning
    print("WARNING: NEWS_API_KEY or GEMINI_API_KEY environment variable not set. API features may not work.")


# --- Main Page Routes ---

@app.route('/')
def home():
    """Serves the Home page (Saved Articles & Learn Progress)."""
    return render_template('home.html')

@app.route('/feed')
def feed():
    """Serves the News Feed page."""
    return render_template('feed.html')

@app.route('/search')
def search():
    """Serves the Search page."""
    return render_template('search.html')

@app.route('/learn')
def learn():
    """Serves the Learn page (Chatbot, Articles, Quizzes)."""
    return render_template('learn.html')

# --- API Endpoints (Placeholders for now) ---
# You've mentioned these are done, but including placeholder routes for structure.

@app.route('/api/get_feed_articles', methods=['GET'])
def get_feed_articles_api():
    """
    Fetches and processes news articles for the Feed page.
    (This function will eventually call your news_fetcher and ai_processor).
    """
    # For now, just return dummy data or an empty list
    return jsonify({"articles": []})

@app.route('/api/search_articles', methods=['POST'])
def search_articles_api():
    """
    Handles search queries and returns processed, fact-checked articles.
    (This function will eventually call your news_fetcher and ai_processor).
    """
    # For now, just return dummy data or an empty list
    return jsonify({"results": []})

@app.route('/api/chatbot_message', methods=['POST'])
def chatbot_message_api():
    """
    Receives user messages for the chatbot and returns AI responses.
    (This is your next focus for the backend if not fully done).
    """
    user_message = request.json.get('message', '')
    history = request.json.get('history', [])
    print(f"Received chatbot message: {user_message} with history length: {len(history)}")
    # Placeholder response
    return jsonify({"response": f"Echo: {user_message}", "history": history + [{"role": "user", "parts": [{"text": user_message}]}]})

@app.route('/api/quiz_submit', methods=['POST'])
def quiz_submit_api():
    """
    Receives quiz answers from the Learn page.
    """
    print(f"Received quiz submission: {request.json}")
    return jsonify({"status": "success", "message": "Quiz answers received."})


# --- Run the Flask app ---
if __name__ == '__main__':
    # Make sure your virtual environment is active before running!
    # To run: python app.py
    app.run(debug=True) # debug=True allows automatic reload on code changes