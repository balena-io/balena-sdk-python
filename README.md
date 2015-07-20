# resin-python-wrapper
A python wrapper for resin.io [work in progress]


## usage 

```
pip install resin
```

```
from resin import Client

client = Client(token=JWT)

device = client.device.get(uuid)

app = client.application.get_by_id(app_id) 

client.environment_variables.create(app_id, "EDITOR", "vim")
```