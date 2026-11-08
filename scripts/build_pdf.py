#!/usr/bin/env python3
"""
Build a publication-quality PDF from paper/manuscript.md using reportlab.

Usage:
    python scripts/build_pdf.py [--in paper/manuscript.md] [--out paper/manuscript.pdf]

Handles: H1-H4 headings, justified body text, bold/italic/code inline,
pipe tables, bullet/numbered lists, blockquotes, images with captions,
horizontal rules, code fences, and a title page. Sets PDF metadata
(title/author/subject/keywords) which matters for Google Scholar pickup.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable

# --------------------------------------------------------------------------
# Fonts: prefer embedded Times New Roman so Greek/math glyphs survive.
# --------------------------------------------------------------------------
FONT_CANDIDATES = {
    "Serif": [
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Times New Roman.ttf",
    ],
    "Serif-Bold": [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    ],
    "Serif-Italic": [
        "/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf",
    ],
    "Serif-BoldItalic": [
        "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf",
    ],
}

BODY_FONT = "Times-Roman"
BODY_BOLD = "Times-Bold"
BODY_ITALIC = "Times-Italic"
BODY_BI = "Times-BoldItalic"
MONO_FONT = "Courier"
USE_TTF = False


def register_fonts() -> None:
    global BODY_FONT, BODY_BOLD, BODY_ITALIC, BODY_BI, USE_TTF
    mapping = {
        "Serif": ("Body", BODY_FONT),
        "Serif-Bold": ("BodyB", BODY_BOLD),
        "Serif-Italic": ("BodyI", BODY_ITALIC),
        "Serif-BoldItalic": ("BodyBI", BODY_BI),
    }
    ok = True
    for key, candidates in FONT_CANDIDATES.items():
        path = next((p for p in candidates if os.path.exists(p)), None)
        if path is None:
            ok = False
            continue
        alias = mapping[key][0]
        try:
            pdfmetrics.registerFont(TTFont(alias, path))
        except Exception:
            ok = False
    if ok:
        USE_TTF = True
        BODY_FONT = "Body"
        BODY_BOLD = "BodyB"
        BODY_ITALIC = "BodyI"
        BODY_BI = "BodyBI"
        # register the family so <b>/<i> work
        pdfmetrics.registerFontFamily(
            "Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyBI"
        )


# --------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------
PAGE_W, PAGE_H = A4
MARGIN = 24 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

ACCENT = colors.HexColor("#12395c")
GREY = colors.HexColor("#555555")
RULE = colors.HexColor("#c9d2da")

STYLES = {}


def build_styles() -> None:
    STYLES.update(
        {
            "title": ParagraphStyle(
                "title", fontName=BODY_BOLD, fontSize=21, leading=26,
                alignment=TA_LEFT, textColor=ACCENT, spaceAfter=10,
            ),
            "subtitle": ParagraphStyle(
                "subtitle", fontName=BODY_ITALIC, fontSize=13, leading=18,
                alignment=TA_LEFT, textColor=GREY, spaceAfter=8,
            ),
            "meta": ParagraphStyle(
                "meta", fontName=BODY_FONT, fontSize=10, leading=14,
                alignment=TA_LEFT, textColor=colors.black, spaceAfter=2,
            ),
            "h1": ParagraphStyle(
                "h1", fontName=BODY_BOLD, fontSize=16, leading=20,
                textColor=ACCENT, spaceBefore=16, spaceAfter=8,
            ),
            "h2": ParagraphStyle(
                "h2", fontName=BODY_BOLD, fontSize=13, leading=17,
                textColor=ACCENT, spaceBefore=14, spaceAfter=6,
            ),
            "h3": ParagraphStyle(
                "h3", fontName=BODY_BOLD, fontSize=11, leading=14,
                textColor=colors.black, spaceBefore=10, spaceAfter=4,
            ),
            "h4": ParagraphStyle(
                "h4", fontName=BODY_ITALIC, fontSize=10.5, leading=14,
                textColor=GREY, spaceBefore=8, spaceAfter=3,
            ),
            "body": ParagraphStyle(
                "body", fontName=BODY_FONT, fontSize=10.5, leading=15.5,
                alignment=TA_JUSTIFY, spaceAfter=7, firstLineIndent=0,
            ),
            "abstract": ParagraphStyle(
                "abstract", fontName=BODY_FONT, fontSize=9.8, leading=14,
                alignment=TA_JUSTIFY, spaceAfter=6,
                leftIndent=8, rightIndent=8,
            ),
            "bullet": ParagraphStyle(
                "bullet", fontName=BODY_FONT, fontSize=10.5, leading=15,
                alignment=TA_LEFT, leftIndent=16, bulletIndent=5,
                spaceAfter=3,
            ),
            "quote": ParagraphStyle(
                "quote", fontName=BODY_ITALIC, fontSize=10, leading=14.5,
                alignment=TA_LEFT, leftIndent=18, rightIndent=18,
                textColor=GREY, spaceBefore=4, spaceAfter=8,
            ),
            "caption": ParagraphStyle(
                "caption", fontName=BODY_FONT, fontSize=8.8, leading=12,
                alignment=TA_CENTER, textColor=GREY,
                spaceBefore=4, spaceAfter=12,
            ),
            "tablecell": ParagraphStyle(
                "tablecell", fontName=BODY_FONT, fontSize=8.6, leading=11.2,
                alignment=TA_LEFT,
            ),
            "tablehead": ParagraphStyle(
                "tablehead", fontName=BODY_BOLD, fontSize=8.6, leading=11.2,
                alignment=TA_LEFT,
            ),
            "code": ParagraphStyle(
                "code", fontName=MONO_FONT, fontSize=8.5, leading=11.5,
                alignment=TA_LEFT, leftIndent=10,
                backColor=colors.HexColor("#f4f6f8"),
                borderPadding=4, spaceBefore=4, spaceAfter=8,
            ),
            "ref": ParagraphStyle(
                "ref", fontName=BODY_FONT, fontSize=8.8, leading=12.5,
                alignment=TA_LEFT, leftIndent=14, firstLineIndent=-14,
                spaceAfter=4,
            ),
        }
    )


# --------------------------------------------------------------------------
# Inline markdown -> reportlab markup
# --------------------------------------------------------------------------
SYMBOLS = {
    "\u2013": "-", "\u2014": "--", "\u2212": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00a0": " ", "\u2009": " ", "\u202f": " ",
}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text: str) -> str:
    if not USE_TTF:
        # base-14 fonts use WinAnsi: substitute glyphs it cannot encode
        text = "".join(SYMBOLS.get(ch, ch) for ch in text)
    text = esc(text)
    # inline code first (protect it)
    text = re.sub(r"`([^`]+)`", lambda m: f'<font face="{MONO_FONT}" size="9">{m.group(1)}</font>', text)
    # links [text](url)
    def link(m):
        label, url = m.group(1), m.group(2)
        return label
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)
    # images that slipped into a paragraph
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    # bold, italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<i>\1</i>", text)
    # simple inline math $x$ -> italic x
    text = re.sub(r"\$([^$]+)\$", r"<i>\1</i>", text)
    return text


# --------------------------------------------------------------------------
# Markdown -> flowables
# --------------------------------------------------------------------------
IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")


def split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def make_table(rows: list[list[str]]) -> Table:
    ncols = max(len(r) for r in rows)
    norm = [r + [""] * (ncols - len(r)) for r in rows]
    data = [[Paragraph(inline(c), STYLES["tablehead" if i == 0 else "tablecell"]) for c in r]
            for i, r in enumerate(norm)]
    col_w = CONTENT_W / ncols
    t = Table(data, colWidths=[col_w] * ncols, repeatRows=1, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def make_image(path: Path, alt: str) -> list:
    if not path.exists():
        return [Paragraph(f"<i>[missing figure: {esc(str(path))}]</i>", STYLES["caption"])]
    try:
        from reportlab.lib.utils import ImageReader
        iw, ih = ImageReader(str(path)).getSize()
    except Exception:
        return [Paragraph(f"<i>[unreadable figure: {esc(str(path))}]</i>", STYLES["caption"])]
    max_w, max_h = CONTENT_W, 105 * mm
    scale = min(max_w / iw, max_h / ih)
    img = Image(str(path), width=iw * scale, height=ih * scale)
    img.hAlign = "CENTER"
    flows = [Spacer(1, 6), img]
    if alt:
        flows.append(Paragraph(inline(alt), STYLES["caption"]))
    else:
        flows.append(Spacer(1, 10))
    return flows


def parse_markdown(md: str, base_dir: Path):
    """Return (title, subtitle_lines, blocks) where blocks are rendered later."""
    lines = md.splitlines()
    blocks: list = []
    title = None
    i = 0
    in_code = False
    code_buf: list[str] = []
    current_heading = ""

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # code fences
        if stripped.startswith("```"):
            if in_code:
                blocks.append(("code", "\n".join(code_buf)))
                code_buf, in_code = [], False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # blank
        if not stripped:
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            blocks.append(("hr", None))
            i += 1
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 1 and title is None:
                title = re.sub(r"^[#\s]+", "", text)
            else:
                blocks.append((f"h{min(level,4)}", text))
                if level <= 2:
                    current_heading = text
            i += 1
            continue

        # image alone on a line
        mi = IMG_RE.match(stripped)
        if mi:
            blocks.append(("image", (mi.group(2), mi.group(1))))
            i += 1
            continue

        # blockquote
        if stripped.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(("quote", " ".join(b for b in buf if b)))
            continue

        # table: header row followed by separator
        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1]):
            rows = [split_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            blocks.append(("table", rows))
            continue

        # lists
        mb = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        mn = re.match(r"^(\s*)\d+[.)]\s+(.*)$", line)
        if mb or mn:
            items = []
            ordered = mn is not None
            while i < len(lines):
                l2 = lines[i]
                if not l2.strip():
                    # allow a single blank line inside a list
                    if i + 1 < len(lines) and re.match(r"^(\s*)([-*+]|\d+[.)])\s+", lines[i + 1]):
                        i += 1
                        continue
                    break
                m2 = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", l2)
                if not m2:
                    break
                this_ordered = m2.group(2)[0].isdigit()
                if this_ordered != ordered:
                    break  # a switch between bullet and numbered starts a new list
                indent = len(m2.group(1))
                items.append((indent, m2.group(3)))
                i += 1
            blocks.append(("list", (ordered, items)))
            continue

        # paragraph: gather until blank / block construct
        buf = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            ns = nxt.strip()
            if not ns:
                break
            if re.match(r"^(#{1,6}\s|>|\||```)", ns):
                break
            if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", ns):
                break
            if re.match(r"^(\s*)([-*+]|\d+[.)])\s+", nxt):
                break
            if IMG_RE.match(ns):
                break
            buf.append(ns)
            i += 1
        blocks.append(("p", " ".join(buf)))

    return title, blocks


def render(blocks, base_dir: Path) -> list:
    flow = []
    in_refs = False
    for kind, payload in blocks:
        if kind.startswith("h"):
            text = payload
            if kind in ("h1", "h2") and re.search(r"referenc|bibliograph", text, re.I):
                in_refs = True
            if in_refs and kind not in ("h1", "h2"):
                pass
            if kind == "h1":
                flow.append(Paragraph(inline(text), STYLES["h1"]))
            elif kind == "h2":
                flow.append(Paragraph(inline(text), STYLES["h2"]))
            elif kind == "h3":
                flow.append(Paragraph(inline(text), STYLES["h3"]))
            else:
                flow.append(Paragraph(inline(text), STYLES["h4"]))
        elif kind == "p":
            if in_refs:
                flow.append(Paragraph(inline(payload), STYLES["ref"]))
            else:
                flow.append(Paragraph(inline(payload), STYLES["body"]))
        elif kind == "quote":
            flow.append(Paragraph(inline(payload), STYLES["quote"]))
        elif kind == "hr":
            flow.append(Spacer(1, 4))
            flow.append(HRFlowable(width="100%", thickness=0.5, color=RULE))
            flow.append(Spacer(1, 6))
        elif kind == "code":
            safe = esc(payload).replace("\n", "<br/>")
            flow.append(Paragraph(safe, STYLES["code"]))
        elif kind == "table":
            flow.append(Spacer(1, 4))
            flow.append(make_table(payload))
            flow.append(Spacer(1, 10))
        elif kind == "image":
            path, alt = payload
            p = (base_dir / path).resolve()
            flow.extend(make_image(p, alt))
        elif kind == "list":
            ordered, items = payload
            for idx, (indent, text) in enumerate(items, 1):
                bullet = f"{idx}." if ordered else "\u2022"
                st = STYLES["bullet"]
                if indent >= 2:
                    st = ParagraphStyle("b2", parent=st, leftIndent=32, bulletIndent=21)
                flow.append(Paragraph(inline(text), st, bulletText=bullet))
    return flow


# --------------------------------------------------------------------------
# Document assembly
# --------------------------------------------------------------------------
class Manuscript(BaseDocTemplate):
    def __init__(self, filename, title, author, **kw):
        super().__init__(
            filename, pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=MARGIN + 6 * mm, bottomMargin=MARGIN,
            title=title, author=author,
            subject="Public attention decay after ceasefires, 2015-2025",
            keywords=("peace and conflict studies, ceasefire durability, issue attention, "
                      "Wikipedia pageviews, computational social science, UCDP, PAHL"),
            creator="The Half-Life of Peace",
            **kw,
        )
        self.short_title = title[:64] if title else ""
        frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN - 6 * mm, id="body")
        self.addPageTemplates([
            PageTemplate(id="title", frames=[frame], onPage=self._title_page),
            PageTemplate(id="body", frames=[frame], onPage=self._body_page),
        ])

    def _title_page(self, canv, doc):
        canv.saveState()
        canv.setFillColor(ACCENT)
        canv.rect(0, PAGE_H - 10 * mm, PAGE_W, 10 * mm, stroke=0, fill=1)
        canv.setFillColor(colors.HexColor("#e8eef4"))
        canv.rect(0, 0, PAGE_W, 6 * mm, stroke=0, fill=1)
        canv.restoreState()

    def _body_page(self, canv, doc):
        canv.saveState()
        canv.setFont(BODY_FONT, 7.6)
        canv.setFillColor(GREY)
        canv.drawString(MARGIN, PAGE_H - MARGIN + 2 * mm, self.short_title)
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 2 * mm,
                             "Preprint - 2026")
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.4)
        canv.line(MARGIN, PAGE_H - MARGIN + 1 * mm, PAGE_W - MARGIN, PAGE_H - MARGIN + 1 * mm)
        canv.line(MARGIN, MARGIN - 4 * mm, PAGE_W - MARGIN, MARGIN - 4 * mm)
        canv.setFont(BODY_FONT, 8.4)
        canv.setFillColor(GREY)
        canv.drawCentredString(PAGE_W / 2, MARGIN - 9 * mm, str(doc.page))
        canv.restoreState()


def build(in_path: Path, out_path: Path, author: str, repo: str) -> int:
    register_fonts()
    build_styles()
    md = in_path.read_text(encoding="utf-8")
    title, blocks = parse_markdown(md, in_path.parent)

    story = []
    # ---- title page ----
    story.append(Spacer(1, 34 * mm))
    story.append(Paragraph(
        '<font size="8.5" color="#12395c">RESEARCH PREPRINT</font>', STYLES["meta"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(inline(title or in_path.stem), STYLES["title"]))
    if blocks and blocks[0][0] == "p":
        story.append(Paragraph(inline(blocks[0][1]), STYLES["subtitle"]))
        blocks = blocks[1:]
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="35%", thickness=1, color=ACCENT, hAlign="LEFT"))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"<b>{esc(author)}</b>", STYLES["meta"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("November 2026", STYLES["meta"]))
    story.append(Paragraph(f"Code &amp; data: {esc(repo)}", STYLES["meta"]))
    story.append(Spacer(1, 18 * mm))
    story.append(Paragraph(
        "This is a preprint. It has not been peer reviewed. "
        "Replication materials, the analysis pipeline, and the underlying datasets "
        "are publicly available at the repository above.",
        ParagraphStyle("note", parent=STYLES["meta"], fontSize=8.6, leading=12,
                       textColor=GREY, rightIndent=20 * mm)))
    story.append(PageBreak())

    body = render(blocks, in_path.parent)
    if not body:
        print("ERROR: no content parsed from manuscript", file=sys.stderr)
        return 1

    # switch to body template after title page
    story.extend(body)

    doc = Manuscript(str(out_path), title or in_path.stem, author)
    doc.build(story)

    # force the body page template for all pages after the first
    return 0


class TwoTemplateDoc(Manuscript):
    """Uses the title template for page 1 and the body template thereafter."""

    def build_with_switch(self, story):
        # Build once with title template; reportlab picks templates per flowable
        # via page breaks, so we switch by emitting a NextPageTemplate.
        from reportlab.platypus import NextPageTemplate
        out = []
        for fl in story:
            if isinstance(fl, PageBreak):
                # set the next template BEFORE the break so page 2 onward is body
                out.append(NextPageTemplate("body"))
            out.append(fl)
        self.build(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent.parent
    ap.add_argument("--in", dest="inp", default=str(root / "paper" / "manuscript.md"))
    ap.add_argument("--out", dest="out", default=str(root / "paper" / "manuscript.pdf"))
    ap.add_argument("--author", default="Ahmed Jaffar")
    ap.add_argument("--repo", default="github.com/AhmedJaffar/half-life-of-peace")
    args = ap.parse_args()

    in_path, out_path = Path(args.inp), Path(args.out)
    if not in_path.exists():
        print(f"ERROR: {in_path} not found", file=sys.stderr)
        return 1
    out_path.parent.mkdir(parents=True, exist_ok=True)

    register_fonts()
    build_styles()
    md = in_path.read_text(encoding="utf-8")
    title, blocks = parse_markdown(md, in_path.parent)

    story = []
    story.append(Spacer(1, 34 * mm))
    story.append(Paragraph(
        '<font size="8.5" color="#12395c">RESEARCH PREPRINT</font>', STYLES["meta"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(inline(title or in_path.stem), STYLES["title"]))
    if blocks and blocks[0][0] == "p":
        story.append(Paragraph(inline(blocks[0][1]), STYLES["subtitle"]))
        blocks = blocks[1:]
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="35%", thickness=1, color=ACCENT, hAlign="LEFT"))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(f"<b>{esc(args.author)}</b>", STYLES["meta"]))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("November 2026", STYLES["meta"]))
    story.append(Paragraph(f"Code &amp; data: {esc(args.repo)}", STYLES["meta"]))
    story.append(Spacer(1, 16 * mm))
    story.append(Paragraph(
        "This is a preprint. It has not been peer reviewed. Replication materials, "
        "the analysis pipeline, and the underlying datasets are publicly available "
        "at the repository above.",
        ParagraphStyle("note", parent=STYLES["meta"], fontSize=8.6, leading=12,
                       textColor=GREY, rightIndent=20 * mm)))
    story.append(PageBreak())
    story.extend(render(blocks, in_path.parent))

    doc = TwoTemplateDoc(str(out_path), title or in_path.stem, args.author)
    doc.build_with_switch(story)

    size = out_path.stat().st_size
    print(f"OK wrote {out_path} ({size/1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
