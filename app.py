from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv, find_dotenv

# --- Explicitly load environment variables from .env file ---
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=True) # Keep override=True for robustness
else:
    print("DEBUG: .env file not found. Ensure it's in the project root.")


# --- API Keys (will be loaded from environment variables) ---
# Your developer keys
# FIX: Changed NEWS_API_KEY to NEWSAPI_API_KEY to match your .env file
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY") # <--- THIS LINE IS CHANGED
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


if not NEWSAPI_API_KEY or not GEMINI_API_KEY: # <--- ALSO CHANGE HERE FOR THE CHECK
    print("WARNING: NEWSAPI_API_KEY or GEMINI_API_KEY environment variable not set. API features may not work.")

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
    """
    # Determine which API key to use for NewsAPI
    user_newsapi_key_from_header = request.headers.get('X-User-News-API-Key')
    news_api_key_to_use = user_newsapi_key_from_header if user_newsapi_key_from_header else NEWSAPI_API_KEY

    # Determine which API key to use for Gemini
    user_gemini_api_key_from_header = request.headers.get('X-User-Gemini-API-Key')
    gemini_api_key_to_use = user_gemini_api_key_from_header if user_gemini_api_key_from_header else GEMINI_API_KEY

    if not news_api_key_to_use or not gemini_api_key_to_use:
        return jsonify({"error": "API keys not provided or configured."}), 401

    try:
        # Call your functions to get data for each section
        # Pass the determined API keys
        latest_news_articles = news_creation(gemini_api_key_to_use, news_api_key_to_use)
        general_misconceptions_articles = misconception_creation(gemini_api_key_to_use)
        important_issues_articles = issue_creation(gemini_api_key_to_use)

        # Return a single JSON object containing all three lists
        return jsonify({
            "latest_news": latest_news_articles,
            "general_misconceptions": general_misconceptions_articles,
            "important_issues": important_issues_articles
        })
    except Exception as e:
        print(f"Error fetching feed articles: {e}")
        return jsonify({"error": "Failed to load articles", "message": str(e)}), 500

@app.route('/api/search_articles', methods=['GET'])
def search_articles_api():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "No search query provided"}), 400

    user_newsapi_key_from_header = request.headers.get('X-User-News-API-Key')
    news_api_key_to_use = user_newsapi_key_from_header if user_newsapi_key_from_header else NEWSAPI_API_KEY

    user_gemini_api_key_from_header = request.headers.get('X-User-Gemini-API-Key')
    gemini_api_key_to_use = user_gemini_api_key_from_header if user_gemini_api_key_from_header else GEMINI_API_KEY

    if not news_api_key_to_use or not gemini_api_key_to_use:
        return jsonify({"error": "API keys not provided or configured."}), 401

    try:
        detailed_article_result = search_debunked(query, gemini_api_key_to_use, news_api_key_to_use)

        # --- ADD THIS DEBUG PRINT STATEMENT ---
        print(f"DEBUG: search_debunked returned type: {type(detailed_article_result)}")
        print(f"DEBUG: search_debunked returned value: {detailed_article_result}")
        # --- END DEBUG PRINT ---

        return jsonify({"results": [detailed_article_result]})
    except Exception as e:
        print(f"Error performing search in app.py: {e}") # Clarify where error is
        return jsonify({"error": "Failed to perform search", "message": str(e)}), 500

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