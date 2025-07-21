from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from dotenv import load_dotenv, find_dotenv
import uuid
import time
import threading
import collections
import traceback
import requests
import json
import markdown
from news_backend.knowledge_hub_data import knowledge_articles

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
    "latest_news": {"headlines": [], "full_articles": [], "timestamp": 0},
    "general_misconceptions": {"headlines": [], "full_articles": [], "timestamp": 0},
    "important_issues": {"headlines": [], "full_articles": [], "timestamp": 0}
}
cache_lock = threading.Lock() # Protects feed_cache and ARTICLE_CACHE

# Global state for the background worker's sequence
worker_state = {
    "initial_generation_complete": False,
    "creation_sequence_active": False,
    "refresh_sequence_active": False,
    "current_generation_step": 0,
    "last_sequence_execution_time": 0,
    "user_requested_more": False
}
worker_state_lock = threading.Lock() # Protects worker_state

MAX_HEADLINES_TO_GENERATE_AT_ONCE = 15
MAX_ARTICLES_PER_SECTION = 15 # Target max articles to generate/store per section
INITIAL_DISPLAY_ARTICLES = 3 # Initial articles to display on feed load (from the first 3 generated)

stop_background_thread = threading.Event()
background_thread = None

section_configs = {
    "latest_news": {
        "get_headlines_func": get_news_headlines,
        "create_article_func": create_full_news_article,
        "headlines_topic": "current events",
        "initial_articles_target": 3,
        "needs_news_key": True
    },
    "general_misconceptions": {
        "get_headlines_func": get_misconception_headlines,
        "create_article_func": create_full_misconception_article,
        "headlines_topic": "common myths",
        "initial_articles_target": 3,
        "needs_news_key": False
    },
    "important_issues": {
        "get_headlines_func": get_issue_headlines,
        "create_article_func": create_full_issue_article,
        "headlines_topic": "global challenges",
        "initial_articles_target": 3,
        "needs_news_key": False
    }
}

# Global variable to track 429 errors and implement backoff
last_429_error_time = 0
BACKOFF_DURATION_ON_429 = 300 # 5 minutes in seconds, can be increased if needed

# Define CATEGORY_COLORS to match frontend (for article_detail.html)
CATEGORY_COLORS = {
    'health': {'bg': '#e8f5e9', 'text': '#2e7d32'},
    'environment': {'bg': '#e3f2fd', 'text': '#1565c0'},
    'science': {'bg': '#ffe0b2', 'text': '#e65100'},
    'technology': {'bg': '#ede7f6', 'text': '#673ab7'},
    'business': {'bg': '#fffde7', 'text': '#fbc02d'},
    'politics': {'bg': '#ffebee', 'text': '#c62828'},
    'society': {'bg': '#eeeeee', 'text': '#616161'},
    'education': {'bg': '#e0f2f7', 'text': '#006064'},
    'general': {'bg': '#f0f0f0', 'text': '#424242'},
    'events': {'bg': '#fde0dc', 'text': '#d32f2f'}
}
DEFAULT_CATEGORY_COLOR = CATEGORY_COLORS['general'] # Fallback if category not found

