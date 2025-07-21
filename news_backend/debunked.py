import requests
from typing import NamedTuple
import json
import os
from dotenv import load_dotenv
import datetime
import re
import time
import traceback
import collections # Import collections for deque
import threading # Import threading for lock
import uuid # Import the uuid module

# --- Environment Variables & API Clients ---
load_dotenv()

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
NEWSAPI_API_KEY = os.environ.get('NEWSAPI_API_KEY')

API_CALL_DELAY = 6

RATE_LIMIT_MAX_CALLS_PER_MINUTE = 15
RATE_LIMIT_INTERVAL_SECONDS = 60
api_call_timestamps = collections.deque()
api_call_lock = threading.Lock()

# --- Allowed Categories for AI Classification ---
ALLOWED_ARTICLE_CATEGORIES = [
    "Events", "Environment", "Politics", "Health", "Science",
    "Technology", "Business", "Society", "Education", "General"
]

ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES = [
    "Science", "Health", "Environment", "Society", "Technology", "Politics", "Economics", "Education"
]

# --- NamedTuple for NewsAPI Articles ---
class Article(NamedTuple):
    url: str
    title: str

# --- Rate Limiting Function ---
def enforce_rate_limit():
    global api_call_timestamps
    with api_call_lock:
        while api_call_timestamps and api_call_timestamps[0] < time.time() - RATE_LIMIT_INTERVAL_SECONDS:
            api_call_timestamps.popleft()

        if len(api_call_timestamps) >= RATE_LIMIT_MAX_CALLS_PER_MINUTE:
            time_to_wait = api_call_timestamps[0] + RATE_LIMIT_INTERVAL_SECONDS - time.time()
            if time_to_wait > 0:
                print(f"DEBUG: Rate limit hit. Waiting for {time_to_wait:.2f} seconds before next API call.")
                time.sleep(time_to_wait)
                while api_call_timestamps and api_call_timestamps[0] < time.time() - RATE_LIMIT_INTERVAL_SECONDS:
                    api_call_timestamps.popleft()
        
        api_call_timestamps.append(time.time())

# --- Helper Functions for LLM Interaction (Revised for JSON Schema) ---
def call_gemini_api_with_json_schema(prompt_text, response_schema, gem_api_key):
    api_key = gem_api_key
    if not api_key:
        print("ERROR: Gemini API key is missing for LLM call.")
        return {"error": "Gemini API key is missing."}

    headers = {'Content-Type': 'application/json'}
    params = {'key': api_key}
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt_text}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }

    enforce_rate_limit()
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()

        if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            try:
                # The LLM's structured output is a JSON string inside parts[0]["text"].
                # We need to parse that inner string.
                parsed_json_output = json.loads(result["candidates"][0]["content"]["parts"][0]["text"])
                return parsed_json_output
            except json.JSONDecodeError as e:
                print(f"JSON decode error for LLM structured output: {e} - Raw text: {result['candidates'][0]['content']['parts'][0]['text']}")
                return {"error": f"LLM returned malformed JSON: {e}"}
        else:
            print(f"WARNING: Gemini API response missing content or candidates: {result}")
            return {"error": "Gemini API response missing content."}

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred during Gemini API call: {http_err} - Response text: {response.text}")
        return {"error": f"HTTP error: {http_err}. Response: {response.text}"}
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred during Gemini API call: {conn_err}")
        return {"error": f"Connection error: {conn_err}"}
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred during Gemini API call: {timeout_err}")
        return {"error": f"Timeout error: {timeout_err}"}
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected request error occurred during Gemini API call: {req_err}")
        return {"error": f"Request error: {req_err}"}
    except Exception as e:
        print(f"An unexpected error occurred in call_gemini_api_with_json_schema: {e}")
        return {"error": f"An unexpected error: {e}"}

