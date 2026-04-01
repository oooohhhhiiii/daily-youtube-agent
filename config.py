"""Daily YouTube Agent 설정"""

# 구독 채널 목록: (채널명, 채널ID)
CHANNELS = [
    ("머니코믹스 Money Comics", "UCJo6G1u0e_-wS-JQn3T-zEw"),
    ("경제 읽어주는 남자(김광석TV)", "UC3pfEoxaRDT6hvZZjpHu7Tg"),
    ("교양이를 부탁해", "UChY8VUjXv0aA7RF9hDQ0ISg"),
    ("월가아재의 과학적 투자", "UCpqD9_OJNtF6suPpi6mOQCQ"),
    ("삼프로TV 3PROTV", "UChlv4GSd7OQl3js-jkLOnFA"),
    ("꿀직장TV - 김현준 주식", "UCWF7npJlzMvcMHocK7QwaUw"),
    ("지식인사이드", "UCA_hgsFzmynpv1zkvA5A7jA"),
]

# RSS 피드 URL 템플릿
RSS_URL_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

# 자막 설정
TRANSCRIPT_LANGUAGES = ["ko", "en"]
TRANSCRIPT_MAX_LENGTH = None  # 제한 없음

# 영상 필터링 설정
LIVE_EXCLUDE_KEYWORDS = ["[live]", "전체보기", "생방송", "실시간"]
TOPIC_BLACKLIST_KEYWORDS = ["먹방", "브이로그", "vlog", "asmr", "일상", "언박싱", "unboxing", "쇼츠", "shorts"]

# 자막 요청 딜레이 (초) — IP 차단 방지
TRANSCRIPT_REQUEST_DELAY = (3.0, 7.0)  # (최소, 최대) 랜덤 딜레이

# 프록시 설정 (선택적, IP 차단 우회용)
PROXY_TYPE = None          # None, "generic", "webshare"
PROXY_HTTP_URL = None      # generic 프록시: "http://user:pass@host:port"
PROXY_HTTPS_URL = None     # generic 프록시: "https://user:pass@host:port"
WEBSHARE_USERNAME = None   # Webshare 프록시 사용자명
WEBSHARE_PASSWORD = None   # Webshare 프록시 비밀번호
WEBSHARE_RETRIES = 10      # 차단 시 재시도 횟수

# 요청 설정
REQUEST_DELAY = 1.0  # RSS 요청 간 딜레이 (초)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/xml,text/xml,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# GitHub Pages
GHPAGES_BASE_URL = "https://oooohhhhiiii.github.io/daily-youtube-agent"
