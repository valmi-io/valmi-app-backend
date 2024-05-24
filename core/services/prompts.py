import json
import logging
from pathlib import Path

import requests


from core.models import Credential, SourceAccessInfo, Sync
from liquid import Environment, FileSystemLoader, Mode, StrictUndefined

from core.schemas.prompt import TimeWindow, Filter
from decouple import config
logger = logging.getLogger(__name__)
ACTIVATION_URL = config("ACTIVATION_SERVER")


class PromptService():
    @classmethod
    def getTemplateFile(cls):
        return 'prompts.liquid'

    @staticmethod
    def build(table, timeWindow: TimeWindow, filters: list[Filter]) -> str:
        try:
            if isinstance(timeWindow, TimeWindow):
                timeWindowDict = timeWindow.dict()
            else:
                timeWindowDict = timeWindow
            if isinstance(filters, Filter):
                filterList = [filter.__dict__ for filter in filters]
            else:
                filterList = filters
            file_name = PromptService.getTemplateFile()
            template_parent_path = Path(__file__).parent.absolute()
            env = Environment(
                tolerance=Mode.STRICT,
                undefined=StrictUndefined,
                loader=FileSystemLoader(
                    f"{str(template_parent_path)}/prompt_templates"
                ),
            )
            template = env.get_template(file_name)
            filters = list(filters)
            return template.render(table=table, timeWindow=timeWindowDict, filters=filterList)
        except Exception as e:
            logger.exception(e)
            raise e

    @staticmethod
    def is_enabled(workspace_id: str, prompt: object) -> bool:
        connector_ids = list(Credential.objects.filter(workspace_id=workspace_id).values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        if isinstance(prompt, dict):
            return prompt["type"] in connector_types
        return prompt.type in connector_types

    @staticmethod
    def is_sync_finished(schema_id: str) -> bool:
        try:
            source_access_info = SourceAccessInfo.objects.get(storage_credentials_id=schema_id)
            sync = Sync.objects.get(source_id=source_access_info.source.id)
            sync_id = sync.id
            response = requests.get(f"{ACTIVATION_URL}/syncs/{sync_id}/last_successful_sync")
            json_string = response.content.decode('utf-8')
            dict_data = json.loads(json_string)
            return dict_data["found"] == True
        except Exception as e:
            logger.exception(e)
            raise e
