
Install:
`python -m pip install -e .`

Use:
```python
import serialize_to_py

reusedObject = {'key': 'value'}
reusedObject['cyclicSelf'] = reusedObject
ob = {
    "s": "hello world!",
    "num": 3.1415,
    "bool": True,
    "None": None,
    "ob": {"foo": "bar", "reusedObject": reusedObject},
    "arr": [1, "2", reusedObject],
}
print(serialize_to_py.serialize(ob))
```

Will output:
```python

def serialise_to_python_temporary_function():
  root = {
    "s": "hello world!",
    "num": 3.1415,
    "bool": True,
    "None": None,
    "ob": {
      "foo": "bar",
      "reusedObject": {
        "key": "value",
        "cyclicSelf": 'Linked later'
      }
    },
    "arr": [
      1,
      "2",
      "Linked later"
    ]
  }
  root["ob"]["reusedObject"]["cyclicSelf"] = root["ob"]["reusedObject"];
  root["arr"] = root["ob"]["reusedObject"]

  return root
serialise_to_python_temporary_function()
```

Format:
`black --line-length 120 .`
