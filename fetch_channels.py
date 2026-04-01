"""YouTube 채널 RSS 피드에서 전날 업로드된 영상을 수집"""

import json
import time
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

import config

KST = timezone(timedelta(hours=9))

ATOM_NS = "http://www.w3.org/2005/Atom"
YT_NS = "http://www.youtube.com/xml/schemas/2015"


def get_yesterday_kst():
    """어제 날짜(KST) 반환"""
    now_kst = datetime.now(KST)
    yesterday = now_kst - timedelta(days=1)
    return yesterday.date()


def is_yesterday(published_str, yesterday_date):
    """published 날짜가 어제(KST)인지 확인"""
    # ISO 8601: 2026-03-31T08:30:00+00:00
    published = datetime.fromisoformat(published_str)
    published_kst = published.astimezone(KST)
    return published_kst.date() == yesterday_date


def is_excluded_video(title):
    """Live 영상 또는 블랙리스트 키워드 포함 영상인지 확인"""
    title_lower = title.lower()
    for kw in config.LIVE_EXCLUDE_KEYWORDS:
        if kw in title_lower:
            return f"Live: {kw}"
    for kw in config.TOPIC_BLACKLIST_KEYWORDS:
        if kw in title_lower:
            return f"비관련: {kw}"
    return None


def fetch_channel_videos(channel_name, channel_id, yesterday_date):
    """단일 채널의 RSS 피드에서 어제 영상 추출"""
    url = config.RSS_URL_TEMPLATE.format(channel_id=channel_id)

    try:
        resp = requests.get(url, headers=config.HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [오류] {channel_name} RSS 요청 실패: {e}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"  [오류] {channel_name} XML 파싱 실패: {e}")
        return []

    videos = []
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        video_id_el = entry.find(f"{{{YT_NS}}}videoId")
        title_el = entry.find(f"{{{ATOM_NS}}}title")
        published_el = entry.find(f"{{{ATOM_NS}}}published")

        if video_id_el is None or title_el is None or published_el is None:
            continue

        published_str = published_el.text.strip()

        if is_yesterday(published_str, yesterday_date):
            title = title_el.text.strip()
            exclude_reason = is_excluded_video(title)
            if exclude_reason:
                print(f"    → 제외 ({exclude_reason}): {title}")
                continue

            video_id = video_id_el.text.strip()
            videos.append({
                "channel_name": channel_name,
                "channel_id": channel_id,
                "video_id": video_id,
                "title": title,
                "published": published_str,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })

    return videos


def main():
    yesterday = get_yesterday_kst()
    date_str = yesterday.isoformat()
    print(f"수집 대상 날짜: {date_str} (KST)")

    all_videos = []

    for channel_name, channel_id in config.CHANNELS:
        print(f"  채널 조회: {channel_name}")
        videos = fetch_channel_videos(channel_name, channel_id, yesterday)
        if videos:
            print(f"    → {len(videos)}개 영상 발견")
        else:
            print(f"    → 어제 업로드된 영상 없음")
        all_videos.extend(videos)
        time.sleep(config.REQUEST_DELAY)

    output_path = Path("output") / f"videos_{date_str}.json"
    output_path.parent.mkdir(exist_ok=True)

    result = {
        "date": date_str,
        "channels_checked": len(config.CHANNELS),
        "total_videos": len(all_videos),
        "videos": all_videos,
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과: {len(all_videos)}개 영상 → {output_path}")

    if len(all_videos) == 0:
        print("어제 업로드된 영상이 없습니다.")
        sys.exit(0)


if __name__ == "__main__":
    main()
