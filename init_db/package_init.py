"""
Copyright (c) 2024 valmi.io <https://github.com/valmi-io>

Created Date: Wednesday, April 11th 2024, 9:56:52 pm
Author: Rajashekar Varkala @ valmi.io

"""


from os.path import dirname, join
import json
import logging
import requests
import os
from requests.auth import HTTPBasicAuth
logger = logging.getLogger(__name__)

package_defs = json.loads(open(join(dirname(__file__), "package_def.json"), "r").read())

for package_def in package_defs["definitions"]:
    resp = requests.post(
        f"http://localhost:{os.environ['PORT']}/api/v1/superuser/packages/create",
        json={
            "name": package_def["name"],
            "scopes":package_def["scopes"],
            "gated":package_def["gated"],
        },
        auth=HTTPBasicAuth(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"]),
    )
    if resp.status_code != 200:
        print("Failed to create package. May exist already. Do better - continuing...")
