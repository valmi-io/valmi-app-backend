"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, April 11th 2024, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""

import json
import logging
import os
import uuid
from os.path import dirname, join

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

prompt_defs = json.loads(open(join(dirname(__file__), "prompt_def.json"), "r").read())

for prompt_def in prompt_defs["definitions"]:
    logger.debug(prompt_def)
    resp = requests.post(
        f"http://localhost:{os.environ['PORT']}/api/v1/superuser/prompts/create",
        json={
            "id": str(uuid.uuid4()),
            "name": prompt_def["name"],
            "description": prompt_def["description"],
            "type": prompt_def["type"],
            "query": prompt_def["query"],
            "spec": prompt_def["spec"],
            "package_id": prompt_def["package_id"],
            "gated": prompt_def["gated"],
        },
        auth=HTTPBasicAuth(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"]),
    )
    if resp.status_code != 200:
        print("Failed to create prompt. May exist already. Do better - continuing...")
