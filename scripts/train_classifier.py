import numpy as np
import json
import re
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline


def text_cleaner(text):
    text = text.strip()
    text = text.lower()
    text = re.sub(r'\b\d+\b', ' digit ', text)
    return text


def load_data():
    data = {'text': [], 'tag': []}
    for line in open('../test_data.txt', encoding='utf-8').readlines():
        if line[0] != '#':  # Комментарий
            text, tag = line.split('@')
            text = text_cleaner(text)

            data['text'].append(text)
            data['tag'].append(tag.lstrip())
    return data


def train(data):
    size = len(data['text'])
    indices = np.arange(size)
    np.random.shuffle(indices)

    return {
        'x': [data['text'][i] for i in indices],
        'y': [data['tag'][i] for i in indices]
    }


def load_json(path):
    data = {'text': [], 'tag': []}
    with open(f'{path}/data.json', 'r', encoding='UTF-8') as file:
        js = json.load(file)

    for i in js.keys():
        for j in js[i]:
            j = text_cleaner(j)
            data['text'].append(j)
            data['tag'].append(i)

    return data


def ai_classify(r, path):
    data = load_json(path)
    print(data)
    data = train(data)
    text_clf = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('clf', SGDClassifier(loss='hinge'))
    ])
    text_clf.fit(data['x'], data['y'])

    predicted = text_clf.predict([text_cleaner(r)])
    return predicted[0]

"""
{
  "имя": [
    "как тебя зовут",
    "моё имя - Андрей"
  ],
  "дата": [
    "когда родился Ленин",
    "дата моей свадьбы",
    "какое сегодня число"
  ]
}
"""