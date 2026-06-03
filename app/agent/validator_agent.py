import re
from typing import TypedDict, Any
from concurrent.futures import ThreadPoolExecutor
from langgraph.graph import StateGraph, END
from app.utils.config import client, MODEL, MAX_TOKENS
from app.utils.logger import logger
from app.utils.input_validator import input_validator
from app.utils.output_validator import ProjectAnalysis
from pydantic import ValidationError
from app.tools import custom_tools
from app.tools.tools_schema import TOOLS_SCHEMA
from langsmith import traceable
from langgraph.graph import START



# Define the workflow state
class AnalysisState(TypedDict):
    """State that flows through the LangGraph workflow"""
    project_idea: str
    messages: list
    response: Any
    response_text: str
    validation_error: bool
    error_message: str
    final_result: dict
    conversation_history: list


class ValidatorAgent:
    """AI Agent that validates project ideas using LangGraph workflow"""

    def __init__(self):
        """Initialize the agent with model config and build workflow"""
        self.model = MODEL
        self.max_tokens = MAX_TOKENS
        self.tools = TOOLS_SCHEMA
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the LangGraph workflow"""
        
        graph = StateGraph(AnalysisState)

        # Add workflow nodes (steps)
        graph.add_node("validate_input", self._node_validate_input)
        graph.add_node("call_claude", self._node_call_claude)
        graph.add_node("execute_tools", self._node_execute_tools)
        graph.add_node("parse_response", self._node_parse_response)

        # Add edges (connections)
        graph.add_edge(START, "validate_input")
        graph.add_edge("validate_input", "call_claude")
        graph.add_conditional_edges(
            "call_claude",
            self._should_execute_tools,
            {
                "execute": "execute_tools",
                "parse": "parse_response"
            }
        )
        graph.add_edge("execute_tools", "call_claude")
        graph.add_edge("parse_response", END)

        return graph.compile()

    @traceable(name="validate_input_node", tags=["validation", "node"])
    def _node_validate_input(self, state: AnalysisState) -> AnalysisState:
        """Node 1: Validate user input"""
        logger.info(f"→ Validating input...")
        logger.debug(f"  Project idea length: {len(state['project_idea'])} chars")

        try:
            is_valid, validation_message = input_validator.validate_complete(state["project_idea"])
            logger.debug(f"  Validation result: {is_valid}")

            if not is_valid:
                logger.warning(f"⚠️  Input validation failed: {validation_message}")
                return {
                    **state,
                    "validation_error": True,
                    "error_message": validation_message,
                    "final_result": {
                        "score": 0,
                        "reasoning": validation_message,
                        "recommendation": "Please provide a valid project idea",
                        "raw_response": validation_message,
                        "validation_failed": True
                    }
                }

            logger.info("✅ Input validated successfully, preparing prompt...")

            prompt = f"""You are an expert startup advisor validating a project idea.

Here's the idea: {state['project_idea']}

CRITICAL: Follow this exact sequence BEFORE writing your analysis:
1. FIRST: Check if user mentioned a zipcode or location. If yes, IMMEDIATELY use google_places_search with that zipcode and the business type.
2. THEN: Use tavily_search exactly 2 times:
- First search: find real competitors for this idea
- Second search: find current market size and demand for this idea

3. Only use send_email_to_user if the user explicitly asks to send results to their email.

IMPORTANT: When you find results from google_places_search, you MUST include them in your COMPETITOR_ANALYSIS section with their exact names, ratings, and Google Maps links.

