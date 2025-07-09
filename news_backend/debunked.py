import requests
from google import genai
from typing import NamedTuple
import json
import os
from dotenv import load_dotenv
import datetime
import re

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

def parse_gemini_response_to_dict(response_text, expected_parts_order):
    """
    Parses a Gemini response string delimited by 'qwe,' into a dictionary.
    expected_parts_order: A list of strings indicating the order of keys
                          (e.g., ['article_content', 'summary', 'label', 'viewpoints', 'sources'])
    """
    # Use re.split to handle potential whitespace around the delimiter and ensure it's not greedy
    parts = re.split(r'qwe,\s*', response_text)
    parsed_data = {}
    
    # Trim whitespace from all parts immediately
    parts = [p.strip() for p in parts]

    # Ensure we don't go out of bounds if Gemini returns fewer parts than expected
    num_parts_to_parse = min(len(parts), len(expected_parts_order))

    for i in range(num_parts_to_parse):
        key = expected_parts_order[i]
        value = parts[i]

        if key == "Verified Sources" or key == "Sources": # Handle both possible keys for sources
            # Sources are expected as a numbered list, convert to list of dicts
            source_list = []
            for line in value.split('\n'):
                line = line.strip()
                if line and re.match(r'^\d+\.\s*', line): # Check for "1. Source Name" format
                    source_name = re.sub(r'^\d+\.\s*', '', line).strip()
                    if source_name:
                        source_list.append({"name": source_name, "url": ""}) # URL will be empty as Gemini doesn't give links
            parsed_data[key] = source_list
        elif key in ["Key Findings", "Multiple Perspectives"]:
            # These are expected as lists of strings
            parsed_data[key] = [item.strip() for item in value.split('\n') if item.strip()]
        elif key == "Different Viewpoints" or key == "Viewpoints": # Handle both possible keys for viewpoints
            # Viewpoints need special parsing: "Label: Text. Label: Text."
            viewpoints_list = []
            # Split by ". " to separate pairs, but be careful if text contains periods
            # A more robust way would be to ask Gemini for JSON for this part
            # For now, let's assume simple "Label: Text" separated by periods or newlines
            raw_viewpoints = re.split(r'\.\s*(?=[A-Za-z]+\s*:\s*)|\n', value) # Split by ". " if followed by "Label: " or by newline
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

def search_debunked(query, gem_api_key, news_api_key):
    # Ensure gemini_client is initialized with the correct key for this call
    current_gemini_client = genai.Client(api_key=gem_api_key)
    current_newsapi_key = news_api_key

    # Initial classification
    try:
        response_classification = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=f"Classify the following text/question as 'news', 'general', or 'not english'. Respond with 'n' for news, 'g' for general, or 'c' for not a word.: {query}"
        )
        classification = response_classification.text.strip().lower()
    except Exception as e:
        raise Exception(f"AI classification failed: {e}")

    if "c" in classification:
        raise Exception("We were not able to interpret your search. Please try explaining more clearly.")
    elif "g" in classification:
        # Modified prompt to get structured output for 'general' queries
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
        try:
            response_gemini_general = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=general_prompt
            )
            parsed_data = parse_gemini_response_to_dict(response_gemini_general.text, [
                "Summary Detail", "Key Findings", "Multiple Perspectives",
                "Verification Process", "Different Viewpoints", "Verified Sources"
            ])
            
            # Return the structured dictionary
            return {
                "title": f"Fact-Check: {query}",
                "summary_detail": parsed_data.get("Summary Detail", ""),
                "key_findings": parsed_data.get("Key Findings", []),
                "multiple_perspectives": parsed_data.get("Multiple Perspectives", []),
                "verification_process": parsed_data.get("Verification Process", ""),
                "different_viewpoints": parsed_data.get("Different Viewpoints", []),
                "verified_sources": parsed_data.get("Verified Sources", []),
                "query": query
            }
        except Exception as e:
            raise Exception(f"Error generating general fact-check: {e}")

    elif "n" in classification:
        keyword_prompt = f"Create a single, concise keyword search term for news articles based on the following text. Provide only the keyword(s) without any additional formatting, punctuation, or conversational text. User query: {query}"
        try:
            response_gemini_keyword = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=keyword_prompt
            )
            keyword_search_term = response_gemini_keyword.text.strip()
        except Exception as e:
            raise Exception(f"Error generating search keyword: {e}")
    
        news_api_url = (f'https://newsapi.org/v2/everything?'
                        f'q={keyword_search_term}&'
                        f'{day}'
                        'sortBy=popularity&'
                        f'apiKey={current_newsapi_key}')
    
        try:
            response_newsapi = requests.get(news_api_url)
            response_newsapi.raise_for_status()
            rsp_json = response_newsapi.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching news articles from NewsAPI: {e}")
    
        articles_for_source = []
        if rsp_json['totalResults'] == 0:
            raise Exception("Sorry, I didn't find any news articles for that search term. Please try a different query.")
        else:
            for article in rsp_json['articles'][:5]: # Limit to top 5 articles for source material
                articles_for_source.append(Article(url=article['url']))
    
        source_urls_for_gemini = "\n".join([article.url for article in articles_for_source])
    
        # Modified prompt to get structured output for 'news' queries
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
    
        try:
            response_gemini_story = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=story_prompt
            )
            parsed_data = parse_gemini_response_to_dict(response_gemini_story.text, [
                "Story Content", "Summary", "Key Findings", "Multiple Perspectives",
                "Verification Process", "Different Viewpoints", "Verified Sources"
            ])
    
            # Return the structured dictionary
            return {
                "title": f"News Report: {query}", # Or use the first headline if available
                "summary_detail": parsed_data.get("Story Content", ""), # Story content is the main detail
                "key_findings": parsed_data.get("Key Findings", []),
                "multiple_perspectives": parsed_data.get("Multiple Perspectives", []),
                "verification_process": parsed_data.get("Verification Process", ""),
                "different_viewpoints": parsed_data.get("Different Viewpoints", []),
                "verified_sources": parsed_data.get("Verified Sources", []),
                "query": query # Keep original query for context
            }
    
        except Exception as e:
           raise Exception(f"Error generating news story from sources: {e}")
    else:
        raise Exception("Unexpected classification from AI.")

