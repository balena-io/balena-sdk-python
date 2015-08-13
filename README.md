# resin-python-wrapper
A python wrapper for resin.io [work in progress]


## usage 

```
from resin import Client

client = Client()

device = client.auth.login(**credentials)
(Example: credentials={'username': YOUR USERNAME, 'password': YOUR PASSWORD})

app = client.models.application.get_by_id(app_id) 

device = client.models.device.get(uuid)
```

This project is work in progress so the API config is now pointing at our staging server.
If anyone wants to pre-test, please change the `'pine_endpoint'` to `'https://api.resin.io/ewa/'` and `'api_endpoint'` to `'https://api.resin.io/'` in `settings.py`.
