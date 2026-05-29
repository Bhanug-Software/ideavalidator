"""
Custom Tools for ideavalidator
Email sending tool using Gmail API with OAuth 2.0
Web search tool using Tavily API
"""

import base64
import os
import pickle
import re
import time
from datetime import datetime
from email.mime.text import MIMEText
from urllib.parse import quote_plus
from functools import wraps
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tavily import TavilyClient
from dotenv import load_dotenv
import googlemaps

# Load environment variables from .env file
load_dotenv()


def retry_with_backoff(max_retries=3, initial_delay=1):
    """Decorator for retrying failed API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            return None
        return wrapper
    return decorator


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """
    Authenticate with Gmail API using OAuth 2.0
    Returns Gmail service object
    """

    credentials = None
    credentials_path = "app/credentials/oauth_credentials.json"
    token_path = "app/credentials/token.json"

    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token_file:
            credentials = pickle.load(token_file)

    # If no valid credentials, get new ones
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # Open browser for user to authorize
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path,
                SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save token for future use
        with open(token_path, 'wb') as token_file:
            pickle.dump(credentials, token_file)

    # Build and return Gmail service
    service = build('gmail', 'v1', credentials=credentials)
    return service


def format_analysis_as_html(body):
    """Convert plain text analysis to formatted HTML email"""

    # Map section keys to display labels and icons
    sections = [
        ("IDEA SUMMARY",        "💡 Idea Summary"),
        ("PROBLEM STATEMENT",   "🎯 Problem Statement"),
        ("TARGET AUDIENCE",     "👥 Target Audience"),
        ("MARKET VALIDATION",   "📊 Market Validation"),
        ("COMPETITOR ANALYSIS", "🔍 Competitor Analysis"),
        ("MVP RECOMMENDATION",  "🚀 MVP Recommendation"),
        ("RISK ANALYSIS",       "⚠️ Risk Analysis"),
        ("FINAL RECOMMENDATION","✅ Final Recommendation"),
    ]

    # Build HTML sections from the plain text body
    sections_html = ""
    for i, (key, label) in enumerate(sections):
        # Find content between this key and the next one
        next_key = sections[i + 1][0] if i + 1 < len(sections) else None
        if next_key:
            pattern = rf'{re.escape(key)}:\s*(.+?)(?={re.escape(next_key)}:)'
        else:
            pattern = rf'{re.escape(key)}:\s*(.+?)$'

        match = re.search(pattern, body, re.DOTALL)
        content = match.group(1).strip() if match else ""

        # Convert newlines to <br> for HTML
        content_html = content.replace('\n', '<br>')

        sections_html += f"""
        <div class="section">
            <h2>{label}</h2>
            <p>{content_html}</p>
        </div>
        <hr>
        """

    html_template = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.7; color: #333; background: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ max-width: 700px; margin: 0 auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px 20px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 26px; }}
            .content {{ padding: 30px 25px; }}
            .section {{ margin: 20px 0; }}
            h2 {{ color: #667eea; font-size: 17px; border-bottom: 2px solid #667eea; padding-bottom: 6px; margin-bottom: 10px; }}
            p {{ margin: 0; font-size: 15px; }}
            hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
            .footer {{ background: #f9f9f9; padding: 15px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Project Analysis Results</h1>
                <p>Your AI-powered project validation report</p>
            </div>
            <div class="content">
                {sections_html}
            </div>
            <div class="footer">
                Generated by AI Project Idea Validator | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    return html_template


def send_email_to_user(email_address, subject, body):
    """
    Send project analysis results to user's email using Gmail API with OAuth 2.0

    Parameters:
    -----------
    email_address : str
        Recipient email address
    subject : str
        Email subject line
    body : str
        Email body content (analysis results)

    Returns:
    --------
    str
        Confirmation message
    """

    try:
        # Check if credentials file exists
        credentials_path = "app/credentials/oauth_credentials.json"

        if not os.path.exists(credentials_path):
            return f"❌ Error: OAuth credentials file not found at {credentials_path}"

        # Get Gmail service (with OAuth 2.0 authentication)
        service = get_gmail_service()

        # Convert analysis to HTML format
        html_body = format_analysis_as_html(body)

        # Create email message with HTML content
        message = MIMEText(html_body, 'html')
        message['to'] = email_address
        message['subject'] = subject

        # Encode message in base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email
        send_message = {'raw': raw_message}
        result = service.users().messages().send(
            userId='me',
            body=send_message
        ).execute()

        # Get sender email
        profile = service.users().getProfile(userId='me').execute()
        sender_email = profile.get('emailAddress', 'your-email@gmail.com')

        # Return success message
        confirmation = f"""✅ Email sent successfully!

