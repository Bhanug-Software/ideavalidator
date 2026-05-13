# TOPIC 2: Use Case Selection - When to Use Agents (And When Not To)

## Quick Summary (1 sentence)
Use agents for problems that require thinking, research, and multiple steps to reach uncertain outcomes—use traditional code for problems with fixed rules, known inputs/outputs, and predictable solutions.

---

## The $10 Million Decision

**Hiring Manager Question:** "You used an AI agent here—why not just write code?"

**Bad Answer:** "Because AI agents are cool."

**Good Answer:** "Because the problem requires reasoning through uncertainty, multiple research steps, and handling unpredictable outcomes. Code is deterministic; this needs adaptive thinking."

**The Reality:** Companies make this wrong choice and waste 6 months building agents for problems that need 2 days of code.

---

## Decision Matrix: Agent vs Code

### **Use AGENT When:**

| Characteristic | Example | Why Agent? |
|---|---|---|
| **Unknown how to start** | "Validate a project idea" | Agent can research, think, decide approach |
| **Multiple possible paths** | "Decide if we should hire this person" | Different info sources, different reasoning paths |
| **Needs reasoning** | "Why is this project risky?" | Requires thinking, not lookup |
| **Output is subjective** | "Is this code review good?" | Needs judgment, not exact match |
| **Needs to learn from feedback** | "Get better at reviewing code over time" | Agent can improve through feedback loops |
| **Uncertain success criteria** | "Generate innovative product ideas" | No single "right" answer |

### **Use CODE When:**

| Characteristic | Example | Why Code? |
|---|---|---|
| **Fixed rules** | "Convert Celsius to Fahrenheit" | Formula doesn't change |
| **Deterministic output** | "Sort this list of numbers" | Same input = same output always |
| **Just a lookup** | "Get user profile by ID" | Database query, not reasoning |
| **Performance critical** | "Process 1M requests/second" | Code is 1000x faster than agent |
| **Simple logic** | "If age > 18, allow access" | If/else statement, not AI needed |
| **Already solved perfectly** | "Validate email format" | Regex exists, agents add no value |

---

## The Acid Test: 3 Questions

Before building an agent, ask yourself:

### **Question 1: Does thinking help?**
- **Agent:** "Should we launch this product in Japan?" (needs reasoning about market, culture, regulations)
- **Code:** "Is this email valid?" (no thinking needed)

### **Question 2: Are there multiple valid approaches?**
- **Agent:** "How should we handle this customer complaint?" (could apologize, offer refund, escalate—multiple valid paths)
- **Code:** "Calculate invoice total" (one correct way)

### **Question 3: Does uncertainty exist?**
- **Agent:** "Will this startup succeed?" (inherently uncertain, needs research and judgment)
- **Code:** "Does user exist in database?" (certain—yes or no)

**If all 3 = YES → Agent. If any = NO → Code.**

---

## Real Example: Your Validator Agent

### **Why Your Project Is Perfect for an Agent:**

```
Question 1: Does thinking help?
→ YES - Analyzing "Netflix clone" needs reasoning about market saturation,
  licensing costs, competitive advantage

Question 2: Are there multiple valid approaches?
→ YES - Could analyze market, tech stack, capital, licensing, team expertise
  in different orders and ways

Question 3: Does uncertainty exist?
→ YES - No "formula" for startup viability. It's inherently uncertain.

Result: ✅ AGENT IS CORRECT CHOICE
```

### **What Your Agent Does That Code Can't:**

```python
# CODE APPROACH (❌ Fails)
if idea == "Netflix clone":
    return {"score": 22, "reason": "Netflix exists"}

# AGENT APPROACH (✅ Works)
- Understands the nuance of "Netflix clone"
- Researches market saturation (Netflix, Disney+, Hulu, Amazon Prime)
- Thinks about licensing costs (billions for content)
- Analyzes competitive advantage (none if just copying)
- Produces thoughtful reasoning (not just "Netflix exists")
- Could handle "Netflix clone + unique anime focus" differently
  (different analysis = lower risk)
```

---

## The Cost Calculation: When Is an Agent Worth It?

### **Agent Costs:**
- API calls: ~$0.01-0.10 per request (depends on prompt length)
- Development time: 1-2 weeks to build properly
- Maintenance: Needs logging, error handling, monitoring
- Latency: 1-3 seconds per request (vs code: 1ms)

