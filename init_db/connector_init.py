"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, March 8th 2023, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

from os.path import dirname, join
import json
import requests
import os
from requests.auth import HTTPBasicAuth

connector_defs = json.loads(open(join(dirname(__file__), "connector_def.json"), "r").read())

for conn_def in connector_defs["definitions"]:
    resp = requests.post(
        f"http://localhost:{os.environ['PORT']}/api/v1/superuser/connectors/create",
        json={
            "type": conn_def["type"].upper() + "_" + conn_def["unique_name"].upper(),
            "display_name": conn_def["display_name"],
            "docker_image": conn_def["docker_image"],
            "docker_tag": conn_def["docker_tag"],
            "oauth": conn_def["oauth"],
            "oauth_keys": conn_def["oauth_keys"],
            "mode": conn_def["mode"],
        },
        auth=HTTPBasicAuth(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"]),
    )
    if resp.status_code != 200:
        print("Failed to create connector. May exist already. Do better - continuing...")