# --- Headline Generation Functions ---
def get_news_headlines(gem_api_key, news_api_key, count=12):
    current_newsapi_key = news_api_key
    if not current_newsapi_key:
        print("ERROR: NewsAPI key is missing for headline fetching.")
        return {"error": "NewsAPI key is missing."}

    url = ('https://newsapi.org/v2/top-headlines?'
           'country=us&'
           f'apiKey={current_newsapi_key}')

    enforce_rate_limit()
    try:
        response_url = requests.get(url, timeout=10)
        response_url.raise_for_status()
        rsp_json = response_url.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching raw news articles for headlines: {e}")
        traceback.print_exc()
        return {"error": f"Error fetching news headlines: {e}"}

    articles_raw_data = []
    if rsp_json['totalResults'] == 0:
        return []
    else:
        for article in rsp_json['articles']:
            if article.get('url') and article.get('title'):
                articles_raw_data.append(Article(url=article['url'], title=article['title']))
            if len(articles_raw_data) >= count * 3:
                break

    if not articles_raw_data:
        return []

    source_urls_for_gemini = "\n".join([article.url for article in articles_raw_data])

    headlines_prompt = (
        f"From the following sources, generate a list of exactly {count} distinct and concise news headlines. "
        f"Ensure each headline is unique and directly reflects content from the sources. "
        f"Only provide the headlines, separated by commas, with no introductory or concluding remarks. "
        f"Format: [headline1], [headline2], [headline3], ...\n\n"
        f"Sources:\n{source_urls_for_gemini}"
    )
    
    enforce_rate_limit()
    try:
        response_gemini_headlines = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={'Content-Type': 'application/json'},
            params={'key': gem_api_key},
            json={"contents": [{"role": "user", "parts": [{"text": headlines_prompt}]}]},
            timeout=60
        )
        response_gemini_headlines.raise_for_status()
        result = response_gemini_headlines.json()
        
        if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            headlines = [h.strip() for h in result["candidates"][0]["content"]["parts"][0]["text"].split(", ") if h.strip()]
            headlines = list(collections.OrderedDict.fromkeys(headlines))
            headlines = headlines[:count]
            print(f"DEBUG: Generated {len(headlines)} headlines: {headlines}")
            return headlines
        else:
            print(f"WARNING: Gemini API response missing content for headlines: {result}")
            return {"error": "Gemini API response missing content for headlines."}

    except requests.exceptions.RequestException as e:
        print(f"Error generating news headlines: {e}")
        traceback.print_exc()
        return {"error": f"Error generating news headlines: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred in get_news_headlines: {e}")
        return {"error": f"An unexpected error: {e}"}

def get_misconception_headlines(gem_api_key, count=12):
    misconception_titles_prompt = (
        f"Generate exactly {count} distinct and common misconceptions. "
        f"Each should be phrased as a factual statement debunking the misconception (e.g., 'Vaccines do NOT cause Autism', 'Flat Earth is NOT real'). "
        f"Only provide the statements, separated by commas, with no other text. "
        f"Format: [misconception1], [misconception2], ...\n"
    )
    enforce_rate_limit()
    try:
        response_gemini_misconception = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={'Content-Type': 'application/json'},
            params={'key': gem_api_key},
            json={"contents": [{"role": "user", "parts": [{"text": misconception_titles_prompt}]}]},
            timeout=60
        )
        response_gemini_misconception.raise_for_status()
        result = response_gemini_misconception.json()

        if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            misconceptions_titles = [m.strip() for m in result["candidates"][0]["content"]["parts"][0]["text"].split(", ") if m.strip()]
            misconceptions_titles = list(collections.OrderedDict.fromkeys(misconceptions_titles))
            misconceptions_titles = misconceptions_titles[:count]
            print(f"DEBUG: Generated {len(misconceptions_titles)} misconception headlines: {misconceptions_titles}")
            return misconceptions_titles
        else:
            print(f"WARNING: Gemini API response missing content for misconception headlines: {result}")
            return {"error": "Gemini API response missing content for misconception headlines."}
    except requests.exceptions.RequestException as e:
        print(f"Error generating misconception headlines: {e}")
        traceback.print_exc()
        return {"error": f"Error generating misconception headlines: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred in get_misconception_headlines: {e}")
        return {"error": f"An unexpected error: {e}"}

