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
    API_CALL_DELAY # Import the delay from debunked.py
)

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# --- Global Caching and Threading Setup ---
ARTICLE_CACHE = {} # Stores full article objects by ID for /article/<id> route

feed_cache = {
    "latest_news": {"headlines": [], "full_articles": [], "timestamp": 0, "last_generated_headline_index": -1, "last_generated_article_index": -1},
    "general_misconceptions": {"headlines": [], "full_articles": [], "timestamp": 0, "last_generated_headline_index": -1, "last_generated_article_index": -1},
    "important_issues": {"headlines": [], "full_articles": [], "timestamp": 0, "last_generated_headline_index": -1, "last_generated_article_index": -1}
}
cache_lock = threading.Lock()

# New global state for the background worker's sequence
worker_state = {
    "initial_generation_complete": False,
    "creation_sequence_active": False,
    "refresh_sequence_active": False,
    "current_generation_step": 0,      # Tracks progress within a sequence
    "last_sequence_execution_time": 0, # To manage the 1-minute waits
    "user_requested_more": False       # Flag set by API endpoint for refresh
}
worker_state_lock = threading.Lock() # Protects worker_state

CACHE_DURATION = 3600 # Cache articles for 1 hour (in seconds) - Less relevant with explicit cycles
# API_CALL_DELAY is imported from debunked.py

MAX_HEADLINES_TO_GENERATE_AT_ONCE = 15 # Changed from 32
MAX_ARTICLES_PER_SECTION = 30 # Max full articles to generate/store per section (target for creation/refresh)
INITIAL_DISPLAY_ARTICLES = 3 # Initial articles to display on feed load (from the first 3 generated)

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
BACKOFF_DURATION_ON_429 = 60 # 5 minutes in seconds, can be increased if needed