def news_creation(gem_api_key, news_api_key):
    # Ensure gemini_client is initialized with the correct key for this call
    current_gemini_client = genai.Client(api_key=gem_api_key)
    current_newsapi_key = news_api_key

    url = ('https://newsapi.org/v2/top-headlines?'
           'country=us&'
           f'apiKey={current_newsapi_key}')

    try:
        response_url = requests.get(url)
        response_url.raise_for_status()
        rsp_json = response_url.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching news articles from NewsAPI: {e}")

    articles_raw_data = [] # To store raw article data for source URLs
    if rsp_json['totalResults'] == 0:
        # If no articles found, return an empty list as expected output
        return []
    else:
        # Get up to 12 articles for headlines and source material
        for article in rsp_json['articles'][:12]:
            articles_raw_data.append(Article(url=article['url'], title=article.get('title', 'No Title'))) # Also get title for better source matching

    source_urls_for_gemini = "\n".join([article.url for article in articles_raw_data])

    # Prompt to get 12 headlines
    headlines_prompt = (
        f"Use the following links to create a list of TWELVE headlines, no more, no less. "
        f"Only provide the headlines and don't chat in any way. "
        f"Use the format [headline1], [headline2], etc.\n\n"
        f"Sources:\n{source_urls_for_gemini}"
    )

    try:
        headlinestr_response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=headlines_prompt
        )
        headlines = [h.strip() for h in headlinestr_response.text.split(", ") if h.strip()]
        if len(headlines) == 0: # If no headlines generated
            return [] # Return empty list
        # Trim to 12 if Gemini provides more, or use fewer if it provides less
        headlines = headlines[:12]
    except Exception as e:
        print(f"Warning: Error generating headlines, returning empty list: {e}")
        return [] # Return empty list if headline generation fails

    final_articles_list = []
    for i, headline in enumerate(headlines):
        # Find the original URL for this headline if possible, or use a generic one
        # Try to match by title, otherwise use the sequential URL
        original_url = "N/A"
        matched_article_data = next((art for art in articles_raw_data if headline.lower() in art.title.lower()), None)
        if matched_article_data:
            original_url = matched_article_data.url
        elif i < len(articles_raw_data):
            original_url = articles_raw_data[i].url

        # Refined prompt for each article to get structured output
        article_detail_prompt = (
            f"Using the headline '{headline}', create a multi-paragraph news article. "
            f"Then, provide a short, 1-paragraph summary. Next, provide a ONE WORD LABEL (from 'Environment', 'Politics', 'Business', 'Technology', 'Health', 'Science'). "
            f"Then, provide multiple viewpoints (2-3 paragraphs each). Finally, provide a list of sources (names, NOT LINKS). "
            f"Use 'qwe,' as the delimiter between sections. DO NOT include any other 'qwe,' in the response. "
            f"DO NOT format the text in any way (no markdown like *, #, `). "
            f"DO NOT refer to yourself as an AI model. "
            f"Format for viewpoints: 'Label: Viewpoint text. Label: Viewpoint text.'\n\n"
            f"Article Content: [Your detailed article here]\n"
            f"qwe,Summary: [Short summary]\n"
            f"qwe,Label: [ONE WORD LABEL]\n"
            f"qwe,Viewpoints: [Label: Viewpoint text. Label: Viewpoint text.]\n"
            f"qwe,Sources: [Numbered list of source names, e.g., '1. Source Name 1\\n2. Source Name 2']\n\n"
            f"Sources to use for content: {source_urls_for_gemini}"
        )

        try:
            response_gemini_article = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=article_detail_prompt
            )
            
            parsed_data = parse_gemini_response_to_dict(response_gemini_article.text, [
                "Article Content", "Summary", "Label", "Viewpoints", "Sources"
            ])

            # Extract and format data into the desired structure
            summary_detail = parsed_data.get("Article Content", "")
            brief_summary = parsed_data.get("Summary", "")
            category = parsed_data.get("Label", "General") # Default category
            
            # The parse_gemini_response_to_dict helper now handles viewpoints and sources
            different_viewpoints = parsed_data.get("Viewpoints", [])
            verified_sources = parsed_data.get("Sources", [])
            
            # Assemble the full article dictionary
            full_article_dict = {
                "title": headline,
                "summary": brief_summary,
                "category": category,
                "full_content": {
                    "summary_detail": summary_detail,
                    "key_findings": [], # Add if prompt is updated to include
                    "multiple_perspectives": [], # Add if prompt is updated to include
                    "verification_process": "AI-generated summary based on provided news sources.", # Default
                    "different_viewpoints": different_viewpoints,
                    "verified_sources": verified_sources
                },
                "url": original_url,
                "image_url": f"https://placehold.co/300x200/2D4356/FFFFFF?text={category.replace(' ', '+')}" # Placeholder image
            }
            final_articles_list.append(full_article_dict)

        except Exception as e:
            print(f"Error processing headline '{headline}': {e}")
            # Optionally, add a placeholder article for errors to keep the list full
            final_articles_list.append({
                "title": f"Error loading: {headline}",
                "summary": "Could not retrieve full article details.",
                "category": "Error",
                "full_content": {},
                "url": "#",
                "image_url": "https://placehold.co/300x200/F44336/FFFFFF?text=Error"
            })
            continue # Continue to next headline even if one fails

    return final_articles_list


