import streamlit as st
import math
import pandas as pd
import io
from datetime import datetime

# --- ReportLab Imports ---
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
except ImportError:
    st.error("Gerekli 'reportlab' kütüphanesi bulunamadı. Lütfen 'pip install reportlab Pillow' komutunu çalıştırın ve uygulamayı yeniden başlatın.")
    st.stop()


# --- Font Registration for ReportLab ---
try:
    pdfmetrics.registerFont(TTFont("FreeSans", "./fonts/FreeSans.ttf"))
    pdfmetrics.registerFont(TTFont("FreeSans-Bold", "./fonts/FreeSansBold.ttf"))
    pdfmetrics.registerFontFamily('FreeSans',
                                  normal='FreeSans',
                                  bold='FreeSans-Bold',
                                  italic='FreeSans',
                                  boldItalic='FreeSans-Bold')
    MAIN_FONT = "FreeSans"
except Exception as e:
    st.warning(f"UYARI: FreeSans fontları yüklenemedi. Lütfen 'FreeSans.ttf' ve 'FreeSansBold.ttf' dosyalarının uygulama dizininizdeki './fonts/' klasöründe olduğundan emin olun. Helvetica kullanılacaktır. Hata: {e}")
    MAIN_FONT = "Helvetica"

# === COMPANY INFORMATION ===
LOGO_URL = "https://drive.google.com/file/d/1yOH-k1Gm2Gos-ITSiZ1t3yMdq-_3MqZK"
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
    "steel_profile_120x60x5mm": 60.00,
    "steel_profile_50x50x2": 11.00,
    # "steel_profile_30x30x2": 8.50, # Kaldırıldı
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
    "kitchen_installation_standard_piece": 550.00,
    "kitchen_installation_special_piece": 1000.00,
    "shower_wc_installation_piece": 1000.00,
    "connection_element_m2": 1.50,
    "transportation": 350.00,
    "floor_heating_m2": 50.00,
    "wc_ceramic_m2_material": 20.00,
    "wc_ceramic_m2_labor": 20.00,
    "electrical_per_m2": 25.00,
    "plumbing_per_m2": 25.00,
    "osb_piece": 12.00,
    "insulation_per_m2": 5.00,
    # Labor Prices
    "welding_labor_m2_standard": 160.00,
    "welding_labor_m2_trmontaj": 20.00,
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00,
    "plasterboard_labor_m2_avg": 80.00,
    "plywood_flooring_labor_m2": 11.11,
    "door_window_assembly_labor_piece": 10.00,
    "solar_per_kw": 1250.00,
    
    # Yeni Zemin Sistemi Malzemeleri Fiyatları
    "skirting_meter_price": 2.00,
    "laminate_flooring_m2_price": 15.00,
    "under_parquet_mat_m2_price": 3.00,
    "osb2_18mm_piece_price": 30.00,
    "galvanized_sheet_m2_price": 10.00,

    # Aether Living Paket Bilgileri ve Fiyatları (Artık otomatik hesaplanacak, sabit fiyatlar kaldırıldı)
    # Yeni Ürün Malzeme Fiyatları ve Bilgi Kalemleri (UI'dan kaldırılanların price'ları silindi, sadece info'lar kaldı)
    "smart_home_systems_total_price": 350.00, # Akıllı Ev Sistemleri toplam fiyatı
    "white_goods_total_price": 800.00, # Beyaz Eşya (Buzdolabı, TV) toplam fiyatı
    "sofa_total_price": 400.00, # Kanepe toplam fiyatı
    "security_camera_total_price": 650.00, # Güvenlik Kamerası toplam fiyatı
    "exterior_cladding_price_per_m2": 150.00, # Dış Cephe Kaplama M2 fiyatı
    "bedroom_set_total_price": 800.00, # Yatak Odası Takımı toplam fiyatı
    "terrace_laminated_wood_flooring_price_per_m2": 40.00, # İşlenmiş çam zemin kaplama (teras için m2 fiyatı)
    "porcelain_tile_m2_price": 25.00, # Porselen fayans (zemin için, wc_ceramic fiyatı kullanılacak ama burada da bilgi olarak tutuldu)
    "concrete_panel_floor_price_per_m2": 50.00, # Beton panel zemin (m2 fiyatı)
    "premium_faucets_total_price": 200.00, # Premium Bataryalar toplam fiyatı
    "designer_furniture_total_price": 1000.00, # Entegre Özel Tasarım Mobilyalar toplam fiyatı
    "italian_sofa_total_price": 800.00, # İtalyan Kanepe toplam fiyatı
    "inclass_chairs_unit_price": 150.00, # Inclass Sandalyeler tane başı fiyatı
    "exterior_wood_cladding_m2_price": 150.00, # Dış cephe ahşap kaplama (işçilik ve malzeme dahil m2)
    "brushed_grey_granite_countertops_price_m2_avg": 425.00, # Granit Tezgahlar ortalama m2 fiyatı

    # Malzeme Bilgi Kalemleri (Fiyatı olmayanlar veya başka bir yerde fiyatı olanlar - Sadece listeleme ve PDF'e detay ekleme için)
    "steel_skeleton_info": "Metal iskelet", # EKLENDİ (KEYERROR DÜZELTMESİ İÇİN)
    "protective_automotive_paint_info": "Koruyucu otomotiv boyası",
    "insulation_info": "Yalıtım",
    "60mm_eps_sandwich_panel_info": "Standart 60mm EPS veya Poliüretan Sandviç Paneller (beyaz)",
    "100mm_eps_isothermal_panel_info": "Yüksek performanslı 100mm EPS veya Poliüretan İzotermik Paneller", # EKLENDİ (KEYERROR DÜZELTMESİ İÇİN)
    "galvanized_sheet_info": "Galvanizli sac",
    "plywood_osb_floor_panel_info": "Kontraplak/OSB zemin paneli",
    "12mm_laminate_parquet_info": "12mm Laminat Parke",
    "induction_hob_info": "İndüksiyonlu ocak",
    "electric_faucet_info": "Elektrikli batarya",
    "kitchen_sink_info": "Mutfak evyesi",
    "fully_functional_bathroom_fixtures_info": "Tam fonksiyonel banyo armatürleri (klozet, lavabo, elektrikli duş)",
    "kitchen_bathroom_countertops_info": "Mutfak ve banyo tezgahları",
    "treated_pine_floor_info": "İşlenmiş Çam Zemin Kaplaması (Teras Seçeneği ile)",
    "porcelain_tiles_info": "Porselen Fayans",
    "concrete_panel_floor_info": "Beton Panel Zemin",
    "premium_faucets_info": "Premium Bataryalar (örn. Hansgrohe)",
    "integrated_refrigerator_info": "Entegre Buzdolabı", # Zaten beyaz eşya içinde değerlendiriliyor
    "integrated_custom_furniture_info": "Entegre Özel Tasarım Mobilyalar (yüksek kaliteli MDF/lake)",
    "italian_sofa_info": "İtalyan Kanepe",
    "inclass_chairs_info": "Inclass Sandalyeler",
    "smart_home_systems_info": "Akıllı Ev Sistemleri",
    "advanced_security_camera_pre_installation_info": "Gelişmiş güvenlik kamerası ön kurulumu",
    "exterior_wood_cladding_lambiri_info": "Dış cephe ahşap kaplama - Lambiri",
    "brushed_grey_granite_countertops_info": "Fırçalanmış Gri Kale Granit Mutfak/Banyo Tezgahları",

    "electrical_cable_info": "Elektrik Kabloları (3x2.5 mm², 3x1.5 mm²)",
    "electrical_conduits_info": "Kablolama için Spiral Borular ve Kanallar",
    "electrical_junction_boxes_info": "Buatlar",
    "electrical_distribution_board_info": "Sigorta Kutusu (Dağıtım Panosu)",
    "electrical_circuit_breakers_info": "Sigortalar & Kaçak Akım Rölesi",
    "electrical_sockets_switches_info": "Prizler ve Anahtarlar",
    "electrical_lighting_fixtures_info": "İç Aydınlatma Armatürleri (LED Spot / Tavan Lambası)",
    "electrical_grounding_info": "Topraklama Sistemi Bileşenleri",

    "plumbing_pprc_pipes_info": "Sıcak/Soğuk Su için PPRC Borular",
    "plumbing_faucets_info": "Mutfak ve Banyo Bataryaları",
    "plumbing_shower_mixer_info": "Duş Başlığı ve Bataryası",
    "plumbing_valves_info": "Ana ve ara kesme vanaları",
    "plumbing_pvc_pipes_info": "PVC Gider Boruları (50mm / 100mm)",
    "plumbing_siphons_info": "Sifonlar ve yer süzgeçleri",

    "wc_toilet_bowl_info": "Klozet & Rezervuar",
    "wc_washbasin_info": "El Yıkama Lavabosu & Batarya",
    "wc_towel_rail_info": "Havluluk",
    "wc_mirror_info": "Ayna",
    "wc_accessories_info": "Banyo Aksesuarları",
    "wc_shower_unit_info": "Duş Ünitesi (Duş Başlığı ve Batarya)",

    "kitchen_mdf_info": "Parlak Beyaz Renk MDF Malzeme",
    "kitchen_cabinets_info": "Özel Üretim Mutfak Dolapları (özel ölçülerde)",
    "kitchen_countertop_info": "Tezgah (Laminat veya belirtilen eşdeğeri)",
    "kitchen_sink_faucet_info": "Evye ve Batarya",
}

FIRE_RATE = 0.05
VAT_RATE = 0.19
MONTHLY_ACCOUNTING_EXPENSES = 180.00
MONTHLY_OFFICE_RENT = 280.00
ANNUAL_INCOME_TAX_RATE = 0.235
OSB_PANEL_AREA_M2 = 1.22 * 2.44

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

# PDF için yeni metinler (İsteğe Bağlı Özellikler kaldırıldı ve format düzeltildi)
LIGHT_STEEL_BUILDING_STRUCTURE_EN_GR = """
<b>Building structure details:</b><br/>
Skeleton: Box profile with dimensions of 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm will be used. Antirust will be applied to all box profiles and can be painted with the desired color. All our profile welding works have EN3834 certification in accordance with European standards. The construction operations of the entire building are subject to European standards and EN 1090-1 Light Steel Construction license inspection.
"""

HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR = """
<b>Building structure details:</b><br/>
Skeleton: Steel house frame with all necessary cross-sections (columns, beams), including connection components (flanges, screws, bolts), all as static drawings.<br/>
HEA120 OR HEA160 Heavy metal will be used in models with title deed and construction permit. All non-galvanized metal surfaces will be sandblasted according to the Swedish standard Sa 2.5 and will be coated with a zincphosphate primer 80μm thick.<br/>
Anti-rust will be applied to all profiles and can be painted in the desired color.<br/>
All our profile welding works have EN3834 certificate in accordance with European standards. All construction processes of the building are subject to European standards and EN 1090-1 Steel Construction license inspection.
"""

LIGHT_STEEL_BUILDING_STRUCTURE_TR = """
<b>Bina yapı detayları:</b><br/>
İskelet: 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm ölçülerinde kutu profil kullanılacaktır. Tüm kutu profillere pas önleyici uygulanacak ve istenilen renge boyanabilir. Tüm profil kaynak işlerimiz Avrupa standartlarına uygun olarak EN3834 sertifikalıdır. Binanın tüm yapım süreçleri Avrupa standartlarına ve EN 1090-1 Hafif Çelik Yapı ruhsat denetimine tabidir.
"""

HEAVY_STEEL_BUILDING_STRUCTURE_TR = """
<b>Bina yapı detayları:</b><br/>
İskelet: Tüm gerekli kesitlere (kolonlar, kirişler) sahip çelik ev iskeleti, bağlantı elemanları (flanşlar, vidalar, cıvatalar) dahil, hepsi statik çizimlere göre olacaktır.<br/>
Tapulu ve inşaat ruhsatlı modellerde HEA120 VEYA HEA160 Ağır metal kullanılacaktır. Tüm galvanizli olmayan metal yüzeyler İsveç standardı Sa 2.5'e göre kumlama yapılacak ve 80μm kalınlığında çinko-fosfat astar ile kaplanacaktır.<br/>
Anti-rust will be applied to all profillere pas önleyici uygulanacak ve istenilen renge boyanabilir.<br/>
All our profile welding works have EN3834 certificate in accordance with European standards. All construction processes of the building are subject to Avrupa standartlarına ve EN 1090-1 Çelik Yapı ruhsat denetimine tabidir.
"""

# PDF özellikleri açıklamaları (İsteğe Bağlı Özellikler kaldırıldı)
INTERIOR_WALLS_DESCRIPTION_EN_GR = """
<b>1.4. INTERIOR WALLS:</b> 50mm polyurethane Sandwich Panel. Colour Option.
"""
INTERIOR_WALLS_DESCRIPTION_TR = """
<b>1.4. İÇ DUVARLAR:</b> 50mm poliüretan Sandviç Panel. Renk Seçeneği.
"""

ROOF_DESCRIPTION_EN_GR = """
<b>1.1. ROOF:</b> 100mm polyurethane Sandwich Panel. Bordex Internal Roofing 9 mm. 2 Coats Satin Plaster, 1 Coat Primer, 2 Coats Paint.
"""
ROOF_DESCRIPTION_TR = """
<b>1.1. ÇATI:</b> 100mm poliüretan Sandviç Panel. Bordex İç Çatı Kaplaması 9 mm. 2 Kat Saten Alçı, 1 Kat Astar, 2 Kat Boya.
"""

EXTERIOR_WALLS_DESCRIPTION_EN_GR = """
<b>1.2. EXTERIOR WALLS:</b> 50mm polyurethane Sandwich Panel. Color option.
"""
EXTERIOR_WALLS_DESCRIPTION_TR = """
<b>1.2. DIŞ DUVARLAR:</b> 50mm poliüretan Sandviç Panel. Renk seçeneği.
"""

