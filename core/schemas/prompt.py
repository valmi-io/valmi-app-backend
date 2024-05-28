from datetime import datetime
from typing import Optional
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
    schema_id: str
    time_window: TimeWindow
    filters: list[Filter]


class LastSuccessfulSyncInfo(Schema):
    found: bool
    run_end_at: Optional[datetime] = None