To: {email_address}
From: {sender_email}
Subject: {subject}
Message ID: {result.get('id')}"""

        return confirmation

    except HttpError as error:
        return f"❌ Gmail API Error: {error}"
    except FileNotFoundError:
        return f"❌ Error: Credentials file not found"
    except Exception as error:
        return f"❌ Error sending email: {str(error)}"


@retry_with_backoff(max_retries=3, initial_delay=1)
def tavily_search(query):
    """
    Search the web using Tavily API for real-time information

    Parameters:
    -----------
    query : str
        Search query (e.g., "AI market size 2026")

    Returns:
    --------
    str
        Search results formatted as readable text
    """

    try:
        # Get API key from environment variable
        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            return "❌ Error: TAVILY_API_KEY not found in .env file"

        # Initialize Tavily client with 30 second timeout
        client = TavilyClient(api_key=api_key)

        # Search the web (with implicit timeout from client)
        response = client.search(
            query=query,
            max_results=5,  # Return top 5 results
            include_answer=True
        )

        # Format results
        if response.get("answer"):
            search_results = f"""Search Results for: "{query}"

            Answer: {response['answer']}

            Sources:
            """

            for i, result in enumerate(response.get("results", []), 1):
                search_results += f"\n{i}. {result['title']}\n   URL: {result['url']}\n   {result['content'][:150]}...\n"

            return search_results

        else:
            return f"❌ No results found for: {query}"

    except Exception as error:
        return f"❌ Error searching web: {str(error)}"


@retry_with_backoff(max_retries=3, initial_delay=1)
def google_places_search(zipcode, business_type):
    """
    Search for business locations in a specific zipcode using Google Places API

    Parameters:
    -----------
    zipcode : str
        US zipcode to search for businesses (e.g., '10001')
    business_type : str
        Type of business to search for (e.g., 'coffee shop', 'restaurant')

    Returns:
    --------
    str
        Formatted list of businesses found with details
    """

    try:
        # Get API key from environment variable
        api_key = os.getenv("GOOGLE_PLACES_API_KEY")

        if not api_key:
            return "❌ Error: GOOGLE_PLACES_API_KEY not found in .env file"

        # Initialize Google Maps client with 30 second timeout
        gmaps = googlemaps.Client(key=api_key, timeout=30)

        # Get coordinates from zipcode using geocoding
        try:
            geocode_result = gmaps.geocode(address=zipcode)
            if not geocode_result:
                return f"❌ Error: Could not find coordinates for zipcode {zipcode}"

            location = geocode_result[0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
        except Exception as e:
            return f"❌ Error geocoding zipcode: {str(e)}"

        # Search for places near the zipcode center
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,  # 5km radius search
            keyword=business_type,
            type='establishment'
        )

        if not places_result.get('results'):
            return f"❌ No {business_type} businesses found in zipcode {zipcode}"

        # Format results
        search_results = f"Businesses matching '{business_type}' in zipcode {zipcode}:\n\n"

        for i, place in enumerate(places_result.get('results', [])[:10], 1):  # Top 10 results
            name = place.get('name', 'N/A')
            address = place.get('vicinity', 'Address not available')
            rating = place.get('rating', 'No rating')
            open_status = "Open" if place.get('opening_hours', {}).get('open_now') else "Closed"

            # Create Google Maps link using place name and address with proper URL encoding
            maps_link = f"https://www.google.com/maps/search/{quote_plus(name)}+{quote_plus(address)}"

            search_results += f"{i}. {name}\n"
            search_results += f"   📍 Address: {address}\n"
            search_results += f"   ⭐ Rating: {rating}/5.0\n"
            search_results += f"   🔗 Google Maps: {maps_link}\n"
            search_results += f"   Status: {open_status}\n\n"

        return search_results

    except Exception as error:
        return f"❌ Error searching Google Places: {str(error)}"
