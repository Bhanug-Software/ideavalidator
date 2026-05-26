from loguru import logger

class UserGuidance:
    """Show users how to input project ideas"""

    @staticmethod
    def show_format():
        """Display input format to user"""

        guide = """
╔════════════════════════════════════════════════════════════════╗
║       PROJECT IDEA VALIDATOR - INPUT GUIDE                     ║
╚════════════════════════════════════════════════════════════════╝

📝 DESCRIBE YOUR PROJECT IDEA

Your idea should answer:
  • What is it? (mobile app, web platform, service, etc.)
  • What problem does it solve?
  • Who would use it?

✅ GOOD EXAMPLES:
  1. "A mobile app that helps busy professionals track daily
      expenses automatically by scanning receipts with AI"

  2. "A marketplace platform connecting freelance designers
      with small businesses who need branding help"

❌ BAD EXAMPLES (too vague):
  • "An app"
  • "A startup idea"
  • "Something cool for people"

📌 REQUIREMENTS:
  • Minimum 20 characters
  • At least 5 words
  • Describe what, why, and who

Now enter YOUR project idea below:
════════════════════════════════════════════════════════════════
"""
        print(guide)
        logger.info("User guidance displayed")

user_guidance = UserGuidance()
