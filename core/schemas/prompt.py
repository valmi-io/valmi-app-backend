from datetime import datetime
from enum import Enum
from typing import Optional

from ninja import Schema


class TimeWindowRange(Schema):
    start: str
    end: str


class TimeWindow(Schema):
    label: str
    range: TimeWindowRange

class TimeGrain(str, Enum):
    day =  'day'
    week = 'week'
    month = 'month'
    def members():
        return TimeGrain._member_names_


class TableInfo(Schema):
    tableSchema: str
    query: str


class Filter(Schema):
    column: str
    column_type: str
    operator: str
    value: str


class PromptPreviewSchemaIn(Schema):
    schema_id: str
    time_window: TimeWindow
    time_grain: Optional[TimeGrain]
    filters: list[Filter]


class LastSuccessfulSyncInfo(Schema):
    found: bool
    run_end_at: Optional[datetime] = None
    run_end_at: Optional[datetime] = None
