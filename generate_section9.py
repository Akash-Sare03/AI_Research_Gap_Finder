import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import pypdf

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Geometry
        width, height = A4
        margin = 36
        
        # Calculate overall page numbers (starting at page 15 of 16)
        curr_page_num = 14 + self._pageNumber
        overall_total = 14 + total_pages
        
        # Running Top Header
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(margin, height - 26, width - margin, height - 26)
        self.drawString(margin, height - 22, "ScrutinAI — Master Project Documentation & Interview Case Studies")
        self.drawRightString(width - margin, height - 22, "Section 9: Real-World Experiments")

        # Running Bottom Footer
        self.line(margin, 28, width - margin, 28)
        self.drawString(margin, 18, "Master Documentation and Interview Guide for AI Research Gap Finder (ScrutinAI).")
        self.drawRightString(width - margin, 18, f"Page {curr_page_num} of {overall_total}")
        
        self.restoreState()


def create_section9_pdf(output_path="_sec9_temp.pdf"):
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 36 # 0.5 inch
    CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 2,
        bottomMargin=MARGIN + 4
    )

    styles = getSampleStyleSheet()

    # Typography Styles
    sec_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=5
    )

    sub_title_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=14.5,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=6,
        spaceAfter=3
    )

    h3_style = ParagraphStyle(
        'Heading3Style',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.3,
        leading=12.3,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=4,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.1,
        leading=11.0,
        textColor=colors.HexColor('#334155')
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.1,
        leading=11.2,
        textColor=colors.HexColor('#1E293B')
    )

    script_q_style = ParagraphStyle(
        'ScriptQ',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=11.8,
        textColor=colors.HexColor('#0F172A')
    )

    script_a_style = ParagraphStyle(
        'ScriptA',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.1,
        leading=11.2,
        textColor=colors.HexColor('#1E293B')
    )

    def make_box(content_flowables, bg_color='#F8FAFC', border_color='#CBD5E1', left_accent='#2563EB', padding=5):
        t = Table([[content_flowables]], colWidths=[CONTENT_WIDTH])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor(border_color)),
            ('LINELEFT', (0,0), (-1,-1), 3.5, colors.HexColor(left_accent)),
            ('TOPPADDING', (0,0), (-1,-1), padding),
            ('BOTTOMPADDING', (0,0), (-1,-1), padding),
            ('LEFTPADDING', (0,0), (-1,-1), padding + 3),
            ('RIGHTPADDING', (0,0), (-1,-1), padding),
        ]))
        return t

    story = []

    # ==================== PAGE 15: ROAD-tv CASE STUDY ====================
    # Section 9 Header
    story.append(Paragraph("SECTION 9: REAL-WORLD PAPER EXPERIMENTS &amp; INTERVIEW CASE STUDIES", sec_title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=5))

    # Intro Callout Box
    intro_p1 = Paragraph("<b>&ldquo;What specific findings did you get from real research papers you uploaded in your project?&rdquo;</b>", script_q_style)
    intro_p2 = Paragraph("This section provides rigorous, end-to-end evidence from two actual state-of-the-art scientific discovery papers tested inside ScrutinAI, including exact ground-truth extractions (98% confidence) and 5-agent autonomous breakthrough formulations.", callout_style)
    story.append(make_box([intro_p1, Spacer(1, 2), intro_p2], bg_color='#EFF6FF', border_color='#BFDBFE', left_accent='#2563EB', padding=5))
    story.append(Spacer(1, 6))

    # 9.1 Case Study 1: ROAD-tv
    story.append(Paragraph("9.1 Case Study 1: The &ldquo;ROAD-tv&rdquo; Paper (Topological Opportunity Discovery)", sub_title_style))
    road_meta = [
        Paragraph("<b>Paper:</b> <i>ROAD-tv: Research Opportunity Discovery via Topological Data Analysis and Adversarial Multi-LLM Validation</i>", body_style),
        Paragraph("<b>Authors:</b> Basma Afifi, Mervat Abu-Elkheir, Slim Abdennadher (German University in Cairo &amp; GIU, Egypt)", body_style),
        Paragraph("<b>Core Premise:</b> Employs Topological Data Analysis (TDA) on high-dimensional paper embeddings and multi-LLMs to automatically discover uncharted research directions.", body_style)
    ]
    story.append(make_box(road_meta, bg_color='#F8FAFC', border_color='#E2E8F0', left_accent='#64748B', padding=4))
    story.append(Spacer(1, 5))

    # Q1: Research Gaps
    story.append(Paragraph("<b>Question 1 Asked in App:</b> <i>&ldquo;What are the main research gaps that could be explored?&rdquo;</i>", h3_style))
    
    q1_items = [
        Paragraph("<b>🎯 Layer 1 Grounded Extraction (Confidence: 98% | Grounded in Source Excerpts)</b>", ParagraphStyle('GroundedH', parent=body_bold, textColor=colors.HexColor('#065F46'))),
        Spacer(1, 2),
        Paragraph("ScrutinAI proved that research gaps are not just missing keywords, but are rigorously categorized by structural connectivity and empirical evidence density:", body_style),
        Spacer(1, 2),
        Paragraph("<b>1. Structural Gaps (Topologically Disconnected Regions):</b> Identified isolated clusters in high-dimensional literature embedding spaces lacking citation or thematic bridges [Page 2]. These represent untouched interdisciplinary connections.", body_style),
        Paragraph("<b>2. Semantic Gaps (Method-Problem-Application Triads):</b> Unexplored combinatorial novelty where an established method has never been applied to a specific problem within a domain, validated against formal domain ontologies [Page 2].", body_style),
        Paragraph("<b>3. Evidence-Stratified Gaps (Niches vs. Frontiers):</b><br/>"
                  "&bull;&nbsp;<b>Strong Evidence (62.2%):</b> Active research areas where 18 out of 28 identified questions are validated by 3+ recent papers [Page 7]. Immediate, actionable research niches.<br/>"
                  "&bull;&nbsp;<b>Frontier Opportunities (26.7%):</b> Coherent combinations lacking verifiable literature support [Page 7]. High-risk, high-reward speculative research directions.", body_style),
        Paragraph("<b>4. Automated Noise Rejection (11.1%):</b> Filtered out 11.1% of candidate gaps because they were already well-established in current literature [Page 7], preventing false-positive discoveries.", body_style),
        Paragraph("<b>5. Temporal-Thematic Intersections:</b> Addressed technology lag (e.g., Transformers, persistent homology taking years to diffuse into applied disciplines) to discover lagging temporal opportunities [Page 2].", body_style),
    ]
    story.append(make_box(q1_items, bg_color='#ECFDF5', border_color='#A7F3D0', left_accent='#059669', padding=5))
    story.append(Spacer(1, 6))

    # Q2: Novel Insights & Breakthroughs
    story.append(Paragraph("<b>Question 2 Asked in App:</b> <i>&ldquo;What novel insights or patterns can you find?&rdquo;</i>", h3_style))
    
    q2_items = [
        Paragraph("<b>🚀 5-Agent Autonomous Breakthrough Hypotheses (Formulated Beyond Original Paper)</b>", ParagraphStyle('BreakthroughH', parent=body_bold, textColor=colors.HexColor('#5B21B6'))),
        Spacer(1, 2),
        Paragraph("The 5-agent discovery engine analyzed ROAD-tv's methodological limitations and synthesized 4 concrete research breakthroughs:", body_style),
        Spacer(1, 2),
        Paragraph("<b>1. Temporal Topological Persistence (Noise vs. Structure):</b><br/>"
                  "&bull;&nbsp;<i>Problem:</i> Static TDA cannot distinguish transient 6-month conference hype from fundamental research voids.<br/>"
                  "&bull;&nbsp;<i>Breakthrough:</i> Run persistent homology over 1-year sliding windows to compute 'topological lifespan'. Voids persisting 5+ years are verified structural opportunities.", body_style),
        Spacer(1, 2),
        Paragraph("<b>2. Cross-Domain Topological Isomorphism (Analogical Discovery):</b><br/>"
                  "&bull;&nbsp;<i>Problem:</i> Cross-domain keyword search fails across disparate scientific vocabularies.<br/>"
                  "&bull;&nbsp;<i>Breakthrough:</i> Apply Gromov-Hausdorff Distance / Optimal Transport to align topological manifolds across disciplines (e.g., condensed matter physics &rarr; neural network theory) to discover isomorphic gaps.", body_style),
        Spacer(1, 2),
        Paragraph("<b>3. Adversarial Hallucination Topology (Fake vs. Paywalled Papers):</b><br/>"
                  "&bull;&nbsp;<i>Problem:</i> Literature visualizers struggle to distinguish paywalled papers from LLM hallucinations.<br/>"
                  "&bull;&nbsp;<i>Breakthrough:</i> Implemented <i>Local Topological Consistency Score (LTCS)</i>. Authentic citations preserve subgraph manifold stability even when inaccessible, whereas hallucinations collapse under adversarial perturbation.", body_style),
        Spacer(1, 2),
        Paragraph("<b>4. Topological Entropy as a Research Maturity Metric:</b><br/>"
                  "&bull;&nbsp;<i>Problem:</i> Citation counts and h-indexes are scalar lag indicators that fail to forecast phase transitions.<br/>"
                  "&bull;&nbsp;<i>Breakthrough:</i> Compute Kolmogorov-Sinai topological entropy over citation manifolds to detect fields approaching explosive innovation phases.", body_style),
    ]
    story.append(make_box(q2_items, bg_color='#FAF5FF', border_color='#DDD6FE', left_accent='#7C3AED', padding=5))

    # ==================== PAGE 16: ROBIN CASE STUDY & INTERVIEW SCRIPT ====================
    story.append(PageBreak())

    # 9.2 Case Study 2: ROBIN
    story.append(Paragraph("9.2 Case Study 2: The &ldquo;ROBIN&rdquo; Paper (Multi-Agent Discovery)", sub_title_style))
    robin_meta = [
        Paragraph("<b>Paper:</b> <i>ROBIN: A Multi-Agent System for Automating Scientific Discovery</i>", body_style),
        Paragraph("<b>Core Premise:</b> An automated multi-agent framework where LLMs propose and evaluate therapeutic and chemical hypotheses.", body_style)
    ]
    story.append(make_box(robin_meta, bg_color='#F8FAFC', border_color='#E2E8F0', left_accent='#64748B', padding=4))
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>Question Asked in App:</b> <i>&ldquo;What are the explicit and inferred limitations of this research?&rdquo;</i>", h3_style))
    
    robin_items = [
        Paragraph("<b>🔍 Layer 1 Grounded Extraction (Confidence: 98% | Methodological Audit)</b>", ParagraphStyle('AuditH', parent=body_bold, textColor=colors.HexColor('#991B1B'))),
        Spacer(1, 2),
        Paragraph("ScrutinAI audited the authors' prompt engineering and system architecture, extracting 6 critical limitations:", body_style),
        Spacer(1, 2),
        Paragraph("<b>1. Rigid Single-Agent Constraint:</b> Prompt engineering explicitly mandates that candidate solutions must be a 'single agent, not a combination' and bans formulations/delivery methods like liposomes [Page 21]. This artificially constrains discovery in oncology and immunology where combination therapies are essential.", body_style),
        Paragraph("<b>2. Evidence-Over-Novelty Bias:</b> Heavily penalizes high-risk hypotheses by requiring 'robust existing data' [Page 23], skewing the system toward incremental, safe science rather than true transformative breakthroughs.", body_style),
        Paragraph("<b>3. Consensus-Driven Meta-Analysis Bottleneck:</b> Aggregating multiple trajectories into a consensus conclusion [Page 5] risks averaging out high-conviction, non-consensus insights into mediocre conformism.", body_style),
        Paragraph("<b>4. Semantic Drift in Query Generation:</b> LLM literature search queries [Page 20] suffer from vocabulary drift, missing nuanced subfield keywords and starving downstream agents of vital context.", body_style),
        Paragraph("<b>5. Unverified Causal Reasoning Chains:</b> Verifies whether supporting papers exist for candidate drugs, but lacks formal verification for the internal multi-step causal mechanism linking target protein to disease phenotype [Page 21].", body_style),
        Paragraph("<b>6. High Computational Latency &amp; Cost:</b> Running multiple unpruned analytical trajectories produces high cloud API expenses and excessive latency, restricting high-throughput screening [Page 5].", body_style)
    ]
    story.append(make_box(robin_items, bg_color='#FEF2F2', border_color='#FECACA', left_accent='#DC2626', padding=5))
    story.append(Spacer(1, 7))

    # 9.3 Master Interview Script
    story.append(Paragraph("9.3 Master Interview Question &amp; Response Script", sub_title_style))
    
    script_items = [
        Paragraph("<b>🎙️ INTERVIEWER:</b> <i>&ldquo;Can you give a concrete example of a paper you uploaded to ScrutinAI and what unique findings your system produced?&rdquo;</i>", script_q_style),
        Spacer(1, 4),
        HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#CBD5E1'), spaceAfter=4),
        Paragraph("<b>CANDIDATE RESPONSE (Simple, Crisp &amp; Impressive):</b>", ParagraphStyle('RespTag', parent=body_bold, textColor=colors.HexColor('#1E3A8A'))),
        Spacer(1, 3),
        Paragraph("&ldquo;Absolutely. One of the primary papers I tested was <b>ROAD-tv</b>, an academic paper on discovering research opportunities using Topological Data Analysis and Multi-LLMs.", script_a_style),
        Spacer(1, 2),
        Paragraph("When I asked ScrutinAI to extract the main research gaps, it didn't just give a bulleted summary. It retrieved a <b>98% confidence breakdown directly cited from pages 2 and 7</b>: it proved that <b>62.2% of gaps had strong multi-paper evidence</b>, <b>26.7% were unproven frontier opportunities</b>, and it demonstrated how <b>11.1% of candidates were rejected as already saturated</b>.", script_a_style),
        Spacer(1, 2),
        Paragraph("Next, I triggered ScrutinAI's <b>5-Agent Autonomous Discovery Engine</b> on that same paper. The agents identified that ROAD-tv's topological gap detection is static and cannot distinguish transient conference hype from real theoretical voids. In response, our agents autonomously formulated a novel mathematical blueprint: <b>Temporal Topological Persistence</b>, using persistent homology over sliding time windows to track the 'topological lifespan' of research voids.", script_a_style),
        Spacer(1, 2),
        Paragraph("When I tested another paper, <b>ROBIN</b>, our system audited the prompt engineering on page 21 and uncovered a major hidden limitation: ROBIN hard-codes a 'single-agent constraint' that prevents it from discovering combination drug therapies.", script_a_style),
        Spacer(1, 2),
        Paragraph("This proved that ScrutinAI doesn't just read papers&mdash;it acts as an <b>automated peer referee</b> that stress-tests methodologies and generates publishable follow-up hypotheses.&rdquo;", script_a_style),
    ]
    story.append(make_box(script_items, bg_color='#F8FAFC', border_color='#CBD5E1', left_accent='#0F172A', padding=7))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Section 9 PDF generated successfully: {output_path}")