Write in a casual, friendly tone - like advising a friend.
- Use regular dashes (-), NOT em dashes (—)
- Do NOT use markdown formatting (no **, no *, no ---, no ###)
- Plain text only

Format your response EXACTLY like this (keep every section, don't skip any):

IDEA_SUMMARY: [2-3 sentences describing what this idea is]

PROBLEM_STATEMENT: [What specific problem does this solve? Who feels this pain?]

TARGET_AUDIENCE: [Who exactly is this for? Age, role, situation - be specific]

MARKET_VALIDATION: [Real market size, demand signals, growth trends based on your search]

COMPETITOR_ANALYSIS: [List 3-5 real competitors found (including local ones from zipcode search), their ratings, and how this idea is different]

MVP_RECOMMENDATION: [What is the simplest version to build first? What features are must-haves vs nice-to-haves?]

RISK_ANALYSIS: [4-5 real risks with a short mitigation for each]

FINAL_RECOMMENDATION: [MUST be exactly one of: "Build it" OR "Don't build it" OR "Consider changes" - pick the one that best fits your analysis]"""

            logger.info("→ Sending prompt to Claude API with tools...")
            messages = [{"role": "user", "content": prompt}]

            return {**state, "messages": messages, "validation_error": False}

        except Exception as e:
            logger.error(f"❌ Input validation node failed: {str(e)}", exc_info=True)
            return {
                **state,
                "validation_error": True,
                "error_message": f"Validation error: {str(e)}",
                "final_result": {
                    "score": 0,
                    "reasoning": f"Validation Error: {str(e)}",
                    "recommendation": "Please try again",
                    "validation_failed": True
                }
            }

    @traceable(name="call_claude_node", tags=["claude", "node"])
    def _node_call_claude(self, state: AnalysisState) -> AnalysisState:
        """Node 2: Call Claude API"""
        logger.info(f"← Calling Claude API")
        logger.debug(f"  Messages: {len(state['messages'])}, Model: {self.model}")

        try:
            # Check if this is the final call (no more tools needed)
            is_final_call = len(state["messages"]) > 1 and state["messages"][-1].get("role") == "user"

            logger.debug(f"  Is final call: {is_final_call}")
            response_stream = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=TOOLS_SCHEMA,
                messages=state["messages"],
                stream=is_final_call
            )

            if is_final_call:
                # Stream mode - collect text as it arrives with error handling
                logger.info(f"→ Streaming analysis response...\n")
                response_text = ""
                stream_interrupted = False

                try:
                    for event in response_stream:
                        try:
                            if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                                chunk = event.delta.text
                                if chunk:  # Only add non-empty chunks
                                    print(chunk, end="", flush=True)
                                    response_text += chunk
                            elif event.type == "message_stop":
                                logger.debug(f"  Stream message_stop received")
                                break
                            elif event.type == "content_block_stop":
                                logger.debug(f"  Stream content_block_stop received")
                                continue
                        except AttributeError as e:
                            logger.warning(f"⚠️  Unexpected event structure: {str(e)}")
                            continue
                        except Exception as e:
                            logger.warning(f"⚠️  Error processing stream event: {str(e)}")
                            continue

                except StopIteration:
                    logger.warning(f"⚠️  Stream ended prematurely (StopIteration)")
                    stream_interrupted = True

                except Exception as stream_error:
                    logger.error(f"❌ Stream interrupted: {str(stream_error)}", exc_info=True)
                    stream_interrupted = True

                    # If we got some response before interruption, use it
                    if response_text:
                        logger.warning(f"⚠️  Using partial response ({len(response_text)} chars collected before interruption)")
                        print("\n[Stream interrupted - using partial response]\n")
                        return {**state, "response": None, "response_text": response_text}
                    else:
                        # No data collected at all
                        error_msg = f"Stream failed before any data collected: {str(stream_error)}"
                        logger.error(f"❌ {error_msg}")
                        return {
                            **state,
                            "validation_error": True,
                            "error_message": error_msg,
                            "final_result": {
                                "score": 0,
                                "reasoning": "Stream connection lost",
                                "recommendation": "Please try again",
                                "validation_failed": True
                            }
                        }

                print()  # New line after streaming

                if stream_interrupted and response_text:
                    logger.warning(f"⚠️  Streaming completed with interruption ({len(response_text)} chars collected)")
                else:
                    logger.info(f"← Streaming complete ({len(response_text)} chars)")

                # Validate we got meaningful response
                if not response_text or len(response_text.strip()) == 0:
                    logger.error(f"❌ Stream produced empty response")
                    return {
                        **state,
                        "validation_error": True,
                        "error_message": "Received empty response from Claude",
                        "final_result": {
                            "score": 0,
                            "reasoning": "Empty response received",
                            "recommendation": "Please try again",
                            "validation_failed": True
                        }
                    }

                return {**state, "response": None, "response_text": response_text}
            else:
                # Non-streaming mode
                logger.info(f"← Received response from Claude")
                logger.debug(f"  Response blocks: {len(response_stream.content)}")
                return {**state, "response": response_stream}

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            # Log specific error types
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.error(f"❌ Claude API timeout: {error_msg}", exc_info=True)
                recommendation = "Request timed out. Please try again."
            elif "rate_limit" in error_type.lower() or "overloaded" in error_msg.lower():
                logger.error(f"❌ Claude API rate limited: {error_msg}", exc_info=True)
                recommendation = "API rate limited. Please wait and try again."
            elif "authentication" in error_type.lower() or "unauthorized" in error_msg.lower():
                logger.error(f"❌ Claude API authentication failed: {error_msg}", exc_info=True)
                recommendation = "Authentication failed. Check API key."
            else:
                logger.error(f"❌ Claude API call failed ({error_type}): {error_msg}", exc_info=True)
                recommendation = "Please try again later"

            return {
                **state,
                "validation_error": True,
                "error_message": f"Claude API error: {error_msg}",
                "final_result": {
                    "score": 0,
                    "reasoning": f"API Error ({error_type}): {error_msg}",
                    "recommendation": recommendation,
                    "validation_failed": True
                }
            }

    def _should_execute_tools(self, state: AnalysisState) -> str:
        """Conditional logic: Should we execute tools or parse response?"""
        if state["response"] is None:
            # Streaming mode - response already collected, go to parse
            return "parse"

        # Non-streaming mode - check for tool calls
        tool_calls = [block for block in state["response"].content if block.type == "tool_use"]

        if not tool_calls:
            # No tools called, extract text and parse
            response_text = next(
                (block.text for block in state["response"].content if hasattr(block, "text")),
                ""
            )
            state["response_text"] = response_text
            return "parse"

        return "execute"

    @traceable(name="execute_tools_node", tags=["tools", "node"])
    def _node_execute_tools(self, state: AnalysisState) -> AnalysisState:
        """Node 3: Execute tools called by Claude"""
        logger.info(f"→ Executing tools...")
        logger.debug(f"  State keys: {state.keys()}")

        try:
            tool_calls = [block for block in state["response"].content if block.type == "tool_use"]
            logger.info(f"Claude requested {len(tool_calls)} tool call(s)")

            for i, tool in enumerate(tool_calls, 1):
                logger.debug(f"  {i}. {tool.name} (ID: {tool.id})")

            # Add Claude's response to messages
            messages = state["messages"] + [{"role": "assistant", "content": state["response"].content}]

            # Execute tools
            def run_tool(tool_call):
                logger.info(f"⚙️  Executing: {tool_call.name}")
                try:
                    result = self._execute_tool(tool_call.name, tool_call.input)
                    logger.info(f"✅ {tool_call.name} completed")
                    logger.debug(f"  Result length: {len(str(result))} chars")
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result
                    }
                except Exception as e:
                    logger.error(f"❌ Tool {tool_call.name} failed: {str(e)}", exc_info=True)
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": f"Error executing {tool_call.name}: {str(e)}"
                    }

            tool_results = []
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(run_tool, tool_call) for tool_call in tool_calls]
                for future in futures:
                    try:
                        result = future.result()
                        tool_results.append(result)
                    except Exception as e:
                        logger.error(f"❌ Unexpected error in tool execution: {str(e)}", exc_info=True)
                        continue

            logger.info(f"✅ All tools executed ({len(tool_results)} results)")

            # Send tool results back to Claude
            messages.append({"role": "user", "content": tool_results})

            return {**state, "messages": messages, "response": None}

        except Exception as e:
            logger.error(f"❌ Tool execution node failed: {str(e)}", exc_info=True)
            return {
                **state,
                "validation_error": True,
                "error_message": f"Tool execution error: {str(e)}",
                "final_result": {
                    "score": 0,
                    "reasoning": f"Tool Error: {str(e)}",
                    "recommendation": "Please try again",
                    "validation_failed": True
                }
            }

    @traceable(name="parse_response_node", tags=["parsing", "node"])
    def _node_parse_response(self, state: AnalysisState) -> AnalysisState:
        """Node 4: Parse and validate Claude's response"""
        logger.info(f"→ Parsing response...")
        logger.debug(f"  Response text length: {len(state['response_text'])} chars")

        try:
            result = self._parse_response(state["response_text"])
            logger.info("✅ Analysis parsed successfully")
            logger.debug(f"  Fields extracted: {list(result.keys())}")

            if result.get("validation_failed"):
                logger.warning("⚠️ Output validation failed during parsing")
            

            history = state.get("conversation_history",[])
            history.append(
                {
                "role": "assistant",
                "content": state["response_text"]
                }
            )

            
            return {
                **state, 
                "conversation_history": history,
                "final_result": result
            }

        except Exception as e:
            logger.error(f"❌ Parse response node failed: {str(e)}", exc_info=True)
            return {
                **state,
                "validation_error": True,
                "error_message": f"Parsing error: {str(e)}",
                "final_result": {
                    "score": 0,
                    "reasoning": f"Parsing Error: {str(e)}",
                    "recommendation": "Please try again",
                    "validation_failed": True
                }
            }

    def _validate_tool_input(self, tool_name: str, tool_input: dict) -> tuple[bool, str]:
        """Validate tool input before execution

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters dictionary

        Returns:
            (is_valid, error_message)
        """
        # Check input is a dictionary
        if not isinstance(tool_input, dict):
            return False, f"Tool input must be a dictionary, got {type(tool_input).__name__}"

        # Tool-specific validation
        if tool_name == "send_email_to_user":
            required = {"email_address", "subject", "body"}
            missing = required - set(tool_input.keys())
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"

            # Validate types
            if not isinstance(tool_input["email_address"], str):
                return False, "email_address must be a string"
            if not isinstance(tool_input["subject"], str):
                return False, "subject must be a string"
            if not isinstance(tool_input["body"], str):
                return False, "body must be a string"

            # Validate email format (basic check)
            email = tool_input["email_address"].strip()
            if "@" not in email or "." not in email:
                return False, f"Invalid email format: {email}"

            # Validate non-empty
            if not email or not tool_input["subject"] or not tool_input["body"]:
                return False, "email_address, subject, and body cannot be empty"

            return True, ""

        elif tool_name == "tavily_search":
            if "query" not in tool_input:
                return False, "Missing required field: query"

            if not isinstance(tool_input["query"], str):
                return False, "query must be a string"

            query = tool_input["query"].strip()
            if not query:
                return False, "query cannot be empty"

            if len(query) > 1000:
                return False, f"query too long (max 1000 chars, got {len(query)})"

            return True, ""

        elif tool_name == "google_places_search":
            required = {"zipcode", "business_type"}
            missing = required - set(tool_input.keys())
            if missing:
                return False, f"Missing required fields: {', '.join(missing)}"

            if not isinstance(tool_input["zipcode"], str):
                return False, "zipcode must be a string"
            if not isinstance(tool_input["business_type"], str):
                return False, "business_type must be a string"

            zipcode = tool_input["zipcode"].strip()
            business_type = tool_input["business_type"].strip()

            if not zipcode or not business_type:
                return False, "zipcode and business_type cannot be empty"

            # Validate zipcode format (US zip codes are 5-9 digits)
            if not zipcode.replace("-", "").isdigit() or len(zipcode.replace("-", "")) < 5:
                return False, f"Invalid zipcode format: {zipcode}"

            if len(business_type) > 200:
                return False, f"business_type too long (max 200 chars)"

            return True, ""

        else:
            return False, f"Unknown tool: {tool_name}"

    @traceable(name="execute_tool", tags=["tools", "execution"])
    def _execute_tool(self, tool_name, tool_input):
        """Execute a tool and return the result with input validation"""
        logger.info(f"🔧 Executing tool: {tool_name}")
        logger.debug(f"  Tool input: {tool_input}")

        try:
            # Validate input BEFORE execution
            is_valid, error_message = self._validate_tool_input(tool_name, tool_input)
            if not is_valid:
                logger.error(f"❌ Invalid input for {tool_name}: {error_message}")
                return f"Validation Error: {error_message}"

            logger.debug(f"  Input validation passed")

            if tool_name == "send_email_to_user":
                logger.debug(f"  Sending email to {tool_input['email_address']}")
                result = custom_tools.send_email_to_user(
                    tool_input["email_address"],
                    tool_input["subject"],
                    tool_input["body"]
                )
                logger.info(f"✅ Email sent successfully")
                return result

            elif tool_name == "tavily_search":
                logger.debug(f"  Searching for: {tool_input['query']}")
                result = custom_tools.tavily_search(tool_input["query"])
                logger.info(f"✅ Search completed")
                return result

            elif tool_name == "google_places_search":
                logger.debug(f"  Searching places in {tool_input['zipcode']} for {tool_input['business_type']}")
                result = custom_tools.google_places_search(
                    tool_input["zipcode"],
                    tool_input["business_type"]
                )
                logger.info(f"✅ Places search completed")
                return result

        except KeyError as e:
            logger.error(f"❌ Missing parameter for {tool_name}: {str(e)}", exc_info=True)
            return f"Error: Missing parameter {str(e)} for tool {tool_name}"

        except ValueError as e:
            logger.error(f"❌ Invalid value for {tool_name}: {str(e)}", exc_info=True)
            return f"Error: Invalid value - {str(e)}"

        except Exception as e:
            logger.error(f"❌ Tool {tool_name} execution failed: {str(e)}", exc_info=True)
            return f"Error executing {tool_name}: {str(e)}"

    def _clean_text(self, text: str) -> str:
        """Remove markdown and formatting artifacts from Claude's response"""
        text = text.replace("—", " - ")
        text = text.replace("–", "-")
        text = text.replace("**", "")
        text = text.replace("*", "")
        text = re.sub(r'\n---+\n', '\n', text)
        text = re.sub(r'\n===+\n', '\n', text)
        lines = [line.rstrip() for line in text.split('\n')]
        cleaned = []
        prev_blank = False
        for line in lines:
            is_blank = line.strip() == ""
            if is_blank and prev_blank:
                continue
            cleaned.append(line)
            prev_blank = is_blank
        return '\n'.join(cleaned).strip()

    @traceable(name="parse_response", tags=["parsing", "claude"])
    def _parse_response(self, response_text: str) -> dict:
        """Parse claude response into structured format using regex"""

        def extract(label, next_label):
            pattern = rf'{label}:\s*(.+?)(?={next_label}:|$)'
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
            logger.warning(f"⚠️ {label} field not found in response")
            return ""

        idea_summary = extract("IDEA_SUMMARY", "PROBLEM_STATEMENT")
        problem_statement = extract("PROBLEM_STATEMENT", "TARGET_AUDIENCE")
        target_audience = extract("TARGET_AUDIENCE", "MARKET_VALIDATION")
        market_validation = extract("MARKET_VALIDATION", "COMPETITOR_ANALYSIS")
        competitor_analysis = extract("COMPETITOR_ANALYSIS", "MVP_RECOMMENDATION")
        mvp_recommendation = extract("MVP_RECOMMENDATION", "RISK_ANALYSIS")
        risk_analysis = extract("RISK_ANALYSIS", "FINAL_RECOMMENDATION")

        rec_match = re.search(r'FINAL_RECOMMENDATION:\s*(.+?)$', response_text, re.DOTALL)
        rec_text = rec_match.group(1).strip() if rec_match else ""

        rec_text_lower = rec_text.lower()
        if "don't build" in rec_text_lower or "do not build" in rec_text_lower:
            final_recommendation = "Don't build it"
        elif "consider changes" in rec_text_lower or "reconsider" in rec_text_lower:
            final_recommendation = "Consider changes"
        elif "build" in rec_text_lower:
            final_recommendation = "Build it"
        else:
            final_recommendation = "Consider changes"

        try:
            validated = ProjectAnalysis(
                idea_summary=idea_summary,
                problem_statement=problem_statement,
                target_audience=target_audience,
                market_validation=market_validation,
                competitor_analysis=competitor_analysis,
                mvp_recommendation=mvp_recommendation,
                risk_analysis=risk_analysis,
                final_recommendation=final_recommendation
            )
            logger.info("✅ Output validation passed")
            return {
                "idea_summary": self._clean_text(validated.idea_summary),
                "problem_statement": self._clean_text(validated.problem_statement),
                "target_audience": self._clean_text(validated.target_audience),
                "market_validation": self._clean_text(validated.market_validation),
                "competitor_analysis": self._clean_text(validated.competitor_analysis),
                "mvp_recommendation": self._clean_text(validated.mvp_recommendation),
                "risk_analysis": self._clean_text(validated.risk_analysis),
                "final_recommendation": self._clean_text(validated.final_recommendation),
                "raw_response": response_text
            }
        except ValidationError as e:
            logger.error(f"❌ Output validation failed: {e}")
            return {
                "idea_summary": "",
                "problem_statement": "",
                "target_audience": "",
                "market_validation": "",
                "competitor_analysis": "",
                "mvp_recommendation": "",
                "risk_analysis": "",
                "final_recommendation": f"Validation error: {str(e)}",
                "raw_response": response_text,
                "validation_failed": True
            }

    def validate_idea(self, project_idea: str) -> dict:
        """Validate a project idea using LangGraph workflow

        Args:
            project_idea: Description of the project idea

        Returns:
            dict with analysis results
        """
        logger.info(f"✓ Validation started for: {project_idea}")

        # Initialize state and run workflow
        initial_state = {
            "project_idea": project_idea,
            "messages": [],
            "response": None,
            "response_text": "",
            "validation_error": False,
            "error_message": "",
            "final_result": {},
            "conversation_history": []
        }

        result = self.workflow.invoke(initial_state)

        if result["validation_error"]:
            return result["final_result"]

        return result["final_result"]

    def ask_follow_up(self, question: str, previous_messages: list, conversation_history: list) -> dict:
        """Ask a follow-up question about the analysis

        Args:
            question: The follow-up question from the user
            previous_messages: Previous messages from the workflow
            conversation_history: Previous conversation history

        Returns:
            dict with updated analysis
        """
        logger.info(f"✓ Follow-up question: {question}")

        # Add user's follow-up question to messages
        messages = previous_messages + [{"role": "user", "content": question}]

        try:
            # Keep looping until Claude gives final text answer (not tool calls)
            while True:
                logger.info(f"← Calling Claude for follow-up...")

                # First call without streaming to check for tool calls
                response = client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    tools=TOOLS_SCHEMA,
                    messages=messages,
                    stream=False
                )

                # Check if Claude called tools
                tool_calls = [block for block in response.content if block.type == "tool_use"]

                if not tool_calls:
                    # No tools called - stream the text response
                    logger.info(f"→ Streaming follow-up response...\n")
                    response_text = ""

                    # Create a streaming request for the response
                    stream_response = client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        tools=TOOLS_SCHEMA,
                        messages=messages,
                        stream=True
                    )

                    try:
                        for event in stream_response:
                            try:
                                if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                                    chunk = event.delta.text
                                    if chunk:
                                        print(chunk, end="", flush=True)
                                        response_text += chunk
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"⚠️  Stream interrupted: {str(e)}")
                        if not response_text:
                            return {
                                "validation_failed": True,
                                "reasoning": "Stream failed. Please try again."
                            }

                    if not response_text:
                        return {
                            "validation_failed": True,
                            "reasoning": "Received empty response. Please try again."
                        }

                    print()  # New line after response
                    logger.info(f"← Follow-up response complete ({len(response_text)} chars)")

                    # Update conversation history
                    updated_history = conversation_history + [
                        {"role": "user", "content": question},
                        {"role": "assistant", "content": response_text}
                    ]

                    logger.info("✅ Follow-up processed successfully")
                    return {
                        "follow_up_response": response_text,
                        "conversation_history": updated_history,
                        "messages": messages + [{"role": "assistant", "content": response_text}]
                    }

                else:
                    # Tools were called - execute them and continue loop
                    logger.info(f"Claude requested {len(tool_calls)} tool call(s) for follow-up")

                    # Add Claude's response to messages
                    messages.append({"role": "assistant", "content": response.content})

                    # Execute tools
                    def run_tool(tool_call):
                        logger.info(f"⚙️  Executing: {tool_call.name}")
                        try:
                            result = self._execute_tool(tool_call.name, tool_call.input)
                            logger.info(f"✅ {tool_call.name} completed")
                            return {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": result
                            }
                        except Exception as e:
                            logger.error(f"❌ Tool {tool_call.name} failed: {str(e)}")
                            return {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": f"Error: {str(e)}"
                            }

                    tool_results = []
                    with ThreadPoolExecutor() as executor:
                        futures = [executor.submit(run_tool, tool_call) for tool_call in tool_calls]
                        for future in futures:
                            try:
                                result = future.result()
                                tool_results.append(result)
                            except Exception as e:
                                logger.error(f"❌ Unexpected error in tool execution: {str(e)}")
                                continue

                    logger.info(f"✅ All tools executed ({len(tool_results)} results)")

                    # Send tool results back to Claude and loop again
                    messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            logger.error(f"❌ Follow-up question failed: {str(e)}", exc_info=True)
            return {
                "validation_failed": True,
                "reasoning": f"Follow-up failed: {str(e)}"
            }

    def send_analysis_via_email(self, email_address: str, analysis_result: dict) -> str:
        """Send project analysis results via email

        Args:
            email_address: User's email address
            analysis_result: Analysis results dictionary

        Returns:
            Confirmation message
        """
        logger.info(f"📧 Preparing to send analysis to {email_address}")

        email_body = f"""PROJECT ANALYSIS RESULTS

IDEA SUMMARY:
{analysis_result['idea_summary']}

PROBLEM STATEMENT:
{analysis_result['problem_statement']}

TARGET AUDIENCE:
{analysis_result['target_audience']}

MARKET VALIDATION:
{analysis_result['market_validation']}

COMPETITOR ANALYSIS:
{analysis_result['competitor_analysis']}

MVP RECOMMENDATION:
{analysis_result['mvp_recommendation']}

RISK ANALYSIS:
{analysis_result['risk_analysis']}

FINAL RECOMMENDATION: {analysis_result['final_recommendation']}"""

        email_result = custom_tools.send_email_to_user(
            email_address=email_address,
            subject="Your Project Analysis Results",
            body=email_body
        )

        logger.info("✅ Email sent successfully")
        return email_result
