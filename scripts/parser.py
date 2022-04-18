from yargy import Parser, rule
from yargy.predicates import gram, dictionary, type as type_p
import json


def load(path):
    with open(f'{path}/data.json', 'r', encoding='UTF-8') as file:
        return json.load(file)


def to_rule(data):
    result = []
    for i in data:
        r = []
        if "gram" in i.keys():
            r.append(gram(i["gram"]))
        if "dictionary" in i.keys():
            for j in i["dictionary"]:
                r.append(dictionary({k for k in j}))
        if "arg" in i.keys():
            r.append(type_p(i["arg"].upper()).repeatable())
        r = rule(*r), i['name']
        result.append(r)
    return result


def parse_text_rules(text, path):
    rules = to_rule(path)
    result = {}
    for r in rules:
        parser = Parser(r[0])
        result[r[1]] = []
        for match in parser.findall(text):
            result[r[1]].append([x.value for x in match.tokens])
    return result
