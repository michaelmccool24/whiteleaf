import json
import csv
import os
import time
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("prompt.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment-based configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
TOGETHERAI_API_KEY = os.environ.get('TOGETHERAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
TOGETHERAI_MODEL = os.environ.get('TOGETHERAI_MODEL', 'deepseek-ai/DeepSeek-V3')
PREFERRED_AI_SERVICE = os.environ.get('PREFERRED_AI_SERVICE', 'together')  # 'openai' or 'together'
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
RETRY_DELAY = float(os.environ.get('RETRY_DELAY', 1.0))  # seconds
REQUEST_TIMEOUT = int(os.environ.get('REQUEST_TIMEOUT', 30))  # seconds

# Lazy-loaded API clients
_openai_client = None
_together_client = None

def get_openai_client():
    """Lazily initialize OpenAI client"""
    global _openai_client
    if _openai_client is None:
        if not OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY environment variable not set")
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=OPENAI_API_KEY)
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
    return _openai_client

def get_together_client():
    """Lazily initialize Together client"""
    global _together_client
    if _together_client is None:
        if not TOGETHERAI_API_KEY:
            raise EnvironmentError("TOGETHERAI_API_KEY environment variable not set")
        try:
            from together import Together
            _together_client = Together(api_key=TOGETHERAI_API_KEY)
        except ImportError:
            raise ImportError("Together package not installed. Install with: pip install together")
    return _together_client

@lru_cache(maxsize=32)
def load_prompt_config(case: str) -> Dict[str, Any]:
    """
    Load prompt configuration with caching
    
    Args:
        case: The case identifier (e.g., 'WLUC1')
        
    Returns:
        Dictionary containing prompt configuration
    
    Raises:
        ValueError: If prompt configuration is invalid or not found
    """
    try:
        with open('prompts.json', 'r') as file:
            prompts = json.load(file)
        
        if case not in prompts:
            raise ValueError(f"Case '{case}' not found in configuration")
            
        return prompts[case]
    except json.JSONDecodeError:
        logger.error("Failed to parse prompts.json")
        raise ValueError("Invalid prompt configuration format")
    except FileNotFoundError:
        logger.error("prompts.json file not found")
        raise ValueError("Prompt configuration file not found")

def load_rag_data(config: Dict[str, Any]) -> tuple:
    """
    Load RAG data based on configuration
    
    Args:
        config: Prompt configuration dictionary
        
    Returns:
        Tuple of (rag_bad, rag_ok) data
    """
    rag_bad = []
    rag_ok = []
    
    try:
        if 'dir' in config and 'rag_bad' in config:
            file_path = os.path.join(config['dir'], config['rag_bad'])
            if os.path.exists(file_path):
                with open(file_path, newline='') as file:
                    rag_bad = list(csv.reader(file))
                    logger.info(f"Loaded {len(rag_bad)} bad RAG examples")
    except Exception as e:
        logger.warning(f"Failed to load bad RAG data: {str(e)}")
    
    try:
        if 'dir' in config and 'rag_ok' in config:
            file_path = os.path.join(config['dir'], config['rag_ok'])
            if os.path.exists(file_path):
                with open(file_path, newline='') as file:
                    rag_ok = list(csv.reader(file))
                    logger.info(f"Loaded {len(rag_ok)} good RAG examples")
    except Exception as e:
        logger.warning(f"Failed to load good RAG data: {str(e)}")
    
    return rag_bad, rag_ok

def retry_with_backoff(func, max_retries=MAX_RETRIES, initial_delay=RETRY_DELAY):
    """
    Retry a function with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay between retries in seconds
        
    Returns:
        Result of the function call
        
    Raises:
        Exception: The last exception encountered after all retries
    """
    retries = 0
    delay = initial_delay
    last_exception = None
    
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            last_exception = e
            wait = delay * (2 ** retries)
            logger.warning(f"Retry {retries + 1}/{max_retries} after error: {str(e)}. Waiting {wait:.2f}s")
            time.sleep(wait)
            retries += 1
    
    logger.error(f"All {max_retries} retries failed")
    raise last_exception

def openai_call(prompt: str) -> str:
    """
    Execute OpenAI API call with error handling and retries
    
    Args:
        prompt: The prompt to send to the API
        
    Returns:
        API response content
        
    Raises:
        Exception: If all retries fail
    """
    def _call():
        client = get_openai_client()
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT
        )
        return response.choices[0].message.content
    
    try:
        return retry_with_backoff(_call)
    except Exception as e:
        logger.error(f"OpenAI API call failed after retries: {str(e)}")
        raise RuntimeError(f"AI service error: {str(e)}")

