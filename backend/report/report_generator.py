"""
report_generator.py
───────────────────
Generates a multi-page PDF report using ReportLab.

Structure:
  Page 1  — Cover page
  Page 2  — Executive Summary (overall scores table)
  Page 3+ — Aspect-by-aspect breakdown
  Last    — Recommendations for directors/producers

Usage (standalone):
  python report/report_generator.py

Or called via: GET /api/report/download
"""

import json
from pathlib import Path
from datetime import datetime
from reportlab.lib                    import colors
from reportlab.lib.pagesizes          import A4
from reportlab.lib.styles             import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units              import cm, mm
from reportlab.lib.enums              import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus               import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.graphics.shapes        import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics                import renderPDF

BASE_DIR = Path(__file__).resolve().parent.parent
AGG_DIR  = BASE_DIR / "data" / "aggregated"

# ── Colour palette ────────────────────────────────────────────
HINDI_COLOR  = colors.HexColor("#E85D04")    # warm orange
TELUGU_COLOR = colors.HexColor("#0077B6")    # deep blue
POS_COLOR    = colors.HexColor("#2D6A4F")    # forest green
NEG_COLOR    = colors.HexColor("#D62828")    # red
NEU_COLOR    = colors.HexColor("#6B7280")    # grey
DARK_BG      = colors.HexColor("#0F0F0F")
LIGHT_BG     = colors.HexColor("#F8F9FA")
ACCENT       = colors.HexColor("#FFB703")

ALL_ASPECTS = ["acting", "audio", "technical", "plot", "dub_quality", "direction"]


# ── Custom styles ─────────────────────────────────────────────

def build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontSize   = 32,
        fontName   = "Helvetica-Bold",
        textColor  = colors.white,
        alignment  = TA_CENTER,
        spaceAfter = 12,
    )
    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontSize   = 14,
        fontName   = "Helvetica",
        textColor  = colors.HexColor("#CCCCCC"),
        alignment  = TA_CENTER,
        spaceAfter = 8,
    )
    styles["section_title"] = ParagraphStyle(
        "section_title",
        fontSize    = 16,
        fontName    = "Helvetica-Bold",
        textColor   = colors.HexColor("#0F0F0F"),
        spaceBefore = 16,
        spaceAfter  = 8,
        borderPad   = 4,
    )
    styles["body"] = ParagraphStyle(
        "body",
        fontSize   = 10,
        fontName   = "Helvetica",
        textColor  = colors.HexColor("#333333"),
        spaceAfter = 6,
        leading    = 14,
    )
    styles["comment"] = ParagraphStyle(
        "comment",
        fontSize   = 9,
        fontName   = "Helvetica-Oblique",
        textColor  = colors.HexColor("#555555"),
        spaceAfter = 4,
        leftIndent = 12,
        leading    = 13,
    )
    styles["label_pos"] = ParagraphStyle(
        "label_pos",
        fontSize  = 9,
        fontName  = "Helvetica-Bold",
        textColor = POS_COLOR,
    )
    styles["label_neg"] = ParagraphStyle(
        "label_neg",
        fontSize  = 9,
        fontName  = "Helvetica-Bold",
        textColor = NEG_COLOR,
    )
    styles["rec"] = ParagraphStyle(
        "rec",
        fontSize    = 10,
        fontName    = "Helvetica",
        textColor   = colors.HexColor("#1A1A2E"),
        leftIndent  = 16,
        spaceAfter  = 6,
        bulletText  = "▸",
        leading     = 14,
    )
    return styles


def score_to_pct(score: float) -> str:
    """Convert -1..+1 score to a readable sentiment percentage."""
    pct = (score + 1) / 2 * 100
    return f"{pct:.1f}%"


