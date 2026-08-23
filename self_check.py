"""외부 API 키 없이 실행하는 최소 자체 점검."""

from core import Item, clean_text, deduplicate, parse_naver_date


def main() -> None:
    assert clean_text("<b>삼성</b>&amp;전자") == "삼성&전자"
    parsed = parse_naver_date("Sun, 23 Aug 2026 12:00:00 +0900")
    assert parsed and parsed.year == 2026 and parsed.hour == 12
    items = [
        Item("AI", "뉴스", "삼성전자 AI 가전 신제품 공개", "", "https://a", "2026-08-23T12:00:00+09:00"),
        Item("AI", "뉴스", "삼성전자, AI 가전 신제품 공개!", "", "https://b", "2026-08-23T11:00:00+09:00"),
        Item("AI", "블로그", "완전히 다른 소비자 사용기", "", "https://c", None),
    ]
    assert len(deduplicate(items)) == 2
    print("self-check: OK")


if __name__ == "__main__":
    main()
