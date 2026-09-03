# backend/services/report_generator.py

import os
import io
import html
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

def sanitize_for_pdf(text: Any) -> str:
    """
    Replace all unicode typography (curly quotes, dashes, mathematical symbols,
    non-breaking hyphens/spaces, LaTeX formulas) with clean ASCII equivalents that
    render flawlessly in standard ReportLab Helvetica fonts without black box (■) artifacts.
    """
    if text is None:
        return ""
    s = str(text)
    
    # 1. Non-breaking hyphens, soft hyphens, and dashes -> Standard hyphen '-'
    s = s.replace('\u2010', '-')   # Hyphen
    s = s.replace('\u2011', '-')   # Non-breaking hyphen (CRITICAL: was showing as black box ■)
    s = s.replace('\u2012', '-')   # Figure dash
    s = s.replace('\u2013', ' - ') # En dash
    s = s.replace('\u2014', ' -- ')# Em dash
    s = s.replace('\u2015', ' -- ')# Horizontal bar
    s = s.replace('\u2212', '-')   # Minus sign
    s = s.replace('\u00ad', '')    # Soft hyphen
    s = s.replace('\u25a0', '')    # Black square
    s = s.replace('\u25aa', '')    # Black small square
    s = s.replace('\u25cf', '-')   # Black circle
    s = s.replace('\u2022', '-')   # Bullet
    s = s.replace('\u2219', '-')   # Bullet operator
    
    # 2. Curly Quotes & Apostrophes -> Standard quotes
    s = s.replace('\u2018', "'")   # Left single quote
    s = s.replace('\u2019', "'")   # Right single quote
    s = s.replace('\u201a', "'")   # Single low-9 quote
    s = s.replace('\u201b', "'")   # Single high-reversed-9 quote
    s = s.replace('\u201c', '"')   # Left double quote
    s = s.replace('\u201d', '"')   # Right double quote
    s = s.replace('\u201e', '"')   # Double low-9 quote
    s = s.replace('\u201f', '"')   # Double high-reversed-9 quote
    s = s.replace('\u00ab', '"')   # Left-pointing double angle quotation mark
    s = s.replace('\u00bb', '"')   # Right-pointing double angle quotation mark
    s = s.replace('`', "'")
    
    # 3. Spaces (Non-breaking, thin, zero-width)
    s = s.replace('\u00a0', ' ')   # No-break space
    s = s.replace('\u202f', ' ')   # Narrow no-break space
    s = s.replace('\u2009', ' ')   # Thin space
    s = s.replace('\u200a', ' ')   # Hair space
    s = s.replace('\u200b', '')    # Zero-width space
    s = s.replace('\u200c', '')    # Zero-width non-joiner
    s = s.replace('\u200d', '')    # Zero-width joiner
    s = s.replace('\ufeff', '')    # Byte order mark
    
    # 4. Math, Arrows, and Symbols
    s = s.replace('\u00d7', 'x')   # Multiplication sign × -> x
    s = s.replace('\u2248', '~')   # Almost equal ≈ -> ~
    s = s.replace('\u2264', '<=')  # Less than or equal ≤ -> <=
    s = s.replace('\u2265', '>=')  # Greater than or equal ≥ -> >=
    s = s.replace('\u2260', '!=')  # Not equal ≠ -> !=
    s = s.replace('\u2192', '->')  # Right arrow → -> ->
    s = s.replace('\u2190', '<-')  # Left arrow ← -> <-
    s = s.replace('\u21d2', '=>')  # Rightwards double arrow ⇒ -> =>
    s = s.replace('\u2211', 'sum') # N-ary summation
    s = s.replace('\u221a', 'sqrt')# Square root
    s = s.replace('\u221e', 'inf') # Infinity
    s = s.replace('\u00b1', '+/-') # Plus-minus sign
    s = s.replace('\u00b0', ' deg')# Degree sign
    s = s.replace('\u2026', '...') # Horizontal ellipsis
    
    # 5. LaTeX cleanup
    s = re.sub(r'\\\(', '', s)
    s = re.sub(r'\\\)', '', s)
    s = re.sub(r'\$\$', '', s)
    s = re.sub(r'\$', '', s)
    s = re.sub(r'\\text\{([^}]+)\}', r'\1', s)
    s = re.sub(r'\\log', 'log', s)
    s = re.sub(r'\\exp', 'exp', s)
    s = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1/\2)', s)
    s = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', s)
    s = re.sub(r'\\sum', 'sum', s)
    s = re.sub(r'\\_', '_', s)
    s = re.sub(r'\{([^}]+)\}', r'\1', s)
    
    return s

