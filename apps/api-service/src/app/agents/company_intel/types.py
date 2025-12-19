from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class NewsItem(BaseModel):
    headline: str
    date: str | None = Field(
        None, description="ISO8601 date if possible; else a short date string"
    )
    source: str
    url: HttpUrl


class Person(BaseModel):
    name: str
    role: str
    url: HttpUrl | None = None


class SourceRef(BaseModel):
    title: str
    url: HttpUrl
    type: Literal["news", "docs", "marketing", "other"]


class CompanyIntelBrief(BaseModel):
    company_name: str
    canonical_url: str
    summary: str
    offerings: list[str]
    positioning: str
    target_customers: list[str]
    differentiators: list[str]
    pricing_signals: str
    recent_news: list[NewsItem]
    risks_or_concerns: list[str]
    key_people: list[Person]
    sources: list[SourceRef]
