# Daily YouTube Agent

구독 유튜브 채널의 전날 업로드 영상을 수집하고, 자막을 추출하여 요약한 뒤 뉴스레터로 전달하는 자동화 에이전트.

## 대상 채널

config.py의 CHANNELS 리스트 참조. 현재 7개 채널:
머니코믹스, 경제 읽어주는 남자(김광석TV), 교양이를 부탁해, 월가아재의 과학적 투자, 삼프로TV, 꿀직장TV, 지식인사이드

## 일일 워크플로우 (매일 아침 7시 KST)

### Step 1: 채널 영상 수집
```bash
python fetch_channels.py
```
- config.py에 등록된 채널의 YouTube RSS 피드를 조회
- 전날(KST 기준) 업로드된 영상을 필터링
- 결과: `output/videos_YYYYMMDD.json`
- **영상이 0개인 경우**: 텔레그램으로 "어제 업로드된 영상이 없습니다" 알림 후 종료
```bash
python telegram_send.py --message "🎬 Daily YouTube Agent: 어제 업로드된 영상이 없습니다."
```

### Step 2: 자막 추출
```bash
python extract_transcripts.py
```
- 수집된 영상의 자막(transcript)을 추출
- 언어 우선순위: 한국어 → 영어 → 기타 사용 가능한 언어
- 자막 없는 영상은 건너뛰고 계속 진행
- 결과: `output/transcripts_YYYYMMDD.json`
- **모든 자막 추출 실패 시**: 텔레그램 알림 후 종료
```bash
python telegram_send.py --message "🎬 Daily YouTube Agent: 모든 영상의 자막 추출에 실패했습니다."
```

### Step 3: 영상 요약 (Claude Code 내부 LLM 활용)
- `output/transcripts_YYYYMMDD.json` 파일을 읽는다
- 자막이 있는 각 영상에 대해 아래 4개 카테고리로 구조화하여 요약한다:
  - **summary.core_claim**: 핵심 주장 2~3문장 (한국어)
  - **summary.evidence**: 근거 및 논리 전개 5문장 내외 (한국어)
  - **summary.facts**: 구체적 팩트(수치, 사건, 데이터 등) 2~3문장 (한국어)
  - **summary.opinion**: 발표자의 개인 의견이나 전망 2~3문장 (한국어)
  - **keywords**: 핵심 키워드 2~3개
- 결과를 `output/summaries_YYYYMMDD.json` 파일로 저장한다

**summaries JSON 형식:**
```json
{
  "date": "YYYY-MM-DD",
  "total": 10,
  "success": 10,
  "summaries": [
    {
      "video_id": "...",
      "title": "영상 제목",
      "channel_name": "채널명",
      "url": "https://www.youtube.com/watch?v=...",
      "summary": {
        "core_claim": "핵심 주장 2~3문장",
        "evidence": "근거 및 논리 전개 5문장 내외",
        "facts": "구체적 팩트(수치, 사건, 데이터) 2~3문장",
        "opinion": "발표자의 의견/전망 2~3문장"
      },
      "keywords": ["키워드1", "키워드2", "키워드3"],
      "error": null
    }
  ]
}
```

### Step 4: HTML 뉴스레터 생성
```bash
python html_generator.py
```
- 요약 데이터를 HTML 뉴스레터로 변환
- 영상 제목, 채널명, 요약, 키워드, 원문 링크 포함
- 결과: `output/newsletter_YYYYMMDD.html`

### Step 5: Telegram 전송
HTML 뉴스레터 파일을 텔레그램으로 전송:
```bash
python telegram_send.py --document output/newsletter_YYYYMMDD.html "🎬 YouTube 데일리 브리핑"
```

### Step 6: GitHub Pages 배포 및 Notion 아카이브 저장
Telegram 전송 완료 후, HTML 파일을 GitHub Pages에 배포하고 Notion에 링크를 저장한다.

#### Step 6-1: GitHub Pages 배포
```bash
python publish_ghpages.py
```
- `output/` 디렉토리의 HTML 뉴스레터 파일 1개를 gh-pages 브랜치에 push
- 날짜별 폴더 구조로 정리 (`YYYY/MM/DD/`)
- 실행 결과로 GitHub Pages URL이 JSON으로 출력됨
- URL 형식: `https://oooohhhhiiii.github.io/daily-youtube-agent/YYYY/MM/DD/newsletter_YYYY-MM-DD.html`

#### Step 6-2: Notion 아카이브 저장
- `.env` 파일에서 `NOTION_PAGE_ID`를 읽는다
- Step 6-1의 JSON 출력에서 URL을 파싱한다
- Notion MCP의 `notion-create-pages` 도구를 사용하여 NOTION_PAGE_ID 페이지 아래에 서브 페이지 생성:
  - **페이지 제목**: "YYYY-MM-DD YouTube Digest" (전날 날짜 기준)
  - **페이지 내용**: 각 영상의 제목, 채널명, 요약(core_claim), 키워드, 영상 링크를 bulleted list로 정리하고, 맨 상단에 GitHub Pages 뉴스레터 링크를 포함

#### Notion 페이지 내용 형식 (Notion-flavored Markdown):
```
[뉴스레터 전문 보기](GitHub Pages URL)

---

**1. 영상 제목** (채널명)
핵심 주장 요약
키워드: keyword1, keyword2
🎬 [영상 보기](YouTube URL)

**2. 영상 제목** (채널명)
...
```

#### 주의사항:
- GitHub Pages 배포 실패 시 오류를 콘솔에 출력하되 Notion 저장은 건너뛴다
- Notion 저장 실패 시 오류를 콘솔에 출력하되 전체 워크플로우는 중단하지 않음
- **일회성 설정 필요**: GitHub repo Settings > Pages > Source에서 `gh-pages` 브랜치, `/ (root)` 선택하여 활성화

## 주의사항
- 모든 스크립트는 프로젝트 루트 디렉토리에서 실행
- 뉴스레터 요약은 한국어로 작성
- 자막이 없는 영상은 건너뛰고 로그에 기록
- 오류 발생 시 텔레그램으로 알림 보내고 다음 단계로 진행
- 영상이 0개인 날은 Step 1 이후 파이프라인 종료
