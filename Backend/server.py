from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Tuple
import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from Backend.services.aggregator import analyze_country

from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware

# Configure logging to output to a file
log_file = "full_server_debug.log"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# File handler
file_handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024 * 5, backupCount=5) # 5 MB per file, 5 backup files
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler (optional, for real-time console output)
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('%(levelname)s:     %(name)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class SubScores(BaseModel):
    travel_risk: float
    health_infra: float
    env_stability: float

class AnalyzeResult(BaseModel):
    country_code: str
    country_name: str
    rank: int
    overall_score: float
    sub_scores: SubScores
    explanation: str

class AnalyzeResponse(BaseModel):
    results: List[AnalyzeResult]
    metadata: Dict[str, Any]

class AnalyzeRequest(BaseModel):
    countries: List[str]
    risk_tolerance: str
    duration: str
    debug: Optional[bool] = False

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


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    tasks = [analyze_country(country_code, request.risk_tolerance, request.duration, request.debug) for country_code in request.countries]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    final_results = []
    cache_hits = []
    cache_misses = []
    all_missing_metrics = []
    debug_analyses = {}

    for i, res_tuple in enumerate(raw_results):
        country_code = request.countries[i]
        
        if isinstance(res_tuple, Exception):
            logger.error(f"Error processing country {country_code}: {res_tuple}")
            all_missing_metrics.append(country_code)
            continue
        
        result_dict, is_cache_hit, country_missing_metrics = res_tuple

        if not result_dict: # Empty dict means critical failure in _fetch_and_build
            all_missing_metrics.append(country_code)
            continue

        if is_cache_hit:
            cache_hits.append(country_code)
        else:
            cache_misses.append(country_code)
        
        all_missing_metrics.extend(country_missing_metrics)
        
        # Store debug analysis separately if present
        if request.debug and "debug_analysis" in result_dict:
            debug_analysis = result_dict.pop("debug_analysis")
            debug_analysis["pre_sorted_score"] = result_dict["overall_score"] # Store score before sorting
            debug_analyses[country_code] = debug_analysis
            
        final_results.append(result_dict)

    # Sort results by overall_score in descending order
    final_results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    # Assign rank and update debug analysis with post-sort rank
    for i, result in enumerate(final_results):
        result["rank"] = i + 1
        if request.debug and result["country_code"] in debug_analyses:
            debug_analyses[result["country_code"]]["post_sort_rank"] = i + 1
            logger.debug(f"[{result['country_code']}] Post-sort Rank: {i+1}")

    # Ensure unique missing metrics
    unique_missing_metrics = list(set(all_missing_metrics))

    response_metadata = {
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "missing_metrics": unique_missing_metrics
    }

    if request.debug:
        response_metadata["debug_analyses"] = debug_analyses
        logger.info(f"Debug mode enabled. Debug analyses: {debug_analyses}")

    results_order = [f"{r['country_code']}:{r['overall_score']}" for r in final_results]
    logger.info(f"Final results order: {results_order}")

    return {
        "results": final_results,
        "metadata": response_metadata
    }