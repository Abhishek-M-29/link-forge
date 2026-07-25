from pydantic import BaseModel

class DailyClicks(BaseModel):
    date: str
    clicks: int

class AnalyticsSummary(BaseModel):
    total_clicks: int
    daily_clicks: list[DailyClicks]
    top_browsers: dict[str, int]
    top_devices: dict[str, int]
    top_referrers: dict[str, int]
