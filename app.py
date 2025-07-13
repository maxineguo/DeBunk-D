from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from dotenv import load_dotenv, find_dotenv
import uuid
import time
import threading
import collections
import traceback
import requests
from news_backend.debunked import Article, enforce_rate_limit # Import enforce_rate_limit

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
    get_news_headlines,
    get_misconception_headlines,
    get_issue_headlines,
    create_full_news_article,
    create_full_misconception_article,
    create_full_issue_article,
    API_CALL_DELAY
)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# --- Global Caching and Threading Setup ---
ARTICLE_CACHE = {} # Stores full article objects by ID for /article/<id> route

feed_cache = {
    "latest_news": {"headlines": [], "full_articles": [], "timestamp": 0, "last_generated_headline_index": -1, "last_generated_article_index": -1, "user_requested_more": False},
    "general_misconceptions": {"headlines": [], "full_articles": [], "timestamp": 0, "last_generated_headline_index": -1, "last_generated_article_index": -1, "user_requested_more": False},
    "important_issues": {"headlines": [], "full_articles": [], "timestamp": 0, "last_generated_headline_index": -1, "last_generated_article_index": -1, "user_requested_more": False}
}
cache_lock = threading.Lock()

CACHE_DURATION = 3600 # Cache articles for 1 hour (in seconds)
BACKGROUND_CALL_INTERVAL = API_CALL_DELAY + 1 # Use API_CALL_DELAY from debunked.py, plus a buffer
MAX_HEADLINES_TO_GENERATE_AT_ONCE = 32 # Generate 32 headlines at once when replenishing
MAX_ARTICLES_PER_SECTION = 32 # Max full articles to generate/store per section (3 full pages max)
INITIAL_DISPLAY_ARTICLES = 4 # Initial articles to display on feed load

stop_background_thread = threading.Event()
background_thread = None

section_configs = {
    "latest_news": {
        "get_headlines_func": get_news_headlines,
        "create_article_func": create_full_news_article,
        "needs_news_key": True
    },
    "general_misconceptions": {
        "get_headlines_func": get_misconception_headlines,
        "create_article_func": create_full_misconception_article,
        "needs_news_key": False
    },
    "important_issues": {
        "get_headlines_func": get_issue_headlines,
        "create_article_func": create_full_issue_article,
        "needs_news_key": False
    }
}

# Global variable to track 429 errors and implement backoff
last_429_error_time = 0
BACKOFF_DURATION_ON_429 = 300 # 5 minutes in seconds, can be increased if needed

