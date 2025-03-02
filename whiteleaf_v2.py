import splunk.Intersplunk as intersplunk
import splunk.mining.dcutils as dcu
import traceback
import json
import os,sys
import requests
import logging


log = open("myprog.log", "a")
sys.stdout = log
server_url = "http://35.87.82.114:8080"
header = {
    "Accept": "application/json"
}

# Read results from Splunk
results, dummyresults, settings = intersplunk.getOrganizedResults()


if not results:
    intersplunk.outputResults([])
    sys.exit(0)

prompt_values = [row["prompt"] for row in results if "prompt" in row]
print(prompt_values)

if not prompt_values:
    intersplunk.outputResults([{"error": "No 'prompt' field found in results"}])
    sys.exit(0)

params = {"prompts": ",".join(map(str, prompt_values))}
print(params)

try:
    response = requests.get(server_url, params=params, headers=header)
    response.raise_for_status()

    if response.header.get("Content-Type") == "application/json":
        server_response = response.json()
    else:
        server_response = {"error": "Unexpected response format", "raw_response": response.text}

    print(server_response)
    intersplunk.outputResults([{"server_response": json.dumps(server_response)}])




except Exception as e:
    # General error handling
    error_message = f"Script failed with error: {str(e)}\n{traceback.format_exc()}"
    intersplunk.outputResults([{"error": error_message}])
