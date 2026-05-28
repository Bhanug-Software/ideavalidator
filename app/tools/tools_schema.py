"""
Tool Schema Definitions
Describes all available tools to Claude in JSON format
"""

TOOLS_SCHEMA = [
    {
        "name": "send_email_to_user",
        "description": "Send project analysis results to user's email address",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_address": {
                    "type": "string",
                    "description": "User's email address to send analysis to"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Complete analysis results to send in email body"
                }
            },
            "required": ["email_address", "subject", "body"]
        }
    },
    {
        "name": "tavily_search",
        "description": "Search the web for real-time information about markets, competitors, trends, and statistics",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'AI market size 2026', 'competitor analysis for SaaS', 'blockchain adoption trends')"
                }
            },
            "required": ["query"]
        }
    }
]
