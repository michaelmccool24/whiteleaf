import json

with open('test_data.json', 'r') as file:
    data_dict = json.load(file)
    prompt_key = next(iter(data_dict))
    values_list = [prompt_key] + list(data_dict.values())

    flattened_list = [values_list[0]] + values_list[1]

    print(flattened_list)
