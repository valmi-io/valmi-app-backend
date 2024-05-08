"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, April 11th 2024, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

from os.path import dirname, join
import json
import uuid
import requests
import os
from requests.auth import HTTPBasicAuth


prompt_defs = json.loads(open(join(dirname(__file__), "test_prompt_def.json"), "r").read())

for prompt_def in prompt_defs["definitions"]:
    resp = requests.post(
        f"http://localhost:{os.environ['PORT']}/api/v1/superuser/prompts/create",
        json={
            "id":str(uuid.uuid4()),
            "name": prompt_def["name"],
            "description": prompt_def["description"],
            "type": prompt_def["type"],
            "table":prompt_def["table"],
            "spec":prompt_def["spec"],
            "package_id":prompt_def["package_id"],
            "gated":prompt_def["gated"],
        },
        auth=HTTPBasicAuth(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"]),
    )
    if resp.status_code != 200:
        print("Failed to create prompt. May exist already. Do better - continuing...")
