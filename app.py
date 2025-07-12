from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from dotenv import load_dotenv, find_dotenv
import uuid # For generating unique IDs for articles

# --- Explicitly load environment variables from .env file ---
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path, override=True)
else:
    print("DEBUG: .env file not found. Ensure it's in the project root.")

# --- API Keys (will be loaded from environment variables) ---
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not NEWSAPI_API_KEY or not GEMINI_API_KEY:
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

# In-memory cache for articles (simulates a database for this demo)
# This will reset every time the server restarts
ARTICLE_CACHE = {}

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

# --- New Route for Full Article Display ---
@app.route('/article/<article_id>')
def article_detail(article_id):
    article = ARTICLE_CACHE.get(article_id)
    if not article:
        # Handle case where article is not found (e.g., direct access, server restart)
        return render_template('error.html', message="Article not found or has expired."), 404
    return render_template('article_detail.html', article=article)


# --- API Endpoints ---

@app.route('/api/get_feed_articles', methods=['GET'])
def get_feed_articles_api():
    """
    Fetches and processes news articles for the Feed page.
    """
    user_newsapi_key_from_header = request.headers.get('X-User-News-API-Key')
    news_api_key_to_use = user_newsapi_key_from_header if user_newsapi_key_from_header else NEWSAPI_API_KEY

    user_gemini_api_key_from_header = request.headers.get('X-User-Gemini-API-Key')
    gemini_api_key_to_use = user_gemini_api_key_from_header if user_gemini_api_key_from_header else GEMINI_API_KEY

    if not news_api_key_to_use or not gemini_api_key_to_use:
        return jsonify({"error": "API keys not provided or configured."}), 401

    try:
        latest_news_articles = news_creation(gemini_api_key_to_use, news_api_key_to_use)
        general_misconceptions_articles = misconception_creation(gemini_api_key_to_use)
        important_issues_articles = issue_creation(gemini_api_key_to_use)

        # Add unique IDs and cache articles before sending to frontend
        for article_list in [latest_news_articles, general_misconceptions_articles, important_issues_articles]:
            for article in article_list:
                # Use existing URL if it's unique, otherwise generate UUID
                if article.get('url') and not article['url'].startswith('debunkd-'):
                    article_id = article['url'] # Use URL as ID for NewsAPI articles
                else:
                    article_id = str(uuid.uuid4()) # Generate UUID for AI-generated content

                article['id'] = article_id
                ARTICLE_CACHE[article_id] = article

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

        # Add unique ID and cache for search results too
        article_id = str(uuid.uuid4()) # Always generate UUID for search results
        detailed_article_result['id'] = article_id
        ARTICLE_CACHE[article_id] = detailed_article_result

        # Return a list of one result for consistency with feed structure
        return jsonify({"results": [detailed_article_result]})
    except Exception as e:
        print(f"Error performing search in app.py: {e}")
        return jsonify({"error": "Failed to perform search", "message": str(e)}), 500

@app.route('/api/chatbot_message', methods=['POST'])
def chatbot_message_api():
    user_message = request.json.get('message', '')
    history = request.json.get('history', [])

    user_gemini_api_key_from_header = request.headers.get('X-User-Gemini-API-Key')
    gemini_api_key_to_use = user_gemini_api_key_from_header if user_gemini_api_key_from_header else GEMINI_API_KEY

    if not gemini_api_key_to_use:
        return jsonify({"response": "Error: Gemini API key is missing.", "history": history}), 401

    try:
        model_response_text, updated_history = learn_chat(history, user_message, gemini_api_key_to_use)
        return jsonify({"response": model_response_text, "history": updated_history})
    except Exception as e:
        print(f"Error in chatbot_message_api: {e}")
        return jsonify({"response": "Sorry, I'm having trouble responding right now. Please try again.", "history": history}), 500

@app.route('/api/quiz_submit', methods=['POST'])
def quiz_submit_api():
    print(f"Received quiz submission: {request.json}")
    return jsonify({"status": "success", "message": "Quiz answers received."})

# --- Run the Flask app ---
if __name__ == '__main__':
    app.run(debug=True)