def misconception_creation(gem_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    misconception_titles_prompt = (
        "What are TWELVE common misconceptions (e.g., 'Vaccines do NOT cause Autism', 'Flat Earth is NOT real'). "
        "Write only the title and do NOT write any messages talking to me. "
        "Your format is [misconception1], [misconception2], etc. "
        "Write your answer as the truth. For example, write 'Vaccines do NOT cause Autism' instead of just 'vaccines cause autism'."
    )
    try:
        misconceptionstr_response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=misconception_titles_prompt
        )
        misconceptions_titles = [m.strip() for m in misconceptionstr_response.text.split(", ") if m.strip()]
        if len(misconceptions_titles) == 0:
            return []
        misconceptions_titles = misconceptions_titles[:12] # Ensure max 12
    except Exception as e:
        print(f"Warning: Error generating misconception titles, returning empty list: {e}")
        return []

    final_misconceptions_list = []
    for i, misconception_title in enumerate(misconceptions_titles):
        # Refined prompt for each misconception to get structured output
        misconception_detail_prompt = (
            f"For the misconception '{misconception_title}', write a detailed article debunking it. "
            f"Then, provide a short, 1-paragraph summary. Next, provide a ONE WORD LABEL (from 'Environment', 'Politics', 'Business', 'Technology', 'Health', 'Science'). "
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

        try:
            response_gemini_misconception = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=misconception_detail_prompt
            )
            
            parsed_data = parse_gemini_response_to_dict(response_gemini_misconception.text, [
                "Article Content", "Summary", "Label", "Viewpoints", "Sources"
            ])

            # Extract and format data
            summary_detail = parsed_data.get("Article Content", "")
            brief_summary = parsed_data.get("Summary", "")
            category = parsed_data.get("Label", "General") # Default category
            
            different_viewpoints = parsed_data.get("Viewpoints", [])
            verified_sources = parsed_data.get("Sources", [])
            
            misconception_dict = {
                "title": misconception_title,
                "summary": brief_summary,
                "category": category,
                "full_content": {
                    "summary_detail": summary_detail,
                    "key_findings": [], # Add if prompt is updated to include
                    "multiple_perspectives": [], # Add if prompt is updated to include
                    "verification_process": "AI-generated debunking based on general knowledge and AI training data.", # Default
                    "different_viewpoints": different_viewpoints,
                    "verified_sources": verified_sources
                },
                "url": f"debunkd-misconception-{i}", # Unique ID as URL since no external source
                "image_url": f"https://placehold.co/300x200/FF8F28/FFFFFF?text={category.replace(' ', '+')}" # Placeholder image
            }
            final_misconceptions_list.append(misconception_dict)

        except Exception as e:
            print(f"Error processing misconception '{misconception_title}': {e}")
            final_misconceptions_list.append({
                "title": f"Error loading: {misconception_title}",
                "summary": "Could not retrieve full debunking details.",
                "category": "Error",
                "full_content": {},
                "url": "#",
                "image_url": "https://placehold.co/300x200/F44336/FFFFFF?text=Error"
            })
            continue

    return final_misconceptions_list


