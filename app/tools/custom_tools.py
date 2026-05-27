"""
Custom Tools for ideavalidator
Email sending tool using Gmail API with OAuth 2.0
"""

import base64
import os
import pickle
from datetime import datetime
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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
    """
    Convert plain text analysis to formatted HTML with styling
    """
    html_template = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 700px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .score-box {{
                background-color: #f0f4ff;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .score-value {{
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }}
            .recommendation {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            h2 {{
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
                margin-top: 25px;
                font-size: 18px;
            }}
            .section {{
                margin: 20px 0;
            }}
            .section p {{
                margin: 10px 0;
                text-align: justify;
            }}
            ul {{
                margin: 15px 0;
                padding-left: 20px;
            }}
            li {{
                margin: 8px 0;
                line-height: 1.5;
            }}
            .do-item {{
                color: #28a745;
            }}
            .dont-item {{
                color: #dc3545;
            }}
            .footer {{
                background-color: #f9f9f9;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #999;
                border-top: 1px solid #ddd;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Project Analysis Results</h1>
                <p>Your AI-powered project validation report</p>
            </div>

            <div class="content">
                <div class="score-box">
                    <div>Overall Score</div>
                    <div class="score-value">72 / 100</div>
                </div>

                <div class="recommendation">
                    <strong>Recommendation:</strong> Consider changes
                </div>

                <div class="section">
                    <h2>🎯 Market Opportunity</h2>
                    <p>There is real demand for personal productivity and activity tracking tools. Millions of people — students, remote workers, freelancers, and professionals — want to understand how they spend their time each day.</p>
                    <p>Apps like Notion, Todoist, and RescueTime already do parts of this. So the market exists, but it is crowded. Your edge needs to be the AI part — making it smarter and more personal than what already exists.</p>
                    <p><strong>Key insight:</strong> If you target a specific group (like freelancers or students), your chances of standing out go up a lot.</p>
                </div>

                <div class="section">
                    <h2>⚙️ Feasibility</h2>
                    <p>This is moderately hard to build. It is not impossible, but it has multiple moving parts — tracking activities, using AI to process them, and then showing them in clear visual dashboards.</p>
                    <ul>
                        <li><strong>Basic version:</strong> 3-6 months with small team</li>
                        <li><strong>Polished product:</strong> 9-12 months</li>
                        <li><strong>Cost:</strong> $10,000 to $50,000+ depending on complexity</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>📦 Resources Required</h2>
                    <p>You will need:</p>
                    <ul>
                        <li>Full-stack developer (web or mobile)</li>
                        <li>AI/Machine learning engineer</li>
                        <li>UI/UX designer</li>
                        <li>User researcher/product manager</li>
                    </ul>
                    <p><strong>Budget for MVP:</strong> $15,000–$40,000 (less with free AI tools like OpenAI APIs)</p>
                </div>

                <div class="section">
                    <h2>✅ DO's</h2>
                    <ul>
                        <li class="do-item">Start with a clear focus — pick ONE type of user before trying to serve everyone</li>
                        <li class="do-item">Build a simple version first (tracking + display), then add AI</li>
                        <li class="do-item">Talk to 20–30 real potential users BEFORE coding</li>
                        <li class="do-item">Use existing AI tools (OpenAI, Google AI) instead of building from scratch</li>
                        <li class="do-item">Make dashboard visuals extremely simple and beautiful</li>
                        <li class="do-item">Add a "daily summary" feature with AI-powered recaps</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>❌ DON'Ts</h2>
                    <ul>
                        <li class="dont-item">Don't track every activity from day one — start small</li>
                        <li class="dont-item">Don't copy existing apps exactly — find your unique angle</li>
                        <li class="dont-item">Don't make onboarding complicated — 5 minutes max</li>
                        <li class="dont-item">Don't ignore privacy — be transparent about data use</li>
                        <li class="dont-item">Don't build for months without user feedback</li>
                        <li class="dont-item">Don't overcrowd the dashboard — keep it simple</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>⚠️ Key Risks & Solutions</h2>
                    <ul>
                        <li><strong>Privacy concerns:</strong> Be transparent, offer local storage, get GDPR compliance</li>
                        <li><strong>Crowded market:</strong> Focus on niche, make AI recommendations truly personal</li>
                        <li><strong>Low engagement:</strong> Add daily nudges, streaks, and helpful insights</li>
                        <li><strong>Poor AI insights:</strong> Start with rule-based suggestions, improve over time</li>
                        <li><strong>High AI costs:</strong> Use affordable APIs, run heavy processing only when needed</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>📅 Timeline (10-12 months)</h2>
                    <ul>
                        <li><strong>Weeks 1-4:</strong> Research phase, talk to users, sketch ideas</li>
                        <li><strong>Months 2-3:</strong> Build basic version (activity tracking, basic charts)</li>
                        <li><strong>Months 4-5:</strong> Add AI features (summaries, pattern detection)</li>
                        <li><strong>Month 6:</strong> Test with 10-20 real users</li>
                        <li><strong>Months 7-9:</strong> Polish, improve visuals, fix bugs</li>
                        <li><strong>Months 10-12:</strong> Launch publicly, gather feedback</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>🚀 Next Step</h2>
                    <p><strong>This week:</strong> Write down 5 questions and go ask 10 real people how they currently track their daily activities and what frustrates them most. Their answers will tell you if your idea solves a real problem.</p>
                </div>

                <div class="section">
                    <h2>⚡ Changes Required</h2>
                    <p>Narrow your focus — instead of "all daily activities for all users," pick one specific group like freelancers tracking work hours or students tracking study habits.</p>
                </div>
            </div>

            <div class="footer">
                <p>Generated by AI Project Idea Validator | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
