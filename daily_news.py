"""
Daily science & engineering news digest (civil engineering focus).

Setup:   pip install feedparser
Run:     python daily_news.py
Output:  prints the digest and saves news_YYYY-MM-DD.html

Civil engineering stories are listed first, then general
engineering, then general science.
"""

import datetime as dt
import html
import time

import feedparser

# (section name, feed URL). Edit freely: add or remove feeds.
FEEDS = {
    "Civil Engineering & Construction": [
        "https://www.constructiondive.com/feeds/news/",
        "https://www.sciencedaily.com/rss/matter_energy/civil_engineering.xml",
        "https://phys.org/rss-feed/technology-news/engineering/",
    ],
    "Engineering": [
        "https://www.sciencedaily.com/rss/matter_energy/engineering.xml",
        "https://spectrum.ieee.org/feeds/feed.rss",
    ],
    "Science": [
        "https://www.sciencedaily.com/rss/top/science.xml",
        "https://www.nature.com/nature.rss",
    ],
}

# Extra keywords used to pull civil-engineering stories out of the
# general feeds and move them to the top section.
CIVIL_KEYWORDS = [
    "bridge", "concrete", "structural", "infrastructure", "tunnel", "dam",
    "geotechnical", "seismic", "earthquake", "highway", "road", "railway",
    "construction", "building", "steel", "foundation", "sustainable cement",
    "urban", "flood", "water supply", "civil engineering",
]

MAX_PER_SECTION = 8
MAX_AGE_DAYS = 3  # only show stories from the last few days


def is_recent(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return True  # no date given, keep it
    age = time.time() - time.mktime(t)
    return age <= MAX_AGE_DAYS * 86400


def is_civil(entry):
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(k in text for k in CIVIL_KEYWORDS)


def fetch_section(urls):
    items = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"Could not read {url}: {e}")
            continue
        source = feed.feed.get("title", url)
        for e in feed.entries:
            if is_recent(e):
                items.append((source, e))
    return items


def build_digest():
    seen = set()
    sections = {}

    for name, urls in FEEDS.items():
        entries = []
        for source, e in fetch_section(urls):
            link = e.get("link")
            if not link or link in seen:
                continue
            entries.append((source, e))

        # Move civil-related stories from the general sections up top.
        if name != "Civil Engineering & Construction":
            civil = [x for x in entries if is_civil(x[1])]
            rest = [x for x in entries if not is_civil(x[1])]
            sections.setdefault("Civil Engineering & Construction", []).extend(civil)
            entries = rest

        sections.setdefault(name, []).extend(entries)

    # De-duplicate and trim, keeping the civil section first.
    ordered = {}
    for name in FEEDS:
        picked = []
        for source, e in sections.get(name, []):
            link = e["link"]
            if link in seen:
                continue
            seen.add(link)
            picked.append((source, e))
            if len(picked) >= MAX_PER_SECTION:
                break
        ordered[name] = picked
    return ordered


def render_text(sections):
    lines = [f"DAILY NEWS - {dt.date.today():%A, %d %B %Y}", ""]
    for name, items in sections.items():
        lines.append(f"== {name} ==")
        if not items:
            lines.append("(nothing new)")
        for source, e in items:
            lines.append(f"- {e.get('title', '').strip()} [{source}]")
            lines.append(f"  {e['link']}")
        lines.append("")
    return "\n".join(lines)


def render_html(sections):
    parts = [
        "<html><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<style>body{font-family:sans-serif;max-width:700px;margin:auto;padding:16px}"
        "h2{border-bottom:2px solid #ddd;padding-bottom:4px}"
        "li{margin:10px 0}small{color:#666}</style></head><body>",
        f"<h1>Daily News - {dt.date.today():%d %B %Y}</h1>",
    ]
    for name, items in sections.items():
        parts.append(f"<h2>{html.escape(name)}</h2><ul>")
        if not items:
            parts.append("<li>Nothing new</li>")
        for source, e in items:
            title = html.escape(e.get("title", "").strip())
            link = html.escape(e["link"])
            parts.append(
                f"<li><a href='{link}'>{title}</a><br><small>{html.escape(source)}</small></li>"
            )
        parts.append("</ul>")
    parts.append("</body></html>")
    return "\n".join(parts)


if __name__ == "__main__":
    digest = build_digest()
    print(render_text(digest))
    filename = f"news_{dt.date.today():%Y-%m-%d}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(render_html(digest))
    print(f"Saved {filename}")
