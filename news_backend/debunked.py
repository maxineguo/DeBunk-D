import requests
from google import genai
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

today = datetime.date.today()
one_day = datetime.timedelta(days=1)
yesterday = today - one_day
day = "from=" + yesterday.strftime('%Y-%m-%d') + "&"

class Article(NamedTuple):
    url: str
    title: str

load_dotenv()

GEMINI_API_KEY=os.environ['GEMINI_API_KEY']
NEWSAPI_API_KEY=os.environ['NEWSAPI_API_KEY']
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Define a global delay for API calls to prevent rate limiting
API_CALL_DELAY = 6 # seconds, increased based on previous errors

# Global rate limit variables for Gemini/NewsAPI calls
RATE_LIMIT_MAX_CALLS_PER_MINUTE = 15
RATE_LIMIT_INTERVAL_SECONDS = 60
api_call_timestamps = collections.deque() # Stores timestamps of recent calls
api_call_lock = threading.Lock() # Protects api_call_timestamps

def enforce_rate_limit():
    """
    Enforces a rate limit of RATE_LIMIT_MAX_CALLS_PER_MINUTE API calls per minute.
    Blocks execution if the limit is exceeded until a slot becomes available.
    """
    global api_call_timestamps
    with api_call_lock:
        # Remove timestamps older than RATE_LIMIT_INTERVAL_SECONDS
        while api_call_timestamps and api_call_timestamps[0] < time.time() - RATE_LIMIT_INTERVAL_SECONDS:
            api_call_timestamps.popleft()

        # If we've hit the limit, wait until a slot opens up
        if len(api_call_timestamps) >= RATE_LIMIT_MAX_CALLS_PER_MINUTE:
            time_to_wait = api_call_timestamps[0] + RATE_LIMIT_INTERVAL_SECONDS - time.time()
            if time_to_wait > 0:
                print(f"DEBUG: Rate limit hit. Waiting for {time_to_wait:.2f} seconds before next API call.")
                time.sleep(time_to_wait)
                # After waiting, remove old timestamps again
                while api_call_timestamps and api_call_timestamps[0] < time.time() - RATE_LIMIT_INTERVAL_SECONDS:
                    api_call_timestamps.popleft()
        
        # Add current call timestamp
        api_call_timestamps.append(time.time())
        # print(f"DEBUG: API call made. Current calls in last minute: {len(api_call_timestamps)}")


def parse_gemini_response_to_dict(response_text, expected_parts_order):
    """
    Parses a Gemini response string delimited by 'qwe,' into a dictionary.
    expected_parts_order: A list of strings indicating the order of keys
    """
    parts = re.split(r'qwe,\s*', response_text)
    parsed_data = {}
    
    parts = [p.strip() for p in parts]

    num_parts_to_parse = min(len(parts), len(expected_parts_order))

    for i in range(num_parts_to_parse):
        key = expected_parts_order[i]
        value = parts[i]

        if key in ["Verified Sources", "Sources"]:
            source_list = []
            for line in value.split('\n'):
                line = line.strip()
                if line and re.match(r'^\d+\.\s*', line):
                    source_name = re.sub(r'^\d+\.\s*', '', line).strip()
                    if source_name:
                        source_list.append({"name": source_name, "url": ""})
            parsed_data[key] = source_list
        elif key in ["Key Findings", "Multiple Perspectives"]:
            parsed_data[key] = [item.strip() for item in value.split('\n') if item.strip()]
        elif key in ["Different Viewpoints", "Viewpoints"]:
            viewpoints_list = []
            raw_viewpoints = re.split(r'\.\s*(?=[A-Za-z]+\s*:\s*)|\n', value)
            for vp_pair in raw_viewpoints:
                vp_pair = vp_pair.strip()
                if ':' in vp_pair:
                    label, text = vp_pair.split(':', 1)
                    if label.strip() and text.strip():
                        viewpoints_list.append({"label": label.strip(), "text": text.strip()})
            parsed_data[key] = viewpoints_list
        else:
            parsed_data[key] = value
            
    return parsed_data

