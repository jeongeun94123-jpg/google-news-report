from __future__ import annotations

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
import yaml
from dotenv import load_dotenv
from openai import OpenAI

from core import Item, clean_text, deduplicate, parse_naver_date

KST = timezone(timedelta(hours=9))
RSS_URL = "https://news.google.com/rss/search"


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not config.get("keywords"):
        raise ValueError("config.yaml에 keywords를 하나 이상 입력하세요.")
    return config


def fetch_keyword(keyword: str, display: int) -> list[Item]:
    params = urlencode({"q": keyword, "hl": "ko", "gl": "KR", "ceid": "KR:ko"})
    response = requests.get(
        f"{RSS_URL}?{params}",
        headers={"User-Agent": "Mozilla/5.0 KeywordReportAgent/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    results: list[Item] = []
    root = ET.fromstring(response.content)
    for raw in root.findall("./channel/item")[:display]:
        title = clean_text(raw.findtext("title", ""))
        source_node = raw.find("source")
        publisher = clean_text(source_node.text if source_node is not None and source_node.text else "")
        if publisher and title.endswith(f" - {publisher}"):
            title = title[: -(len(publisher) + 3)].strip()
        dt = parse_naver_date(raw.findtext("pubDate"))
        results.append(Item(
            keyword=keyword,
            source=publisher or "Google 뉴스",
            title=title,
            description=clean_text(raw.findtext("description", "")),
            link=raw.findtext("link", ""),
            published_at=dt.isoformat() if dt else None,
        ))
    return results


def collect(config: dict[str, Any]) -> list[Item]:
    cutoff = datetime.now(KST) - timedelta(hours=int(config.get("lookback_hours", 24)))
    excluded = [x.lower() for x in config.get("exclude_words", [])]
    items: list[Item] = []
    for keyword in config["keywords"]:
        for item in fetch_keyword(keyword, int(config.get("results_per_keyword", 30))):
            searchable = f"{item.title} {item.description}".lower()
            dt = datetime.fromisoformat(item.published_at) if item.published_at else None
            if any(word in searchable for word in excluded):
                continue
            if dt and dt < cutoff:
                continue
            items.append(item)
    return deduplicate(items)


def make_report(items: list[Item], config: dict[str, Any]) -> str:
    if not items:
        return "□ 수집 결과\n- 조건에 맞는 신규 검색결과가 없습니다.\n· 키워드 또는 수집 시간 범위를 조정한 뒤 다시 실행하세요."
    selected = items[: int(config.get("max_items_for_ai", 60))]
    evidence = "\n".join(
        f"[{i}] 키워드={x.keyword} | 유형={x.source} | 시각={x.published_at or '미상'}\n"
        f"제목: {x.title}\n요약문: {x.description}\nURL: {x.link}"
        for i, x in enumerate(selected, 1)
    )
    prompt = f"""당신은 한국 기업의 시장정보 분석가다. 아래 자료만 근거로 즉시 업무에 사용할 수 있는 한국어 보고서를 작성하라.

보고서 관점: {config.get('report_focus', '시장 변화와 기회·리스크')}
필수 구성: 핵심 요약, 주요 이슈 3~5개, 키워드별 동향, 시장 반응 신호,
기회·리스크 및 권고 행동, 다음 모니터링 포인트, 출처 목록.

규칙:
- 모든 줄은 반드시 '□ ', '- ', '· ' 중 하나로 시작한다. Markdown 제목·표·별표는 쓰지 않는다.
- '□'는 가장 큰 이야기 또는 섹션 제목이다.
- '-'는 바로 위 '□'를 설명하는 완결된 문장이다.
- '·'는 바로 위 '-'의 구체적 근거·수치·해석·실행 항목을 설명하는 완결된 문장이다.
- 각 '□' 아래에는 최소 1개의 '-', 각 '-' 아래에는 가능한 한 1개 이상의 '·'를 둔다.
- 제공 자료에 없는 사실을 만들지 않는다.
- 같은 사건을 다룬 여러 자료는 하나의 이슈로 묶는다.
- 불확실한 해석은 '추정'이라고 명시한다.
- 각 핵심 주장 뒤에 [1], [2]처럼 근거 번호를 단다.
- 출처 목록도 같은 계층을 사용하고 URL을 원문 그대로 포함한다.
- 보고서 시작은 '□ 보고서 개요'로 하고 생성 시각과 수집 건수를 하위 문장에 적는다.

생성 시각: {datetime.now(KST).strftime('%Y-%m-%d %H:%M KST')}
수집 건수: {len(items)}건 (AI 분석 입력 {len(selected)}건)

자료:
{evidence}
"""
    api_key = os.environ["OPENAI_API_KEY"].strip().strip('"').strip("'")
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=config.get("model", "gpt-5.6-luna"),
        input=prompt,
        reasoning={"effort": "low"},
    )
    return response.output_text or "보고서를 생성하지 못했습니다."


def save_report(report: str, items: list[Item], output_dir: str | Path = "reports") -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    md_path = output / f"google_news_report_{stamp}.md"
    json_path = output / f"google_news_raw_{stamp}.json"
    md_path.write_text(report, encoding="utf-8")
    json_path.write_text(json.dumps([asdict(x) for x in items], ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


def run_once(config_path: str = "config.yaml") -> tuple[str, list[Item], Path, Path]:
    # 같은 이름의 오래된 시스템 환경변수보다 현재 폴더의 .env를 우선합니다.
    load_dotenv(override=True)
    for name in ("OPENAI_API_KEY",):
        if not os.getenv(name):
            raise RuntimeError(f"환경변수 {name}가 없습니다. .env 파일을 확인하세요.")
    config = load_config(config_path)
    items = collect(config)
    report = make_report(items, config)
    md_path, json_path = save_report(report, items)
    return report, items, md_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Google 뉴스 키워드 리포트 에이전트")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=30, help="반복 간격(분)")
    args = parser.parse_args()
    while True:
        try:
            _, items, md_path, _ = run_once(args.config)
            print(f"[{datetime.now(KST):%Y-%m-%d %H:%M}] {len(items)}건 분석 완료: {md_path}")
        except Exception as exc:
            print(f"실행 실패: {exc}")
            if not args.watch:
                raise
        if not args.watch:
            break
        time.sleep(max(args.interval, 1) * 60)


if __name__ == "__main__":
    main()
