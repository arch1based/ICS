#!/usr/bin/env python3
"""Generate ICS Printer Server Guide PDF"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Colors
ICS_BLUE = HexColor('#1A7DC0')
ICS_DARK = HexColor('#1A3A5C')
ICS_LIGHT_BG = HexColor('#EBF4FB')
ICS_BORDER = HexColor('#C5DFF0')
TEXT_DARK = HexColor('#1A1A2E')
TEXT_GRAY = HexColor('#555566')
TABLE_HEADER = HexColor('#1A7DC0')
TABLE_ROW_ALT = HexColor('#F0F7FC')
TABLE_ROW = white
SUCCESS_GREEN = HexColor('#27AE60')
WARNING_ORANGE = HexColor('#E67E22')
CODE_BG = HexColor('#F4F6F8')
CODE_BORDER = HexColor('#D0D8E0')

W, H = A4

# Try to register a Unicode font for Greek support
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'
FONT_ITALIC = 'Helvetica-Oblique'

# Try DejaVu (supports Greek) if available
DEJAVU_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    '/usr/local/share/fonts/DejaVuSans.ttf',
]
DEJAVU_BOLD_PATHS = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
]

for p in DEJAVU_PATHS:
    if os.path.exists(p):
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', p))
            FONT_NAME = 'DejaVu'
        except Exception:
            pass
        break

for p in DEJAVU_BOLD_PATHS:
    if os.path.exists(p):
        try:
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', p))
            FONT_BOLD = 'DejaVu-Bold'
        except Exception:
            pass
        break

# Also try Noto Sans
NOTO_PATHS = [
    '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
    '/usr/share/fonts/noto/NotoSans-Regular.ttf',
]
NOTO_BOLD = [
    '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
    '/usr/share/fonts/noto/NotoSans-Bold.ttf',
]
if FONT_NAME == 'Helvetica':
    for p in NOTO_PATHS:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont('Noto', p))
                FONT_NAME = 'Noto'
            except Exception:
                pass
            break
    for p in NOTO_BOLD:
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont('Noto-Bold', p))
                FONT_BOLD = 'Noto-Bold'
            except Exception:
                pass
            break

print(f"Using fonts: {FONT_NAME} / {FONT_BOLD}")


def make_styles():
    s = getSampleStyleSheet()

    def style(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        'title': style('MyTitle',
            fontName=FONT_BOLD, fontSize=26, textColor=white,
            alignment=TA_CENTER, leading=32, spaceAfter=4),
        'subtitle': style('MySubtitle',
            fontName=FONT_NAME, fontSize=13, textColor=HexColor('#D4EEFF'),
            alignment=TA_CENTER, leading=18, spaceAfter=0),
        'author': style('MyAuthor',
            fontName=FONT_NAME, fontSize=10, textColor=HexColor('#AACCE8'),
            alignment=TA_CENTER, leading=14, spaceAfter=0),
        'h1': style('MyH1',
            fontName=FONT_BOLD, fontSize=16, textColor=white,
            leading=20, spaceBefore=2, spaceAfter=2),
        'h2': style('MyH2',
            fontName=FONT_BOLD, fontSize=13, textColor=ICS_DARK,
            leading=18, spaceBefore=14, spaceAfter=6),
        'h3': style('MyH3',
            fontName=FONT_BOLD, fontSize=11, textColor=ICS_BLUE,
            leading=15, spaceBefore=10, spaceAfter=4),
        'body': style('MyBody',
            fontName=FONT_NAME, fontSize=10, textColor=TEXT_DARK,
            leading=15, spaceBefore=2, spaceAfter=4, alignment=TA_JUSTIFY),
        'body_left': style('MyBodyLeft',
            fontName=FONT_NAME, fontSize=10, textColor=TEXT_DARK,
            leading=15, spaceBefore=2, spaceAfter=4),
        'bullet': style('MyBullet',
            fontName=FONT_NAME, fontSize=10, textColor=TEXT_DARK,
            leading=15, spaceBefore=1, spaceAfter=2, leftIndent=16, bulletIndent=4),
        'caption': style('MyCaption',
            fontName=FONT_NAME, fontSize=8, textColor=TEXT_GRAY,
            alignment=TA_CENTER, leading=11, spaceBefore=2, spaceAfter=6),
        'code': style('MyCode',
            fontName='Courier', fontSize=8.5, textColor=TEXT_DARK,
            leading=12, spaceBefore=4, spaceAfter=4, leftIndent=8),
        'note': style('MyNote',
            fontName=FONT_ITALIC if FONT_ITALIC != FONT_NAME else FONT_NAME,
            fontSize=9, textColor=TEXT_GRAY,
            leading=13, spaceBefore=2, spaceAfter=4, leftIndent=12),
        'table_h': style('TH',
            fontName=FONT_BOLD, fontSize=9.5, textColor=white,
            alignment=TA_CENTER, leading=13),
        'table_c': style('TC',
            fontName=FONT_NAME, fontSize=9.5, textColor=TEXT_DARK,
            alignment=TA_LEFT, leading=13),
        'table_bold': style('TCB',
            fontName=FONT_BOLD, fontSize=9.5, textColor=ICS_DARK,
            alignment=TA_LEFT, leading=13),
        'table_code': style('TCode',
            fontName='Courier', fontSize=9, textColor=ICS_DARK,
            alignment=TA_LEFT, leading=13),
        'footer': style('Footer',
            fontName=FONT_NAME, fontSize=8, textColor=TEXT_GRAY,
            alignment=TA_CENTER, leading=11),
        'toc_item': style('TOCItem',
            fontName=FONT_NAME, fontSize=10, textColor=ICS_DARK,
            leading=18, spaceBefore=1, spaceAfter=1, leftIndent=8),
        'info_box': style('InfoBox',
            fontName=FONT_NAME, fontSize=10, textColor=ICS_DARK,
            leading=15, spaceBefore=2, spaceAfter=2, leftIndent=8),
    }


def header_section(title, st):
    """Blue section header bar"""
    t = Table([[Paragraph(title, st['h1'])]], colWidths=[W - 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ICS_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [4,4,4,4]),
    ]))
    return t


def make_table(headers, rows, st, col_widths=None):
    data = [[Paragraph(h, st['table_h']) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), st['table_c']) if not isinstance(c, Paragraph) else c for c in row])

    if col_widths is None:
        avail = W - 4*cm
        col_widths = [avail / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, ICS_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [TABLE_ROW, TABLE_ROW_ALT]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    t.setStyle(TableStyle(style))
    return t


def code_box(lines, st):
    """Monospace code box"""
    text = '\n'.join(lines)
    t = Table([[Paragraph(text.replace('\n', '<br/>'), st['code'])]],
              colWidths=[W - 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CODE_BG),
        ('BOX', (0,0), (-1,-1), 1, CODE_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    return t


def info_box(text, st, color=ICS_LIGHT_BG, border=ICS_BLUE):
    t = Table([[Paragraph(text, st['info_box'])]], colWidths=[W - 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), color),
        ('LINEAFTER', (0,0), (0,-1), 4, border),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def on_page(canvas, doc):
    """Page header and footer"""
    canvas.saveState()
    # Top bar
    canvas.setFillColor(ICS_BLUE)
    canvas.rect(0, H - 1.2*cm, W, 1.2*cm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont(FONT_BOLD, 9)
    canvas.drawString(2*cm, H - 0.78*cm, "ICS Printer Server")
    canvas.setFont(FONT_NAME, 9)
    canvas.drawRightString(W - 2*cm, H - 0.78*cm, "Οδηγός Εγκατάστασης & Λειτουργίας")

    # Bottom bar
    canvas.setFillColor(ICS_BORDER)
    canvas.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)
    canvas.setFillColor(TEXT_GRAY)
    canvas.setFont(FONT_NAME, 7.5)
    canvas.drawString(2*cm, 0.28*cm, "Πέτρος Αποστολόπουλος | ICS — Καραφύλλης Συστήματα Πληροφορικής | support-ng@ics.gr")
    canvas.drawRightString(W - 2*cm, 0.28*cm, f"Σελίδα {doc.page}")
    canvas.restoreState()


def build():
    out = 'ics-printer-server-guide/ICS_Printer_Server_Οδηγός.pdf'
    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=1.5*cm,
        title='ICS Printer Server — Οδηγός',
        author='Πέτρος Αποστολόπουλος — ICS',
        subject='Cross-Platform Printing Infrastructure',
    )

    st = make_styles()
    story = []

    # ── COVER PAGE ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))

    # Cover title block
    cover_data = [[
        Paragraph("ICS Printer Server", st['title']),
    ]]
    cover_sub = [[
        Paragraph("Cross-Platform Printing Infrastructure", st['subtitle']),
    ]]
    cover_auth = [[
        Paragraph("Ανάπτυξη: Πέτρος Αποστολόπουλος | ICS — Καραφύλλης Συστήματα Πληροφορικής", st['author']),
    ]]
    cover_ver = [[
        Paragraph("Έκδοση 2.0 | Πλατφόρμα: Android / Sunmi | 2026", st['author']),
    ]]

    for data, bg, pad_t, pad_b in [
        (cover_data, ICS_DARK, 32, 12),
        (cover_sub, ICS_BLUE, 10, 10),
        (cover_auth, HexColor('#155A8A'), 12, 8),
        (cover_ver, HexColor('#155A8A'), 4, 16),
    ]:
        t = Table(data, colWidths=[W - 4*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg),
            ('TOPPADDING', (0,0), (-1,-1), pad_t),
            ('BOTTOMPADDING', (0,0), (-1,-1), pad_b),
            ('LEFTPADDING', (0,0), (-1,-1), 20),
            ('RIGHTPADDING', (0,0), (-1,-1), 20),
        ]))
        story.append(t)

    story.append(Spacer(1, 1.2*cm))

    # Feature badges on cover
    badges = [
        ("TCP Raw Sockets", "Πρωτόκολλο"),
        ("Bluetooth SPP", "Σύνδεση"),
        ("Sunmi Cloud API", "Cloud"),
        ("Kiosk Mode", "Android"),
    ]
    badge_data = [[Paragraph(f"<b>{b[0]}</b><br/><font size='8'>{b[1]}</font>", ParagraphStyle('badge',
        fontName=FONT_BOLD, fontSize=10, textColor=white, alignment=TA_CENTER, leading=14)) for b in badges]]
    bt = Table(badge_data, colWidths=[(W-4*cm)/4]*4)
    bt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ICS_BLUE),
        ('GRID', (0,0), (-1,-1), 1, ICS_DARK),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(bt)

    story.append(Spacer(1, 1.5*cm))
    story.append(HRFlowable(width='100%', thickness=2, color=ICS_BLUE))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "Πλήρης Οδηγός Εγκατάστασης, Ρύθμισης & Λειτουργίας",
        ParagraphStyle('coverDesc', fontName=FONT_BOLD, fontSize=13, textColor=ICS_DARK,
                       alignment=TA_CENTER, leading=18)))

    story.append(PageBreak())

    # ── TABLE OF CONTENTS ────────────────────────────────────────────────────
    story.append(header_section("Περιεχόμενα", st))
    story.append(Spacer(1, 0.3*cm))

    toc_items = [
        ("1.", "Τι είναι το ICS Printer Server"),
        ("2.", "Αρχιτεκτονική & Λειτουργία"),
        ("3.", "Εγκατάσταση"),
        ("4.", "Κεντρική Οθόνη (Dashboard)"),
        ("5.", "Προσθήκη Εκτυπωτή"),
        ("6.", "Τύποι Σύνδεσης"),
        ("7.", "Κωδικοποιήσεις Χαρακτήρων"),
        ("8.", "Πίνακας Ενεργών Εκτυπωτών"),
        ("9.", "Ρυθμίσεις & Αδειοδότηση"),
        ("10.", "Ασφάλεια & Hardware-Locked Άδεια"),
        ("11.", "Αντιμετώπιση Προβλημάτων"),
    ]
    for num, title in toc_items:
        row = Table([
            [Paragraph(f"<b>{num}</b>", st['toc_item']),
             Paragraph(title, st['toc_item'])]
        ], colWidths=[1.2*cm, W - 4*cm - 1.2*cm])
        row.setStyle(TableStyle([
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LINEBELOW', (0,0), (-1,-1), 0.3, ICS_BORDER),
        ]))
        story.append(row)

    story.append(PageBreak())

    # ── SECTION 1: OVERVIEW ─────────────────────────────────────────────────
    story.append(header_section("1. Τι είναι το ICS Printer Server", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Το <b>ICS Printer Server</b> είναι ένα ισχυρό middleware που σχεδιάστηκε για την αδιάλειπτη "
        "διαχείριση εκτυπώσεων σε ετερογενή επιχειρηματικά περιβάλλοντα. Δρα ως ενδιάμεσος σταθμός "
        "μεταξύ εφαρμογών (POS, ERP) και φυσικών εκτυπωτών, υποστηρίζοντας πολλαπλά πρωτόκολλα και "
        "τύπους συσκευών σε ένα ενιαίο σύστημα.",
        st['body']))
    story.append(Spacer(1, 0.2*cm))

    story.append(make_table(
        ["Χαρακτηριστικό", "Περιγραφή"],
        [
            ["Gateway Role", "Μεσολαβητής μεταξύ εφαρμογών (POS, ERP) και φυσικών εκτυπωτών"],
            ["Multi-Protocol", "TCP Raw Sockets, Bluetooth, Sunmi Cloud API"],
            ["High Availability", "Background execution χωρίς διακοπή από το λειτουργικό"],
            ["Kiosk Mode", "Πλήρης αφιέρωση συσκευής Android/Sunmi ως Print Server"],
            ["Multi-Printer", "Ταυτόχρονη διαχείριση πολλαπλών εκτυπωτών σε διαφορετικά πρωτόκολλα"],
        ],
        st, col_widths=[5*cm, W - 4*cm - 5*cm]
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("<b>Ιδανικό για:</b>", st['h3']))
    for bullet in [
        "Επιχειρήσεις με POS συστήματα που χρειάζονται αξιόπιστη εκτύπωση",
        "Εστιατόρια, ξενοδοχεία, καταστήματα με πολλαπλές θέσεις εκτύπωσης (κουζίνα, μπαρ, ταμείο)",
        "Οποιοδήποτε περιβάλλον με ετερογενείς εκτυπωτές (δικτυακοί, Bluetooth, Cloud)",
    ]:
        story.append(Paragraph(f"• {bullet}", st['bullet']))

    # ── SECTION 2: ARCHITECTURE ─────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(header_section("2. Αρχιτεκτονική & Λειτουργία", st))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Πώς Λειτουργεί", st['h3']))
    story.append(code_box([
        "┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐",
        "│   POS / ERP     │──TCP──▶ │  ICS Printer Server  │──BT──▶ │ Εκτυπωτής BT   │",
        "│   Application   │         │   (Android/Sunmi)    │──IP──▶ │ Εκτυπωτής LAN  │",
        "└─────────────────┘         │   Port: 9100 (RAW)   │─Cloud▶ │ Sunmi Cloud    │",
        "                            └──────────────────────┘         └─────────────────┘",
    ], st))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Core Architecture", st['h3']))
    story.append(Paragraph(
        "Η αρχιτεκτονική βασίζεται στην αρχή <b>Dependency Injection</b>. Κρίσιμα services "
        "(διαχείριση εκτυπώσεων, τοπική αποθήκευση) αρχικοποιούνται σωστά και είναι διαθέσιμα "
        "παγκοσμίως. Όλα τα κανάλια επικοινωνίας και κλειδιά αποθήκευσης ορίζονται κεντρικά "
        "για πλήρη <b>type-safety</b>, αποφεύγοντας τυπογραφικά λάθη.",
        st['body']))

    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("OS Integration & High Availability", st['h3']))
    story.append(make_table(
        ["Μηχανισμός", "Λειτουργία"],
        [
            ["Background Service", "Τρέχει αδιάλειπτα χωρίς να τερματίζεται από το Android"],
            ["Wakelocks", "Εξαίρεση από Battery Optimization — πάντα ενεργό"],
            ["Startup App", "Αυτόματη εκκίνηση μετά από επανεκκίνηση συσκευής"],
            ["Kiosk Mode", "Η συσκευή αφιερώνεται αποκλειστικά ως Print Server"],
        ],
        st, col_widths=[4.5*cm, W - 4*cm - 4.5*cm]
    ))

    story.append(PageBreak())

    # ── SECTION 3: INSTALLATION ─────────────────────────────────────────────
    story.append(header_section("3. Εγκατάσταση", st))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Απαιτήσεις Συστήματος", st['h3']))
    story.append(make_table(
        ["Απαίτηση", "Λεπτομέρεια"],
        [
            ["Συσκευή", "Android ή Sunmi (συνιστάται)"],
            ["Android Version", "7.0 (API 24) ή νεότερο"],
            ["Δίκτυο", "Σύνδεση στο ίδιο δίκτυο με τους εκτυπωτές / POS"],
            ["Permissions", "Bluetooth, Network, Device Admin"],
        ],
        st, col_widths=[4.5*cm, W - 4*cm - 4.5*cm]
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Βήματα Εγκατάστασης", st['h3']))
    steps = [
        ("1", "Κατεβάστε το αρχείο ICS Printer Server v2.0.zip από το repository"),
        ("2", "Αποσυμπιέστε το αρχείο και εγκαταστήστε το .apk στη συσκευή Android/Sunmi"),
        ("3", "Κατά την πρώτη εκκίνηση, αποδεχτείτε όλα τα ζητούμενα permissions (Bluetooth, Network, Device Admin)"),
        ("4", "Η εφαρμογή θα ρυθμίσει αυτόματα το Kiosk Mode αν δεν είναι ήδη ενεργό"),
        ("5", "Εισάγετε τα στοιχεία αδειοδότησης στις Ρυθμίσεις (ΑΦΜ, License ID, API Key)"),
        ("6", "Προσθέστε τους εκτυπωτές σας μέσω του κουμπιού ➕ στην κεντρική οθόνη"),
    ]
    for num, desc in steps:
        row_t = Table(
            [[Paragraph(f"<b>{num}</b>", ParagraphStyle('snum',
                fontName=FONT_BOLD, fontSize=11, textColor=white, alignment=TA_CENTER, leading=14)),
              Paragraph(desc, st['body_left'])]],
            colWidths=[0.8*cm, W - 4*cm - 0.8*cm]
        )
        row_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), ICS_BLUE),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (0,-1), 4),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, ICS_BORDER),
        ]))
        story.append(row_t)

    # ── SECTION 4: DASHBOARD ────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(header_section("4. Κεντρική Οθόνη (Dashboard)", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Η κεντρική οθόνη παρέχει πλήρη εικόνα του συστήματος σε πραγματικό χρόνο.",
        st['body']))

    story.append(code_box([
        "┌─────────────────────────────────┐",
        "│       ICS Printer Server        │",
        "│   IP: 10.130.10.116             │",
        "│   Ενεργές Θύρες: 9100 (RAW)    │",
        "├─────────────────────────────────┤",
        "│ ✓  Service created              │",
        "│ ●  BT Server: Listening on COM  │",
        "│ ✓  Sunmi Kiosk Mode Configured  │",
        "│ ○  Server ακούει στη θύρα: 9100 │",
        "└─────────────────────────────────┘",
    ], st))

    story.append(make_table(
        ["Πεδίο", "Περιγραφή"],
        [
            ["IP Address", "Η διεύθυνση δικτύου — χρησιμοποιείται από το POS για αποστολή εντολών"],
            ["Ενεργές Θύρες", "Οι θύρες TCP που ακούει ο server (default: 9100)"],
            ["Log Console", "Real-time καταγραφή όλων των events σε πραγματικό χρόνο"],
        ],
        st, col_widths=[4.5*cm, W - 4*cm - 4.5*cm]
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Μηνύματα Log — Τι σημαίνουν", st['h3']))
    story.append(make_table(
        ["Μήνυμα", "Κατάσταση"],
        [
            ["Service created", "Background service εκκίνησε επιτυχώς"],
            ["BT Server: Listening on COM port...", "Bluetooth server ενεργός και αναμένει συνδέσεις"],
            ["Sunmi Kiosk Mode Configured.", "Kiosk Mode ενεργοποιήθηκε επιτυχώς"],
            ["Server ακούει στη θύρα: 9100", "TCP server έτοιμος να δέχεται εντολές εκτύπωσης"],
        ],
        st, col_widths=[6*cm, W - 4*cm - 6*cm]
    ))

    story.append(PageBreak())

    # ── SECTION 5: ADD PRINTER ──────────────────────────────────────────────
    story.append(header_section("5. Προσθήκη Εκτυπωτή", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Πατήστε το κουμπί <b>➕</b> για να προσθέσετε νέο εκτυπωτή στο σύστημα.",
        st['body']))

    story.append(make_table(
        ["Πεδίο", "Παράδειγμα", "Περιγραφή"],
        [
            ["Όνομα", "Κουζίνα, Ταμείο, Μπαρ", "Φιλικό όνομα αναγνώρισης"],
            ["Τύπος Σύνδεσης", "Bluetooth / IP / Cloud", "Πρωτόκολλο επικοινωνίας"],
            ["IP Address ή MAC / SN", "192.168.1.50 ή 00:11:22:33:44:55", "Αναγνωριστικό εκτυπωτή"],
            ["Τοπική Θύρα Ακρόασης", "9100, 9101, 9102", "Μοναδική θύρα ανά εκτυπωτή"],
            ["Greek CP737", "ON / OFF", "Κωδικοποίηση για ελληνικούς χαρακτήρες"],
            ["UTF-8 Mode", "ON / OFF", "Εναλλακτική κωδικοποίηση Unicode"],
        ],
        st, col_widths=[4.2*cm, 4.5*cm, W - 4*cm - 8.7*cm]
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(info_box(
        "Tip: Κάθε εκτυπωτής πρέπει να έχει μοναδική θύρα ακρόασης. "
        "Για πολλαπλούς εκτυπωτές χρησιμοποιήστε π.χ. 9100, 9101, 9102.",
        st, ICS_LIGHT_BG, ICS_BLUE
    ))

    # ── SECTION 6: CONNECTION TYPES ─────────────────────────────────────────
    story.append(Spacer(1, 0.4*cm))
    story.append(header_section("6. Τύποι Σύνδεσης", st))
    story.append(Spacer(1, 0.3*cm))

    for title, color, content in [
        ("Bluetooth (Sunmi Internal)", ICS_BLUE, [
            "Για ενσωματωμένους εκτυπωτές Sunmi ή εξωτερικούς Bluetooth εκτυπωτές.",
            "• Τα δεδομένα κωδικοποιούνται σε Base64 στο επίπεδο της εφαρμογής",
            "• Αποστέλλονται στο native επίπεδο της συσκευής για εκτέλεση",
            "• Αναγνωριστικό: Διεύθυνση MAC (π.χ. 00:11:22:33:44:55)",
        ]),
        ("Network IP (Ethernet / WiFi)", ICS_DARK, [
            "Για δικτυακούς εκτυπωτές συνδεδεμένους μέσω LAN ή WiFi.",
            "• Επικοινωνία μέσω TCP Raw Sockets",
            "• Αναγνωριστικό: IP Address (π.χ. 192.168.1.50)",
            "• Θύρα εκτυπωτή: συνήθως 9100",
        ]),
        ("Sunmi Cloud", HexColor('#1565A0'), [
            "Για απομακρυσμένους εκτυπωτές μέσω του Sunmi Cloud API.",
            "• Δεν απαιτεί τοπική δικτυακή σύνδεση με τον εκτυπωτή",
            "• Αναγνωριστικό: Serial Number (SN) Sunmi συσκευής",
            "• Απαιτεί διαμορφωμένα Sunmi Cloud credentials (App ID + App Key)",
        ]),
    ]:
        block = Table(
            [[Paragraph(f"<b>{title}</b>", ParagraphStyle('connTitle',
                fontName=FONT_BOLD, fontSize=11, textColor=white, leading=15))]] +
            [[Paragraph(line, ParagraphStyle('connItem',
                fontName=FONT_NAME, fontSize=9.5, textColor=white, leading=14,
                leftIndent=0 if not line.startswith('•') else 10))]
             for line in content],
            colWidths=[W - 4*cm]
        )
        block.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), color),
            ('BACKGROUND', (0,1), (-1,-1), HexColor('#E8F4FD')),
            ('TEXTCOLOR', (0,1), (-1,-1), TEXT_DARK),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('BOX', (0,0), (-1,-1), 1, ICS_BORDER),
        ]))
        story.append(block)
        story.append(Spacer(1, 0.25*cm))

    story.append(PageBreak())

    # ── SECTION 7: ENCODINGS ────────────────────────────────────────────────
    story.append(header_section("7. Κωδικοποιήσεις Χαρακτήρων", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Η σωστή κωδικοποίηση είναι κρίσιμη για την ορθή εκτύπωση <b>ελληνικών χαρακτήρων</b>.",
        st['body']))

    story.append(make_table(
        ["Επιλογή", "Χρήση", "Συνιστάται για"],
        [
            ["Greek CP737", "Κωδικοποίηση DOS-Greek", "Εκτυπωτές παλιότερου firmware"],
            ["UTF-8 Mode", "Unicode κωδικοποίηση", "Νεότεροι εκτυπωτές με Unicode"],
        ],
        st, col_widths=[3.5*cm, 5*cm, W - 4*cm - 8.5*cm]
    ))

    story.append(Spacer(1, 0.2*cm))
    story.append(info_box(
        "Σημαντικό: Ενεργοποιήστε μόνο ΕΝΑ από τους δύο τύπους ανά εκτυπωτή. "
        "Λανθασμένη επιλογή εμφανίζει άγνωστους χαρακτήρες αντί για ελληνικά.",
        st, HexColor('#FFF3E0'), WARNING_ORANGE
    ))

    # ── SECTION 8: ROUTING TABLE ────────────────────────────────────────────
    story.append(Spacer(1, 0.4*cm))
    story.append(header_section("8. Πίνακας Ενεργών Εκτυπωτών", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Η κεντρική οθόνη εμφανίζει όλους τους εγγεγραμμένους εκτυπωτές:",
        st['body']))

    story.append(code_box([
        "┌──────────────────────────────────────────────┐",
        "│ ✱  inner                          🖨  🗑      │",
        "│    BLUETOOTH: 00:11:22:33:44:55             │",
        "│    Port: 9100  [CP737]                      │",
        "├──────────────────────────────────────────────┤",
        "│ ☁  cloud                          🖨  🗑      │",
        "│    CLOUD: N411228N00603                     │",
        "│    Port: 9100  [CP737]                      │",
        "└──────────────────────────────────────────────┘",
    ], st))

    story.append(make_table(
        ["Στοιχείο", "Περιγραφή"],
        [
            ["Εικονίδιο πρωτοκόλλου", "✱ Bluetooth, 🌐 Network IP, ☁ Sunmi Cloud"],
            ["Αναγνωριστικό", "MAC address, IP address, ή Serial Number συσκευής"],
            ["Port", "Τοπική θύρα ακρόασης που αντιστοιχεί σε αυτόν τον εκτυπωτή"],
            ["Badge κωδικοποίησης", "CP737 ή UTF-8 — η ενεργή κωδικοποίηση χαρακτήρων"],
            ["🖨 Test Print", "Αποστολή δοκιμαστικής εκτύπωσης για επαλήθευση"],
            ["🗑 Διαγραφή", "Αφαίρεση εκτυπωτή από το σύστημα"],
        ],
        st, col_widths=[5*cm, W - 4*cm - 5*cm]
    ))

    story.append(PageBreak())

    # ── SECTION 9: SETTINGS ─────────────────────────────────────────────────
    story.append(header_section("9. Ρυθμίσεις & Αδειοδότηση", st))
    story.append(Spacer(1, 0.3*cm))

    # Local Server
    story.append(Paragraph("Τοπικός Server (Multi-Port)", st['h3']))
    story.append(code_box([
        "┌────────────────────────────────────┐",
        "│  Τοπικός Server (Multi-Port)        │",
        "│     Ενεργές θύρες: 9100             │",
        "│                        [↺ Restart]  │",
        "└────────────────────────────────────┘",
    ], st))
    story.append(Paragraph(
        "Εμφανίζει τις ενεργές θύρες TCP. Το κουμπί <b>Restart</b> επανεκκινεί "
        "τον server χωρίς κλείσιμο της εφαρμογής.",
        st['body_left']))

    story.append(Spacer(1, 0.3*cm))

    # Cloud Settings
    story.append(Paragraph("Sunmi Cloud Settings", st['h3']))
    story.append(make_table(
        ["Πεδίο", "Περιγραφή"],
        [
            ["App ID", "Το μοναδικό αναγνωριστικό της εφαρμογής (από Sunmi Developer Console)"],
            ["App Key", "Το μυστικό κλειδί πρόσβασης στο Sunmi Cloud API"],
        ],
        st, col_widths=[3.5*cm, W - 4*cm - 3.5*cm]
    ))

    story.append(Spacer(1, 0.3*cm))

    # License
    story.append(Paragraph("Αδειοδότηση (License)", st['h3']))
    story.append(code_box([
        "┌────────────────────────────────────┐",
        "│  ΑΔΕΙΑ ΕΝΕΡΓΗ     Λήξη: 25/2/2027  │",
        "│  Πλάνο: 08008                       │",
        "│  Device ID: 7c6b74b409080568        │",
        "│  ΑΦΜ: 1234567890                    │",
        "│  License ID: st44va                 │",
        "│  API Key: ••••                      │",
        "│                  [↺ Επανέλεγχος]    │",
        "└────────────────────────────────────┘",
    ], st))

    story.append(make_table(
        ["Πεδίο", "Περιγραφή"],
        [
            ["ΑΦΜ", "Το ΑΦΜ της επιχείρησής σας"],
            ["License ID", "Το αναγνωριστικό άδειας που σας δόθηκε από ICS"],
            ["API Key", "Το μυστικό κλειδί αδειοδότησης"],
            ["Device ID", "Αυτόματα από το σύστημα — δεν τροποποιείται χειροκίνητα"],
            ["Επανέλεγχος", "Online επαλήθευση της άδειας με τον server"],
        ],
        st, col_widths=[3.5*cm, W - 4*cm - 3.5*cm]
    ))

    # ── SECTION 10: SECURITY ────────────────────────────────────────────────
    story.append(Spacer(1, 0.4*cm))
    story.append(header_section("10. Ασφάλεια & Hardware-Locked Άδεια", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Το ICS Printer Server υλοποιεί <b>αυστηρό σύστημα αδειοδότησης</b> δεσμευμένο στο hardware. "
        "Κάθε άδεια συνδέεται κρυπτογραφικά με το μοναδικό Device ID της συσκευής, "
        "εξασφαλίζοντας υψηλό επίπεδο ασφάλειας.",
        st['body']))

    story.append(Spacer(1, 0.2*cm))
    story.append(code_box([
        "Στοιχεία Άδειας (ΑΦΜ + License ID + API Key)",
        "              ⬇",
        "   Κρυπτογραφική Δέσμευση (Binding)",
        "              ⬇",
        "   Device ID (μοναδικό αναγνωριστικό συσκευής)",
        "              ⬇",
        "   ✓ Η άδεια λειτουργεί ΜΟΝΟ σε αυτή τη συσκευή",
    ], st))

    story.append(Spacer(1, 0.2*cm))
    story.append(make_table(
        ["Χαρακτηριστικό", "Λεπτομέρεια"],
        [
            ["Hardware-Locked", "Δεσμεύεται κρυπτογραφικά με το Device ID"],
            ["Μη μεταβιβάσιμη", "Δεν μπορεί να χρησιμοποιηθεί σε άλλο hardware"],
            ["Ημερομηνία Λήξης", "Εμφανής στην οθόνη ρυθμίσεων"],
            ["Online Επαλήθευση", "Άμεση επικοινωνία με τον server αδειοδότησης μέσω 'Επανέλεγχος'"],
        ],
        st, col_widths=[4.5*cm, W - 4*cm - 4.5*cm]
    ))

    story.append(PageBreak())

    # ── SECTION 11: TROUBLESHOOTING ─────────────────────────────────────────
    story.append(header_section("11. Αντιμετώπιση Προβλημάτων", st))
    story.append(Spacer(1, 0.3*cm))

    problems = [
        ("Ο Server δεν ξεκινά", [
            "Ελέγξτε ότι δεν υπάρχει άλλη εφαρμογή που χρησιμοποιεί τη θύρα 9100",
            "Πατήστε Restart από τις Ρυθμίσεις → Τοπικός Server",
            "Επανεκκινήστε τη συσκευή και βεβαιωθείτε ότι η εφαρμογή εκκινεί αυτόματα",
        ]),
        ("Δεν εκτυπώνει / Ελληνικοί χαρακτήρες εμφανίζονται λάθος", [
            "Ελέγξτε την κωδικοποίηση του εκτυπωτή (CP737 ή UTF-8)",
            "Δοκιμάστε την άλλη επιλογή αν εμφανίζονται άγνωστοι χαρακτήρες",
            "Χρησιμοποιήστε το Test Print για επαλήθευση",
        ]),
        ("Bluetooth εκτυπωτής δεν βρίσκεται", [
            "Βεβαιωθείτε ότι ο εκτυπωτής είναι paired με τη συσκευή Android",
            "Ελέγξτε ότι το Bluetooth είναι ενεργοποιημένο",
            "Επαληθεύστε τη MAC address στις ρυθμίσεις εκτυπωτή",
        ]),
        ("Sunmi Cloud δεν συνδέεται", [
            "Επαληθεύστε τα App ID και App Key στις ρυθμίσεις",
            "Βεβαιωθείτε ότι η συσκευή έχει πρόσβαση στο internet",
            "Ελέγξτε το SN (Serial Number) του Cloud εκτυπωτή",
        ]),
        ("Άδεια δεν αναγνωρίζεται", [
            "Πατήστε Επανέλεγχος για online επαλήθευση",
            "Επαληθεύστε τα στοιχεία ΑΦΜ, License ID και API Key",
            "Επικοινωνήστε με ICS: support-ng@ics.gr",
        ]),
    ]

    for prob, solutions in problems:
        block_data = [
            [Paragraph(f"<b>⚠ {prob}</b>", ParagraphStyle('probTitle',
                fontName=FONT_BOLD, fontSize=10.5, textColor=white, leading=14))]
        ] + [
            [Paragraph(f"  ▶  {s}", ParagraphStyle('probSol',
                fontName=FONT_NAME, fontSize=9.5, textColor=TEXT_DARK, leading=13, leftIndent=4))]
            for s in solutions
        ]
        bt = Table(block_data, colWidths=[W - 4*cm])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), ICS_DARK),
            ('BACKGROUND', (0,1), (-1,-1), HexColor('#F8FBFD')),
            ('BOX', (0,0), (-1,-1), 1, ICS_BORDER),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(bt)
        story.append(Spacer(1, 0.3*cm))

    # ── TECHNICAL SPECS ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width='100%', thickness=1.5, color=ICS_BLUE))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Τεχνικές Προδιαγραφές", st['h2']))

    story.append(make_table(
        ["Παράμετρος", "Τιμή"],
        [
            ["Default Port", "9100 (TCP RAW)"],
            ["Πρωτόκολλα", "TCP Raw Sockets, Bluetooth SPP, Sunmi Cloud API"],
            ["Πλατφόρμα", "Android 7.0+ / Sunmi OS"],
            ["Κωδικοποιήσεις", "Greek CP737, UTF-8"],
            ["Αρχιτεκτονική", "Dependency Injection, Background Service, Kiosk Mode"],
            ["Αδειοδότηση", "Hardware-Locked (Device ID binding)"],
        ],
        st, col_widths=[4.5*cm, W - 4*cm - 4.5*cm]
    ))

    # ── FOOTER BOX ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    footer_t = Table([[
        Paragraph(
            "<b>ICS — Καραφύλλης Συστήματα Πληροφορικής</b><br/>"
            "Ανάπτυξη: <b>Πέτρος Αποστολόπουλος</b><br/>"
            "ICS Technical Dept. N. Greece<br/>"
            "support-ng@ics.gr",
            ParagraphStyle('footerBox',
                fontName=FONT_NAME, fontSize=9.5, textColor=white,
                leading=15, alignment=TA_CENTER)
        )
    ]], colWidths=[W - 4*cm])
    footer_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ICS_DARK),
        ('TOPPADDING', (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
    ]))
    story.append(footer_t)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF created: {out}")


if __name__ == '__main__':
    build()