# --- Headline Generation Functions ---
def get_news_headlines(gem_api_key, news_api_key, count=12):
    current_gemini_client = genai.Client(api_key=gem_api_key)
    current_newsapi_key = news_api_key

    url = ('https://newsapi.org/v2/top-headlines?'
           'country=us&'
           f'apiKey={current_newsapi_key}')

    enforce_rate_limit() # Enforce rate limit before NewsAPI call
    try:
        response_url = requests.get(url)
        response_url.raise_for_status()
        rsp_json = response_url.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching raw news articles for headlines: {e}")
        traceback.print_exc()
        return []

    articles_raw_data = []
    if rsp_json['totalResults'] == 0:
        return []
    else:
        for article in rsp_json['articles']:
            if article.get('url') and article.get('title'):
                articles_raw_data.append(Article(url=article['url'], title=article['title']))
            if len(articles_raw_data) >= count * 3: # Fetch more raw articles to generate 'count' unique headlines
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

    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        headlinestr_response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=headlines_prompt
        )
        headlines = [h.strip() for h in headlinestr_response.text.split(", ") if h.strip()]
        # Use OrderedDict to maintain order while removing duplicates
        headlines = list(collections.OrderedDict.fromkeys(headlines))
        headlines = headlines[:count] # Ensure we only return 'count' headlines
        return headlines
    except Exception as e:
        print(f"Error generating news headlines: {e}")
        traceback.print_exc()
        return []

def get_misconception_headlines(gem_api_key, count=12):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    misconception_titles_prompt = (
        f"Generate exactly {count} distinct and common misconceptions. "
        f"Each should be phrased as a factual statement debunking the misconception (e.g., 'Vaccines do NOT cause Autism', 'Flat Earth is NOT real'). "
        f"Only provide the statements, separated by commas, with no other text. "
        f"Format: [misconception1], [misconception2], ...\n"
    )
    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        misconceptionstr_response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=misconception_titles_prompt
        )
        misconceptions_titles = [m.strip() for m in misconceptionstr_response.text.split(", ") if m.strip()]
        misconceptions_titles = list(collections.OrderedDict.fromkeys(misconceptions_titles))
        misconceptions_titles = misconceptions_titles[:count]
        return misconceptions_titles
    except Exception as e:
        print(f"Error generating misconception headlines: {e}")
        traceback.print_exc()
        return []

def get_issue_headlines(gem_api_key, count=12):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    issue_titles_prompt = (
        f"Generate exactly {count} distinct and important global issues that warrant more attention and have significant world impact. "
        f"Only provide the issue titles, separated by commas, with no other text. "
        f"Format: [issue1], [issue2], ...\n"
    )
    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        issuestr_response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=issue_titles_prompt
        )
        issue_titles = [i.strip() for i in issuestr_response.text.split(", ") if i.strip()]
        issue_titles = list(collections.OrderedDict.fromkeys(issue_titles))
        issue_titles = issue_titles[:count]
        return issue_titles
    except Exception as e:
        print(f"Error generating issue headlines: {e}")
        traceback.print_exc()
        return []