def get_issue_headlines(gem_api_key, count=12):
    issue_titles_prompt = (
        f"Generate exactly {count} distinct and important global issues that warrant more attention and have significant world impact. "
        f"Only provide the issue titles, separated by commas, with no other text. "
        f"Format: [issue1], [issue2], ...\n"
    )
    enforce_rate_limit()
    try:
        response_gemini_issue = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={'Content-Type': 'application/json'},
            params={'key': gem_api_key},
            json={"contents": [{"role": "user", "parts": [{"text": issue_titles_prompt}]}]},
            timeout=60
        )
        response_gemini_issue.raise_for_status()
        result = response_gemini_issue.json()

        if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            issue_titles = [i.strip() for i in result["candidates"][0]["content"]["parts"][0]["text"].split(", ") if i.strip()]
            issue_titles = list(collections.OrderedDict.fromkeys(issue_titles))
            issue_titles = issue_titles[:count]
            print(f"DEBUG: Generated {len(issue_titles)} issue headlines: {issue_titles}")
            return issue_titles
        else:
            print(f"WARNING: Gemini API response missing content for issue headlines: {result}")
            return {"error": "Gemini API response missing content for issue headlines."}
    except requests.exceptions.RequestException as e:
        print(f"Error generating issue headlines: {e}")
        traceback.print_exc()
        return {"error": f"Error generating issue headlines: {e}"}
    except Exception as e:
        print(f"An unexpected error occurred in get_issue_headlines: {e}")
        return {"error": f"An unexpected error: {e}"}

# --- Full Article Creation Functions (now extract full_content fields) ---
def create_full_news_article(headline, raw_articles_for_source, gem_api_key):
    source_urls_for_gemini = "\n".join([article.url for article in raw_articles_for_source]) if raw_articles_for_source else "No specific sources provided."

    prompt_text = (
        f"Create a detailed, in-depth news story based strictly on the information found at the following URLs, focusing on the headline '{headline}'. "
        f"If no specific sources are provided, generate a plausible, well-researched news story for the headline. "
        f"Classify this news article into ONE of the following categories: {', '.join(ALLOWED_ARTICLE_CATEGORIES)}. "
        f"DO NOT refer to yourself as an AI model. DO NOT use any Markdown formatting like italics, bolding, or headings within the generated text content. "
        f"The 'title' should be a concise and engaging article title, not just the headline. "
        f"The 'summary' should be a brief, one-sentence overview. "
        f"The 'summary_detail' should be a comprehensive, multi-paragraph explanation of the news story. Ensure it is at least 3 distinct paragraphs, with each paragraph separated by two newline characters (\\n\\n) to ensure proper visual separation, and provides thorough detail. "
        f"The 'key_findings' should be a list of crucial facts, each as a separate string item. Each item must contain actual text, not just an empty string. "
        f"The 'viewpoints' should provide at least 2-3 distinct perspectives or contrasting opinions on the topic, each as a separate string item. Each item must contain actual text, not just an empty string or a colon. "
        f"The 'verified_sources' should be a list of objects, each with a 'name' (string) and 'url' (string) for the sources used. Each source must have a valid name and URL. If no specific sources are available, provide plausible, general sources like 'News Agency' with a placeholder URL like 'https://example.com/news'."
        f"Provide the output in JSON format with the following structure:"
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"},
            "summary": {"type": "STRING"},
            "category": {
                "type": "STRING",
                "enum": ALLOWED_ARTICLE_CATEGORIES
            },
            "full_content": {
                "type": "OBJECT",
                "properties": {
                    "summary_detail": {"type": "STRING"},
                    "key_findings": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "viewpoints": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "verified_sources": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "url": {"type": "STRING"}}}}
                }
            }
        },
        "required": ["title", "summary", "category", "full_content"]
    }

    print(f"DEBUG: Generating full news article for '{headline}' with AI classification and detailed content.")
    generated_data = call_gemini_api_with_json_schema(prompt_text, response_schema, gem_api_key)

    if generated_data and not generated_data.get("error"):
        title = generated_data.get("title", headline)
        summary = generated_data.get("summary", "")
        category = generated_data.get("category", "General")
        full_content = generated_data.get("full_content", {})
        
        # Ensure full_content has all expected keys, even if empty from AI
        summary_detail = full_content.get("summary_detail", "")
        key_findings = full_content.get("key_findings", [])
        viewpoints = full_content.get("viewpoints", [])
        verified_sources = full_content.get("verified_sources", [])

        # Generate unique ID and image URL
        article_id = f"debunkd-news-{uuid.uuid4()}"
        image_url = f"https://placehold.co/300x200/007bff/FFFFFF?text={category.replace(' ', '+')}"

        article_obj = {
            "id": article_id,
            "title": title,
            "summary": summary,
            "category": category,
            "image_url": image_url,
            "original_url": source_urls_for_gemini.split('\n')[0] if raw_articles_for_source else "",
            "summary_detail": summary_detail,
            "key_insights": key_findings,
            "viewpoints": viewpoints,
            "sources": verified_sources
        }
        print(f"DEBUG: Generated News Article: Title='{article_obj['title']}', Category='{article_obj['category']}'")
        return article_obj
    else:
        print(f"Error generating full news article for '{headline}': {generated_data.get('error', 'Unknown error')}")
        return None

