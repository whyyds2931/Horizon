#!/usr/bin/env python3
"""Publish Horizon daily summary to whyyds2931.github.io blog.

Reads the generated summary-zh.md, converts it to a blog post page
(posts/<date>-horizon-news.html) and inserts it into script.js's
articles array, then pushes both files via the GitHub API.

Usage:
  python publish_to_blog.py --token <GH_PAT> --summary <path-to-summary-zh.md> [--dry-run]
"""
import argparse
import base64
import json
import re
import sys
import urllib.request
import urllib.error

BLOG_REPO = "whyyds2931/whyyds2931.github.io"
API_BASE = "https://api.github.com/repos/" + BLOG_REPO


def gh_request(headers, path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API_BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        print(f"  HTTP {e.code} on {method} {path}: {body}", file=sys.stderr)
        raise


def fetch_file(headers, path, ref=None):
    q = f"?ref={ref}" if ref else ""
    data = gh_request(headers, f"/contents/{path}{q}")
    return base64.b64decode(data["content"]).decode(), data["sha"]


def put_file(headers, path, content, message, sha=None):
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha
    return gh_request(headers, f"/contents/{path}", method="PUT", payload=payload)


def md_to_html(md_text):
    """Convert the summary markdown to HTML with a minimal, dependency-free converter."""
    lines = md_text.split("\n")
    out = []
    in_list = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # blank line: close open structures
        if not stripped:
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("")
            i += 1
            continue
        # blockquote
        if stripped.startswith(">"):
            out.append(f'<blockquote>{inline(stripped.lstrip(">").strip())}</blockquote>')
            i += 1
            continue
        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue
        # horizontal rule
        if re.match(r"^-{3,}$", stripped):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append("<hr>")
            i += 1
            continue
        # list items (dash or numbered)
        m = re.match(r"^[-*]\s+(.*)$", stripped) or re.match(r"^\d+\.\s+(.*)$", stripped)
        if m:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue
        # anchor tags (raw HTML <a id=...>)
        if stripped.startswith("<a id=") and stripped.endswith("</a>"):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(stripped)
            i += 1
            continue
        # paragraph
        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{inline(stripped)}</p>")
        i += 1
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def inline(text):
    """Minimal inline markdown: bold, code backticks, links, images (emoji kept)."""
    # escape stray HTML angle brackets but keep raw <a id> handled by caller
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # restore anchor tags
    text = re.sub(r"&lt;a id=&quot;([^&]+)&quot;&gt;", r'<a id="\1">', text)
    text = text.replace("&lt;/a&gt;", "</a>")
    # inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # links [text](url)
    def link_repl(m):
        url = m.group(2)
        if url.startswith("#"):
            return f'<a href="{url}">{m.group(1)}</a>'
        return f'<a href="{url}" target="_blank" rel="noopener">{m.group(1)}</a>'
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    return text


def build_article(summary_md):
    # parse front matter
    fm = re.match(r"^---\n(.*?)\n---\n", summary_md, re.S)
    meta = {}
    body = summary_md
    if fm:
        for line in fm.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        body = summary_md[fm.end():]

    date = meta.get("date", "")
    title = meta.get("title", "").strip('"')
    # plain title: "Horizon Summary: 2026-09-23 (ZH)"
    m = re.match(r"Horizon Summary:\s*([\d-]+)", title)
    if m:
        title = f"{m.group(1)} 每日资讯日报"
    else:
        title = (title or f"{date} 每日资讯日报").strip()

    # extract excerpt from first blockquote
    excerpt = ""
    qm = re.search(r">\s*(.+?)\n", body)
    if qm:
        excerpt = qm.group(1).strip()

    # count items
    item_count = len(re.findall(r"^\d+\.\s+\[", body, re.M))

    # main content HTML
    content_html = md_to_html(body)
    readtime = max(1, round(item_count * 0.8 + 1))

    article = {
        "slug": f"{date}-horizon-news",
        "title": title,
        "date": date,
        "tag": "AI 日报",
        "readtime": f"{readtime} 分钟",
        "excerpt": excerpt or f"今日精选 {item_count} 条重要资讯（自动生成）",
        "content": content_html,
    }
    return article


POST_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — why</title>
  <meta name="description" content="{excerpt}">
  <link rel="stylesheet" href="../style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌿</text></svg>">
</head>
<body>
  <div class="grain-overlay"></div>
  <header class="site-header scrolled">
    <div class="header-inner">
      <a href="../index.html" class="logo">
        <span class="logo-mark">✦</span>
        <span class="logo-text">聆语会数锯分析</span>
      </a>
      <nav class="main-nav">
        <a href="../index.html" class="nav-link">文章</a>
        <a href="../archive.html" class="nav-link">归档</a>
        <a href="../about.html" class="nav-link">关于</a>
      </nav>
    </div>
  </header>
  <main class="main-content">
    <div id="postContent"></div>
  </main>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-left">
        <span class="footer-logo">✦ 聆语会数锯分析</span>
        <p class="footer-desc">用文字捕捉思维的吉光片羽</p>
      </div>
      <div class="footer-right">
        <a href="https://github.com/whyyds2931" class="footer-link" target="_blank">GitHub</a>
        <a href="https://github.com/whyyds2931/whyyds2931.github.io" class="footer-link" target="_blank">Source</a>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© 2025 — 2026 · 使用 <a href="https://pages.github.com/" target="_blank">GitHub Pages</a> 托管</p>
    </div>
  </footer>
  <script>
    const article = {article_json};

    document.addEventListener('DOMContentLoaded', () => {{
      const container = document.getElementById('postContent');
      if (!container) return;
      container.innerHTML = `
        <div class="post-hero">
          <div class="post-hero-tag">${{article.tag}}</div>
          <h1 class="post-hero-title">${{article.title}}</h1>
          <div class="post-hero-meta">
            <span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              ${{new Date(article.date).toLocaleDateString('zh-CN', {{year:'numeric', month:'long', day:'numeric'}})}}
            </span>
            <span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              ${{article.readtime}}
            </span>
          </div>
        </div>
        <div class="post-divider"></div>
        <div class="post-content">${{article.content}}</div>
      `;
      document.title = article.title + " — 聆语会数锯分析";
    }});
  </script>
</body>
</html>
"""


def update_script_js(script_js, article):
    marker = "const articles = ["
    idx = script_js.find(marker)
    if idx < 0:
        raise RuntimeError("Cannot find articles array in script.js")
    insert_at = idx + len(marker)
    new_entry = "\n  " + json.dumps(article, ensure_ascii=False) + ","
    return script_js[:insert_at] + new_entry + script_js[insert_at:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--summary", required=True, help="path to summary-zh.md")
    ap.add_argument("--dry-run", action="store_true", help="build artifacts locally without pushing")
    args = ap.parse_args()

    with open(args.summary, encoding="utf-8") as f:
        summary_md = f.read()

    article = build_article(summary_md)
    print(f"文章: {article['title']} / slug={article['slug']} / {article['readtime']}")
    print(f"摘要: {article['excerpt']}")

    post_html = POST_TEMPLATE.format(
        title=article["title"].replace('"', "&quot;"),
        excerpt=article["excerpt"].replace('"', "&quot;"),
        article_json=json.dumps(article, ensure_ascii=False),
    )

    if args.dry_run:
        with open(f"out_{article['slug']}.html", "w", encoding="utf-8") as f:
            f.write(post_html)
        print(f"[dry-run] 已生成 out_{article['slug']}.html")
        return

    headers = {
        "Authorization": f"token {args.token}",
        "Accept": "application/vnd.github+json",
    }

    post_path = f"posts/{article['slug']}.html"
    print(f"→ 上传 {post_path}")
    put_file(headers, post_path, post_html, f"🤖 每日资讯自动发布: {article['date']}")

    script_js, script_sha = fetch_file(headers, "script.js")
    new_script = update_script_js(script_js, article)
    print("→ 更新 script.js（插入文章列表）")
    put_file(headers, "script.js", new_script, f"🤖 每日资讯自动发布: 更新列表 {article['date']}", sha=script_sha)

    print("✅ 已发布到博客仓库 main 分支，Pages 将自动部署")


if __name__ == "__main__":
    main()
