import subprocess
import json
import csv
from openai import OpenAI
from together import Together


with open("openai_apikey", "r") as file:
        openai_key = file.read()

with open("togetherai_apikey", "r") as file:
        togetherai_key = file.read()

client = OpenAI(api_key=openai_key)
client2 = Together(api_key=togetherai_key)



openai_model = "gpt-4o-mini"
togetherai_model = "deepseek-ai/DeepSeek-V3"

test_data = ["WWW.XN--ZALGO075952-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM",
        "WWW.XN--ZALGO003446-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM",
        "WWW.XN--ZALGO012841-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM",
        "WWW.XN--ZALGO029243-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM",
        "CLIENTALALAXP.MN",
        "CLIENTALNOTHING.ME",
        "USERALCLICLIENT.ME",
        "AGENTCLIENTCLIENT.ME",
        "JSCJSCAXPCLIALLOW.ME",
        "JSCCLIENTAGENTDISA.ME",
        "DISAALALLOWDISALLOW.ME",
        "QUJFVNN.TO",
        "CRWKBMX.TW",
        "OLKQXMAEUIWYX.XXX",
        "BPWENCSDVRJXJI.PRO",
        "pop.imvhhht.ru",
        "pop.hrfomio.ru",
        "pop.jkkjymtb.com,"
        "etotheipiplusone.net"]

case = "DGA"


def main(case, data):
    """Formats the data, appending RAG and the prompt, then calls the AI API

    Args:
        case(str) -- The appreviation for the use case (e.g. 'DGA')
        case["str...] -- The list of strings that represent each event's information

    Returns:
        None at this point
    """
    with open('prompts.json', 'r') as file:
        prompts = json.load(file)
    
    with open(prompts[case]['dir'] + prompts[case]['rag_bad'], newline='') as file:
        rag_bad = list(csv.reader(file))

    with open(prompts[case]['dir'] + prompts[case]['rag_ok'], newline='') as file:
        rag_ok = list(csv.reader(file))

    api_string = prompts[case]["prompt"]+"\n"+"\n".join(data)

    response = openai_call(api_string)
    print(response)


def openai_call(prompt):
    """Calls OpenAI using the specified model and primpt, returns the response

    Args:
        prompt(str) the prompt string that is sent to the AI

    Returns:
        message_content(str) the response from the AI model
    """
    try:
        response = client.chat.completions.create(
             model=openai_model,
             messages=[{"role": "user", "content": prompt}
            ]
        )

        message_content = response.choices[0].message.content

    except Exception as e:
        print(f"An error occured: {e}")
    
    return(message_content)

def together_call(prompt):
    """Calls TogetherAI using the specified model and primpt, returns the response

    Args:
        prompt(str) the prompt string that is sent to the AI

    Returns:
        message_content(str) the response from the AI model
    """
    try:
        response = client2.chat.completions.create(
            model=togetherai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=None,
            temperature=0.7,
            top_p=0.7,
            top_k=50,
            repitition_penalty=1,
        )

        message_content = response.choices[0].message.content

    except Exception as e:
        print(f"An error occured: {e}")
    
    return(message_content)

main(case, test_data)