def background_article_generation_worker(gemini_key, news_key):
    """global last_429_error_time
    print("DEBUG: Background article generation worker started.")
    
    while not stop_background_thread.is_set():
        current_time = time.time()

        with worker_state_lock:
            initial_complete = worker_state["initial_generation_complete"]
            creation_active = worker_state["creation_sequence_active"]
            refresh_active = worker_state["refresh_sequence_active"]
            current_step = worker_state["current_generation_step"]
            last_exec_time = worker_state["last_sequence_execution_time"]
            user_requested_refresh = worker_state["user_requested_more"]

        # Check if we are in a 429 backoff period
        if current_time - last_429_error_time < BACKOFF_DURATION_ON_429:
            remaining_backoff = BACKOFF_DURATION_ON_429 - (current_time - last_429_error_time)
            print(f"DEBUG: Background: In 429 backoff. Sleeping for {remaining_backoff:.2f} seconds.")
            time.sleep(remaining_backoff)
            continue

        try:
            task_processed_in_this_loop = False

            # --- Initial Generation Sequence ---
            if not initial_complete:
                print(f"DEBUG: Initial Generation Sequence - Step {current_step}")
                with cache_lock: # Acquire lock for cache modifications
                    sec_names = ["latest_news", "general_misconceptions", "important_issues"]
                    
                    if current_step == 0: # Generate 15 headlines for news
                        print("DEBUG: Initial: Generating 15 headlines for latest_news.")
                        new_headlines = section_configs["latest_news"]["get_headlines_func"](gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                        feed_cache["latest_news"]["headlines"].extend(new_headlines)
                        print(f"DEBUG: Initial: Added {len(new_headlines)} headlines to latest_news. Total: {len(feed_cache['latest_news']['headlines'])}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY) # Delay after API call
                        
                    elif current_step == 1: # Generate 3 articles for news
                        print("DEBUG: Initial: Generating 3 articles for latest_news.")
                        for _ in range(3):
                            next_headline_index = feed_cache["latest_news"]["last_generated_article_index"] + 1
                            if next_headline_index < len(feed_cache["latest_news"]["headlines"]):
                                headline_to_process = feed_cache["latest_news"]["headlines"][next_headline_index]
                                full_article = section_configs["latest_news"]["create_article_func"](headline_to_process, [], gemini_key) # raw_articles_for_source is empty for now
                                if full_article:
                                    ARTICLE_CACHE[full_article['id']] = full_article
                                    feed_cache["latest_news"]["full_articles"].append(full_article)
                                    feed_cache["latest_news"]["timestamp"] = time.time()
                                    feed_cache["latest_news"]["last_generated_article_index"] = next_headline_index
                                    print(f"DEBUG: Initial: Added full article to latest_news. Total: {len(feed_cache['latest_news']['full_articles'])}")
                                time.sleep(API_CALL_DELAY)
                            else:
                                print("WARNING: Initial: Not enough headlines for latest_news to generate 3 articles.")
                                break # Exit inner loop if no more headlines
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True

                    elif current_step == 2: # Generate 15 headlines for misconceptions
                        print("DEBUG: Initial: Generating 15 headlines for general_misconceptions.")
                        new_headlines = section_configs["general_misconceptions"]["get_headlines_func"](gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                        feed_cache["general_misconceptions"]["headlines"].extend(new_headlines)
                        print(f"DEBUG: Initial: Added {len(new_headlines)} headlines to general_misconceptions. Total: {len(feed_cache['general_misconceptions']['headlines'])}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 3: # Generate 3 articles for misconceptions
                        print("DEBUG: Initial: Generating 3 articles for general_misconceptions.")
                        for _ in range(3):
                            next_headline_index = feed_cache["general_misconceptions"]["last_generated_article_index"] + 1
                            if next_headline_index < len(feed_cache["general_misconceptions"]["headlines"]):
                                headline_to_process = feed_cache["general_misconceptions"]["headlines"][next_headline_index]
                                full_article = section_configs["general_misconceptions"]["create_article_func"](headline_to_process, gemini_key)
                                if full_article:
                                    ARTICLE_CACHE[full_article['id']] = full_article
                                    feed_cache["general_misconceptions"]["full_articles"].append(full_article)
                                    feed_cache["general_misconceptions"]["timestamp"] = time.time()
                                    feed_cache["general_misconceptions"]["last_generated_article_index"] = next_headline_index
                                    print(f"DEBUG: Initial: Added full article to general_misconceptions. Total: {len(feed_cache['general_misconceptions']['full_articles'])}")
                                time.sleep(API_CALL_DELAY)
                            else:
                                print("WARNING: Initial: Not enough headlines for general_misconceptions to generate 3 articles.")
                                break
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True

                    elif current_step == 4: # Generate 15 headlines for issues
                        print("DEBUG: Initial: Generating 15 headlines for important_issues.")
                        new_headlines = section_configs["important_issues"]["get_headlines_func"](gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                        feed_cache["important_issues"]["headlines"].extend(new_headlines)
                        print(f"DEBUG: Initial: Added {len(new_headlines)} headlines to important_issues. Total: {len(feed_cache['important_issues']['headlines'])}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 5: # Generate 3 articles for issues
                        print("DEBUG: Initial: Generating 3 articles for important_issues.")
                        for _ in range(3):
                            next_headline_index = feed_cache["important_issues"]["last_generated_article_index"] + 1
                            if next_headline_index < len(feed_cache["important_issues"]["headlines"]):
                                headline_to_process = feed_cache["important_issues"]["headlines"][next_headline_index]
                                full_article = section_configs["important_issues"]["create_article_func"](headline_to_process, gemini_key)
                                if full_article:
                                    ARTICLE_CACHE[full_article['id']] = full_article
                                    feed_cache["important_issues"]["full_articles"].append(full_article)
                                    feed_cache["important_issues"]["timestamp"] = time.time()
                                    feed_cache["important_issues"]["last_generated_article_index"] = next_headline_index
                                    print(f"DEBUG: Initial: Added full article to important_issues. Total: {len(feed_cache['important_issues']['full_articles'])}")
                                time.sleep(API_CALL_DELAY)
                            else:
                                print("WARNING: Initial: Not enough headlines for important_issues to generate 3 articles.")
                                break
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True

                    elif current_step == 6: # Generate 3 headlines for news (add to current 12)
                        print("DEBUG: Initial: Generating 3 more headlines for latest_news.")
                        new_headlines = section_configs["latest_news"]["get_headlines_func"](gemini_key, news_key, count=3)
                        feed_cache["latest_news"]["headlines"].extend(new_headlines)
                        print(f"DEBUG: Initial: Added {len(new_headlines)} headlines to latest_news. Total: {len(feed_cache['latest_news']['headlines'])}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 7: # Generate 3 headlines for misconceptions (add to current 12)
                        print("DEBUG: Initial: Generating 3 more headlines for general_misconceptions.")
                        new_headlines = section_configs["general_misconceptions"]["get_headlines_func"](gemini_key, count=3)
                        feed_cache["general_misconceptions"]["headlines"].extend(new_headlines)
                        print(f"DEBUG: Initial: Added {len(new_headlines)} headlines to general_misconceptions. Total: {len(feed_cache['general_misconceptions']['headlines'])}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 8: # Generate 3 headlines for issues (add to current 12)
                        print("DEBUG: Initial: Generating 3 more headlines for important_issues.")
                        new_headlines = section_configs["important_issues"]["get_headlines_func"](gemini_key, count=3)
                        feed_cache["important_issues"]["headlines"].extend(new_headlines)
                        print(f"DEBUG: Initial: Added {len(new_headlines)} headlines to important_issues. Total: {len(feed_cache['important_issues']['headlines'])}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 9: # Initial sequence complete, wait 1 minute
                        print("DEBUG: Initial Generation Sequence Complete. Waiting 1 minute.")
                        with worker_state_lock:
                            worker_state["initial_generation_complete"] = True
                            worker_state["last_sequence_execution_time"] = time.time() # Mark time of completion
                            worker_state["current_generation_step"] = 0 # Reset step for next sequence
                        task_processed_in_this_loop = True
                        time.sleep(60) # Wait 1 minute
                        
                if task_processed_in_this_loop:
                    continue # Continue to next loop iteration immediately after a step is processed

            # --- Creation Sequence ---
            # This sequence runs if initial is complete AND full_articles count is not 15 for any section
            # And no refresh is active
            needs_creation_sequence = False
            with cache_lock:
                if initial_complete and not refresh_active:
                    for sec_name in section_configs:
                        if len(feed_cache[sec_name]["full_articles"]) < 15: # Target 15 articles after initial 3
                            needs_creation_sequence = True
                            break
            
            if needs_creation_sequence:
                with worker_state_lock:
                    worker_state["creation_sequence_active"] = True # Activate creation sequence

                print(f"DEBUG: Creation Sequence - Step {current_step}")
                with cache_lock:
                    sec_names = ["latest_news", "general_misconceptions", "important_issues"]
                    
                    # Check if 1 minute has passed since last sequence execution (only for steps after the first)
                    if current_step > 0 and current_time - last_exec_time < 60:
                        remaining_wait = 60 - (current_time - last_exec_time)
                        print(f"DEBUG: Creation: Waiting for {remaining_wait:.2f} seconds for 1-minute interval.")
                        time.sleep(remaining_wait)
                        continue # Re-evaluate after wait

                    # Generate 5 articles per section (2 times)
                    if current_step < 2: # Steps 0, 1 for generating 5 articles per section
                        articles_to_generate = 5
                        for sec_name in sec_names:
                            for _ in range(articles_to_generate):
                                next_headline_index = feed_cache[sec_name]["last_generated_article_index"] + 1
                                if next_headline_index < len(feed_cache[sec_name]["headlines"]):
                                    headline_to_process = feed_cache[sec_name]["headlines"][next_headline_index]
                                    create_func = section_configs[sec_name]["create_article_func"]
                                    # Pass raw_articles_for_source as empty list for news, or gemini_key for others
                                    full_article = create_func(headline_to_process, [] if sec_name == "latest_news" else gemini_key, gemini_key if sec_name == "latest_news" else None)
                                    if full_article:
                                        ARTICLE_CACHE[full_article['id']] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        feed_cache[sec_name]["last_generated_article_index"] = next_headline_index
                                        print(f"DEBUG: Creation: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    time.sleep(API_CALL_DELAY)
                                else:
                                    print(f"WARNING: Creation: Not enough headlines for {sec_name} to generate {articles_to_generate} articles.")
                                    # Don't break, try other sections for this step
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        
                    elif current_step == 2: # Generate 2 articles per section
                        articles_to_generate = 2
                        for sec_name in sec_names:
                            for _ in range(articles_to_generate):
                                next_headline_index = feed_cache[sec_name]["last_generated_article_index"] + 1
                                if next_headline_index < len(feed_cache[sec_name]["headlines"]):
                                    headline_to_process = feed_cache[sec_name]["headlines"][next_headline_index]
                                    create_func = section_configs[sec_name]["create_article_func"]
                                    full_article = create_func(headline_to_process, [] if sec_name == "latest_news" else gemini_key, gemini_key if sec_name == "latest_news" else None)
                                    if full_article:
                                        ARTICLE_CACHE[full_article['id']] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        feed_cache[sec_name]["last_generated_article_index"] = next_headline_index
                                        print(f"DEBUG: Creation: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    time.sleep(API_CALL_DELAY)
                                else:
                                    print(f"WARNING: Creation: Not enough headlines for {sec_name} to generate {articles_to_generate} articles.")
                                    # Don't break, try other sections for this step
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True

                    elif current_step == 3: # Generate 15 headlines per section
                        for sec_name in sec_names:
                            print(f"DEBUG: Creation: Generating 15 headlines for {sec_name}.")
                            get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                            if section_configs[sec_name]["needs_news_key"]:
                                new_headlines = get_headlines_func(gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            else:
                                new_headlines = get_headlines_func(gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            feed_cache[sec_name]["headlines"].extend(new_headlines)
                            print(f"DEBUG: Creation: Added {len(new_headlines)} headlines to {sec_name}. Total: {len(feed_cache[sec_name]['headlines'])}")
                            time.sleep(API_CALL_DELAY)
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True

                    elif current_step == 4: # Creation sequence complete, wait 1 minute
                        print("DEBUG: Creation Sequence Complete. Waiting 1 minute.")
                        with worker_state_lock:
                            worker_state["creation_sequence_active"] = False
                            worker_state["current_generation_step"] = 0 # Reset for next sequence
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        time.sleep(60)
                        
                if task_processed_in_this_loop:
                    continue


            # --- Refresh Sequence ---
            # This sequence runs if user_requested_more is True OR if creation sequence just finished
            needs_refresh_sequence = False
            with worker_state_lock:
                # Trigger refresh if user requested OR if creation sequence just completed
                if user_requested_refresh or (initial_complete and not creation_active and not refresh_active and current_time - last_exec_time >= 60):
                    needs_refresh_sequence = True
                    worker_state["user_requested_more"] = False # Reset flag
                    worker_state["refresh_sequence_active"] = True # Activate refresh sequence
                    worker_state["current_generation_step"] = 0 # Start from step 0 of refresh

            if needs_refresh_sequence:
                print(f"DEBUG: Refresh Sequence - Step {current_step}")
                with cache_lock:
                    sec_names = ["latest_news", "general_misconceptions", "important_issues"]

                    # Check if 1 minute has passed since last sequence execution (only for steps after the first)
                    if current_step > 0 and current_time - last_exec_time < 60:
                        remaining_wait = 60 - (current_time - last_exec_time)
                        print(f"DEBUG: Refresh: Waiting for {remaining_wait:.2f} seconds for 1-minute interval.")
                        time.sleep(remaining_wait)
                        continue # Re-evaluate after wait

                    # Generate 5 articles per section (3 times)
                    if current_step < 3: # Steps 0, 1, 2 for generating 5 articles per section
                        articles_to_generate = 5
                        for sec_name in sec_names:
                            for _ in range(articles_to_generate):
                                next_headline_index = feed_cache[sec_name]["last_generated_article_index"] + 1
                                if next_headline_index < len(feed_cache[sec_name]["headlines"]):
                                    headline_to_process = feed_cache[sec_name]["headlines"][next_headline_index]
                                    create_func = section_configs[sec_name]["create_article_func"]
                                    full_article = create_func(headline_to_process, [] if sec_name == "latest_news" else gemini_key, gemini_key if sec_name == "latest_news" else None)
                                    if full_article:
                                        ARTICLE_CACHE[full_article['id']] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        feed_cache[sec_name]["last_generated_article_index"] = next_headline_index
                                        print(f"DEBUG: Refresh: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    time.sleep(API_CALL_DELAY)
                                else:
                                    print(f"WARNING: Refresh: Not enough headlines for {sec_name} to generate {articles_to_generate} articles.")
                                    # Don't break, try other sections for this step
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        
                    elif current_step == 3: # Generate 15 headlines per section
                        for sec_name in sec_names:
                            print(f"DEBUG: Refresh: Generating 15 headlines for {sec_name}.")
                            get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                            if section_configs[sec_name]["needs_news_key"]:
                                new_headlines = get_headlines_func(gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            else:
                                new_headlines = get_headlines_func(gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            feed_cache[sec_name]["headlines"].extend(new_headlines)
                            print(f"DEBUG: Refresh: Added {len(new_headlines)} headlines to {sec_name}. Total: {len(feed_cache[sec_name]['headlines'])}")
                            time.sleep(API_CALL_DELAY)
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True

                    elif current_step == 4: # Refresh sequence complete, wait for next refresh
                        print("DEBUG: Refresh Sequence Complete. Waiting for next refresh.")
                        with worker_state_lock:
                            worker_state["refresh_sequence_active"] = False
                            worker_state["current_generation_step"] = 0 # Reset for next sequence
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        # The request implies "wait for refresh" means to stop active generation until user clicks refresh.
                        # This will be handled by the outer loop's sleep if no sequence is active.
                        
                if task_processed_in_this_loop:
                    continue

            # If no sequence is active, and initial generation is complete, and no refresh is requested, sleep longer
            with worker_state_lock: # Re-check state after potential sequence completion
                initial_complete = worker_state["initial_generation_complete"]
                creation_active = worker_state["creation_sequence_active"]
                refresh_active = worker_state["refresh_sequence_active"]

            if initial_complete and not creation_active and not refresh_active:
                print("DEBUG: Background: All sequences complete. Sleeping longer, waiting for refresh trigger.")
                time.sleep(30) # Long sleep until a refresh is triggered
                continue

            # Fallback sleep if no task processed in this iteration
            if not task_processed_in_this_loop:
                print("DEBUG: Background: No specific sequence task processed this loop. Sleeping normally.")
                time.sleep(API_CALL_DELAY)

        except Exception as e:
            print(f"CRITICAL ERROR in background generation worker main loop: {e}")
            traceback.print_exc()
            if "429 RESOURCE_EXHAUSTED" in str(e):
                last_429_error_time = time.time()
                print(f"DEBUG: Background: Encountered 429. Initiating backoff for {BACKOFF_DURATION_ON_429} seconds.")
            time.sleep(10) # Short sleep on any error

    print("DEBUG: Background article generation worker stopped.")"""


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
    
    with cache_lock: # Acquire lock for feed_cache read
        response_data = {
            "latest_news": [a for a in feed_cache["latest_news"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION],
            "general_misconceptions": [a for a in feed_cache["general_misconceptions"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION],
            "important_issues": [a for a in feed_cache["important_issues"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION]
        }
        
    # Check if refresh button was clicked and signal the worker
    if request.args.get('refresh') == 'true':
        with worker_state_lock:
            worker_state["user_requested_more"] = True
            print(f"DEBUG: get_feed_articles_api: User requested refresh. Setting user_requested_more=True.")

    # IMPORTANT: Add the initial_generation_complete status to the response
    with worker_state_lock:
        response_data["initial_generation_complete"] = worker_state["initial_generation_complete"]

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
    else:
        print("WARNING: Background generation worker not started due to missing API keys.")

    app.run(debug=True)