from liquid import Environment, FileSystemLoader


class PromptService():    
    @classmethod
    def getTemplateFile(cls, tab:str):
        return 'prompts.liquid'
    @staticmethod
    def build(table, timeWindow, filters)-> str:
        file_name  = PromptService.getTemplateFile()
        env = Environment(loader=FileSystemLoader("templates/"))
        template = env.get_template(file_name)
        return template.render(table=table, timeWindow=timeWindow, filters=filters)




        