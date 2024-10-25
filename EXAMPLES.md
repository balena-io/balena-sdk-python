# Pine Query Examples

This file presents a few tricks and tips regarding how to use the Pine queries more effectively, putting together some knowledge acquired while developing several applications using it. For an introduction to the Pine client, please check https://blog.balena.io/balena-python-sdk-v13/.


### Getting devices from a list of devices IDs/UUIDs

When we have a list of device UUIDs without any particular common grouping (all devices in a given application or all devices in a given organization) and want to get information about all these devices, we might be tempted to do something like:

```python
for device_uuid in list_of_device_uuids:
    device = sdk.models.device.get(device_uuid)
    do_something(device)
    ...
```
This works, but it can be rather slow as it has to get each device one by one. Instead, we can use:

```python
devices = sdk.models.device.get_all({
    "$filter": {
        "uuid": {
            "$in": list_of_device_uuids
        }
    }
})

for device in devices:
    do_something(device)
    ...
```

This second version, instead of requiring multiple round trips to the API, requires only one, which makes it faster and uses always 1 request instead of `len(list_of_device_uuids)`.

It is also interesting to mention that this pattern does not only work for `device` but for all resources in the balena API.


### Foreign key references

If we look at the typing for Foreign Key (FK) references, for example: a Device has an FK for a DeviceType on `is_of__device_type`. If we just query the device, for example:

```python
device = sdk.models.device.get(123)
print(device["is_of__device_type"])
```

The result will be a dictoinary containing only one key `__id`. Notice that if we add an `$expand`

```python
device = sdk.models.device.get(123, {"$expand": "is_of__device_type"})
print(device["is_of__device_type"])
```

The result is now a List of device types. The detail here is to notice that because in the underlying model this is a FK the List is guaranteed to have maximum size of 1. Notice that in the JS SDK we use Typescript to express this typing [here](https://github.com/balena-io/balena-sdk/blob/master/typings/pinejs-client-core.d.ts#L24) which means a either a PineDeferred (object with `__id`) or a list of maximum size 1 (and generic type T), whereas in Python type hint we just use a generic list [here](https://github.com/balena-io/balena-sdk-python/blob/master/balena/types/models.py#L10) of any size altough it is guaranteed that in runtime it will have maximum size of 1.
