import json
import csv
import os
import time
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
from pymongo import MongoClient
from datetime import datetime, timedelta

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
MONGO_URI = "localhost:27017"
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
def load_prompt_config(case: str, request_id: int) -> Dict[str, Any]:
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
        logger.error(f"Request {request_id}: Failed to parse prompts.json")
        raise ValueError("Invalid prompt configuration format")
    except FileNotFoundError:
        logger.error(f"Request {request_id}: prompts.json file not found")
        raise ValueError("Prompt configuration file not found")

def load_rag_data(config: Dict[str, Any], request_id: int) -> tuple:
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
                    logger.info(f"Request {request_id}: Loaded {len(rag_bad)} bad RAG examples")
    except Exception as e:
        logger.warning(f"Request {request_id}: Failed to load bad RAG data: {str(e)}")
    
    try:
        if 'dir' in config and 'rag_ok' in config:
            file_path = os.path.join(config['dir'], config['rag_ok'])
            if os.path.exists(file_path):
                with open(file_path, newline='') as file:
                    rag_ok = list(csv.reader(file))
                    logger.info(f"Request {request_id}: Loaded {len(rag_ok)} good RAG examples")
    except Exception as e:
        logger.warning(f"Request {request_id}: Failed to load good RAG data: {str(e)}")
    
    return rag_bad, rag_ok

def retry_with_backoff(func, request_id: int, max_retries=MAX_RETRIES, initial_delay=RETRY_DELAY):
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
            logger.warning(f"Request {request_id}: Retry {retries + 1}/{max_retries} after error: {str(e)}. Waiting {wait:.2f}s")
            time.sleep(wait)
            retries += 1
    
    logger.error(f"Request {request_id}: All {max_retries} retries failed")
    raise last_exception

def openai_call(prompt: str, request_id: int) -> str:
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
        return retry_with_backoff(_call, request_id)
    except Exception as e:
        logger.error(f"Request {request_id}: OpenAI API call failed after retries: {str(e)}")
        raise RuntimeError(f"AI service error: {str(e)}")

def together_call(prompt: str, request_id: int) -> str:
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
        return retry_with_backoff(_call, request_id)
    except Exception as e:
        logger.error(f"Request {request_id}: TogetherAI API call failed after retries: {str(e)}")
        raise RuntimeError(f"AI service error: {str(e)}")

def ai_service_call(prompt: str, request_id: int) -> str:
    """
    Call preferred AI service with fallback
    
    Args:
        prompt: The prompt to send to the API
        
    Returns:
        API response content
    """
    try:
        if PREFERRED_AI_SERVICE.lower() == 'openai':
            return openai_call(prompt, request_id)
        else:
            return together_call(prompt, request_id)
    except Exception as primary_error:
        # Fallback to the other service if primary fails
        logger.warning(f"Request {request_id}: Primary AI service failed: {str(primary_error)}. Trying fallback.")
        try:
            if PREFERRED_AI_SERVICE.lower() == 'openai':
                return together_call(prompt, request_id)
            else:
                return openai_call(prompt, request_id)
        except Exception as fallback_error:
            logger.error(f"Request {request_id}: Fallback AI service also failed: {str(fallback_error)}")
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
        
def hit_cache(case: str, data: List[str], cache_time: int, request_id: int) -> tuple[List[bool], List[str]]:
    """
    Seperate list of items into cached and uncached results
    
    Args:
        case: The case identifier
        data: List of input data strings
        cache_time: Number of minutes to cache back
        
    Raises:
        ValueError: If caching is not working
    """

    client = MongoClient(MONGO_URI)
    db = client["cache"]
    collection = db[case]

    time_cutoff = datetime.now() - timedelta(minutes=cache_time)

    cache_hit_success = []
    cache_hit_vals = []

    try:
        for item in data:
            query = {
                "key": item,
                "time": {'$gte': time_cutoff}
            }

            if result := collection.find_one(query):
                cache_hit_success.append(True)
                cache_hit_vals.append(result["value"])
            else:
                cache_hit_success.append(False)
        
        logger.info(f"Request {request_id}: Accessed cache for case '{case}', cache hits: {len(cache_hit_vals)}")
    
    except Exception as e:
        logger.warning(f"Request {request_id}: Cache access failed {str(e)}")

    client.close()
    return cache_hit_success, cache_hit_vals

def update_cache(case: str, uncached_data: List[str], response_data: List[str], request_id: int):
    """
    cache results from AI
    
    Args:
        case: The case identifier
        uncached_data: List of input data strings that did not have a cache hit
        response_data: List of AI responses to uncached_data
        
        
    Raises:
        ValueError: If caching is not working
    """

    client = MongoClient(MONGO_URI)
    db = client["cache"]
    collection = db[case]

    time_update = datetime.now()
    number_updated = 0

    try:
        for i in range(len(uncached_data)):
            query_filter = {'key': uncached_data[i]}
            update_operation = { '$set': { "time":  time_update, "value": response_data[i] } }
            result = collection.update_one(query_filter, update_operation, upsert=True)
            number_updated += result.raw_result["n"]
        logger.info(f"Request {request_id}: Updated cache for case '{case}', with {number_updated} data items")
    
    except Exception as e:
        logger.warning(f"Request {request_id}: Cache update operation failed: {str(e)}")
    
    client.close()
    
    return

def generate_uncached_list(data: List[str], cache_hit_success: List[bool]) -> List[str]:
    uncached_data = []
    for i in range(len(data)):
        if not cache_hit_success[i]:
            uncached_data.append(data[i])
        
    return uncached_data

def combine_data(cache_hit_vals: List[str], response_data: List[str], cache_hit_success: List[bool]) -> List[str]:
    output_data = []
    cache_hit_index = 0
    response_data_index = 0

    for i in range(len(cache_hit_success)):
        if cache_hit_success[i]:
            output_data.append(cache_hit_vals[cache_hit_index])
            cache_hit_index += 1
        else:
            output_data.append(response_data[response_data_index])
            response_data_index += 1

    return output_data

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
        config = load_prompt_config(case, request_id)

        # Attempt to find cache hits for each item
        cache_hit_success, cache_hit_vals = hit_cache(case, data, config['cache_time'], request_id)

        # Generate list free from successful cache hits
        uncached_data = generate_uncached_list(data, cache_hit_success)

        # Load RAG data if available
        rag_bad, rag_ok = load_rag_data(config, request_id)

        response_data = []
        if len(uncached_data) > 0:
            # Generate API prompt
            api_string = f"{config['prompt']}\n" + "\n".join(uncached_data)
        
            # Get AI response
            logger.info(f"Request {request_id}: Calling AI service with {len(uncached_data)} data items")
            response = ai_service_call(api_string, request_id)
        
            # convert to list
            response_data = response.splitlines()

            # cache responses
            update_cache(case, uncached_data, response_data, request_id)

        # recombined cached and uncached results
        output = combine_data(cache_hit_vals, response_data, cache_hit_success)

        elapsed_time = time.time() - start_time
        logger.info(f"Request {request_id}: Completed in {elapsed_time:.2f}s")
        return output

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