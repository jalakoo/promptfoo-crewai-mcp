# OPTIONAL -------------------------------
# Using ollama - by default OpenAI is used
# Remove / comment this block if using OpenAI
# from crewai import LLM
# from langchain_community.chat_models import ChatOpenAI

# llm = ChatOpenAI(
#     model="ollama/mixtral:latest",
#     base_url="http://localhost:11434",
#     streaming=True
# )
# ----------------------------------------

from crewai import Agent, Task, Crew, LLM, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from dotenv import load_dotenv
import os
import atexit
import threading

# Load .env file
load_dotenv()

# Store generated crews by model name
crews = {}

# Create a StdioServerParameters object
server_params = [
    StdioServerParameters(
        command="uvx",
        args=["mcp-neo4j-cypher@0.3.0"],
        env=os.environ,
    ),
    # StdioServerParameters(
    #     command="uvx",
    #     args=["mcp-neo4j-data-modeling"],
    #     env=os.environ,
    # )
]

# Singleton MCP adapter/tools
_mcp_adapter = None
_tools = None
_tools_lock = threading.Lock()


def _ensure_tools():
    global _mcp_adapter, _tools
    if _tools is None:
        with _tools_lock:
            if _tools is None:
                # Persist the adapter across calls
                _mcp_adapter = MCPServerAdapter(server_params)
                tools = _mcp_adapter.__enter__()
                # Ensure clean shutdown on process exit
                atexit.register(
                    lambda: _mcp_adapter and _mcp_adapter.__exit__(None, None, None)
                )
                _tools = tools
    return _tools


# Optionally logging callbacks from Agents & Tasks
def log_step_callback(output):
    print(
        f"""
        Step completed!
        details: {output.__dict__}
    """
    )


def log_task_callback(output):
    print(
        f"""
        Task completed!
        details: {output.__dict__}
    """
    )


def llm_by_name(name: str = "sambanova/Meta-Llama-3.1-8B-Instruct"):
    # Local ollama models require the base url be defined
    if "ollama/" in name:
        return LLM(model=name, temperature=0, base_url="http://localhost:11434")
    if "gpt-5" in name:
        return LLM(
            model=name, drop_params=True, additional_drop_params=["stop", "temperature"]
        )
    else:
        return LLM(model=name, temperature=0)


def mcp_crew(tools, llm_name: str):

    llm = llm_by_name(llm_name)

    # Create an agent with access to tools
    cypher_agent = Agent(
        role="Cypher MCP Tool User",
        goal=(
            "Accurately answer user questions by querying a Neo4j database "
            "using the available MCP tools when needed. Prefer precision over verbosity."
        ),
        backstory=(
            "You are an expert data analyst proficient in Cypher and Neo4j.\n"
            "You have access to MCP tools to: (1) inspect the schema, (2) read data with Cypher,"
            " and (3) write data with Cypher. Use the minimal set of tool calls needed to answer.\n"
            "Always validate Cypher syntax before execution and avoid destructive writes unless explicitly requested."
        ),
        max_iter=3,
        tools=tools,
        reasoning=False,  # False for better compatibility
        step_callback=log_step_callback,  # Optional
        llm=llm,  # Optional - Remove if using OpenAI
    )

    cypher_task = Task(
        description=(
            "Given the user's request: '{prompt}', decide if tools are required.\n"
            "If needed, first get the schema, then compose precise Cypher.\n"
            "Return ONLY the final answer for the user, not internal reasoning."
        ),
        expected_output=(
            "1-3 concise sentences answering the question. Include specific figures when asked."
        ),
        agent=cypher_agent,
        callback=log_task_callback,  # Optional
    )

    # Create the crew
    return Crew(
        agents=[cypher_agent],
        tasks=[cypher_task],
        verbose=os.getenv("CREWAI_VERBOSE", "0") in ("1", "true", "True"),
        memory=False,
    )


def run(prompt: str, full_model_name: str):
    # Load the MCP Tools once and reuse across calls
    tools = _ensure_tools()

    print(f"\nRunning Crew with model: {full_model_name} and prompt: {prompt}")
    print(f"Available tools from MCP server(s): {[tool.name for tool in tools]}")

    if full_model_name not in crews:
        crews[full_model_name] = mcp_crew(tools, full_model_name)

    crew = crews[full_model_name]

    # Run the crew w/ the user prompt (with a simple retry for transient LLM errors)
    last_err = None
    for attempt in range(2):
        try:
            result = crew.kickoff(inputs={"prompt": prompt})
            break
        except Exception as e:
            last_err = e
            import time, logging

            logging.exception("Error during crew.kickoff (attempt %d)", attempt + 1)
            time.sleep(0.5)
    else:
        # All attempts failed
        result = f"LLM error: {last_err}"

    # Return a plain string for provider compatibility
    return str(result)


# For running as a script
if __name__ == "__main__":

    # llm_name = "sambanova/Meta-Llama-3.1-8B-Instruct"
    llm_name = "ollama/qwen3"
    # write_command = "Create a database record for a company named 'Acme Inc'"
    read_command = "Describe the data from the database"
    result = run(read_command, llm_name)

    print(
        f"""
        Query completed!
        result: {result}
    """
    )
