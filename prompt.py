import subprocess
import json
import csv
from openai import OpenAI


with open("openai_apikey", "r") as file:
        openai_key = file.read()


client = OpenAI(api_key=openai_key)



openai_model = "gpt-4o"
togetherai_model = "deepseek-ai/DeepSeek-V3"

=======
with open("apikey", "r") as file:
        key = file.read()
client = OpenAI(api_key=key)
#client2 = Together(api_key="")
ai_model = "gpt-4o"
>>>>>>> Stashed changes
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
    with open('prompts.json', 'r') as file:
        prompts = json.load(file)
    with open(prompts[case]['dir'] + prompts[case]['rag_bad'], newline='') as file:
        rag_bad = list(csv.reader(file))
    with open(prompts[case]['dir'] + prompts[case]['rag_ok'], newline='') as file:
        rag_ok = list(csv.reader(file))

    print(data)
    api_string = prompts[case]["prompt"]+"\n"+"\n".join(data)
    print(api_string)
    response = open_ai_call(api_string)
    print(response)
    return response
def open_ai_call(prompt):
    try:
        response = client.chat.completions.create(
             model=ai_model,
             messages=[{"role": "user", "content": prompt}
            ]
        )
        message_content = response.choices[0].message.content
    except Exception as e:
        print(f"An error occured: {e}")
    return(message_content)
