from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List

app = FastAPI()

class AnalyzeRequest(BaseModel):
    countries: List[str]
    risk_tolerance: str
    duration: str

    @field_validator("countries")
    @classmethod
    def validate_countries(cls, v):
        if len(v) < 3:
            raise ValueError("At least 3 countries required")
        for code in v:
            if len(code) != 3 or not code.isalpha():
                raise ValueError("Countries must be ISO3 codes (e.g., FRA, JPN)")
        return [code.upper() for code in v]

    @field_validator("risk_tolerance")
    @classmethod
    def validate_risk(cls, v):
        allowed = {"low", "moderate", "high"}
        if v.lower() not in allowed:
            raise ValueError("risk_tolerance must be low, moderate, or high")
        return v.lower()

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v):
        allowed = {"short-term", "long-term"}
        if v.lower() not in allowed:
            raise ValueError("duration must be short-term or long-term")
        return v.lower()


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    return {
        "results": [
            {
                "country_code": "JPN",
                "country_name": "Japan",
                "rank": 1,
                "overall_score": 82.5,
                "sub_scores": {
                    "travel_risk": 90,
                    "health_infra": 88,
                    "env_stability": 70
                },
                "explanation": "Ranked highest due to exceptional health infrastructure suitable for long-term stays, despite minor environmental volatility."
            }
        ],
        "metadata": {
            "cache_hits": [],
            "cache_misses": request.countries,
            "missing_metrics": []
        }
    }