# Promptfoo Evals w/ CrewAI + MCP Servers
Example application for evaluating Crew performance using MCP servers.

## Requirements
The following packages will need to be installed:
- [Astral's UV](https://docs.astral.sh/uv/#installation)
- [Promptfoo](https://www.promptfoo.dev/docs/installation/)

## Setup
1. First pull down dependencies: `uv sync`
2. Copy the sample.env file to a .env file: `cp sample.env .env`
3. Add your credentials to the .env file


## Running
1. First Start the FastAPI server to act as an interface for promptfoo tests: `uv run main.py`
2. Run `promptfoo eval -o output.html` to run the eval tests

## License
MIT