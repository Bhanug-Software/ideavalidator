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
    }
]