def mini_bar_chart(hindi_score: float, telugu_score: float,
                   width: float = 200, height: float = 60) -> Drawing:
    """Create a small horizontal bar chart for aspect comparison."""
    d = Drawing(width, height)

    bar_h = 14
    max_w = width - 60

    # Hindi bar
    hi_w = max(4, (hindi_score + 1) / 2 * max_w)
    d.add(Rect(50, 38, hi_w, bar_h,
               fillColor=HINDI_COLOR, strokeColor=None))
    d.add(String(2, 44, "Hindi", fontSize=8,
                 fillColor=colors.HexColor("#333333")))
    d.add(String(50 + hi_w + 4, 44,
                 f"{hindi_score:+.2f}", fontSize=8,
                 fillColor=HINDI_COLOR))

    # Telugu bar
    te_w = max(4, (telugu_score + 1) / 2 * max_w)
    d.add(Rect(50, 16, te_w, bar_h,
               fillColor=TELUGU_COLOR, strokeColor=None))
    d.add(String(2, 22, "Telugu", fontSize=8,
                 fillColor=colors.HexColor("#333333")))
    d.add(String(50 + te_w + 4, 22,
                 f"{telugu_score:+.2f}", fontSize=8,
                 fillColor=TELUGU_COLOR))

    return d


# ── Page builders ─────────────────────────────────────────────

def build_cover(styles: dict, movie: str, generated_at: str) -> list:
    story = []

    # Dark background rectangle drawn via canvas (we use a table trick)
    cover_table = Table(
        [[Paragraph(
            f"<font color='#FFB703'>CINEPULSE</font>"
            f"<font color='white'>-INDIC</font>",
            styles["cover_title"]
        )],
         [Paragraph("Cross-Linguistic Sentiment Analysis", styles["cover_sub"])],
         [Paragraph(f"PAN-INDIA CINEMA REPORT", styles["cover_sub"])],
         [Spacer(1, 0.5*cm)],
         [Paragraph(f"<font size=22><b>{movie}</b></font>",
                    ParagraphStyle("mv", fontSize=22, fontName="Helvetica-Bold",
                                   textColor=ACCENT, alignment=TA_CENTER))],
         [Spacer(1, 0.3*cm)],
         [Paragraph("Hindi &amp; Telugu Community Sentiment",
                    ParagraphStyle("ml", fontSize=13, fontName="Helvetica",
                                   textColor=colors.HexColor("#AAAAAA"),
                                   alignment=TA_CENTER))],
         [Spacer(1, 1*cm)],
         [Paragraph(
             f"Generated: {generated_at[:10]}",
             ParagraphStyle("dt", fontSize=10, fontName="Helvetica",
                            textColor=colors.HexColor("#888888"),
                            alignment=TA_CENTER)
         )],
        ],
        colWidths=[15*cm],
    )
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING",  (0, 0), (-1, -1), 24),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [8]),
    ]))

    story.append(Spacer(1, 3*cm))
    story.append(cover_table)
    story.append(PageBreak())
    return story