def background_article_generation_worker(gemini_key, news_key):
    """
    Worker thread to generate and update articles in the cache.
    It performs initial generation and then continuous updates.
    """
    global last_429_error_time
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
                with cache_lock:
                    
                    if current_step == 0: # Generate 15 headlines for news
                        print("DEBUG: Initial: Generating 15 headlines for latest_news.")
                        new_headlines_response = section_configs["latest_news"]["get_headlines_func"](gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                        if isinstance(new_headlines_response, list):
                            feed_cache["latest_news"]["headlines"].extend(new_headlines_response)
                            print(f"DEBUG: Initial: Added {len(new_headlines_response)} headlines to latest_news. Total: {len(feed_cache['latest_news']['headlines'])}")
                        else:
                            print(f"ERROR: Initial: Failed to get headlines for latest_news: {new_headlines_response.get('error', 'Unknown error')}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 1: # Generate 3 articles for news
                        print("DEBUG: Initial: Generating 3 articles for latest_news.")
                        for _ in range(3):
                            if feed_cache["latest_news"]["headlines"]:
                                headline_to_process = feed_cache["latest_news"]["headlines"].pop(0)
                                full_article = section_configs["latest_news"]["create_article_func"](headline_to_process, [], gemini_key)
                                if full_article:
                                    category_key = full_article.get('category', 'General').lower().replace(' ', '-')
                                    full_article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
                                    ARTICLE_CACHE[full_article['id']] = full_article
                                    feed_cache["latest_news"]["full_articles"].append(full_article)
                                    feed_cache["latest_news"]["timestamp"] = time.time()
                                    print(f"DEBUG: Initial: Added full article to latest_news. Total: {len(feed_cache['latest_news']['full_articles'])}")
                                time.sleep(API_CALL_DELAY)
                            else:
                                print("WARNING: Initial: Not enough headlines for latest_news to generate 3 articles.")
                                break
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True

                    elif current_step == 2: # Generate 15 headlines for misconceptions
                        print("DEBUG: Initial: Generating 15 headlines for general_misconceptions.")
                        new_headlines_response = section_configs["general_misconceptions"]["get_headlines_func"](gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                        if isinstance(new_headlines_response, list):
                            feed_cache["general_misconceptions"]["headlines"].extend(new_headlines_response)
                            print(f"DEBUG: Initial: Added {len(new_headlines_response)} headlines to general_misconceptions. Total: {len(feed_cache['general_misconceptions']['headlines'])}")
                        else:
                            print(f"ERROR: Initial: Failed to get headlines for general_misconceptions: {new_headlines_response.get('error', 'Unknown error')}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 3: # Generate 3 articles for misconceptions
                        print("DEBUG: Initial: Generating 3 articles for general_misconceptions.")
                        for _ in range(3):
                            if feed_cache["general_misconceptions"]["headlines"]:
                                headline_to_process = feed_cache["general_misconceptions"]["headlines"].pop(0)
                                full_article = section_configs["general_misconceptions"]["create_article_func"](headline_to_process, gemini_key)
                                if full_article:
                                    category_key = full_article.get('category', 'General').lower().replace(' ', '-')
                                    full_article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
                                    ARTICLE_CACHE[full_article['id']] = full_article
                                    feed_cache["general_misconceptions"]["full_articles"].append(full_article)
                                    feed_cache["general_misconceptions"]["timestamp"] = time.time()
                                    print(f"DEBUG: Initial: Added full article to general_misconceptions. Total: {len(feed_cache['general_misconceptions']['full_articles'])}")
                                time.sleep(API_CALL_DELAY)
                            else:
                                print("WARNING: Initial: Not enough headlines for general_misconceptions to generate 3 articles.")
                                break
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True

                    elif current_step == 4: # Generate 15 headlines for issues
                        print("DEBUG: Initial: Generating 15 headlines for important_issues.")
                        new_headlines_response = section_configs["important_issues"]["get_headlines_func"](gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                        if isinstance(new_headlines_response, list):
                            feed_cache["important_issues"]["headlines"].extend(new_headlines_response)
                            print(f"DEBUG: Initial: Added {len(new_headlines_response)} headlines to important_issues. Total: {len(feed_cache['important_issues']['headlines'])}")
                        else:
                            print(f"ERROR: Initial: Failed to get headlines for important_issues: {new_headlines_response.get('error', 'Unknown error')}")
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True
                        time.sleep(API_CALL_DELAY)
                        
                    elif current_step == 5: # Generate 3 articles for issues
                        print("DEBUG: Initial: Generating 3 articles for important_issues.")
                        for _ in range(3):
                            if feed_cache["important_issues"]["headlines"]:
                                headline_to_process = feed_cache["important_issues"]["headlines"].pop(0)
                                full_article = section_configs["important_issues"]["create_article_func"](headline_to_process, gemini_key)
                                if full_article:
                                    category_key = full_article.get('category', 'General').lower().replace(' ', '-')
                                    full_article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
                                    ARTICLE_CACHE[full_article['id']] = full_article
                                    feed_cache["important_issues"]["full_articles"].append(full_article)
                                    feed_cache["important_issues"]["timestamp"] = time.time()
                                    print(f"DEBUG: Initial: Added full article to important_issues. Total: {len(feed_cache['important_issues']['full_articles'])}")
                                time.sleep(API_CALL_DELAY)
                            else:
                                print("WARNING: Initial: Not enough headlines for important_issues to generate 3 articles.")
                                break
                        with worker_state_lock: worker_state["current_generation_step"] += 1
                        task_processed_in_this_loop = True

                    elif current_step == 6: # Check if initial generation is complete and set flag
                        all_sections_met_initial_target = True
                        for section in section_configs:
                            if len(feed_cache[section]["full_articles"]) < section_configs[section]["initial_articles_target"]:
                                all_sections_met_initial_target = False
                                break
                        
                        with worker_state_lock:
                            worker_state["initial_generation_complete"] = all_sections_met_initial_target
                            if all_sections_met_initial_target:
                                print("DEBUG: All initial article generation complete. Resetting step and transitioning.")
                                worker_state["current_generation_step"] = 0
                            else:
                                print("DEBUG: Initial generation not yet complete. Looping back to step 0.")
                                worker_state["current_generation_step"] = 0
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        time.sleep(5)

                if task_processed_in_this_loop:
                    continue


            # --- Creation Sequence ---
            needs_creation_sequence = False
            with cache_lock:
                if initial_complete and not refresh_active:
                    for sec_name in section_configs:
                        if len(feed_cache[sec_name]["full_articles"]) < MAX_ARTICLES_PER_SECTION:
                            needs_creation_sequence = True
                            break
            
            if needs_creation_sequence:
                with worker_state_lock:
                    worker_state["creation_sequence_active"] = True

                print(f"DEBUG: Creation Sequence - Step {current_step}")
                with cache_lock:
                    if current_step > 0 and current_time - last_exec_time < 60:
                        remaining_wait = 60 - (current_time - last_exec_time)
                        print(f"DEBUG: Creation: Waiting for {remaining_wait:.2f} seconds for 1-minute interval.")
                        time.sleep(remaining_wait)
                        continue

                    if current_step < 2:
                        articles_to_generate = 5
                        for sec_name in section_configs:
                            for _ in range(articles_to_generate):
                                if len(feed_cache[sec_name]["full_articles"]) >= MAX_ARTICLES_PER_SECTION:
                                    print(f"DEBUG: Creation: {sec_name} already has MAX_ARTICLES_PER_SECTION. Skipping.")
                                    continue

                                if feed_cache[sec_name]["headlines"]:
                                    headline_to_process = feed_cache[sec_name]["headlines"].pop(0)
                                    create_func = section_configs[sec_name]["create_article_func"]
                                    if sec_name == "latest_news":
                                        full_article = create_func(headline_to_process, [], gemini_key)
                                    else:
                                        full_article = create_func(headline_to_process, gemini_key)

                                    if full_article:
                                        category_key = full_article.get('category', 'General').lower().replace(' ', '-')
                                        full_article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
                                        ARTICLE_CACHE[full_article['id']] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        print(f"DEBUG: Creation: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    time.sleep(API_CALL_DELAY)
                                else:
                                    print(f"WARNING: Creation: Not enough headlines for {sec_name} to generate {articles_to_generate} articles. Re-fetching headlines...")
                                    get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                                    if section_configs[sec_name]["needs_news_key"]:
                                        new_headlines_response = get_headlines_func(gemini_key, news_key, count=5)
                                    else:
                                        new_headlines_response = get_headlines_func(gemini_key, count=5)
                                    if isinstance(new_headlines_response, list):
                                        feed_cache[sec_name]["headlines"].extend(new_headlines_response)
                                        print(f"DEBUG: Creation: Added {len(new_headlines_response)} new headlines for {sec_name}.")
                                    else:
                                        print(f"ERROR: Creation: Failed to fetch more headlines for {sec_name}: {new_headlines_response.get('error', 'Unknown error')}")
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        
                    elif current_step == 2:
                        articles_to_generate = 2
                        for sec_name in section_configs:
                            for _ in range(articles_to_generate):
                                if len(feed_cache[sec_name]["full_articles"]) >= MAX_ARTICLES_PER_SECTION:
                                    print(f"DEBUG: Creation: {sec_name} already has MAX_ARTICLES_PER_SECTION. Skipping.")
                                    continue

                                if feed_cache[sec_name]["headlines"]:
                                    headline_to_process = feed_cache[sec_name]["headlines"].pop(0)
                                    create_func = section_configs[sec_name]["create_article_func"]
                                    if sec_name == "latest_news":
                                        full_article = create_func(headline_to_process, [], gemini_key)
                                    else:
                                        full_article = create_func(headline_to_process, gemini_key)

                                    if full_article:
                                        category_key = full_article.get('category', 'General').lower().replace(' ', '-')
                                        full_article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
                                        ARTICLE_CACHE[full_article['id']] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        print(f"DEBUG: Creation: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    time.sleep(API_CALL_DELAY)
                                else:
                                    print(f"WARNING: Creation: Not enough headlines for {sec_name} to generate {articles_to_generate} articles. Re-fetching headlines...")
                                    get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                                    if section_configs[sec_name]["needs_news_key"]:
                                        new_headlines_response = get_headlines_func(gemini_key, news_key, count=5)
                                    else:
                                        new_headlines_response = get_headlines_func(gemini_key, count=5)
                                    if isinstance(new_headlines_response, list):
                                        feed_cache[sec_name]["headlines"].extend(new_headlines_response)
                                        print(f"DEBUG: Creation: Added {len(new_headlines_response)} new headlines for {sec_name}.")
                                    else:
                                        print(f"ERROR: Creation: Failed to fetch more headlines for {sec_name}: {new_headlines_response.get('error', 'Unknown error')}")
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True

                    elif current_step == 3:
                        for sec_name in section_configs:
                            print(f"DEBUG: Creation: Generating 15 headlines for {sec_name}.")
                            get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                            if section_configs[sec_name]["needs_news_key"]:
                                new_headlines_response = get_headlines_func(gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            else:
                                new_headlines_response = get_headlines_func(gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            if isinstance(new_headlines_response, list):
                                feed_cache[sec_name]["headlines"].extend(new_headlines_response)
                                print(f"DEBUG: Creation: Added {len(new_headlines_response)} headlines to {sec_name}. Total: {len(feed_cache[sec_name]['headlines'])}")
                            else:
                                print(f"ERROR: Creation: Failed to get headlines for {sec_name}: {new_headlines_response.get('error', 'Unknown error')}")
                            time.sleep(API_CALL_DELAY)
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True

                    elif current_step == 4:
                        print("DEBUG: Creation Sequence Complete. Waiting 1 minute.")
                        with worker_state_lock:
                            worker_state["creation_sequence_active"] = False
                            worker_state["current_generation_step"] = 0
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        time.sleep(60)
                        
                if task_processed_in_this_loop:
                    continue


            # --- Refresh Sequence ---
            needs_refresh_sequence = False
            with worker_state_lock:
                if user_requested_refresh or (initial_complete and not creation_active and not refresh_active and current_time - last_exec_time >= 60):
                    needs_refresh_sequence = True
                    worker_state["user_requested_more"] = False
                    worker_state["refresh_sequence_active"] = True
                    worker_state["current_generation_step"] = 0

            if needs_refresh_sequence:
                print(f"DEBUG: Refresh Sequence - Step {current_step}")
                with cache_lock:
                    if current_step > 0 and current_time - last_exec_time < 60:
                        remaining_wait = 60 - (current_time - last_exec_time)
                        print(f"DEBUG: Refresh: Waiting for {remaining_wait:.2f} seconds for 1-minute interval.")
                        time.sleep(remaining_wait)
                        continue

                    if current_step < 3:
                        articles_to_generate = 5
                        for sec_name in section_configs:
                            for _ in range(articles_to_generate):
                                if len(feed_cache[sec_name]["full_articles"]) >= MAX_ARTICLES_PER_SECTION:
                                    print(f"DEBUG: Refresh: {sec_name} already has MAX_ARTICLES_PER_SECTION. Skipping.")
                                    continue

                                if feed_cache[sec_name]["headlines"]:
                                    headline_to_process = feed_cache[sec_name]["headlines"].pop(0)
                                    create_func = section_configs[sec_name]["create_article_func"]
                                    if sec_name == "latest_news":
                                        full_article = create_func(headline_to_process, [], gemini_key)
                                    else:
                                        full_article = create_func(headline_to_process, gemini_key)

                                    if full_article:
                                        category_key = full_article.get('category', 'General').lower().replace(' ', '-')
                                        full_article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
                                        ARTICLE_CACHE[full_article['id']] = full_article
                                        feed_cache[sec_name]["full_articles"].append(full_article)
                                        feed_cache[sec_name]["timestamp"] = time.time()
                                        print(f"DEBUG: Refresh: Added full article to {sec_name}. Total: {len(feed_cache[sec_name]['full_articles'])}")
                                    time.sleep(API_CALL_DELAY)
                                else:
                                    print(f"WARNING: Refresh: Not enough headlines for {sec_name} to generate {articles_to_generate} articles. Re-fetching headlines...")
                                    get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                                    if section_configs[sec_name]["needs_news_key"]:
                                        new_headlines_response = get_headlines_func(gemini_key, news_key, count=5)
                                    else:
                                        new_headlines_response = get_headlines_func(gemini_key, count=5)
                                    if isinstance(new_headlines_response, list):
                                        feed_cache[sec_name]["headlines"].extend(new_headlines_response)
                                        print(f"DEBUG: Refresh: Added {len(new_headlines_response)} new headlines for {sec_name}.")
                                    else:
                                        print(f"ERROR: Refresh: Failed to fetch more headlines for {sec_name}: {new_headlines_response.get('error', 'Unknown error')}")
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        
                    elif current_step == 3:
                        for sec_name in section_configs:
                            print(f"DEBUG: Refresh: Generating 15 headlines for {sec_name}.")
                            get_headlines_func = section_configs[sec_name]["get_headlines_func"]
                            if section_configs[sec_name]["needs_news_key"]:
                                new_headlines_response = get_headlines_func(gemini_key, news_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            else:
                                new_headlines_response = get_headlines_func(gemini_key, count=MAX_HEADLINES_TO_GENERATE_AT_ONCE)
                            if isinstance(new_headlines_response, list):
                                feed_cache[sec_name]["headlines"].extend(new_headlines_response)
                                print(f"DEBUG: Refresh: Added {len(new_headlines_response)} headlines to {sec_name}. Total: {len(feed_cache[sec_name]['headlines'])}")
                            else:
                                print(f"ERROR: Refresh: Failed to get headlines for {sec_name}: {new_headlines_response.get('error', 'Unknown error')}")
                            time.sleep(API_CALL_DELAY)
                        with worker_state_lock:
                            worker_state["current_generation_step"] += 1
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True

                    elif current_step == 4:
                        print("DEBUG: Refresh Sequence Complete. Waiting for next refresh.")
                        with worker_state_lock:
                            worker_state["refresh_sequence_active"] = False
                            worker_state["current_generation_step"] = 0
                            worker_state["last_sequence_execution_time"] = time.time()
                        task_processed_in_this_loop = True
                        
                if task_processed_in_this_loop:
                    continue

            with worker_state_lock:
                initial_complete = worker_state["initial_generation_complete"]
                creation_active = worker_state["creation_sequence_active"]
                refresh_active = worker_state["refresh_sequence_active"]

            if initial_complete and not creation_active and not refresh_active:
                print("DEBUG: Background: All sequences complete. Sleeping longer, waiting for refresh trigger.")
                time.sleep(30)
                continue

            if not task_processed_in_this_loop:
                print("DEBUG: Background: No specific sequence task processed this loop. Sleeping normally.")
                time.sleep(API_CALL_DELAY)

        except Exception as e:
            print(f"CRITICAL ERROR in background generation worker main loop: {e}")
            traceback.print_exc()
            if "429 RESOURCE_EXHAUSTED" in str(e):
                last_429_error_time = time.time()
                print(f"DEBUG: Background: Encountered 429. Initiating backoff for {BACKOFF_DURATION_ON_429} seconds.")
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
    return render_template('learn.html')

# --- New Route for Full Article Display ---
@app.route('/article/<article_id>')
def article_detail(article_id):
    article = ARTICLE_CACHE.get(article_id)
    if not article:
        return render_template('error.html', message="Article not found or has expired."), 404
    
    # Add category_color to the article before passing to template
    category_key = article.get('category', 'General').lower().replace(' ', '-')
    article['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)
    
    # MODIFIED: Determine back link and text based on referrer
    referrer = request.referrer
    if referrer and '/search' in referrer:
        back_link = url_for('search')
        back_text = "Search"
    else:
        back_link = url_for('feed')
        back_text = "Feed"

    return render_template('article_detail.html', article=article, back_link=back_link, back_text=back_text)

@app.route('/learn/<path:article_id>')
def learn_article_detail(article_id):
    article_data = None
    for unit_name, unit_info in knowledge_articles.items():
        if article_id in unit_info["lessons"]:
            article_data = unit_info["lessons"][article_id]
            break
    if not article_data:
        return "Article not found", 404
    return render_template('learn_article_detail.html', article=article_data)
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
        return jsonify({"error": "API keys not provided or configured. Please enter them in your profile settings.", "code": 401}), 401

    with cache_lock:
        response_data = {
            "latest_news": [a for a in feed_cache["latest_news"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION],
            "general_misconceptions": [a for a in feed_cache["general_misconceptions"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION],
            "important_issues": [a for a in feed_cache["important_issues"]["full_articles"] if a is not None][:MAX_ARTICLES_PER_SECTION]
        }
        
    if request.args.get('refresh') == 'true':
        with worker_state_lock:
            worker_state["user_requested_more"] = True
            print(f"DEBUG: get_feed_articles_api: User requested refresh. Setting user_requested_more=True.")

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

        if detailed_article_result:
            category_key = detailed_article_result.get('category', 'General').lower().replace(' ', '-')
            detailed_article_result['category_color'] = CATEGORY_COLORS.get(category_key, DEFAULT_CATEGORY_COLOR)

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

    app.run(debug=True, use_reloader=False)
