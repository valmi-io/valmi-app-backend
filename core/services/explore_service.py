import json
import logging
import os
import uuid
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from os.path import dirname, join
from core.api import create_new_run
from core.models import Credential, Destination, OAuthApiKeys, Source, StorageCredentials, Sync, Workspace
logger = logging.getLogger(__name__)
class ExploreService:
    @staticmethod
    def create_spreadsheet(name:str,refresh_token:str):
        logger.debug("create_spreadsheet")
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        credentials_dict = {
            "client_id": os.environ["NEXTAUTH_GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["NEXTAUTH_GOOGLE_CLIENT_SECRET"],
            "refresh_token": refresh_token
        }
        # Create a Credentials object from the dictionary
        try:
            credentials = Credentials.from_authorized_user_info(
             credentials_dict, scopes=SCOPES
            )
            service = build("sheets", "v4", credentials=credentials)
            # Create the spreadsheet
            spreadsheet = {"properties": {"title": name}}
            spreadsheet = (
                service.spreadsheets()
                .create(body=spreadsheet, fields="spreadsheetId")
                .execute()
            )
            spreadsheet_id = spreadsheet.get("spreadsheetId")
            #Update the sharing settings to make the spreadsheet publicly accessible
            drive_service = build('drive', 'v3', credentials=credentials)
            drive_service.permissions().create(
                fileId=spreadsheet_id,
                body={
                    "role": "writer",
                    "type": "anyone",
                    "withLink": True
                },  
                fields="id"
            ).execute()

            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
            print(f"Spreadsheet URL: {spreadsheet_url}")
            return spreadsheet_url
        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
            raise Exception("spreadhseet creationm failed")
    
    @staticmethod
    def create_source(workspace_id,account:object):
        try:
            #creating source credentail
            credential = {"id": uuid.uuid4()}
            credential["workspace"] = Workspace.objects.get(id=workspace_id)
            credential["connector_id"] = "SRC_POSTGRES"
            credential["name"] = "SRC_POSTGRES"
            credential["account"] = account
            credential["status"] = "active"
            storage_credential = StorageCredentials.objects.get(workspace_id = workspace_id)
            connector_config = {
                "ssl": False,
                "host": storage_credential.connector_config["host"],
                "port": storage_credential.connector_config["port"],
                "user": storage_credential.connector_config["username"],
                "database": storage_credential.connector_config["database"],
                "password": storage_credential.connector_config["password"],
                "namespace": storage_credential.connector_config["namespace"],
            }
            credential["connector_config"] = connector_config
            cred = Credential.objects.create(**credential)
            source = {
            "name":"SRC_POSTGRES",
            "id":uuid.uuid4()
            }
            #creating source object
            source["workspace"] = Workspace.objects.get(id=workspace_id)
            source["credential"] = Credential.objects.get(id=cred.id)
            source_catalog = {}
            json_file_path = join(dirname(__file__), 'source_catalog.json')
            with open(json_file_path, 'r') as openfile:
                source_catalog = json.load(openfile)
            source["catalog"] = source_catalog
            source["status"] = "active"
            result = Source.objects.create(**source)
            return result
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            raise Exception("unable to create source")
    
    @staticmethod
    def create_destination(spreadsheet_name:str,workspace_id,account:object):
        try:
            #creating destination credential
            oauthkeys = OAuthApiKeys.objects.get(workspace_id=workspace_id,type="GOOGLE_LOGIN")
            credential = {"id": uuid.uuid4()}
            credential["workspace"] = Workspace.objects.get(id=workspace_id)
            credential["connector_id"] = "DEST_GOOGLE-SHEETS"
            credential["name"] = "DEST_GOOGLE-SHEETS"
            credential["account"] = account
            credential["status"] = "active"
            spreadsheet_url = ExploreService.create_spreadsheet(spreadsheet_name,refresh_token=oauthkeys.oauth_config["refresh_token"])
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
            destination= {
            "name":"DEST_GOOGLE-SHEETS",
            "id":uuid.uuid4()

            }
            #creating destination object
            destination["workspace"] = Workspace.objects.get(id=workspace_id)
            destination["credential"] = Credential.objects.get(id=cred.id)
            destination_catalog = {}
            json_file_path = join(dirname(__file__), 'destination_catalog.json')
            with open(json_file_path, 'r') as openfile:
                destination_catalog = json.load(openfile)
            destination["catalog"] = destination_catalog
            result = Destination.objects.create(**destination)
            logger.info(result)
            return result
        except Exception as e:
            logger.error(f"Error creating destination: {e}")
            raise Exception("unable to create destination")
        
    @staticmethod
    def create_sync(source:object,destination:object,workspace_id):
        try:
            logger.debug("creating sync in service")
            logger.debug(source.id)
            sync_config = {
            "name":"Warehouse to sheets",
            "id":uuid.uuid4(),
            "status":"active",
            "ui_state":{}

            }
            schedule = {"run_interval": 3600000}
            sync_config["schedule"] = schedule
            sync_config["source"] = source
            sync_config["destination"] = destination
            sync_config["workspace"] = Workspace.objects.get(id=workspace_id)
            sync = Sync.objects.create(**sync_config)
            return sync
        except Exception as e:
            logger.error(f"Error creating sync: {e}")
            raise Exception("unable to create sync")

    @staticmethod
    def create_run(request,workspace_id,sync_id,payload):
        try:
             response = create_new_run(request,workspace_id,sync_id,payload)
             logger.debug(response)
        except Exception as e:
            logger.error(f"Error creating run: {e}")
            raise Exception("unable to create run")