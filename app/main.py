from fastapi import FastAPI, Query
from crawl4ai.deep_crawling.filters import URLPatternFilter
from app.crawler import handle_crawl, handle_deep_crawl
import asyncio
from typing import List, Optional

app = FastAPI()

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Health check successful"
    }

@app.get("/crawl")
async def crawl_endpoint(
    url: str = Query(..., description="Target URL")
):
    try:
        response = await handle_crawl(url)
        return {
            "status": 200, 
            "data": response, 
            "message": "Successfully crawled."
        }
    except Exception as e:
        return {
            "status": 500, 
            "data": null, 
            "message": str(e)
        }


@app.get("/crawl/deep")
async def deep_crawl_endpoint(
    url: str = Query(..., description="Target URL"),
    max_pages: int = Query(10, description="Maximum pages to crawl"),
    filter_patterns: Optional[List[str]] = Query(
        None, description="List of URL patterns to filter (e.g., *services*, *products*)"
    )
):
    try:
        patterns = filter_patterns if filter_patterns else ["/service", "/services", "/product", "/products"]

        url_filter = URLPatternFilter(patterns=patterns)

        response = await handle_deep_crawl(url, max_pages, url_filter)
        return {
            "status": 200, 
            "data": response, 
            "message": "Successfully deep crawled."
        }

    except Exception as e:
        return {
            "status": 500, 
            "data": None, 
            "message": str(e)
        } 