def build_executive_summary(styles, scores_data: dict) -> list:
    story = []
    story.append(Paragraph("Executive Summary", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=2,
                            color=ACCENT, spaceAfter=12))

    languages = scores_data.get("languages", {})
    total_comments = sum(
        v.get("total_comments", 0) for v in languages.values()
    )

    story.append(Paragraph(
        f"This report analyses <b>{total_comments:,}</b> comments collected "
        f"from YouTube and Reddit for the movie "
        f"<b>{scores_data.get('movie', 'Dhurandhar')}</b>, "
        f"covering both Hindi and Telugu language communities.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.4*cm))

    # Overall scores table
    table_data = [
        ["Metric", "Hindi", "Telugu"],
    ]
    for lang in ["hindi", "telugu"]:
        ov = languages.get(lang, {}).get("overall", {})
        table_data[0].append("")  # placeholder

    table_data = [["Metric", "Hindi", "Telugu"]]

    hi_ov = languages.get("hindi",  {}).get("overall", {})
    te_ov = languages.get("telugu", {}).get("overall", {})

    rows = [
        ("Total Comments",
         str(languages.get("hindi",  {}).get("total_comments", 0)),
         str(languages.get("telugu", {}).get("total_comments", 0))),
        ("Positive %",
         f"{hi_ov.get('positive_pct', 0):.1f}%",
         f"{te_ov.get('positive_pct', 0):.1f}%"),
        ("Negative %",
         f"{hi_ov.get('negative_pct', 0):.1f}%",
         f"{te_ov.get('negative_pct', 0):.1f}%"),
        ("Neutral %",
         f"{hi_ov.get('neutral_pct', 0):.1f}%",
         f"{te_ov.get('neutral_pct', 0):.1f}%"),
        ("Weighted Sentiment Score",
         f"{hi_ov.get('weighted_sentiment_score', 0):+.3f}",
         f"{te_ov.get('weighted_sentiment_score', 0):+.3f}"),
    ]
    table_data.extend(rows)

    tbl = Table(table_data, colWidths=[6*cm, 4*cm, 4*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  DARK_BG),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  11),
        ("BACKGROUND",   (1, 1), (1, -1),  colors.HexColor("#FFF3E8")),
        ("BACKGROUND",   (2, 1), (2, -1),  colors.HexColor("#E8F4FD")),
        ("FONTSIZE",     (0, 1), (-1, -1), 10),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8F9FA")]),
        ("BOX",          (0, 0), (-1, -1), 1, colors.HexColor("#E0E0E0")),
        ("INNERGRID",    (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    story.append(tbl)
    story.append(PageBreak())
    return story


def build_aspect_pages(styles, scores_data: dict,
                        report_data: dict) -> list:
    story = []
    languages = scores_data.get("languages", {})
    top_comments = report_data.get("top_comments", {})

    aspect_labels = {
        "acting"     : "Acting & Performance",
        "audio"      : "Background Music & Audio",
        "technical"  : "VFX, Cinematography & Editing",
        "plot"        : "Story & Screenplay",
        "dub_quality": "Dubbing Quality",
        "direction"  : "Direction & Pacing",
    }

    for aspect in ALL_ASPECTS:
        label = aspect_labels.get(aspect, aspect.replace("_", " ").title())
        story.append(Paragraph(label, styles["section_title"]))
        story.append(HRFlowable(width="100%", thickness=1.5,
                                color=ACCENT, spaceAfter=10))

        hi_data = (languages.get("hindi",  {})
                   .get("aspects", {}).get(aspect, {}))
        te_data = (languages.get("telugu", {})
                   .get("aspects", {}).get(aspect, {}))

        hi_score = hi_data.get("weighted_sentiment_score", 0)
        te_score = te_data.get("weighted_sentiment_score", 0)

        # Score comparison table
        tbl_data = [
            ["", "Hindi", "Telugu"],
            ["Comments",
             str(hi_data.get("comment_count", 0)),
             str(te_data.get("comment_count", 0))],
            ["Positive %",
             f"{hi_data.get('positive_pct', 0):.1f}%",
             f"{te_data.get('positive_pct', 0):.1f}%"],
            ["Negative %",
             f"{hi_data.get('negative_pct', 0):.1f}%",
             f"{te_data.get('negative_pct', 0):.1f}%"],
            ["Sentiment Score",
             f"{hi_score:+.3f}",
             f"{te_score:+.3f}"],
        ]

        tbl = Table(tbl_data, colWidths=[5*cm, 3.5*cm, 3.5*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND",  (1, 1), (1, -1), colors.HexColor("#FFF3E8")),
            ("BACKGROUND",  (2, 1), (2, -1), colors.HexColor("#E8F4FD")),
            ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("INNERGRID",   (0, 0), (-1, -1), 0.5, colors.HexColor("#EEEEEE")),
            ("TOPPADDING",  (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0,0), (-1, -1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.4*cm))

        # Mini bar chart
        story.append(mini_bar_chart(hi_score, te_score))
        story.append(Spacer(1, 0.4*cm))

        # Top comments
        aspect_comments = top_comments.get(aspect, {})
        for lang in ["hindi", "telugu"]:
            lang_label = "Hindi" if lang == "hindi" else "Telugu"
            lang_color = HINDI_COLOR if lang == "hindi" else TELUGU_COLOR

            pos_comments = aspect_comments.get(lang, {}).get("positive", [])
            neg_comments = aspect_comments.get(lang, {}).get("negative", [])

            if pos_comments or neg_comments:
                story.append(Paragraph(
                    f"<font color='{'#E85D04' if lang == 'hindi' else '#0077B6'}'>"
                    f"<b>{lang_label} Community</b></font>",
                    styles["body"],
                ))

            for c in pos_comments[:2]:
                text = str(c.get("text", ""))[:200]
                story.append(Paragraph(
                    f'<font color="#2D6A4F">▲ POSITIVE</font>  "{text}"',
                    styles["comment"],
                ))
            for c in neg_comments[:2]:
                text = str(c.get("text", ""))[:200]
                story.append(Paragraph(
                    f'<font color="#D62828">▼ NEGATIVE</font>  "{text}"',
                    styles["comment"],
                ))

        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.HexColor("#DDDDDD")))
        story.append(Spacer(1, 0.3*cm))

    story.append(PageBreak())
    return story


def build_recommendations(styles, report_data: dict) -> list:
    story = []
    story.append(Paragraph("Recommendations", styles["section_title"]))
    story.append(HRFlowable(width="100%", thickness=2,
                            color=ACCENT, spaceAfter=12))
    story.append(Paragraph(
        "Based on the weighted sentiment analysis across both language communities, "
        "the following actionable insights are highlighted for the production team:",
        styles["body"],
    ))
    story.append(Spacer(1, 0.3*cm))

    recs = report_data.get("recommendations", [])
    for rec in recs:
        story.append(Paragraph(f"▸  {rec}", styles["body"]))
        story.append(Spacer(1, 0.2*cm))

    # Gap analysis table
    gaps = report_data.get("gap_analysis", [])
    if gaps:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Aspect Gap Analysis", styles["section_title"]))
        story.append(Paragraph(
            "Aspects ranked by sentiment gap between Hindi and Telugu communities. "
            "Larger gaps indicate localisation or quality mismatches.",
            styles["body"],
        ))

        gap_table_data = [["Aspect", "Hindi Score", "Telugu Score", "Gap"]]
        for item in gaps:
            aspect = item["aspect"].replace("_", " ").title()
            gap_table_data.append([
                aspect,
                f"{item['hindi_score']:+.3f}",
                f"{item['telugu_score']:+.3f}",
                f"{item['gap']:.3f}",
            ])

        tbl = Table(gap_table_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F8F9FA")]),
            ("BOX",         (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("INNERGRID",   (0, 0), (-1, -1), 0.5, colors.HexColor("#EEEEEE")),
            ("TOPPADDING",  (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0,0), (-1, -1), 6),
        ]))
        story.append(tbl)

    return story


# ── Main generate function ────────────────────────────────────

def generate_pdf(report_data: dict, scores_data: dict,
                 output_path: str):
    print(f"  Generating PDF report → {output_path}")

    doc = SimpleDocTemplate(
        output_path,
        pagesize    = A4,
        rightMargin = 2*cm,
        leftMargin  = 2*cm,
        topMargin   = 2*cm,
        bottomMargin= 2*cm,
    )

    styles = build_styles()
    story  = []

    movie        = scores_data.get("movie", "Dhurandhar")
    generated_at = report_data.get("generated_at", datetime.now().isoformat())

    story += build_cover(styles, movie, generated_at)
    story += build_executive_summary(styles, scores_data)
    story += build_aspect_pages(styles, scores_data, report_data)
    story += build_recommendations(styles, report_data)

    doc.build(story)
    print(f"  ✅ PDF saved → {output_path}")


# ── Standalone usage ──────────────────────────────────────────

if __name__ == "__main__":
    report_path = AGG_DIR / "dhurandhar_report_data.json"
    scores_path = AGG_DIR / "dhurandhar_scores.json"
    out_path    = AGG_DIR / "dhurandhar_report.pdf"

    if not report_path.exists() or not scores_path.exists():
        print("  ✗ Run the pipeline first: python run_pipeline.py")
        exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)
    with open(scores_path, "r", encoding="utf-8") as f:
        scores_data = json.load(f)

    generate_pdf(report_data, scores_data, str(out_path))