def create_full_misconception_article(misconception_title, gem_api_key):
    prompt_text = (
        f"For the misconception '{misconception_title}', write a detailed article debunking it. "
        f"Classify the core topic of this misconception into ONE of the following categories: {', '.join(ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES)}. "
        f"DO NOT refer to yourself as an AI model. DO NOT use any Markdown formatting like italics, bolding, or headings within the generated text content. "
        f"The 'title' should be a concise and engaging article title, not just the misconception title. "
        f"The 'summary' should be a brief, one-sentence overview. "
        f"The 'summary_detail' should be a comprehensive, multi-paragraph explanation of the debunking. Ensure it is at least 3 distinct paragraphs, with each paragraph separated by two newline characters (\\n\\n) to ensure proper visual separation, and provides thorough detail. "
        f"The 'key_findings' should be a list of crucial facts, each as a separate string item. Each item must contain actual text, not just an empty string. "
        f"The 'viewpoints' should provide at least 2-3 distinct common arguments for and against the misconception, or contrasting interpretations of the evidence, each as a separate string item. Each item must contain actual text, not just an empty string or a colon. "
        f"The 'verified_sources' should be a list of objects, each with a 'name' (string) and 'url' (string) for the sources used. Each source must have a valid name and URL. If no specific sources are available, provide plausible, general sources like 'Fact-Check Org' with a placeholder URL like 'https://example.com/factcheck'."
        f"Provide the output in JSON format with the following structure:"
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"},
            "summary": {"type": "STRING"},
            "category": {
                "type": "STRING",
                "enum": ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES
            },
            "full_content": {
                "type": "OBJECT",
                "properties": {
                    "summary_detail": {"type": "STRING"},
                    "key_findings": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "viewpoints": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "verified_sources": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "url": {"type": "STRING"}}}}
                }
            }
        },
        "required": ["title", "summary", "category", "full_content"]
    }

    print(f"DEBUG: Generating full misconception article for '{misconception_title}' with AI classification and detailed content.")
    generated_data = call_gemini_api_with_json_schema(prompt_text, response_schema, gem_api_key)

    if generated_data and not generated_data.get("error"):
        title = generated_data.get("title", misconception_title)
        summary = generated_data.get("summary", "")
        category = generated_data.get("category", "General")
        full_content = generated_data.get("full_content", {})

        summary_detail = full_content.get("summary_detail", "")
        key_findings = full_content.get("key_findings", [])
        viewpoints = full_content.get("viewpoints", [])
        verified_sources = full_content.get("verified_sources", [])

        article_id = f"debunkd-misconception-{uuid.uuid4()}"
        clean_category_for_image = category.replace(' ', '+')
        image_url = f"https://placehold.co/300x200/FF8C00/FFFFFF?text={clean_category_for_image}"

        article_obj = {
            "id": article_id,
            "title": title,
            "summary": summary,
            "category": category,
            "image_url": image_url,
            "original_url": "",
            "summary_detail": summary_detail,
            "key_insights": key_findings,
            "viewpoints": viewpoints,
            "sources": verified_sources
        }
        print(f"DEBUG: Generated Misconception Article: Title='{article_obj['title']}', Category='{article_obj['category']}'")
        return article_obj
    else:
        print(f"Error generating full misconception article for '{misconception_title}': {generated_data.get('error', 'Unknown error')}")
        return None

