"""요약 데이터를 HTML 뉴스레터로 변환"""

import json
import sys
import html
from pathlib import Path


def render_html(date, summaries):
    """요약 리스트를 HTML 뉴스레터로 렌더링"""
    article_blocks = []

    for i, s in enumerate(summaries, 1):
        title_html = html.escape(s["title"])
        channel_html = html.escape(s["channel_name"])
        link = html.escape(s.get("url", ""))
        keywords = s.get("keywords", [])
        summary = s.get("summary", {})

        # 4분류 구조화 요약 렌더링
        sections = [
            ("&#128161; 핵심 주장", summary.get("core_claim", "")),
            ("&#128202; 근거 및 논리", summary.get("evidence", "")),
            ("&#128204; 팩트", summary.get("facts", "")),
            ("&#128172; 의견", summary.get("opinion", "")),
        ]
        summary_html = ""
        for label, text in sections:
            if text:
                text_html = html.escape(text).replace("\n", "<br>")
                summary_html += f"""
        <div style="margin:6px 0;">
          <p style="margin:0 0 2px; font-size:13px; font-weight:bold; color:#1a1a2e;">{label}</p>
          <p style="margin:0; font-size:14px; color:#444; line-height:1.6;">{text_html}</p>
        </div>"""

        keywords_html = ""
        if keywords:
            kw_str = ", ".join(html.escape(k) for k in keywords)
            keywords_html = f"""
        <p style="margin:6px 0; font-size:12px; color:#6b7280;">&#128161; 키워드: {kw_str}</p>"""

        block = f"""      <div style="border-bottom:1px solid #eee; padding:16px 0;">
        <h2 style="margin:0 0 4px; font-size:16px; color:#1a1a2e; line-height:1.4;">{i}. {title_html}</h2>
        <p style="margin:0 0 8px; font-size:12px; color:#888;">{channel_html}</p>{summary_html}{keywords_html}
        <a href="{link}" style="font-size:13px; color:#4a90d9; text-decoration:none;">&#127909; 영상 보기</a>
      </div>"""
        article_blocks.append(block)

    articles_html = "\n".join(article_blocks)
    title = f"YouTube 데일리 브리핑 ({date})"
    title_html = html.escape(title)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_html}</title>
</head>
<body style="margin:0; padding:16px; background:#f5f5f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;">
  <div style="max-width:640px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:#c0392b; color:#fff; padding:20px 24px;">
      <h1 style="margin:0; font-size:20px;">&#127909; {title_html}</h1>
      <p style="margin:6px 0 0; font-size:14px; color:rgba(255,255,255,0.7);">{len(summaries)}개 영상 요약</p>
    </div>
    <div style="padding:4px 24px 16px;">
{articles_html}
    </div>
    <div style="padding:12px 24px; text-align:center; font-size:12px; color:#999; border-top:1px solid #eee;">
      Daily YouTube Agent
    </div>
  </div>
</body>
</html>"""


def find_latest_summaries_file():
    """가장 최근 summaries_*.json 파일 경로 반환"""
    output_dir = Path("output")
    files = sorted(output_dir.glob("summaries_*.json"), reverse=True)
    return files[0] if files else None


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--input":
        input_path = Path(sys.argv[2])
    else:
        input_path = find_latest_summaries_file()

    if not input_path or not input_path.exists():
        print("summaries_*.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    date_str = data["date"]
    summaries = [s for s in data["summaries"] if s.get("summary") and isinstance(s["summary"], dict)]

    if not summaries:
        print("요약된 영상이 없습니다.")
        sys.exit(1)

    html_content = render_html(date_str, summaries)

    output_path = Path("output") / f"newsletter_{date_str}.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"HTML 뉴스레터 생성 완료: {output_path} ({len(summaries)}개 영상)")


if __name__ == "__main__":
    main()
