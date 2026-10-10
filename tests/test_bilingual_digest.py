import asyncio
from datetime import datetime, timezone

from src.ai.summarizer import DailySummarizer
from src.models import (
    ClassificationResult,
    ContentAnalysis,
    ContentArtifact,
    ContentBlock,
    ContentItem,
    ProcessingResult,
    SourceType,
)


def _item() -> ContentItem:
    return ContentItem(
        id="rss:bilingual:1",
        source_type=SourceType.RSS,
        title="Unused source title",
        url="https://example.com/1",
        content="A source article.",
        published_at=datetime.now(timezone.utc),
        processing=ProcessingResult(
            classification=ClassificationResult(profile="tech-news", method="source_override"),
            analysis=ContentAnalysis(score=8.5, reason="signal", summary="fallback"),
            artifacts={
                "zh": ContentArtifact(
                    language="zh",
                    title="English headline\n中文：中文标题",
                    blocks=[
                        ContentBlock(
                            id="summary",
                            title="English summary\n中文：中文摘要",
                            content="English explanation.\n中文：中文解释。",
                            primary=True,
                        )
                    ],
                )
            },
        ),
    )


def test_bilingual_summary_is_english_first_and_has_chinese_toggle_hooks():
    output = asyncio.run(
        DailySummarizer(profile_names={"tech-news": {"default": "Technology News", "zh": "科技新闻"}})
        .generate_summary([_item()], "2026-10-10", 1, language="zh", bilingual=True)
    )

    assert output.index("English headline") < output.index("中文标题")
    assert '<div class="bilingual-en">English explanation.</div>' in output
    assert '<div class="bilingual-zh"><strong>中文：</strong>中文解释。</div>' in output
    assert "Technology News" in output or "Tech News" in output
    assert "科技新闻" in output or "Tech News" in output
