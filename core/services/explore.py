import asyncio
import json
import logging
import os
import re
import uuid
from os.path import dirname, join
from typing import List, Union

import requests
from decouple import config
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from core.models import (Credential, Destination, Explore, OAuthApiKeys,
                         Prompt, Source, StorageCredentials, Sync, Workspace)
from core.routes.workspace_api import create_new_run
from core.schemas.explore import LatestSyncInfo
from core.schemas.prompt import Filter, TableInfo, TimeWindow
from core.services.prompts import PromptService

logger = logging.getLogger(__name__)
ACTIVATION_URL = config("ACTIVATION_SERVER")
SPREADSHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']


class ExploreService:
    @staticmethod
    def create_spreadsheet(title: str, name: str, refresh_token: str) -> str:
        logger.debug("create_spreadsheet")
        credentials_dict = {
            "client_id": os.environ["NEXTAUTH_GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["NEXTAUTH_GOOGLE_CLIENT_SECRET"],
            "refresh_token": refresh_token
        }
        # Create a Credentials object from the dictionary
        try:
            base_spreadsheet_url = "https://docs.google.com/spreadsheets/d/"
            credentials = Credentials.from_authorized_user_info(
                credentials_dict, scopes=SPREADSHEET_SCOPES
            )
            service = build("sheets", "v4", credentials=credentials)
            # Create the spreadsheet
            spreadsheet = {
                "properties": {
                    "title": title,
                },
                "sheets": [
                    {
                        "properties": {
                            "title": name
                        }
                    }
                ]}
            spreadsheet = (
                service.spreadsheets()
                .create(body=spreadsheet, fields="spreadsheetId")
                .execute()
            )
            spreadsheet_id = spreadsheet.get("spreadsheetId")
            # Update the sharing settings to make the spreadsheet publicly accessible
            # drive_service = build('drive', 'v3', credentials=credentials)
            # drive_service.permissions().create(
            #     fileId=spreadsheet_id,
            #     body={
            #         "role": "writer",
            #         "type": "anyone",
            #         "withLink": True
            #     },
            #     fields="id"
            # ).execute()

            spreadsheet_url = f"{base_spreadsheet_url}{spreadsheet_id}"
            return spreadsheet_url
        except Exception as e:
            logger.exception(f"Error creating spreadsheet: {e}")
            raise Exception("spreadhseet creation failed")

    @staticmethod
    def create_source(explore_table_name: str, prompt_id: str, schema_id: str, time_window: TimeWindow, filters: list[Filter], workspace_id: str, account: object) -> object:
        try:
            # creating source credentail
            credential = {"id": uuid.uuid4()}
            credential["workspace"] = Workspace.objects.get(id=workspace_id)
            credential["connector_id"] = "SRC_POSTGRES"
            credential["name"] = "VALMI_ENGINE"
            credential["account"] = account
            credential["status"] = "active"
            # building query
            logger.debug(type(time_window))
            prompt = Prompt.objects.get(id=prompt_id)
            storage_credential = StorageCredentials.objects.get(id=schema_id)
            namespace = storage_credential.connector_config["namespace"]
            table_info = TableInfo(
                tableSchema=namespace,
                query=prompt.query
            )
            query = PromptService().build(table_info, time_window, filters)
            # creating source credentials
            connector_config = {
                "ssl": storage_credential.connector_config["ssl"],
                "host": storage_credential.connector_config["host"],
                "port": storage_credential.connector_config["port"],
                "user": storage_credential.connector_config["username"],
                "database": storage_credential.connector_config["database"],
                "password": storage_credential.connector_config["password"],
                "namespace": storage_credential.connector_config["namespace"],
                "query": query
            }
            credential["connector_config"] = connector_config
            cred = Credential.objects.create(**credential)
            source = {
                "name": "VALMI_ENGINE",
                "id": uuid.uuid4()
            }
            # creating source object
            source["workspace"] = Workspace.objects.get(id=workspace_id)
            source["credential"] = Credential.objects.get(id=cred.id)
            namespace = storage_credential.connector_config["namespace"]
            # creating source catalog
            url = f"{ACTIVATION_URL}/connectors/SRC_POSTGRES/discover"
            config = {
                'docker_image': 'valmiio/source-postgres',
                'docker_tag': 'latest',
                'config': connector_config
            }
            response = requests.post(url, json=config)
            response_json = response.json()
            json_file_path = join(dirname(__file__), 'source_catalog.json')
            with open(json_file_path, 'r') as openfile:
                source_catalog = json.load(openfile)
            source_catalog["streams"][0]["stream"] = response_json["catalog"]["streams"][0]
            source_catalog["streams"][0]["stream"][
                "name"
            ] = explore_table_name
            source["catalog"] = source_catalog
            source["status"] = "active"
            logger.debug(source_catalog)
            result = Source.objects.create(**source)
            return result
        except Exception as e:
            logger.exception(f"Error creating source: {e}")
            raise Exception("unable to create source")

    @staticmethod
    def create_destination(spreadsheet_title: str, spreadsheet_name: str, sheet_url: str, workspace_id: str, account: object) -> List[Union[str, object]]:
        try:
            # creating destination credential
            oauthkeys = OAuthApiKeys.objects.get(workspace_id=workspace_id, type="GOOGLE_LOGIN")
            credential = {"id": uuid.uuid4()}
            credential["workspace"] = Workspace.objects.get(id=workspace_id)
            credential["connector_id"] = "DEST_GOOGLE-SHEETS"
            credential["name"] = "DEST_GOOGLE-SHEETS"
            credential["account"] = account
            credential["status"] = "active"
            # if sheet url is none create a new sheet
            if sheet_url is None:
                spreadsheet_url = ExploreService.create_spreadsheet(
                    spreadsheet_title, spreadsheet_name, refresh_token=oauthkeys.oauth_config["refresh_token"])
            else:
                spreadsheet_url = sheet_url
            connector_config = {
                "spreadsheet_id": spreadsheet_url,
                "credentials": {
                    "client_id": os.environ["NEXTAUTH_GOOGLE_CLIENT_ID"],
                    "client_secret": os.environ["NEXTAUTH_GOOGLE_CLIENT_SECRET"],
                    "refresh_token": oauthkeys.oauth_config["refresh_token"],
                },
            }
            credential["connector_config"] = connector_config
            cred = Credential.objects.create(**credential)
            destination = {
                "name": "DEST_GOOGLE-SHEETS",
                "id": uuid.uuid4()

            }
            # creating destination object
            destination["workspace"] = Workspace.objects.get(id=workspace_id)
            destination["credential"] = Credential.objects.get(id=cred.id)
            destination_catalog = {}
            json_file_path = join(dirname(__file__), 'destination_catalog.json')
            with open(json_file_path, 'r') as openfile:
                destination_catalog = json.load(openfile)
            destination["catalog"] = destination_catalog
            result = Destination.objects.create(**destination)
            logger.info(result)
            return [spreadsheet_url, result]
        except Exception as e:
            logger.exception(f"Error creating destination: {e}")
            raise Exception("unable to create destination")

    @staticmethod
    def create_sync(source: object, destination: object, workspace_id: str) -> object:
        try:
            logger.debug("creating sync in service")
            logger.debug(source.id)
            sync_config = {
                "name": "Warehouse to sheets",
                "id": uuid.uuid4(),
                "status": "active",
                "ui_state": {}

            }
            schedule = {"run_interval": 3600000}
            sync_config["schedule"] = schedule
            sync_config["source"] = source
            sync_config["destination"] = destination
            sync_config["workspace"] = Workspace.objects.get(id=workspace_id)
            sync = Sync.objects.create(**sync_config)
            return sync
        except Exception as e:
            logger.exception(f"Error creating sync: {e}")
            raise Exception("unable to create sync")

    @staticmethod
    async def wait_for_run(time: int):
        await asyncio.sleep(time)

    @staticmethod
    def create_run(request: object, workspace_id: str, sync_id: str, payload: object) -> None:
        try:
            response = create_new_run(request, workspace_id, sync_id, payload)
            logger.debug(response)
        except Exception as e:
            logger.exception(f"Error creating run: {e}")
            raise Exception("unable to create run")

    @staticmethod
    def get_latest_sync_info(sync_id: str) -> LatestSyncInfo:
        try:
            response = requests.get(f"{ACTIVATION_URL}/syncs/{sync_id}/latest_sync_info")
            json_string = response.content.decode('utf-8')
            latest_sync_info_dict = json.loads(json_string)
            latest_sync_info = LatestSyncInfo(**latest_sync_info_dict)
            return latest_sync_info
        except Exception as e:
            logger.exception(f"Error : {e}")
            raise Exception("unable to query activation")

    @staticmethod
    def validate_explore_name(name: str, workspace_id: str) -> str:
        if Explore.objects.filter(workspace_id=workspace_id, name=name).exists():
            raise Exception(f"The name '{name}' already exists. Please provide a different name.")
        if re.match(r'^\d', name):
            raise Exception(f"Explore name cannot start with a number.")
        name = re.sub(r'[^a-zA-Z0-9]', '_', name)
        return name

    @staticmethod
    def extract_spreadsheet_id(sheet_url: str) -> str:
        pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, sheet_url)
        if match:
            return match.group(1)
        else:
            return None

    @ staticmethod
    # check wether the given sheet is accessible using the stored refresh token
    def is_sheet_accessible(sheet_url: str, workspace_id: str) -> bool:
        try:
            oauthkeys = OAuthApiKeys.objects.get(workspace_id=workspace_id, type="GOOGLE_LOGIN")
            credentials_dict = {
                "client_id": os.environ["NEXTAUTH_GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["NEXTAUTH_GOOGLE_CLIENT_SECRET"],
                "refresh_token": oauthkeys.oauth_config["refresh_token"]
            }
            credentials = Credentials.from_authorized_user_info(
                credentials_dict, scopes=SPREADSHEET_SCOPES
            )
            drive_service = build('drive', 'v3', credentials=credentials)

            spreadsheet_id = ExploreService.extract_spreadsheet_id(sheet_url)

            # Check if the file exists if file does not exist it will throw an exception
            try:
                response = drive_service.files().get(fileId=spreadsheet_id).execute()
            except Exception as e:
                return False
            spreadsheet_metadata = drive_service.files().get(fileId=spreadsheet_id, fields='id, permissions').execute()

            # Check permissions to see if the file is accessible
            permissions = spreadsheet_metadata.get('permissions', [])
            for permission in permissions:
                if (permission.get('type') == 'user' and permission.get('role') == 'writer') or (permission.get('type') == 'domain' and permission.get('role') == 'writer') or (permission.get('type') == 'anyone' and permission.get('role') == 'writer'):
                    return True
            return False
        except Exception as e:
            logger.exception(f"Error : {e}")
            raise Exception(e)
