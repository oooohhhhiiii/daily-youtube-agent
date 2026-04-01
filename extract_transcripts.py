"""수집된 영상의 자막(transcript)을 추출"""

import json
import random
import sys
import time
from pathlib import Path

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    IpBlocked,
    RequestBlocked,
    AgeRestricted,
    VideoUnavailable,
    VideoUnplayable,
    PoTokenRequired,
    NotTranslatable,
    TranslationLanguageNotAvailable,
)

import config


def _build_proxy_config():
    """config 설정에 따라 프록시 구성 반환 (None이면 프록시 미사용)"""
    if config.PROXY_TYPE == "webshare":
        from youtube_transcript_api.proxies import WebshareProxyConfig
        return WebshareProxyConfig(
            proxy_username=config.WEBSHARE_USERNAME,
            proxy_password=config.WEBSHARE_PASSWORD,
            retries_when_blocked=config.WEBSHARE_RETRIES,
        )
    elif config.PROXY_TYPE == "generic":
        from youtube_transcript_api.proxies import GenericProxyConfig
        return GenericProxyConfig(
            http_url=config.PROXY_HTTP_URL,
            https_url=config.PROXY_HTTPS_URL,
        )
    return None


def get_transcript(ytt_api, video_id):
    """영상 자막을 추출하여 (텍스트, 언어) 튜플 반환"""

    # 1차 시도: 선호 언어(ko, en)로 직접 fetch
    try:
        transcript = ytt_api.fetch(video_id, languages=config.TRANSCRIPT_LANGUAGES)
        text = "\n".join(snippet.text for snippet in transcript)
        lang = transcript.language_code

        if config.TRANSCRIPT_MAX_LENGTH and len(text) > config.TRANSCRIPT_MAX_LENGTH:
            text = text[:config.TRANSCRIPT_MAX_LENGTH] + "\n...(truncated)"

        return text, lang

    except NoTranscriptFound:
        pass  # fallback으로 진행

    # 2차 시도: 사용 가능한 자막 목록에서 탐색 + 한국어 번역 시도
    transcript_list = ytt_api.list(video_id)
    first_transcript = next(iter(transcript_list))

    # 한국어 번역 가능하면 번역 시도
    try:
        if first_transcript.is_translatable:
            korean = first_transcript.translate("ko")
            fetched = korean.fetch()
            text = "\n".join(snippet.text for snippet in fetched)
            lang = "ko-translated"
        else:
            raise NotTranslatable(video_id)
    except (NotTranslatable, TranslationLanguageNotAvailable):
        # 번역 불가 → 원본 자막 사용
        fetched = first_transcript.fetch()
        text = "\n".join(snippet.text for snippet in fetched)
        lang = fetched.language_code

    if config.TRANSCRIPT_MAX_LENGTH and len(text) > config.TRANSCRIPT_MAX_LENGTH:
        text = text[:config.TRANSCRIPT_MAX_LENGTH] + "\n...(truncated)"

    return text, lang


def find_latest_videos_file():
    """가장 최근 videos_*.json 파일 경로 반환"""
    output_dir = Path("output")
    files = sorted(output_dir.glob("videos_*.json"), reverse=True)
    return files[0] if files else None


def main():
    # 입력 파일 결정
    if len(sys.argv) > 2 and sys.argv[1] == "--input":
        input_path = Path(sys.argv[2])
    else:
        input_path = find_latest_videos_file()

    if not input_path or not input_path.exists():
        print("videos_*.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    videos_data = json.loads(input_path.read_text(encoding="utf-8"))
    videos = videos_data["videos"]
    date_str = videos_data["date"]

    if not videos:
        print("수집된 영상이 없습니다.")
        sys.exit(0)

    print(f"자막 추출 시작: {len(videos)}개 영상")

    # API 인스턴스 1회 생성 (세션 재사용)
    proxy_config = _build_proxy_config()
    ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)

    transcripts = []
    ip_blocked = False

    for i, video in enumerate(videos):
        video_id = video["video_id"]
        print(f"  [{video['channel_name']}] {video['title']}")

        try:
            text, lang = get_transcript(ytt_api, video_id)
            print(f"    → 자막 추출 성공 ({lang}, {len(text)}자)")
            transcripts.append({
                "video_id": video_id,
                "title": video["title"],
                "channel_name": video["channel_name"],
                "url": video["url"],
                "transcript": text,
                "language": lang,
                "error": None,
            })
        except (IpBlocked, RequestBlocked) as e:
            print(f"    → IP 차단 감지: {e}")
            print("    [!] IP가 차단되어 나머지 영상을 건너뜁니다.")
            transcripts.append({
                "video_id": video_id,
                "title": video["title"],
                "channel_name": video["channel_name"],
                "url": video["url"],
                "transcript": None,
                "language": None,
                "error": f"IP 차단: {e}",
            })
            ip_blocked = True
            break
        except TranscriptsDisabled:
            print(f"    → 자막 비활성화됨")
            transcripts.append({
                "video_id": video_id,
                "title": video["title"],
                "channel_name": video["channel_name"],
                "url": video["url"],
                "transcript": None,
                "language": None,
                "error": "자막이 비활성화된 영상입니다",
            })
        except (AgeRestricted, VideoUnavailable, VideoUnplayable, PoTokenRequired) as e:
            print(f"    → 영상 접근 불가: {type(e).__name__}")
            transcripts.append({
                "video_id": video_id,
                "title": video["title"],
                "channel_name": video["channel_name"],
                "url": video["url"],
                "transcript": None,
                "language": None,
                "error": f"{type(e).__name__}: {e}",
            })
        except Exception as e:
            print(f"    → 자막 추출 실패: {e}")
            transcripts.append({
                "video_id": video_id,
                "title": video["title"],
                "channel_name": video["channel_name"],
                "url": video["url"],
                "transcript": None,
                "language": None,
                "error": str(e),
            })

        # 요청 간 딜레이 (마지막 영상 제외)
        if i < len(videos) - 1:
            delay = random.uniform(*config.TRANSCRIPT_REQUEST_DELAY)
            time.sleep(delay)

    # IP 차단으로 건너뛴 영상 기록
    if ip_blocked:
        for video in videos[len(transcripts):]:
            transcripts.append({
                "video_id": video["video_id"],
                "title": video["title"],
                "channel_name": video["channel_name"],
                "url": video["url"],
                "transcript": None,
                "language": None,
                "error": "IP 차단으로 건너뜀",
            })

    output_path = Path("output") / f"transcripts_{date_str}.json"
    result = {
        "date": date_str,
        "total": len(transcripts),
        "success": sum(1 for t in transcripts if t["transcript"]),
        "failed": sum(1 for t in transcripts if t["error"]),
        "transcripts": transcripts,
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n결과: 성공 {result['success']}개, 실패 {result['failed']}개 → {output_path}")

    if ip_blocked:
        print("[!] IP 차단이 감지되었습니다. 프록시 설정을 고려해주세요.")

    if result["success"] == 0:
        print("자막을 추출할 수 있는 영상이 없습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
