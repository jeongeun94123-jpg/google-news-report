from core import Item, clean_text, deduplicate, parse_naver_date


def test_clean_text():
    assert clean_text("<b>삼성</b>&amp;전자") == "삼성&전자"


def test_parse_news_date():
    result = parse_naver_date("Sun, 23 Aug 2026 12:00:00 +0900")
    assert result and result.year == 2026 and result.hour == 12


def test_deduplicate_same_link_and_similar_title():
    items = [
        Item("AI", "뉴스", "삼성전자 AI 가전 신제품 공개", "", "https://a", "2026-08-23T12:00:00+09:00"),
        Item("AI", "뉴스", "삼성전자, AI 가전 신제품 공개!", "", "https://b", "2026-08-23T11:00:00+09:00"),
        Item("AI", "블로그", "완전히 다른 소비자 사용기", "", "https://c", None),
    ]
    assert len(deduplicate(items)) == 2
