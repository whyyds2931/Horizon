---
layout: default
title: Horizon Daily
---

<div class="home-intro" markdown="1">

# Horizon Daily

> English-first, Chinese-second briefings across technology, finance, biology, psychology, and research.

[配置指南](configuration) · [信息源](scrapers) · [评分系统](scoring) · [中文说明](https://github.com/whyyds2931/Horizon/blob/main/README_zh.md)

</div>

## Daily Briefings

{% assign digest_posts = site.posts | where: "lang", "bilingual" %}
{% assign fallback_posts = site.posts | where: "lang", "zh" %}
{% if digest_posts.size == 0 %}{% assign digest_posts = fallback_posts %}{% endif %}

<div class="digest-list">
{% for post in digest_posts limit:20 %}
  <a class="digest-row" href="{{ post.url | relative_url }}">
    <span class="digest-date">{{ post.date | date: "%Y.%m.%d" }}</span>
    <span class="digest-title">{{ post.title }}</span>
    <span class="digest-arrow" aria-hidden="true">↗</span>
  </a>
{% else %}
  <p><em>No daily briefing has been published yet. / 暂无日报。</em></p>
{% endfor %}
</div>

<div class="home-grid">
  <section>
    <h2>What Horizon follows</h2>
    <p>Four editorial lanes keep the daily digest useful: technology and tools, markets and finance, biology and life sciences, plus psychology and neuroscience.</p>
  </section>
  <section>
    <h2>How to read</h2>
    <p>Every item puts the English briefing first and the Simplified Chinese translation directly below it. Use the floating toggle for bilingual, English-only, or Chinese-only reading.</p>
  </section>
</div>
