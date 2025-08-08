from crawl4ai import AsyncWebCrawler, RegexExtractionStrategy
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, LinkPreviewConfig
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
    js_fonts_colors_extractor
)
from urllib.parse import urlparse, urljoin

async def handle_crawl(url: str):
    js_font_extractor = js_fonts_colors_extractor()

    strategy = RegexExtractionStrategy(
        pattern = (
            RegexExtractionStrategy.Email |
            RegexExtractionStrategy.PhoneUS
        )
    )

    # link_config = LinkPreviewConfig(
    #     include_internal=True,          
    #     include_external=False,         
    #     max_links=30,                   
    #     concurrency=5,                 
    #     timeout=10,                    
    #     query="Offer Service",              
    #     score_threshold=0.3,            
    #     verbose=True,                   
    #     exclude_patterns=[             
    #         "*/login*",
    #         "*/admin*",
    #         "*/contact*", 
    #         "*/about*", 
    #         "*/blog*", 
    #         "*/faq*", 
    #         "*/team*", 
    #         "*/terms*", 
    #         "*/privacy*"
    #     ],
    # )

    browser_config = BrowserConfig()

    run_config = CrawlerRunConfig(
        # link_preview_config=link_config,
        # score_links=True,
        exclude_external_links=True,
        scraping_strategy=LXMLWebScrapingStrategy(),
        extraction_strategy=strategy,
        js_code=js_font_extractor,
        capture_console_messages=True,
    )

    base_result = None
    basic_info = None
    page_content = None
    internal_links = []
    filtered_links = []
    pages = []
    services = []
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config,
            use_browser=True
        )
        base_result = result._results[0] if len(result._results) else None

    if base_result:
        internal_links = base_result.links.get("internal")
        basic_info = extract_basic_info(base_result)
        page_content = {
            "url": base_result.url,
            "html": base_result.html,
            "basicInfo": basic_info   
        }

    if internal_links:
        excluded_keywords = [
            'contact',
            'about',
            'blog',
            'faq',
            'team',
            'terms',
            'privacy',
            'financing',
            'login',
            'signup',
            'register',
            'cart',
            'checkout',
            'account',
            'dashboard',
            'profile',
            'search',
            'policy',
            'cookie',
            'sitemap',
            'appointment',
            'careers',
            'news',
            'press',
            'testimonials',
            'reviews',
            'gallery',
            'events',
            'admin',
            'rss',
            'help',
            'support',
            'partners',
            'legal',
            'newsletter',
            'subscribe',
            'unsubscribe',
            'disclaimer'
        ]


        filtered_links = [
            link for link in internal_links
            if (href := link.get("href"))  # safe get
            and not any(x in href.lower() for x in excluded_keywords)
            and urlparse(urljoin(url, href)).path.strip('/')  # exclude homepage
        ][:25]


    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            exclude_external_links=True,
            scraping_strategy=LXMLWebScrapingStrategy(),
        )

        urls = [t["href"] for t in filtered_links]
        results = await crawler.arun_many(urls, config=config)

        seen_titles = set()
        for result in results:
            content = result._results[0] if result._results else None
            if not content:
                continue

            extracted_contents = extract_repeated_sections(content.html)

            for item in extracted_contents:
                title = item.get("title", "").strip()
                
                if not title or title in seen_titles:
                    continue  # Skip duplicates or empty titles
                
                seen_titles.add(title)
                
                services.append({
                    "url_source": content.url,
                    "img_src": item.get("img_src"),
                    "title": item.get("title"),
                    "description": item.get("description"),
                })

    return {
        "pageContent": page_content,
        "services": services
    }

async def handle_deep_crawl(url: str, max_pages: int, url_filter: List[str]):
    filter_chain = FilterChain([
        url_filter,
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    strategy = RegexExtractionStrategy(
        pattern = (
            RegexExtractionStrategy.Email |
            RegexExtractionStrategy.PhoneUS
        )
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
        extraction_strategy=strategy,
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
            basicInfo = extract_basic_info(content)
            page_content = {
                "url": content.url,
                "html": content.html,
                "basicInfo": basicInfo
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