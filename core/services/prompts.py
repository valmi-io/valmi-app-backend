import logging
from pathlib import Path

from liquid import Environment, FileSystemLoader, Mode, StrictUndefined

from core.schemas.prompt import TimeWindow

logger = logging.getLogger(__name__)
class PromptService():    
    @classmethod
    def getTemplateFile(cls):
        return 'prompts.liquid'
    @staticmethod
    def build(table, timeWindow: TimeWindow , filters: list[TimeWindow])-> str:
        timeWindowDict = timeWindow.dict()
        filterList = []
        for filter in filters:
            filterList.append(filter.__dict__)
        file_name  = PromptService.getTemplateFile()
        template_parent_path = Path(__file__).parent.absolute()
        env = Environment(
            tolerance=Mode.STRICT,
            undefined=StrictUndefined,
            loader=FileSystemLoader(str(template_parent_path) + "/prompt_templates"))
        template = env.get_template(file_name)
        filters = list(filters)
        return template.render(table=table, timeWindow=timeWindowDict, filters=filterList)




        