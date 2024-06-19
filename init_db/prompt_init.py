import json
import logging
import os
import uuid
from os.path import dirname, join
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# Load prompt definitions
prompt_defs = json.loads(open(join(dirname(__file__), "prompt_def.json"), "r").read())

# Function to create or update prompt
def create_or_update_prompt(prompt_def):
    # Add a unique ID for prompt creation
    prompt_def['id'] = str(uuid.uuid4())

    # Attempt to create or update the prompt
    resp = requests.post(
        f"http://localhost:{os.environ['PORT']}/api/v1/superuser/prompts/create",
        json=prompt_def,
        auth=HTTPBasicAuth(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"]),
    )

    if resp.status_code == 200:
        logger.debug("Prompt created successfully")
        return
    

# Iterate through prompt definitions and create or update prompts
for prompt_def in prompt_defs["definitions"]:
    create_or_update_prompt(prompt_def)