# --- Full Article Creation Functions (now take a single headline) ---
def create_full_news_article(headline, raw_articles_for_source, gem_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    source_urls_for_gemini = "\n".join([article.url for article in raw_articles_for_source]) if raw_articles_for_source else "No specific sources provided."

    story_prompt = (
        f"Create a detailed news story based strictly on the information found at the following URLs, focusing on the headline '{headline}'. "
        f"If no specific sources are provided, generate a plausible news story for the headline. "
        f"Then, provide a short, 1-paragraph summary. Next, provide key findings (list). "
        f"Then, provide multiple perspectives (list). Then, provide a verification process explanation. "
        f"Then, provide different viewpoints (label: text format). Finally, provide verified sources (numbered list of names). "
        f"Use 'qwe,' as the delimiter between sections. DO NOT include any other 'qwe,' in the response. "
        f"DO NOT format the text in any way (no markdown like *, #, `). "
        f"DO NOT refer to yourself as an AI model.\n\n"
        f"Story Content: [Detailed news story content]\n"
        f"qwe,Summary: [Short, 1-paragraph summary]\n"
        f"qwe,Key Findings: [List of key findings, each on a new line, e.g., '- Finding 1\\n- Finding 2']\n"
        f"qwe,Multiple Perspectives: [List of different perspectives, each on a new line, e.g., '- Perspective A\\n- Perspective B']\n"
        f"qwe,Verification Process: [Explanation of verification process]\n"
        f"qwe,Different Viewpoints: [Label: Viewpoint text. Label: Viewpoint text. (e.g., 'Analyst: Text. Public: Text.')]\n"
        f"qwe,Verified Sources: [Numbered list of source names, e.g., '1. Source Name 1\\n2. Source Name 2']\n\n"
        f"Sources to use:\n{source_urls_for_gemini}"
    )

    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        response_gemini_story = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=story_prompt
        )
        parsed_data = parse_gemini_response_to_dict(response_gemini_story.text, [
            "Story Content", "Summary", "Key Findings", "Multiple Perspectives",
            "Verification Process", "Different Viewpoints", "Verified Sources"
        ])

        original_url = next((art.url for art in raw_articles_for_source if headline.lower() in art.title.lower()), f"debunkd-news-{headline.replace(' ', '-')[:50]}-{uuid.uuid4()}")

        return {
            "id": f"debunkd-news-{headline.replace(' ', '-')[:50]}-{uuid.uuid4()}", # Ensure unique ID
            "title": headline,
            "summary": parsed_data.get("Summary", "")[:150] + "...",
            "category": "News Report",
            "full_content": {
                "summary_detail": parsed_data.get("Story Content", ""),
                "key_findings": parsed_data.get("Key Findings", []),
                "multiple_perspectives": parsed_data.get("Multiple Perspectives", []),
                "verification_process": parsed_data.get("Verification Process", ""),
                "different_viewpoints": parsed_data.get("Different Viewpoints", []),
                "verified_sources": parsed_data.get("Verified Sources", []),
            },
            "url": original_url,
            "image_url": f"https://placehold.co/300x200/007bff/FFFFFF?text=News+Report"
        }
    except Exception as e:
        print(f"Error generating full news article for '{headline}': {e}")
        traceback.print_exc()
        return None # Return None if generation fails

def create_full_misconception_article(misconception_title, gem_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    misconception_detail_prompt = (
        f"For the misconception '{misconception_title}', write a detailed article debunking it. "
        f"Then, provide a short, 1-paragraph summary. Next, provide a ONE WORD LABEL (from 'Environment', 'Politics', 'Business', 'Technology', 'Health', 'Science', 'Society', 'Education'). "
        f"Then, provide multiple viewpoints (2-3 paragraphs each). Finally, provide a list of sources (names, NOT LINKS). "
        f"Use 'qwe,' as the delimiter between sections. DO NOT include any other 'qwe,' in the response. "
        f"DO NOT format the text in any way (no markdown like *, #, `). "
        f"DO NOT refer to yourself as an AI model. "
        f"Format for viewpoints: 'Label: Viewpoint text. Label: Viewpoint text.'\n\n"
        f"Article Content: [Your detailed debunking article here]\n"
        f"qwe,Summary: [Short summary]\n"
        f"qwe,Label: [ONE WORD LABEL]\n"
        f"qwe,Viewpoints: [Label: Viewpoint text. Label: Viewpoint text.]\n"
        f"qwe,Sources: [Numbered list of source names, e.g., '1. Source Name 1\\n2. Source Name 2']"
    )

    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        response_gemini_misconception = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=misconception_detail_prompt
        )
        parsed_data = parse_gemini_response_to_dict(response_gemini_misconception.text, [
            "Article Content", "Summary", "Label", "Viewpoints", "Sources"
        ])

        summary_detail = parsed_data.get("Article Content", "")
        brief_summary = parsed_data.get("Summary", "")
        category = parsed_data.get("Label", "General")
        
        different_viewpoints = parsed_data.get("Viewpoints", [])
        verified_sources = parsed_data.get("Sources", [])
        
        misconception_dict = {
            "id": f"debunkd-misconception-{misconception_title.replace(' ', '-')[:50]}-{uuid.uuid4()}", # Ensure unique ID
            "title": misconception_title,
            "summary": brief_summary,
            "category": category,
            "full_content": {
                "summary_detail": summary_detail,
                "key_findings": [],
                "multiple_perspectives": [],
                "verification_process": "AI-generated debunking based on general knowledge and AI training data.",
                "different_viewpoints": different_viewpoints,
                "verified_sources": verified_sources
            },
            "url": f"debunkd-misconception-{misconception_title.replace(' ', '-')[:50]}",
            "image_url": f"https://placehold.co/300x200/FF8C00/FFFFFF?text={category.replace(' ', '+')}"
        }
        return misconception_dict
    except Exception as e:
        print(f"Error generating full misconception article for '{misconception_title}': {e}")
        traceback.print_exc()
        return None

