# Google 뉴스 키워드 리포트 에이전트

지정한 키워드의 Google 뉴스 RSS 검색 결과를 최신순으로 수집하고, 중복 제거 후 OpenAI가 한국어 보고서를 작성합니다.

## 주요 기능

- 여러 키워드와 제외어 지원
- 국내외 언론사의 Google 뉴스 결과 수집
- 최근 N시간 자료만 선별
- URL 및 유사 제목 기준 중복 제거
- 핵심 요약, 주요 이슈, 출처별 근거, 시사점, 다음 모니터링 포인트 생성
- `□ → - → ·` 계층형 업무 보고서 생성
- Word(.docx), Markdown 및 원본 JSON 제공
- 1회 실행 또는 일정 간격 반복 실행
- Streamlit 화면 제공

## 1. API 키 준비

1. [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키를 발급받습니다.
2. `.env.example`을 `.env`로 복사하고 값을 입력합니다.

```env
OPENAI_API_KEY=...
```

## 2. 설치

```bash
cd naver_keyword_report_agent
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python self_check.py
```

이미 설치한 적이 있다면 최신 OpenAI SDK로 갱신합니다.

```bash
python -m pip install --upgrade "openai>=2.0.0"
```

프로그램은 `.env`의 `OPENAI_API_KEY`를 명시적으로 사용합니다.

## 3. 설정

`config.yaml`에서 키워드, 제외어, 검색 영역, 수집 범위, 보고서 관점을 바꿉니다.

## 4. 실행

한 번 실행:

```bash
python agent.py
```

30분마다 반복:

```bash
python agent.py --watch --interval 30
```

화면에서 실행:

```bash
streamlit run app.py
```

화면의 **다운로드** 탭에서 Word 보고서를 받을 수 있으며, `reports/`에는 Markdown과 JSON 원본이 생성됩니다.

기존 버전을 설치했던 경우 Word 생성 기능을 위해 의존성을 다시 설치하세요.

```bash
python -m pip install --upgrade -r requirements.txt
```

## 운영 팁

- 회사/제품명처럼 동음이의어가 많은 키워드는 `exclude_words`를 적극 활용하세요.
- Google 뉴스 RSS 결과는 제목·링크·간단한 설명이며 기사 본문 전체가 아닙니다.
- Google 뉴스 RSS 수집에는 API 키가 필요하지 않습니다. OpenAI 보고서 작성에만 키가 필요합니다.
- 반복 실행은 로컬 PC가 켜져 있어야 합니다. 서버에서는 cron, 작업 스케줄러, GitHub Actions 등으로 `python agent.py`를 호출할 수 있습니다.
- API 키는 코드나 저장소에 올리지 마세요.