def create_full_issue_article(issue_title, gem_api_key):
    prompt_text = (
        f"For the important issue '{issue_title}', write a detailed overview. "
        f"Classify the core topic of this issue into ONE of the following categories: {', '.join(ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES)}. "
        f"DO NOT refer to yourself as an AI model. DO NOT use any Markdown formatting like italics, bolding, or headings within the generated text content. "
        f"The 'title' should be a concise and engaging article title, not just the issue title. "
        f"The 'summary' should be a brief, one-sentence overview. "
        f"The 'summary_detail' should be a comprehensive, multi-paragraph explanation of the issue. Ensure it is at least 3 distinct paragraphs, with each paragraph separated by two newline characters (\\n\\n) to ensure proper visual separation, and provides thorough detail. "
        f"The 'key_findings' should be a list of crucial facts, each as a separate string item. Each item must contain actual text, not just an empty string. "
        f"The 'viewpoints' should provide at least 2-3 distinct angles or contrasting opinions/solutions related to the issue, each as a separate string item. Each item must contain actual text, not just an empty string or a colon. "
        f"The 'verified_sources' should be a list of objects, each with a 'name' (string) and 'url' (string) for the sources used. Each source must have a valid name and URL. If no specific sources are available, provide plausible, general sources like 'Research Institute' with a placeholder URL like 'https://example.com/research'."
        f"Provide the output in JSON format with the following structure:"
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"},
            "summary": {"type": "STRING"},
            "category": {
                "type": "STRING",
                "enum": ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES
            },
            "full_content": {
                "type": "OBJECT",
                "properties": {
                    "summary_detail": {"type": "STRING"},
                    "key_findings": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "viewpoints": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "verified_sources": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "url": {"type": "STRING"}}}}
                }
            }
        },
        "required": ["title", "summary", "category", "full_content"]
    }

    print(f"DEBUG: Generating full issue article for '{issue_title}' with AI classification and detailed content.")
    generated_data = call_gemini_api_with_json_schema(prompt_text, response_schema, gem_api_key)

    if generated_data and not generated_data.get("error"):
        title = generated_data.get("title", issue_title)
        summary = generated_data.get("summary", "")
        category = generated_data.get("category", "General")
        full_content = generated_data.get("full_content", {})

        summary_detail = full_content.get("summary_detail", "")
        key_findings = full_content.get("key_findings", [])
        viewpoints = full_content.get("viewpoints", [])
        verified_sources = full_content.get("verified_sources", [])

        article_id = f"debunkd-issue-{uuid.uuid4()}"
        clean_category_for_image = category.replace(' ', '+')
        image_url = f"https://placehold.co/300x200/1A202C/FFFFFF?text={clean_category_for_image}"

        article_obj = {
            "id": article_id,
            "title": title,
            "summary": summary,
            "category": category,
            "image_url": image_url,
            "original_url": "",
            "summary_detail": summary_detail,
            "key_insights": key_findings,
            "viewpoints": viewpoints,
            "sources": verified_sources
        }
        print(f"DEBUG: Generated Issue Article: Title='{article_obj['title']}', Category='{article_obj['category']}'")
        return article_obj
    else:
        print(f"Error generating full issue article for '{issue_title}': {generated_data.get('error', 'Unknown error')}")
        return None

