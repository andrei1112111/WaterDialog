import requests

data_get1 = {'login': '1', 'password': '1', 'id': '2', 'text': 'заказ номер 123: вишневый морс; яблочный компот'}
# data_get1 = {'login': '1', 'password': '1', 'id': '3', 'text': 'Когда ты родился'}
data_get2 = {'login': '1', 'password': '1', 'id': '3'}
data_post = {'login': '1', 'password': '1', 'name': 'api_c_parser', 'api_users': ['1', '2'], 'for_all': False,
             'type': 'parser'}
files_post = {'data_file': open('parser.json', 'rb')}
data_put = {'login': '2', 'password': '2', 'id': '4', 'name': 'apic_parser'}
data_delete = {'login': '1', 'password': '1', 'id': '3'}
# r = requests.post('http://water-dialog.herokuapp.com/api/settings', params=data_post, files=files_post).json()
# r = requests.delete('http://water-dialog.herokuapp.com/api/settings', params=data_delete).json()
r = requests.get('http://water-dialog.herokuapp.com/api', params=data_get1).json()
# r = requests.get('http://water-dialog.herokuapp.com/api/settings', params=data_get2).json()

print(r)
