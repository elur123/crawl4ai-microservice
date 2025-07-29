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
from app.helper import (
    extract_image_attribute, 
    split_desc_blocks, 
    extract_repeated_sections, 
    extract_basic_info,
    js_fonts_colors_extractor,
    extact_fonts_colors_from_console
)

async def handle_crawl(url: str):
    js_font_extractor = js_fonts_colors_extractor()

    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
        js_code=js_font_extractor,
        # delay_before_return_html=2.5,
        capture_console_messages=True,
        # capture_network_requests=True
    )

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
        js_code=js_fonts_colors_extractor(),
        capture_console_messages=True,
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
            fonts_colors = extact_fonts_colors_from_console(content.console_messages)
            page_content = {
                "url": content.url,
                "html": content.html,
                "basicInfo": {
                    "fonts": fonts_colors.get("fonts"),
                    "colors": fonts_colors.get("colors")
                }
            }
            # page_content = content
            continue

        if len(result._results):
            content = result._results[0]

            contents.append({
                "url": content.url,
                # "html": content.html,
                "extracted_content": extract_repeated_sections(content.html)
            })

    return {
        "pageContent": page_content,
        "pages": contents
    }