"""
Scraper configuration — all targets, URLs, keywords, and rate-limit settings.
Central config for all 7 scraper modules.
"""

KEYWORD_FILTERS = [
    "wishlist", "wish list", "saved", "save for later", "favourites", "favorites",
    "size", "fit", "quality", "returns", "return", "delivery", "cart",
    "didn't buy", "did not buy", "abandoned", "too expensive", "out of stock",
    "returned", "ordered", "exchange", "refund", "authentic", "fake",
    "restock", "notify", "price drop", "sale", "compare", "comparison",
]

GOOGLE_PLAY_CONFIG = {
    "apps": [
        {"app_id": "com.myntra.android",           "platform": "Myntra"},
        {"app_id": "com.ril.ajio",                  "platform": "AJIO"},
        {"app_id": "com.fsn.nykaa",                 "platform": "Nykaa Fashion"},
        {"app_id": "com.tatacliq.palace",           "platform": "Tata CLiQ"},
        {"app_id": "com.shoppersstop.shopping",     "platform": "Shoppers Stop"},
        {"app_id": "com.meesho.supply",             "platform": "Meesho"},
        {"app_id": "in.amazon.mShop.android.shopping", "platform": "Amazon Fashion"},
        {"app_id": "com.flipkart.android",          "platform": "Flipkart Fashion"},
    ],
    "max_reviews_per_app": 200,
    "delay_seconds": 2,
}

APP_STORE_CONFIG = {
    "apps": [
        {
            "app_id": "907394059",
            "platform": "Myntra",
            "countries": ["in", "us"],
        },
    ],
    "delay_seconds": 2,
}

REDDIT_CONFIG = {
    "thread_urls": [
        "https://www.reddit.com/r/MyntraSucks/comments/1pemstf/myntra_doesnt_want_me_to_wishlist_the_products/",
        "https://www.reddit.com/r/IndianFashionAddicts/comments/1osrk03/myntra_is_deleting_reviews_from_the_listed/",
        "https://www.reddit.com/r/NoStupidQuestions/comments/a0zb8y/whats_the_point_of_the_wishlist_option_on_online/",
        "https://www.reddit.com/r/femalefashionadvice/comments/7qeem8/planning_your_shoppingkeeping_a_wishlist/",
        "https://www.reddit.com/r/SneakersIndia/comments/1g1xzhy/bought_these-from-myntra-in-the-wrong-size-they/",
        "https://www.reddit.com/r/IndianBeautyDeals/comments/1hmjhsb/currently-out-of-stock-but-has-anyone-got-a-full/",
        "https://www.reddit.com/r/IndianBeautyDeals/comments/1geiafh/has-anybody-received-what-you-ordered-from-zara/",
        "https://www.reddit.com/r/IndianFashionAddicts/comments/1luj4sw/after-11-years-with-myntra-this-is-the-crap-that/",
    ],
    "scroll_count": 10,
    "delay_seconds": 5,
}

YOUTUBE_CONFIG = {
    "search_queries": [
        "Myntra haul review",
        "Myntra wishlist tips",
        "Ajio vs Myntra review",
        "Nykaa Fashion try on haul",
        "online shopping India Myntra experience",
    ],
    "video_urls": [
        # Manually discovered video URLs — paste here after searching YouTube in browser
    ],
    "max_videos_per_query": 5,
    "max_comments_per_video": 100,
    "scroll_pause_seconds": 2,
}

PRODUCT_REVIEWS_CONFIG = {
    "platforms": {
        "trustpilot": {
            "urls": [
                "https://www.trustpilot.com/review/www.myntra.com",
            ],
            "platform_name": "Myntra",
        },
        "reviews_io": {
            "urls": [
                "https://www.reviews.io/company-reviews/store/myntra",
            ],
            "platform_name": "Myntra",
        },
        "worthepenny": {
            "urls": [
                "https://myntra.worthepenny.com/",
            ],
            "platform_name": "Myntra",
        },
        "consumer_complaints": {
            "urls": [
                "https://www.consumercomplaints.in/myntra-com-regarding-items-out-of-stock-c1075485",
            ],
            "platform_name": "Myntra",
        },
    },
    "delay_seconds": 3,
}