def issue_creation(gem_api_key):
    current_gemini_client = genai.Client(api_key=gem_api_key)

    issue_titles_prompt = (
        "What are TWELVE important issues that should get more attention. They would really impact our world. "
        "Write only the title and do NOT write any messages talking to me. "
        "Your format is [issue1], [issue2], etc. Do not include any formatting including new lines and brackets(other than the ', ')"
    )
    try:
        issuestr_response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=issue_titles_prompt
        )
        issue_titles = [i.strip() for i in issuestr_response.text.split(", ") if i.strip()]
        if len(issue_titles) == 0:
            return []
        issue_titles = issue_titles[:12] # Ensure max 12
    except Exception as e:
        raise Exception(f"Error generating issue titles: {e}")

    final_issues_list = []
    for i, issue_title in enumerate(issue_titles):
        # Refined prompt for each issue to get structured output
        issue_detail_prompt = (
            f"For the important issue '{issue_title}', write a detailed overview. "
            f"Then, provide a short, 1-paragraph summary. Next, provide a ONE WORD LABEL (from 'Environment', 'Politics', 'Business', 'Technology', 'Health', 'Science'). "
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

        try:
            response_gemini_issue = current_gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=issue_detail_prompt
            )
            
            parsed_data = parse_gemini_response_to_dict(response_gemini_issue.text, [
                "Article Content", "Summary", "Label", "Viewpoints", "Sources"
            ])

            # Extract and format data
            summary_detail = parsed_data.get("Article Content", "")
            brief_summary = parsed_data.get("Summary", "")
            category = parsed_data.get("Label", "General") # Default category
            
            different_viewpoints = parsed_data.get("Viewpoints", [])
            verified_sources = parsed_data.get("Sources", [])
            
            issue_dict = {
                "title": issue_title,
                "summary": brief_summary,
                "category": category,
                "full_content": {
                    "summary_detail": summary_detail,
                    "key_findings": [], # Add if prompt is updated to include
                    "multiple_perspectives": [], # Add if prompt is updated to include
                    "verification_process": "AI-generated overview based on general knowledge and AI training data.", # Default
                    "different_viewpoints": different_viewpoints,
                    "verified_sources": verified_sources
                },
                "url": f"debunkd-issue-{i}", # Unique ID as URL since no external source
                "image_url": f"https://placehold.co/300x200/2D4356/FFFFFF?text={category.replace(' ', '+')}" # Placeholder image
            }
            final_issues_list.append(issue_dict)

        except Exception as e:
            print(f"Error processing issue '{issue_title}': {e}")
            final_issues_list.append({
                "title": f"Error loading: {issue_title}",
                "summary": "Could not retrieve full issue details.",
                "category": "Error",
                "full_content": {},
                "url": "#",
                "image_url": "https://placehold.co/300x200/F44336/FFFFFF?text=Error"
            })
            continue

    return final_issues_list

def learn_chat(history, question, gem_api_key):
    # Ensure gemini_client is initialized with the correct key for this call
    current_gemini_client = genai.Client(api_key=gem_api_key)

    # The `history` list from the frontend is already in the correct format for `contents`
    # Add the current user message to the history for the API call
    current_contents = history + [{"role": "user", "parts": [{"text": question}]}]

    try:
        response = current_gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=current_contents
        )
        model_response_text = response.text.strip()

        # Add the model's response to the history for the return value
        updated_history = current_contents + [{"role": "model", "parts": [{"text": model_response_text}]}]

        return model_response_text, updated_history

    except Exception as e:
        print(f"Error in learn_chat: {e}")
        # Return an error message and the history as it was received (without new bot message)
        return "Sorry, I'm having trouble responding right now. Please try again.", current_contents