# Zemin Yalıtım Malzemeleri Açıklaması (PDF için)
FLOOR_INSULATION_MATERIALS_EN_GR = """
<b>Floor Insulation Materials / Zemin Yalıtım Malzemeleri:</b>
"""
FLOOR_INSULATION_MATERIALS_TR = """
<b>Zemin Yalıtım Malzemeleri:</b>
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
        ["Mounting System", "Çatı kurulumu için sertifikalı montaj yapısı"],
        ["Cabling & Connectors", "Tüm gerekli DC/AC kablolar, MC4 konnektörler ve güvenlik şalterleri"],
        ["Installation & Commissioning", "Tam profesyonel kurulum ve sistemin devreye alınması"],
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
        name='NormalBilingual', parent=styles['Normal'], fontSize=8, leading=10,
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
    styles.add(ParagraphStyle(
        name='SectionSubheading', parent=styles['Heading3'], fontSize=9, spaceAfter=3, spaceBefore=7,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568")
    ))

    title_style = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=17, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER,
        spaceAfter=7, fontName=MAIN_FONT, textColor=colors.HexColor("#4a5568")
    )
    
    payment_heading_style = ParagraphStyle(
        name='PaymentHeading', parent=styles['Heading3'], fontSize=9, spaceAfter=3,
        spaceBefore=7, fontName=f"{MAIN_FONT}-Bold"
    )
    signature_style = ParagraphStyle(
        name='Signature', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT,
        alignment=TA_CENTER, leading=10
    )
    
    colored_table_header_style = ParagraphStyle(
        name='ColoredTableHeader', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold",
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

    # --- Customer & Project Information Section (Tablolar halinde düzenlendi) ---
    elements.append(Paragraph("CUSTOMER & PROJECT INFORMATION / ΠΛΗΡΟΦΟΡΙΕΣ ΠΕΛΑΤΗ & ΕΡΓΟΥ", styles['Heading']))
    
    # Oda Konfigürasyonu ve Boyut Bilgileri (Müşteri Bilgileri tablosu üstünde)
    elements.append(Paragraph(f"<b>Room Configuration / Διαμόρφωση Δωματίου:</b> {project_details['room_configuration']}", styles['NormalBilingual']))
    elements.append(Paragraph(f"<b>Dimensions / Διαστάσεις:</b> {project_details['width']}m x {project_details['length']}m x {project_details['height']}m | <b>Total Area / Συνολική Επιφάνεια:</b> {project_details['area']:.2f} m² | <b>Structure Type / Τύπος Κατασκευής:</b> {project_details['structure_type']}", styles['NormalBilingual']))
    elements.append(Spacer(1, 8*mm))

    customer_info_table_data = [
        [Paragraph("<b>Name / Όνομα:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['name']}", styles['NormalBilingual'])],
        [Paragraph("<b>Company / Εταιρεία:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['company'] or ''}", styles['NormalBilingual'])],
        [Paragraph("<b>Address / Διεύθυνση:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['address'] or ''}", styles['NormalBilingual'])],
        [Paragraph("<b>Phone / Τηλέφωνο:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['phone'] or ''}", styles['NormalBilingual'])],
        [Paragraph("<b>ID/Passport No / Αρ. Ταυτότητας/Διαβατηρίου:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['id_no'] or ''}", styles['NormalBilingual'])],
    ]
    customer_info_table = Table(customer_info_table_data, colWidths=[65*mm, 105*mm])
    customer_info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(customer_info_table)
    elements.append(Spacer(1, 8*mm))

    # --- Technical Specifications Section (Tablolar halinde düzenlendi) ---
    elements.append(Paragraph("TECHNICAL SPECIFICATIONS / ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", styles['Heading']))
    
    def get_yes_no(value):
        return 'Yes / Ναι' if value else 'No / Όχι'
    
    def get_yes_no_empty(value):
        return 'Yes / Ναι' if value else ''

    # Yapı ve Malzemeler (Construction Materials) - Kurumsal yapıya uygun hale getirildi, opsiyonel kaldırıldı
    building_structure_table_data = []
    if project_details['structure_type'] == 'Light Steel':
        building_structure_table_data.append([Paragraph('<b>Construction Type / Τύπος Κατασκευής</b>', styles['NormalBilingual']), Paragraph('Light Steel', styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Steel Structure Details / Λεπτομέρειες Χαλύβδινης Κατασκευής</b>', styles['NormalBilingual']), Paragraph(LIGHT_STEEL_BUILDING_STRUCTURE_EN_GR, styles['NormalBilingual'])])
        if project_details['plasterboard_interior'] or project_details['plasterboard_all']: # Koşullu ekleme
            building_structure_table_data.append([Paragraph('<b>Interior Walls / Εσωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(INTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof / Στέγη</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Exterior Walls / Εξωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
    else: # Heavy Steel
        building_structure_table_data.append([Paragraph('<b>Construction Type / Τύπος Κατασκευής</b>', styles['NormalBilingual']), Paragraph('Heavy Steel', styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Steel Structure Details / Λεπτομέρειες Χαλύβδινης Κατασκευής</b>', styles['NormalBilingual']), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof / Στέγη</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
    
    building_materials_table = Table(building_structure_table_data, colWidths=[60*mm, 110*mm])
    building_materials_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(building_materials_table)
    elements.append(Spacer(1, 5*mm))

    # İç Mekan ve Yalıtım (Interior and Insulation)
    interior_insulation_table_data = [
        [Paragraph('<b>Interior / Εσωτερικό</b>', styles['NormalBilingual']), Paragraph(f"Floor Covering: {project_details['floor_covering_type']}.", styles['NormalBilingual'])],
        [Paragraph('<b>Insulation / Μόνωση</b>', styles['NormalBilingual']), Paragraph(f"Floor Insulation: {get_yes_no_empty(project_details['insulation_floor'])}. Wall Insulation: {get_yes_no_empty(project_details['insulation_wall'])}.", styles['NormalBilingual'])],
    ]
    # Zemin yalıtım malzemeleri listesi doğrudan yalıtım bölümünün altına (TEKLİFTE BURAYA TAŞINDI)
    if project_details['insulation_floor']:
        floor_insulation_details_display_en_gr_text = [FLOOR_INSULATION_MATERIALS_EN_GR]
        if project_details['skirting_length_val'] > 0:
            floor_insulation_details_display_en_gr_text.append(f"• Skirting / Σοβατεπί ({project_details['skirting_length_val']:.2f} m)")
        if project_details['laminate_flooring_m2_val'] > 0:
            floor_insulation_details_display_en_gr_text.append(f"• Laminate Flooring 12mm / Laminate Δάπεδο 12mm ({project_details['laminate_flooring_m2_val']:.2f} m²)")
        if project_details['under_parquet_mat_m2_val'] > 0:
            floor_insulation_details_display_en_gr_text.append(f"• Under Parquet Mat 4mm / Υπόστρωμα Πακέτου 4mm ({project_details['under_parquet_mat_m2_val']:.2f} m²)")
        if project_details['osb2_18mm_count_val'] > 0:
            floor_insulation_details_display_en_gr_text.append(f"• OSB2 18mm or Concrete Panel 18mm / OSB2 18mm ή Πάνελ Σκυροδέματος 18mm ({project_details['osb2_18mm_count_val']} pcs)")
        if project_details['galvanized_sheet_m2_val'] > 0:
            floor_insulation_details_display_en_gr_text.append(f"• 5mm Galvanized Sheet / 5mm Γαλβανισμένο Φύλλο ({project_details['galvanized_sheet_m2_val']:.2f} m²)")
        floor_insulation_details_display_en_gr_text.append("<i>Note: Insulation thickness can be increased. Ceramic coating can be preferred. (without concrete, special floor system)</i>")
        
        # Malzeme listesi Paragraph olarak eklendi
        interior_insulation_table_data.append([Paragraph('<b>Floor Insulation Materials / Υλικά Μόνωσης Δαπέδου:</b>', styles['NormalBilingual']), Paragraph("<br/>".join(floor_insulation_details_display_en_gr_text), styles['NormalBilingual'])])


    interior_insulation_table = Table(interior_insulation_table_data, colWidths=[60*mm, 110*mm])
    interior_insulation_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(interior_insulation_table)
    elements.append(Spacer(1, 5*mm))

    # Doğramalar (Openings)
    openings_table_data = [
        [Paragraph('<b>Openings / Ανοίγματα</b>', styles['NormalBilingual']), Paragraph(f"Windows: {project_details['window_count']} ({project_details['window_size']} - {project_details['window_door_color']})<br/>Doors: {project_details['door_count']} ({project_details['door_size']} - {project_details['window_door_color']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size']} - {project_details['window_door_color']})<br/>WC Windows: {project_details['wc_window_count']} ({project_details['wc_window_size']} - {project_details['window_door_color']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sliding Doors: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size'] + ' - ' + project_details['window_door_color'] + ')'}", styles['NormalBilingual'])],
    ]
    openings_table = Table(openings_table_data, colWidths=[60*mm, 110*mm])
    openings_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(openings_table)
    elements.append(Spacer(1, 5*mm))

    # --- Sayfa Sonu: Teknik Özellikler Bölümünün Kalanı Yeni Sayfada (GÜNCELLENDİ) ---
    elements.append(PageBreak())

    # Diğer Teknik Özellikler (Mutfak, Duş/WC, Elektrik, Sıhhi Tesisat, Ekstra Genel İlaveler)
    elements.append(Paragraph("ADDITIONAL TECHNICAL FEATURES / ΠΡΟΣΘΕΤΑ ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", styles['Heading'])) # Yeni başlık

    other_features_table_data = [
        [Paragraph('<b>Kitchen / Κουζίνα</b>', styles['NormalBilingual']), Paragraph(project_details['kitchen_type_display_en_gr'], styles['NormalBilingual'])],
    ]
    if project_details['kitchen']:
        other_features_table_data.append([Paragraph('<b>Kitchen Materials / Υλικά Κουζίνας</b>', styles['NormalBilingual']), Paragraph(KITCHEN_MATERIALS_EN, styles['NormalBilingual'])])

    other_features_table_data.append([Paragraph('<b>Shower/WC / Ντους/WC</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['shower']), styles['NormalBilingual'])])
    if project_details['shower']:
        other_features_table_data.append([Paragraph('<b>Shower/WC Materials / Υλικά Ντους/WC</b>', styles['NormalBilingual']), Paragraph(SHOWER_WC_MATERIALS_EN, styles['NormalBilingual'])])

    if project_details['electrical']:
        other_features_table_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph(ELECTRICAL_MATERIALS_EN.strip(), styles['NormalBilingual'])])
    else:
        other_features_table_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph('', styles['NormalBilingual'])])

    if project_details['plumbing']:
        other_features_table_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph(PLUMBING_MATERIALS_EN.strip(), styles['NormalBilingual'])])
    else:
        other_features_table_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph('', styles['NormalBilingual'])])

    # Ekstra Genel İlaveler (koşullu olarak ayrı tabloya)
    extra_general_additions_list_en_gr = []
    if project_details['heating']:
        extra_general_additions_list_en_gr.append(f"Floor Heating: {get_yes_no_empty(project_details['heating'])}")
    if project_details['solar']:
        extra_general_additions_list_en_gr.append(f"Solar System: {get_yes_no_empty(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '')
    if project_details['wheeled_trailer_included']:
        extra_general_additions_list_en_gr.append(f"Wheeled Trailer: {get_yes_no_empty(project_details['wheeled_trailer_included'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer_included'] else '')
    
    if extra_general_additions_list_en_gr:
        other_features_table_data.append([Paragraph('<b>Extra General Additions / Έξτρα Γενικές Προσθήκες</b>', styles['NormalBilingual']), Paragraph("<br/>".join(extra_general_additions_list_en_gr), styles['NormalBilingual'])])


    other_features_table = Table(other_features_table_data, colWidths=[60*mm, 110*mm])
    other_features_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(other_features_table)
    elements.append(Spacer(1, 5*mm))


    elements.append(Paragraph('<b>Estimated Delivery / Εκτιμώμενη Παράδοση</b>', styles['NormalBilingual']))
    elements.append(Paragraph(f"Approx. {project_details['delivery_duration_business_days']} business days / Περίπου {project_details['delivery_duration_business_days']} εργάσιμες ημέρες", styles['NormalBilingual']))
    elements.append(Spacer(1, 8*mm))

    if notes.strip():
        elements.append(Paragraph("CUSTOMER NOTES / ΣΗΜΕΙΩΣΕΙΣ ΠΕΛΑΤΗ", styles['Heading']))
        elements.append(Paragraph(notes, styles['NormalBilingual']))
        elements.append(Spacer(1, 8*mm))

    # --- PRICE & PAYMENT SCHEDULE Section ---
    elements.append(PageBreak())
    final_page_elements = [Spacer(1, 12*mm)]

    final_page_elements.append(Paragraph("PRICE & PAYMENT SCHEDULE / ΤΙΜΗ & ΠΡΟΓΡΑΜΜΑ ΠΛΗΡΩΜΩΝ", styles['Heading']))
    
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
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#3182ce")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#4a5568")),
    ]))
    final_page_elements.append(price_summary_table)
    final_page_elements.append(Spacer(1, 8*mm))

    # KDV Dahildir notu ve garanti açıklaması
    final_page_elements.append(Paragraph("All prices are VAT included / Όλες οι τιμές περιλαμβάνουν ΦΠΑ.", payment_heading_style))
    final_page_elements.append(Paragraph("Our prefabricated living spaces have a 3-year warranty. Hot and cold balance is provided with polyurethane panels, fire class is A quality and energy consumption is A+++. / Οι προκατασκευασμένοι χώροι διαβίωσης μας έχουν 3ετή εγγύηση. Η ισορροπία ζεστού και κρύου επιτυγχάνεται με πάνελ πολυουρεθάνης, η κλάση πυρός είναι Α ποιότητας και η κατανάλωση ενέργειας είναι Α+++.", styles['NormalBilingual']))
    
    final_page_elements.append(Spacer(1, 8*mm))
    final_page_elements.append(Paragraph(f"<b>Estimated Delivery / Εκτιμώμενη Παράδοση:</b> Approx. {project_details['delivery_duration_business_days']} business days / Περίy{project_details['delivery_duration_business_days']} εργάσιμες ημέρες", payment_heading_style))
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
        heating_elements = _create_heating_appendix_elements_en_gr(styles)
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
        name='NormalTR', parent=styles['Normal'], fontSize=8, leading=10,
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
    styles.add(ParagraphStyle(
        name='SectionSubheading', parent=styles['Heading3'], fontSize=9, spaceAfter=3, spaceBefore=7,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568")
    ))

    title_style = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=17, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER,
        spaceAfter=7, fontName=MAIN_FONT, textColor=colors.HexColor("#4a5568")
    )
    
    payment_heading_style = ParagraphStyle(
        name='PaymentHeading', parent=styles['Heading3'], fontSize=9, spaceAfter=3,
        spaceBefore=7, fontName=f"{MAIN_FONT}-Bold"
    )
    signature_style = ParagraphStyle(
        name='Signature', parent=styles['Normal'], fontSize=8, fontName=MAIN_FONT,
        alignment=TA_CENTER, leading=10
    )

    colored_table_header_style_tr = ParagraphStyle(
        name='ColoredTableHeaderTR', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold",
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

    # --- Customer & Project Information Section ---
    elements.append(Paragraph("MÜŞTERİ VE PROJE BİLGİLERİ", styles['Heading']))

    # Oda Konfigürasyonu ve Boyut Bilgileri (Müşteri Bilgileri tablosu üstünde)
    elements.append(Paragraph(f"<b>Oda Konfigürasyonu:</b> {project_details['room_configuration']}", styles['NormalTR']))
    elements.append(Paragraph(f"<b>Boyutlar:</b> {project_details['width']}m x {project_details['length']}m x {project_details['height']}m | <b>Toplam Alan:</b> {project_details['area']:.2f} m² | <b>Yapı Tipi:</b> {project_details['structure_type']}", styles['NormalTR']))
    elements.append(Spacer(1, 8*mm))

    customer_project_table_data_tr = [
        [Paragraph("<b>Adı Soyadı:</b>", styles['NormalTR']), Paragraph(f"{customer_info['name']}", styles['NormalTR'])],
        [Paragraph("<b>Firma:</b>", styles['NormalTR']), Paragraph(f"{customer_info['company'] or ''}", styles['NormalTR'])],
        [Paragraph("<b>Adres:</b>", styles['NormalTR']), Paragraph(f"{customer_info['address'] or ''}", styles['NormalTR'])],
        [Paragraph("<b>Telefon:</b>", styles['NormalTR']), Paragraph(f"{customer_info['phone'] or ''}", styles['NormalTR'])],
        [Paragraph("<b>Kimlik/Pasaport No:</b>", styles['NormalTR']), Paragraph(f"{customer_info['id_no'] or ''}", styles['NormalTR'])],
    ]
    customer_project_table_tr = Table(customer_project_table_data_tr, colWidths=[65*mm, 105*mm])
    customer_project_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(customer_project_table_tr)
    elements.append(Spacer(1, 8*mm))

    # --- Technical Specifications Section ---
    elements.append(Paragraph("TEKNİK ÖZELLİKLER", styles['Heading']))

    def get_var_yok(value):
        return 'Var' if value else 'Yok'
    
    def get_var_yok_empty(value):
        return 'Var' if value else ''

    # Yapı ve Malzemeler
    building_structure_table_data_tr = []
    if project_details['structure_type'] == 'Light Steel':
        building_structure_table_data_tr.append([Paragraph('<b>Yapı Tipi</b>', styles['NormalTR']), Paragraph('Hafif Çelik', styles['NormalTR'])])
        building_structure_table_data_tr.append([Paragraph('<b>Çelik Yapı Detayları</b>', styles['NormalTR']), Paragraph(LIGHT_STEEL_BUILDING_STRUCTURE_TR, styles['NormalTR'])])
        if project_details['plasterboard_interior'] or project_details['plasterboard_all']: # Koşullu ekleme
            building_structure_table_data_tr.append([Paragraph('<b>İç Duvarlar</b>', styles['NormalTR']), Paragraph(INTERIOR_WALLS_DESCRIPTION_TR, styles['NormalTR'])])
        building_structure_table_data_tr.append([Paragraph('<b>Çatı</b>', styles['NormalTR']), Paragraph(ROOF_DESCRIPTION_TR, styles['NormalTR'])])
        building_structure_table_data_tr.append([Paragraph('<b>Dış Duvarlar</b>', styles['NormalTR']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_TR, styles['NormalTR'])])
    else: # Ağır Çelik
        building_structure_table_data_tr.append([Paragraph('<b>Yapı Tipi</b>', styles['NormalTR']), Paragraph('Ağır Çelik', styles['NormalTR'])])
        building_structure_table_data_tr.append([Paragraph('<b>Çelik Yapı Detayları</b>', styles['NormalTR']), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_TR, styles['NormalTR'])])
        building_structure_table_data_tr.append([Paragraph('<b>Çatı</b>', styles['NormalTR']), Paragraph(ROOF_DESCRIPTION_TR, styles['NormalTR'])])
    
    building_materials_table_tr = Table(building_structure_table_data_tr, colWidths=[60*mm, 110*mm])
    building_materials_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(building_materials_table_tr)
    elements.append(Spacer(1, 5*mm))

    # İç Mekan ve Yalıtım
    interior_insulation_table_data_tr = [
        [Paragraph('<b>İç Mekan</b>', styles['NormalTR']), Paragraph(f"Zemin Kaplama: {project_details['floor_covering_type']}.", styles['NormalTR'])],
        [Paragraph('<b>Yalıtım</b>', styles['NormalTR']), Paragraph(f"Zemin Yalıtımı: {get_var_yok_empty(project_details['insulation_floor'])}. Duvar Yalıtımı: {get_var_yok_empty(project_details['insulation_wall'])}.", styles['NormalTR'])],
    ]
    if project_details['insulation_floor']:
        floor_insulation_details_display_tr_text = [FLOOR_INSULATION_MATERIALS_TR]
        if project_details['skirting_length_val'] > 0:
            floor_insulation_details_display_tr_text.append(f"• Süpürgelik ({project_details['skirting_length_val']:.2f} m)")
        if project_details['laminate_flooring_m2_val'] > 0:
            floor_insulation_details_display_tr_text.append(f"• Laminat Parke 12mm ({project_details['laminat_flooring_m2_val']:.2f} m²)")
        if project_details['under_parquet_mat_m2_val'] > 0:
            floor_insulation_details_display_tr_text.append(f"• Parke Altı Şilte 4mm ({project_details['under_parquet_mat_m2_val']:.2f} m²)")
        if project_details['osb2_18mm_count_val'] > 0:
            floor_insulation_details_display_tr_text.append(f"• OSB2 18mm veya Beton Panel 18mm ({project_details['osb2_18mm_count_val']} adet)")
        if project_details['galvanized_sheet_m2_val'] > 0:
            floor_insulation_details_display_tr_text.append(f"• 5mm Galvanizli Sac ({project_details['galvanized_sheet_m2_val']:.2f} m²)")
        floor_insulation_details_display_tr_text.append("<i>Not: Zemin Yalıtımı Kalınlığı artırılabilir. Seramik kaplama tercih edilebilir. (Beton hariç özel zemin sistemi)</i>")
        
        interior_insulation_table_data_tr.append([Paragraph('<b>Zemin Yalıtım Malzemeleri:</b>', styles['NormalTR']), Paragraph("<br/>".join(floor_insulation_details_display_tr_text), styles['NormalTR'])])

    interior_insulation_table_tr = Table(interior_insulation_table_data_tr, colWidths=[60*mm, 110*mm])
    interior_insulation_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(interior_insulation_table_tr)
    elements.append(Spacer(1, 5*mm))

    # Doğramalar
    openings_table_data_tr = [
        [Paragraph('<b>Doğramalar</b>', styles['NormalTR']), Paragraph(f"Pencereler: {project_details['window_count']} adet ({project_details['window_size']} - {project_details['window_door_color']})<br/>Kapılar: {project_details['door_count']} adet ({project_details['door_size']} - {project_details['window_door_color']})<br/>Sürme Kapılar: {project_details['sliding_door_count']} adet ({project_details['sliding_door_size']} - {project_details['window_door_color']})<br/>WC Pencereler: {project_details['wc_window_count']} adet ({project_details['wc_window_size']} - {project_details['window_door_color']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sürme Kapılar: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size'] + ' - ' + project_details['window_door_color'] + ')'}", styles['NormalTR'])],
    ]
    openings_table_tr = Table(openings_table_data_tr, colWidths=[60*mm, 110*mm])
    openings_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(openings_table_tr)
    elements.append(Spacer(1, 5*mm))

    # --- Sayfa Sonu: Teknik Özellikler Bölümünün Kalanı Yeni Sayfada (GÜNCELLENDİ) ---
    elements.append(PageBreak())

    # Diğer Teknik Özellikler (Mutfak, Duş/WC, Elektrik, Sıhhi Tesisat, Ekstra Genel İlaveler)
    elements.append(Paragraph("DİĞER TEKNİK ÖZELLİKLER", styles['Heading'])) # Yeni başlık

    other_features_table_data_tr = [
        [Paragraph('<b>Mutfak</b>', styles['NormalTR']), Paragraph(project_details['kitchen_type_display_tr'], styles['NormalTR'])],
    ]
    if project_details['kitchen']:
        other_features_table_data_tr.append([Paragraph('<b>Mutfak Malzemeleri</b>', styles['NormalTR']), Paragraph(KITCHEN_MATERIALS_TR, styles['NormalTR'])])

    other_features_table_data_tr.append([Paragraph('<b>Duş/WC</b>', styles['NormalTR']), Paragraph(get_var_yok_empty(project_details['shower']), styles['NormalTR'])])
    if project_details['shower']:
        other_features_table_data_tr.append([Paragraph('<b>Duş/WC Malzemeleri</b>', styles['NormalTR']), Paragraph(SHOWER_WC_MATERIALS_TR, styles['NormalTR'])])

    if project_details['electrical']:
        other_features_table_data_tr.append([Paragraph('<b>Elektrik Tesisatı</b>', styles['NormalTR']), Paragraph(ELECTRICAL_MATERIALS_TR.strip(), styles['NormalTR'])])
    else:
        other_features_table_data_tr.append([Paragraph('<b>Elektrik Tesisatı</b>', styles['NormalTR']), Paragraph('', styles['NormalTR'])])

    if project_details['plumbing']:
        other_features_table_data_tr.append([Paragraph('<b>Sıhhi Tesisat</b>', styles['NormalTR']), Paragraph(PLUMBING_MATERIALS_TR.strip(), styles['NormalTR'])])
    else:
        other_features_table_data_tr.append([Paragraph('<b>Sıhhi Tesisat</b>', styles['NormalTR']), Paragraph('', styles['NormalTR'])])

    extra_general_additions_list_tr = []
    if project_details['heating']:
        extra_general_additions_list_tr.append(f"Yerden Isıtma: {get_var_yok_empty(project_details['heating'])}")
    if project_details['solar']:
        extra_general_additions_list_tr.append(f"Güneş Enerjisi: {get_var_yok_empty(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '')
    if project_details['wheeled_trailer_included']:
        extra_general_additions_list_tr.append(f"Tekerlekli Römork: {get_var_yok_empty(project_details['wheeled_trailer_included'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer_included'] else '')

    if extra_general_additions_list_tr:
        other_features_table_data_tr.append([Paragraph('<b>Ekstra Genel İlaveler</b>', styles['NormalTR']), Paragraph("<br/>".join(extra_general_additions_list_tr), styles['NormalTR'])])

    other_features_table_tr = Table(other_features_table_data_tr, colWidths=[60*mm, 110*mm])
    other_features_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(other_features_table_tr)
    elements.append(Spacer(1, 5*mm))

    # Tahmini Teslimat
    elements.append(Paragraph('<b>Tahmini Teslimat</b>', styles['NormalTR']))
    elements.append(Paragraph(f"Yaklaşık {project_details['delivery_duration_business_days']} iş günü", styles['NormalTR']))
    elements.append(Spacer(1, 8*mm))

    if notes.strip():
        elements.append(Paragraph("MÜŞTERİ NOTLARI", styles['Heading']))
        elements.append(Paragraph(notes, styles['NormalTR']))
        elements.append(Spacer(1, 8*mm))

    # --- PRICE & PAYMENT SCHEDULE Section ---
    elements.append(PageBreak())
    final_page_elements = [Spacer(1, 12*mm)]

    final_page_elements.append(Paragraph("FİYAT VE ÖDEME PLANI", styles['Heading']))

    price_table_data_tr = []
    price_table_data_tr.append([
        Paragraph("Ana Ev Bedeli", colored_table_header_style_tr),
        Paragraph(format_currency(house_price), colored_table_header_style_tr)
    ])
    if solar_price > 0:
        price_table_data_tr.append([
            Paragraph("Güneş Enerjisi Sistemi Bedeli", colored_table_header_style_tr),
            Paragraph(format_currency(solar_price), colored_table_header_style_tr)
        ])
    price_table_data_tr.append([
        Paragraph("TOPLAM BEDEL", colored_table_header_style_tr),
        Paragraph(format_currency(total_price), colored_table_header_style_tr)
    ])

    price_summary_table_tr = Table(price_table_data_tr, colWidths=[120*mm, 50*mm])
    price_summary_table_tr.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#3182ce")),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#4a5568")),
    ]))
    final_page_elements.append(price_summary_table_tr)
    final_page_elements.append(Spacer(1, 8*mm))

    # KDV Dahildir notu ve garanti açıklaması
    final_page_elements.append(Paragraph("Tüm fiyatlar KDV dahildir.", payment_heading_style))
    final_page_elements.append(Paragraph("Prefabrik yaşam alanlarımız 3 yıl garantiye sahiptir. Poliüretan panellerle sıcak ve soğuk dengesi sağlanır, yangın sınıfı A kalitedir ve enerji tüketimi A+++'dır.", styles['NormalTR']))
    
    final_page_elements.append(Spacer(1, 8*mm))
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
        payment_data.append([Paragraph("Güneş Enerjisi Sistemi", payment_heading_style), Paragraph(format_currency(solar_price), payment_heading_style)])
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
        heating_elements = _create_heating_appendix_elements_tr(styles)
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
    styles.add(ParagraphStyle(
        name='SubsectionHeading', parent=styles['Heading3'], fontSize=10, spaceBefore=8, spaceAfter=4,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568"), alignment=TA_LEFT
    ))


    header_style = styles['Header']
    section_heading_style = styles['SectionHeading']
    normal_tr_style = styles['NormalTR']
    subsection_heading_style = styles['SubsectionHeading']


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
    elements.append(Paragraph("MALİYET DAĞILIMI", section_heading_style))

    # Helper to create a styled table
    def create_cost_table(data_list, title):
        if not data_list:
            return []
        table_data = [[Paragraph(c, table_header_style) for c in ['Kalem', 'Miktar', 'Birim Fiyat (€)', 'Toplam (€)']]]
        total_section_cost = 0.0
        for item in data_list:
            unit_price_display = format_currency(item['Unit Price (€)']) if isinstance(item['Unit Price (€)'], (int, float)) and item['Unit Price (€)'] != 0.0 else "N/A"
            total_price_display = format_currency(item['Total (€)']) if isinstance(item['Total (€)'], (int, float)) and item['Total (€)'] != 0.0 else "N/A"
            
            table_data.append([
                Paragraph(str(item['Item']), table_cell_style),
                Paragraph(str(item['Quantity']), center_table_cell_style),
                Paragraph(unit_price_display, right_table_cell_style),
                Paragraph(total_price_display, right_table_cell_style)
            ])
            if isinstance(item['Total (€)'], (int, float)):
                total_section_cost += item['Total (€)']
        
        table_data.append([
            Paragraph("<b>TOPLAM</b>", table_header_style),
            "", "",
            Paragraph(format_currency(total_section_cost), table_header_style)
        ])

        table = Table(table_data, colWidths=[65*mm, 30*mm, 35*mm, 40*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.HexColor("#f7fafc"), colors.white]),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#2c5282")),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
        ]))
        return [Paragraph(f"<b>{title}</b>", subsection_heading_style), table, Spacer(1, 5*mm)]

    # Categorize costs for detailed tables
    steel_costs = []
    floor_and_insulation_costs = []
    wall_plasterboard_costs = []
    sandwich_panel_costs = []
    kitchen_costs = []
    shower_wc_costs = []
    electrical_costs = []
    plumbing_costs = []
    door_window_costs = []
    other_general_costs = []

    for item in cost_breakdown_df.to_dict('records'):
        item_name = str(item['Item'])
        if item_name.startswith(("Steel Profile", "Heavy Steel Construction", "Steel Welding Labor")):
            steel_costs.append(item)
        elif item_name.startswith(("Zemin", "Floor", "WC Seramik", "Süpürgelik", "Laminat Parke", "Parke Altı Şilte", "OSB2 18mm", "5mm Galvanizli Sac", "Beton Panel Zemin")):
            floor_and_insulation_costs.append(item)
        elif item_name.startswith(("Alçıpan", "Plasterboard")):
            wall_plasterboard_costs.append(item)
        elif item_name.startswith(("Roof (Sandwich Panel)", "Facade (Sandwich Panel)", "Panel Assembly Labor")):
            sandwich_panel_costs.append(item)
        elif item_name.startswith("Mutfak Kurulumu") or \
             item_name in [FIYATLAR[k] for k in FIYATLAR if k.startswith('kitchen_') and k.endswith('_info')]:
            kitchen_costs.append(item)
        elif item_name.startswith("Duş/WC Kurulumu") or \
             item_name in [FIYATLAR[k] for k in FIYATLAR if k.startswith('wc_') and k.endswith('_info')]:
            shower_wc_costs.append(item)
        elif item_name.startswith("Elektrik Tesisatı") or \
             item_name in [FIYATLAR[k] for k in FIYATLAR if k.startswith('electrical_') and k.endswith('_info')]:
            electrical_costs.append(item)
        elif item_name.startswith("Sıhhi Tesisat") or \
             item_name in [FIYATLAR[k] for k in FIYATLAR if k.startswith('plumbing_') and k.endswith('_info')]:
            plumbing_costs.append(item)
        elif item_name.startswith(("Pencere", "Sürme Cam Kapı", "WC Pencere", "WC Sürme Kapı", "Kapı", "Kapı/Pencere Montaj İşçiliği")):
            door_window_costs.append(item)
        else: # Nakliye, Römork, Solar, Yerden Isıtma ve diğer genel maliyetler
            other_general_costs.append(item)
    
    if steel_costs:
        elements.extend(create_cost_table(steel_costs, "Çelik Yapı & Profil Detayları"))
    
    if floor_and_insulation_costs:
        elements.extend(create_cost_table(floor_and_insulation_costs, "Zemin ve Yalıtım Detayları"))

    if wall_plasterboard_costs:
        elements.extend(create_cost_table(wall_plasterboard_costs, "Duvarlar (Alçıpan) Detayları"))

    # Sandviç Panel Detayları ve sonrası yeni sayfada (GÜNCELLENDİ)
    # Koşul, sadece bu bölümlerden sonra sayfa sonu eklemek için.
    if sandwich_panel_costs or kitchen_costs or shower_wc_costs or electrical_costs or plumbing_costs or door_window_costs or other_general_costs:
        elements.append(PageBreak())

    if sandwich_panel_costs:
        elements.extend(create_cost_table(sandwich_panel_costs, "Sandviç Panel Detayları"))

    if kitchen_costs:
        elements.extend(create_cost_table(kitchen_costs, "Mutfak Detayları"))
    
    if shower_wc_costs:
        elements.extend(create_cost_table(shower_wc_costs, "Duş/WC Detayları"))

    # Elektrik Tesisatı Detayları ve sonrası yeni sayfada (GÜNCELLENDİ)
    if electrical_costs or plumbing_costs or door_window_costs or other_general_costs:
        elements.append(PageBreak())

    if electrical_costs:
        elements.extend(create_cost_table(electrical_costs, "Elektrik Tesisatı Detayları"))

    if plumbing_costs:
        elements.extend(create_cost_table(plumbing_costs, "Sıhhi Tesisat Detayları"))

    if door_window_costs:
        elements.extend(create_cost_table(door_window_costs, "Pencere ve Kapı Detayları"))

    if other_general_costs:
        elements.extend(create_cost_table(other_general_costs, "Diğer Maliyet Kalemleri"))
        
    # ÇELİK PROFİL ANALİZİ KALDIRILDI

    # --- Financials on a NEW PAGE ---
    elements.append(PageBreak())
    elements.append(Paragraph("FİNANSAL ÖZET", section_heading_style))
    financial_data = []
    for _, row in financial_summary_df.iterrows():
        item_cell = Paragraph(str(row['Item']), table_cell_style)
        amount_cell = Paragraph(str(row['Amount (€)']), right_table_cell_style)
        if "TOTAL" in row['Item'] or "Total Cost" in row['Item'] or "TOPLAM" in row['Item'] or "Toplam Maliyet" in row['Item'] or "TOPLAM SATIŞ" in row['Item'] or "Kar" in row['Item'] or "Atık Maliyeti" in row['Item'] or "Vergisi" in row['Item'] or "Giderleri" in row['Item'] or "Kirası" in row['Item'] or "Subtotal" in row['Item']:
             item_cell = Paragraph(f"<b>{row['Item']}</b>", table_cell_style)
             amount_cell = Paragraph(f"<b>{row['Amount (€)']}</b>", right_table_cell_style)
        financial_data.append([item_cell, amount_cell])

    financial_table = Table(financial_data, colWidths=[100*mm, 70*mm])
    financial_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#f7fafc"), colors.white])
    ]))
    elements.append(financial_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_sales_contract_pdf(customer_info, house_sales_price, solar_sales_price, project_details, company_info):
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
    contract_heading_style = ParagraphStyle(
        name='ContractHeading', parent=styles['Heading2'], fontSize=13, spaceAfter=8,
        spaceBefore=12, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_CENTER
    )
    contract_subheading_style = ParagraphStyle(
        name='ContractSubheading', parent=styles['Heading3'], fontSize=10, spaceAfter=5,
        spaceBefore=8, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568")
    )
    contract_normal_style = ParagraphStyle(
        name='ContractNormal', parent=styles['Normal'], fontSize=8, leading=10,
        spaceAfter=4, fontName=MAIN_FONT, alignment=TA_LEFT
    )
    contract_list_style = ParagraphStyle(
        name='ContractList', parent=styles['Normal'], fontSize=8, leading=10,
        spaceAfter=2, leftIndent=8*mm, fontName=MAIN_FONT
    )
    contract_signature_style = ParagraphStyle(
        name='ContractSignature', parent=styles['Normal'], fontSize=8, leading=10,
        alignment=TA_CENTER
    )

    elements = []

    # Title
    elements.append(Paragraph("SALES CONTRACT", contract_heading_style))
    elements.append(Spacer(1, 6*mm))

    # Parties involved (updated with dynamic ID and Company No)
    today_date = datetime.now().strftime('%d')
    today_month = datetime.now().strftime('%B')
    today_year = datetime.now().year
    elements.append(Paragraph(f"This Agreement (\"Agreement\") is entered into as of this {today_date} day of {today_month}, {today_year} by and between,", contract_normal_style))
    elements.append(Paragraph(f"<b>{customer_info['name'].upper()}</b> (I.D. No: <b>{customer_info['id_no']}</b>) hereinafter referred to as the \"Buyer,\" and", contract_normal_style))
    elements.append(Paragraph(f"<b>{company_info['name'].upper()}</b>, Company No. <b>{company_info['company_no']}</b>, with a registered address at {company_info['address']}, hereinafter referred to as the \"Seller.\"", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Subject of the Agreement
    elements.append(Paragraph("Subject of the Agreement:", contract_subheading_style))
    elements.append(Paragraph(f"A. The Seller agrees to complete and deliver to the Buyer the LIGHT STEEL STRUCTURE CONSTRUCTION (Tiny House) being constructed under its coordination at the address specified by the Buyer, in accordance with the specifications detailed in Appendix A.", contract_normal_style))
    elements.append(Paragraph("B. The details of the construction related to the Portable House project will be considered as appendixes to this agreement, which constitute integral parts of the present agreement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Definitions
    elements.append(Paragraph("1. Definitions:", contract_subheading_style))
    elements.append(Paragraph("1.1. \"Completion\" refers to the point at which the Light Steel Structure House is fully constructed, inspected, and ready for delivery.", contract_normal_style))
    elements.append(Paragraph("1.2. \"Delivery Date\" refers to the date on which the property is handed over to the Buyer, at which point the Buyer assumes full ownership and risk.", contract_normal_style))
    elements.append(Paragraph("1.3. \"Force Majeure Event\" means any event beyond the reasonable control of the Seller that prevents the timely delivery of the house, including but not limited to acts of God, war, terrorism, strikes, lockouts, natural disasters, or any other event recognized under law.", contract_normal_style))
    elements.append(Paragraph("1.4. \"House\" means the structure, as described in Appendix A.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

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

    # APPENDIX "A" - Scope of Work (Tablolar halinde düzenlendi)
    elements.append(Paragraph("APPENDIX \"A\" - SCOPE OF WORK", contract_heading_style))
    elements.append(Paragraph("Within the scope of this sales agreement, the specified Light Steel Structure House will have the following features and materials:", contract_normal_style))
    elements.append(Spacer(1, 5*mm))

    def get_yes_no_en(value):
        return 'Yes' if value else ''

    # Boyutlar ve Alan (Dimensions and Area)
    dimensions_area_table_data = []
    dimensions_area_table_data.append([Paragraph("<b>Dimensions and Area:</b>", contract_subheading_style), Paragraph(f"The house has dimensions of {project_details['width']}m x {project_details['length']}m x {project_details['height']}m. It has a total area of {project_details['area']:.2f} m².", contract_normal_style)])
    dimensions_area_table = Table(dimensions_area_table_data, colWidths=[40*mm, 130*mm])
    dimensions_area_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(dimensions_area_table)
    elements.append(Spacer(1, 5*mm))

    # Yapı Malzemeleri (Construction Materials)
    construction_materials_table_data = []
    if project_details['structure_type'] == 'Light Steel':
        construction_materials_table_data.append([Paragraph('<b>Construction Type:</b>', contract_subheading_style), Paragraph('Light Steel', contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Steel Structure Details:</b>', contract_subheading_style), Paragraph(LIGHT_STEEL_BUILDING_STRUCTURE_EN_GR, contract_normal_style)])
        if project_details['plasterboard_interior'] or project_details['plasterboard_all']: # Koşullu ekleme
            construction_materials_table_data.append([Paragraph('<b>Interior Walls:</b>', contract_subheading_style), Paragraph(INTERIOR_WALLS_DESCRIPTION_EN_GR, contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Roof:</b>', contract_subheading_style), Paragraph(ROOF_DESCRIPTION_EN_GR, contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Exterior Walls:</b>', contract_subheading_style), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, contract_normal_style)])
    else: # Heavy Steel
        construction_materials_table_data.append([Paragraph('<b>Construction Type:</b>', contract_subheading_style), Paragraph('Heavy Steel', contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Steel Structure Details:</b>', contract_subheading_style), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR, contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Roof:</b>', contract_subheading_style), Paragraph(ROOF_DESCRIPTION_EN_GR, contract_normal_style)])
    
    construction_materials_table = Table(construction_materials_table_data, colWidths=[40*mm, 130*mm])
    construction_materials_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(construction_materials_table)
    elements.append(Spacer(1, 5*mm))

    # İç Mekan ve Yalıtım (Interior and Insulation)
    interior_insulation_table_data_contract_en = [
        [Paragraph('<b>Interior Covering:</b>', contract_subheading_style), Paragraph(f"12mm plywood will be used for interior flooring. Knauf AquaPanel will be used for both interior and exterior drywall. Inner Wall OSB: {get_yes_no_en(project_details['osb_inner_wall'])}. Interior Walls: Plasterboard {get_yes_no_en(project_details['plasterboard_interior'] or project_details['plasterboard_all'])}.", contract_normal_style)],
        [Paragraph('<b>Insulation:</b>', contract_subheading_style), Paragraph(f"Floor Insulation: {get_yes_no_en(project_details['insulation_floor'])}. Wall Insulation: {get_yes_no_en(project_details['insulation_wall'])}.", contract_normal_style)],
    ]
    # Zemin yalıtım malzemeleri listesi doğrudan yalıtım bölümünün altına (Sözleşme'de de)
    if project_details['insulation_floor']:
        floor_insulation_details_contract_en = [Paragraph("<b>Floor Insulation Materials:</b>", contract_normal_style)]
        if project_details['skirting_length_val'] > 0:
            floor_insulation_details_contract_en.append(Paragraph(f"• Skirting ({project_details['skirting_length_val']:.2f} m)", contract_normal_style))
        if project_details['laminate_flooring_m2_val'] > 0:
            floor_insulation_details_contract_en.append(Paragraph(f"• Laminate Flooring 12mm ({project_details['laminate_flooring_m2_val']:.2f} m²)", contract_normal_style))
        if project_details['under_parquet_mat_m2_val'] > 0:
            floor_insulation_details_contract_en.append(Paragraph(f"• Under Parquet Mat 4mm ({project_details['under_parquet_mat_m2_val']:.2f} m²)", contract_normal_style))
        if project_details['osb2_18mm_count_val'] > 0:
            floor_insulation_details_contract_en.append(Paragraph(f"• OSB2 18mm or Concrete Panel 18mm ({project_details['osb2_18mm_count_val']} pcs)", contract_normal_style))
        if project_details['galvanized_sheet_m2_val'] > 0:
            floor_insulation_details_contract_en.append(Paragraph(f"• 5mm Galvanized Sheet ({project_details['galvanized_sheet_m2_val']:.2f} m²)", contract_normal_style))
        floor_insulation_details_contract_en.append(Paragraph("<i>Note: Insulation thickness can be increased. Ceramic coating can be preferred. (without concrete, special floor system)</i>", contract_normal_style))
        
        interior_insulation_table_data_contract_en.append([Paragraph("<b>Floor Insulation Details:</b>", contract_subheading_style), Paragraph("<br/>".join([p.text for p in floor_insulation_details_contract_en]), contract_normal_style)])

    interior_insulation_table_contract_en = Table(interior_insulation_table_data_contract_en, colWidths=[40*mm, 130*mm])
    interior_insulation_table_contract_en.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(interior_insulation_table_contract_en)
    elements.append(Spacer(1, 5*mm))

    # Zemin Kaplamaları ve Çatı Kaplaması (Floor Coverings and Roof Covering)
    coverings_table_data = [
        [Paragraph("<b>Floor Coverings:</b>", contract_subheading_style), Paragraph(f"{project_details['floor_covering_type']} will be used for floor coverings.", contract_normal_style)],
        [Paragraph("<b>Roof Covering:</b>", contract_subheading_style), Paragraph("100mm Sandwich Panel will be used for the roof.", contract_normal_style)],
    ]
    coverings_table = Table(coverings_table_data, colWidths=[40*mm, 130*mm])
    coverings_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(coverings_table)
    elements.append(Spacer(1, 5*mm))

    # Tesisatlar (Plumbing and Electrical)
    plumbing_electrical_table_data = []
    if project_details['plumbing']:
        plumbing_electrical_table_data.append([Paragraph("<b>Plumbing:</b>", contract_subheading_style), Paragraph(PLUMBING_MATERIALS_EN.strip(), contract_normal_style)])
    if project_details['electrical']:
        plumbing_electrical_table_data.append([Paragraph("<b>Electrical:</b>", contract_subheading_style), Paragraph(ELECTRICAL_MATERIALS_EN.strip(), contract_normal_style)])
    
    if plumbing_electrical_table_data:
        plumbing_electrical_table = Table(plumbing_electrical_table_data, colWidths=[40*mm, 130*mm])
        plumbing_electrical_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        elements.append(plumbing_electrical_table)
        elements.append(Spacer(1, 5*mm))


    # Pencere ve Kapılar (Windows and Doors)
    windows_doors_table_data = [
        [Paragraph("<b>Windows and Doors:</b>", contract_subheading_style), Paragraph(f"Aluminum windows and doors of various sizes will be used, with a height of 2.00m. Color: {project_details['window_door_color']}. The following windows and doors will be included in this project:<br/>Windows: {project_details['window_count']} ({project_details['window_size']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size']})<br/>WC Windows: {project_details['wc_window_count']} ({project_details['wc_window_size']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sliding Doors: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size'] + ')'}<br/>Doors: {project_details['door_count']} ({project_details['door_size']})", contract_normal_style)],
    ]
    windows_doors_table = Table(windows_doors_table_data, colWidths=[40*mm, 130*mm])
    windows_doors_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(windows_doors_table)
    elements.append(Spacer(1, 5*mm))

    # Ekstra Özellikler (Additional Features)
    additional_features_table_data = []
    
    # İç Alçıpan ve OSB koşullu olarak Ekstra İlavelere eklendi (Sözleşme'de de)
    if project_details['plasterboard_interior'] or project_details['plasterboard_all']:
        additional_features_table_data.append([Paragraph("<b>Interior Plasterboard:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['plasterboard_interior'] or project_details['plasterboard_all']), contract_normal_style)])
    if project_details['osb_inner_wall']:
        additional_features_table_data.append([Paragraph("<b>Inner Wall OSB Material:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['osb_inner_wall']), contract_normal_style)])
    
    # Mutfak ve Duş/WC (eğer pakete dahil değilse ve seçiliyse)
    if project_details['kitchen']:
        additional_features_table_data.append([Paragraph("<b>Kitchen:</b>", contract_subheading_style), Paragraph(project_details['kitchen_type_display_en_gr'], contract_normal_style)])
    if project_details['shower']:
        additional_features_table_data.append([Paragraph("<b>Shower/WC:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['shower']), contract_normal_style)])
    
    # Diğer Opsiyonel Özellikler (Aether Living'e özel olanlar dahil)
    if project_details['heating']:
        additional_features_table_data.append([Paragraph("<b>Floor Heating:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['heating']), contract_normal_style)])
    if project_details['solar']:
        additional_features_table_data.append([Paragraph("<b>Solar System:</b>", contract_subheading_style), Paragraph(f"{get_yes_no_en(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '', contract_normal_style)])
    if project_details['wheeled_trailer_included']:
        additional_features_table_data.append([Paragraph("<b>Wheeled Trailer:</b>", contract_subheading_style), Paragraph(f"{get_yes_no_en(project_details['wheeled_trailer_included'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer_included'] else '', contract_normal_style)])
    
    # Aether Living'e özel eklenenler (UI'dan kaldırılsa da raporlarda yer almalı)
    if project_details['smart_home_systems_option']:
        additional_features_table_data.append([Paragraph("<b>Smart Home Systems:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['smart_home_systems_option']), contract_normal_style)])
    if project_details['white_goods_fridge_tv_option']:
        additional_features_table_data.append([Paragraph("<b>White Goods (Fridge, TV):</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['white_goods_fridge_tv_option']), contract_normal_style)])
    if project_details['sofa_option']:
        additional_features_table_data.append([Paragraph("<b>Sofa:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['sofa_option']), contract_normal_style)])
    if project_details['security_camera_option']:
        additional_features_table_data.append([Paragraph("<b>Security Camera Pre-Installation:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['security_camera_option']), contract_normal_style)])
    if project_details['exterior_cladding_m2_option']:
        additional_features_table_data.append([Paragraph("<b>Exterior Cladding:</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['exterior_cladding_m2_val']:.2f} m²)", contract_normal_style)])
    if project_details['bedroom_set_option']:
        additional_features_table_data.append([Paragraph("<b>Bedroom Set:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['bedroom_set_option']), contract_normal_style)])
    if project_details['terrace_laminated_wood_flooring_option']:
        additional_features_table_data.append([Paragraph("<b>Treated Pine Floor (Terrace Option):</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['terrace_laminated_wood_flooring_m2_val']:.2f} m²)", contract_normal_style)])
    if project_details['porcelain_tiles_option']:
        additional_features_table_data.append([Paragraph("<b>Porcelain Tiles:</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['porcelain_tiles_m2_val']:.2f} m²)", contract_normal_style)])
    if project_details['concrete_panel_floor_option']:
        additional_features_table_data.append([Paragraph("<b>Concrete Panel Floor:</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['concrete_panel_floor_m2_val']:.2f} m²)", contract_normal_style)])
    if project_details['premium_faucets_option']:
        additional_features_table_data.append([Paragraph("<b>Premium Faucets:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['premium_faucets_option']), contract_normal_style)])
    if project_details['integrated_fridge_option']:
        additional_features_table_data.append([Paragraph("<b>Integrated Refrigerator:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['integrated_fridge_option']), contract_normal_style)])
    if project_details['designer_furniture_option']:
        additional_features_table_data.append([Paragraph("<b>Integrated Custom Design Furniture:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['designer_furniture_option']), contract_normal_style)])
    if project_details['italian_sofa_option']:
        additional_features_table_data.append([Paragraph("<b>Italian Sofa:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['italian_sofa_option']), contract_normal_style)])
    if project_details['inclass_chairs_option']:
        additional_features_table_data.append([Paragraph("<b>Inclass Chairs:</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['inclass_chairs_count']} pcs)", contract_normal_style)])
    if project_details['brushed_granite_countertops_option']:
        additional_features_table_data.append([Paragraph("<b>Brushed Granite Countertops:</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['brushed_granite_countertops_m2_val']:.2f} m²)", contract_normal_style)])
    if project_details['exterior_wood_cladding_m2_option']:
        additional_features_table_data.append([Paragraph("<b>Exterior Wood Cladding (Lambiri):</b>", contract_subheading_style), Paragraph(f"Yes ({project_details['exterior_wood_cladding_m2_val']:.2f} m²)", contract_normal_style)])


    if additional_features_table_data:
        additional_features_table = Table(additional_features_table_data, colWidths=[60*mm, 110*mm])
        additional_features_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
        elements.append(additional_features_table)
        elements.append(Spacer(1, 5*mm))

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
    
    # Aether Living | Loft Serisi Paket Seçimi PROJE DETAYLARI içine alındı
    aether_package_choice = st.radio(
        "Aether Living | Loft Serisi Paket Seçimi:",
        ['Yok', 'Aether Living | Loft Standard (BASICS)', 'Aether Living | Loft Premium (ESSENTIAL)', 'Aether Living | Loft Elite (LUXURY)'],
        key="aether_package_select"
    )

    col1, col2 = st.columns(2)
    with col1:
        structure_type_val = st.radio("Yapı Tipi:", ['Light Steel', 'Heavy Steel'], key="structure_type_radio")
        welding_labor_type_val = st.selectbox("Çelik Kaynak İşçiliği:", ['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'], key="welding_labor_select")
        
        if welding_labor_type_val == 'Standard Welding (160€/m²)':
            welding_labor_option_val = 'standard'
        else:
            welding_labor_option_val = 'trmontaj'

        plasterboard_interior_disabled = (structure_type_val == 'Heavy Steel')
        plasterboard_all_disabled = (structure_type_val == 'Light Steel')

        plasterboard_interior_option_val = st.checkbox("İç Alçıpan Dahil Et", value=True, disabled=plasterboard_interior_disabled, key="pb_int_checkbox")
        plasterboard_all_option_val = st.checkbox("İç ve Dış Alçıpan Dahil Et", value=False, disabled=plasterboard_all_disabled, key="pb_all_checkbox")
        
        if structure_type_val == 'Light Steel':
            plasterboard_all_calc = False 
            plasterboard_interior_calc = plasterboard_interior_option_val
        elif structure_type_val == 'Heavy Steel':
            plasterboard_interior_calc = False
            plasterboard_all_calc = plasterboard_all_option_val
        else:
            plasterboard_interior_calc = plasterboard_interior_option_val
            plasterboard_all_calc = plasterboard_all_option_val

        osb_inner_wall_disabled = not (plasterboard_interior_calc or plasterboard_all_calc)
        osb_inner_wall_option_val = st.checkbox("İç Duvar OSB Malzemesi Dahil Et", value=True, disabled=osb_inner_wall_disabled, key="osb_inner_checkbox")
        
        if osb_inner_wall_disabled:
            osb_inner_wall_calc = False
        else:
            osb_inner_wall_calc = osb_inner_wall_option_val


    with col2:
        width_val = st.number_input("Genişlik (m):", value=10.0, step=0.1, key="width_input")
        length_val = st.number_input("Uzunluk (m):", value=8.0, step=0.1, key="length_input")
        height_val = st.number_input("Yükseklik (m):", value=2.6, step=0.1, key="height_input")
        
        room_config_options = [
            'Empty Model', 
            '1 Room', 
            '1 Room + Shower / WC', 
            '1 Room + Kitchen',
            '1 Room + Kitchen + WC',
            '1 Room + Shower / WC + Kitchen', 
            '2 Rooms + Shower / WC + Kitchen',
            '3 Rooms + 2 Showers / WC + Kitchen'
        ]
        room_config_val = st.selectbox("Oda Konfigürasyonu:", room_config_options, key="room_config_select")
        
        facade_sandwich_panel_disabled = (structure_type_val == 'Light Steel')
        facade_sandwich_panel_option_val = st.checkbox("Dış Cephe Sandviç Panel Dahil Et (Ağır Çelik için)", value=True, disabled=facade_sandwich_panel_disabled, key="facade_panel_checkbox")
        
        if facade_sandwich_panel_disabled:
            facade_sandwich_panel_calc = False
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
        profile_120x60x5mm_count_val = st.number_input("120x60x5mm Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="p120x60x5mm_input")
    with col8:
        profile_HEA160_count_val = st.number_input("HEA160 Adet:", value=0, min_value=0, disabled=steel_profile_disabled, key="pHEA160_input")

    # --- Windows and Doors Section ---
    st.markdown("<div class='section-title'>PENCERELER VE KAPILAR</div>", unsafe_allow_html=True)
    col9, col10, col11 = st.columns(3)
    with col9:
        window_input_val = st.number_input("Pencere Adedi:", value=4, min_value=0, key="window_count_input")
    with col10:
        window_size_val = st.text_input("Pencere Boyutu:", value="100x100 cm", key="window_size_input")
    with col11:
        window_door_color_val = st.selectbox("Pencere/Kapı Rengi:", ['White', 'Black', 'Grey'], key="window_door_color_select")

    col_door1, col_door2, col_door3 = st.columns(3)
    with col_door1:
        sliding_door_input_val = st.number_input("Sürme Cam Kapı Adedi:", value=0, min_value=0, key="sliding_door_count_input")
    with col_door2:
        sliding_door_size_val = st.text_input("Sürme Kapı Boyutu:", value="200x200 cm", key="sliding_door_size_input")
    with col_door3:
        pass

    col_wc_win1, col_wc_win2, col_wc_win3 = st.columns(3)
    with col_wc_win1:
        wc_window_input_val = st.number_input("WC Pencere Adedi:", value=1, min_value=0, key="wc_window_count_input")
    with col_wc_win2:
        wc_window_size_val = st.text_input("WC Pencere Boyutu:", value="60x50 cm", key="wc_window_size_input")
    with col_wc_win3:
        pass

    col_wc_slid1, col_wc_slid2, col_wc_slid3 = st.columns(3)
    with col_wc_slid1:
        wc_sliding_door_input_val = st.number_input("WC Sürme Kapı Adedi:", value=0, min_value=0, key="wc_sliding_door_count_input")
    with col_wc_slid2:
        wc_sliding_door_size_val = st.text_input("WC Sürme Kapı Boyutu:", value="140x70 cm", key="wc_sliding_door_size_input")
    with col_wc_slid3:
        pass
    
    col_door_main1, col_door_main2, col_door_main3 = st.columns(3)
    with col_door_main1:
        door_input_val = st.number_input("Kapı Adedi:", value=2, min_value=0, key="door_count_input")
    with col_door_main2:
        door_size_val = st.text_input("Kapı Boyutu:", value="90x210 cm", key="door_size_input")
    with col_door_main3:
        pass

    # --- Additional Equipment Section ---
    st.markdown("<div class='section-title'>EK DONANIMLAR</div>", unsafe_allow_html=True)
    
    # Mutfak seçeneğini radio butonları ile değiştir (paket seçimine göre varsayılan değer)
    kitchen_choice = st.radio("Mutfak Tipi Seçimi:", ['Mutfak Yok', 'Standart Mutfak', 'Special Design Mutfak'], index=['Mutfak Yok', 'Standart Mutfak', 'Special Design Mutfak'].index(default_kitchen_choice_radio), key="kitchen_type_radio_select")
    
    kitchen_input_val = False
    kitchen_cost_val = 0.0
    kitchen_type_display_en_gr = "No"
    kitchen_type_display_tr = "Yok"

    if kitchen_choice == 'Standart Mutfak':
        kitchen_input_val = True
        kitchen_cost_val = FIYATLAR["kitchen_installation_standard_piece"]
        kitchen_type_display_en_gr = "Yes (Standard)"
        kitchen_type_display_tr = "Var (Standart)"
    elif kitchen_choice == 'Special Design Mutfak':
        kitchen_input_val = True
        kitchen_cost_val = FIYATLAR["kitchen_installation_special_piece"]
        kitchen_type_display_en_gr = "Yes (Special Design)"
        kitchen_type_display_tr = "Var (Özel Tasarım)"
    
    shower_input_val = st.checkbox("Duş/WC Dahil Et", value=default_shower_val, key="shower_checkbox")
    
    col_ceramic1, col_ceramic2 = st.columns(2)
    with col_ceramic1:
        wc_ceramic_input_val = st.checkbox("WC Seramik Zemin/Duvar", value=default_wc_ceramic_val, key="wc_ceramic_checkbox")
    with col_ceramic2:
        wc_ceramic_area_disabled = not wc_ceramic_input_val
        wc_ceramic_area_val = st.number_input("WC Seramik Alanı (m²):", value=0.0, step=0.1, min_value=0.0, disabled=wc_ceramic_area_disabled, key="wc_ceramic_area_input")
    
    electrical_installation_input_val = st.checkbox("Elektrik Tesisatı (Malzemelerle)", value=default_electrical_val, key="electrical_checkbox")
    plumbing_installation_input_val = st.checkbox("Sıhhi Tesisat (Malzemelerle)", value=default_plumbing_val, key="plumbing_checkbox")
    
    # Zemin yalıtım malzemeleri girişleri
    st.markdown("---")
    st.subheader("Zemin Yalıtımı ve Malzemeleri")
    insulation_floor_option_val = st.checkbox("Zemin Yalıtımı Dahil Et (5€/m²)", value=default_insulation_floor_val, key="floor_insulation_checkbox")
    
    floor_insulation_material_disabled = not insulation_floor_option_val

    col_floor_mats = st.columns(3)
    with col_floor_mats[0]:
        skirting_count_val = st.number_input(f"Süpürgelik ({FIYATLAR['skirting_meter_price']}€/m) Uzunluğu (m):", value=0.0, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="skirting_input")
    with col_floor_mats[1]:
        laminate_flooring_m2_val = st.number_input(f"Laminat Parke 12mm ({FIYATLAR['laminate_flooring_m2_price']}€/m²) Alanı (m²):", value=0.0, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="laminate_flooring_input")
    with col_floor_mats[2]:
        under_parquet_mat_m2_val = st.number_input(f"Parke Altı Şilte 4mm ({FIYATLAR['under_parquet_mat_m2_price']}€/m²) Alanı (m²):", value=0.0, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="under_parquet_mat_input")
    
    col_floor_mats2 = st.columns(3)
    with col_floor_mats2[0]:
        osb2_18mm_count_val = st.number_input(f"OSB2 18mm/Beton Panel ({FIYATLAR['osb2_18mm_piece_price']}€/adet) Adet:", value=0, min_value=0, disabled=floor_insulation_material_disabled, key="osb2_input")
    with col_floor_mats2[1]:
        galvanized_sheet_m2_val = st.number_input(f"5mm Galvanizli Sac ({FIYATLAR['galvanized_sheet_m2_price']}€/m²) Alanı (m²):", value=0.0, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="galvanized_sheet_input")
    with col_floor_mats2[2]:
        pass

    insulation_wall_option_val = st.checkbox("Duvar Yalıtımı Dahil Et (10€/m²)", value=default_insulation_wall_val, key="wall_insulation_checkbox")
    
    st.markdown("---")

    transportation_input_val = st.checkbox("Nakliye Dahil Et (350€)", value=False, key="transportation_checkbox")
    heating_option_val = st.checkbox("Yerden Isıtma Dahil Et (50€/m²)", value=default_heating_val, key="heating_checkbox")
    solar_option_val = st.checkbox("Güneş Enerjisi Sistemi", value=default_solar_val, key="solar_checkbox")
    
    floor_covering_option_val = st.selectbox("Zemin Kaplama Tipi:", ['Laminate Parquet', 'Ceramic'], index=['Laminate Parquet', 'Ceramic'].index(default_floor_covering), key="floor_covering_select")

    col14, col15 = st.columns(2)
    with col14:
        solar_capacity_val = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not solar_option_val, key="solar_capacity_select")
    with col15:
        solar_price_val = solar_capacity_val * FIYATLAR['solar_per_kw'] if solar_option_val else 0.0
        st.number_input("Güneş Enerjisi Fiyatı (€):", value=solar_price_val, disabled=True, key="solar_price_display")

    wheeled_trailer_option_val = st.checkbox("Tekerlekli Römork", value=default_wheeled_trailer_val, key="trailer_checkbox")
    wheeled_trailer_price_input_val = st.number_input("Römork Fiyatı (€):", value=0.0, step=0.1, disabled=not wheeled_trailer_option_val, key="trailer_price_input")

    # --- Financial Settings Section ---
    st.markdown("<div class='section-title'>FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
    profit_rate_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
    profit_rate_val_tuple = st.selectbox("Kar Oranı:", options=profit_rate_options, format_func=lambda x: x[0], index=3, key="profit_rate_select")
    profit_rate_val = profit_rate_val_tuple[1]
    st.markdown(f"<div>KDV Oranı: {VAT_RATE*100:.0f}% (Sabit)</div>", unsafe_allow_html=True)

    # --- Customer Notes Section ---
    st.markdown("<div class='section-title'>MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR</div>", unsafe_allow_html=True)
    customer_notes_val = st.text_area("Müşteri Notları:", key="customer_notes_textarea")

    # --- PDF Language Selection ---
    pdf_language_selector_val_tuple = st.selectbox("Teklif PDF Dili:", options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')], format_func=lambda x: x[0], key="pdf_language_select")
    pdf_language_selector_val = pdf_language_selector_val_tuple[1]

    # --- Calculate Button and Results Display ---
    if st.button("Hesapla ve Teklifleri Oluştur"):
        try:
            # --- Calculation Logic ---
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
            
            # Aether Living Paket Fiyatlandırması ve Malzeme Hesaplaması
            # Her paketin kendi içinde standartları ve ekstra yükseltmeleri olacak
            if aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
                # Yapı (Metal iskelet, koruyucu otomotiv boyası)
                # Buraya varsayılan metal iskelet ve boya maliyetleri eklenmeli.
                # Varsayılan Light Steel profillerini kullanıyoruz
                basics_100x100_count = math.ceil(floor_area * (12 / 27.0))
                basics_50x50_count = math.ceil(floor_area * (6 / 27.0))
                
                if basics_100x100_count > 0:
                    costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (100x100x3)', 'Quantity': f"{basics_100x100_count} adet ({basics_100x100_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(basics_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                if basics_50x50_count > 0:
                    costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (50x50x2)', 'Quantity': f"{basics_50x50_count} adet ({basics_50x50_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(basics_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                costs.append({'Item': FIYATLAR['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

                # Dış/İç Kaplamalar (60mm EPS veya Poliüretan Sandviç Paneller (beyaz))
                sandwich_panel_60mm_cost = calculate_rounded_up_cost((wall_area + roof_area) * FIYATLAR["sandwich_panel_m2"])
                costs.append({'Item': FIYATLAR['60mm_eps_sandwich_panel_info'], 'Quantity': f"{wall_area + roof_area:.2f} m²", 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': sandwich_panel_60mm_cost})
                
                # Zemin (Galvanizli sac, yalıtım, Kontraplak/OSB zemin paneli, 12mm Laminat Parke)
                # Bu kısım mevcut zemin yalıtımı ve kaplama hesaplamalarıyla çakışıyor, bu yüzden paket seçildiğinde çakışanları varsayılan olarak kabul etmeliyiz
                if not insulation_floor_option_val: # Eğer kullanıcı yerden yalıtımı seçmediyse paketten varsayılanı ekle
                     costs.append({'Item': FIYATLAR['insulation_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': calculate_rounded_up_cost(floor_area * FIYATLAR["insulation_per_m2"])})
                
                costs.append({'Item': FIYATLAR['galvanized_sheet_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["galvanized_sheet_m2_price"], 'Total (€)': calculate_rounded_up_cost(floor_area * FIYATLAR["galvanized_sheet_m2_price"])})
                costs.append({'Item': FIYATLAR['plywood_osb_floor_panel_info'], 'Quantity': f"{plywood_pieces_needed} adet", 'Unit Price (€)': FIYATLAR["plywood_piece"], 'Total (€)': calculate_rounded_up_cost(plywood_pieces_needed * FIYATLAR["plywood_piece"])})
                costs.append({'Item': FIYATLAR['12mm_laminate_parquet_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["laminate_flooring_m2_price"], 'Total (€)': calculate_rounded_up_cost(floor_area * FIYATLAR["laminate_flooring_m2_price"])})
                
                # Mutfak/Banyo (İndüksiyonlu ocak, elektrikli batarya, mutfak evyesi, tam fonksiyonel banyo armatürleri)
                costs.append({'Item': FIYATLAR['induction_hob_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['electric_faucet_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['kitchen_sink_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['fully_functional_bathroom_fixtures_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['kitchen_bathroom_countertops_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                # Bu maliyetler genel mutfak/banyo kurulumuna yansıtılacak (UI'da seçiliyse)

            elif aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
                # Premium pakete özel eklemeler (Standard özelliklere ek olarak)
                # Dış/İç Kaplamalar (Yüksek performanslı 100mm EPS veya Poliüretan İzotermik Paneller)
                sandwich_panel_100mm_cost = calculate_rounded_up_cost((wall_area + roof_area) * FIYATLAR["100mm_eps_isothermal_panel_info"]) # burası hata veriyor
                costs.append({'Item': FIYATLAR['100mm_eps_isothermal_panel_info'], 'Quantity': f"{wall_area + roof_area:.2f} m²", 'Unit Price (€)': FIYATLAR["100mm_eps_isothermal_panel_info"], 'Total (€)': sandwich_panel_100mm_cost})
                
                # Zemin: İşlenmiş çam zemin kaplaması (teras seçeneği) veya porselen fayans
                if terrace_laminated_wood_flooring_option_val:
                    terrace_laminated_cost = calculate_rounded_up_cost(floor_area * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'])
                    costs.append({'Item': FIYATLAR['treated_pine_floor_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_laminated_cost})
                elif porcelain_tiles_option_val:
                    porcelain_tiles_cost = calculate_rounded_up_cost(floor_area * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']))
                    costs.append({'Item': FIYATLAR['porcelain_tiles_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']), 'Total (€)': porcelain_tiles_cost})
                else: # Varsayılan laminat parke
                    laminate_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["laminate_flooring_m2_price"])
                    costs.append({'Item': FIYATLAR['12mm_laminate_parquet_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["laminate_flooring_m2_price"], 'Total (€)': laminate_cost})
                
                # Mobilyalar: Destekleyici mobilyalı yatak başlığı
                if bedroom_set_option_val: # Checkbox ile kontrol eklendi
                    costs.append({'Item': FIYATLAR['supportive_headboard_furniture_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['bedroom_set_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['bedroom_set_total_price'])})
                
                # Tezgahlar: Fırçalanmış gri kale granit
                if brushed_granite_countertops_option_val:
                    granite_area_default = floor_area / 10 # Örnek m2
                    granite_cost = calculate_rounded_up_cost(granite_area_default * FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'])
                    costs.append({'Item': FIYATLAR['brushed_grey_granite_countertops_info'], 'Quantity': f"{granite_area_default:.2f} m²", 'Unit Price (€)': FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'], 'Total (€)': granite_cost})

            elif aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                # Elite pakete özel eklemeler (Premium özellikleri de içerir)
                # Dış Cephe (Knauf Aquapanel, vb.)
                if exterior_cladding_m2_option_val:
                    exterior_cladding_cost_elite = calculate_rounded_up_cost(wall_area * FIYATLAR['exterior_cladding_price_per_m2'])
                    costs.append({'Item': FIYATLAR['knauf_aquapanel_gypsum_board_info'], 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_price_per_m2'], 'Total (€)': exterior_cladding_cost_elite})
                    costs.append({'Item': FIYATLAR['eps_styrofoam_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                    costs.append({'Item': FIYATLAR['knauf_mineralplus_insulation_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                
                # Dış cephe ahşap kaplama (Lambiri)
                if exterior_wood_cladding_m2_option_val and exterior_wood_cladding_m2_val > 0:
                    wood_cladding_cost = calculate_rounded_up_cost(exterior_wood_cladding_m2_val * FIYATLAR['exterior_wood_cladding_m2_price'])
                    costs.append({'Item': FIYATLAR['exterior_wood_cladding_lambiri_info'], 'Quantity': f"{exterior_wood_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'], 'Total (€)': wood_cladding_cost})

                # İç Duvarlar (Knauf Guardex Alçıpan, saten sıva ve boya)
                if plasterboard_interior_calc or plasterboard_all_calc:
                    costs.append({'Item': FIYATLAR['knauf_guardex_gypsum_board_info'], 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_material_m2"], 'Total (€)': calculate_rounded_up_cost(plasterboard_total_area * FIYATLAR["plasterboard_material_m2"])})
                    costs.append({'Item': FIYATLAR['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

                # Zemin: Beton panel zemin (isteğe bağlı yerden ısıtma)
                if concrete_panel_floor_option_val:
                    concrete_panel_cost = calculate_rounded_up_cost(floor_area * FIYATLAR['concrete_panel_floor_price_per_m2'])
                    costs.append({'Item': FIYATLAR['concrete_panel_floor_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})
                if heating_option_val:
                    total_heating_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["floor_heating_m2"])
                    costs.append({'Item': 'Yerden Isıtma Sistemi', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["floor_heating_m2"], 'Total (€)': total_heating_cost})
                
                # Armatürler: Premium bataryalar
                if premium_faucets_option_val:
                    costs.append({'Item': FIYATLAR['premium_faucets_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['premium_faucets_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['premium_faucets_total_price'])})

                # Yükseltilmiş mutfak cihazları (örn. entegre buzdolabı) - Zaten beyaz eşya içinde değerlendiriliyor, ayrıca eklenmeyecek.
                # if integrated_fridge_option_val: # Ayrı fiyatlandırılmıyor
                #     costs.append({'Item': FIYATLAR['integrated_refrigerator_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

                # Mobilyalar: Entegre özel tasarım mobilyalar, seçkin oturma grupları
                if designer_furniture_option_val:
                    costs.append({'Item': FIYATLAR['integrated_custom_furniture_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['designer_furniture_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['designer_furniture_total_price'])})
                if italian_sofa_option_val:
                    costs.append({'Item': FIYATLAR['italian_sofa_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['italian_sofa_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['italian_sofa_total_price'])})
                if inclass_chairs_option_val and inclass_chairs_count_val > 0: # Adet girişi kontrol edildi
                    inclass_chairs_cost = calculate_rounded_up_cost(inclass_chairs_count_val * FIYATLAR['inclass_chairs_unit_price'])
                    costs.append({'Item': FIYATLAR['inclass_chairs_info'], 'Quantity': f"{inclass_chairs_count_val} adet", 'Unit Price (€)': FIYATLAR['inclass_chairs_unit_price'], 'Total (€)': inclass_chairs_cost})
                
                # Teknoloji: Akıllı ev sistemleri, gelişmiş güvenlik kamerası ön kurulumu
                if smart_home_systems_option_val:
                    costs.append({'Item': FIYATLAR['smart_home_systems_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['smart_home_systems_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['smart_home_systems_total_price'])})
                if security_camera_option_val:
                    costs.append({'Item': FIYATLAR['security_camera_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['security_camera_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['security_camera_total_price'])})
                
                # Premium paket ve Elite paketin diğer ortak/üst üste binen özellikleri (burada ayrı ayrı belirtilebilir)
                # Örn: Premium paketin içindeki 100mm panellerin maliyeti Elite'te de geçerli olmalı
                # Bu kısım, paket seçimi mantığının en karmaşık yeri, dikkatli yönetilmeli.
                # Şu anki mantık, her paketin kendi malzemelerini eklemesi üzerine kurulu.
                # Eğer Elite Premium'u içeriyorsa, Premium'un eklediği kalemleri Elite'te de eklememiz gerekir.
                # Ancak burada doğrudan eklenen kalemler, daha sonra costs listesinde toplanıyor.
                # Çözüm: Paket seçimi yapıldığında, ilgili default_val'ler True olarak ayarlandığı için,
                # aşağıdaki genel maliyet hesaplamaları bu durumları otomatik olarak dahil edecek.


            # Mevcut hesaplama mantığından kalanlar (paket seçilmediyse veya paketlere ek olarak seçildiyse)

            # Çelik Yapı Hesaplamaları (Paket dışındaki manuel girişler)
            if aether_package_choice == 'Yok': # Sadece paket seçilmediyse manuel girişleri kullan
                if structure_type_val == 'Heavy Steel':
                    total_structure_price = calculate_rounded_up_cost(floor_area * FIYATLAR["heavy_steel_m2"])
                    costs.append({'Item': 'Heavy Steel Construction (Structure)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["heavy_steel_m2"], 'Total (€)': total_structure_price})
                    selected_welding_labor_price = FIYATLAR[f"welding_labor_m2_{welding_labor_option_val}"]
                    total_welding_labor_price = calculate_rounded_up_cost(floor_area * selected_welding_labor_price)
                    costs.append({'Item': f'Steel Welding Labor ({welding_labor_option_val.upper()})', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': selected_welding_labor_price, 'Total (€)': total_welding_labor_price})
                else: # Light Steel
                    current_100x100_count = profile_100x100_count_val
                    current_100x50_count = profile_100x50_count_val
                    current_40x60_count = profile_40x60_count_val
                    current_50x50_count = profile_50x50_count_val
                    current_120x60x5mm_count = profile_120x60x5mm_count_val # Yeni profil
                    current_hea160_count = profile_HEA160_count_val

                    manual_profile_counts = {
                        "100x100x3": current_100x100_count, "100x50x3": current_100x50_count,
                        "40x60x2": current_40x60_count, "50x50x2": current_50x50_count,
                        "120x60x5mm": current_120x60x5mm_count, "HEA160": current_hea160_count,
                    }
                    default_piece_length = 6.0
                    for profile_type_key, piece_count in manual_profile_counts.items():
                        if piece_count > 0:
                            profile_dict_key = f"steel_profile_{profile_type_key.replace('.', '')}" # Anahtar düzeltme
                            unit_price_6m_piece = FIYATLAR.get(profile_dict_key)
                            if unit_price_6m_piece is None: continue
                            total_price = calculate_rounded_up_cost(piece_count * unit_price_6m_piece)
                            report_length_meters = piece_count * default_piece_length
                            profile_analysis_details.append({'Profile Type': profile_type_key, 'Count': piece_count, 'Unit Price (€)': unit_price_6m_piece, 'Total (€)': total_price})
                            costs.append({'Item': f"Steel Profile ({profile_type_key})", 'Quantity': f"{piece_count} pieces ({report_length_meters:.1f}m)", 'Unit Price (€)': unit_price_6m_piece, 'Total (€)': total_price})
                    selected_welding_labor_price = FIYATLAR[f"welding_labor_m2_{welding_labor_option_val}"]
                    total_welding_labor_price = calculate_rounded_up_cost(floor_area * selected_welding_labor_price)
                    costs.append({'Item': f'Steel Welding Labor ({welding_labor_option_val.upper()})', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': selected_welding_labor_price, 'Total (€)': total_welding_labor_price})

            # Sandviç Panel ve Montaj (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok':
                total_price = calculate_rounded_up_cost(roof_area * FIYATLAR["sandwich_panel_m2"])
                costs.append({'Item': 'Roof (Sandwich Panel)', 'Quantity': f'{roof_area:.2f} m²', 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': total_price})
                if structure_type_val == 'Light Steel' or (structure_type_val == 'Heavy Steel' and facade_sandwich_panel_calc):
                    total_price = calculate_rounded_up_cost(wall_area * FIYATLAR["sandwich_panel_m2"])
                    costs.append({'Item': 'Facade (Sandwich Panel)', 'Quantity': f'{wall_area:.2f} m²', 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': total_price})
                total_panel_assembly_area = wall_area + roof_area
                total_price = calculate_rounded_up_cost(total_panel_assembly_area * FIYATLAR["panel_assembly_labor_m2"])
                costs.append({'Item': "Panel Assembly Labor", 'Quantity': f"{(total_panel_assembly_area):.2f} m²", 'Unit Price (€)': FIYATLAR["panel_assembly_labor_m2"], 'Total (€)': total_price})
            
            # İç Duvar OSB (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and osb_inner_wall_calc:
                inner_wall_area_for_osb_calc = (wall_area / 2)
                osb_area_to_cover = inner_wall_area_for_osb_calc + roof_area
                osb_pieces_needed = math.ceil(osb_area_to_cover / OSB_PANEL_AREA_M2)
                if osb_pieces_needed > 0:
                    costs.append({'Item': 'Inner Wall OSB Material', 'Quantity': f"{osb_pieces_needed} pieces ({osb_area_to_cover:.2f} m²)", 'Unit Price (€)': FIYATLAR["osb_piece"], 'Total (€)': calculate_rounded_up_cost(osb_pieces_needed * FIYATLAR["osb_piece"])})

            # Alçıpan (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok':
                plasterboard_total_area = 0
                plasterboard_labor_m2 = FIYATLAR["plasterboard_labor_m2_avg"]
                if structure_type_val == 'Light Steel' and plasterboard_interior_calc:
                    plasterboard_total_area = wall_area + roof_area
                elif structure_type_val == 'Heavy Steel' and plasterboard_all_calc:
                    plasterboard_total_area = (wall_area * 1.5) + roof_area
                if plasterboard_total_area > 0:
                    costs.append({'Item': 'Alçıpan Malzemesi', 'Quantity': f'{plasterboard_total_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plasterboard_material_m2"], 'Total (€)': calculate_rounded_up_cost(plasterboard_total_area * FIYATLAR["plasterboard_material_m2"])})
                    costs.append({'Item': 'Alçıpan İşçiliği', 'Quantity': f'{plasterboard_total_area:.2f} m²', 'Unit Price (€)': plasterboard_labor_m2, 'Total (€)': calculate_rounded_up_cost(plasterboard_total_area * plasterboard_labor_m2)})
            
            # Yalıtım (Zemin ve Duvar) (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok':
                if insulation_floor_option_val:
                    total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["insulation_per_m2"])
                    costs.append({'Item': 'Zemin Yalıtımı (Ana)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': total_price})
                    
                    if skirting_count_val > 0:
                        skirting_cost = calculate_rounded_up_cost(skirting_count_val * FIYATLAR["skirting_meter_price"])
                        costs.append({'Item': FIYATLAR["skirting_meter_info"], 'Quantity': f"{skirting_count_val:.2f} m", 'Unit Price (€)': FIYATLAR["skirting_meter_price"], 'Total (€)': skirting_cost})

                    if laminate_flooring_m2_val > 0:
                        laminate_flooring_cost = calculate_rounded_up_cost(laminate_flooring_m2_val * FIYATLAR["laminate_flooring_m2_price"])
                        costs.append({'Item': FIYATLAR["laminate_flooring_m2_info"], 'Quantity': f"{laminate_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR["laminate_flooring_m2_price"], 'Total (€)': laminate_flooring_cost})
                    
                    if under_parquet_mat_m2_val > 0:
                        under_parquet_mat_cost = calculate_rounded_up_cost(under_parquet_mat_m2_val * FIYATLAR["under_parquet_mat_m2_price"])
                        costs.append({'Item': FIYATLAR["under_parquet_mat_m2_info"], 'Quantity': f"{under_parquet_mat_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR["under_parquet_mat_m2_price"], 'Total (€)': under_parquet_mat_cost})

                    if osb2_18mm_count_val > 0:
                        osb2_18mm_cost = calculate_rounded_up_cost(osb2_18mm_count_val * FIYATLAR["osb2_18mm_piece_price"])
                        costs.append({'Item': FIYATLAR["osb2_18mm_piece_info"], 'Quantity': f"{osb2_18mm_count_val} adet", 'Unit Price (€)': FIYATLAR["osb2_18mm_piece_price"], 'Total (€)': osb2_18mm_cost})

                    if galvanized_sheet_m2_val > 0:
                        galvanized_sheet_cost = calculate_rounded_up_cost(galvanized_sheet_m2_val * FIYATLAR["galvanized_sheet_m2_price"])
                        costs.append({'Item': FIYATLAR["galvanized_sheet_m2_info"], 'Quantity': f"{galvanized_sheet_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR["galvanized_sheet_m2_price"], 'Total (€)': galvanized_sheet_cost})

                if insulation_wall_option_val:
                    total_price = calculate_rounded_up_cost(wall_area * FIYATLAR["insulation_per_m2"])
                    costs.append({'Item': 'Duvar Yalıtımı', 'Quantity': f'{wall_area:.2f} m²', 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': total_price})

            # Zemin Kaplama ve Plywood (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok':
                plywood_pieces_needed = math.ceil(floor_area / OSB_PANEL_AREA_M2)
                total_price = calculate_rounded_up_cost(plywood_pieces_needed * FIYATLAR["plywood_piece"])
                costs.append({'Item': 'Zemin (Kontrplak Malzemesi)', 'Quantity': plywood_pieces_needed, 'Unit Price (€)': FIYATLAR["plywood_piece"], 'Total (€)': total_price})
                total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["plywood_flooring_labor_m2"])
                costs.append({'Item': f'Zemin ({floor_covering_option_val} İşçiliği)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plywood_flooring_labor_m2"], 'Total (€)': total_price})

            # WC Seramik Malzeme ve İşçilik (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and wc_ceramic_input_val and wc_ceramic_area_val > 0:
                total_material_cost = calculate_rounded_up_cost(wc_ceramic_area_val * FIYATLAR["wc_ceramic_m2_material"])
                total_labor_cost = calculate_rounded_up_cost(wc_ceramic_area_val * FIYATLAR["wc_ceramic_m2_labor"])
                costs.append({'Item': 'WC Seramik Malzemesi', 'Quantity': f"{wc_ceramic_area_val:.2f} m²", 'Unit Price (€)': FIYATLAR["wc_ceramic_m2_material"], 'Total (€)': total_material_cost})
                costs.append({'Item': 'WC Seramik İşçiliği', 'Quantity': f"{wc_ceramic_area_val:.2f} m²", 'Unit Price (€)': FIYATLAR["wc_ceramic_m2_labor"], 'Total (€)': total_labor_cost})
            
            # Yerden Isıtma (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and heating_option_val:
                total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["floor_heating_m2"])
                costs.append({'Item': 'Yerden Isıtma Sistemi', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["floor_heating_m2"], 'Total (€)': total_price})
            
            # Güneş Enerjisi (Paket dışı manuel eklemeler)
            solar_cost = 0
            if aether_package_choice == 'Yok' and solar_option_val:
                solar_cost = calculate_rounded_up_cost(solar_capacity_val * FIYATLAR['solar_per_kw'])
                costs.append({'Item': f'Güneş Enerjisi Sistemi ({solar_capacity_val} kW)', 'Quantity': 1, 'Unit Price (€)': solar_cost, 'Total (€)': solar_cost})
            
            # Pencere ve Kapılar (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok':
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
            
            # Bağlantı Elemanları (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok':
                total_price = calculate_rounded_up_cost(floor_area * FIYATLAR["connection_element_m2"])
                costs.append({'Item': "Bağlantı Elemanları", 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["connection_element_m2"], 'Total (€)': total_price})
            
            # Mutfak Kurulumu ve Malzemeleri (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and kitchen_input_val:
                costs.append({'Item': f'Mutfak Kurulumu ({kitchen_choice})', 'Quantity': 1, 'Unit Price (€)': kitchen_cost_val, 'Total (€)': calculate_rounded_up_cost(kitchen_cost_val)})
                costs.append({'Item': FIYATLAR["kitchen_mdf_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["kitchen_cabinets_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["kitchen_countertop_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["kitchen_sink_faucet_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
            
            # Duş/WC Kurulumu ve Malzemeleri (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and shower_input_val:
                costs.append({'Item': 'Duş/WC Kurulumu', 'Quantity': 1, 'Unit Price (€)': FIYATLAR["shower_wc_installation_piece"], 'Total (€)': calculate_rounded_up_cost(FIYATLAR["shower_wc_installation_piece"])})
                costs.append({'Item': FIYATLAR["wc_shower_unit_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["wc_toilet_bowl_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["wc_washbasin_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["wc_towel_rail_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["wc_mirror_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["wc_accessories_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # Elektrik Tesisatı ve Malzemeleri (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and electrical_installation_input_val:
                electrical_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["electrical_per_m2"])
                costs.append({'Item': 'Elektrik Tesisatı (Malzemelerle)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["electrical_per_m2"], 'Total (€)': electrical_cost})
                costs.append({'Item': FIYATLAR["electrical_cable_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_conduits_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_junction_boxes_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_distribution_board_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_circuit_breakers_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_sockets_switches_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_lighting_fixtures_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["electrical_grounding_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # Sıhhi Tesisat ve Malzemeleri (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and plumbing_installation_input_val:
                plumbing_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["plumbing_per_m2"])
                costs.append({'Item': 'Sıhhi Tesisat (Malzemelerle)', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plumbing_per_m2"], 'Total (€)': plumbing_cost})
                costs.append({'Item': FIYATLAR["plumbing_pprc_pipes_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["plumbing_faucets_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["plumbing_shower_mixer_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["plumbing_valves_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["plumbing_pvc_pipes_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR["plumbing_siphons_info"], 'Quantity': "N/A", 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # Nakliye (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and transportation_input_val:
                costs.append({'Item': 'Nakliye', 'Quantity': 1, 'Unit Price (€)': FIYATLAR["transportation"], 'Total (€)': calculate_rounded_up_cost(FIYATLAR["transportation"])})
            
            # Tekerlekli Römork (Paket dışı manuel eklemeler)
            if aether_package_choice == 'Yok' and wheeled_trailer_option_val and wheeled_trailer_price_input_val > 0:
                trailer_price = calculate_rounded_up_cost(wheeled_trailer_price_input_val)
                costs.append({'Item': 'Tekerlekli Römork', 'Quantity': 1, 'Unit Price (€)': trailer_price, 'Total (€)': trailer_price})

            # Eğer solar_option_val True ise ve Aether Living paketi seçili değilse solar_cost'u hesapla
            solar_cost = 0 # solar_cost'u her zaman tanımlı hale getir (NameError düzeltmesi)
            if aether_package_choice == 'Yok' and solar_option_val:
                solar_cost = calculate_rounded_up_cost(solar_capacity_val * FIYATLAR['solar_per_kw'])
                costs.append({'Item': f'Güneş Enerjisi Sistemi ({solar_capacity_val} kW)', 'Quantity': 1, 'Unit Price (€)': solar_cost, 'Total (€)': solar_cost})


            # Ana Maliyet Hesaplamaları
            # Paket seçiliyse house_subtotal, paketin otomatik toplanan maliyeti olur.
            # Paket seçilmediyse, yukarıdaki manuel seçilenlerin toplamı olur.
            house_subtotal = sum([item['Total (€)'] for item in costs if 'Solar' not in item['Item']]) # Tüm kalemlerin toplamı

            waste_cost = calculate_rounded_up_cost(house_subtotal * FIRE_RATE)
            total_house_cost = calculate_rounded_up_cost(house_subtotal + waste_cost)
            profit = calculate_rounded_up_cost(total_house_cost * profit_rate_val)
            house_vat_base = calculate_rounded_up_cost(total_house_cost + profit)
            house_vat = calculate_rounded_up_cost(house_vat_base * VAT_RATE)
            house_sales_price = calculate_rounded_up_cost(house_vat_base + house_vat)
            total_sales_price = calculate_rounded_up_cost(house_sales_price + solar_cost) # solar_cost artık hep tanımlı

            delivery_duration_business_days = math.ceil((floor_area / 27.0) * 35)
            if delivery_duration_business_days < 10: delivery_duration_business_days = 10
            
            annual_income_tax_calc = calculate_rounded_up_cost((profit + waste_cost) * ANNUAL_INCOME_TAX_RATE)

            financial_summary_data = [
                ["Ara Toplam (Tüm Kalemler, Güneş Dahil)", sum([item['Total (€)'] for item in costs])],
                [f"Atık Maliyeti ({FIRE_RATE*100:.0f}%) (Sadece Ev için)", waste_cost],
                ["Toplam Maliyet (Ev + Atık + Güneş)", total_house_cost + solar_cost],
                [f"Kar ({profit_rate_val*100:.0f}%) (Sadece Ev için)", profit],
                ["", ""],
                ["Ev Satış Fiyatı (KDV Dahil)", house_sales_price],
                ["Güneş Enerjisi Sistemi Fiyatı (KDV Dahil)", solar_cost],
                ["TOPLAM SATIŞ FİYATI", total_sales_price],
                ["", ""],
                [f"KDV ({VAT_RATE*100:.0f}%)", house_vat],
                ["Yıllık Kurumlar Vergisi (%23.5)", annual_income_tax_calc],
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
                'plasterboard_interior': plasterboard_interior_calc,
                'plasterboard_all': plasterboard_all_calc,
                'osb_inner_wall': osb_inner_wall_calc,
                'insulation_floor': insulation_floor_option_val,
                'insulation_wall': insulation_wall_option_val,
                'window_count': window_count, 'window_size': window_size_val,
                'window_door_color': window_door_color_val,
                'sliding_door_count': sliding_door_count, 'sliding_door_size': sliding_door_size_val,
                'wc_window_count': wc_window_count, 'wc_window_size': wc_window_size_val,
                'wc_sliding_door_count': wc_sliding_door_count, 'wc_sliding_door_size': wc_sliding_door_size_val,
                'door_count': door_count, 'door_size': door_size_val,
                'kitchen_type_display_en_gr': kitchen_type_display_en_gr,
                'kitchen_type_display_tr': kitchen_type_display_tr,
                'kitchen': kitchen_input_val,
                'shower': shower_input_val,
                'wc_ceramic': wc_ceramic_input_val, 'wc_ceramic_area': wc_ceramic_area_val,
                'electrical': electrical_installation_input_val, 'plumbing': plumbing_installation_input_val,
                'transportation': transportation_input_val, 'heating': heating_option_val,
                'solar': solar_option_val, 'solar_kw': solar_capacity_val, 'solar_price': solar_cost, # solar_price buraya solar_cost olarak düzeltildi
                'vat_rate': VAT_RATE, 'profit_rate': profit_rate_val,
                'room_configuration': room_config_val,
                'wheeled_trailer_included': wheeled_trailer_option_val,
                'wheeled_trailer_price': wheeled_trailer_price_input_val,
                'sales_price': total_sales_price,
                'delivery_duration_business_days': delivery_duration_business_days,
                'welding_labor_type': welding_labor_option_val,
                'facade_sandwich_panel_included': facade_sandwich_panel_calc,
                'floor_covering_type': floor_covering_option_val,
                'skirting_length_val': skirting_count_val,
                'laminate_flooring_m2_val': laminate_flooring_m2_val,
                'under_parquet_mat_m2_val': under_parquet_mat_m2_val,
                'osb2_18mm_count_val': osb2_18mm_count_val,
                'galvanized_sheet_m2_val': galvanized_sheet_m2_val,
                
                # Yeni Aether Living Opsiyonları için değerler (UI'dan kaldırılsa da mantıkta kullanılacak ve rapora eklenecek)
                'aether_package_choice': aether_package_choice,
                'exterior_cladding_m2_option': exterior_cladding_m2_option_val,
                'exterior_cladding_m2_val': exterior_cladding_m2_val,
                'exterior_wood_cladding_m2_option': exterior_wood_cladding_m2_option_val,
                'exterior_wood_cladding_m2_val': exterior_wood_cladding_m2_val,
                'porcelain_tiles_option': porcelain_tiles_option_val,
                'porcelain_tiles_m2_val': porcelain_tiles_m2_val,
                'concrete_panel_floor_option': concrete_panel_floor_option_val,
                'concrete_panel_floor_m2_val': concrete_panel_floor_m2_val,
                'bedroom_set_option': bedroom_set_option_val,
                'sofa_option': sofa_option_val,
                'white_goods_fridge_tv_option': white_goods_fridge_tv_option_val,
                'premium_faucets_option': premium_faucets_option_val,
                'integrated_fridge_option': integrated_fridge_option_val,
                'designer_furniture_option': designer_furniture_option_val,
                'italian_sofa_option': italian_sofa_option_val,
                'inclass_chairs_option': inclass_chairs_option_val,
                'inclass_chairs_count': inclass_chairs_count_val, # Adet bilgisi eklendi
                'brushed_granite_countertops_option': brushed_granite_countertops_option_val,
                'brushed_granite_countertops_m2_val': brushed_granite_countertops_m2_val,
                'smart_home_systems_option': smart_home_systems_option_val,
                'security_camera_option': security_camera_option_val,
                'terrace_laminated_wood_flooring_option': terrace_laminated_wood_flooring_option_val,
                'terrace_laminated_wood_flooring_m2_val': terrace_laminated_wood_flooring_m2_val,
            }

            # --- Display Results in Streamlit ---
            st.subheader("Maliyet Detayları (Dahili Rapor)")
            st.dataframe(pd.DataFrame(costs).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            if not pd.DataFrame(profile_analysis_details).empty and project_details_result['structure_type'] == 'Light Steel':
                st.subheader("Çelik Profil Detaylı Analizi (Dahili Rapor)")
                st.dataframe(pd.DataFrame(profile_analysis_details).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            st.subheader("Finansal Özet (Dahili Rapor)")
            st.dataframe(pd.DataFrame(formatted_financial_summary).set_index('Item'), use_container_width=True)
            
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
            st.exception(e)

# --- Start the Streamlit app ---
if __name__ == "__main__":
    run_streamlit_app()
