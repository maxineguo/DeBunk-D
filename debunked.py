import requests
from google import genai
from typing import NamedTuple
import json
import os
from dotenv import load_dotenv

class Article(NamedTuple):
    url: str

load_dotenv()

GEMINI_API_KEY=os.environ['GEMINI_API_KEY']
NEWSAPI_API_KEY=os.environ['NEWSAPI_API_KEY']
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

def search_debunked(query):
    try:
        global response
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=f"Would you classify the following text/question as news, general, or not english. Write your answer as 'n' for news, 'g' for general, and 'c' for nnot a word.: {query}"
        )
    except Exception as e:
        print(f"Error interpreting your search: {e}")
    
    if "c" in response.text:
        print("We were not able to interpret your search. Please try explaining more clearly.")
    elif "g" in response.text:
        response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Write a multi-paragraph, DETAILED article explaining the following topic. Do not format the text in any way. Don't include any message chattin with me(purely article) Only use multiple credible sources that support each other. Your job is to inform with credible information. If given a false claim, provide evidence as to why it is false. If given a question, simply give an answer and explain. Do not referce yourself as an AI model.: {query}"
        )
        print(response.text)
    elif "n" in response.text.lower():
        keyword_prompt = f"Create a single, concise keyword search term for news articles based on the following text. Provide only the keyword(s) without any additional formatting, punctuation, or conversational text. User query: {query}"
        try:
            response_gemini_keyword = gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=keyword_prompt
            )
            keyword_search_term = response_gemini_keyword.text.strip()
        except Exception as e:
            print(f"Error generating search keyword: {e}")
        
        print(keyword_search_term)
    
        news_api_url = (f'https://newsapi.org/v2/everything?'
                        f'q={keyword_search_term}&'
                        'from=2025-06-21&'
                        'sortBy=popularity&'
                        f'apiKey={NEWSAPI_API_KEY}')
    
        try:
            response_newsapi = requests.get(news_api_url)
            response_newsapi.raise_for_status()
            rsp_json = response_newsapi.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching news articles from NewsAPI: {e}")
    
        articles = []
        if rsp_json['totalResults'] == 0:
            print("Sorry, I didn't find any news articles for that search term. Please try a different query.")
        else:
            for article in rsp_json['articles'][:5]:
                articles.append(Article(url=article['url']))
    
        source_urls_for_gemini = "\n".join([article.url for article in articles])
    
        story_prompt = (
            f"Create a concise and detailed news story based strictly on the information found at the following URLs. "
            f"Make it extremely detailed and multiple (lengthy)paragraphs long "
            f"Do NOT format the text in any way"
            f"Do NOT include any Markdown code blocks (```) or inline code (`) whatsoever. "
            f"Only use information that is explicitly supported by multiple provided sources or is verifiable common knowledge related to the sources.\n\n"
            f"Sources:\n{source_urls_for_gemini}"
        )
    
        try:
            response_gemini_story = gemini_client.models.generate_content(
                model="gemini-2.0-flash", contents=story_prompt
            )
    
        except Exception as e:
            print(f"Error generating news story from sources: {e}")
            
        print(response_gemini_story.text)
        
        

