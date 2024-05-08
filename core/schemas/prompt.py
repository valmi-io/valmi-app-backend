from ninja import Schema


class TimeWindowRange(Schema):
    start: str
    end: str

class TimeWindow(Schema):
    label: str
    range: TimeWindowRange


class Filter(Schema):
    label: str
    operator: str
    name: str
    value: str
    

class PromptPreviewSchemaIn(Schema):
    source_id: str
    time_window: TimeWindow
    filters: list[Filter]


