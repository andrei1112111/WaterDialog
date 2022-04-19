import os


def generate(data=None):
    sp = []
    if data:
        data = data.split('|')
        for i in data:
            if '@' in i:
                sp.append(i.split("@"))
    return sp


def correct_login(login):
    if len(login) < 17 and \
            all([s in 'abcdefghigklmnopqrstuvwxyz_-1234567890' for s in login.lower()]):
        return True


def correct_data(data, rule):
    data = data.strip()
    data = data.replace('\n', '').replace('\r', '').replace('\t', '')
    if rule == 'cl':
        if data[0] == '{' and data[-1] == ']}':
            return True
    elif rule == 'pa':
        if data[0] == '[{' and data[-1] == '}]':
            return True
    return False


def correct_file(file):
    if '.json' in file and '.' not in file.replace('.json', ''):
        return True


def exists(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True
