#!/usr/bin/env python
"""Generate Mermaid diagram of LangGraph workflow"""

from app.agent.validator_agent import ValidatorAgent

# Create agent
agent = ValidatorAgent()

# Get Mermaid diagram
try:
    mermaid_diagram = agent.workflow.get_graph().draw_mermaid()

    print("\n" + "="*70)
    print("MERMAID DIAGRAM (Copy to mermaid.live to visualize)")
    print("="*70 + "\n")
    print(mermaid_diagram)

    # Save to file
    with open("workflow_diagram.md", "w") as f:
        f.write("# LangGraph Workflow Diagram\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_diagram)
        f.write("\n```\n")

    print("\n" + "="*70)
    print("Saved to: workflow_diagram.md")
    print("="*70)

except Exception as e:
    print(f"Error generating Mermaid diagram: {e}")