### **When These Costs Make Sense:**

| Scenario | Agent Cost | Value | Worth It? |
|---|---|---|---|
| Internal tool used 10x/year | $0.50/year | Saves 1 developer-day of thinking | ❌ NO (overkill) |
| Product feature, 10k users/month | $100/month | Improves user satisfaction | ✅ YES |
| Complex decision that prevents bad launches | $1/request | Prevents $100k loss | ✅ YES |
| Prototype to test if idea works | $10 total | Learn if concept is viable | ✅ YES |

---

## The 5 Classic Mistakes in Use Case Selection

### **Mistake 1: Building an Agent for a Lookup Problem**

```python
# ❌ WRONG - Agent when code suffices
class RestaurantFinder:
    def find_restaurant(self, cuisine: str):
        prompt = f"""Find me a {cuisine} restaurant"""
        response = client.messages.create(...)  # Costs $0.05, takes 2 seconds
        return parse(response)

# ✅ RIGHT - Just query the database
def find_restaurant(cuisine: str):
    return db.query(Restaurant).filter(cuisine=cuisine)  # Costs nothing, takes 0.001s
```

**Why it's wrong:** Database has the answer. Asking Claude to "find" it is like asking a consultant to Google something.

---

### **Mistake 2: Building an Agent for Simple Logic**

```python
# ❌ WRONG - Agent when if/else works
class AgeVerifier:
    def can_vote(self, age: int):
        prompt = f"""Can someone aged {age} vote? Answer 'yes' or 'no'"""
        response = client.messages.create(...)
        return "yes" in response.lower()

# ✅ RIGHT - Simple code
def can_vote(age: int):
    return age >= 18
```

**Why it's wrong:** Voting age is a fixed rule. No reasoning needed. Agent adds 99% overhead for 0% value.

---

### **Mistake 3: Building an Agent for a Known Formula**

```python
# ❌ WRONG - Agent for math problem
class InvoiceCalculator:
    def calculate_total(self, items):
        prompt = f"""Calculate total cost of: {items}"""
        response = client.messages.create(...)
        return parse_number(response)

# ✅ RIGHT - Use code
def calculate_total(items):
    return sum(item.price * item.quantity for item in items)
```

**Why it's wrong:** Math has exact answers. Asking an LLM "1+1" when you already know it's 2 is absurd.

---

### **Mistake 4: Building an Agent for High-Volume Operations**

```python
# ❌ WRONG - Agent for high throughput
class EmailValidator:
    def validate(self, email: str):
        prompt = f"""Is {email} a valid email?"""
        response = client.messages.create(...)  # $0.05 per email
        return is_valid(response)

# ✅ RIGHT - Use regex
import re
def validate(email: str):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)
```

**Why it's wrong:** Validating 1M emails costs $50k and takes hours. Regex costs $0 and takes seconds.

---

### **Mistake 5: Building an Agent for Something That Needs Real Data Access**

```python
# ❌ WRONG - Agent without tools
class CustomerAnalyzer:
    def analyze_customer(self, customer_id: str):
        prompt = f"""Analyze customer {customer_id}. Do they seem loyal?"""
        response = client.messages.create(...)
        # Claude has NO idea who customer 123 is!
        return response

# ✅ RIGHT - Agent WITH tools
class CustomerAnalyzer:
    def analyze_customer(self, customer_id: str):
        # First, fetch actual customer data
        customer = db.get_customer(customer_id)
        orders = db.get_orders(customer_id)
        payments = db.get_payments(customer_id)

        # THEN analyze with context
        prompt = f"""Analyze this customer:
        Name: {customer.name}
        Orders: {len(orders)} (total: ${sum(o.amount for o in orders)})
        Payment history: {payments}
        Are they loyal?"""

        response = client.messages.create(...)
        return response
```

**Why it's wrong:** Claude doesn't know your data. An agent needs tools to fetch data before it can reason about it.

---

## Decision Tree: Should I Build This As an Agent?

```
START: "I want to build feature X"
  │
  ├─ Does it require thinking/reasoning/judgment?
  │  ├─ NO → Use CODE ✅
  │  └─ YES → Continue
  │
  ├─ Are there multiple valid solutions/approaches?
  │  ├─ NO → Use CODE ✅
  │  └─ YES → Continue
  │
  ├─ Is the success criteria uncertain?
  │  ├─ NO → Use CODE ✅
  │  └─ YES → Continue
  │
  ├─ Will the agent need external tools/data?
  │  ├─ NO → Agent works, but maybe CODE is simpler ⚖️
  │  └─ YES → Agent is probably RIGHT ✅
  │
  └─ Does this provide genuine value (vs just being cool)?
     ├─ NO → Use CODE ✅
     └─ YES → BUILD AGENT 🚀
```

