import logging
from typing import Dict, Any
from crew_manager import run

# Configure logging to write to error.log
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="debug.log",
    filemode="a",  # append to the file if it exists
)
logger = logging.getLogger(__name__)


# Required by promptfoo
def call_api(
    prompt: str,
    options: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, str]:
    """Call the crew manager API with the given prompt and options.
    Args:
        prompt (str): The prompt to send to the crew manager.
        options (Dict[str, Any]): Options for the API call, from the 'config' arg.
        context (Dict[str, Any]): Prompt data for the API call - user & system prompts.
    Returns:
        Dict[str, str]: The response from the crew manager API.
    """

    logger.debug(f"call_api: prompt: {prompt}")
    logger.debug(f"call_api: options: {options}")
    logger.debug(f"call_api: context: {context}")

    try:
        model_name = options["config"]["model_name"]
        result = run(prompt, model_name)
        # Normalize to Promptfoo provider response shape
        return {"output": result}
    except Exception as e:
        # Can't user print here when promptfoo running
        # Uncertain what promptfoos own logger name is, if even using
        error_msg = f"Error in call_api: {str(e)}"
        logging.error(error_msg, exc_info=True)  # This will log the full traceback
        return {"output": f"Error: {str(e)}"}
