import datetime
import json
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import os
from os.path import dirname, join
from typing import List
import uuid
from decouple import config
import time
import json
from pydantic import Json
import requests

from core.api import create_new_run

from .models import OAuthApiKeys, Source
import psycopg2
from core.models import Account, Credential, Destination, Explore, Prompt, StorageCredentials, Workspace,Sync
from core.schemas import DetailSchema, ExploreSchema, ExploreSchemaIn, SyncStartStopSchemaIn
from ninja import Router

logger = logging.getLogger(__name__)

router = Router()
ACTIVATION_URL = config("ACTIVATION_SERVER")

@router.get("/workspaces/{workspace_id}", response={200: List[ExploreSchema], 400: DetailSchema})
def get_explores(request,workspace_id):
    try:
        logger.debug("listing explores")
        workspace = Workspace.objects.get(id=workspace_id)
        return Explore.objects.filter(workspace=workspace)
    except Exception:
        logger.exception("explores listing error")
        return (400, {"detail": "The list of explores cannot be fetched."})


@router.post("/workspaces/{workspace_id}/create",response={200: ExploreSchema, 400: DetailSchema})
def create_explore(request, workspace_id,payload: ExploreSchemaIn):
    logger.info("logging rquest")
    logger.info(request.user)
    logger.info("data before creating")
    data = payload.dict()
    logger.info("data before creating")
    logger.info(data)
    try:
        data["id"] = uuid.uuid4()
        data["workspace"] = Workspace.objects.get(id=workspace_id)
        prompt = Prompt.objects.get(id=data["prompt_id"])
        data["prompt"] = prompt
        account_info = data.pop("account", None)
        account = {}
        if account_info and len(account_info) > 0:
            account_info["id"] = uuid.uuid4()
            account_info["workspace"] = data["workspace"]
            account = Account.objects.create(**account_info)
            data["account"] = account
        logger.debug(data)
        oauthkeys = OAuthApiKeys.objects.get(workspace_id=workspace_id,type="GOOGLE_LOGIN")
        src_credential = {"id": uuid.uuid4()}
        src_credential["workspace"] = Workspace.objects.get(id=workspace_id)
        src_credential["connector_id"] = "SRC_POSTGRES"
        src_credential["name"] = "SRC_POSTGRES 2819"
        src_credential["account"] = account
        src_credential["status"] = "active"
        #TODO: give nice nmaes for each creation(sync,credentials,sources,destination)
        storage_credential = StorageCredentials.objects.get(workspace_id = workspace_id)
        src_connector_config = {
            "ssl": False,
            "host": "classspace.in",
            "port": 5432,
            "user": storage_credential.connector_config["username"],
            "database": "dvdrental",
            "password": storage_credential.connector_config["password"],
            "namespace": storage_credential.connector_config["namespace"],
        }
        src_credential["connector_config"] = src_connector_config
        src_cred = Credential.objects.create(**src_credential)
        logger.info(src_cred)
        des_credential = {"id": uuid.uuid4()}
        des_credential["workspace"] = Workspace.objects.get(id=workspace_id)
        des_credential["connector_id"] = "DEST_GOOGLE-SHEETS"
        des_credential["name"] = "DEST_GOOGLE-SHEETS 2819"
        des_credential["account"] = account
        des_credential["status"] = "active"
        name = f"valmi.io {prompt.name}"
        spreadsheet_url = create_spreadsheet(name,refresh_token=oauthkeys.oauth_config["refresh_token"])
        des_connector_config = {
            "spreadsheet_id": spreadsheet_url,
            "credentials": {
               "client_id": os.environ["NEXTAUTH_GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["NEXTAUTH_GOOGLE_CLIENT_SECRET"],
                "refresh_token": oauthkeys.oauth_config["refresh_token"],
            },
        }
        des_credential["connector_config"] = des_connector_config
        des_cred = Credential.objects.create(**des_credential)
        source_connector = {
            "name":"SRC_POSTGRES 2819",
            "id":uuid.uuid4()
        }
        source_connector["workspace"] = Workspace.objects.get(id=workspace_id)
        source_connector["credential"] = Credential.objects.get(id=src_cred.id)
        source_connector_catalog = {}
        json_file_path = join(dirname(__file__), 'source_catalog.json')
        with open(json_file_path, 'r') as openfile:
            source_connector_catalog = json.load(openfile)
        source_connector["catalog"] = source_connector_catalog
        source_connector["status"] = "active"
        src_connector = Source.objects.create(**source_connector)
        logger.info(src_connector)
        time.sleep(3)
        destination_connector = {
            "name":"DEST_GOOGLE-SHEETS 2819",
            "id":uuid.uuid4()

        }
        destination_connector["workspace"] = Workspace.objects.get(id=workspace_id)
        destination_connector["credential"] = Credential.objects.get(id=des_cred.id)
        destination_connector_catalog = {}
        json_file_path = join(dirname(__file__), 'destination_catalog.json')
        with open(json_file_path, 'r') as openfile:
            destination_connector_catalog = json.load(openfile)
        destination_connector["catalog"] = destination_connector_catalog
        des_connector = Destination.objects.create(**destination_connector)
        logger.info(des_connector)
        time.sleep(3)
        sync_config = {
            "name":"test 2819",
            "id":uuid.uuid4(),
            "status":"active",
            "ui_state":{}

        }
        schedule = {"run_interval": 3600000}
        sync_config["schedule"] = schedule
        sync_config["source"] = Source.objects.get(id=src_connector.id)
        sync_config["destination"] = Destination.objects.get(id=des_connector.id)
        sync_config["workspace"] = Workspace.objects.get(id=workspace_id)
        sync = Sync.objects.create(**sync_config)
        logger.info(sync)
        time.sleep(10)
        payload = SyncStartStopSchemaIn(full_refresh=True)
        response = create_new_run(request,workspace_id,sync.id,payload)
        print(response)
        data["name"] = name
        data["sync"] = sync
        explore =  Explore.objects.create(**data)
        explore.spreadsheet_url = spreadsheet_url
        explore.save()
        return explore
    except Exception:
        logger.exception("explore creation error")
        return (400, {"detail": "The specific explore cannot be created."})
    

def custom_serializer(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    
@router.get("/workspaces/{workspace_id}/prompts/{prompt_id}/preview",response={200: Json, 404: DetailSchema})
def preview_data(request, workspace_id,prompt_id):
    prompt = Prompt.objects.get(id=prompt_id)
    storage_cred = StorageCredentials.objects.get(workspace_id=workspace_id)
    host_url = os.environ["DATA_WAREHOUSE_URL"]
    db_password = storage_cred.connector_config.get('password')
    db_username = storage_cred.connector_config.get('username')
    db_namespace = storage_cred.connector_config.get('namespace')
    conn = psycopg2.connect(host=host_url,port="5432",database="dvdrental",user=db_username,password=db_password)
    cursor = conn.cursor()
    table = prompt.table
    # LOGIC for implementing pagination if necessary
    # query = f'SELECT COUNT(*) FROM {db_namespace}.{table}'
    # cursor.execute(query)
    # count_row = cursor.fetchone()
    # count = count_row[0] if count_row is not None else 0
    # page_id_int = int(page_id)

    # if page_id_int > count/25 or page_id_int<=0:
    #     return (404, {"detail": "Invalid page Id."})
    # skip = 25*(page_id_int-1)
    query = f'SELECT * FROM {db_namespace}.{table} LIMIT 100'
    cursor.execute(query)
    items = [dict(zip([key[0] for key in cursor.description], row)) for row in cursor.fetchall()]
    return json.dumps(items, indent=4, default=custom_serializer)


@router.get("/workspaces/{workspace_id}/{explore_id}", response={200: ExploreSchema, 400: DetailSchema})
def get_explores(request,workspace_id,explore_id):
    try:
        logger.debug("listing explores")
        return Explore.objects.get(id=explore_id)
    except Exception:
        logger.exception("explore listing error")
        return (400, {"detail": "The  explore cannot be fetched."})

def create_spreadsheet(name,refresh_token):
    logger.debug("create_spreadsheet")
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials_dict = {
        "client_id": os.environ["NEXTAUTH_GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["NEXTAUTH_GOOGLE_CLIENT_SECRET"],
        "refresh_token": refresh_token
    }
    sheet_name = f'{name} sheet'
    # Create a Credentials object from the dictionary
    credentials = Credentials.from_authorized_user_info(
        credentials_dict, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    # Create the spreadsheet
    spreadsheet = {"properties": {"title": sheet_name}}
    try:
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
        return e


@router.get("/workspaces/{workspace_id}/{explore_id}/status", response={200: Json, 400: DetailSchema})
def get_explore_status(request,workspace_id,explore_id):
    try:
        logger.debug("getting_explore_status")
        explore = Explore.objects.get(id=explore_id)
        if explore.ready:
            return "sync completed"
        sync_id = explore.sync.id
        response = requests.get(f"{ACTIVATION_URL}/syncs/{sync_id}/latestRunStatus")
        status = response.text
        print(status)
        # if status == 'stopped':
        #     CODE for re running the sync from backend
        #     payload = SyncStartStopSchemaIn(full_refresh=True)       
        #     response = create_new_run(request,workspace_id,sync_id,payload)
        #     print(response)
        #     return "sync got failed. Please re-try again"
        response = {}
        if status == '"running"':
            response["status"] = "running"
            return json.dumps(response)
        if status == '"failed"':
            response["status"] = "failed"
            return json.dumps(response)
        explore.ready = True
        explore.save()
        response["status"] = "success"
        return json.dumps(response)
    except Exception:
        logger.exception("get_explore_status error")
        return (400, {"detail": "The  explore cannot be fetched."})
