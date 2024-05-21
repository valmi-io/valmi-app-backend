import logging
from pathlib import Path

from core.models import Credential
from liquid import Environment, FileSystemLoader, Mode, StrictUndefined

from core.schemas.prompt import TimeWindow, Filter

logger = logging.getLogger(__name__)


class PromptService():
    @classmethod
    def getTemplateFile(cls):
        return 'prompts.liquid'

    @staticmethod
    def build(table, timeWindow: TimeWindow, filters: list[Filter]) -> str:
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

    @staticmethod
    def is_prompt_enabled(workspace_id: str, prompt: object) -> bool:
        connector_ids = list(Credential.objects.filter(workspace_id=workspace_id).values('connector_id').distinct())
        connector_types = [connector['connector_id'] for connector in connector_ids]
        return prompt.type in connector_types
