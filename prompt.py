import subprocess
import json


def main():

    with open('prompts.json', 'r') as file:
        prompts = json.load(file)
    
    print(prompts['DGA']['base_domain'])

    
main()