def merge_with_main_pdf(original_pdf="Markdown Live Preview.pdf", section9_pdf="_sec9_temp.pdf", output_pdf="Markdown Live Preview.pdf"):
    # Read original
    reader_orig = pypdf.PdfReader(original_pdf)
    orig_pages = len(reader_orig.pages)
    
    # Read section 9
    reader_sec9 = pypdf.PdfReader(section9_pdf)
    sec9_pages = len(reader_sec9.pages)
    
    print(f"Original pages: {orig_pages}, Section 9 pages: {sec9_pages}")
    
    writer = pypdf.PdfWriter()
    
    # If the original already has >14 pages (e.g. from a prior test merge), keep only the first 14
    target_orig_pages = 14 if orig_pages >= 14 else orig_pages
    for i in range(target_orig_pages):
        writer.add_page(reader_orig.pages[i])
        
    for i in range(sec9_pages):
        writer.add_page(reader_sec9.pages[i])
        
    temp_output = "_merged_temp.pdf"
    with open(temp_output, "wb") as f_out:
        writer.write(f_out)
        
    # Replace original
    os.replace(temp_output, original_pdf)
    print(f"Successfully updated '{output_pdf}'. New total pages: {len(writer.pages)}")

if __name__ == '__main__':
    create_section9_pdf()
    merge_with_main_pdf()