def create_full_issue_article(issue_title, gem_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    issue_detail_prompt = (
        f"For the important issue '{issue_title}', write a detailed overview. "
        f"Then, provide a short, 1-paragraph summary. Next, provide a ONE WORD LABEL (from 'Environment', 'Politics', 'Business', 'Technology', 'Health', 'Science', 'Society', 'Education'). "
        f"Then, provide multiple viewpoints (2-3 paragraphs each). Finally, provide a list of sources (names, NOT LINKS). "
        f"Use 'qwe,' as the delimiter between sections. DO NOT include any other 'qwe,' in the response. "
        f"DO NOT format the text in any way (no markdown like *, #, `). "
        f"DO NOT refer to yourself as an AI model. "
        f"Format for viewpoints: 'Label: Viewpoint text. Label: Viewpoint text.'\n\n"
        f"Article Content: [Your detailed issue overview here]\n"
        f"qwe,Summary: [Short summary]\n"
        f"qwe,Label: [ONE WORD LABEL]\n"
        f"qwe,Viewpoints: [Label: Viewpoint text. Label: Viewpoint text.]\n"
        f"qwe,Sources: [Numbered list of source names, e.g., '1. Source Name 1\\n2. Source Name 2']"
    )

    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        response_gemini_issue = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=issue_detail_prompt
        )
        parsed_data = parse_gemini_response_to_dict(response_gemini_issue.text, [
            "Article Content", "Summary", "Label", "Viewpoints", "Sources"
        ])

        summary_detail = parsed_data.get("Article Content", "")
        brief_summary = parsed_data.get("Summary", "")
        category = parsed_data.get("Label", "General")
        
        different_viewpoints = parsed_data.get("Viewpoints", [])
        verified_sources = parsed_data.get("Sources", [])
        
        issue_dict = {
            "id": f"debunkd-issue-{issue_title.replace(' ', '-')[:50]}-{uuid.uuid4()}", # Ensure unique ID
            "title": issue_title,
            "summary": brief_summary,
            "category": category,
            "full_content": {
                "summary_detail": summary_detail,
                "key_findings": [],
                "multiple_perspectives": [],
                "verification_process": "AI-generated overview based on general knowledge and AI training data.",
                "different_viewpoints": different_viewpoints,
                "verified_sources": verified_sources
            },
            "url": f"debunkd-issue-{issue_title.replace(' ', '-')[:50]}",
            "image_url": f"https://placehold.co/300x200/1A202C/FFFFFF?text={category.replace(' ', '+')}"
        }
        return issue_dict
    except Exception as e:
        print(f"Error generating full issue article for '{issue_title}': {e}")
        traceback.print_exc()
        return None

