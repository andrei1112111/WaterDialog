import requests

data_get1 = {'login': '2', 'password': '2', 'id': '3', 'text': 'как а'}
data_get2 = {'login': '2', 'password': '2', 'id': '2'}
data_post = {'login': '2', 'password': '2', 'name': 'api_c_parser', 'api_users': ['1', '2'], 'for_all': False,
             'type': 'parser'}
files_post = {'data_file': open('parser.json', 'rb')}
data_put = {'login': '2', 'password': '2', 'id': '4', 'name': 'apic_parser'}
data_delete = {'login': '2', 'password': '2', 'id': '4'}
# r = requests.post('http://127.0.0.1:5000/api/settings', params=data_post, files=files_post).json()
# r = requests.delete('http://127.0.0.1:5000/api/settings', params=data_put).json()
r = requests.get('http://water-dialog.herokuapp.com/api', params=data_get1).json()

print(r)
