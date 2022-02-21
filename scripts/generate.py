import os


def generate(data=None):
    sp = []
    if data:
        data = data.split('|')
        for i in data:
            if '@' in i:
                sp.append(i.split("@"))
                # sp += f"""<li>\n<input name="ch" type="button" value="{i.split("@")[0]}"
            # onclick="window.location.href = 'http://127.0.0.1:5000/api/config/{i}';">  {i.split("@")[1]}\n</li>\n"""
    return sp


def correct_login(login):
    if len(login) < 17 and \
            all([s in 'abcdefghigklmnopqrstuvwxyz_-1234567890' for s in login.lower()]):
        return True


def correct_file(file, rule='.json'):
    if rule in file and '.' not in file.replace(rule, ''):
        return True


def exists(path):
    try:
        os.stat(path)
    except OSError:
        return False
    return True