# --- Original search_debunked (remains largely the same, but uses API_CALL_DELAY) ---
def search_debunked(query, gem_api_key, news_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)
    current_newsapi_key = news_api_key

    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        response_classification = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=f"Classify the following text/question as 'news', 'general', or 'not english'. Respond with 'n' for news, 'g' for general, or 'c' for not a word.: {query}"
        )
        classification = response_classification.text.strip().lower()
    except Exception as e:
        print(f"Error in search_debunked (classification): {e}")
        traceback.print_exc()
        raise Exception(f"AI classification failed: {e}")

    if "c" in classification:
        raise Exception("We were not able to interpret your search. Please try explaining more clearly.")
    elif "g" in classification:
        general_prompt = (
            f"For the topic '{query}', generate a detailed fact-check in the following structured format. "
            f"Use 'qwe,' as the delimiter between sections. DO NOT include any other 'qwe,' in the response. "
            f"Each section should be detailed. Provide evidence for claims. "
            f"For Key Findings and Multiple Perspectives, use a new line for each item.\n\n"
            f"Summary Detail: [Detailed summary of the topic/claim]\n"
            f"qwe,Key Findings: [List of key findings, each on a new line, e.g., '- Finding 1\\n- Finding 2']\n"
            f"qwe,Multiple Perspectives: [List of different perspectives, each on a new line, e.g., '- Perspective A\\n- Perspective B']\n"
            f"qwe,Verification Process: [Explanation of how the information was verified]\n"
            f"qwe,Different Viewpoints: [Label: Viewpoint text. Label: Viewpoint text. (e.g., 'Scientific Community: Text. Public Opinion: Text.')]\n"
            f"qwe,Verified Sources: [Numbered list of source names, e.g., '1. Source Name 1\\n2. Source Name 2']"
        )
        enforce_rate_limit() # Enforce rate limit before Gemini call
        try:
            response_gemini_general = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=general_prompt
            )
            parsed_data = parse_gemini_response_to_dict(response_gemini_general.text, [
                "Summary Detail", "Key Findings", "Multiple Perspectives",
                "Verification Process", "Different Viewpoints", "Verified Sources"
            ])

            return {
                "id": f"debunkd-search-general-{query}-{uuid.uuid4()}", # Ensure unique ID
                "title": f"Fact-Check: {query}",
                "summary": parsed_data.get("Summary Detail", "")[:150] + "...",
                "category": "Fact-Check",
                "full_content": {
                    "summary_detail": parsed_data.get("Summary Detail", ""),
                    "key_findings": parsed_data.get("Key Findings", []),
                    "multiple_perspectives": parsed_data.get("Multiple Perspectives", []),
                    "verification_process": parsed_data.get("Verification Process", ""),
                    "different_viewpoints": parsed_data.get("Different Viewpoints", []),
                    "verified_sources": parsed_data.get("Verified Sources", []),
                },
                "url": f"debunkd-search-general-{query}",
                "image_url": f"https://placehold.co/300x200/5C6BC0/FFFFFF?text=Fact+Check"
            }
        except Exception as e:
            print(f"Error generating general fact-check: {e}")
            traceback.print_exc()
            raise Exception(f"Error generating general fact-check: {e}")

    elif "n" in classification:
        keyword_prompt = f"Create a single, concise keyword search term for news articles based on the following text. Provide only the keyword(s) without any additional formatting, punctuation, or conversational text. User query: {query}"
        enforce_rate_limit() # Enforce rate limit before Gemini call
        try:
            response_gemini_keyword = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=keyword_prompt
            )
            keyword_search_term = response_gemini_keyword.text.strip()
        except Exception as e:
            print(f"Error generating search keyword: {e}")
            traceback.print_exc()
            raise Exception(f"Error generating search keyword: {e}")

        news_api_url = (f'https://newsapi.org/v2/everything?'
                        f'q={keyword_search_term}&'
                        f'{day}'
                        'sortBy=popularity&'
                        f'apiKey={current_newsapi_key}')

        enforce_rate_limit() # Enforce rate limit before NewsAPI call
        try:
            response_newsapi = requests.get(news_api_url)
            response_newsapi.raise_for_status()
            rsp_json = response_newsapi.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news articles from NewsAPI: {e}")
            traceback.print_exc()
            raise Exception(f"Error fetching news articles from NewsAPI: {e}")

        articles_for_source = []
        if rsp_json['totalResults'] == 0:
            raise Exception("Sorry, I didn't find any news articles for that search term. Please try a different query.")
        else:
            for article in rsp_json['articles'][:5]:
                articles_for_source.append(Article(url=article['url'], title=article.get('title', 'No Title')))

        source_urls_for_gemini = "\n".join([article.url for article in articles_for_source])

        story_prompt = (
            f"Create a detailed news story based strictly on the information found at the following URLs. "
            f"Then, provide a short, 1-paragraph summary. Next, provide key findings (list). "
            f"Then, provide multiple perspectives (list). Then, provide a verification process explanation. "
            f"Then, provide different viewpoints (label: text format). Finally, provide verified sources (numbered list of names). "
            f"Use 'qwe,' as the delimiter between sections. DO NOT include any other 'qwe,' in the response. "
            f"DO NOT format the text in any way (no markdown like *, #, `). "
            f"DO NOT refer to yourself as an AI model.\n\n"
            f"Story Content: [Detailed news story content]\n"
            f"qwe,Summary: [Short, 1-paragraph summary]\n"
            f"qwe,Key Findings: [List of key findings, each on a new line, e.g., '- Finding 1\\n- Finding 2']\n"
            f"qwe,Multiple Perspectives: [List of different perspectives, each on a new line, e.g., '- Perspective A\\n- Perspective B']\n"
            f"qwe,Verification Process: [Explanation of verification process]\n"
            f"qwe,Different Viewpoints: [Label: Viewpoint text. Label: Viewpoint text. (e.g., 'Analyst: Text. Public: Text.')]\n"
            f"qwe,Verified Sources: [Numbered list of source names, e.g., '1. Source Name 1\\n2. Source Name 2']\n\n"
            f"Sources to use:\n{source_urls_for_gemini}"
        )

        enforce_rate_limit() # Enforce rate limit before Gemini call
        try:
            response_gemini_story = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=story_prompt
            )
            parsed_data = parse_gemini_response_to_dict(response_gemini_story.text, [
                "Story Content", "Summary", "Key Findings", "Multiple Perspectives",
                "Verification Process", "Different Viewpoints", "Verified Sources"
            ])

            original_url = articles_for_source[0].url if articles_for_source else f"debunkd-search-news-{query}-{uuid.uuid4()}"

            return {
                "id": f"debunkd-search-news-{query.replace(' ', '-')[:50]}-{uuid.uuid4()}", # Ensure unique ID
                "title": f"News Report: {query}",
                "summary": parsed_data.get("Summary", "")[:150] + "...",
                "category": "News Report",
                "full_content": {
                    "summary_detail": parsed_data.get("Story Content", ""),
                    "key_findings": parsed_data.get("Key Findings", []),
                    "multiple_perspectives": parsed_data.get("Multiple Perspectives", []),
                    "verification_process": parsed_data.get("Verification Process", ""),
                    "different_viewpoints": parsed_data.get("Different Viewpoints", []),
                    "verified_sources": parsed_data.get("Verified Sources", []),
                },
                "url": original_url,
                "image_url": f"https://placehold.co/300x200/007bff/FFFFFF?text=News+Report"
            }

        except Exception as e:
           print(f"Error generating news story from sources: {e}")
           traceback.print_exc()
           raise Exception(f"Error generating news story from sources: {e}")
    else:
        raise Exception("Unexpected classification from AI.")
    
def learn_chat(history, question, gem_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    current_contents = history + [{"role": "user", "parts": [{"text": question}]}]

    enforce_rate_limit() # Enforce rate limit before Gemini call
    try:
        response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=current_contents
        )
        model_response_text = response.text.strip()

        updated_history = current_contents + [{"role": "model", "parts": [{"text": model_response_text}]}]

        return model_response_text, updated_history

    except Exception as e:
        print(f"Error in learn_chat: {e}")
        traceback.print_exc()
        return "Sorry, I'm having trouble responding right now. Please try again.", current_contents