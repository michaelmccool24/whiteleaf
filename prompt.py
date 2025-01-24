import subprocess
import json
import csv
import openai

ai_model = "gpt-3.5-turbo"

def main(request):

    with open("apikey", "r") as file:
        key = file.read()

    openai.api_key = key

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