def clean_xml_text(text: Any) -> str:
    """Safely sanitize and escape text for ReportLab XML Paragraph parser."""
    if text is None:
        return ""
    s = sanitize_for_pdf(text)
    s = html.escape(s, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', s)
    return s

class ReportGenerator:
    """
    Generate comprehensive, multi-section academic research reports in Markdown,
    JSON, and professionally styled PDF formats.
    Includes all information generated across tabs (Simplified Summary, Limitations,
    Research Gaps, Novel Discoveries, Improvements, Online Comparison, and Chat Q&A).
    """

    def generate_markdown_report(self, analysis: dict, paper_id: str,
                                 simplified_summary: Optional[dict] = None,
                                 novel_discovery: Optional[dict] = None,
                                 comparison: Optional[dict] = None,
                                 qa_history: Optional[List[dict]] = None) -> str:
        """Generate a complete, structured markdown report with all app generated content."""
        title = analysis.get("title") or paper_id
        domain = (novel_discovery and novel_discovery.get("domain")) or analysis.get("domain") or "Academic Research"
        date_str = datetime.now().strftime("%B %d, %Y - %H:%M")
        
        report = []
        report.append(f"# Research Analysis & Gap Report: {title}")
        report.append(f"**Paper ID:** `{paper_id}` | **Detected Domain:** {domain}")
        report.append(f"*Generated on: {date_str} by ScrutinAI - Research Gap Finder*")
        report.append("\n---\n")
        
        # 1. Executive Summary (Simplified)
        if simplified_summary:
            solves = simplified_summary.get("what_it_solves", {})
            flowchart = solves.get("flowchart", {}) if isinstance(solves.get("flowchart"), dict) else {}
            
            report.append("## 1. Executive Plain-English Summary\n")
            if solves.get("plain_summary"):
                report.append(f"{solves['plain_summary']}\n")
            
            report.append("### Core Problem-Solution Workflow")
            report.append(f"- **The Problem:** {flowchart.get('problem', solves.get('problem', 'Researchers face efficiency and complexity bottlenecks.'))}")
            report.append(f"- **The Solution:** {flowchart.get('solution', solves.get('solution', 'A streamlined computational framework introduced by the authors.'))}")
            report.append(f"- **Real-World Impact:** {flowchart.get('impact', solves.get('impact', 'Accelerated discovery speed with verified empirical accuracy.'))}")
            report.append("")
        
        # 2. Limitations (Author-Stated & Methodological)
        explicit = analysis.get("explicit_limitations", [])
        inferred = analysis.get("inferred_limitations", [])
        
        if explicit or inferred:
            report.append("## 2. Research Limitations & Practical Constraints\n")
            
            if explicit:
                report.append("### 2.1 Author-Acknowledged Explicit Limitations\n")
                for i, item in enumerate(explicit, 1):
                    report.append(f"#### 2.1.{i} {item.get('title', 'Explicit Limitation')}")
                    if item.get("page"):
                        report.append(f"*Source Citation: Page {item.get('page')}*")
                    if item.get("quote"):
                        report.append(f"> \"{item.get('quote')}\"")
                    if item.get("description"):
                        report.append(f"\n**Technical Analysis:** {item.get('description')}")
                    if item.get("literature_comparison"):
                        report.append(f"\n**Practical Impact & Context:** {item.get('literature_comparison')}")
                    report.append("")
            
            if inferred:
                report.append("### 2.2 System-Inferred Methodological Vulnerabilities\n")
                for i, item in enumerate(inferred, 1):
                    report.append(f"#### 2.2.{i} {item.get('title', 'Inferred Vulnerability')}")
                    if item.get("description"):
                        report.append(f"**Methodological Flaw:** {item.get('description')}")
                    if item.get("reasoning_chain"):
                        report.append("\n**Deductive Reasoning Chain:**")
                        for step in item.get("reasoning_chain", []):
                            report.append(f"- {step}")
                    if item.get("literature_comparison"):
                        report.append(f"\n**Literature Perspective:** {item.get('literature_comparison')}")
                    report.append("")
        
        # 3. Prioritized Research Gaps
        gaps = analysis.get("research_gaps", [])
        if gaps:
            report.append("## 3. Prioritized Research Gaps & Open Questions\n")
            for i, gap in enumerate(gaps, 1):
                priority = (gap.get("priority") or "MEDIUM").upper()
                report.append(f"### 3.{i} [{priority} PRIORITY] {gap.get('title') or gap.get('description', 'Research Gap')}")
                if gap.get("description"):
                    report.append(f"**Problem Formulation:** {gap.get('description')}")
                if gap.get("impact"):
                    report.append(f"**Transformative Impact:** {gap.get('impact')}")
                if gap.get("evidence"):
                    report.append(f"**Evidence from Paper:** {gap.get('evidence')}")
                if gap.get("cross_literature_gap"):
                    report.append(f"**Cross-Literature Frontier:** {gap.get('cross_literature_gap')}")
                if gap.get("proposed_blueprint"):
                    report.append("\n**Proposed Research Blueprint:**")
                    for step in gap.get("proposed_blueprint", []):
                        report.append(f"- {step}")
                report.append("")
        
        # 4. Novel Discoveries (Elite Insights)
        disc_source = novel_discovery or analysis.get("novel_discoveries", {})
        all_disc = disc_source.get("all_discoveries", []) if isinstance(disc_source, dict) else []
        if all_disc:
            report.append("## 4. 'New-to-the-World' Novel Breakthrough Discoveries\n")
            for i, disc in enumerate(all_disc, 1):
                cat = disc.get("category", "Novel Discovery")
                report.append(f"### 4.{i} [{cat}] {disc.get('title', 'Discovery')}")
                if disc.get("the_core_paradigm"):
                    report.append(f"**The Core Paradigm:** {disc.get('the_core_paradigm')}")
                if disc.get("why_it_is_new"):
                    report.append(f"**Why This Is NEW to the World:** {disc.get('why_it_is_new')}")
                if disc.get("reasoning_chain"):
                    report.append("\n**Deductive Reasoning Chain:**")
                    for step in disc.get("reasoning_chain", []):
                        report.append(f"- {step}")
                if disc.get("evidence"):
                    report.append(f"**Evidence from Paper:** {disc.get('evidence')}")
                if disc.get("impact"):
                    report.append(f"**Theoretical & Empirical Impact:** {disc.get('impact')}")
                if disc.get("actionable_blueprint"):
                    report.append(f"**Actionable Blueprint:** {disc.get('actionable_blueprint')}")
                report.append("")
        
        # 5. Actionable Improvements
        improvements = analysis.get("suggested_improvements", [])
        if improvements:
            report.append("## 5. Actionable Methodological Improvements\n")
            for i, imp in enumerate(improvements, 1):
                report.append(f"### 5.{i} {imp.get('title', 'Improvement Recommendation')}")
                if imp.get("what_to_change"):
                    report.append(f"**What to Change:** {imp.get('what_to_change')}")
                if imp.get("why_it_helps"):
                    report.append(f"**Why It Helps:** {imp.get('why_it_helps')}")
                if imp.get("implementation_steps"):
                    report.append("\n**Step-by-Step Implementation Protocol:**")
                    for step in imp.get("implementation_steps", []):
                        report.append(f"- {step}")
                if imp.get("expected_benefit"):
                    report.append(f"\n**Expected Benefit:** {imp.get('expected_benefit')}")
                if imp.get("comparative_baseline"):
                    report.append(f"**Comparative Baseline:** {imp.get('comparative_baseline')}")
                report.append("")
        
        # 6. Online Literature Comparison
        comp_obj = comparison or {}
        comp_analysis = comp_obj.get("comparison_analysis") or analysis.get("comparison_analysis", "")
        similar_papers = comp_obj.get("similar_papers") or analysis.get("similar_papers", [])
        
        if comp_analysis or similar_papers:
            report.append("## 6. Online Literature Comparison & SOTA Baseline Synthesis\n")
            if comp_analysis:
                report.append(f"{comp_analysis}\n")
            
            if similar_papers:
                report.append("### Related Publications Found Online:")
                for p in similar_papers:
                    p_title = p.get("title", "Related Paper")
                    p_url = p.get("url", "#")
                    p_source = p.get("source", "Online Repository")
                    p_contrast = p.get("what_it_covers_that_your_paper_doesnt", "Covers broader comparative baselines.")
                    report.append(f"- [{p_title}]({p_url}) *({p_source})*")
                    report.append(f"  - **Coverage Difference:** {p_contrast}")
                report.append("")
        
        # 7. Interactive Q&A Sessions
        if qa_history:
            valid_qa = [qa for qa in qa_history if isinstance(qa, dict) and qa.get("question") and qa.get("answer")]
            if valid_qa:
                report.append("## 7. Interactive Research Q&A Sessions\n")
                for i, qa in enumerate(valid_qa, 1):
                    q = qa.get("question", "").strip()
                    a = qa.get("answer", "").strip()
                    report.append(f"### Q{i}: {q}")
                    report.append(f"**Answer:**\n{a}\n")
        
        report.append("\n---\n*Report generated by ScrutinAI - Research Gap Finder(Elite Academic Discovery System)*")
        return "\n".join(report)

    def export_to_json(self, analysis: dict,
                       simplified_summary: Optional[dict] = None,
                       novel_discovery: Optional[dict] = None,
                       comparison: Optional[dict] = None,
                       qa_history: Optional[List[dict]] = None) -> dict:
        """Export full analysis as structured JSON."""
        return {
            "paper_id": analysis.get("paper_id", ""),
            "title": analysis.get("title", ""),
            "domain": (novel_discovery and novel_discovery.get("domain")) or analysis.get("domain", ""),
            "simplified_summary": simplified_summary or {},
            "explicit_limitations": analysis.get("explicit_limitations", []),
            "inferred_limitations": analysis.get("inferred_limitations", []),
            "research_gaps": analysis.get("research_gaps", []),
            "novel_discoveries": novel_discovery or analysis.get("novel_discoveries", {}),
            "suggested_improvements": analysis.get("suggested_improvements", []),
            "online_comparison": comparison or {
                "comparison_analysis": analysis.get("comparison_analysis", ""),
                "similar_papers": analysis.get("similar_papers", [])
            },
            "qa_history": qa_history or [],
            "generated_at": datetime.now().isoformat()
        }

    def _render_markdown_to_story(self, md_text: str, story: list, styles: dict, colors_dict: dict, max_width: float = 540.0):
        """
        Parses Markdown text (including markdown tables, headings, bold/italic, lists,
        and horizontal rules) into styled ReportLab Flowable objects.
        """
        from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, HRFlowable
        from reportlab.lib.styles import ParagraphStyle
        
        if not md_text:
            return

        lines = md_text.strip().split('\n')
        i = 0
        n = len(lines)
        
        c_primary = colors_dict['primary']
        c_dark = colors_dict['dark']
        c_border = colors_dict['border']
        c_card_bg = colors_dict['card_bg']
        
        body_style = styles['Body_Custom']
        h2_style = styles['Heading2_Custom']
        h3_style = ParagraphStyle('H3_Custom', parent=h2_style, fontSize=9, leading=12, textColor=c_primary, spaceBefore=4, spaceAfter=2)
        bullet_style = ParagraphStyle('Bullet_Custom', parent=body_style, leftIndent=12, firstLineIndent=-8, spaceAfter=2)
        quote_style = styles['Quote_Custom']
        
        # Table cell styles
        th_style = ParagraphStyle('TH_Style', fontName='Helvetica-Bold', fontSize=7.5, leading=10, textColor=colors_dict['white'])
        td_style = ParagraphStyle('TD_Style', fontName='Helvetica', fontSize=7.5, leading=10, textColor=c_dark)
        
        while i < n:
            line = lines[i].strip()
            
            # Blank line
            if not line:
                i += 1
                continue
            
            # Horizontal rule
            if line in ['---', '***', '___']:
                story.append(HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=3, spaceAfter=3))
                i += 1
                continue
            
            # Markdown Table detection
            if line.startswith('|') and i + 1 < n and '|---' in lines[i + 1]:
                table_raw_rows = []
                while i < n and lines[i].strip().startswith('|'):
                    row_line = lines[i].strip()
                    # Skip separator line |---|---|
                    if not re.match(r'^\|(\s*[-:]+\s*\|)+$', row_line):
                        cells = [c.strip() for c in row_line.strip('|').split('|')]
                        table_raw_rows.append(cells)
                    i += 1
                
                if table_raw_rows:
                    num_cols = max(len(r) for r in table_raw_rows)
                    norm_rows = []
                    for r_idx, row in enumerate(table_raw_rows):
                        while len(row) < num_cols:
                            row.append('')
                        
                        styled_row = []
                        is_header = (r_idx == 0)
                        for cell in row:
                            cell_text = clean_xml_text(cell)
                            p = Paragraph(cell_text, th_style if is_header else td_style)
                            styled_row.append(p)
                        norm_rows.append(styled_row)
                    
                    # Calculate column widths to fit max_width
                    if num_cols == 2:
                        col_widths = [150, max_width - 150]
                    elif num_cols == 3:
                        col_widths = [120, 180, max_width - 300]
                    elif num_cols == 4:
                        col_widths = [25, 150, 165, max_width - 340]
                    elif num_cols == 5:
                        col_widths = [25, 120, 120, 130, max_width - 395]
                    else:
                        w = max_width / num_cols
                        col_widths = [w] * num_cols
                    
                    t = Table(norm_rows, colWidths=col_widths)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors_dict['white'], c_card_bg]),
                        ('BOX', (0, 0), (-1, -1), 0.75, c_border),
                        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 5),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 4))
                continue
            
            # Headings
            if line.startswith('### '):
                h_text = clean_xml_text(line[4:].strip())
                story.append(Paragraph(h_text, h3_style))
                i += 1
                continue
            elif line.startswith('## '):
                h_text = clean_xml_text(line[3:].strip())
                story.append(Paragraph(h_text, h2_style))
                i += 1
                continue
            elif line.startswith('# '):
                h_text = clean_xml_text(line[2:].strip())
                story.append(Paragraph(h_text, h2_style))
                i += 1
                continue
            
            # Bullet / Numbered lists
            if line.startswith(('-', '*', '•')) or re.match(r'^\d+\.\s', line):
                bullet_match = re.match(r'^(\d+\.|\-|\*|•)\s*(.*)', line)
                if bullet_match:
                    prefix = bullet_match.group(1)
                    content = bullet_match.group(2)
                    bullet_sym = '&bull; ' if prefix in ['-', '*', '•'] else f'{prefix} '
                    p_text = f"{bullet_sym}{clean_xml_text(content)}"
                    story.append(Paragraph(p_text, bullet_style))
                    i += 1
                    continue
            
            # Blockquotes
            if line.startswith('>'):
                q_text = clean_xml_text(line.lstrip('>').strip())
                story.append(Paragraph(f"\"{q_text}\"", quote_style))
                i += 1
                continue
            
            # Regular paragraph text
            p_text = clean_xml_text(line)
            story.append(Paragraph(p_text, body_style))
            i += 1

    def generate_pdf_report(self, analysis: dict, paper_id: str,
                            simplified_summary: Optional[dict] = None,
                            novel_discovery: Optional[dict] = None,
                            comparison: Optional[dict] = None,
                            qa_history: Optional[List[dict]] = None) -> bytes:
        """
        Generate a publication-grade, fully styled academic critique PDF.
        Features zero black-box Unicode defects (■), beautiful tables, and complete section synthesis.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        buffer = io.BytesIO()
        
        # Standard Letter Page (612 x 792 pt). Usable width with 36pt margins = 540 pt.
        max_printable_width = 540.0
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        # Professional Academic Color Palette
        c_primary = colors.HexColor("#1e3a8a")     # Deep Navy
        c_accent = colors.HexColor("#2563eb")      # Indigo Blue
        c_dark = colors.HexColor("#0f172a")        # Dark Slate Text
        c_muted = colors.HexColor("#475569")       # Slate Muted
        c_card_bg = colors.HexColor("#f8fafc")     # Light Slate BG
        c_border = colors.HexColor("#cbd5e1")      # Slate Border
        c_high_text = colors.HexColor("#b91c1c")   # Crimson Red
        c_green = colors.HexColor("#059669")       # Emerald Green
        c_white = colors.HexColor("#ffffff")
        
        colors_dict = {
            'primary': c_primary,
            'accent': c_accent,
            'dark': c_dark,
            'muted': c_muted,
            'card_bg': c_card_bg,
            'border': c_border,
            'high_text': c_high_text,
            'green': c_green,
            'white': c_white
        }
        
        # Typography Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=c_primary,
            spaceAfter=3
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=c_muted,
            spaceAfter=8
        )
        
        h1_style = ParagraphStyle(
            'Heading1_Custom',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=11.5,
            leading=15,
            textColor=c_primary,
            spaceBefore=10,
            spaceAfter=5,
            keepWithNext=True
        )
        
        h2_style = ParagraphStyle(
            'Heading2_Custom',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=9.5,
            leading=13,
            textColor=c_dark,
            spaceBefore=6,
            spaceAfter=3,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'Body_Custom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=c_dark,
            spaceAfter=3
        )
        
        quote_style = ParagraphStyle(
            'Quote_Custom',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
            leftIndent=10,
            spaceAfter=3
        )
        
        styles_dict = {
            'Body_Custom': body_style,
            'Heading2_Custom': h2_style,
            'Quote_Custom': quote_style
        }
        
        story = []
        
        # Document Header
        title = analysis.get("title") or paper_id
        domain = (novel_discovery and novel_discovery.get("domain")) or analysis.get("domain") or "Academic Research"
        date_str = datetime.now().strftime("%B %d, %Y - %H:%M")
        
        story.append(Paragraph(clean_xml_text(title), title_style))
        story.append(Paragraph(f"<b>Paper ID:</b> {clean_xml_text(paper_id)} &nbsp;|&nbsp; <b>Domain:</b> {clean_xml_text(domain)} &nbsp;|&nbsp; <b>Generated:</b> {clean_xml_text(date_str)}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=2, spaceAfter=8))
        
        # 1. Executive Summary (Simplified Breakdown)
        if simplified_summary:
            solves = simplified_summary.get("what_it_solves", {})
            flowchart = solves.get("flowchart", {}) if isinstance(solves.get("flowchart"), dict) else {}
            
            story.append(Paragraph("1. Executive Summary (Simplified Breakdown)", h1_style))
            if solves.get("plain_summary"):
                story.append(Paragraph(clean_xml_text(solves["plain_summary"]), body_style))
                story.append(Spacer(1, 4))
            
            prob_txt = flowchart.get("problem") or solves.get("problem") or "Existing studies and systems in this field encounter constraints that limit accuracy and scalability."
            sol_txt = flowchart.get("solution") or solves.get("solution") or "The authors introduce a dedicated framework to evaluate and overcome these challenges."
            imp_txt = flowchart.get("impact") or solves.get("impact") or "Empirical findings demonstrate measurable advances over previous baselines."
            
            flow_data = [
                [
                    Paragraph("<b>THE PROBLEM</b>", ParagraphStyle('P1', fontName='Helvetica-Bold', fontSize=8, textColor=c_high_text)),
                    Paragraph("<b>THE SOLUTION</b>", ParagraphStyle('P2', fontName='Helvetica-Bold', fontSize=8, textColor=c_accent)),
                    Paragraph("<b>REAL-WORLD IMPACT</b>", ParagraphStyle('P3', fontName='Helvetica-Bold', fontSize=8, textColor=c_green))
                ],
                [
                    Paragraph(clean_xml_text(prob_txt), body_style),
                    Paragraph(clean_xml_text(sol_txt), body_style),
                    Paragraph(clean_xml_text(imp_txt), body_style)
                ]
            ]
            flow_table = Table(flow_data, colWidths=[175, 175, 190])
            flow_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
                ('BOX', (0,0), (-1,-1), 1, c_border),
                ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(flow_table)
            story.append(Spacer(1, 6))
        
        # 2. Explicit Limitations
        explicit = analysis.get("explicit_limitations", [])
        if explicit:
            story.append(Paragraph("2. Author-Stated Explicit Limitations", h1_style))
            for i, item in enumerate(explicit, 1):
                t_text = item.get("title", f"Limitation {i}")
                page_text = item.get("page", "In text")
                story.append(Paragraph(f"<b>2.{i} {clean_xml_text(t_text)}</b> (<i>{clean_xml_text(page_text)}</i>)", h2_style))
                if item.get("quote"):
                    story.append(Paragraph(f"\"{clean_xml_text(item['quote'])}\"", quote_style))
                if item.get("description"):
                    story.append(Paragraph(f"<b>Technical Analysis:</b> {clean_xml_text(item['description'])}", body_style))
                if item.get("literature_comparison"):
                    story.append(Paragraph(f"<b>Practical Meaning:</b> {clean_xml_text(item['literature_comparison'])}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))
        
        # 3. Inferred Limitations
        inferred = analysis.get("inferred_limitations", [])
        if inferred:
            story.append(Paragraph("3. System-Inferred Methodological Vulnerabilities", h1_style))
            for i, item in enumerate(inferred, 1):
                story.append(Paragraph(f"<b>3.{i} {clean_xml_text(item.get('title', f'Vulnerability {i}'))}</b>", h2_style))
                if item.get("description"):
                    story.append(Paragraph(f"<b>Methodological Flaw:</b> {clean_xml_text(item['description'])}", body_style))
                if item.get("reasoning_chain"):
                    chain_str = "<br/>".join([f"&bull; {clean_xml_text(s)}" for s in item.get("reasoning_chain", [])])
                    story.append(Paragraph(f"<b>Deductive Reasoning:</b><br/>{chain_str}", body_style))
                if item.get("literature_comparison"):
                    story.append(Paragraph(f"<b>Literature Perspective:</b> {clean_xml_text(item['literature_comparison'])}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))
        
        # 4. Prioritized Research Gaps
        gaps = analysis.get("research_gaps", [])
        if gaps:
            story.append(Paragraph("4. Prioritized Research Gaps & Proposed Blueprints", h1_style))
            for i, gap in enumerate(gaps, 1):
                p = (gap.get("priority") or "MEDIUM").upper()
                g_title = gap.get("title") or gap.get("description", f"Research Gap {i}")
                story.append(Paragraph(f"<b>4.{i} [{clean_xml_text(p)} PRIORITY] {clean_xml_text(g_title)}</b>", h2_style))
                if gap.get("description") and gap.get("description") != g_title:
                    story.append(Paragraph(f"<b>Problem Formulation:</b> {clean_xml_text(gap['description'])}", body_style))
                if gap.get("impact"):
                    story.append(Paragraph(f"<b>Transformative Impact:</b> {clean_xml_text(gap['impact'])}", body_style))
                if gap.get("evidence"):
                    story.append(Paragraph(f"<b>Evidence from Paper:</b> {clean_xml_text(gap['evidence'])}", body_style))
                if gap.get("cross_literature_gap"):
                    story.append(Paragraph(f"<b>Cross-Literature Frontier:</b> {clean_xml_text(gap['cross_literature_gap'])}", body_style))
                if gap.get("proposed_blueprint"):
                    bp_str = "<br/>".join([f"&bull; {clean_xml_text(s)}" for s in gap.get("proposed_blueprint", [])])
                    story.append(Paragraph(f"<b>Proposed Blueprint:</b><br/>{bp_str}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))
        
        # 5. Novel Breakthrough Discoveries
        disc_source = novel_discovery or analysis.get("novel_discoveries", {})
        all_disc = disc_source.get("all_discoveries", []) if isinstance(disc_source, dict) else []
        if all_disc:
            story.append(Paragraph("5. 'New-to-the-World' Novel Breakthrough Discoveries", h1_style))
            for i, disc in enumerate(all_disc[:6], 1):
                cat = disc.get("category", "Novel Discovery")
                story.append(Paragraph(f"<b>5.{i} [{clean_xml_text(cat)}] {clean_xml_text(disc.get('title', f'Discovery {i}'))}</b>", h2_style))
                if disc.get("the_core_paradigm"):
                    story.append(Paragraph(f"<b>The Paradigm:</b> {clean_xml_text(disc['the_core_paradigm'])}", body_style))
                if disc.get("why_it_is_new"):
                    story.append(Paragraph(f"<b>Why This Is NEW:</b> {clean_xml_text(disc['why_it_is_new'])}", quote_style))
                if disc.get("reasoning_chain"):
                    chain_str = "<br/>".join([f"&bull; {clean_xml_text(s)}" for s in disc.get("reasoning_chain", [])])
                    story.append(Paragraph(f"<b>Deductive Reasoning:</b><br/>{chain_str}", body_style))
                if disc.get("impact"):
                    story.append(Paragraph(f"<b>Impact:</b> {clean_xml_text(disc['impact'])}", body_style))
                if disc.get("actionable_blueprint"):
                    story.append(Paragraph(f"<b>Actionable Blueprint:</b> {clean_xml_text(disc['actionable_blueprint'])}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))
        
        # 6. Actionable Improvements
        improvements = analysis.get("suggested_improvements", [])
        if improvements:
            story.append(Paragraph("6. Actionable Architectural & Methodological Improvements", h1_style))
            for i, imp in enumerate(improvements, 1):
                story.append(Paragraph(f"<b>6.{i} {clean_xml_text(imp.get('title', f'Improvement {i}'))}</b>", h2_style))
                if imp.get("what_to_change"):
                    story.append(Paragraph(f"<b>What to Change:</b> {clean_xml_text(imp['what_to_change'])}", body_style))
                if imp.get("why_it_helps"):
                    story.append(Paragraph(f"<b>Why It Helps:</b> {clean_xml_text(imp['why_it_helps'])}", body_style))
                if imp.get("implementation_steps"):
                    steps_str = "<br/>".join([f"&bull; {clean_xml_text(s)}" for s in imp.get("implementation_steps", [])])
                    story.append(Paragraph(f"<b>Implementation Steps:</b><br/>{steps_str}", body_style))
                if imp.get("expected_benefit"):
                    story.append(Paragraph(f"<b>Expected Benefit:</b> {clean_xml_text(imp['expected_benefit'])}", body_style))
                if imp.get("comparative_baseline"):
                    story.append(Paragraph(f"<b>Comparative Baseline:</b> {clean_xml_text(imp['comparative_baseline'])}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))
        
        # 7. Online Literature Comparison
        comp_obj = comparison or {}
        comp_text = comp_obj.get("comparison_analysis") or analysis.get("comparison_analysis", "")
        similar_papers = comp_obj.get("similar_papers") or analysis.get("similar_papers", [])
        
        if comp_text or similar_papers:
            story.append(Paragraph("7. Online Literature Comparison & SOTA Synthesis", h1_style))
            if comp_text:
                self._render_markdown_to_story(comp_text, story, styles_dict, colors_dict, max_printable_width)
                story.append(Spacer(1, 3))
            
            if similar_papers:
                story.append(Paragraph("<b>Similar Publications Found Online:</b>", h2_style))
                for p in similar_papers[:4]:
                    p_title = clean_xml_text(p.get("title", "Research Paper"))
                    p_src = clean_xml_text(p.get("source", "Online"))
                    p_diff = clean_xml_text(p.get("what_it_covers_that_your_paper_doesnt", "Covers broader comparative baselines."))
                    story.append(Paragraph(f"&bull; <b>{p_title}</b> (<i>{p_src}</i>)<br/>&nbsp;&nbsp;<b>Coverage Difference:</b> {p_diff}", body_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 4))
        
        # 8. Interactive Q&A Sessions (With Full Markdown Table & Header Rendering)
        if qa_history:
            valid_qa = [qa for qa in qa_history if isinstance(qa, dict) and qa.get("question") and qa.get("answer")]
            if valid_qa:
                story.append(Paragraph("8. Interactive Research Q&A Sessions", h1_style))
                for i, qa in enumerate(valid_qa[-6:], 1):
                    q_text = clean_xml_text(qa.get("question", ""))
                    story.append(Paragraph(f"<b>Q{i}: {q_text}</b>", h2_style))
                    raw_answer = qa.get("answer", "")
                    self._render_markdown_to_story(raw_answer, story, styles_dict, colors_dict, max_printable_width)
                    story.append(Spacer(1, 4))
                story.append(Spacer(1, 4))
        
        # Footer
        story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=8, spaceAfter=4))
        story.append(Paragraph("<i>Report generated autonomously by ScrutinAI - Research Gap Finder(Elite Academic Discovery Assistant)</i>", subtitle_style))
        
        # Build PDF Document
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes