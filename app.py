import streamlit as st
import math
import pandas as pd
import base64
import io
from datetime import datetime

# --- ReportLab Imports ---
# Make sure reportlab and Pillow are in your requirements.txt for deployment
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate, Image, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    # No need for requests or PIL.Image if the logo is not directly embedded from URL
except ImportError:
    st.error("Gerekli 'reportlab' kütüphanesi bulunamadı. Lütfen 'pip install reportlab Pillow' komutunu çalıştırın ve uygulamayı yeniden başlatın.")
    st.stop() # Stop the app if essential library is missing


# --- Font Registration for ReportLab ---
# Ensure FreeSans.ttf and FreeSansBold.ttf are in a 'fonts' subfolder in your app directory.
try:
    pdfmetrics.registerFont(TTFont("FreeSans", "./fonts/FreeSans.ttf"))
    pdfmetrics.registerFont(TTFont("FreeSans-Bold", "./fonts/FreeSansBold.ttf"))
    pdfmetrics.registerFontFamily('FreeSans',
                                  normal='FreeSans',
                                  bold='FreeSans-Bold',
                                  italic='FreeSans', # Fallback to normal if no italic font is available
                                  boldItalic='FreeSans-Bold') # Fallback to bold if no bold-italic font is available
    MAIN_FONT = "FreeSans"
except Exception as e:
    st.warning(f"UYARI: FreeSans fontları yüklenemedi. Lütfen 'FreeSans.ttf' ve 'FreeSansBold.ttf' dosyalarının uygulama dizininizdeki './fonts/' klasöründe olduğundan emin olun. Helvetica kullanılacaktır. Hata: {e}")
    MAIN_FONT = "Helvetica" # Fallback font

# === COMPANY INFORMATION ===
LOGO_URL = "https://drive.google.com/uc?export=download&id=1RD27Gas035iUqe4Ucl3phFwxZPWZPWzn" # Unused in PDF but kept for reference
LINKTREE_URL = "https://linktr.ee/premiumplushome?utm_source=linktree_admin_share"
COMPANY_INFO = {
    "name": "PREMIUM HOME LTD",
    "address": "Iasonos 1, 1082, Nicosia Cyprus",
    "email": "info@premiumpluscy.eu",
    "phone": "+35722584081, +35797550946",
    "website": "www.premiumpluscy.eu",
    "linktree": LINKTREE_URL,
    "company_no": "HE 467707",
    "bank_name": "BANK OF CYPRUS GROUP",
    "bank_address": "12 Esperidon Street 1087 Nicosia",
    "account_name": "SOYKOK PREMIUM HOME LTD",
    "iban": "CY27 0020 0195 0000 3570 4239 2044",
    "account_number": "357042392044",
    "currency_type": "EURO",
    "swift_bic": "BCYPCY2N"
}

# === PRICE DEFINITIONS ===
FIYATLAR = {
    # Steel Profile Prices (per 6m piece)
    "steel_profile_100x100x3": 45.00,
    "steel_profile_100x50x3": 33.00,
    "steel_profile_40x60x2": 14.00,
    "steel_profile_50x50x2": 11.00,
    "steel_profile_30x30x2": 8.50,
    "steel_profile_hea160": 155.00,
    # Material Prices (Base)
    "heavy_steel_m2": 400.00,
    "sandwich_panel_m2": 22.00,
    "plywood_piece": 44.44,
    "aluminum_window_piece": 250.00,
    "sliding_glass_door_piece": 300.00,
    "wc_window_piece": 120.00,
    "wc_sliding_door_piece": 150.00,
    "door_piece": 280.00,
    "kitchen_installation_piece": 1500.00,
    "shower_wc_installation_piece": 1000.00,
    "connection_element_m2": 1.50,
    "transportation": 500.00,
    "floor_heating_m2": 50.00, # Base price for floor heating system
    "wc_ceramic_m2_material": 20.00 + (650/45.5), # Material cost per m2
    "wc_ceramic_m2_labor": 20.00, # Labor cost per m2
    "electrical_per_m2": 75.00, # New dynamic price per m2
    "plumbing_per_m2": 75.00, # New dynamic price per m2
    "osb_piece": 12.00, # OSB price per piece (for inner walls)
    "insulation_per_m2": 10.00, # New insulation price per m2
    # Labor Prices
    "welding_labor_m2_standard": 160.00, # Standard welding labor
    "welding_labor_m2_trmontaj": 20.00, # TR Montaj welding labor
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00,
    "plasterboard_labor_m2_avg": 80.00, # Average for inner/outer
    "plywood_flooring_labor_m2": 11.11,
    "door_window_assembly_labor_piece": 50.00,
    # Solar Price (1kW = 1250€)
    "solar_per_kw": 1250.00
}

FIRE_RATE = 0.05
VAT_RATE = 0.19 # Fixed VAT rate

# Financial Overheads (Monthly)
MONTHLY_ACCOUNTING_EXPENSES = 180.00
MONTHLY_OFFICE_RENT = 280.00
ANNUAL_INCOME_TAX_RATE = 0.235 # 23.5%

# OSB panel dimensions for area calculation (approx)
OSB_PANEL_AREA_M2 = 1.22 * 2.44 # Standard 4x8 ft panel in m2 (~2.9768 m2)

# === MATERIAL LISTS FOR PROPOSAL PDF ===
ELECTRICAL_MATERIALS_EN = """
• Electrical Cables (3x2.5 mm², 3x1.5 mm²)
• Conduits and Pipes for Cabling
• Junction Boxes
• Distribution Board (Fuse Box)
• Circuit Breakers & Residual Current Device (RCD)
• Sockets and Switches
• Interior Lighting Fixtures (LED Spots / Ceiling Lamp)
• Grounding System Components
"""
ELECTRICAL_MATERIALS_GR = """
• Ηλεκτρικά Καλώδια (3x2.5 mm², 3x1.5 mm²)
• Σωλήνες & Κανάλια για Καλωδίωση
• Κουτιά Διακλάδωσης
• Πίνακας Ασφαλειών
• Ασφάλειες & Ρελέ Διαρροής
• Πρίζες & Διακόπτες
• Εσωτερικά Φωτιστικά (LED Σποτ / Φωτιστικό Οροφής)
• Σύστημα Γείωσης
"""
ELECTRICAL_MATERIALS_TR = """
• Elektrik Kabloları (3x2.5 mm², 3x1.5 mm²)
• Kablolama için Spiral Borular ve Kanallar
• Buatlar
• Sigorta Kutusu (Dağıtım Panosu)
• Sigortalar & Kaçak Akım Rölesi
• Prizler ve Anahtarlar
• İç Aydınlatma Armatürleri (LED Spot / Tavan Lambası)
• Topraklama Sistemi Bileşenleri
"""

PLUMBING_MATERIALS_EN = """
<b>Clean Water System:</b>
• PPRC Pipes for Hot/Cold Water
• Kitchen and Bathroom Faucets
• Shower Head and Mixer
• Main and intermediate valves
<b>Wastewater System:</b>
• PVC Pipes (50mm / 100mm)
• Siphons and floor drains
"""
PLUMBING_MATERIALS_GR = """
<b>Σύστημα Καθαρού Νερού:</b>
• Σωλήνες PPRC για Ζεστό/Κρύο Νερό
• Μπαταρίες Κουζίνας και Μπάνιου
• Κεφαλή Ντους και Μπαταρία
• Κύριες και ενδιάμεσες βάνες
<b>Σύστημα Ακάθαρτου Νερού:</b>
• Σωλήνες PVC (50mm / 100mm)
• Σιφώνια και σχάρες δαπέδου
"""
PLUMBING_MATERIALS_TR = """
<b>Temiz Su Tesisatı:</b>
• Sıcak/Soğuk Su için PPRC Borular
• Mutfak ve Banyo Bataryaları
• Duş Başlığı ve Bataryası
• Ana ve ara kesme vanaları
<b>Atık Su Tesisatı:</b>
• PVC Gider Boruları (50mm / 100mm)
• Sifonlar ve yer süzgeçleri
"""

# New: Floor Heating Materials List
FLOOR_HEATING_MATERIALS_EN = """
• Nano Heat Paint
• 48V 2000W Transformer
• Thermostat Control Unit
• Wiring and Connection Terminals
• Insulation Layers
• Subfloor Preparation Materials
"""

FLOOR_HEATING_MATERIALS_GR = """
• Νάνο Θερμική Βαφή
• Μετασχηματιστής 48V 2000W
• Μονάδα Ελέγχου Θερμοστάτη
• Καλωδίωση και Τερματικά Σύνδεσης
• Στρώσεις Μόνωσης
• Υλικά Προετοιμασίας Υποδαπέδου
"""

FLOOR_HEATING_MATERIALS_TR = """
• Nano Isı Boyası
• 48V 2000W Trafo
• Termostat Kontrol Ünitesi
• Kablolama ve Bağlantı Terminalleri
• Yalıtım Katmanları
• Zemin Hazırlık Malzemeleri
"""
# New: Kitchen Materials List - Corrected to separate EN and GR/TR
KITCHEN_MATERIALS_EN = """
Standard materials include:
• Glossy White Color MDF Material
• Special Production Kitchen Cabinets (custom dimensions)
• Countertop (Laminate or specified equivalent)
• Sink and Faucet
Note: Final material selection and detailed list will be provided upon design approval.
"""
KITCHEN_MATERIALS_GR = """
Τυπικά υλικά περιλαμβάνουν:
• Υλικό MDF Γυαλιστερό Λευκό Χρώμα
• Ειδικές Κατασκευές Ντουλαπιών Κουζίνας (προσαρμοσμένες διαστάσεις)
• Πάγκος (Laminate ή καθορισμένο ισοδύναμο)
• Νεροχύτης και Βρύση
Σημείωση: Η τελική επιλογή υλικών και η λεπτομερής λίστα θα παρασχεθούν μετά την έγκριση του σχεδιασμού.
"""
KITCHEN_MATERIALS_TR = """
Standart malzemeler:
• Parlak Beyaz Renk MDF Malzeme
• Özel Üretim Mutfak Dolapları (özel ölçülerde)
• Tezgah (Laminat veya belirtilen eşdeğeri)
• Evye ve Batarya
Not: Malzeme seçimi sonrası nihai ve detaylı liste tasarım onayı ile birlikte sunulacaktır.
"""

# New: Shower/WC Materials
SHOWER_WC_MATERIALS_EN = """
• Shower Unit (Shower Head & Mixer)
• Toilet Bowl & Cistern
• Washbasin & Faucet
• Towel Rail
• Mirror
• Bathroom Accessories
"""
SHOWER_WC_MATERIALS_GR = """
• Μονάδα Ντους (Κεφαλή Ντους & Μπαταρία)
• Λεκάνη Τουαλέτας & Καζανάκι
• Νιπτήρας & Μπαταρία
• Πετσετοθήκη
• Καθρέφτης
• Αξεσουάρ Μπάνιου
"""
SHOWER_WC_MATERIALS_TR = """
• Duş Ünitesi (Duş Başlığı ve Batarya)
• Klozet & Rezervuar
• El Yıkama Lavabosu & Batarya
• Havluluk
• Ayna
• Banyo Aksesuarları
"""

# === CALCULATION FUNCTIONS ===
def calculate_area(width, length, height):
    """Calculates floor, wall, and roof areas based on dimensions."""
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Formats a monetary value as Euro currency."""
    return f"€{value:,.2f}"

def calculate_rounded_up_cost(value):
    """Rounds up a monetary value to two decimal places."""
    return math.ceil(value * 100) / 100.0

# --- PDF creation helper functions ---

def draw_footer_with_signatures(canvas, doc, customer_name, company_name):
    """Draws the standard footer with company info and signature lines for PDFs."""
    footer_text = f"{COMPANY_INFO['address']} | {COMPANY_INFO['email']} | {COMPANY_INFO['phone']} | {COMPANY_INFO['website']}"
    canvas.setFont(f"{MAIN_FONT}", 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 18*mm, footer_text)
    catalog_text = f"Catalog: {COMPANY_INFO['linktree']}"
    canvas.setFont(MAIN_FONT, 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 14*mm, catalog_text)
    page_num = canvas.getPageNumber()
    canvas.setFont(MAIN_FONT, 8)
    canvas.drawRightString(doc.width + doc.leftMargin, 10*mm, f"Page {page_num}")

    # Signature lines
    y_pos_signatures = 35 * mm
    line_length = 70 * mm
    canvas.line(doc.leftMargin, y_pos_signatures, doc.leftMargin + line_length, y_pos_signatures)
    canvas.setFont(MAIN_FONT, 7)
    canvas.drawCentredString(doc.leftMargin + line_length / 2, y_pos_signatures - 4*mm, f"Buyer / {customer_name.upper()}")
    canvas.line(doc.width + doc.leftMargin - line_length, y_pos_signatures, doc.width + doc.leftMargin, y_pos_signatures)
    canvas.setFont(MAIN_FONT, 7)
    canvas.drawCentredString(doc.width + doc.leftMargin - line_length / 2, y_pos_signatures - 4*mm, f"Seller / {company_name.upper()}")

def _header_footer_for_proposal(canvas, doc):
    """Callback for drawing header/footer on proposal pages."""
    draw_footer_with_signatures(canvas, doc, doc.customer_name, doc.company_name)

def _contract_header_footer_for_contract(canvas, doc):
    """Callback for drawing header/footer on contract pages (simplified signatures)."""
    # Only draw page number and company info for contract footer, signatures are in main flow
    footer_text = f"{COMPANY_INFO['address']} | {COMPANY_INFO['email']} | {COMPANY_INFO['phone']} | {COMPANY_INFO['website']}"
    canvas.setFont(f"{MAIN_FONT}", 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 18*mm, footer_text)
    catalog_text = f"Catalog: {COMPANY_INFO['linktree']}"
    canvas.setFont(MAIN_FONT, 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 14*mm, catalog_text)
    
    page_num = canvas.getPageNumber()
    canvas.setFont(MAIN_FONT, 8)
    canvas.drawRightString(doc.width + doc.leftMargin, 10*mm, f"Page {page_num}")

def _create_solar_appendix_elements_en_gr(solar_kw, solar_price, heading_style, normal_bilingual_style, price_total_style):
    """Generates elements for Solar Energy System appendix (English-Greek)."""
    elements = [
        PageBreak(),
        Paragraph("APPENDIX B: SOLAR ENERGY SYSTEM / ΠΑΡΑΡΤΗΜΑ Β: ΣΥΣΤΗΜΑ ΗΛΙΑΚΗΣ ΕΝΕΡΓΕΙΑΣ", heading_style),
        Spacer(1, 8*mm),
        Paragraph(f"Below are the details for the included <b>{solar_kw} kW</b> Solar Energy System. The price for this system is handled separately from the main house payment plan.<br/><br/>Ακολουθούν οι λεπτομέρειες για το συμπεριλαμβανόμενο Σύστημα Ηλιακής Ενέργειας <b>{solar_kw} kW</b>. Η τιμή για αυτό το σύστημα διαχειρίζεται ξεχωριστά από το πρόγραμμα πληρωμών του κυρίως σπιτιού.", normal_bilingual_style),
        Spacer(1, 8*mm),
    ]
    solar_materials = [
        ["<b>Component / Εξάρτημα</b>", "<b>Description / Περιγραφή</b>"],
        ["Solar Panels / Ηλιακοί Συλλέκτες", f"{solar_kw} kW High-Efficiency Monocrystalline Panels"],
        ["Inverter / Μετατροπέας", "Hybrid Inverter with Grid-Tie Capability"],
        ["Batteries / Μπαταρίες", "Lithium-Ion Battery Storage System (optional, priced separately)"],
        ["Mounting System / Σύστημα Στήριξης", "Certified mounting structure for roof installation"],
        ["Cabling & Connectors / Καλωδίωση & Συνδέσεις", "All necessary DC/AC cables, MC4 connectors, and safety switches"],
        ["Installation & Commissioning / Εγκατάσταση & Θέση σε Λειτουργία", "Full professional installation and system commissioning"],
    ]
    solar_materials_p = [[Paragraph(cell, normal_bilingual_style) for cell in row] for row in solar_materials]
    solar_table = Table(solar_materials_p, colWidths=[60*mm, 110*mm])
    solar_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(solar_table)
    elements.append(Spacer(1, 12*mm))
    elements.append(Paragraph("Total Price (Solar System) / Συνολική Τιμή (Ηλιακό Σύστημα)", heading_style))
    elements.append(Paragraph(format_currency(solar_price), price_total_style))
    return elements

def _create_solar_appendix_elements_tr(solar_kw, solar_price, heading_style, normal_tr_style, price_total_style):
    """Generates elements for Solar Energy System appendix (Turkish)."""
    elements = [
        PageBreak(),
        Paragraph("EK B: GÜNEŞ ENERJİ SİSTEMİ", heading_style),
        Spacer(1, 8*mm),
        Paragraph(f"Projeye dahil edilen <b>{solar_kw} kW</b> Güneş Enerji Sistemi'nin detayları aşağıdadır. Bu sistemin bedeli, ana ev ödeme planından ayrı olarak faturalandırılacaktır.", normal_tr_style),
        Spacer(1, 8*mm),
    ]
    solar_materials = [
        ["<b>Bileşen</b>", "<b>Açıklama</b>"],
        ["Güneş Panelleri", f"{solar_kw} kW Yüksek Verimli Monokristal Panel"],
        ["Inverter (Çevirici)", "Hibrit Inverter (Şebeke Bağlantı Özellikli)"],
        ["Bataryalar", "Lityum-İyon Batarya Depolama Sistemi (opsiyonel, ayrı fiyatlandırılır)"],
        ["Montaj Sistemi", "Çatı kurulumu için sertifikalı montaj yapısı"],
        ["Kablolama & Konnektörler", "Tüm gerekli DC/AC kablolar, MC4 konnektörler ve güvenlik şalterleri"],
        ["Kurulum & Devreye Alma", "Tam profesyonel kurulum ve sistemin devreye alınması"],
    ]
    solar_materials_p = [[Paragraph(cell, normal_tr_style) for cell in row] for row in solar_materials]
    solar_table = Table(solar_materials_p, colWidths=[60*mm, 110*mm])
    solar_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(solar_table)
    elements.append(Spacer(1, 12*mm))
    elements.append(Paragraph("Toplam Fiyat (Güneş Enerji Sistemi)", heading_style))
    elements.append(Paragraph(format_currency(solar_price), price_total_style))
    return elements


def _create_heating_appendix_elements_en_gr(styles):
    """Generates elements for Floor Heating System appendix (English-Greek)."""
    heading_style = styles['Heading']
    normal_bilingual_style = styles['NormalBilingual']
    elements = [
        PageBreak(),
        Paragraph("APPENDIX C: FLOOR HEATING SYSTEM / ΠΑΡΑΡΤΗΜΑ Γ: ΣΥΣΤΗΜΑ ΕΝΔΟΔΑΠΕΔΙΑΣ ΘΕΡΜΑΝΣΗΣ", heading_style),
        Spacer(1, 8*mm),
        Paragraph("Below are the standard materials included in the Floor Heating System:<br/><br/>Ακολουθούν τα στάνταρ υλικά που περιλαμβάνονται στο Σύστημα Ενδοδαπέδιας Θέρμανσης:", normal_bilingual_style),
        Spacer(1, 4*mm),
    ]
    # Split strings to get individual lines for table
    heating_materials_en_lines = FLOOR_HEATING_MATERIALS_EN.strip().split('\n')
    heating_materials_gr_lines = FLOOR_HEATING_MATERIALS_GR.strip().split('\n')
    
    heating_materials = [
        ["<b>Component / Εξάρτημα</b>", "<b>Description / Περιγραφή</b>"],
        ["Heating Elements / Στοιχεία Θέρμανσης", heating_materials_en_lines[0].strip() + " / " + heating_materials_gr_lines[0].strip()],
        ["Transformer / Μετατροπέας", heating_materials_en_lines[1].strip() + " / " + heating_materials_gr_lines[1].strip()],
        ["Thermostat / Θερμοστάτης", heating_materials_en_lines[2].strip() + " / " + heating_materials_gr_lines[2].strip()],
        ["Wiring / Καλωδίωση", heating_materials_en_lines[3].strip() + " / " + heating_materials_gr_lines[3].strip()],
        ["Insulation / Μόνωση", heating_materials_en_lines[4].strip() + " / " + heating_materials_gr_lines[4].strip()],
        ["Subfloor Materials / Υλικά Υποδαπέδου", heating_materials_en_lines[5].strip() + " / " + heating_materials_gr_lines[5].strip()],
    ]
    heating_table_p = [[Paragraph(cell, normal_bilingual_style) for cell in row] for row in heating_materials]
    heating_table = Table(heating_table_p, colWidths=[70*mm, 100*mm])
    heating_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(heating_table)
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("Note: Final material selection and detailed specifications will be confirmed during the design phase based on specific project requirements.<br/><br/>Σημείωση: Η τελική επιλογή υλικών και οι λεπτομερείς προδιαγραφές θα επιβεβαιωθούν κατά τη φάση του σχεδιασμού με βάση τις συγκεκριμένες απαιτήσεις του έργου.", normal_bilingual_style))
    return elements

def _create_heating_appendix_elements_tr(styles):
    """Generates elements for Floor Heating System appendix (Turkish)."""
    heading_style = styles['Heading']
    normal_tr_style = styles['NormalTR']
    elements = [
        PageBreak(),
        Paragraph("EK C: YERDEN ISITMA SİSTEMİ", heading_style),
        Spacer(1, 8*mm),
        Paragraph("Yerden Isıtma Sistemi'ne dahil olan standart malzemeler aşağıdadır:", normal_tr_style),
        Spacer(1, 4*mm),
    ]
    # Split string to get individual lines for table
    heating_materials_tr_lines = FLOOR_HEATING_MATERIALS_TR.strip().split('\n')

    heating_materials = [
        ["<b>Bileşen</b>", "<b>Açıklama</b>"],
        ["Isıtma Elemanları", heating_materials_tr_lines[0].strip()],
        ["Trafo", heating_materials_tr_lines[1].strip()],
        ["Termostat", heating_materials_tr_lines[2].strip()],
        ["Kablolama", heating_materials_tr_lines[3].strip()],
        ["Yalıtım Katmanları", heating_materials_tr_lines[4].strip()],
        ["Zemin Hazırlık Malzemeleri", heating_materials_tr_lines[5].strip()],
    ]
    heating_table_p = [[Paragraph(cell, normal_tr_style) for cell in row] for row in heating_materials]
    heating_table = Table(heating_table_p, colWidths=[70*mm, 100*mm])
    heating_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(heating_table)
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("Not: Malzeme seçimi sonrası nihai ve detaylı spesifikasyonlar, proje gereksinimlerine göre tasarım aşamasında teyit edilecektir.", normal_tr_style))
    return elements


def create_customer_proposal_pdf(house_price, solar_price, total_price, project_details, notes, customer_info):
    """Creates a professional proposal PDF for the customer (English and Greek)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=25*mm,
        bottomMargin=25*mm
    )

    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']

    doc.onFirstPage = _header_footer_for_proposal
    doc.onLaterPages = _header_footer_for_proposal

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='NormalBilingual', parent=styles['Normal'], fontSize=8, leading=10, # Font size 8pt, leading 10pt
        spaceAfter=2, fontName=MAIN_FONT
    ))
    styles.add(ParagraphStyle(
        name='Heading', parent=styles['Heading2'], fontSize=11, spaceAfter=5, spaceBefore=10,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='PriceTotal', parent=styles['Heading1'], fontSize=21, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#c53030")
    ))

    title_style = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=17, alignment=TA_CENTER, # Font size 17pt
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, # Font size 10pt
        spaceAfter=7, fontName=MAIN_FONT, textColor=colors.HexColor("#4a5568")
    )
    
    payment_heading_style = ParagraphStyle(
        name='PaymentHeading', parent=styles['Heading3'], fontSize=9, spaceAfter=3, # Font size 9pt
        spaceBefore=7, fontName=f"{MAIN_FONT}-Bold"
    )
    signature_style = ParagraphStyle(
        name='Signature', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT, # Font size 8pt
        alignment=TA_CENTER, leading=10
    )
    
    # New style for single-color table headers
    colored_table_header_style = ParagraphStyle(
        name='ColoredTableHeader', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold", # Font size 8pt
        textColor=colors.white, alignment=TA_LEFT
    )

    elements = []

    # --- Cover Page ---
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("PREFABRICATED HOUSE PROPOSAL", title_style))
    elements.append(Paragraph("ΠΡΟΤΑΣΗ ΠΡΟΚΑΤΑΣΚΕΥΑΣΜΕΝΟΥ ΣΠΙΤΙΟΥ", title_style))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph(f"For / Για: {customer_info['name']}", subtitle_style))
    if customer_info['company']:
        elements.append(Paragraph(f"Company / Εταιρεία: {customer_info['company']}", subtitle_style))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"Date / Ημερομηνία: {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(PageBreak())

    # --- Customer, Project, and Specs on one page ---
    elements.append(Paragraph("CUSTOMER & PROJECT INFORMATION / ΠΛΗΡΟΦΟΡΙΕΣ ΠΕΛΑΤΗ & ΕΡΓΟΥ", styles['Heading'])) # Use defined 'Heading'
    customer_project_data = [
        [Paragraph("<b>Name / Όνομα:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['name']}", styles['NormalBilingual'])],
        [Paragraph("<b>Company / Εταιρεία:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['company'] or ''}", styles['NormalBilingual'])],
        [Paragraph("<b>Address / Διεύθυνση:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['address'] or ''}", styles['NormalBilingual'])],
        [Paragraph("<b>Phone / Τηλέφωνο:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['phone'] or ''}", styles['NormalBilingual'])],
        [Paragraph("<b>ID/Passport No / Αρ. Ταυτότητας/Διαβατηρίου:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['id_no'] or ''}", styles['NormalBilingual'])],
    ]
    info_table = Table(customer_project_data, colWidths=[65*mm, 105*mm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(info_table)

    elements.append(Spacer(1, 8*mm))

    # --- Technical Specifications Table ---
    elements.append(Paragraph("TECHNICAL SPECIFICATIONS / ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", styles['Heading'])) # Use defined 'Heading'
    
    def get_yes_no(value):
        return 'Yes / Ναι' if value else 'No / Όχι'
    
    def get_yes_no_empty(value): # For cases where 'No' should be empty string
        return 'Yes / Ναι' if value else ''

    # Building structure details (dynamic based on type)
    building_structure_details_en_gr = ""
    if project_details['structure_type'] == 'Light Steel':
        building_structure_details_en_gr = """
        <b>Building structure details:</b><br/>
        Skeleton: Box profile with dimensions of 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm will be used. (Optional dimensions can be changed) Antirust will be applied to all box profiles and can be painted with the desired color. All our profile welding works have EN3834 certification in accordance with European standards. The construction operations of the entire building are subject to European standards and EN 1090-1 Light Steel Construction license inspection.
        """
    else: # Heavy Steel
        building_structure_details_en_gr = """
        <b>Building structure details:</b><br/>
        Skeleton: Steel house frame with all necessary cross-sections (columns, beams), including connection components (flanges, screws, bolts), all as static drawings.<br/>
        HEA120 OR HEA160 Heavy metal will be used in models with title deed and construction permit. All non-galvanized metal surfaces will be sandblasted according to the Swedish standard Sa 2.5 and will be coated with a zincphosphate primer 80μm thick.<br/>
        Anti-rust will be applied to all profiles and can be painted in the desired color.<br/>
        All our profile welding works have EN3834 certificate in accordance with European standards. All construction processes of the building are subject to European standards and EN 1090-1 Steel Construction license inspection.
        """
    
    # Corrected plasterboard logic for display
    display_plasterboard_interior = project_details['plasterboard_interior'] and project_details['structure_type'] == 'Light Steel'
    display_plasterboard_all = project_details['plasterboard_all'] and project_details['structure_type'] == 'Heavy Steel'

    spec_data = [
        [Paragraph('<b>Dimension / Διαστάσεις</b>', styles['NormalBilingual']), Paragraph(f"{project_details['width']}m x {project_details['length']}m x {project_details['height']}m ({project_details['area']:.2f} m²)", styles['NormalBilingual'])],
        [Paragraph('<b>Structure / Δομή</b>', styles['NormalBilingual']), Paragraph(f"{project_details['structure_type']} with Sandwich Panel facade & roof.", styles['NormalBilingual'])],
        [Paragraph('<b>Construction Materials / Υλικά Κατασκευής</b>', styles['NormalBilingual']), Paragraph(building_structure_details_en_gr, styles['NormalBilingual'])],
        [Paragraph('<b>Interior / Εσωτερικό</b>', styles['NormalBilingual']), Paragraph(f"Floor Covering: {project_details['floor_covering_type']}. Inner Wall OSB: {get_yes_no_empty(project_details['osb_inner_wall'])}. Interior Walls: Plasterboard {get_yes_no(display_plasterboard_interior or display_plasterboard_all)}", styles['NormalBilingual'])],
        [Paragraph('<b>Insulation / Μόνωση</b>', styles['NormalBilingual']), Paragraph(f"Floor Insulation: {get_yes_no_empty(project_details['insulation_floor'])}. Wall Insulation: {get_yes_no_empty(project_details['insulation_wall'])}.", styles['NormalBilingual'])],
        [Paragraph('<b>Openings / Ανοίγματα</b>', styles['NormalBilingual']), Paragraph(f"Windows: {project_details['window_count']} ({project_details['window_size']} - {project_details['window_door_color']})<br/>Doors: {project_details['door_count']} ({project_details['door_size']} - {project_details['window_door_color']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size']} - {project_details['window_door_color']})<br/>WC Windows: {project_details['wc_window_count']} ({project_details['wc_window_size']} - {project_details['window_door_color']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sliding Doors: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size'] + ' - ' + project_details['window_door_color'] + ')'}", styles['NormalBilingual'])],
        [Paragraph('<b>Kitchen / Κουζίνα</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['kitchen']), styles['NormalBilingual'])],
    ]
    if project_details['kitchen']: # Add kitchen materials note only if kitchen is included
        spec_data.append([Paragraph('<b>Kitchen Materials / Υλικά Κουζίνας</b>', styles['NormalBilingual']), Paragraph(KITCHEN_MATERIALS_EN + "<br/><br/>" + KITCHEN_MATERIALS_GR, styles['NormalBilingual'])])

    spec_data.append([Paragraph('<b>Shower/WC / Ντους/WC</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['shower']), styles['NormalBilingual'])])
    if project_details['shower']: # Add shower/WC materials note only if included
        spec_data.append([Paragraph('<b>Shower/WC Materials / Υλικά Ντους/WC</b>', styles['NormalBilingual']), Paragraph(SHOWER_WC_MATERIALS_EN + "<br/><br/>" + SHOWER_WC_MATERIALS_GR, styles['NormalBilingual'])])


    # Add electrical materials if included, otherwise leave empty
    if project_details['electrical']:
        spec_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph(f"{ELECTRICAL_MATERIALS_EN.strip()}<br/><br/>{ELECTRICAL_MATERIALS_GR.strip()}", styles['NormalBilingual'])])
    else:
        spec_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph('', styles['NormalBilingual'])])

    # Add plumbing materials if included, otherwise leave empty
    if project_details['plumbing']:
        spec_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph(f"{PLUMBING_MATERIALS_EN.strip()}<br/><br/>{PLUMBING_MATERIALS_GR.strip()}", styles['NormalBilingual'])])
    else:
        spec_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph('', styles['NormalBilingual'])])

    # Add optional features only if included
    if project_details['heating']:
        spec_data.append([Paragraph('<b>Floor Heating / Ενδοδαπέδια</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['heating']), styles['NormalBilingual'])])
    if project_details['solar']:
        spec_data.append([Paragraph('<b>Solar System / Ηλιακό Σύστημα</b>', styles['NormalBilingual']), Paragraph(f"{get_yes_no_empty(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '', styles['NormalBilingual'])])
    if project_details['wheeled_trailer_included']:
        spec_data.append([Paragraph('<b>Wheeled Trailer / Τροχοφόρο Ρυμουλκούμενο</b>', styles['NormalBilingual']), Paragraph(f"{get_yes_no_empty(project_details['wheeled_trailer_included'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer_included'] else '', styles['NormalBilingual'])])

    spec_data.append([Paragraph('<b>Estimated Delivery / Εκτιμώμενη Παράδοση</b>', styles['NormalBilingual']), Paragraph(f"Approx. {project_details['delivery_duration_business_days']} business days / Περίπου {project_details['delivery_duration_business_days']} εργάσιμες ημέρες", styles['NormalBilingual'])])

    spec_table = Table(spec_data, colWidths=[60*mm, 110*mm]) # Adjusted first col width for headings
    spec_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f4f4f4")), # Header column background
        ('ALIGN', (0,0), (0,-1), 'LEFT'), # Ensure first column is left aligned
        ('ALIGN', (1,0), (-1,-1), 'LEFT'), # Ensure second column is left aligned
    ]))
    elements.append(spec_table)

    if notes.strip():
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("CUSTOMER NOTES / ΣΗΜΕΙΩΣΕΙΣ ΠΕΛΑΤΗ", styles['Heading'])) # Use defined 'Heading'
        elements.append(Paragraph(notes, styles['NormalBilingual']))

    # --- PRICE & PAYMENT SCHEDULE on a NEW PAGE ---
    elements.append(PageBreak())
    final_page_elements = [Spacer(1, 12*mm)]

    # Use a single-color table for PRICE & PAYMENT SCHEDULE
    final_page_elements.append(Paragraph("PRICE & PAYMENT SCHEDULE / ΤΙΜΗ & ΠΡΟΓΡΑΜΜΑ ΠΛΗΡΩΜΩΝ", styles['Heading'])) # Use defined 'Heading'
    
    price_table_data = []
    price_table_data.append([
        Paragraph("Main House Price / Τιμή Κυρίως Σπιτιού", colored_table_header_style),
        Paragraph(format_currency(house_price), colored_table_header_style)
    ])
    if solar_price > 0:
        price_table_data.append([
            Paragraph("Solar System Price / Τιμή Ηλιακού Συστήματος", colored_table_header_style),
            Paragraph(format_currency(solar_price), colored_table_header_style)
        ])
    price_table_data.append([
        Paragraph("TOTAL PRICE / ΣΥΝΟΛΙΚΗ ΤΙΜΗ", colored_table_header_style),
        Paragraph(format_currency(total_price), colored_table_header_style)
    ])

    price_summary_table = Table(price_table_data, colWidths=[120*mm, 50*mm])
    price_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#3182ce")), # Single color background
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#4a5568")), # Darker grid for contrast
    ]))
    final_page_elements.append(price_summary_table)
    final_page_elements.append(Spacer(1, 8*mm))

    # Estimated Delivery added to Price section
    final_page_elements.append(Paragraph(f"<b>Estimated Delivery / Εκτιμώμενη Παράδοση:</b> Approx. {project_details['delivery_duration_business_days']} business days / Περίπου {project_details['delivery_duration_business_days']} εργάσιμες ημέρες", payment_heading_style))
    final_page_elements.append(Spacer(1, 8*mm))


    final_page_elements.append(Paragraph("Main House Payment Plan / Πρόγραμμα Πληρωμών Κυρίως Σπιτιού", payment_heading_style))

    down_payment = house_price * 0.40
    remaining_balance = house_price - down_payment
    installment_amount = remaining_balance / 3

    payment_data = [
        [Paragraph("1. Down Payment / Προκαταβολή (40%)", payment_heading_style), Paragraph(format_currency(down_payment), payment_heading_style)],
        [Paragraph("   - Due upon contract signing / Με την υπογραφή της σύμβασης.", styles['NormalBilingual']), ""],
        [Paragraph("2. 1st Installment / 1η Δόση", payment_heading_style), Paragraph(format_currency(installment_amount), payment_heading_style)],
        [Paragraph("   - Due upon completion of structure / Με την ολοκλήρωση της κατασκευής.", styles['NormalBilingual']), ""],
        [Paragraph("3. 2nd Installment / 2η Δόση", payment_heading_style), Paragraph(format_currency(installment_amount), payment_heading_style)],
        [Paragraph("   - Due upon completion of interior works / Με την ολοκλήρωση των εσωτερικών εργασιών.", styles['NormalBilingual']), ""],
        [Paragraph("4. Final Payment / Τελική Εξόφληση", payment_heading_style), Paragraph(format_currency(installment_amount), payment_heading_style)],
        [Paragraph("   - Due upon final delivery / Με την τελική παράδοση.", styles['NormalBilingual']), ""],
    ]

    if solar_price > 0:
        payment_data.append([Paragraph("Solar System / Ηλιακό Σύστημα", payment_heading_style), Paragraph(format_currency(solar_price), payment_heading_style)])
        payment_data.append([Paragraph("   - Due upon contract signing / Με την υπογραφή της σύμβασης.", styles['NormalBilingual']), ""])

    payment_table = Table(payment_data, colWidths=[120*mm, 50*mm])
    payment_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    final_page_elements.append(payment_table)
    elements.append(KeepTogether(final_page_elements))

    # Add Solar Appendix if applicable
    if project_details['solar']:
        solar_elements = _create_solar_appendix_elements_en_gr(project_details['solar_kw'], project_details['solar_price'], styles['Heading'], styles['NormalBilingual'], styles['PriceTotal'])
        elements.extend(solar_elements)
    
    # Add Floor Heating Appendix if applicable
    if project_details['heating']:
        heating_elements = _create_heating_appendix_elements_en_gr(styles) # Pass styles dict directly
        elements.extend(heating_elements)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_customer_proposal_pdf_tr(house_price, solar_price, total_price, project_details, notes, customer_info):
    """Creates a professional proposal PDF for the customer (Turkish)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=25*mm,
        bottomMargin=25*mm
    )

    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']

    doc.onFirstPage = _header_footer_for_proposal
    doc.onLaterPages = _header_footer_for_proposal

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='NormalTR', parent=styles['Normal'], fontSize=8, leading=10, # Font size 8pt, leading 10pt
        spaceAfter=2, fontName=MAIN_FONT
    ))
    # Custom Heading style to pass explicitly
    styles.add(ParagraphStyle(
        name='Heading', parent=styles['Heading2'], fontSize=11, spaceAfter=5, spaceBefore=10,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='PriceTotal', parent=styles['Heading1'], fontSize=21, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#c53030")
    ))

    title_style = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=17, alignment=TA_CENTER, # Font size 17pt
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, # Font size 10pt
        spaceAfter=7, fontName=MAIN_FONT, textColor=colors.HexColor("#4a5568")
    )
    
    payment_heading_style = ParagraphStyle(
        name='PaymentHeading', parent=styles['Heading3'], fontSize=9, spaceAfter=3, # Font size 9pt
        spaceBefore=7, fontName=f"{MAIN_FONT}-Bold"
    )
    signature_style = ParagraphStyle(
        name='Signature', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT, # Font size 8pt
        alignment=TA_CENTER, leading=10
    )

    # New style for single-color table headers (Turkish)
    colored_table_header_style_tr = ParagraphStyle(
        name='ColoredTableHeaderTR', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold", # Font size 8pt
        textColor=colors.white, alignment=TA_LEFT
    )

    elements = []
    # --- Cover Page ---
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("PREFABRİK EV TEKLİFİ", title_style))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph(f"Müşteri: {customer_info['name']}", subtitle_style))
    if customer_info['company']:
        elements.append(Paragraph(f"Firma: {customer_info['company']}", subtitle_style))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(PageBreak())

    # --- Customer, Project, and Specs on one page ---
    elements.append(Paragraph("MÜŞTERİ VE PROJE BİLGİLERİ", styles['Heading'])) # Use defined 'Heading'
    customer_project_data = [
        [Paragraph("<b>Adı Soyadı:</b>", styles['NormalTR']), Paragraph(f"{customer_info['name']}", styles['NormalTR'])],
        [Paragraph("<b>Firma:</b>", styles['NormalTR']), Paragraph(f"{customer_info['company'] or ''}", styles['NormalTR'])], # Changed Yok to empty string
        [Paragraph("<b>Adres:</b>", styles['NormalTR']), Paragraph(f"{customer_info['address'] or ''}", styles['NormalTR'])], # Changed Yok to empty string
        [Paragraph("<b>Telefon:</b>", styles['NormalTR']), Paragraph(f"{customer_info['phone'] or ''}", styles['NormalTR'])], # Changed Yok to empty string
        [Paragraph("<b>Kimlik/Pasaport No:</b>", styles['NormalTR']), Paragraph(f"{customer_info['id_no'] or ''}", styles['NormalTR'])], # Changed Yok to empty string
    ]
    info_table = Table(customer_project_data, colWidths=[65*mm, 105*mm]) # Adjusted colWidths
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(info_table)

    elements.append(Spacer(1, 8*mm))

    # --- Technical Specifications Table ---
    elements.append(Paragraph("TEKNİK ÖZELLİKLER", styles['Heading']))

    def get_var_yok(value):
        return 'Var' if value else 'Yok'
    
    def get_var_yok_empty(value): # For cases where 'Yok' should be empty string
        return 'Var' if value else ''

    # Building structure details (dynamic based on type)
    building_structure_details_tr = ""
    if project_details['structure_type'] == 'Light Steel':
        building_structure_details_tr = """
        <b>Bina yapı detayları:</b><br/>
        İskelet: 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm ölçülerinde kutu profil kullanılacaktır. (İsteğe bağlı ölçüler değiştirilebilir) Tüm kutu profillere pas önleyici uygulanacak ve istenilen renge boyanabilir. Tüm profil kaynak işlerimiz Avrupa standartlarına uygun olarak EN3834 sertifikalıdır. Binanın tüm yapım süreçleri Avrupa standartlarına ve EN 1090-1 Hafif Çelik Yapı ruhsat denetimine tabidir.
        """
    else: # Heavy Steel
        building_structure_details_tr = """
        <b>Bina yapı detayları:</b><br/>
        İskelet: Tüm gerekli kesitlere (kolonlar, kirişler) sahip çelik ev iskeleti, bağlantı elemanları (flanşlar, vidalar, cıvatalar) dahil, hepsi statik çizimlere göre olacaktır.<br/>
        Tapulu ve inşaat ruhsatlı modellerde HEA120 VEYA HEA160 Ağır metal kullanılacaktır. Tüm galvanizli olmayan metal yüzeyler İsveç standardı Sa 2.5'e göre kumlama yapılacak ve 80μm kalınlığında çinko-fosfat astar ile kaplanacaktır.<br/>
        Tüm profillere pas önleyici uygulanacak ve istenilen renge boyanabilir.<br/>
        Tüm profil kaynak işlerimiz Avrupa standartlarına uygun olarak EN3834 sertifikalıdır. Binanın tüm yapım süreçleri Avrupa standartlarına ve EN 1090-1 Çelik Yapı ruhsat denetimine tabidir.
        """
    
    # Corrected plasterboard logic for display
    display_plasterboard_interior = project_details['plasterboard_interior'] and project_details['structure_type'] == 'Light Steel'
    display_plasterboard_all = project_details['plasterboard_all'] and project_details['structure_type'] == 'Heavy Steel'

    spec_data = [
        [Paragraph('<b>Boyutlar</b>', styles['NormalTR']), Paragraph(f"{project_details['width']}m x {project_details['length']}m x {project_details['height']}m ({project_details['area']:.2f} m²)", styles['NormalTR'])],
        [Paragraph('<b>Yapı</b>', styles['NormalTR']), Paragraph(f"{project_details['structure_type']}, Sandviç Panel cephe & çatı.", styles['NormalTR'])],
        [Paragraph('<b>Yapı Malzemeleri</b>', styles['NormalTR']), Paragraph(building_structure_details_tr, styles['NormalTR'])],
        [Paragraph('<b>İç Mekan</b>', styles['NormalTR']), Paragraph(f"Zemin Kaplama: {project_details['floor_covering_type']}. İç Duvar OSB: {get_var_yok_empty(project_details['osb_inner_wall'])}. İç Duvarlar: Alçıpan: {get_var_yok(display_plasterboard_interior or display_plasterboard_all)}", styles['NormalTR'])],
        [Paragraph('<b>Yalıtım</b>', styles['NormalTR']), Paragraph(f"Zemin Yalıtımı: {get_var_yok_empty(project_details['insulation_floor'])}. Duvar Yalıtımı: {get_var_yok_empty(project_details['insulation_wall'])}.", styles['NormalTR'])],
        [Paragraph('<b>Doğramalar</b>', styles['NormalTR']), Paragraph(f"Pencereler: {project_details['window_count']} adet ({project_details['window_size']} - {project_details['window_door_color']})<br/>Kapılar: {project_details['door_count']} adet ({project_details['door_size']} - {project_details['window_door_color']})<br/>Sürme Kapılar: {project_details['sliding_door_count']} adet ({project_details['sliding_door_size']} - {project_details['window_door_color']})<br/>WC Pencereler: {project_details['wc_window_count']} adet ({project_details['wc_window_size']} - {project_details['window_door_color']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sürme Kapılar: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size'] + ' - ' + project_details['window_door_color'] + ')'}", styles['NormalTR'])],
        [Paragraph('<b>Mutfak</b>', styles['NormalTR']), Paragraph(get_var_yok_empty(project_details['kitchen']), styles['NormalTR'])],
    ]
    if project_details['kitchen']: # Add kitchen materials note only if kitchen is included
        spec_data.append([Paragraph('<b>Mutfak Malzemeleri</b>', styles['NormalTR']), Paragraph(KITCHEN_MATERIALS_TR, styles['NormalTR'])])

    spec_data.append([Paragraph('<b>Duş/WC</b>', styles['NormalTR']), Paragraph(get_var_yok_empty(project_details['shower']), styles['NormalTR'])])
    if project_details['shower']: # Add shower/WC materials note only if included
        spec_data.append([Paragraph('<b>Duş/WC Malzemeleri</b>', styles['NormalTR']), Paragraph(SHOWER_WC_MATERIALS_TR, styles['NormalTR'])])


    if project_details['electrical']:
        spec_data.append([Paragraph('<b>Elektrik Tesisatı</b>', styles['NormalTR']), Paragraph(ELECTRICAL_MATERIALS_TR.strip(), styles['NormalTR'])])
    else:
        spec_data.append([Paragraph('<b>Elektrik Tesisatı</b>', styles['NormalTR']), Paragraph('', styles['NormalTR'])])

    if project_details['plumbing']:
        spec_data.append([Paragraph('<b>Sıhhi Tesisat</b>', styles['NormalTR']), Paragraph(PLUMBING_MATERIALS_TR.strip(), styles['NormalTR'])])
    else:
        spec_data.append([Paragraph('<b>Sıhhi Tesisat</b>', styles['NormalTR']), Paragraph('', styles['NormalTR'])])

    # Add optional features only if included
    if project_details['heating']:
        spec_data.append([Paragraph('<b>Yerden Isıtma</b>', styles['NormalTR']), Paragraph(get_var_yok_empty(project_details['heating']), styles['NormalTR'])])
    if project_details['solar']:
        spec_data.append([Paragraph('<b>Güneş Enerjisi</b>', styles['NormalTR']), Paragraph(f"{get_var_yok_empty(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '', styles['NormalTR'])])
    if project_details['wheeled_trailer_included']:
        spec_data.append([Paragraph('<b>Tekerlekli Römork</b>', styles['NormalTR']), Paragraph(f"{get_var_yok_empty(project_details['wheeled_trailer_included'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer_included'] else '', styles['NormalTR'])])

    spec_data.append([Paragraph('<b>Tahmini Teslimat</b>', styles['NormalTR']), Paragraph(f"Yaklaşık {project_details['delivery_duration_business_days']} iş günü", styles['NormalTR'])])

    spec_table = Table(spec_data, colWidths=[60*mm, 110*mm]) # Adjusted first col width for headings
    spec_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f4f4f4")), # Header column background
        ('ALIGN', (0,0), (0,-1), 'LEFT'), # Ensure first column is left aligned
        ('ALIGN', (1,0), (-1,-1), 'LEFT'), # Ensure second column is left aligned
    ]))
    elements.append(spec_table)

    if notes.strip():
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("MÜŞTERİ NOTLARI", styles['Heading'])) # Use defined 'Heading'
        elements.append(Paragraph(notes, styles['NormalTR']))

    # --- PRICE & PAYMENT SCHEDULE on a NEW PAGE ---
    elements.append(PageBreak())
    final_page_elements = [Spacer(1, 12*mm)]

    # Use a single-color table for PRICE & PAYMENT SCHEDULE
    final_page_elements.append(Paragraph("FİYAT VE ÖDEME PLANI", styles['Heading'])) # Use defined 'Heading'

    price_table_data_tr = []
    price_table_data_tr.append([
        Paragraph("Ana Ev Bedeli", colored_table_header_style_tr),
        Paragraph(format_currency(house_price), colored_table_header_style_tr)
    ])
    if solar_price > 0:
        price_table_data_tr.append([
            Paragraph("Güneş Enerji Sistemi Bedeli", colored_table_header_style_tr),
            Paragraph(format_currency(solar_price), colored_table_header_style_tr)
        ])
    price_table_data_tr.append([
        Paragraph("TOPLAM BEDEL", colored_table_header_style_tr),
        Paragraph(format_currency(total_price), colored_table_header_style_tr)
    ])

    price_summary_table_tr = Table(price_table_data_tr, colWidths=[120*mm, 50*mm])
    price_summary_table_tr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#3182ce")), # Single color background
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#4a5568")), # Darker grid for contrast
    ]))
    final_page_elements.append(price_summary_table_tr)
    final_page_elements.append(Spacer(1, 8*mm))

    # Estimated Delivery added to Price section
    final_page_elements.append(Paragraph(f"<b>Tahmini Teslimat:</b> Yaklaşık {project_details['delivery_duration_business_days']} iş günü", payment_heading_style))
    final_page_elements.append(Spacer(1, 8*mm))


    final_page_elements.append(Paragraph("Ana Ev Ödeme Planı", payment_heading_style))

    down_payment = house_price * 0.40
    remaining_balance = house_price - down_payment
    installment_amount = remaining_balance / 3

    payment_data = [
        [Paragraph("1. Peşinat (%40)", payment_heading_style), Paragraph(format_currency(down_payment), payment_heading_style)],
        [Paragraph("   - Sözleşme anında ödenir.", styles['NormalTR']), ""],
        [Paragraph("2. 1. Ara Ödeme", payment_heading_style), Paragraph(format_currency(installment_amount), payment_heading_style)],
        [Paragraph("   - Karkas imalatı bitiminde ödenir.", styles['NormalTR']), ""],
        [Paragraph("3. 2. Ara Ödeme", payment_heading_style), Paragraph(format_currency(installment_amount), payment_heading_style)],
        [Paragraph("   - İç imalatlar bitiminde ödenir.", styles['NormalTR']), ""],
        [Paragraph("4. Son Ödeme", payment_heading_style), Paragraph(format_currency(installment_amount), payment_heading_style)],
        [Paragraph("   - Teslimat sırasında ödenir.", styles['NormalTR']), ""],
    ]
    if solar_price > 0:
        payment_data.append([Paragraph("Güneş Enerji Sistemi", payment_heading_style), Paragraph(format_currency(solar_price), payment_heading_style)])
        payment_data.append([Paragraph("   - Sözleşme anında ödenir.", styles['NormalTR']), ""])

    payment_table = Table(payment_data, colWidths=[120*mm, 50*mm])
    payment_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    final_page_elements.append(payment_table)
    elements.append(KeepTogether(final_page_elements))

    # Add Solar Appendix if applicable
    if project_details['solar']:
        solar_elements = _create_solar_appendix_elements_tr(project_details['solar_kw'], project_details['solar_price'], styles['Heading'], styles['NormalTR'], styles['PriceTotal'])
        elements.extend(solar_elements)
    
    # Add Floor Heating Appendix if applicable
    if project_details['heating']:
        heating_elements = _create_heating_appendix_elements_tr(styles) # Pass styles dict directly
        elements.extend(heating_elements)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_internal_cost_report_pdf(cost_breakdown_df, financial_summary_df, profile_analysis_df, project_details, customer_info):
    """Creates an internal cost report PDF in Turkish."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=25*mm,
        bottomMargin=25*mm
    )

    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']

    doc.onFirstPage = _header_footer_for_proposal
    doc.onLaterPages = _header_footer_for_proposal

    styles = getSampleStyleSheet()
    # Custom styles for Turkish report
    styles.add(ParagraphStyle(
        name='Header', parent=styles['Normal'], fontSize=18, alignment=TA_CENTER,
        spaceAfter=20, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    ))
    styles.add(ParagraphStyle(
        name='SectionHeading', parent=styles['Heading2'], fontSize=12, spaceBefore=12,
        spaceAfter=6, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='NormalTR', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=4, fontName=MAIN_FONT
    ))

    # Now define style variables after they are added to 'styles'
    header_style = styles['Header']
    section_heading_style = styles['SectionHeading']
    normal_tr_style = styles['NormalTR']


    table_header_style = ParagraphStyle(
        name='TableHeader', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.white, alignment=TA_CENTER
    )
    table_cell_style = ParagraphStyle(
        name='TableCell', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT, alignment=TA_LEFT
    )
    center_table_cell_style = ParagraphStyle(
        name='CenterTableCell', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT, alignment=TA_CENTER
    )
    right_table_cell_style = ParagraphStyle(
        name='RightTableCell', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT, alignment=TA_RIGHT
    )
    elements = []

    # --- Title ---
    elements.append(Paragraph("İÇ MALİYET RAPORU / INTERNAL COST REPORT", header_style))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f"<b>Müşteri:</b> {customer_info['name']} | <b>Tarih:</b> {datetime.now().strftime('%d/%m/%Y')}", normal_tr_style))
    elements.append(Spacer(1, 10*mm))

    # --- Project Information ---
    elements.append(Paragraph("PROJE BİLGİLERİ", section_heading_style))
    elements.append(Paragraph(f"<b>Boyutlar:</b> {project_details['width']}m x {project_details['length']}m x {project_details['height']}m | <b>Toplam Alan:</b> {project_details['area']:.2f} m² | <b>Yapı Tipi:</b> {project_details['structure_type']}", normal_tr_style))
    elements.append(Spacer(1, 8*mm))

    # --- Cost Breakdown ---
    cost_data = [[Paragraph(c, table_header_style) for c in cost_breakdown_df.columns]]
    for _, row in cost_breakdown_df.iterrows():
        cost_data.append([
            Paragraph(str(row['Item']), table_cell_style),
            Paragraph(str(row['Quantity']), center_table_cell_style),
            Paragraph(format_currency(row['Unit Price (€)']), right_table_cell_style),
            Paragraph(format_currency(row['Total (€)']), right_table_cell_style)
        ])
    cost_table = Table(cost_data, colWidths=[65*mm, 30*mm, 35*mm, 40*mm])
    cost_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")),('GRID', (0,0), (-1,-1), 0.5, colors.grey),('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f7fafc"), colors.white])]))
    elements.append(Paragraph("MALİYET DAĞILIMI", section_heading_style))
    elements.append(cost_table)

    # --- Steel Profile Analysis (if any) on a NEW PAGE ---
    if not profile_analysis_df.empty and project_details['structure_type'] == 'Light Steel':
        elements.append(PageBreak()) # NEW: Force page break
        elements.append(Paragraph("ÇELİK PROFİL ANALİZİ", section_heading_style))
        profile_data = [[Paragraph(c, table_header_style) for c in profile_analysis_df.columns]]
        for _, row in profile_analysis_df.iterrows():
            profile_data.append([
                Paragraph(str(row['Profile Type']), table_cell_style),
                Paragraph(str(row['Count']), center_table_cell_style),
                Paragraph(format_currency(row['Unit Price (€)']), right_table_cell_style),
                Paragraph(format_currency(row['Total (€)']), right_table_cell_style)
            ])
        profile_table = Table(profile_data, colWidths=[55*mm, 25*mm, 45*mm, 45*mm])
        profile_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")),('GRID', (0,0), (-1,-1), 0.5, colors.grey),('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f7fafc"), colors.white])]))
        elements.append(profile_table)

    # --- Financials on a NEW PAGE ---
    elements.append(PageBreak())
    elements.append(Paragraph("FİNANSAL ÖZET", section_heading_style))
    financial_data = []
    for _, row in financial_summary_df.iterrows():
        item_cell = Paragraph(str(row['Item']), table_cell_style)
        amount_cell = Paragraph(str(row['Amount (€)']), right_table_cell_style)
        if "TOTAL" in row['Item'] or "Total Cost" in row['Item']:
             item_cell = Paragraph(f"<b>{row['Item']}</b>", table_cell_style)
             amount_cell = Paragraph(f"<b>{row['Amount (€)']}</b>", right_table_cell_style)
        financial_data.append([item_cell, amount_cell])

    # Adjusted Table Style for Financial Summary for better professional look
    financial_table = Table(financial_data, colWidths=[100*mm, 70*mm])
    financial_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")), # Header background
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),             # Header text color
        ('LINEBELOW', (0,0), (-1,0), 1, colors.grey),           # Line below header
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f7fafc"), colors.white]) # Row banding
    ]))
    elements.append(financial_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_sales_contract_pdf(customer_info, house_sales_price, solar_sales_price, project_details, company_info): # logo_img_data is now optional and unused
    """Creates a sales contract PDF based on the provided template and project details."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=25*mm,
        bottomMargin=25*mm
    )
    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']

    doc.onFirstPage = _contract_header_footer_for_contract
    doc.onLaterPages = _contract_header_footer_for_contract

    styles = getSampleStyleSheet()
    # Define contract specific styles
    contract_heading_style = ParagraphStyle(
        name='ContractHeading', parent=styles['Heading2'], fontSize=13, spaceAfter=8, # Font size 13pt
        spaceBefore=12, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_CENTER
    )
    contract_subheading_style = ParagraphStyle(
        name='ContractSubheading', parent=styles['Heading3'], fontSize=10, spaceAfter=5, # Font size 10pt
        spaceBefore=8, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568")
    )
    contract_normal_style = ParagraphStyle(
        name='ContractNormal', parent=styles['Normal'], fontSize=8, leading=10, # Font size 8pt, leading 10pt
        spaceAfter=4, fontName=MAIN_FONT, alignment=TA_LEFT
    )
    contract_list_style = ParagraphStyle(
        name='ContractList', parent=styles['Normal'], fontSize=8, leading=10, # Font size 8pt, leading 10pt
        spaceAfter=2, leftIndent=8*mm, fontName=MAIN_FONT # Reduced leftIndent
    )
    contract_signature_style = ParagraphStyle(
        name='ContractSignature', parent=styles['Normal'], fontSize=8, leading=10, # Font size 8pt
        alignment=TA_CENTER
    )

    elements = []

    # Title
    elements.append(Paragraph("SALES CONTRACT", contract_heading_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Parties involved (updated with dynamic ID and Company No)
    today_date = datetime.now().strftime('%d')
    today_month = datetime.now().strftime('%B')
    today_year = datetime.now().year
    elements.append(Paragraph(f"This Agreement (\"Agreement\") is entered into as of this {today_date} day of {today_month}, {today_year} by and between,", contract_normal_style))
    elements.append(Paragraph(f"<b>{customer_info['name'].upper()}</b> (I.D. No: <b>{customer_info['id_no']}</b>) hereinafter referred to as the \"Buyer,\" and", contract_normal_style))
    elements.append(Paragraph(f"<b>{company_info['name'].upper()}</b>, Company No. <b>{company_info['company_no']}</b>, with a registered address at {company_info['address']}, hereinafter referred to as the \"Seller.\"", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Subject of the Agreement
    elements.append(Paragraph("Subject of the Agreement:", contract_subheading_style))
    elements.append(Paragraph(f"A. The Seller agrees to complete and deliver to the Buyer the LIGHT STEEL STRUCTURE CONSTRUCTION (Tiny House) being constructed under its coordination at the address specified by the Buyer, in accordance with the specifications detailed in Appendix A.", contract_normal_style))
    elements.append(Paragraph("B. The details of the construction related to the Portable House project will be considered as appendixes to this agreement, which constitute integral parts of the present agreement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Definitions
    elements.append(Paragraph("1. Definitions:", contract_subheading_style))
    elements.append(Paragraph("1.1. \"Completion\" refers to the point at which the Light Steel Structure House is fully constructed, inspected, and ready for delivery.", contract_normal_style))
    elements.append(Paragraph("1.2. \"Delivery Date\" refers to the date on which the property is handed over to the Buyer, at which point the Buyer assumes full ownership and risk.", contract_normal_style))
    elements.append(Paragraph("1.3. \"Force Majeure Event\" means any event beyond the reasonable control of the Seller that prevents the timely delivery of the house, including but not limited to acts of God, war, terrorism, strikes, lockouts, natural disasters, or any other event recognized under law.", contract_normal_style))
    elements.append(Paragraph("1.4. \"House\" means the structure, as described in Appendix A.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Sales Price and Payment Terms
    total_sales_price_for_contract = house_sales_price + solar_sales_price
    total_sales_price_formatted = format_currency(total_sales_price_for_contract)
    
    down_payment = house_sales_price * 0.40
    remaining_balance = house_sales_price - down_payment
    installment_amount = remaining_balance / 3

    elements.append(Paragraph("2. Sales Price and Payment Terms:", contract_subheading_style))
    elements.append(Paragraph(f"2.1. The sales price of the Portable Container House (herein after \"the house\") is <b>{format_currency(house_sales_price)}</b>, plus 19% VAT, according to the specifications, as described to APPENDIX \"A\", which constitutes an integral part of the present agreement.", contract_list_style))
    elements.append(Paragraph(f"2.2. The total sales price (including solar if applicable) is <b>{total_sales_price_formatted}</b> (VAT Included).", contract_list_style))
    elements.append(Paragraph("2.3. The Buyer will pay the following amounts according to the schedule:", contract_list_style))

    elements.append(Paragraph(f"- Main House (Total: {format_currency(house_sales_price)})", contract_list_style, bulletText=''))
    elements.append(Paragraph(f"   - 40% Down Payment: {format_currency(down_payment)} upon contract signing.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f"   - 1st Installment: {format_currency(installment_amount)} upon completion of structure.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f"   - 2nd Installment: {format_currency(installment_amount)} upon completion of interior works.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f"   - Final Payment: {format_currency(installment_amount)} upon final delivery.", contract_list_style, bulletText='-'))

    if solar_sales_price > 0:
        elements.append(Paragraph(f"- Solar System: {format_currency(solar_sales_price)} due upon contract signing.", contract_list_style, bulletText=''))

    elements.append(Paragraph("2.4. Any delay in payment shall result in legal interest charges at 2% per month.", contract_list_style))
    elements.append(Paragraph("2.5. If the Buyer fails to pay any installment for more than 20 days upon written notice, the seller reserves the right to terminate the contract and keep the deposit, as a compensation for damages caused.", contract_list_style))
    elements.append(Paragraph("2.6. The payment terms and dates envisaged under the headings of the sales price, payment terms, and delivery above constitute the essence of this sales agreement and form its basis.", contract_list_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Bank Details
    elements.append(Paragraph("2.7. Bank Details:", contract_subheading_style))
    bank_details_data = [
        [Paragraph("Bank Name:", contract_normal_style), Paragraph(COMPANY_INFO['bank_name'], contract_normal_style)],
        [Paragraph("Bank Address:", contract_normal_style), Paragraph(COMPANY_INFO['bank_address'], contract_normal_style)],
        [Paragraph("Account Name:", contract_normal_style), Paragraph(COMPANY_INFO['account_name'], contract_normal_style)],
        [Paragraph("IBAN:", contract_normal_style), Paragraph(COMPANY_INFO['iban'], contract_normal_style)],
        [Paragraph("Account Number:", contract_normal_style), Paragraph(COMPANY_INFO['account_number'], contract_normal_style)],
        [Paragraph("Currency:", contract_normal_style), Paragraph(COMPANY_INFO['currency_type'], contract_normal_style)],
        [Paragraph("SWIFT/BIC:", contract_normal_style), Paragraph(COMPANY_INFO['swift_bic'], contract_normal_style)],
    ]
    bank_details_table = Table(bank_details_data, colWidths=[40*mm, 130*mm])
    bank_details_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(bank_details_table)
    elements.append(Spacer(1, 6*mm)) # Reduced space


    # Inspection of the Property and Defects
    elements.append(Paragraph("3. Inspection of the Property and Defects:", contract_subheading_style))
    elements.append(Paragraph("3.1. The Buyer shall have the right to inspect the property during the construction process. The Buyer may request an inspection at any point with 7 days' notice.", contract_normal_style))
    elements.append(Paragraph("3.2. Any defects or concerns raised during inspections shall be addressed by the Seller at no additional cost to the Buyer. The buyer shall keep a written record of inspections which the byuer signs after each inspection, confirming the status of affairs.", contract_normal_style))
    elements.append(Paragraph("3.3. Final inspection of the completed house will occur within 10 days of the delivery date, after which the Buyer shall provide written a list of defects.", contract_normal_style))
    elements.append(Paragraph("3.4. If there are any possible defects, the seller will restore them within ........ days/months and notify the buyer. In such a case, the delivery of the house will be determined accordingly.", contract_normal_style))
    elements.append(Paragraph("3.5. The seller will repair and/or replace any possible defects, within ........ days/months.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Completion of the House
    elements.append(Paragraph("4. Completion of the House:", contract_subheading_style))
    elements.append(Paragraph("4.1. The Seller will issue an invoice and deliver the property to the Buyer after the full payment of the sales price and all amounts specified in Article 2, upon completion of the construction of the light steel structure house. Document procurement related to this matter is outside the specified time for delivery.", contract_normal_style))
    elements.append(Paragraph("4.2. In order to complete processes such as partitioning, transfer, etc., the Buyer agrees to assist the Seller and, for this purpose, to apply to official, semi-official, and other authorities jointly or individually with the Seller and/or other shareholder or shareholders, to sign necessary signatures, fill out forms, and/or, if necessary, appoint the Seller as a representative.", contract_normal_style))
    elements.append(Paragraph("4.3. The Buyer will be responsible for the Tax (VAT) of the house from the delivery of the light steel structure house.", contract_normal_style))
    elements.append(Paragraph("4.4. Despite the Seller's completion of the necessary legal procedures, the Seller will not be responsible for delays and extra transit expenses related to customs procedures and exit of the materials of this house.", contract_normal_style))
    
    # project_details['delivery_duration_business_days'] is already calculated in calculate()
    elements.append(Paragraph(f"4.5. The House will be delivered within approximately {project_details['delivery_duration_business_days']} working days (excluding weekends and public holidays), as from the signing of this agreement.", contract_normal_style))
    elements.append(Paragraph("4.6. Any delays caused by Force Majeure events or by the Buyer shall extend the delivery period accordingly.", contract_normal_style))
    elements.append(Paragraph("4.7. If the seller fails to deliver the house within the set delivery date (4.5.), due to unforeseen delays, he is obliged to notify the buyer in writing, stating the reasons for the delay and proposing ways of overcoming the said delay.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Termination
    elements.append(Paragraph("5. Termination:", contract_subheading_style))
    elements.append(Paragraph("5.1. In case the Buyer fails to fulfill any of the conditions of this agreement, the Seller has the right to terminate the agreement immediately, by sending a written notification explaining the reasons for such termination.", contract_normal_style))
    elements.append(Paragraph("5.2. If the Buyer decides not to purchase the house by the given date, the Buyer acknowledges and undertakes that they will lose the entire deposit given as compensation for damages. In the event of a problem caused by the Seller or if the Seller decides not to transfer to the Buyer, the Seller will refund the full deposit to the Buyer.", contract_normal_style))
    elements.append(Paragraph("5.3. All notices to be given under this agreement will be deemed to have been given or served by being left at the above-mentioned addresses of the parties or by being sent by post.", contract_normal_style))
    elements.append(Paragraph("5.4. This agreement is made in 2 copies, signed and initialed by the parties.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Notifications
    elements.append(Paragraph("6. Notifications:", contract_subheading_style))
    elements.append(Paragraph("The following shall be considered as valid notifications:", contract_normal_style))
    elements.append(Paragraph("6.1. By regular mail", contract_list_style))
    elements.append(Paragraph("6.2. By registered mail", contract_list_style))
    elements.append(Paragraph("6.3. By double registered mail", contract_list_style))
    elements.append(Paragraph("6.4. By email which shall be sent by the usual electronic email used by the parties", contract_list_style))
    elements.append(Paragraph("6.5. By service via a bailiff", contract_list_style))
    elements.append(Paragraph("6.6. By fax", contract_list_style))
    elements.append(Paragraph("6.7. Telephone conversations, telephone messages (SMS), messages through viber, whats'app, facebook messenger and any other application/s not mentioned in this paragraph, shall not constitute a valid notice under above paragraph (4c).", contract_list_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Warranty and Defects liability
    elements.append(Paragraph("7. Warranty and Defects liability:", contract_subheading_style))
    elements.append(Paragraph("7.1. The seller warrants that the house will be free if defects in materials and workmanship, for a period of ........ (months/year), from the day of delivery.", contract_normal_style))
    elements.append(Paragraph("7.2. The said warrantee does not cover damages caused by misuse, negligence, or external factors (e.g. natural disasters).", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Applicable Law
    elements.append(Paragraph("8. Applicable Law:", contract_subheading_style))
    elements.append(Paragraph("This Agreement and any matter relating thereto shall be governed, construed and interpreted in accordance with the laws of the Republic of Cyprus any dispute arising under it shall be subject to the exclusive jurisdiction of the Cyprus courts.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Dispute Resolution - Mediation / Arbitration
    elements.append(Paragraph("9. Dispute Resolution - Mediation / Arbitration", contract_subheading_style))
    elements.append(Paragraph("9.1. Any disputes arising under this Agreement and prior to any litigation before the relevant Court, will first be addressed through negotiation between the parties.", contract_normal_style))
    elements.append(Paragraph("9.2. If the dispute cannot be resolved through negotiation, the parties agree to submit to mediation in the Republic of Cyprus, according to Mediation Act §159(1)/2012.", contract_normal_style))
    elements.append(Paragraph("9.3. If mediation fails, the dispute will be resolved through binding arbitration under the rules of [Arbitration Organization].", contract_normal_style))
    elements.append(Paragraph("9.4. The above alternative dispute resolution, do not conflict the Constitutional right of either party may seek relief in the courts of Cyprus if there will be no amicable settlement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Amendments
    elements.append(Paragraph("10. Amendements:", contract_subheading_style))
    elements.append(Paragraph("Any amendements or modifications to this agreement, must be made in writing and signed by both parties prior to a written notification as above (term 6).", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Final Clause
    elements.append(Paragraph("11. This Agreement is made in two (2) identical copies in English language, with each party receiving one copy of the Agreement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    elements.append(Paragraph("IN WITNESS THEREOF, the parties have caused their authorized representatives to sign this Agreement on their behalf, the day and year above written.", contract_normal_style))
    elements.append(Spacer(1, 25*mm)) # Sufficient space before final signatures

    # Final Signature Block (at the very end of the document, centered, larger gap for actual signatures)
    final_signature_data = [
        [Paragraph(f"<b>THE SELLER</b><br/><br/><br/>________________________________________<br/>For and on behalf of<br/>{company_info['name'].upper()}", contract_signature_style),
         Paragraph(f"<b>THE BUYER</b><br/><br/><br/>________________________________________<br/>{customer_info['name'].upper()}<br/>I.D. No: {customer_info['id_no']}", contract_signature_style)]
    ]
    # Adjust colWidths to ensure text fits and lines are proportional
    final_signature_table = Table(final_signature_data, colWidths=[80*mm, 80*mm], hAlign='CENTER')
    final_signature_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(final_signature_table)

    elements.append(Spacer(1, 10*mm)) # Space between signatures and date
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", contract_normal_style))

    # Witnesses (from original template)
    elements.append(Spacer(1, 8*mm)) # Space before witnesses
    elements.append(Paragraph("Witnesses:", contract_normal_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("1 (Sgn.) _____________________________________", contract_normal_style))
    elements.append(Paragraph("(name and i.d.)", contract_normal_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("2 (Sgn.) _____________________________________", contract_normal_style))
    elements.append(Paragraph("(name and i.d.)", contract_normal_style))

    elements.append(PageBreak())

    # APPENDIX "A" - Scope of Work
    elements.append(Paragraph("APPENDIX \"A\" - SCOPE OF WORK", contract_heading_style))
    elements.append(Paragraph("Within the scope of this sales agreement, the specified Light Steel Structure House will have the following features and materials:", contract_normal_style))
    elements.append(Spacer(1, 5*mm))

    def get_yes_no_en(value):
        return 'Yes' if value else '' # Changed 'No' to empty string

    appendix_data = []
    appendix_data.append([Paragraph("<b>Dimensions and Area:</b>", contract_subheading_style), Paragraph(f"The house has dimensions of {project_details['width']}m x {project_details['length']}m x {project_details['height']}m. It has a total area of {project_details['area']:.2f} m².", contract_normal_style)])
    
    # Building structure details (dynamic based on type for Appendix A)
    building_structure_details_appendix_en = ""
    if project_details['structure_type'] == 'Light Steel':
        building_structure_details_appendix_en = """
        Skeleton: Box profile with dimensions of 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm will be used. (Optional dimensions can be changed) Antirust will be applied to all box profiles and can be painted with the desired color. All our profile welding works have EN3834 certification in accordance with European standards. The construction operations of the entire building are subject to European standards and EN 1090-1 Light Steel Construction license inspection.
        """
    else: # Heavy Steel
        building_structure_details_appendix_en = """
        Skeleton: Steel house frame with all necessary cross-sections (columns, beams), including connection components (flanges, screws, bolts), all as static drawings.
        HEA120 OR HEA160 Heavy metal will be used in models with title deed and construction permit. All non-galvanized metal surfaces will be sandblasted according to the Swedish standard Sa 2.5 and will be coated with a zincphosphate primer 80μm thick.
        Anti-rust will be applied to all profiles and can be painted in the desired color.
        All our profile welding works have EN3834 certificate in accordance with European standards. All construction processes of the building are subject to European standards and EN 1090-1 Steel Construction license inspection.
        """
    appendix_data.append([Paragraph("<b>Construction Materials:</b>", contract_subheading_style), Paragraph(building_structure_details_appendix_en, contract_normal_style)])

    # Corrected plasterboard logic for Appendix A display
    display_plasterboard_interior_appendix = project_details['plasterboard_interior'] and project_details['structure_type'] == 'Light Steel'
    display_plasterboard_all_appendix = project_details['plasterboard_all'] and project_details['structure_type'] == 'Heavy Steel'

    appendix_data.append([Paragraph("<b>Interior and Exterior Covering:</b>", contract_subheading_style), Paragraph(f"12mm plywood will be used for interior flooring. Knauf AquaPanel will be used for both interior and exterior drywall. Inner Wall OSB: {get_yes_no_en(project_details['osb_inner_wall'])}. Interior Walls: Plasterboard {get_yes_no_en(display_plasterboard_interior_appendix or display_plasterboard_all_appendix)}.", contract_normal_style)])
    appendix_data.append([Paragraph("<b>Insulation:</b>", contract_subheading_style), Paragraph(f"Floor Insulation: {get_yes_no_en(project_details['insulation_floor'])}. Wall Insulation: {get_yes_no_en(project_details['insulation_wall'])}.", contract_normal_style)])
    appendix_data.append([Paragraph("<b>Floor Coverings:</b>", contract_subheading_style), Paragraph(f"{project_details['floor_covering_type']} will be used for floor coverings.", contract_normal_style)])
    appendix_data.append([Paragraph("<b>Roof Covering:</b>", contract_subheading_style), Paragraph("100mm Sandwich Panel will be used for the roof.", contract_normal_style)])
    
    # Plumbing (only include if plumbing is TRUE)
    if project_details['plumbing']:
        appendix_data.append([Paragraph("<b>Plumbing:</b>", contract_subheading_style), Paragraph(f"Plumbing installation {'' if project_details['plumbing'] else 'does NOT'} include external water connection. {PLUMBING_MATERIALS_EN.strip()}", contract_normal_style)])
    
    # Electrical (only include if electrical is TRUE)
    if project_details['electrical']:
        appendix_data.append([Paragraph("<b>Electrical:</b>", contract_subheading_style), Paragraph(f"Electrical installation {'' if project_details['electrical'] else 'does NOT'} include external connection. {ELECTRICAL_MATERIALS_EN.strip()}", contract_normal_style)])

    # Aluminum Windows and Doors (unified details)
    appendix_data.append([Paragraph("<b>Windows and Doors:</b>", contract_subheading_style), Paragraph(f"Aluminum windows and doors of various sizes will be used, with a height of 2.00m. Color: {project_details['window_door_color']}. The following windows and doors will be included in this project:<br/>Windows: {project_details['window_count']} ({project_details['window_size']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size']})<br/>WC Windows: {project_details['wc_window_count']} ({project_details['wc_window_size']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sliding Doors: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size'] + ')'}<br/>Doors: {project_details['door_count']} ({project_details['door_size']})", contract_normal_style)])
    
    # Additional Features (only list if included)
    additional_features_text = []
    if project_details['kitchen']:
        additional_features_text.append(f"Kitchen: {get_yes_no_en(project_details['kitchen'])}")
        additional_features_text.append(KITCHEN_MATERIALS_EN.replace('\n', '<br/>')) # Add kitchen materials
    if project_details['shower']:
        additional_features_text.append(f"Shower/WC: {get_yes_no_en(project_details['shower'])}")
        additional_features_text.append(SHOWER_WC_MATERIALS_EN.replace('\n', '<br/>')) # Add Shower/WC materials
    if project_details['heating']:
        additional_features_text.append(f"Floor Heating: {get_yes_no_en(project_details['heating'])}")
    if project_details['solar']:
        additional_features_text.append(f"Solar: {get_yes_no_en(project_details['solar'])} ({project_details['solar_kw']} kW)")
    if project_details['wheeled_trailer_included']:
        additional_features_text.append(f"Wheeled Trailer: {get_yes_no_en(project_details['wheeled_trailer_included'])} ({format_currency(project_details['wheeled_trailer_price'])})")
    
    if additional_features_text: # Only add this row if there are any features to list
        appendix_data.append([Paragraph("<b>Additional Features:</b>", contract_subheading_style), Paragraph("<br/>".join(additional_features_text), contract_normal_style)])

    appendix_table = Table(appendix_data, colWidths=[40*mm, 130*mm])
    appendix_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-2), 0.5, colors.grey),
    ]))
    elements.append(appendix_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# === Streamlit App Definition ===
def run_streamlit_app():
    # Set page configuration for wide layout and title
    st.set_page_config(layout="wide", page_title="Premium Home Cost Calculator")

    # Custom CSS for Streamlit UI
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
        color: #2d3748; /* Light Mode default */
        background-color: #f8f9fa; /* Light Mode default */
    }
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        transition: all 0.3s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #2c5282;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .st-dg { /* DataFrame style */
        width: 100%;
    }
    .section-title {
        background-color: #3182ce;
        color: white;
        padding: 10px;
        border-radius: 8px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .warning {
        color: #e53e3e;
        font-weight: 500;
        background-color: #fff5f5;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #fed7d7;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Premium Home Cost Calculator")

    # --- Customer Information Section ---
    st.header("Müşteri Bilgileri (İsteğe Bağlı)")
    # Using st.session_state to persist values across reruns if needed, though for simple inputs, direct assignment often works.
    # We add keys for clarity and best practice, especially with conditional rendering or multiple widgets of the same type.
    customer_name = st.text_input("Ad Soyad:", value="GENEL", key="customer_name_input")
    customer_company = st.text_input("Şirket:", key="customer_company_input")
    customer_address = st.text_input("Adres:", key="customer_address_input")
    customer_city = st.text_input("Şehir:", key="customer_city_input")
    customer_phone = st.text_input("Telefon:", key="customer_phone_input")
    customer_email = st.text_input("E-posta:", key="customer_email_input")
    customer_id_no = st.text_input("Kimlik/Pasaport No:", value="", key="customer_id_input")
    st.markdown("<div class='warning'>Not: Müşteri bilgileri zorunlu değildir. Boş bırakılırsa 'GENEL' olarak işaretlenecektir.</div>", unsafe_allow_html=True)

    # --- Project Details Section ---
    st.markdown("<div class='section-title'>PROJE DETAYLARI</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        structure_type_val = st.radio("Yapı Tipi:", ['Light Steel', 'Heavy Steel'], key="structure_type_radio")
        welding_labor_type_val = st.selectbox("Çelik Kaynak İşçiliği:", ['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'], key="welding_labor_select")
        
        # Determine actual welding labor key for calculation
        if welding_labor_type_val == 'Standard Welding (160€/m²)':
            welding_labor_option_val = 'standard'
        else:
            welding_labor_option_val = 'trmontaj'

        # Streamlit handles disabling widgets directly.
        plasterboard_interior_disabled = (structure_type_val == 'Heavy Steel')
        plasterboard_all_disabled = (structure_type_val == 'Light Steel')

        plasterboard_interior_option_val = st.checkbox("İç Alçıpan Dahil Et", value=True, disabled=plasterboard_interior_disabled, key="pb_int_checkbox")
        plasterboard_all_option_val = st.checkbox("İç ve Dış Alçıpan Dahil Et", value=False, disabled=plasterboard_all_disabled, key="pb_all_checkbox")
        
        # Logic to ensure only one plasterboard option is considered True for calculation based on structure type
        # These are the *calculated* values used in the backend logic, not directly the checkbox states
        if structure_type_val == 'Light Steel':
            plasterboard_all_calc = False # Heavy Steel'e ait seçenek Light Steel'de otomatik false olsun
            plasterboard_interior_calc = plasterboard_interior_option_val # Light Steel'de iç alçıpan seçimi geçerli
        elif structure_type_val == 'Heavy Steel':
            plasterboard_interior_calc = False # Light Steel'e ait seçenek Heavy Steel'de otomatik false olsun
            plasterboard_all_calc = plasterboard_all_option_val # Heavy Steel'de tüm alçıpan seçimi geçerli
        else: # Fallback (should not be reached with radio buttons)
            plasterboard_interior_calc = plasterboard_interior_option_val
            plasterboard_all_calc = plasterboard_all_option_val

        # OSB depends on either plasterboard being selected (the calculated values)
        osb_inner_wall_disabled = not (plasterboard_interior_calc or plasterboard_all_calc)
        osb_inner_wall_option_val = st.checkbox("İç Duvar OSB Malzemesi Dahil Et", value=True, disabled=osb_inner_wall_disabled, key="osb_inner_checkbox")
        
        if osb_inner_wall_disabled: # If no plasterboard is selected, OSB should be false for calculation
            osb_inner_wall_calc = False
        else:
            osb_inner_wall_calc = osb_inner_wall_option_val


    with col2:
        width_val = st.number_input("Genişlik (m):", value=10.0, step=0.1, key="width_input")
        length_val = st.number_input("Uzunluk (m):", value=8.0, step=0.1, key="length_input")
        height_val = st.number_input("Yükseklik (m):", value=2.6, step=0.1, key="height_input")
        room_config_val = st.selectbox("Oda Konfigürasyonu:", [
            'Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
            '1 Room + Shower / WC + Kitchen', '2 Rooms + Shower / WC + Kitchen',
            '3 Rooms + 2 Showers / WC + Kitchen'
        ], key="room_config_select")
        
        facade_sandwich_panel_disabled = (structure_type_val == 'Light Steel')
        facade_sandwich_panel_option_val = st.checkbox("Dış Cephe Sandviç Panel Dahil Et (Ağır Çelik için)", value=True, disabled=facade_sandwich_panel_disabled, key="facade_panel_checkbox")
        
        if facade_sandwich_panel_disabled:
            facade_sandwich_panel_calc = False # Ensure false if Light Steel
        else:
            facade_sandwich_panel_calc = facade_sandwich_panel_option_val


    # --- Steel Profile Quantities Section ---
    st.markdown("<div class='section-title'>ÇELİK PROFİL MİKTARLARI (Hafif Çelik için)</div>", unsafe_allow_html=True)
    st.markdown("<b>(Her 6m parça için - manuel olarak girin, aksi takdirde otomatik hesaplanır)</b>", unsafe_allow_html=True)
    
    steel_profile_disabled = (structure_type_val == 'Heavy Steel')
    
    col3, col4, col5 = st.columns(3)
    with col3:
        profile_100x100_count_val = st.number_input("100x100x3 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="p100x100_input")
    with col4:
        profile_100x50_count_val = st.number_input("100x50x3 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="p100x50_input")
    with col5:
        profile_40x60_count_val = st.number_input("40x60x2 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="p40x60_input")
    
    col6, col7, col8 = st.columns(3)
    with col6:
        profile_50x50_count_val = st.number_input("50x50x2 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="p50x50_input")
    with col7:
        profile_30x30_count_val = st.number_input("30x30x2 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="p30x30_input")
    with col8:
        profile_HEA160_count_val = st.number_input("HEA160 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="pHEA160_input")

    # --- Windows and Doors Section ---
    st.markdown("<div class='section-title'>PENCERELER VE KAPILAR</div>", unsafe_allow_html=True)
    col9, col10, col11 = st.columns(3)
    with col9:
        window_input_val = st.number_input("Pencere Adedi:", value=4, min_value=0, key="window_count_input")
        sliding_door_input_val = st.number_input("Sürme Cam Kapı Adedi:", value=0, min_value=0, key="sliding_door_count_input")
        wc_window_input_val = st.number_input("WC Pencere Adedi:", value=1, min_value=0, key="wc_window_count_input")
        wc_sliding_door_input_val = st.number_input("WC Sürme Kapı Adedi:", value=0, min_value=0, key="wc_sliding_door_count_input")
        door_input_val = st.number_input("Kapı Adedi:", value=2, min_value=0, key="door_count_input")
    with col10:
        window_size_val = st.text_input("Pencere Boyutu:", value="100x100 cm", key="window_size_input")
        sliding_door_size_val = st.text_input("Sürme Kapı Boyutu:", value="200x200 cm", key="sliding_door_size_input")
        wc_window_size_val = st.text_input("WC Pencere Boyutu:", value="60x50 cm", key="wc_window_size_input")
        wc_sliding_door_size_val = st.text_input("WC Sürme Kapı Boyutu:", value="140x70 cm", key="wc_sliding_door_size_input")
        door_size_val = st.text_input("Kapı Boyutu:", value="90x210 cm", key="door_size_input")
    with col11:
        window_door_color_val = st.selectbox("Pencere/Kapı Rengi:", ['White', 'Black', 'Grey'], key="window_door_color_select")

    # --- Additional Equipment Section ---
    st.markdown("<div class='section-title'>EK DONANIMLAR</div>", unsafe_allow_html=True)
    col12, col13 = st.columns(2)
    with col12:
        kitchen_input_val = st.checkbox("Mutfak Dahil Et", value=True, key="kitchen_checkbox")
        shower_input_val = st.checkbox("Duş/WC Dahil Et", value=True, key="shower_checkbox")
        wc_ceramic_input_val = st.checkbox("WC Seramik Zemin/Duvar", value=False, key="wc_ceramic_checkbox")
        electrical_installation_input_val = st.checkbox("Elektrik Tesisatı (Malzemelerle)", value=False, key="electrical_checkbox")
        plumbing_installation_input_val = st.checkbox("Sıhhi Tesisat (Malzemelerle)", value=False, key="plumbing_checkbox")
        insulation_floor_option_val = st.checkbox("Zemin Yalıtımı Dahil Et (10€/m²)", value=True, key="floor_insulation_checkbox")
        insulation_wall_option_val = st.checkbox("Duvar Yalıtımı Dahil Et (10€/m²)", value=True, key="wall_insulation_checkbox")
    with col13:
        # Disable if WC Ceramic is not checked
        wc_ceramic_area_disabled = not wc_ceramic_input_val
        wc_ceramic_area_val = st.number_input("WC Seramik Alanı (m²):", value=0.0, step=0.1, min_value=0.0, disabled=wc_ceramic_area_disabled, key="wc_ceramic_area_input")
        
        transportation_input_val = st.checkbox("Nakliye Dahil Et (500€)", value=False, key="transportation_checkbox")
        heating_option_val = st.checkbox("Yerden Isıtma Dahil Et (50€/m²)", value=False, key="heating_checkbox")
        solar_option_val = st.checkbox("Güneş Enerjisi Sistemi", value=False, key="solar_checkbox")
        floor_covering_option_val = st.selectbox("Zemin Kaplama Tipi:", ['Laminate Parquet', 'Ceramic'], key="floor_covering_select")

    col14, col15 = st.columns(2)
    with col14:
        solar_capacity_val = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not solar_option_val, key="solar_capacity_select")
    with col15:
        solar_price_val = solar_capacity_val * FIYATLAR['solar_per_kw'] if solar_option_val else 0.0
        st.number_input("Güneş Enerjisi Fiyatı (€):", value=solar_price_val, disabled=True, key="solar_price_display")

    wheeled_trailer_option_val = st.checkbox("Tekerlekli Römork", value=False, key="trailer_checkbox")
    wheeled_trailer_price_input_val = st.number_input("Römork Fiyatı (€):", value=0.0, disabled=not wheeled_trailer_option_val, key="trailer_price_input")

    # --- Financial Settings Section ---
    st.markdown("<div class='section-title'>FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
    # Using a tuple for options to easily store and retrieve the numerical value
    profit_rate_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
    profit_rate_val_tuple = st.selectbox("Kar Oranı:", options=profit_rate_options, format_func=lambda x: x[0], index=3, key="profit_rate_select")
    profit_rate_val = profit_rate_val_tuple[1] # Extract numerical value
    st.markdown(f"<div>KDV Oranı: {VAT_RATE*100:.0f}% (Sabit)</div>", unsafe_allow_html=True)

    # --- Customer Notes Section ---
    st.markdown("<div class='section-title'>MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR</div>", unsafe_allow_html=True)
    customer_notes_val = st.text_area("Müşteri Notları:", key="customer_notes_textarea")

    # --- PDF Language Selection ---
    pdf_language_selector_val_tuple = st.selectbox("Teklif PDF Dili:", options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')], format_func=lambda x: x[0], key="pdf_language_select")
    pdf_language_selector_val = pdf_language_selector_val_tuple[1] # Extract value

    # --- Calculate Button and Results Display ---
    if st.button("Hesapla ve Teklifleri Oluştur"):
        try:
            # --- Calculation Logic (Copied from your calculate() function) ---
            width, length, height = width_val, length_val, height_val
            window_count, sliding_door_count = window_input_val, sliding_door_input_val
            wc_window_count, wc_sliding_door_count = wc_window_input_val, wc_sliding_door_input_val
            door_count = door_input_val

            areas = calculate_area(width, length, height)
            floor_area = areas["floor"]
            wall_area = areas["wall"]
            roof_area = areas["roof"]

            costs = []
            profile_analysis_details = []

            if structure_type_val == 'Heavy Steel':
                total_structure_price = calculate_rounded_up_cost(floor_area * FIYATLAR["heavy_steel_m2"])
                costs.append({
                    'Item': 'Heavy Steel Construction (Structure)',
                    'Quantity': f'{floor_area:.2f} m²',
                    'Unit Price (€)': FIYATLAR["heavy_steel_m2"],
                    'Total (€)': total_structure_price
                })
                selected_welding_labor_price = FIYATLAR[f"welding_labor_m2_{welding_labor_option_val}"]
                total_welding_labor_price = calculate_rounded_up_cost(floor_area * selected_welding_labor_price)
                costs.append({
                    'Item': f'Steel Welding Labor ({welding_labor_option_val.upper()})',
                    'Quantity': f'{floor_area:.2f} m²',
                    'Unit Price (€)': selected_welding_labor_price,
                    'Total (€)': total_welding_labor_price
                })
            else: # Light Steel
                current_100x100_count = profile_100x100_count_val
                current_50x50_count = profile_50x50_count_val
                if current_100x100_count == 0 and current_50x50_count == 0:
                    # Automatic calculation if user didn't override manually
                    avg_100x100_per_m2 = 12 / 27.0
                    avg_50x50_per_m2 = 6 / 27.0
                    calculated_100x100 = math.ceil(floor_area * avg_100x100_per_m2)
                    calculated_50x50 = math.ceil(floor_area * avg_50x50_per_m2)
                    manual_profile_counts = {
                        "100x100x3": calculated_100x100, "100x50x3": profile_100x50_count_val,
                        "40x60x2": profile_40x60_count_val, "50x50x2": calculated_50x50,
                        "30x30x2": profile_30x30_count_val, "HEA160": profile_HEA160_count_val,
                    }
                else:
                    # Use user's manual input if provided
                    manual_profile_counts = {
                        "100x100x3": current_100x100_count, "100x50x3": profile_100x50_count_val,
                        "40x60x2": profile_40x60_count_val, "50x50x2": current_50x50_count,
                        "30x30x2": profile_30x30_count_val, "HEA160": profile_HEA160_count_val,
                    }
                default_piece_length = 6.0
                for profile_type_key, piece_count in manual_profile_counts.items():
                    if piece_count > 0:
                        profile_dict_key = f"steel_profile_{profile_type_key.lower()}"
                        if profile_type_key == "HEA160": profile_dict_key = "steel_profile_hea160"
                        unit_price_6m_piece = FIYATLAR.get(profile_dict_key)
                        if unit_price_6m_piece is None: continue
                        total_price = calculate_rounded_up_cost(piece_count * unit_price_6m_piece)
                        report_length_meters = piece_count * default_piece_length
                        profile_analysis_details.append({'Profile Type': profile_type_key, 'Count': piece_count, 'Unit Price (€)': unit_price_6m_piece, 'Total (€)': total_price})
                        costs.append({'Item': f"Steel Profile ({profile_type_key})", 'Quantity': f"{piece_count} pieces ({report_length_meters:.1f}m)", 'Unit Price (€)': unit_price_6m_piece, 'Total (€)': total_price})
                selected_welding_labor_price = FIYATLAR[f"welding_labor_m2_{welding_labor_option_val}"]
                total_welding_labor_price = calculate_rounded_up_cost(floor_area * selected_welding_labor_price)
                costs.append({'Item': f'Steel Welding Labor ({welding_labor_option_val.upper()})', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': selected_welding_labor_price, 'Total (€)': total_welding_labor_price})

            total_price = calculate_rounded_up_cost(roof_area * FIYATLAR["sandwich_panel_m2"])
            costs.append({'Item': 'Roof (Sandwich Panel)', 'Quantity': f'{roof_area:.2f} m²', 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': total_price})
            if structure_type_val == 'Light Steel' or (structure_type_val == 'Heavy Steel' and facade_sandwich_panel_calc): # Use calculated facade_sandwich_panel_calc
                total_price = calculate_rounded_up_cost(wall_area * FIYATLAR["sandwich_panel_m2"])
                costs.append({'Item': 'Facade (Sandwich Panel)', 'Quantity': f'{wall_area:.2f} m²', 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': total_price})
            total_panel_assembly_area = wall_area + roof_area
            total_price = calculate_rounded_up_cost(total_panel_assembly_area * FIYATLAR["panel_assembly_labor_m2"])
            costs.append({'Item': "Panel Assembly Labor", 'Quantity': f"{(total_panel_assembly_area):.2f} m²", 'Unit Price (€)': FIYATLAR["panel_assembly_labor_m2"], 'Total (€)': total_price})
            
            if osb_inner_wall_calc: # Use calculated osb_inner_wall_calc
                inner_wall_area_for_osb_calc = (wall_area / 2)
                osb_area_to_cover = inner_wall_area_for_osb_calc + roof_area
                osb_pieces_needed = math.ceil(osb_area_to_cover / OSB_PANEL_AREA_M2)
                if osb_pieces_needed > 0:
                    costs.append({'Item': 'Inner Wall OSB Material', 'Quantity': f"{osb_pieces_needed} pieces ({osb_area_to_cover:.2f} m²)", 'Unit Price (€)': FIYATLAR["osb_piece"], 'Total (€)': calculate_rounded_up_cost(osb_pieces_needed * FIYATLAR["osb_piece"])})

            plasterboard_total_area = 0
            plasterboard_labor_m2 = FIYATLAR["plasterboard_labor_m2_avg"]
            if structure_type_val == 'Light Steel' and plasterboard_interior_calc: # Use calculated plasterboard_interior_calc
                plasterboard_total_area = wall_area + roof_area
            elif structure_type_val == 'Heavy Steel' and plasterboard_all_calc: # Use calculated plasterboard_all_calc
                plasterboard_total_area = (wall_area * 1.5) + roof_area
            if plasterboard_total_area > 0:
                costs.append({'Item': 'Alçıpan Malzemesi', 'Quantity': f'{plasterboard_total_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plasterboard_material_m2"], 'Total (€)': calculate_rounded_up_cost(plasterboard_total_area * FIYATLAR["plasterboard_material_m2"])})
                costs.append({'Item': 'Alçıpan İşçiliği', 'Quantity': f'{plasterboard_total_area:.2f} m²', 'Unit Price (€)': plasterboard_labor_m2, 'Total (€)': calculate_rounded_up_cost(plasterboard_total_area * plasterboard_labor_m2)})
            
            if insulation_floor_option_val:
                total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["insulation_per_m2"])
                costs.append({'Item': 'Zemin Yalıtımı', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': total_price})
            if insulation_wall_option_val:
                total_price = calculate_rounded_up_cost(wall_area * FIYATLAR["insulation_per_m2"])
                costs.append({'Item': 'Duvar Yalıtımı', 'Quantity': f'{wall_area:.2f} m²', 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': total_price})

            plywood_pieces_needed = math.ceil(floor_area / (1.22 * 2.44))
            total_price = calculate_rounded_up_cost(plywood_pieces_needed * FIYATLAR["plywood_piece"])
            costs.append({'Item': 'Zemin (Kontrplak Malzemesi)', 'Quantity': plywood_pieces_needed, 'Unit Price (€)': FIYATLAR["plywood_piece"], 'Total (€)': total_price})
            total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["plywood_flooring_labor_m2"])
            costs.append({'Item': f'Zemin ({floor_covering_option_val} İşçiliği)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plywood_flooring_labor_m2"], 'Total (€)': total_price})
            
            if heating_option_val:
                total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["floor_heating_m2"])
                costs.append({'Item': 'Yerden Isıtma Sistemi', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["floor_heating_m2"], 'Total (€)': total_price})
            solar_cost = 0
            if solar_option_val:
                solar_cost = calculate_rounded_up_cost(solar_capacity_val * FIYATLAR['solar_per_kw'])
                costs.append({'Item': f'Güneş Enerjisi Sistemi ({solar_capacity_val} kW)', 'Quantity': 1, 'Unit Price (€)': solar_cost, 'Total (€)': solar_cost})
            
            if window_count > 0:
                total_price = calculate_rounded_up_cost(window_count * FIYATLAR["aluminum_window_piece"])
                costs.append({'Item': f'Pencere ({window_size_val} - {window_door_color_val})', 'Quantity': window_count, 'Unit Price (€)': FIYATLAR["aluminum_window_piece"], 'Total (€)': total_price})
            if sliding_door_count > 0:
                total_price = calculate_rounded_up_cost(sliding_door_count * FIYATLAR["sliding_glass_door_piece"])
                costs.append({'Item': f'Sürme Cam Kapı ({sliding_door_size_val} - {window_door_color_val})', 'Quantity': sliding_door_count, 'Unit Price (€)': FIYATLAR["sliding_glass_door_piece"], 'Total (€)': total_price})
            if wc_window_count > 0:
                total_price = calculate_rounded_up_cost(wc_window_count * FIYATLAR["wc_window_piece"])
                costs.append({'Item': f'WC Pencere ({wc_window_size_val} - {window_door_color_val})', 'Quantity': wc_window_count, 'Unit Price (€)': FIYATLAR["wc_window_piece"], 'Total (€)': total_price})
            if wc_sliding_door_count > 0:
                total_price = calculate_rounded_up_cost(wc_sliding_door_count * FIYATLAR["wc_sliding_door_piece"])
                costs.append({'Item': f'WC Sürme Kapı ({wc_sliding_door_size_val} - {window_door_color_val})', 'Quantity': wc_sliding_door_count, 'Unit Price (€)': FIYATLAR["wc_sliding_door_piece"], 'Total (€)': total_price})
            if door_count > 0:
                total_price = calculate_rounded_up_cost(door_count * FIYATLAR["door_piece"])
                costs.append({'Item': f'Kapı ({door_size_val} - {window_door_color_val})', 'Quantity': door_count, 'Unit Price (€)': FIYATLAR["door_piece"], 'Total (€)': total_price})
            total_door_window_count = window_count + sliding_door_count + wc_window_count + wc_sliding_door_count + door_count
            if total_door_window_count > 0:
                total_price = calculate_rounded_up_cost(total_door_window_count * FIYATLAR["door_window_assembly_labor_piece"])
                costs.append({'Item': 'Kapı/Pencere Montaj İşçiliği', 'Quantity': total_door_window_count, 'Unit Price (€)': FIYATLAR["door_window_assembly_labor_piece"], 'Total (€)': total_price})
            
            total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["connection_element_m2"])
            costs.append({'Item': "Bağlantı Elemanları", 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["connection_element_m2"], 'Total (€)': total_price})
            if kitchen_input_val:
                costs.append({'Item': 'Mutfak Kurulumu', 'Quantity': 1, 'Unit Price (€)': FIYATLAR["kitchen_installation_piece"], 'Total (€)': calculate_rounded_up_cost(FIYATLAR["kitchen_installation_piece"])})
            if shower_input_val:
                costs.append({'Item': 'Duş/WC Kurulumu', 'Quantity': 1, 'Unit Price (€)': FIYATLAR["shower_wc_installation_piece"], 'Total (€)': calculate_rounded_up_cost(FIYATLAR["shower_wc_installation_piece"])})
            if wc_ceramic_input_val and wc_ceramic_area_val > 0:
                total_material_cost = calculate_rounded_up_cost(wc_ceramic_area_val * FIYATLAR["wc_ceramic_m2_material"])
                total_labor_cost = calculate_rounded_up_cost(wc_ceramic_area_val * FIYATLAR["wc_ceramic_m2_labor"])
                total_wc_ceramic_cost = calculate_rounded_up_cost(total_material_cost + total_labor_cost)
                costs.append({'Item': 'WC Seramik (Malzeme & İşçilik)', 'Quantity': f"{wc_ceramic_area_val:.2f} m²", 'Unit Price (€)': calculate_rounded_up_cost(FIYATLAR["wc_ceramic_m2_material"] + FIYATLAR["wc_ceramic_m2_labor"]), 'Total (€)': total_wc_ceramic_cost})
            if electrical_installation_input_val:
                electrical_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["electrical_per_m2"])
                costs.append({'Item': 'Elektrik Tesisatı (Malzemelerle)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["electrical_per_m2"], 'Total (€)': electrical_cost})
            if plumbing_installation_input_val:
                plumbing_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["plumbing_per_m2"])
                costs.append({'Item': 'Sıhhi Tesisat (Malzemelerle)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plumbing_per_m2"], 'Total (€)': plumbing_cost})
            if transportation_input_val:
                costs.append({'Item': 'Nakliye', 'Quantity': 1, 'Unit Price (€)': FIYATLAR["transportation"], 'Total (€)': calculate_rounded_up_cost(FIYATLAR["transportation"])})
            if wheeled_trailer_option_val and wheeled_trailer_price_input_val > 0:
                trailer_price = calculate_rounded_up_cost(wheeled_trailer_price_input_val)
                costs.append({'Item': 'Tekerlekli Römork', 'Quantity': 1, 'Unit Price (€)': trailer_price, 'Total (€)': trailer_price})

            house_subtotal = sum([item['Total (€)'] for item in costs if 'Solar' not in item['Item']])
            waste_cost = calculate_rounded_up_cost(house_subtotal * FIRE_RATE)
            total_house_cost = calculate_rounded_up_cost(house_subtotal + waste_cost)
            profit = calculate_rounded_up_cost(total_house_cost * profit_rate_val)
            house_vat_base = calculate_rounded_up_cost(total_house_cost + profit)
            house_vat = calculate_rounded_up_cost(house_vat_base * VAT_RATE)
            house_sales_price = calculate_rounded_up_cost(house_vat_base + house_vat)
            total_sales_price = calculate_rounded_up_cost(house_sales_price + solar_price_val)
            
            delivery_duration_business_days = math.ceil((floor_area / 27.0) * 35)
            if delivery_duration_business_days < 10: delivery_duration_business_days = 10
            
            financial_summary_data = [
                ["Ara Toplam (Tüm Kalemler, Güneş Dahil)", sum([item['Total (€)'] for item in costs])],
                [f"Atık Maliyeti ({FIRE_RATE*100:.0f}%) (Sadece Ev için)", waste_cost],
                ["Toplam Maliyet (Ev + Atık + Güneş)", total_house_cost + solar_cost],
                [f"Kar ({profit_rate_val*100:.0f}%) (Sadece Ev için)", profit],
                ["", ""], # Spacer
                ["Ev Satış Fiyatı (KDV Dahil)", house_sales_price],
                ["Güneş Enerjisi Sistemi Fiyatı (KDV Dahil)", solar_cost],
                ["TOPLAM SATIŞ FİYATI", total_sales_price],
                ["", ""], # Spacer
                [f"KDV ({VAT_RATE*100:.0f}%)", house_vat],
                ["Yıllık Kurumlar Vergisi (%23.5) (yaklaşık)", calculate_rounded_up_cost((total_house_cost + profit) * ANNUAL_INCOME_TAX_RATE)],
                ["Aylık Muhasebe Giderleri", calculate_rounded_up_cost(MONTHLY_ACCOUNTING_EXPENSES)],
                ["Aylık Ofis Kirası", calculate_rounded_up_cost(MONTHLY_OFFICE_RENT)]
            ]

            formatted_financial_summary = []
            for item, amount in financial_summary_data:
                if isinstance(amount, (int, float)): formatted_amount = format_currency(amount)
                else: formatted_amount = amount
                formatted_financial_summary.append({'Item': item, 'Amount (€)': formatted_amount})

            # Prepare results dictionaries
            customer_info_result = {
                'name': customer_name.strip() or "GENEL", 'company': customer_company.strip() or "",
                'address': customer_address.strip() or "", 'city': customer_city.strip() or "",
                'phone': customer_phone.strip() or "", 'email': customer_email.strip() or "",
                'id_no': customer_id_no.strip() or ""
            }

            project_details_result = {
                'width': width_val, 'length': length_val, 'height': height_val, 'area': floor_area,
                'structure_type': structure_type_val,
                'plasterboard_interior': plasterboard_interior_calc, # Use calculated value
                'plasterboard_all': plasterboard_all_calc, # Use calculated value
                'osb_inner_wall': osb_inner_wall_calc, # Use calculated value
                'insulation_floor': insulation_floor_option_val,
                'insulation_wall': insulation_wall_option_val,
                'window_count': window_count, 'window_size': window_size_val,
                'window_door_color': window_door_color_val,
                'sliding_door_count': sliding_door_count, 'sliding_door_size': sliding_door_size_val,
                'wc_window_count': wc_window_count, 'wc_window_size': wc_window_size_val,
                'wc_sliding_door_count': wc_sliding_door_count, 'wc_sliding_door_size': wc_sliding_door_size_val,
                'door_count': door_count, 'door_size': door_size_val,
                'kitchen': kitchen_input_val, 'shower': shower_input_val,
                'wc_ceramic': wc_ceramic_input_val, 'wc_ceramic_area': wc_ceramic_area_val,
                'electrical': electrical_installation_input_val, 'plumbing': plumbing_installation_input_val,
                'transportation': transportation_input_val, 'heating': heating_option_val,
                'solar': solar_option_val, 'solar_kw': solar_capacity_val, 'solar_price': solar_price_val,
                'vat_rate': VAT_RATE, 'profit_rate': profit_rate_val,
                'room_configuration': room_config_val,
                'wheeled_trailer_included': wheeled_trailer_option_val,
                'wheeled_trailer_price': wheeled_trailer_price_input_val,
                'sales_price': total_sales_price,
                'delivery_duration_business_days': delivery_duration_business_days,
                'welding_labor_type': welding_labor_option_val,
                'facade_sandwich_panel_included': facade_sandwich_panel_calc, # Use calculated value
                'floor_covering_type': floor_covering_option_val
            }
            # --- End of Calculation Logic ---

            # --- Display Results in Streamlit ---
            st.subheader("Maliyet Detayları (Dahili Rapor)")
            st.dataframe(pd.DataFrame(costs).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            if not pd.DataFrame(profile_analysis_details).empty and project_details_result['structure_type'] == 'Light Steel':
                st.subheader("Çelik Profil Detaylı Analizi (Dahili Rapor)")
                st.dataframe(pd.DataFrame(profile_analysis_details).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            st.subheader("Finansal Özet (Dahili Rapor)")
            st.dataframe(pd.DataFrame(formatted_financial_summary).set_index('Item').style.format({"Amount (€)": "€{:,.2f}"}), use_container_width=True)

            # --- PDF Generation and Download Links ---
            st.markdown("---")
            st.subheader("PDF Çıktıları")
            col_pdf1, col_pdf2, col_pdf3 = st.columns(3)

            with col_pdf1:
                internal_pdf_bytes = create_internal_cost_report_pdf(pd.DataFrame(costs), pd.DataFrame(formatted_financial_summary), pd.DataFrame(profile_analysis_details), project_details_result, customer_info_result)
                st.download_button(
                    label="Dahili Maliyet Raporu İndir (Türkçe)",
                    data=internal_pdf_bytes,
                    file_name=f"Internal_Cost_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

            with col_pdf2:
                if pdf_language_selector_val == 'en_gr':
                    customer_pdf_bytes = create_customer_proposal_pdf(house_sales_price, solar_price_val, total_sales_price, project_details_result, customer_notes_val, customer_info_result)
                    st.download_button(
                        label="Müşteri Teklifi İndir (İngilizce-Yunanca)",
                        data=customer_pdf_bytes,
                        file_name=f"Customer_Proposal_EN_GR_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
                else: # Turkish version
                    customer_pdf_bytes = create_customer_proposal_pdf_tr(house_sales_price, solar_price_val, total_sales_price, project_details_result, customer_notes_val, customer_info_result)
                    st.download_button(
                        label="Müşteri Teklifi İndir (Türkçe)",
                        data=customer_pdf_bytes,
                        file_name=f"Customer_Proposal_TR_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf"
                    )
            with col_pdf3:
                sales_contract_pdf_bytes = create_sales_contract_pdf(customer_info_result, house_sales_price, solar_price_val, project_details_result, COMPANY_INFO)
                st.download_button(
                    label="Satış Sözleşmesi İndir",
                    data=sales_contract_pdf_bytes,
                    file_name=f"Sales_Contract_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            st.exception(e) # Display full traceback for debugging

# --- Start the Streamlit app ---
if __name__ == "__main__":
    run_streamlit_app()