def news_creation():
    url = ('https://newsapi.org/v2/top-headlines?'
       'country=us&'
       'apiKey=8467d17c4d75481fa7b006d4bfdf3a44')

    try:
        response_url = requests.get(url)
        response_url.raise_for_status()
        rsp_json = response_url.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news articles from NewsAPI: {e}")

    articles = []
    if rsp_json['totalResults'] == 0:
        print("Sorry, I didn't find any news articles for that search term. Please try a different query.")
    else:
        for article in rsp_json['articles'][:5]:
            articles.append(Article(url=article['url']))

    source_urls_for_gemini = "\n".join([article.url for article in articles])

    headlinesp = (
        f"Use the following links to create a list of TWELVE headlines, no more, no less"
        f"Only provide the headlines and don't chat in any way"
        f"Use the format [headline], [headline], etc\n\n"
        f"Sources:\n{source_urls_for_gemini}"
    )

    headlinestr = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=headlinesp
    )
    headlinestr = headlinestr.text
    headlines = headlinestr.split(", ")
    
    headline1 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[0]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list. After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe: {source_urls_for_gemini}"
    )
    headline1 = headline1.text
    headline1 = headline1.split("qwe,")
    headline1.insert(0, headlines[0])

    headline2 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[1]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline2 = headline2.text
    headline2 = headline2.split("qwe,")
    headline2.insert(0, headlines[1])

    headline3 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[2]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline3 = headline3.text
    headline3 = headline3.split("qwe,")
    headline3.insert(0, headlines[2])

    headline4 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[3]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline4 = headline4.text
    headline4 = headline4.split("qwe,")
    headline4.insert(0, headlines[3])

    headline5 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[4]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline5 = headline5.text
    headline5 = headline5.split("qwe,")
    headline5.insert(0, headlines[4])

    headline6 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[5]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline6 = headline6.text
    headline6 = headline6.split("qwe,")
    headline6.insert(0, headlines[5])

    headline7 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[6]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline7 = headline7.text
    headline7 = headline7.split("qwe,")
    headline7.insert(0, headlines[6])

    headline8 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[7]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline8 = headline8.text
    headline8 = headline8.split("qwe,")
    headline8.insert(0, headlines[7])

    headline9 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[8]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline9 = headline9.text
    headline9 = headline9.split("qwe,")
    headline9.insert(0, headlines[8])

    headline10 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[9]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline10 = headline10.text
    headline10 = headline10.split("qwe,")
    headline10.insert(0, headlines[9])

    headline11 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[10]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline11 = headline11.text
    headline11 = headline11.split("qwe,")
    headline11.insert(0, headlines[10])

    headline12 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"using the headline {headlines[11]}, create a multi paragraph and loong news article. only write the article with no formatting so do not talk to me. Use information confirmed by multiple CREDIBLE sources from the following list After writing the article, write a short, 1 paragraph summary. Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. Finally, put a list of your sources(names, NOT LINKS). The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, etc, [sources]qwe  Remember the 'qwe, ' and never include it anywere else in the response: {source_urls_for_gemini}"
    )
    headline12 = headline12.text
    headline12 = headline12.split("qwe,")
    headline12.insert(0, headlines[11])