# --- search_debunked (Updated to use JSON schema for news/fact-check) ---
def search_debunked(query, gem_api_key, news_api_key):
    enforce_rate_limit()
    try:
        response_classification = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={'Content-Type': 'application/json'},
            params={'key': gem_api_key},
            json={"contents": [{"role": "user", "parts": [{"text": f"Classify the following text/question as 'news', 'general', or 'not english'. Respond with 'n' for news, 'g' for general, or 'c' for not a word.: {query}"}]}]},
            timeout=60
        )
        response_classification.raise_for_status()
        result_classification = response_classification.json()
        classification = result_classification["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
    except Exception as e:
        print(f"Error in search_debunked (classification): {e}")
        traceback.print_exc()
        raise Exception(f"AI classification failed: {e}")

    if "c" in classification:
        raise Exception("We were not able to interpret your search. Please try explaining more clearly.")
    elif "g" in classification:
        # Fact-Check / General Article Generation
        prompt_text = (
            f"For the topic '{query}', generate a detailed, in-depth fact-check in JSON format. "
            f"Classify this fact-check into ONE of the following categories: {', '.join(ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES)}. "
            f"DO NOT refer to yourself as an AI model. DO NOT use any Markdown formatting like italics, bolding, or headings within the generated text content. "
            f"The 'title' should be a concise and engaging article title based on the query, not just the query itself. "
            f"The 'summary' should be a brief, one-sentence overview. "
            f"The 'summary_detail' should be a comprehensive, multi-paragraph explanation of the fact-check. Ensure it is at least 3 distinct paragraphs, with each paragraph separated by two newline characters (\\n\\n) to ensure proper visual separation, and provides thorough detail. "
            f"The 'key_findings' should be a list of crucial facts, each as a separate string item. "
            f"The 'viewpoints' should provide at least 2-3 distinct common arguments for and against the topic, or contrasting interpretations of the evidence, each as a separate string item. " # Enhanced instruction
            f"The 'verified_sources' should be a list of objects, each with a 'name' and 'url' for the sources used.\n\n"
            f"Provide the output in JSON format with the following structure:"
        )

        response_schema = {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "summary": {"type": "STRING"},
                "category": {
                    "type": "STRING",
                    "enum": ALLOWED_MISCONCEPTION_ISSUE_CATEGORIES
                },
                "full_content": {
                    "type": "OBJECT",
                    "properties": {
                        "summary_detail": {"type": "STRING"},
                        "key_findings": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "viewpoints": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "verified_sources": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "url": {"type": "STRING"}}}}
                    }
                }
            },
            "required": ["title", "summary", "category", "full_content"]
        }

        print(f"DEBUG: Generating general fact-check for '{query}' with AI classification and detailed content.")
        generated_data = call_gemini_api_with_json_schema(prompt_text, response_schema, gem_api_key)

        if generated_data and not generated_data.get("error"):
            title = generated_data.get("title", f"Fact-Check: {query}")
            summary = generated_data.get("summary", "")
            category = generated_data.get("category", "General")
            full_content = generated_data.get("full_content", {})

            summary_detail = full_content.get("summary_detail", "")
            key_findings = full_content.get("key_findings", [])
            viewpoints = full_content.get("viewpoints", [])
            verified_sources = full_content.get("verified_sources", [])

            article_id = f"debunkd-search-general-{uuid.uuid4()}"
            clean_category_for_image = category.replace(' ', '+')
            image_url = f"https://placehold.co/300x200/5C6BC0/FFFFFF?text={clean_category_for_image}"

            article_obj = {
                "id": article_id,
                "title": title,
                "summary": summary,
                "category": category,
                "image_url": image_url,
                "original_url": "",
                "summary_detail": summary_detail,
                "key_insights": key_findings,
                "viewpoints": viewpoints,
                "sources": verified_sources
            }
            print(f"DEBUG: Generated Search (General) Article: Title='{article_obj['title']}', Category='{article_obj['category']}'")
            return article_obj
        else:
            print(f"Error generating general fact-check: {generated_data.get('error', 'Unknown error')}")
            raise Exception(f"Error generating general fact-check: {generated_data.get('error', 'Unknown error')}")

    elif "n" in classification:
        # News Search
        keyword_prompt = f"Create a single, concise keyword search term for news articles based on the following text. Provide only the keyword(s) without any additional formatting, punctuation, or conversational text. User query: {query}"
        enforce_rate_limit()
        try:
            response_gemini_keyword = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers={'Content-Type': 'application/json'},
                params={'key': gem_api_key},
                json={"contents": [{"role": "user", "parts": [{"text": keyword_prompt}]}]},
                timeout=60
            )
            response_gemini_keyword.raise_for_status()
            result_keyword = response_gemini_keyword.json()
            keyword_search_term = result_keyword["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"Error generating search keyword: {e}")
            traceback.print_exc()
            raise Exception(f"Error generating search keyword: {e}")

        news_api_url = (f'https://newsapi.org/v2/everything?'
                        f'q={keyword_search_term}&'
                        f'sortBy=popularity&'
                        f'apiKey={news_api_key}')

        enforce_rate_limit()
        try:
            response_newsapi = requests.get(news_api_url, timeout=10)
            response_newsapi.raise_for_status()
            rsp_json = response_newsapi.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news articles from NewsAPI for search: {e}")
            traceback.print_exc()
            raise Exception(f"Error fetching news articles from NewsAPI: {e}")

        articles_for_source = []
        if rsp_json['totalResults'] == 0:
            raise Exception("Sorry, I didn't find any news articles for that search term. Please try a different query.")
        else:
            for article in rsp_json['articles'][:5]:
                articles_for_source.append(Article(url=article['url'], title=article.get('title', 'No Title')))

        if not articles_for_source:
            raise Exception("No relevant articles found to generate a news report.")

        generated_news_article = create_full_news_article(
            articles_for_source[0].title,
            articles_for_source,
            gem_api_key
        )
        
        if generated_news_article:
            generated_news_article['original_url'] = articles_for_source[0].url if articles_for_source else generated_news_article.get('original_url', '')
            
            if not generated_news_article.get('title'):
                generated_news_article['title'] = f"News Report: {query}"
            print(f"DEBUG: Generated Search (News) Article: Title='{generated_news_article['title']}', Category='{generated_news_article['category']}'")
            return generated_news_article
        else:
            raise Exception("Failed to generate a detailed news report for your query.")
    else:
        raise Exception("Unexpected classification from AI.")
    
def learn_chat(history, question, gem_api_key):
    context_message = "You are Media Mentor, an AI guide to media literacy. Your goal is to help users learn about media literacy, fact-checking, identifying bias, and navigating information online. Provide helpful, concise, and accurate information. Do not act like a general chatbot outside of media literacy topics. Keep responses focused on education and media literacy."

    contents_for_model = [{"role": "user", "parts": [{"text": context_message}]}] + history + [{"role": "user", "parts": [{"text": question}]}]

    enforce_rate_limit()
    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers={'Content-Type': 'application/json'},
            params={'key': gem_api_key},
            json={"contents": contents_for_model},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            model_response_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            updated_history_for_frontend = history + [{"role": "user", "parts": [{"text": question}]}] + [{"role": "model", "parts": [{"text": model_response_text}]}]
            return model_response_text, updated_history_for_frontend
        else:
            print(f"WARNING: Chatbot API response missing content: {result}")
            return "Sorry, I'm having trouble responding right now. Please try again.", history + [{"role": "user", "parts": [{"text": question}]}]

    except requests.exceptions.RequestException as e:
        print(f"Error in learn_chat: {e}")
        traceback.print_exc()
        return "Sorry, I'm having trouble responding right now. Please try again.", history + [{"role": "user", "parts": [{"text": question}]}]
    except Exception as e:
        print(f"An unexpected error occurred in learn_chat: {e}")
        return "Sorry, I'm having trouble responding right now. Please try again.", history + [{"role": "user", "parts": [{"text": question}]}]