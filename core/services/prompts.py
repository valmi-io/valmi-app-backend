from liquid import Environment, FileSystemLoader


class PromptService():    
    @classmethod
    def getTemplateFile(cls, model:str):
        return model + '.liquid'
    @staticmethod
    def build(model, timeWindow, filters)-> str:
        file_name  = PromptService.getTemplateFile(model)
        env = Environment(loader=FileSystemLoader("templates/"))
        template = env.get_template(file_name)
        return template.render(model=model, timeWindow=timeWindow, filters=filters)




        