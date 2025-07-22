from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from typing import List
from app.helper import extract_image_attribute, split_desc_blocks

async def handle_crawl(url: str):
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config,
            use_browser=True
        )
    return result._results[0] if len(result._results) else None

async def handle_deep_crawl(url: str, max_pages: int, url_filter: List[str]):
    filter_chain = FilterChain([
        url_filter,
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=3,
            max_pages=max_pages,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        exclude_external_links=True,
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True
    )

    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url, config=config):
            results.append(result)


    contents = []
    page_content = None

    for index, result in enumerate(results):
        if index == 0:
            content = result._results[0] if result._results else None
            page_content = content
            continue

        if len(result._results):
            content = result._results[0]

            images_data = content.media.get("images", [])
            desc_blocks = []

            if images_data:
                raw_desc = images_data[0].get("desc", "")
                desc_blocks = split_desc_blocks(raw_desc)

            images = []
            i = 0
            for image in images_data:
                if image.get("width") is None:
                    desc = desc_blocks[i] if i < len(desc_blocks) else ""
                    image_content = extract_image_attribute(image, desc)
                    images.append(image_content)
                    i += 1


            contents.append({
                "url": content.url,
                "images": images
            })

    return {
        "pageContent": page_content,
        "medias": contents
    }
