from os.path import dirname, join
import json
import requests
import os
from requests.auth import HTTPBasicAuth
import logging

connector_defs = json.loads(open(join(dirname(__file__), "connector_def.json"), "r").read())

for conn_def in connector_defs["definitions"]:
    try:
        requests.post(
            f"http://localhost:{os.environ['PORT']}/api/v1/superuser/connectors/create",
            json={"type": conn_def["type"].upper() + "_" + conn_def["unique_name"].upper()},
            auth=HTTPBasicAuth(os.environ['ADMIN_EMAIL'], os.environ['ADMIN_PASSWORD']),
        )
    except:
        logging.exception("Failed to create connector. May exist already. Do better - continuing...")
