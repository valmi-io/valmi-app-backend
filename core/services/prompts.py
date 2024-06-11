import json
import logging
import requests
from decouple import config

from core.models import Credential
from core.schemas.prompt import (Filter, LastSuccessfulSyncInfo, TableInfo,
                                 TimeWindow)

logger = logging.getLogger(__name__)
ACTIVATION_URL = config("ACTIVATION_SERVER")


class PromptService():
    @classmethod
    def getTemplateFile(cls):
        return 'prompts.liquid'

    @staticmethod
    def build(tableInfo: TableInfo, timeWindow: TimeWindow, filters: list[Filter]) -> str:
        where_clause_conditions = " "
        for i, filter in enumerate(filters):
            if filter.column_type in ('integer', 'float'):
                where_clause_conditions += f" {filter.column} {filter.operator} {filter.value} "
            else:
                where_clause_conditions += f" {filter.column} {filter.operator} '{filter.value}' "
            if i != len(filters)-1:
                where_clause_conditions += " and "
        query = tableInfo.query.replace("{{schema}}", tableInfo.tableSchema).replace("{{filters}}", where_clause_conditions)
        logger.debug(f"prompt query built: {query}")
        return query


    @staticmethod
    def is_enabled(workspace_id: str, prompt: object) -> bool:
        connector_ids = list(Credential.objects.filter(workspace_id=workspace_id).values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        if isinstance(prompt, dict):
            return prompt["type"] in connector_types
        return prompt.type in connector_types

    @staticmethod
    def is_sync_finished(sync_id: str) -> LastSuccessfulSyncInfo:
        try:
            response = requests.get(f"{ACTIVATION_URL}/syncs/{sync_id}/last_successful_sync")
            json_string = response.content.decode('utf-8')
            logger.debug(json_string)
            last_success_sync_dict = json.loads(json_string)
            last_success_sync = LastSuccessfulSyncInfo(**last_success_sync_dict)
            logger.debug(last_success_sync)
            return last_success_sync
        except Exception as e:
            logger.exception(e)
            raise e
