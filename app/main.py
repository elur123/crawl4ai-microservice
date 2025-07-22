from fastapi import FastAPI, Query
from app.crawler import handle_crawl, handle_deep_crawl
import asyncio

app = FastAPI()

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
async def crawl_endpoint(
    url: str = Query(..., description="Target URL"),
    max_pages: int = Query(10, description="Maximum pages to crawl")
):
    try:
        response = await handle_deep_crawl(url, max_pages)
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