def background_article_generation_worker(gemini_key, news_key):
    global last_429_error_time
    print("DEBUG: Background article generation worker started.")
    
    while not stop_background_thread.is_set():
        current_time = time.time()

        # Check if we are in a 429 backoff period
        if current_time - last_429_error_time < BACKOFF_DURATION_ON_429:
            remaining_backoff = BACKOFF_DURATION_ON_429 - (current_time - last_429_error_time)
            print(f"DEBUG: Background: In 429 backoff. Sleeping for {remaining_backoff:.2f} seconds.")
            time.sleep(remaining_backoff)
            continue # Re-evaluate after backoff (this will re-check the 429 time)

        try:
            needs_generation = False
            with cache_lock:
                for sec_name in section_configs:
                    # Check if headlines need replenishment (if below max capacity)
                    if len(feed_cache[sec_name]["headlines"]) < MAX_HEADLINES_TO_GENERATE_AT_ONCE:
                        needs_generation = True
                        break
                    # Check if full articles need generation (if below max capacity and have headlines)
                    if len(feed_cache[sec_name]["full_articles"]) < MAX_ARTICLES_PER_SECTION and \
                       feed_cache[sec_name]["last_generated_article_index"] < len(feed_cache[sec_name]["headlines"]) - 1:
                        needs_generation = True
                        break
            
            if not needs_generation:
                print("DEBUG: Background: All sections fully cached or no immediate generation needed. Sleeping longer.")
                time.sleep(30) # Sleep longer if nothing to do
                continue

            task_processed = False
            for sec_name, config in section_configs.items():
                with cache_lock:
                    current_headlines_count = len(feed_cache[sec_name]["headlines"])
                    current_articles_count = len(feed_cache[sec_name]["full_articles"])

                # Phase 1: Generate Headlines if needed
                if current_headlines_count < MAX_HEADLINES_TO_GENERATE_AT_ONCE:
                    print(f"DEBUG: Background: Replenishing headlines for {sec_name} (current: {current_headlines_count}).")
                    try:
                        if config["needs_news_key"]:
                            new_headlines = config["get_headlines_func"](gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE - current_headlines_count)
                        else:
                            new_headlines = config["get_headlines_func"](gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE - current_headlines_count)
                        
                        with cache_lock:
                            existing_headlines_set = set(feed_cache[sec_name]["headlines"])
                            unique_new_headlines = [h for h in new_headlines if h not in existing_headlines_set]
                            feed_cache[sec_name]["headlines"].extend(unique_new_headlines)
                            print(f"DEBUG: Background: Added {len(unique_new_headlines)} unique headlines to {sec_name}. Total: {len(feed_cache[sec_name]['headlines'])}")
                        task_processed = True
                        break # Process one generation task per loop iteration
                    except Exception as e:
                        print(f"ERROR in background headline generation for {sec_name}: {e}")
                        traceback.print_exc()
                        if "429 RESOURCE_EXHAUSTED" in str(e):
                            last_429_error_time = time.time() # Mark 429 time
                            print(f"DEBUG: Background: Encountered 429. Initiating backoff for {BACKOFF_DURATION_ON_429} seconds.")
                        time.sleep(BACKGROUND_CALL_INTERVAL * 2) # Longer sleep on any error
                        task_processed = True
                        break

                # Phase 2: Generate Full Articles from Headlines
                if current_headlines_count > 0 and current_articles_count < MAX_ARTICLES_PER_SECTION:
                    with cache_lock:
                        next_headline_index = feed_cache[sec_name]["last_generated_article_index"] + 1
                        if next_headline_index < current_headlines_count:
                            headline_to_process = feed_cache[sec_name]["headlines"][next_headline_index]
                        else:
                            headline_to_process = None

                    if headline_to_process:
                        print(f"DEBUG: Background: Generating full article for '{headline_to_process}' in {sec_name}.")
                        try:
                            raw_articles_for_source = []
                            if sec_name == "latest_news":
                                # NewsAPI call is now within create_full_news_article or get_news_headlines
                                # but for sourcing, we need some raw articles here if not already fetched.
                                # This part needs careful thought to avoid redundant NewsAPI calls.
                                # Let's assume create_full_news_article will handle its own NewsAPI calls for sourcing.
                                pass 

                            if sec_name == "latest_news":
                                full_article = config["create_article_func"](headline_to_process, raw_articles_for_source, gemini_key)
                            else:
                                full_article = config["create_article_func"](headline_to_process, gemini_key)
                            
                            with cache_lock:
                                # Always advance the index for the headline we tried to process
                                feed_cache[sec_name]["last_generated_article_index"] = next_headline_index

                                if full_article:
                                    article_id = full_article['id'] 
                                    if article_id not in ARTICLE_CACHE:
                                        ARTICLE_CACHE[article_id] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        print(f"DEBUG: Background: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    else:
                                        print(f"DEBUG: Background: Duplicate full article ID '{article_id}' found, skipping addition to feed_cache.")
                                else:
                                    print(f"WARNING: Background: Failed to generate full article for '{headline_to_process}'.")
                                task_processed = True
                                break # Process one generation task per loop iteration
                        except Exception as e:
                            print(f"ERROR in background full article generation for {sec_name} (headline '{headline_to_process}'): {e}")
                            traceback.print_exc()
                            if "429 RESOURCE_EXHAUSTED" in str(e):
                                last_429_error_time = time.time() # Mark 429 time
                                print(f"DEBUG: Background: Encountered 429. Initiating backoff for {BACKOFF_DURATION_ON_429} seconds.")
                            with cache_lock:
                                feed_cache[sec_name]["last_generated_article_index"] = next_headline_index # Still advance index on error
                            time.sleep(BACKGROUND_CALL_INTERVAL * 2)
                            task_processed = True
                            break
                    else:
                        print(f"DEBUG: Background: No more headlines to process for {sec_name} or already at target count.")
                        pass

            if not task_processed:
                print("DEBUG: Background: No generation task processed this loop. Sleeping normally.")
                time.sleep(BACKGROUND_CALL_INTERVAL)

        except Exception as e:
            print(f"CRITICAL ERROR in background generation worker main loop: {e}")
            traceback.print_exc()
            time.sleep(10)

    print("DEBUG: Background article generation worker stopped.")


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
        return render_template('error.html', message="Article not found or has expired."), 404
    return render_template('article_detail.html', article=article)


# --- API Endpoints ---

@app.route('/api/get_feed_articles', methods=['GET'])
def get_feed_articles_api():
    """
    Fetches and processes news articles for the Feed page.
    Prioritizes serving from cache. If cache is empty/stale, returns current cache.
    """
    user_newsapi_key_from_header = request.headers.get('X-User-News-API-Key')
    news_api_key_to_use = user_newsapi_key_from_header if user_newsapi_key_from_header else NEWSAPI_API_KEY

    user_gemini_api_key_from_header = request.headers.get('X-User-Gemini-API-Key')
    gemini_api_key_to_use = user_gemini_api_key_from_header if user_gemini_api_key_from_header else GEMINI_API_KEY

    if not news_api_key_to_use or not gemini_api_key_to_use:
        # If API keys are missing, return an error and prompt user
        return jsonify({"error": "API keys not provided or configured. Please enter them in your profile settings.", "code": 401}), 401

    current_time = time.time()
    
    # Always return current cache content immediately.
    # The background worker is responsible for populating and refreshing it.
    with cache_lock:
        response_data = {
            "latest_news": [a for a in feed_cache["latest_news"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION],
            "general_misconceptions": [a for a in feed_cache["general_misconceptions"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION],
            "important_issues": [a for a in feed_cache["important_issues"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION]
        }
        # Signal the background worker to potentially generate more if needed
        # This is for when the user explicitly refreshes, or if the cache is very low
        for sec in feed_cache:
            # If cache is old, or if user explicitly requested more (via refresh button)
            # The 'refresh' query parameter will be sent by feed.js when the button is clicked.
            if (current_time - feed_cache[sec]["timestamp"] > CACHE_DURATION / 2) or \
               (len(feed_cache[sec]["full_articles"]) < INITIAL_DISPLAY_ARTICLES and request.args.get('refresh') == 'true'):
                feed_cache[sec]["user_requested_more"] = True
                print(f"DEBUG: get_feed_articles_api: Setting user_requested_more=True for {sec}.")
            else:
                feed_cache[sec]["user_requested_more"] = False # Reset if not explicitly requested

    print("DEBUG: Serving feed articles from cache. Background worker will handle generation.")
    return jsonify(response_data)


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

        article_id = detailed_article_result['id'] 
        ARTICLE_CACHE[article_id] = detailed_article_result

        return jsonify({"results": [detailed_article_result]})
    except Exception as e:
        print(f"Error performing search in app.py: {e}")
        traceback.print_exc()
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
        traceback.print_exc()
        return jsonify({"response": "Sorry, I'm having trouble responding right now. Please try again.", "history": history}), 500

@app.route('/api/quiz_submit', methods=['POST'])
def quiz_submit_api():
    print(f"Received quiz submission: {request.json}")
    return jsonify({"status": "success", "message": "Quiz answers received."})

# --- Run the Flask app ---
if __name__ == '__main__':
    if NEWSAPI_API_KEY and GEMINI_API_KEY:
        background_thread = threading.Thread(
            target=background_article_generation_worker,
            args=(GEMINI_API_KEY, NEWSAPI_API_KEY),
            name="background_gen_worker"
        )
        background_thread.daemon = True
        background_thread.start()
        print("DEBUG: Background generation worker started on app startup.")

        # --- TEMPORARY CODE TO STOP BACKGROUND WORKER AFTER 5 MINUTES ---
        # Define the duration in seconds (5 minutes = 300 seconds)
        STOP_WORKER_AFTER_SECONDS = 300

        def stop_worker_gracefully():
            print(f"DEBUG: Timer triggered: Stopping background worker after {STOP_WORKER_AFTER_SECONDS} seconds.")
            stop_background_thread.set()

        # Create and start the timer
        timer = threading.Timer(STOP_WORKER_AFTER_SECONDS, stop_worker_gracefully)
        timer.start()
        print(f"DEBUG: Background worker will stop automatically in {STOP_WORKER_AFTER_SECONDS} seconds.")
        # --- END TEMPORARY CODE ---

    else:
        print("WARNING: Background generation worker not started due to missing API keys.")

    app.run(debug=True)