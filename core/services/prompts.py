import json
import logging
from pathlib import Path
from liquid import Template as LiquidTemplate
import requests
from decouple import config
from liquid import Environment, FileSystemLoader, Mode, StrictUndefined

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
            filterList = [filter.dict() for filter in filters]
            rendered_query = template.render(filters=filterList, timeWindow=timeWindowDict)
            liquid_template = LiquidTemplate(tableInfo.query)
            context = {
                "schema": tableInfo.tableSchema,
                "filters": rendered_query
            }
            query = liquid_template.render(context)
            logger.debug(type(query))
            query = query.replace("\\", "")
            logger.debug(query)
            logger.debug(query)
            return query
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
    def is_sync_finished(sync_id: str) -> LastSuccessfulSyncInfo:
        try:
            response = requests.get(f"{ACTIVATION_URL}/syncs/{sync_id}/last_successful_sync")
            logger.debug(response)
            json_string = response.content.decode('utf-8')
            logger.debug(json_string)
            last_success_sync_dict = json.loads(json_string)
            last_success_sync = LastSuccessfulSyncInfo(**last_success_sync_dict)
            logger.debug(last_success_sync)
            return last_success_sync
        except Exception as e:
            logger.exception(e)
            raise e
