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

from crewai import Agent, Task, Crew, LLM
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Create a StdioServerParameters object
server_params = [
    StdioServerParameters(
        command="uvx",
        args=["mcp-neo4j-cypher"],
        env=os.environ,
    )
]


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
        return LLM(
            model=name,
            temperature=0.7,
            base_url="http://localhost:11434"
        )
    else: 
        return LLM(
            model=name,
            temperature=0.7
        )

crews = {}

def mcp_crew(tools, llm):
    # Create an agent with access to tools
    mcp_agent = Agent(
        role="MCP Tool User",
        goal="Utilize tools from MCP servers.",
        backstory="I can connect to MCP servers and use their tools.",
        tools=tools,
        max_iterations=3,
        step_callback=log_step_callback,  # Optional
        # llm=llm, # Optional - Remove if using OpenAI
    )

    # Create a task referrencing user prompt
    processing_task = Task(
        description="""Process the following prompt about the Neo4j graph database: {prompt}""",
        expected_output="A brief report on the outcome of the command: {prompt}",
        agent=mcp_agent,
        callback=log_task_callback,  # Optional
    )

    # Create the crew
    return Crew(agents=[mcp_agent], tasks=[processing_task], verbose=False)


# Convenience for fastAPI call
def run(prompt: str, full_model_name:str):
    # full_model_name is the full name path used by CrewAI
    # ie 'openai/o3-mini'
    # See https://docs.crewai.com/en/concepts/llms for examples
    
    # Load the MCP Tools
    with MCPServerAdapter(server_params) as tools:

        print(f"Available tools from MCP server(s): {[tool.name for tool in tools]}")

        if full_model_name not in crews:
            llm = llm_by_name(full_model_name)
            crews[full_model_name] = mcp_crew(tools, llm)

        crew = crews[full_model_name]

        # Run the crew w/ the user prompt
        result = crew.kickoff(inputs={"prompt": prompt})

        # Return the final answer
        return {"result": result}


# For running as a script
if __name__ == "__main__":

    llm_name = "sambanova/Meta-Llama-3.1-8B-Instruct"
    # write_command = "Create a database record for a company named 'Acme Inc'"
    read_command = "Describe the data from the database"
    result = run(read_command, llm_name)

    print(
        f"""
        Query completed!
        result: {result}
    """
    )
