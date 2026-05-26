from loguru import logger
from app.utils.config import client

class InputValidator:
    """Validate user input before sending to Claude"""

    def __init__(self):
        self.MIN_LENGTH = 20
        self.MIN_WORDS = 5

    def validate_basic(self, project_idea: str) -> tuple[bool, str]:
        """Check basic requirements: length and word count"""

        # Remove extra spaces
        cleaned = project_idea.strip()

        # Check 1: Minimum length
        if len(cleaned) < self.MIN_LENGTH:
            message = f"Too short! Minimum {self.MIN_LENGTH} characters needed"
            logger.warning(f"❌ Length check failed: {len(cleaned)} chars")
            return False, message

        # Check 2: Minimum words
        word_count = len(cleaned.split())
        if word_count < self.MIN_WORDS:
            message = f"Too vague! Minimum {self.MIN_WORDS} words needed"
            logger.warning(f"❌ Word count failed: {word_count} words")
            return False, message

        # All checks passed
        logger.info(f"✅ Basic validation passed: {word_count} words, {len(cleaned)} chars")
        return True, "Input looks good"

    def validate_relevance(self, project_idea: str) -> tuple[bool, str]:
        """Check if input is actually a project idea (has project keywords)"""

        # Keywords that indicate a project idea
        project_keywords = [
            "app", "product", "service", "startup",
            "platform", "website", "tool", "software",
            "build", "create", "develop", "launch",
            "solution", "system", "feature", "api"
        ]

        text_lower = project_idea.lower()

        # Check if any keyword exists
        found_keywords = [kw for kw in project_keywords if kw in text_lower]

        if found_keywords:
            logger.info(f"✅ Relevance check passed: Found keywords: {found_keywords}")
            return True, "This looks like a project idea"

        logger.warning(f"❌ Relevance check failed: No project keywords found")
        return False, "This doesn't seem like a project idea"

    def validate_semantic(self, project_idea: str) -> tuple[bool, str]:
        """Use Claude to check if this is a project idea (fallback check)"""

        logger.info("🔍 Running semantic check with Claude...")

        prompt = f"""Is this a project idea? Answer YES or NO only.

A project idea describes building something:
- App, product, service, platform, website, tool, software, etc.
- NOT general questions like "what's 2+2" or "how to cook pasta"

Text to check: "{project_idea}"

Answer only YES or NO:"""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.upper().strip()

            if "YES" in response:
                logger.info("✅ Claude confirmed: This is a project idea")
                return True, "Claude confirmed this is a project idea"
            else:
                logger.warning("❌ Claude says: This doesn't seem like a project idea")
                return False, "This doesn't appear to be a project idea"

        except Exception as e:
            logger.error(f"Semantic check failed: {e}")
            return False, "Error checking input"

    def validate_complete(self, project_idea: str) -> tuple[bool, str]:
        """Run all validation checks in smart order"""

        logger.info("=" * 50)
        logger.info("Starting complete validation...")

        # STEP 1: Basic validation (length & words)
        is_valid, message = self.validate_basic(project_idea)
        if not is_valid:
            logger.error(f"❌ Validation failed at STEP 1: {message}")
            return False, message

        # STEP 2: Keyword check (relevance)
        is_valid, message = self.validate_relevance(project_idea)
        if is_valid:
            logger.info(f"✅ Validation passed at STEP 2 (keywords found)")
            return True, "Input validated successfully"

        # STEP 3: Claude semantic check (only if keywords failed)
        logger.info("Keywords not found, running Claude verification...")
        is_valid, message = self.validate_semantic(project_idea)

        if is_valid:
            logger.info(f"✅ Validation passed at STEP 3 (Claude approved)")
            return True, "Input validated successfully"
        else:
            logger.error(f"❌ Validation failed at STEP 3: {message}")
            return False, message

input_validator = InputValidator()
