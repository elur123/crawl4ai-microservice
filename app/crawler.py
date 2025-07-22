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

async def handle_deep_crawl(url: str, max_pages: int):
    filter_chain = FilterChain([
        URLPatternFilter(patterns=["*guide*", "*tutorial*", "*blog*"]),
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
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True
    )

    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url, config=config):
            results.append(result)

    contents = []
    for result in results:
        if(len(result._results)):
            content = result._results[0]
            contents.append({
                "url": content.url,
                "images": content.media["images"]
            })

    return contents