SOCIAL_MEDIA_CONFIG = {
    "post_urls": [
        "https://www.linkedin.com/posts/yashita-aggarwal14_product-feature-analysis-myntra-activity-7425157253982466048-lerO",
        "https://www.linkedin.com/posts/avneesh-singh-ba2097127_ux-revenue-myntra-activity-7306593408276385792-Eccl",
        "https://www.linkedin.com/posts/vineetajain_uxdesign-uiux-activity-7374709051441545216-MOuh",
        "https://www.linkedin.com/posts/vineetajain_uxdesign-productdesign-uxaudit-product-activity-7373227574648299520-UZZv",
        "https://www.linkedin.com/posts/glny_its-a-great-example-of-how-small-ux-shifts-activity-7421465615481245696-OeY2",
        "https://www.linkedin.com/posts/suchismita-debnath-342539b8_productmanagement-30daysofproduct-day1-activity-7315385479451889664-S",
    ],
    "delay_seconds": 5,
}

SEED_URLS_CONFIG = {
    "urls": [
        # Medium articles
        {"url": "https://medium.com/@urjaa17/improving-myntras-wishlist-feature-in-48-hours-31ded225d831",     "type": "medium_article"},
        {"url": "https://medium.com/@anvesh9292/why-you-cant-sort-your-myntra-wishlist-on-desktop-and-what-it-reveals-70c841931e31", "type": "medium_article"},
        {"url": "https://shivam-goyal.medium.com/wishlist-collections-myntra-125b5aa2a6b2",                    "type": "medium_article"},
        {"url": "https://jarettttt.medium.com/myntra-wishlist-makeover-a-ux-enhancement-journey-7fbd1af4f7f8", "type": "medium_article"},
        {"url": "https://medium.com/@ananya.aditi434/feature-table-for-wishlist-functionality-of-indian-ecommerce-apps-b635e076b64c", "type": "medium_article"},
        # Design & research
        {"url": "http://nandha.design/Myntra.html",                                                            "type": "design_case_study"},
        # Academic
        {"url": "https://dinastipub.org/DIJEFA/article/view/3887",                                             "type": "academic_paper"},
        {"url": "https://www.indiatoday.in/information/story/myntra-sale-here-s-how-to-create-a-wishlist-on-myntra-1630285-2019-12-21", "type": "news_article"},
        # New additions
        {"url": "https://www.fashioncapital.co.uk/insights/5-problems-faced-by-online-fashion-retailers-and-how-to-solve-them/", "type": "blog_article"},
        {"url": "https://shanghaigarment.com/is-online-shopping-actually-making-fashion-more-frustrating/", "type": "blog_article"},
        {"url": "https://www.secretsaucepartners.com/blog/the-top-5-challenges-of-online-fashion-retailing-and-how-to-overcome-them", "type": "blog_article"},
        {"url": "https://zoovu.com/blog/solve-the-5-biggest-problems-of-online-shoppers", "type": "blog_article"},
        {"url": "https://pluss.in/blogs/inclusive-fashion-news/online-shopping-pain-points-refund-delays-and-fulfillment-issues?srsltid=AfmBOoosDBiMH8B5bhC8OCsfEfDsmvj04MlEaDKzDY0gxx8hcqzKDLIm&utm_id=flareai_utm_id&utm_source=flareai_inbound_content_marketing_agent&utm_campaign=Q29udmVyc2lvbiBhdHRyaWJ1dGVkIHRvIGZsYXJlQUkgSW5ib3VuZCBCbG9nIHZpc2l0IGh0dHBzOi8vcGx1c3MuaW4vYmxvZ3MvaW5jbHVzaXZlLWZhc2hpb24tbmV3cy9vbmxpbmUtc2hvcHBpbmctcGFpbi1wb2ludHMtcmVmdW5kLWRlbGF5cy1hbmQtZnVsZmlsbG1lbnQtaXNzdWVzLiBTb3VyY2U6IEdvb2dsZSBTZWFyY2ggQ29uc29sZStHb29nbGUgQW5hbHl0aWNzIGZsYXJlQUkgVVRN", "type": "blog_article"}
    ],
    "delay_seconds": 2,
}

