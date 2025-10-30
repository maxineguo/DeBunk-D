"""
Interactive activities for Knowledge Hub lessons using Gemini API
"""
import google.generativeai as genai
import time

API_CALL_DELAY = 1  # Delay between API calls in seconds

def analyze_bias(text, gemini_api_key):
    """
    Analyzes text for various types of bias
    """
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Analyze the following text for bias. Identify:
1. Types of bias present (political, personal, commercial, cultural, etc.)
2. Specific examples of biased language or framing
3. What viewpoints or perspectives are missing
4. How the bias affects the message
5. A "bias score" from 1-10 (1=minimal bias, 10=extreme bias)

Text to analyze:
{text}

Provide your analysis in a clear, educational format suitable for students learning about media literacy.
Format your response with clear sections using markdown."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def analyze_framing(headline, gemini_api_key):
    """
    Analyzes how a headline frames an issue
    """
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Analyze how this headline frames the issue:

Headline: "{headline}"

Identify:
1. The emotional tone (positive, negative, neutral, sensational)
2. Loaded words or phrases that influence perception
3. What information is emphasized vs. what's downplayed
4. Who or what is portrayed as the "hero" or "villain"
5. Alternative ways this same story could be framed
6. The potential impact on reader perception

Provide 2-3 alternative headlines that frame the same story differently, and explain how each changes the message.

Format your response clearly with sections using markdown."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def verify_source(url, gemini_api_key):
    """
    Provides guidance on verifying a source
    """
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Provide a comprehensive guide for verifying this source:

URL: {url}

Include:
1. What to look for in the domain name (.com, .org, .edu, etc.)
2. Questions to ask about the website's "About Us" page
3. How to check the author's credentials
4. What red flags to watch for (poor design, excessive ads, sensational language)
5. How to do lateral reading to verify this source
6. Specific verification steps for this type of source

Also explain what makes a source credible in general.

Format your response as an actionable checklist using markdown."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def analyze_deepfake_signs(description, gemini_api_key):
    """
    Analyzes a description of media for potential deepfake indicators
    """
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Based on this description of an image or video, analyze potential deepfake indicators:

Description: {description}

Identify:
1. Common deepfake red flags that may be present (unnatural blinking, lighting inconsistencies, odd facial features, background anomalies, etc.)
2. What specific details should be examined more closely
3. Verification techniques that could be used (reverse image search, checking metadata, finding original source)
4. A "authenticity confidence score" from 1-10 (1=likely fake, 10=likely authentic)
5. What additional information would help determine authenticity

Explain your reasoning in educational terms suitable for students learning to spot AI-generated content.

Format your response with clear sections using markdown."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def analyze_algorithm_impact(social_media_description, gemini_api_key):
    """
    Analyzes how social media algorithms might affect content visibility
    """
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Analyze how social media algorithms might handle this content:

Content description: {social_media_description}

Explain:
1. What factors would make algorithms promote or suppress this content
2. How engagement metrics (likes, shares, comments) would affect visibility
3. Potential filter bubble effects this could create
4. How the algorithm might personalize this differently for different users
5. Strategies to break out of algorithmic bubbles related to this topic

Use real examples and explain in terms students can understand.

Format your response with clear sections using markdown."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def check_copyright_fair_use(use_case, gemini_api_key):
    """
    Evaluates whether a use case might qualify as fair use
    """
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""Evaluate this use case for copyright fair use:

Use case: {use_case}

Analyze using the four factors of fair use:
1. Purpose and character of use (transformative? educational? commercial?)
2. Nature of the copyrighted work (creative vs. factual)
3. Amount and substantiality of portion used
4. Effect on the market value of the original

Provide:
- An assessment of each factor
- Whether this likely qualifies as fair use (with important disclaimers)
- Alternative approaches if it doesn't qualify
- Best practices for attribution and permission

Remember: This is educational analysis, not legal advice.

Format your response with clear sections using markdown."""
    
    try:
        response = model.generate_content(prompt)
        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }