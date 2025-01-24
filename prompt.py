import subprocess
import json
import csv
import openai

openai.api_key = "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"
ai_model = "gpt-3.5-turbo"

def main(request):

    type = list(request.keys())[0]

    with open('prompts.json', 'r') as file:
        prompts = json.load(file)
    
    with open(prompts[type]['dir'] + prompts[type]['rag_bad'], newline='') as file:
        rag_bad = list(csv.reader(file))

    print(rag_bad[1:])


def test_data():
    with open('test_data.json', 'r') as file:
        test_data = json.load(file)
    
    return(test_data)

def open_ai_call(prompt):
    try:
        response = openai.ChatCompletion.create(model=ai_model, messages=[{"role": "user", "content": prompt}])
    
    except:
        response = f"Error: {str(e)}"

    return(response)

main(test_data())

