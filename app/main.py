from app.agent.validator_agent import ValidatorAgent
from app.utils.logger import logger

def main():
    """Test the validator agent"""

    # Create agent
    agent = ValidatorAgent()

    # Test with a project idea
    project_idea = "I want to build a Netflix clone"

    # Step 1: Starting validation
    print("\n" + "=" * 80)
    print("STEP 1: STARTING VALIDATION")
    print("=" * 80)
    print(f"Project Idea: {project_idea}\n")

    # Step 2: Sending to Claude
    print("=" * 80)
    print("STEP 2: SENDING PROJECT IDEA TO CLAUDE")
    print("=" * 80)
    print("Analyzing project idea...\n")

    # Validate the idea
    result = agent.validate_idea(project_idea)

    # Step 3: Raw response from Claude
    print("\n" + "=" * 80)
    print("STEP 3: RAW RESPONSE FROM CLAUDE")
    print("=" * 80)
    print(result['raw_response'])
    print()

    # Step 4: Parsed results
    print("=" * 80)
    print("STEP 4: PARSED RESULTS")
    print("=" * 80)
    print(f"\n📊 Viability Score: {result['score']}/100")
    print(f"\n💡 Reasoning:\n{result['reasoning']}")
    print(f"\n✅ Recommendation: {result['recommendation']}")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
