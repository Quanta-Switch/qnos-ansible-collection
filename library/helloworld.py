#!/usr/bin/python
# The following Python code converts a …
# for use with an Ansible module call
import json
message = "Hello Ansible"
print(json.dumps({
    "Message" : message
}))