---

## Your Validator Agent: Why It's the Right Choice

### **How It Passes All Tests:**

1. **Requires thinking?** ✅ YES
   - Can't just match patterns ("Netflix exists" = bad analysis)
   - Needs to reason about market, tech, capital, risks

2. **Multiple approaches?** ✅ YES
   - Could focus on market viability, tech feasibility, financial risk, etc.
   - Different ideas need different analysis approaches

3. **Uncertain outcome?** ✅ YES
   - No formula for startup success
   - Different insights from same data

4. **Needs tools?** ⏳ FUTURE (Topic 6)
   - Currently: Claude's training data is the "tool"
   - Later: Will add search_market(), lookup_company(), etc.

5. **Provides real value?** ✅ YES
   - Saves founder weeks of research
   - Prevents launching doomed projects
   - Improves decision-making quality

---

## When to Add Tools to Your Agent

### **Without Tools (Current):**
```python
# Agent only uses Claude's training knowledge
prompt = "Is a Netflix clone viable?"
response = claude.analyze(prompt)
```

### **With Tools (Topic 6):**
```python
# Agent can fetch real data
prompt = """Is a Netflix clone viable?

Real market data:
- Market size: {get_market_size('streaming')}
- Competitors: {list_competitors('streaming')}
- Content licensing cost: {get_licensing_cost()}
- Average startup capital for this: {research_capital()}
"""
response = claude.analyze(prompt)
```

**Tools make agents 10x more powerful because they combine thinking with real information.**

---

## Quick Reference: Agent Decision Framework

**When I see a new problem, I ask:**

1. **Is the answer in code (formula, rules, lookup)?** → CODE
2. **Does it need thinking?** → AGENT
3. **Does it need research?** → AGENT + TOOLS
4. **Does it need learning from feedback?** → AGENT + MEMORY
5. **Does it need human approval?** → AGENT + HUMAN REVIEW

---

## Why This Matters for Your Career

✅ **Shows you understand when to use the right tool**
- Not every problem needs AI
- Not every AI problem needs agents
- Hiring managers: "This person won't over-engineer"

✅ **Prevents wasting time and money**
- No agents for code problems = 10x faster development
- Agents for thinking problems = 10x better results
- You make the right choice the first time

✅ **Foundation for Topics 3-14**
- Topic 3: Prompt Engineering (only matters for agent use cases)
- Topic 6: Tools (adds power to reasoning agents)
- Topic 8: RAG (better data for thinking agents)
- All future topics assume you chose the right tool first

---

## To Remember This Forever

🎯 **Real story from your project:**

**Wrong approach:** "Netflix clone? Code says: Netflix exists. Don't build it. Score: 0."
- ❌ Too simple
- ❌ No reasoning
- ❌ Doesn't work for different ideas

**Right approach (your agent):** Analyzes market saturation, licensing costs, competitive advantage, team viability, capital requirements—then produces Score: 22 with detailed reasoning.
- ✅ Shows thinking
- ✅ Handles different ideas differently
- ✅ Provides actionable insights

**That's why it needed to be an agent.** 🚀

---

## Topics This Connects To

- **Topic 1:** ✅ Completed - What agents are
- **Topic 2:** 📍 YOU ARE HERE - When to use them
- **Topic 3:** Prompt Engineering (craft better prompts for agents)
- **Topic 4:** Structured Outputs (get consistent JSON from agents)
- **Topic 5:** Cost Optimization (don't waste money on wrong tools)
- **Topic 6:** Tools (make agents more powerful)
- **Topic 8:** RAG (give agents knowledge)
- **Topic 9:** Memory (agents remember feedback)

---

## Next: Apply This Knowledge

In Topic 3, you'll learn **Prompt Engineering**—how to give your agent better instructions so it produces better analysis.

But first, reflect on this question:

**"Your Netflix clone analyzer works. But could you solve this with 100 lines of code instead? If yes, should you?"**

(Answer: No—because the human needs to understand *why*, not just get a score.)
