import splunk.Intersplunk as intersplunk
import splunk.mining.dcutils as dcu
import traceback
import json
import os,sys
import requests
#import logging


#log = open("myprog.log", "a")
#sys.stdout = log
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
#print(prompt_values)

if not prompt_values:
    intersplunk.outputResults([{"error": "No 'prompt' field found in results"}])
    sys.exit(0)

usecase_value = next((row["whiteleafuc"] for row in results if "whiteleafuc" in row), None)
#print(usecase_value)

params = {
        "prompts": ",".join(map(str, prompt_values)),
        "whiteleafuc": usecase_value
        }
#print(params)

try:
    response = requests.get(server_url, params=params, headers=header)
    #print(response.request.url)
    response.raise_for_status()

    if response.headers.get("Content-Type") == "application/json":
        #server_response = response.json()
        response_data = response.json()
        #print(response_data)  # Check what the response looks like
        
        # Assuming the response contains a 'scores' field with risk scores
        risk_scores = response_data.get("scores", [])
        #print(f"Risk scores: {risk_scores}")

        # Add risk scores to the original Splunk results
        enriched_results = []
        for idx, row in enumerate(results):
            if idx < len(risk_scores):
                row["risk_score"] = risk_scores[idx]
            else:
                row["risk_score"] = "N/A"  # Default if there are fewer scores than rows
            enriched_results.append(row)
        
        #print("This is enriched data:", enriched_results)
        #enriched_results_cleaned = json.dumps(enriched_results)
        #print("This is enriched data after json dumps:", enriched_results_cleaned)
        # Output the enriched results to Splunk
        intersplunk.outputResults(enriched_results)
    else:
        server_response = {"error": "Unexpected response format", "raw_response": response.text}

    #print(server_response)
    #intersplunk.outputResults([{"server_response": json.dumps(server_response)}])




except Exception as e:
    # General error handling
    error_message = f"Script failed with error: {str(e)}\n{traceback.format_exc()}"
    intersplunk.outputResults([{"error": error_message}])