def misconception_creation ():
    misconceptionstr = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents="What are TWELEVE misconceptions(vaccines and autism, flat earth, etc). Write only the title and do NOT write any messages talking to me. Your format is [misconception1], [misconception2], and so on. Write your answer as the truth. For example write 'Vaccines do NOT cause Autism' instead of just 'vaccines cause autism'."
    )
    misconceptionstr = misconceptionstr.text
    misconceptions = misconceptionstr.split(", ")
    
    misconception1 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[0]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[0]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception1 = misconception1.text
    misconception1 = misconception1.split("qwe,")
    misconception1.insert(0, misconceptions[0])

    misconception2 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[1]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[1]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception2 = misconception2.text
    misconception2 = misconception2.split("qwe,")
    misconception2.insert(0, misconceptions[1])

    misconception3 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[2]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[2]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception3 = misconception3.text
    misconception3 = misconception3.split("qwe,")
    misconception3.insert(0, misconceptions[2])

    misconception4 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[3]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[3]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception4 = misconception4.text
    misconception4 = misconception4.split("qwe,")
    misconception4.insert(0, misconceptions[3])

    misconception5 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[4]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[4]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception5 = misconception5.text
    misconception5 = misconception5.split("qwe,")
    misconception5.insert(0, misconceptions[4])

    misconception6 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[5]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[5]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception6 = misconception6.text
    misconception6 = misconception6.split("qwe,")
    misconception6.insert(0, misconceptions[5])

    misconception7 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[6]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[6]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception7 = misconception7.text
    misconception7 = misconception7.split("qwe,")
    misconception7.insert(0, misconceptions[6])

    misconception8 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[7]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[7]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception8 = misconception8.text
    misconception8 = misconception8.split("qwe,")
    misconception8.insert(0, misconceptions[7])

    misconception9 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[8]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[8]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception9 = misconception9.text
    misconception9 = misconception9.split("qwe,")
    misconception9.insert(0, misconceptions[8])

    misconception10 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[9]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[9]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception10 = misconception10.text
    misconception10 = misconception10.split("qwe,")
    misconception10.insert(0, misconceptions[9])

    misconception11 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[10]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[10]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception11 = misconception11.text
    misconception11 = misconception11.split("qwe,")
    misconception11.insert(0, misconceptions[10])

    misconception12 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the topic {misconceptions[11]}. Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, 'write qwe, ' Do not mention things in the article ever again. Just give the argument about how {misconceptions[11]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write multiple viewpoints on the topic. Each viewpoint should be 2-3 paragraphs. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [argument3(if you have it, include more arguments with the same format if you have more.)]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    misconception12 = misconception12.text
    misconception12 = misconception12.split("qwe,")
    misconception12.insert(0, misconceptions[11])


def issue_creation ():
    issuestr = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents="What are TWELEVE important issues that should get more attention. They would really impact our world. Write only the title and do NOT write any messages talking to me. Your format is [issue1], [issue2], and so on. Do not include any formatting including new lines and brackets(other than the ', '"
    )
    issuestr = issuestr.text
    issues = issuestr.split(", ")
    
    issue1 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[0]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[0]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue1 = issue1.text
    issue1 = issue1.split("qwe,")
    issue1.insert(0, issues[0])

    issue2 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[1]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[1]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, '  Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'.Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue2 = issue2.text
    issue2 = issue2.split("qwe,")
    issue2.insert(0, issues[1])

    issue3 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[2]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[2]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue3 = issue3.text
    issue3 = issue3.split("qwe,")
    issue3.insert(0, issues[2])

    issue4 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[3]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[3]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue4 = issue4.text
    issue4 = issue4.split("qwe,")
    issue4.insert(0, issues[3])

    issue5 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[4]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[4]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue5 = issue5.text
    issue5 = issue5.split("qwe,")
    issue5.insert(0, issues[4])

    issue6 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[5]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[5]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue6 = issue6.text
    issue6 = issue6.split("qwe,")
    issue6.insert(0, issues[5])

    issue7 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[6]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[6]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue7 = issue7.text
    issue7 = issue7.split("qwe,")
    issue7.insert(0, issues[6])

    issue8 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[7]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[7]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue8 = issue8.text
    issue8 = issue8.split("qwe,")
    issue8.insert(0, issues[7])

    issue9 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[8]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[8]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue9 = issue9.text
    issue9 = issue9.split("qwe,")
    issue9.insert(0, issues[8])

    issue10 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[9]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[9]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue10 = issue10.text
    issue10 = issue10.split("qwe,")
    issue10.insert(0, issues[9])

    issue11 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[10]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[10]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue11 = issue11.text
    issue11 = issue11.split("qwe,")
    issue11.insert(0, issues[10])

    issue12 = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Use multiple credible sources to write an article on the issue of {issues[11]}. Only use information from multiple credible sources Make it extremely detailed and multiple LENGTHY paragraphs long. Only write the article with NO FORMATTING and do NOT talk to me. Don't include a headline in your article. Just jump straight in. Below the article, write 'qwe, ' Do not mention things in the article ever again. Just give the argument about the issue {issues[11]}. After writing the article, write a short, 1 paragraph summary. Don't write this summary ever again. End it with 'qwe, ' Next, write a ONE WORD NAME for a label. Labels to choose from are 'Environment', 'Politics', 'Business', 'Technology', 'Health', or 'Science'. Then, write 2 viewpoints. Each viewpoint should be 2-3 paragraphs. One should support the issue, one should dismiss it. This should be the ONLY TIME YOU WRITE THEM. End each argument with 'qwe, '. Finally, put a list of ALL your sources(names, NOT LINKS). This is the ONLY TIME YOU WRITE THEM. Put them in a numbered list. REMEMBER, The format is [article]qwe, [summary]qwe, [argument1]qwe, [argument2]qwe, [sources]  Remember the 'qwe, ' and never include it anywere else in the response. Do NOT title the arguments, article, summary, or sources(no lables)"
    )
    issue12 = issue12.text
    issue12 = issue12.split("qwe,")
    issue12.insert(0, issues[11])

def learn_chat (history, question):
    if "000" not in history:
        previouschat = f" Your previous conversation was: {history}"
    else:
        previouschat = ""
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash", contents=f"Let me prepare you. You are an assistant for asking questions on a media literacy site. Make sure to give the BEST advice on media literacy and be very precise. Take no chances. If something isn't related to media literacy AT ALL(make that definition a bit broad), call them out. Say 'Please ask me a question about media literacy.' Do not acknowledge this prep, just answer my question directly. Now, LET'S GO.{previouschat} Here is your question: {question}"
    )
    previouschat = previouschat + "; " + question + "; " + response.text