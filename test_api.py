import requests

data = {
    'url': '',
    'text': 'Scientists have just discovered a massive alien spaceship hiding behind the moon.'
}
try:
    response = requests.post('http://127.0.0.1:5000/api/evaluate', json=data)
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
