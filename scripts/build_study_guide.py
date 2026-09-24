"""Render the reviewed, page-delimited study guide with ReportLab."""
from pathlib import Path
import re
from html import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'study-guides/unit-1-us-beginnings.md'
OUTPUT = ROOT / 'output/pdf/unit-1-us-beginnings-study-guide.pdf'
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
for name, filename in [('Body', 'Arial.ttf'), ('BodyBold', 'Arial Bold.ttf'),
                       ('BodyItalic', 'Arial Italic.ttf'), ('BodyBoldItalic', 'Arial Bold Italic.ttf'),
                       ('Display', 'Georgia Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic', boldItalic='BodyBoldItalic')
INK = HexColor('#172534')
ACCENT = HexColor('#244b63')
MUTED = HexColor('#53616b')
RULE = HexColor('#ccd5da')
WIDTH, HEIGHT = 612, 792
LEFT, RIGHT, TOP, BOTTOM = 45, 45, 51, 43
AVAILABLE_WIDTH = WIDTH - LEFT - RIGHT
AVAILABLE_HEIGHT = HEIGHT - TOP - BOTTOM

def inline(text):
    text = text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
    text = escape(text)
    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s)]+)\)',
                  r'<link href="\2" color="#244b63"><u>\1</u></link>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return text

def flowables(section, scale, page_num):
    base = 10.3 if page_num < 23 else 9.5
    styles = {
        'body': ParagraphStyle('body', fontName='Body', fontSize=base*scale,
            leading=(base+2.9)*scale, textColor=INK, spaceAfter=5.5*scale),
        'title': ParagraphStyle('title', fontName='Display', fontSize=22*scale,
            leading=26*scale, textColor=ACCENT, spaceAfter=8*scale),
        'subtitle': ParagraphStyle('subtitle', fontName='Body', fontSize=12.5*scale,
            leading=16*scale, textColor=MUTED, spaceAfter=13*scale),
        'head': ParagraphStyle('head', fontName='BodyBold', fontSize=12*scale,
            leading=15*scale, textColor=ACCENT, spaceBefore=5*scale, spaceAfter=6*scale),
        'small': ParagraphStyle('small', fontName='Body', fontSize=8.5*scale,
            leading=11*scale, textColor=MUTED, spaceBefore=4*scale, spaceAfter=2*scale),
        'cell': ParagraphStyle('cell', fontName='Body', fontSize=(base-.6)*scale,
            leading=(base+2.1)*scale, textColor=INK),
        'th': ParagraphStyle('th', fontName='BodyBold', fontSize=(base-.4)*scale,
            leading=(base+2.1)*scale, textColor=white),
    }
    lines = section.strip().splitlines()
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    rows.append(cells)
                i += 1
            n = len(rows[0])
            if n == 4:
                widths = [74, 149.3, 149.3, 149.4]
                if page_num == 13:
                    widths = [86, 119, 113, 204]
            elif n == 2:
                widths = [166, 356]
                if page_num == 13:
                    widths = [316, 206]
                if page_num == 1:
                    widths = [75, 447]
            elif n == 3:
                widths = [118, 217, 187]
                if page_num == 14:
                    widths = [30, 287, 205]
                if page_num == 23:
                    widths = [92, 192, 238]
            else:
                widths = [AVAILABLE_WIDTH/n]*n
            data = [[Paragraph(inline(cell), styles['th' if r == 0 else 'cell'])
                     for cell in row] for r, row in enumerate(rows)]
            table = Table(data, colWidths=widths, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), ACCENT),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f1f5f7'), white]),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 7*scale),
                ('RIGHTPADDING', (0,0), (-1,-1), 7*scale),
                ('TOPPADDING', (0,0), (-1,-1), 6*scale),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6*scale),
                ('LINEBELOW', (0,0), (-1,0), .5, ACCENT),
                ('LINEBELOW', (0,1), (-1,-1), .3, RULE),
            ]))
            blocks.extend([table, Spacer(1, 9*scale)])
            continue
        if line.startswith('### '):
            key, line = 'head', line[4:]
        elif line.startswith('## '):
            key, line = 'subtitle', line[3:]
        elif line.startswith('# '):
            key, line = 'title', line[2:]
        elif line.startswith('Sources:') or line.startswith('These are original study questions'):
            key = 'small'
        else:
            key = 'body'
            if line.startswith('- '):
                line = '\u2022 ' + line[2:]
        blocks.append(Paragraph(inline(line), styles[key]))
        i += 1
    return blocks

def measure(blocks):
    return sum(b.wrap(AVAILABLE_WIDTH, AVAILABLE_HEIGHT)[1] + b.getSpaceBefore() + b.getSpaceAfter()
               for b in blocks)

def main():
    sections = SOURCE.read_text().split('---PAGE---')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(OUTPUT), pagesize=(WIDTH, HEIGHT), pageCompression=1)
    pdf.setTitle('Unit 1: U.S. Beginnings - Study Guide')
    pdf.setAuthor('Study guide prepared from class worksheets and cited sources')
    report = []
    for number, section in enumerate(sections, 1):
        scale = 1.0
        blocks = flowables(section, scale, number)
        while measure(blocks) > AVAILABLE_HEIGHT and scale > .895:
            scale = round(scale-.005, 3)
            blocks = flowables(section, scale, number)
        used = measure(blocks)
        if used > AVAILABLE_HEIGHT:
            raise ValueError(f'Page {number} too long: {used:.1f} > {AVAILABLE_HEIGHT}')
        title = section.strip().splitlines()[0].lstrip('# ')
        pdf.bookmarkPage(f'page-{number}')
        pdf.addOutlineEntry(title, f'page-{number}', 0, False)
        pdf.setFillColor(MUTED)
        pdf.setFont('BodyBold', 8)
        pdf.drawString(LEFT, HEIGHT-28, 'U.S. BEGINNINGS  /  UNIT 1')
        pdf.setStrokeColor(RULE)
        pdf.line(LEFT, HEIGHT-35, WIDTH-RIGHT, HEIGHT-35)
        y = HEIGHT-TOP
        for block in blocks:
            y -= block.getSpaceBefore()
            _, h = block.wrap(AVAILABLE_WIDTH, AVAILABLE_HEIGHT)
            block.drawOn(pdf, LEFT, y-h)
            y -= h + block.getSpaceAfter()
        pdf.setStrokeColor(RULE)
        pdf.line(LEFT, 31, WIDTH-RIGHT, 31)
        pdf.setFillColor(MUTED)
        pdf.setFont('Body', 8)
        pdf.drawString(LEFT, 19, 'Class-aligned review • September 2026')
        pdf.drawRightString(WIDTH-RIGHT, 19, f'{number} / {len(sections)}')
        pdf.showPage()
        report.append(f'{number:02d}: scale={scale:.3f} used={used:.1f} remaining={AVAILABLE_HEIGHT-used:.1f} | {title}')
    pdf.save()
    qa = ROOT/'tmp/pdfs/layout-report.txt'
    qa.parent.mkdir(parents=True, exist_ok=True)
    qa.write_text('\n'.join(report)+'\n')
    print('\n'.join(report))
    print(OUTPUT)

if __name__ == '__main__':
    main()
