"""
Export module - export posts to PDF using reportlab
"""
import os
import datetime

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")


def _ensure_exports_dir():
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def export_posts_to_pdf(posts: list, filename: str = None) -> str:
    """Export a list of post dicts to a PDF file. Returns the file path."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
        )
    except ImportError:
        raise RuntimeError(
            "reportlab is not installed. Run: pip install reportlab"
        )

    _ensure_exports_dir()
    if filename is None:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"blog_export_{ts}.pdf"
    filepath = os.path.join(EXPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PostTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=12,
    )
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#e94560"),
        spaceAfter=4,
        alignment=1,
    )

    story = []
    story.append(Paragraph("📝 Blog Export", header_style))
    ts_str = datetime.datetime.now().strftime("%B %d, %Y %H:%M")
    story.append(Paragraph(f"Generated on {ts_str}", meta_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#e94560")))
    story.append(Spacer(1, 0.5 * cm))

    for i, post in enumerate(posts):
        story.append(Paragraph(post.get("title", "Untitled"), title_style))
        meta = (
            f"By <b>{post.get('author', 'Unknown')}</b> | "
            f"Category: {post.get('category', 'General')} | "
            f"Tags: {post.get('tags', '') or 'None'} | "
            f"👍 {post.get('likes', 0)}  👎 {post.get('dislikes', 0)} | "
            f"Posted: {post.get('created_at', '')[:10]}"
        )
        story.append(Paragraph(meta, meta_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.2 * cm))

        content = post.get("content", "").replace("\n", "<br/>")
        story.append(Paragraph(content, body_style))

        if i < len(posts) - 1:
            story.append(PageBreak())

    doc.build(story)
    return filepath
