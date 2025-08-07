import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Any

# Configure logging to write to error.log
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='debug.log',
    filemode='a'  # append to the file if it exists
)
logger = logging.getLogger(__name__)

def call_api(prompt: str, options: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, str]:
    logger.debug(f'call_api: options: {options}')
    try:
        model_name = options['config']['model_name']
        return call_crew(prompt, model_name)
    except Exception as e:
        # Can't user print here when promptfoo running
        # Uncertain what promptfoos own logger name is, if even using
        error_msg = f'Error in call_api: {str(e)}'
        logging.error(error_msg, exc_info=True)  # This will log the full traceback
        return {
            "output": f"Error: {str(e)}"
        }


def call_crew(prompt: str, full_model_name: str = "openai/o3-mini") -> Dict[str, str]:
    # Get the server port from environment variable with a default fallback
    server_port = 4000
    url = f"http://localhost:{server_port}/crewai"

    try:
        # Build URL with query parameters
        params = {
            "prompt": prompt,
            "full_model_name": full_model_name
        }
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        # Create and send request
        req = urllib.request.Request(full_url, method='GET')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                result = json.loads(response.read().decode('utf-8'))
                return {
                    "output": result.get("result", "")
                }
            else:
                error_msg = f"HTTP Error {response.status}: {response.reason}"
                logger.error(f'Error making API request to {url}: {error_msg}')
                return {
                    "output": f"Error: {error_msg}"
                }
    except urllib.error.URLError as e:
        logger.error(f'Error making API request to {url}: {str(e)}')
        return {
            "output": f"Error: Failed to get response from the server. {str(e)}"
        }