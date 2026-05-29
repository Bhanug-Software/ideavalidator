"""Track API costs for Anthropic Claude"""

class CostTracker:
    """Calculate and track API usage costs"""

    # Anthropic pricing per 1 million tokens (as of 2026)
    CLAUDE_SONNET_INPUT_COST = 3.00  # $3 per 1M input tokens
    CLAUDE_SONNET_OUTPUT_COST = 15.00  # $15 per 1M output tokens

    # Third-party API pricing
    TAVILY_SEARCH_COST = 0.001  # $0.001 per search
    GOOGLE_PLACES_COST = 0.017  # $0.017 per search

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.claude_cost = 0.0
        self.tavily_cost = 0.0
        self.google_places_cost = 0.0
        self.requests = []
        self.tavily_searches = 0
        self.google_places_searches = 0

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage from a Claude API call"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * self.CLAUDE_SONNET_INPUT_COST
        output_cost = (output_tokens / 1_000_000) * self.CLAUDE_SONNET_OUTPUT_COST
        call_cost = input_cost + output_cost

        self.claude_cost += call_cost
        self.total_cost += call_cost

        # Track individual requests
        self.requests.append({
            "type": "claude",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": call_cost
        })

        return call_cost

    def add_tavily_search(self):
        """Track a Tavily search API call"""
        self.tavily_searches += 1
        self.tavily_cost += self.TAVILY_SEARCH_COST
        self.total_cost += self.TAVILY_SEARCH_COST
        self.requests.append({
            "type": "tavily",
            "cost": self.TAVILY_SEARCH_COST
        })

    def add_google_places_search(self):
        """Track a Google Places API call"""
        self.google_places_searches += 1
        self.google_places_cost += self.GOOGLE_PLACES_COST
        self.total_cost += self.GOOGLE_PLACES_COST
        self.requests.append({
            "type": "google_places",
            "cost": self.GOOGLE_PLACES_COST
        })

    def get_summary(self) -> dict:
        """Get cost summary"""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "claude_cost": round(self.claude_cost, 4),
            "tavily_cost": round(self.tavily_cost, 4),
            "google_places_cost": round(self.google_places_cost, 4),
            "total_cost": round(self.total_cost, 4),
            "request_count": len(self.requests),
            "avg_cost_per_request": round(self.total_cost / len(self.requests), 4) if self.requests else 0
        }

    def format_cost(self, cost: float) -> str:
        """Format cost nicely"""
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 1.0:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"

    def print_summary(self):
        """Print cost summary nicely"""
        summary = self.get_summary()
        print("\n" + "=" * 70)
        print("💰 COST SUMMARY")
        print("=" * 70)
        print(f"Input Tokens:        {summary['total_input_tokens']:,}")
        print(f"Output Tokens:       {summary['total_output_tokens']:,}")
        print(f"Total Tokens:        {summary['total_tokens']:,}")
        print(f"\nCost Breakdown:")
        print(f"  Claude API:        {self.format_cost(summary['claude_cost'])}")
        if self.tavily_searches > 0:
            print(f"  Tavily Searches:   {self.format_cost(summary['tavily_cost'])} ({self.tavily_searches} searches)")
        if self.google_places_searches > 0:
            print(f"  Google Places:     {self.format_cost(summary['google_places_cost'])} ({self.google_places_searches} searches)")
        print(f"\nTotal Cost:          {self.format_cost(summary['total_cost'])}")
        print(f"Requests:            {summary['request_count']}")
        print(f"Avg Cost/Request:    {self.format_cost(summary['avg_cost_per_request'])}")
        print("=" * 70 + "\n")


# Global tracker instance
cost_tracker = CostTracker()