def together_call(prompt: str) -> str:
    """
    Execute TogetherAI API call with error handling and retries
    
    Args:
        prompt: The prompt to send to the API
        
    Returns:
        API response content
        
    Raises:
        Exception: If all retries fail
    """
    def _call():
        client = get_together_client()
        response = client.chat.completions.create(
            model=TOGETHERAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=REQUEST_TIMEOUT
        )
        return response.choices[0].message.content
    
    try:
        return retry_with_backoff(_call)
    except Exception as e:
        logger.error(f"TogetherAI API call failed after retries: {str(e)}")
        raise RuntimeError(f"AI service error: {str(e)}")

def ai_service_call(prompt: str) -> str:
    """
    Call preferred AI service with fallback
    
    Args:
        prompt: The prompt to send to the API
        
    Returns:
        API response content
    """
    try:
        if PREFERRED_AI_SERVICE.lower() == 'openai':
            return openai_call(prompt)
        else:
            return together_call(prompt)
    except Exception as primary_error:
        # Fallback to the other service if primary fails
        logger.warning(f"Primary AI service failed: {str(primary_error)}. Trying fallback.")
        try:
            if PREFERRED_AI_SERVICE.lower() == 'openai':
                return together_call(prompt)
            else:
                return openai_call(prompt)
        except Exception as fallback_error:
            logger.error(f"Fallback AI service also failed: {str(fallback_error)}")
            raise RuntimeError("All AI services failed to process the request")

def validate_input(case: str, data: List[str]) -> None:
    """
    Validate input parameters
    
    Args:
        case: The case identifier
        data: List of input data strings
        
    Raises:
        ValueError: If validation fails
    """
    if not case or not isinstance(case, str):
        raise ValueError("Invalid case identifier")
    
    if not data or not isinstance(data, list):
        raise ValueError("Data must be a non-empty list")
    
    for item in data:
        if not isinstance(item, str):
            raise ValueError("All data items must be strings")
        if len(item) > 2048:  # Example limit
            raise ValueError("Data item exceeds maximum length")

def main(case: str, data: List[str]) -> str:
    """
    Process plaintext data through AI service
    
    Args:
        case: The case identifier (e.g., 'WLUC1')
        data: List of plaintext strings
    
    Returns:
        Plaintext response from AI service
    
    Raises:
        ValueError: For input validation errors
        RuntimeError: For processing errors
    """
    start_time = time.time()
    request_id = int(time.time() * 1000)
    logger.info(f"Request {request_id}: Processing request for case '{case}' with {len(data)} data items")
    
    try:
        # Validate input
        validate_input(case, data)
        
        # Load prompt configuration
        config = load_prompt_config(case)
        
        # Load RAG data if available
        rag_bad, rag_ok = load_rag_data(config)
        
        # Generate API prompt
        api_string = f"{config['prompt']}\n" + "\n".join(data)
        
        # Get AI response
        logger.info(f"Request {request_id}: Calling AI service")
        response = ai_service_call(api_string)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Request {request_id}: Completed in {elapsed_time:.2f}s")
        return response

    except ValueError as e:
        logger.warning(f"Request {request_id}: Validation error: {str(e)}")
        return f"Input Error: {str(e)}"
    except RuntimeError as e:
        logger.error(f"Request {request_id}: Runtime error: {str(e)}")
        return f"Processing Error: {str(e)}"
    except Exception as e:
        logger.error(f"Request {request_id}: Unexpected error: {str(e)}", exc_info=True)
        return "An unexpected error occurred"

# Test function
#def test_main():
    """Run a simple test of the main function"""
    """ test_data = ["WWW.EXAMPLE.COM", "TEST.ORG"]
    test_case = "WLUC1"
    
    print(f"Testing with case '{test_case}' and data: {test_data}")
    try:
        result = main(test_case, test_data)
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

# Allow running as script for testing
if __name__ == "__main__":
    test_main()"""