# ==============================================================================
# BÖLÜM 1: Gerekli Kütüphane İçe Aktarımları, Temel Sabitler ve Şirket Bilgileri
# ==============================================================================

import streamlit as st
import math
import pandas as pd
import io
import re
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import requests
from PIL import Image as PILImage
import base64

# --- Görünmez Karakter Temizleme Fonksiyonu ---
def clean_invisible_chars(text):
    """Metindeki görünmez karakterleri temizler (U+00A0, U+200B vb. dahil)."""
    # U+00A0 (non-breaking space) ve U+200B (zero width space) gibi karakterleri temizler
    return re.sub(r'[\u00A0\u200B\s\xA0]+', ' ', text).strip()

# --- Font Kaydı (Türkçe karakter desteği) ---
# Programın çalıştığı klasörde 'fonts' dizini altında 'FreeSans.ttf' ve 'FreeSansBold.ttf' olmalıdır.
try:
    # 'fonts' klasörünün varlığını kontrol et
    if not os.path.exists("fonts"):
        os.makedirs("fonts") # Yoksa oluştur
    
    # Gerekli font dosyalarının varlığını kontrol et
    if not (os.path.exists("fonts/FreeSans.ttf") and os.path.exists("fonts/FreeSansBold.ttf")):
        st.warning("Gerekli 'FreeSans.ttf' veya 'FreeSansBold.ttf' font dosyaları 'fonts/' klasöründe bulunamadı. Lütfen bu dosyaları manuel olarak ekleyin. Aksi takdirde PDF'lerde Türkçe karakterler düzgün görünmeyebilir ve Helvetica kullanılacaktır.")
        raise FileNotFoundError # Fontlar bulunamazsa istisna fırlat
    
    pdfmetrics.registerFont(TTFont("FreeSans", "fonts/FreeSans.ttf"))
    pdfmetrics.registerFont(TTFont("FreeSans-Bold", "fonts/FreeSansBold.ttf"))
    pdfmetrics.registerFontFamily('FreeSans', normal='FreeSans', bold='FreeSans-Bold')
    MAIN_FONT = "FreeSans"
except Exception as e:
    # Fontlar bulunamazsa veya kaydedilemezse Helvetica'ya geri dön
    st.warning(f"Font yükleme hatası: {e}. PDF'lerde 'Helvetica' fontu kullanılacak.")
    MAIN_FONT = "Helvetica"

# --- Şirket Bilgileri ---
# LOGO_URL'nin genel erişime açık bir URL olduğundan emin olun.
# Örnek: Google Drive'dan genel erişimli bir dosya veya GitHub Pages gibi bir CDN.
LOGO_URL = "https://drive.google.com/uc?export=download&id=1RD27Gas035iUqe4Ucl3phFwxZPWZPWzn" 

COMPANY_INFO = {
    "name": "PREMIUM HOME LTD",
    "address": "Iasonos 1, 1082, Nicosia Cyprus",
    "email": "info@premiumpluscy.eu",
    "phone": "+35722584081, +35797550946",
    "website": "www.premiumpluscy.eu",
    "linktree": "https://linktr.ee/premiumplushome",
    "company_no": "HE 467707",
    "bank_name": "BANK OF CYPRUS GROUP",
    "bank_address": "12 Esperidon Street 1087 Nicosia",
    "account_name": "SOYKOK PREMIUM HOME LTD",
    "iban": "CY27 0020 0195 0000 3570 4239 2044",
    "account_number": "357042392044", # Banka hesap numarası eklendi
    "currency_type": "EURO", # Para birimi eklendi
    "swift_bic": "BCYPCY2N"
}

# --- Güncel Fiyat Tanımları ---
# Tüm fiyatlar KDV hariç maliyet fiyatlarıdır.
FIYATLAR = {
    # Çelik Profil Fiyatları (6m parça başı)
    "steel_profile_100x100x3": 45.00,
    "steel_profile_100x50x3": 33.00,
    "steel_profile_40x60x2": 14.00,
    "steel_profile_120x60x5mm": 60.00,
    "steel_profile_50x50x2": 11.00,
    "steel_profile_HEA160": 155.00,
    
    # Temel Malzeme Fiyatları
    "heavy_steel_m2": 400.00, # Ağır çelik m2 fiyatı
    "sandwich_panel_m2": 22.00, # Standart 60mm EPS paneli için
    "plywood_piece": 44.44, # Kontraplak/OSB levha fiyatı (yaklaşık 1.22x2.44m)
    "aluminum_window_piece": 250.00, # Alüminyum pencere adet fiyatı
    "sliding_glass_door_piece": 300.00, # Sürgülü cam kapı adet fiyatı
    "wc_window_piece": 120.00, # WC pencere adet fiyatı
    "wc_sliding_door_piece": 150.00, # WC sürgülü kapı adet fiyatı
    "door_piece": 280.00, # Genel kapı adet fiyatı
    
    # Kurulum/İşçilik Fiyatları
    "kitchen_installation_standard_piece": 550.00, # Standart mutfak kurulumu
    "kitchen_installation_special_piece": 1000.00, # Özel tasarım mutfak kurulumu
    "shower_wc_installation_piece": 1000.00, # Duş/WC kurulumu
    "connection_element_m2": 1.50, # Bağlantı elemanları için m2 fiyatı
    "transportation": 350.00, # Nakliye fiyatı
    "floor_heating_m2": 50.00, # Yerden ısıtma m2 fiyatı
    "wc_ceramic_m2_material": 20.00, # WC Seramik malzeme m2 fiyatı
    "wc_ceramic_m2_labor": 20.00,     # WC Seramik işçilik m2 fiyatı
    "electrical_per_m2": 25.00, # Elektrik tesisatı m2 fiyatı
    "plumbing_per_m2": 25.00, # Sıhhi tesisat m2 fiyatı
    "osb_piece": 12.00, # OSB levha fiyatı
    "insulation_per_m2": 5.00, # Genel yalıtım m2 fiyatı (5cm EPS gibi)
    
    # İşçilik Fiyatları
    "welding_labor_m2_standard": 160.00, # Standart kaynak işçiliği m2 fiyatı
    "welding_labor_m2_trmontaj": 20.00, # TR montaj kaynak işçiliği m2 fiyatı
    "panel_assembly_labor_m2": 5.00, # Panel montaj işçiliği m2 fiyatı
    "plasterboard_material_m2": 20.00, # Alçıpan malzeme m2
    "plasterboard_labor_m2_avg": 80.00, # Alçıpan işçilik m2
    "plywood_flooring_labor_m2": 11.11, # Kontraplak döşeme işçiliği m2 fiyatı
    "door_window_assembly_labor_piece": 10.00, # Kapı/pencere montaj işçiliği adet fiyatı
    "solar_per_kw": 1250.00, # Solar enerji kW başına fiyat

    # Yeni Zemin Sistemi Malzemeleri Fiyatları
    "skirting_meter_price": 2.00, # Süpürgelik metre fiyatı
    "laminate_flooring_m2_price": 15.00, # Laminat parke m2 fiyatı
    "under_parquet_mat_m2_price": 3.00, # Parke altı şilte m2 fiyatı
    "osb2_18mm_piece_price": 30.00, # OSB2 18mm veya Beton Panel için parça fiyatı
    "galvanized_sheet_m2_price": 10.00, # Galvanizli sac m2 fiyatı

    # Yeni Ürün Malzeme Fiyatları ve Bilgi Kalemleri (Aether Living Paketleri için)
    "smart_home_systems_total_price": 350.00,
    "white_goods_total_price": 800.00,
    "sofa_total_price": 400.00,
    "security_camera_total_price": 650.00,
    "exterior_cladding_labor_price_per_m2": 150.00, # Knauf Aquapanel gibi dış cephe işçiliği M2 bazlı
    "bedroom_set_total_price": 800.00,
    "terrace_laminated_wood_flooring_price_per_m2": 40.00,
    "porcelain_tile_m2_price": 25.00, # Porselen fayans (zemin için, wc_ceramic fiyatı kullanılacak ama burada da bilgi olarak tutuldu)
    "concrete_panel_floor_price_per_m2": 50.00,
    "premium_faucets_total_price": 200.00,
    "designer_furniture_total_price": 1000.00,
    "italian_sofa_total_price": 800.00,
    "inclass_chairs_unit_price": 150.00,
    "exterior_wood_cladding_m2_price": 150.00, # Lambiri
    "brushed_grey_granite_countertops_price_m2_avg": 425.00,

    # Detaylı Malzeme Fiyatları (Yeni eklenenler)
    "100mm_eps_isothermal_panel_unit_price": 27.00, # Poliüretan İzotermik Panel m2
    "gypsum_board_white_per_unit_price": 8.65, # Beyaz alçıpan (birim başına fiyat)
    "gypsum_board_green_per_unit_price": 11.95, # Yeşil (suya dayanıklı) alçıpan (birim başına fiyat)
    "gypsum_board_blue_per_unit_price": 22.00, # Mavi (yangına dayanıklı) alçıpan (birim başına fiyat)
    "otb_stone_wool_price": 19.80, # Taş yünü yalıtım m2 fiyatı
    "glass_wool_5cm_packet_price": 19.68, # Cam yünü 5cm (paket fiyatı)
    "tn25_screws_price_per_unit": 5.58, # Vida birim fiyatı
    "cdx400_material_price": 3.40, # Profil
    "ud_material_price": 1.59, # Profil
    "oc50_material_price": 2.20, # Profil
    "oc100_material_price": 3.96, # Profil
    "ch100_material_price": 3.55 # Profil
}

# Malzeme Bilgi Kalemleri (Fiyatı olmayanlar veya başka bir yerde fiyatı olanlar - Sadece listeleme ve PDF'e detay ekleme için)
MATERIAL_INFO_ITEMS = {
    "steel_skeleton_info": "Metal iskelet",
    "protective_automotive_paint_info": "Koruyucu otomotiv boyası",
    "insulation_info": "Yalıtım",
    "60mm_eps_sandwich_panel_info": "Standart 60mm EPS veya Poliüretan Sandviç Paneller (beyaz)",
    "100mm_eps_isothermal_panel_info": "Yüksek performanslı 100mm EPS veya Poliüretan İzotermik Paneller",
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
    "integrated_refrigerator_info": "Entegre Buzdolabı",
    "integrated_custom_furniture_info": "Entegre Özel Tasarım Mobilyalar (yüksek kaliteli MDF/lake)",
    "italian_sofa_info": "İtalyan Kanepe",
    "inclass_chairs_info": "Inclass Sandalyeler",
    "smart_home_systems_info": "Akıllı Ev Sistemleri",
    "advanced_security_camera_pre_installation_info": "Gelişmiş güvenlik kamerası ön kurulumu",
    "exterior_wood_cladding_lambiri_info": "Dış cephe ahşap kaplama - Lambiri",
    "brushed_grey_granite_countertops_info": "Fırçalanmış Gri Kale Granit Mutfak/Banyo Tezgahları",
    "knauf_aquapanel_gypsum_board_info": "Knauf Aquapanel Alçıpan",
    "eps_styrofoam_info": "EPS STYROFOAM",
    "knauf_mineralplus_insulation_info": "Knauf MineralPlus İzolasyon",
    "knauf_guardex_gypsum_board_info": "Knauf Guardex Alçıpan",
    "satin_plaster_paint_info": "Saten sıva ve boya",
    "supportive_headboard_furniture_info": "Destekleyici Mobilyalı Yatak Başlığı",

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

# Sabit oranlar ve alanlar
FIRE_RATE = 0.05
VAT_RATE = 0.19
MONTHLY_ACCOUNTING_EXPENSES = 180.00
MONTHLY_OFFICE_RENT = 280.00
ANNUAL_INCOME_TAX_RATE = 0.235
OSB_PANEL_AREA_M2 = 1.22 * 2.44 # Bir OSB panelinin alanı
GYPSUM_BOARD_UNIT_AREA_M2 = 1.2 * 2.4 # Bir alçıpan panelinin alanı
GLASS_WOOL_M2_PER_PACKET = 10.0 # Bir paket cam yününün kapsadığı alan

# ====================== YARDIMCI FONKSİYONLAR ======================
def clean_invisible_chars(text):
    """Metinden görünmez karakterleri kaldırır."""
    return re.sub(r'[\u00A0\u200B]', ' ', text)

def calculate_area(width, length, height):
    """Boyutlara göre zemin, duvar ve çatı alanlarını hesaplar."""
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Parasal değeri Euro para birimi olarak biçimlendirir."""
    return f"€{value:,.2f}"

def calculate_rounded_up_cost(value):
    """Parasal değeri iki ondalık basamağa yuvarlar."""
    return math.ceil(value * 100) / 100.0

# ====================== PDF OLUŞTURMA YARDIMCI FONKSİYONLARI ======================

# PDF için yeni metinler
ELECTRICAL_MATERIALS_EN = MATERIAL_INFO_ITEMS["electrical_cable_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_conduits_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_junction_boxes_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_distribution_board_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_circuit_breakers_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_sockets_switches_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_lighting_fixtures_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_grounding_info"]
ELECTRICAL_MATERIALS_GR = ELECTRICAL_MATERIALS_EN.replace("Electrical Cables", "Ηλεκτρικά Καλώδια").replace("Conduits and Pipes for Cabling", "Σωλήνες & Κανάλια για Καλωδίωση").replace("Junction Boxes", "Κουτιά Διακλάδωσης").replace("Distribution Board (Fuse Box)", "Πίνακας Ασφαλειών").replace("Circuit Breakers & Residual Current Device (RCD)", "Ασφάλειες & Ρελέ Διαρροής").replace("Sockets and Switches", "Πρίζες & Διακόπτες").replace("Interior Lighting Fixtures (LED Spots / Ceiling Lamp)", "Εσωτερικά Φωτιστικά (LED Σποτ / Φωτιστικό Οροφής)").replace("Grounding System Components", "Σύστημα Γείωσης")
ELECTRICAL_MATERIALS_TR = MATERIAL_INFO_ITEMS["electrical_cable_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_conduits_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_junction_boxes_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_distribution_board_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_circuit_breakers_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_sockets_switches_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_lighting_fixtures_info"] + "\n" + MATERIAL_INFO_ITEMS["electrical_grounding_info"]

PLUMBING_MATERIALS_EN = f"<b>Clean Water System:</b><br/>• {MATERIAL_INFO_ITEMS['plumbing_pprc_pipes_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_faucets_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_shower_mixer_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_valves_info']}<br/><b>Wastewater System:</b><br/>• {MATERIAL_INFO_ITEMS['plumbing_pvc_pipes_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_siphons_info']}"
PLUMBING_MATERIALS_GR = PLUMBING_MATERIALS_EN.replace("Clean Water System:", "Σύστημα Καθαρού Νερού:").replace("Wastewater System:", "Σύστημα Ακάθαρτου Νερού:").replace("PPRC Pipes for Hot/Cold Water", "Σωλήνες PPRC για Ζεστό/Κρύο Νερό").replace("Kitchen and Bathroom Faucets", "Μπαταρίες Κουζίνας και Μπάνιου").replace("Shower Head and Mixer", "Κεφαλή Ντους και Μπαταρία").replace("Main and intermediate valves", "Κύριες και ενδιάμεσες βάνες").replace("PVC Pipes (50mm / 100mm)", "Σωλήνες PVC (50mm / 100mm)").replace("Siphons and floor drains", "Σιφώνια και σχάρες δαπέδου")
PLUMBING_MATERIALS_TR = f"<b>Temiz Su Tesisatı:</b><br/>• {MATERIAL_INFO_ITEMS['plumbing_pprc_pipes_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_faucets_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_shower_mixer_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_valves_info']}<br/><b>Atık Su Tesisatı:</b><br/>• {MATERIAL_INFO_ITEMS['plumbing_pvc_pipes_info']}<br/>• {MATERIAL_INFO_ITEMS['plumbing_siphons_info']}"

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

KITCHEN_MATERIALS_EN = f"""
Standard materials include:
• {MATERIAL_INFO_ITEMS['kitchen_mdf_info']}
• {MATERIAL_INFO_ITEMS['kitchen_cabinets_info']}
• {MATERIAL_INFO_ITEMS['kitchen_countertop_info']}
• {MATERIAL_INFO_ITEMS['kitchen_sink_faucet_info']}
Note: Final material selection and detailed list will be provided upon design approval.
"""
KITCHEN_MATERIALS_GR = KITCHEN_MATERIALS_EN.replace("Standard materials include:", "Τυπικά υλικά περιλαμβάνουν:").replace("Glossy White Color MDF Material", "Υλικό MDF Γυαλιστερό Λευκό Χρώμα").replace("Special Production Kitchen Cabinets (custom dimensions)", "Ειδικές Κατασκευές Ντουλαπιών Κουζίνας (προσαρμοσμένες διαστάσεις)").replace("Countertop (Laminate or specified equivalent)", "Πάγκος (Laminate ή καθορισμένο ισοδύναμο)").replace("Sink and Faucet", "Νεροχύτης και Βρύση").replace("Note: Final material selection and detailed list will be provided upon design approval.", "Σημείωση: Η τελική επιλογή υλικών και η λεπτομερής λίστα θα παρασχεθούν μετά την έγκριση του σχεδιασμού.")
KITCHEN_MATERIALS_TR = f"""
Standard malzemeler:
• {MATERIAL_INFO_ITEMS['kitchen_mdf_info']}
• {MATERIAL_INFO_ITEMS['kitchen_cabinets_info']}
• {MATERIAL_INFO_ITEMS['kitchen_countertop_info']}
• {MATERIAL_INFO_ITEMS['kitchen_sink_faucet_info']}
Not: Malzeme seçimi sonrası nihai ve detaylı liste tasarım onayı ile birlikte sunulacaktır.
"""

SHOWER_WC_MATERIALS_EN = f"""
• {MATERIAL_INFO_ITEMS['wc_shower_unit_info']}
• {MATERIAL_INFO_ITEMS['wc_toilet_bowl_info']}
• {MATERIAL_INFO_ITEMS['wc_washbasin_info']}
• {MATERIAL_INFO_ITEMS['wc_towel_rail_info']}
• {MATERIAL_INFO_ITEMS['wc_mirror_info']}
• {MATERIAL_INFO_ITEMS['wc_accessories_info']}
"""
SHOWER_WC_MATERIALS_GR = SHOWER_WC_MATERIALS_EN.replace("Shower Unit (Shower Head & Mixer)", "Μονάδα Ντους (Κεφαλή Ντους & Μπαταρία)").replace("Toilet Bowl & Cistern", "Λεκάνη Τουαλέτας & Καζανάκι").replace("Washbasin & Faucet", "Νιπτήρας & Μπαταρία").replace("Towel Rail", "Πετσετοθήκη").replace("Mirror", "Καθρέφτης").replace("Bathroom Accessories", "Αξεσουάρ Μπάνιου")
SHOWER_WC_MATERIALS_TR = f"""
• {MATERIAL_INFO_ITEMS['wc_shower_unit_info']}
• {MATERIAL_INFO_ITEMS['wc_toilet_bowl_info']}
• {MATERIAL_INFO_ITEMS['wc_washbasin_info']}
• {MATERIAL_INFO_ITEMS['wc_towel_rail_info']}
• {MATERIAL_INFO_ITEMS['wc_mirror_info']}
• {MATERIAL_INFO_ITEMS['wc_accessories_info']}
"""

# PDF özellikleri açıklamaları
LIGHT_STEEL_BUILDING_STRUCTURE_EN_GR = f"""
<b>Building structure details:</b><br/>
Skeleton: Box profile with dimensions of 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm will be used. Antirust will be applied to all box profiles and can be painted with the desired color. All our profile welding works have EN3834 certification in accordance with European standards. The construction operations of the entire building are subject to European standards and EN 1090-1 Light Steel Construction license inspection.
"""
HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR = f"""
<b>Building structure details:</b><br/>
Skeleton: Steel house frame with all necessary cross-sections (columns, beams), including connection components (flanges, screws, bolts), all as static drawings.<br/>
HEA120 OR HEA160 Heavy metal will be used in models with title deed and construction permit. All non-galvanized metal surfaces will be sandblasted according to the Swedish standard Sa 2.5 and will be coated with a zincphosphate primer 80μm thick.<br/>
Anti-rust will be applied to all profiles and can be painted in the desired color.<br/>
All our profile welding works have EN3834 certificate in accordance with European standards. All construction processes of the building are subject to European standards and EN 1090-1 Steel Construction license inspection.
"""
LIGHT_STEEL_BUILDING_STRUCTURE_TR = f"""
<b>Bina yapı detayları:</b><br/>
İskelet: 100x100*3mm + 100x50*2.5mm + 40x40*2.5mm ölçülerinde kutu profil kullanılacaktır. Tüm kutu profillere pas önleyici uygulanacak ve istenilen renge boyanabilir. Tüm profil kaynak işlerimiz Avrupa standartlarına uygun olarak EN3834 sertifikalıdır. Binanın tüm yapım süreçleri Avrupa standartlarına ve EN 1090-1 Hafif Çelik Yapı ruhsat denetimine tabidir.
"""
HEAVY_STEEL_BUILDING_STRUCTURE_TR = f"""
<b>Bina yapı detayları:</b><br/>
İskelet: Tüm gerekli kesitlere (kolonlar, kirişler) sahip çelik ev iskeleti, bağlantı elemanları (flanşlar, vidalar, cıvatalar) dahil, hepsi statik çizimlere göre olacaktır.<br/>
Tapulu ve inşaat ruhsatlı modellerde HEA120 VEYA HEA160 Ağır metal kullanılacaktır. Tüm galvanizli olmayan metal yüzeyler İsveç standardı Sa 2.5'e göre kumlama yapılacak ve 80μm kalınlığında çinko-fosfat astar ile kaplanacaktır.<br/>
Anti-rust will be applied to all profillere pas önleyici uygulanacak ve istenilen renge boyanabilir.<br/>
All our profile welding works have EN3834 certificate in accordance with European standards. All construction processes of the building are subject to Avrupa standartlarına ve EN 1090-1 Çelik Yapı ruhsat denetimine tabidir.
"""

INTERIOR_WALLS_DESCRIPTION_EN_GR = f"""
<b>1.4. INTERIOR WALLS:</b> 50mm polyurethane Sandwich Panel. Colour Option.
"""
INTERIOR_WALLS_DESCRIPTION_TR = f"""
<b>1.4. İÇ DUVARLAR:</b> 50mm poliüretan Sandviç Panel. Renk Seçeneği.
"""

ROOF_DESCRIPTION_EN_GR = f"""
<b>1.1. ROOF:</b> 100mm polyurethane Sandwich Panel. Bordex Internal Roofing 9 mm. 2 Coats Satin Plaster, 1 Coat Primer, 2 Coats Paint.
"""
ROOF_DESCRIPTION_TR = f"""
<b>1.1. ÇATI:</b> 100mm poliüretan Sandviç Panel. Bordex İç Çatı Kaplaması 9 mm. 2 Kat Saten Alçı, 1 Kat Astar, 2 Kat Boya.
"""

EXTERIOR_WALLS_DESCRIPTION_EN_GR = f"""
<b>1.2. EXTERIOR WALLS:</b> 50mm polyurethane Sandwich Panel. Color option.
"""
EXTERIOR_WALLS_DESCRIPTION_TR = f"""
<b>1.2. DIŞ DUVARLAR:</b> 50mm poliüretan Sandviç Panel. Renk seçeneği.
"""

FLOOR_INSULATION_MATERIALS_EN_GR = f"""
<b>Floor Insulation Materials / Zemin Yalıtım Malzemeleri:</b>
"""
FLOOR_INSULATION_MATERIALS_TR = f"""
<b>Zemin Yalıtım Malzemeleri:</b>
"""

# ====================== UTILITY FUNCTIONS ======================
def calculate_area(width, length, height):
    """Boyutlara göre zemin, duvar ve çatı alanlarını hesaplar."""
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Parasal değeri Euro para birimi olarak biçimlendirir."""
    return f"€{value:,.2f}"

def calculate_rounded_up_cost(value):
    """Parasal değeri iki ondalık basamağa yuvarlar."""
    return math.ceil(value * 100) / 100.0

def calculate_recommended_profiles(floor_area):
    """Proje alanına göre önerilen çelik profil adetlerini hesaplar (kaba tahmin)."""
    base_factor = floor_area / 20.0
    return {
        "100x100x3": int(base_factor * 2),
        "100x50x3": int(base_factor * 3),
        "40x60x2": int(base_factor * 4),
        "50x50x2": int(base_factor * 5),
        "120x60x5mm": int(base_factor * 1.5),
        "HEA160": int(base_factor * 0.5)
    }

def calculate_costs_detailed(project_inputs, areas):
    """
    Proje girdilerine ve alanlara göre detaylı maliyet hesaplamalarını yapar.
    Maliyet dökümü listesini ve diğer hesaplanan değerleri döndürür.
    """
    
    floor_area = areas["floor"]
    wall_area = areas["wall"]
    roof_area = areas["roof"]

    costs = [] # Tüm maliyet kalemleri buraya eklenecek
    profile_analysis_details = [] # Çelik profil analiz detaylarını tutacak
    
    # --- Yapısal Maliyetler ---
    if project_inputs['structure_type'] == 'Light Steel':
        # Eğer manuel olarak adet girildiyse onları kullan
        if sum([project_inputs['profile_100x100_count'], project_inputs['profile_100x50_count'],
                project_inputs['profile_40x60_count'], project_inputs['profile_50x50_count'],
                project_inputs['profile_120x60x5mm_count'], project_inputs['profile_HEA160_count']]) > 0:
            if project_inputs['profile_100x100_count'] > 0:
                cost = project_inputs['profile_100x100_count'] * FIYATLAR['steel_profile_100x100x3']
                costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (100x100x3)", 'Quantity': f"{project_inputs['profile_100x100_count']} adet", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(cost)})
                profile_analysis_details.append({'Item': '100x100x3', 'Quantity': project_inputs['profile_100x100_count'], 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(cost)})
            if project_inputs['profile_100x50_count'] > 0:
                cost = project_inputs['profile_100x50_count'] * FIYATLAR['steel_profile_100x50x3']
                costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (100x50x3)", 'Quantity': f"{project_inputs['profile_100x50_count']} adet", 'Unit Price (€)': FIYATLAR['steel_profile_100x50x3'], 'Total (€)': calculate_rounded_up_cost(cost)})
                profile_analysis_details.append({'Item': '100x50x3', 'Quantity': project_inputs['profile_100x50_count'], 'Unit Price (€)': FIYATLAR['steel_profile_100x50x3'], 'Total (€)': calculate_rounded_up_cost(cost)})
            if project_inputs['profile_40x60_count'] > 0:
                cost = project_inputs['profile_40x60_count'] * FIYATLAR['steel_profile_40x60x2']
                costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (40x60x2)", 'Quantity': f"{project_inputs['profile_40x60_count']} adet", 'Unit Price (€)': FIYATLAR['steel_profile_40x60x2'], 'Total (€)': calculate_rounded_up_cost(cost)})
                profile_analysis_details.append({'Item': '40x60x2', 'Quantity': project_inputs['profile_40x60_count'], 'Unit Price (€)': FIYATLAR['steel_profile_40x60x2'], 'Total (€)': calculate_rounded_up_cost(cost)})
            if project_inputs['profile_50x50_count'] > 0:
                cost = project_inputs['profile_50x50_count'] * FIYATLAR['steel_profile_50x50x2']
                costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (50x50x2)", 'Quantity': f"{project_inputs['profile_50x50_count']} adet", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(cost)})
                profile_analysis_details.append({'Item': '50x50x2', 'Quantity': project_inputs['profile_50x50_count'], 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(cost)})
            if project_inputs['profile_120x60x5mm_count'] > 0:
                cost = project_inputs['profile_120x60x5mm_count'] * FIYATLAR['steel_profile_120x60x5mm']
                costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (120x60x5mm)", 'Quantity': f"{project_inputs['profile_120x60x5mm_count']} adet", 'Unit Price (€)': FIYATLAR['steel_profile_120x60x5mm'], 'Total (€)': calculate_rounded_up_cost(cost)})
                profile_analysis_details.append({'Item': '120x60x5mm', 'Quantity': project_inputs['profile_120x60x5mm_count'], 'Unit Price (€)': FIYATLAR['steel_profile_120x60x5mm'], 'Total (€)': calculate_rounded_up_cost(cost)})
            if project_inputs['profile_HEA160_count'] > 0:
                cost = project_inputs['profile_HEA160_count'] * FIYATLAR['steel_profile_HEA160']
                costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (HEA160)", 'Quantity': f"{project_inputs['profile_HEA160_count']} adet", 'Unit Price (€)': FIYATLAR['steel_profile_HEA160'], 'Total (€)': calculate_rounded_up_cost(cost)})
                profile_analysis_details.append({'Item': 'HEA160', 'Quantity': project_inputs['profile_HEA160_count'], 'Unit Price (€)': FIYATLAR['steel_profile_HEA160'], 'Total (€)': calculate_rounded_up_cost(cost)})
            
            # Hafif çelikte koruyucu otomotiv boyası dahil bilgi olarak eklenir
            costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

        else: # Heavy Steel
            heavy_steel_cost = floor_area * FIYATLAR['heavy_steel_m2']
            costs.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
            profile_analysis_details.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
            costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

        # Kaynak işçiliği
        welding_labor_price = FIYATLAR['welding_labor_m2_standard'] if project_inputs['welding_type'] == 'Standard Welding (160€/m²)' else FIYATLAR['welding_labor_m2_trmontaj']
        welding_cost = floor_area * welding_labor_price
        costs.append({'Item': f"Steel Welding Labor ({project_inputs['welding_type'].split(' ')[0]})", 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': welding_labor_price, 'Total (€)': calculate_rounded_up_cost(welding_cost)})

        # 2. Duvarlar (Sandviç Panel, Alçıpan, OSB, Kaplamalar ve Yalıtım)
        # Dış/İç Duvar Sandviç Panel (Hafif Çelikte varsayılan, Ağır Çelikte opsiyonel)
        if project_inputs['structure_type'] == 'Light Steel' or project_inputs['facade_sandwich_panel_option']:
            sandwich_panel_total_area = wall_area + roof_area
            sandwich_panel_cost = sandwich_panel_total_area * FIYATLAR["sandwich_panel_m2"]
            costs.append({'Item': MATERIAL_INFO_ITEMS['60mm_eps_sandwich_panel_info'], 'Quantity': f"{sandwich_panel_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': calculate_rounded_up_cost(sandwich_panel_cost)})
            costs.append({'Item': 'Panel Assembly Labor', 'Quantity': f"{sandwich_panel_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR['panel_assembly_labor_m2'], 'Total (€)': sandwich_panel_total_area * FIYATLAR['panel_assembly_labor_m2']})

        # İç Alçıpan / İç ve Dış Alçıpan
        plasterboard_total_area = 0
        if project_inputs['plasterboard_interior_option']:
            plasterboard_total_area = wall_area
            costs.append({'Item': 'Interior Plasterboard (White)', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["gypsum_board_white_per_unit_price"], 'Total (€)': plasterboard_total_area * FIYATLAR["gypsum_board_white_per_unit_price"]})
            costs.append({'Item': 'Plasterboard Labor', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': plasterboard_total_area * FIYATLAR["plasterboard_labor_m2_avg"]})
            costs.append({'Item': MATERIAL_INFO_ITEMS['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
        
        if project_inputs['plasterboard_all_option']: # Hem iç hem dış
            plasterboard_total_area = wall_area * 2 # İç ve dış duvar
            costs.append({'Item': 'Interior & Exterior Plasterboard (White)', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["gypsum_board_white_per_unit_price"], 'Total (€)': plasterboard_total_area * FIYATLAR["gypsum_board_white_per_unit_price"]})
            costs.append({'Item': 'Plasterboard Labor', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': plasterboard_total_area * FIYATLAR["plasterboard_labor_m2_avg"]})
            costs.append({'Item': MATERIAL_INFO_ITEMS['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

        # İç Duvar OSB Malzemesi
        if project_inputs['osb_inner_wall_option']:
            osb_inner_wall_pieces = math.ceil(wall_area / OSB_PANEL_AREA_M2)
            costs.append({'Item': 'OSB Inner Wall Material', 'Quantity': f"{osb_inner_wall_pieces} adet", 'Unit Price (€)': FIYATLAR["osb_piece"], 'Total (€)': osb_inner_wall_pieces * FIYATLAR["osb_piece"]})

        # Duvar Yalıtımı
        if project_inputs['insulation_wall']:
            insulation_m2_cost = FIYATLAR["insulation_per_m2"]
            if project_inputs['insulation_material_type'] == 'Stone Wool':
                insulation_m2_cost = FIYATLAR['otb_stone_wool_price']
                costs.append({'Item': f"Wall Insulation ({project_inputs['insulation_material_type']})", 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': insulation_m2_cost, 'Total (€)': wall_area * insulation_m2_cost})
            elif project_inputs['insulation_material_type'] == 'Glass Wool':
                glass_wool_packets = math.ceil(wall_area / GLASS_WOOL_M2_PER_PACKET)
                glass_wool_cost = glass_wool_packets * FIYATLAR['glass_wool_5cm_packet_price']
                costs.append({'Item': f"Wall Insulation ({project_inputs['insulation_material_type']})", 'Quantity': f"{glass_wool_packets} paket", 'Unit Price (€)': FIYATLAR['glass_wool_5cm_packet_price'], 'Total (€)': glass_wool_cost})
            
        # Dış Cephe Kaplaması (Knauf Aquapanel)
        if project_inputs['exterior_cladding_m2_option'] and project_inputs['exterior_cladding_m2_val'] > 0:
            exterior_cladding_cost = project_inputs['exterior_cladding_m2_val'] * FIYATLAR['exterior_cladding_price_per_m2']
            costs.append({'Item': MATERIAL_INFO_ITEMS['knauf_aquapanel_gypsum_board_info'], 'Quantity': f"{project_inputs['exterior_cladding_m2_val']:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_price_per_m2'], 'Total (€)': exterior_cladding_cost})
            costs.append({'Item': MATERIAL_INFO_ITEMS['eps_styrofoam_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
            costs.append({'Item': MATERIAL_INFO_ITEMS['knauf_mineralplus_insulation_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
        
        # Dış Ahşap Kaplama (Lambiri)
        if project_inputs['exterior_wood_cladding_m2_option'] and project_inputs['exterior_wood_cladding_m2_val'] > 0:
            wood_cladding_cost = project_inputs['exterior_wood_cladding_m2_val'] * FIYATLAR['exterior_wood_cladding_m2_price']
            costs.append({'Item': MATERIAL_INFO_ITEMS['exterior_wood_cladding_lambiri_info'], 'Quantity': f"{project_inputs['exterior_wood_cladding_m2_val']:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'], 'Total (€)': wood_cladding_cost})

        # 3. Zemin Maliyetleri (Yalıtım ve Kaplama)
        if project_inputs['insulation_floor']:
            floor_insulation_cost = floor_area * FIYATLAR['insulation_per_m2']
            costs.append({'Item': 'Floor Insulation', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['insulation_per_m2'], 'Total (€)': floor_insulation_cost})
            
            # Zemin yalıtım malzemeleri
            if project_inputs['skirting_length_val'] > 0:
                costs.append({'Item': 'Skirting', 'Quantity': f"{project_inputs['skirting_length_val']:.2f} m", 'Unit Price (€)': FIYATLAR['skirting_meter_price'], 'Total (€)': project_inputs['skirting_length_val'] * FIYATLAR['skirting_meter_price']})
            if project_inputs['laminate_flooring_m2_val'] > 0:
                costs.append({'Item': 'Laminate Flooring 12mm', 'Quantity': f"{st.session_state.laminate_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['laminate_flooring_m2_price'], 'Total (€)': st.session_state.laminate_flooring_m2_val * FIYATLAR['laminate_flooring_m2_price']})
            if st.session_state.under_parquet_mat_m2_val > 0:
                costs.append({'Item': 'Under Parquet Mat 4mm', 'Quantity': f"{st.session_state.under_parquet_mat_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['under_parquet_mat_m2_price'], 'Total (€)': st.session_state.under_parquet_mat_m2_val * FIYATLAR['under_parquet_mat_m2_price']})
            if st.session_state.osb2_18mm_count_val > 0:
                costs.append({'Item': 'OSB2 18mm Panel', 'Quantity': f"{st.session_state.osb2_18mm_count_val} adet", 'Unit Price (€)': FIYATLAR['osb2_18mm_piece_price'], 'Total (€)': st.session_state.osb2_18mm_count_val * FIYATLAR['osb2_18mm_piece_price']})
            if st.session_state.galvanized_sheet_m2_val > 0:
                costs.append({'Item': '5mm Galvanized Sheet', 'Quantity': f"{st.session_state.galvanized_sheet_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['galvanized_sheet_m2_price'], 'Total (€)': st.session_state.galvanized_sheet_m2_val * FIYATLAR['galvanized_sheet_m2_price']})

            # Beton Panel Zemin (Elite pakete özel)
            if st.session_state.concrete_panel_floor_option and st.session_state.concrete_panel_floor_m2_val > 0:
                concrete_panel_cost = st.session_state.concrete_panel_floor_m2_val * FIYATLAR['concrete_panel_floor_price_per_m2']
                costs.append({'Item': MATERIAL_INFO_ITEMS['concrete_panel_floor_info'], 'Quantity': f"{st.session_state.concrete_panel_floor_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})

            # Teras Lamine Ahşap Zemin (Premium/Elite pakete özel)
            if st.session_state.terrace_laminated_wood_flooring_option and st.session_state.terrace_laminated_wood_flooring_m2_val > 0:
                terrace_laminated_cost = st.session_state.terrace_laminated_wood_flooring_m2_val * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2']
                costs.append({'Item': MATERIAL_INFO_ITEMS['treated_pine_floor_info'], 'Quantity': f"{st.session_state.terrace_laminated_wood_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_laminated_cost})

            # Porselen Fayans (Ekstra Zemin)
            if st.session_state.porcelain_tiles_option and st.session_state.porcelain_tiles_m2_val > 0:
                porcelain_tiles_cost = st.session_state.porcelain_tiles_m2_val * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                costs.append({'Item': MATERIAL_INFO_ITEMS['porcelain_tiles_info'], 'Quantity': f"{st.session_state.porcelain_tiles_m2_val:.2f} m²", 'Unit Price (€)': (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']), 'Total (€)': porcelain_tiles_cost})
                
            # 4. Doğramalar (Pencere ve Kapılar)
            window_cost = st.session_state.window_count * FIYATLAR['aluminum_window_piece']
            costs.append({'Item': f"Window ({st.session_state.window_size})", 'Quantity': st.session_state.window_count, 'Unit Price (€)': FIYATLAR['aluminum_window_piece'], 'Total (€)': window_cost})
            
            sliding_door_cost = st.session_state.sliding_door_count * FIYATLAR['sliding_glass_door_piece']
            if st.session_state.sliding_door_count > 0:
                costs.append({'Item': f"Sliding Glass Door ({st.session_state.sliding_door_size})", 'Quantity': st.session_state.sliding_door_count, 'Unit Price (€)': FIYATLAR['sliding_glass_door_piece'], 'Total (€)': sliding_door_cost})

            wc_window_cost = st.session_state.wc_window_count * FIYATLAR['wc_window_piece']
            if st.session_state.wc_window_count > 0:
                costs.append({'Item': f"WC Window ({st.session_state.wc_window_size})", 'Quantity': st.session_state.wc_window_count, 'Unit Price (€)': FIYATLAR['wc_window_piece'], 'Total (€)': wc_window_cost})

            wc_sliding_door_cost = st.session_state.wc_sliding_door_count * FIYATLAR['wc_sliding_door_piece']
            if st.session_state.wc_sliding_door_count > 0:
                costs.append({'Item': f"WC Sliding Door ({st.session_state.wc_sliding_door_size})", 'Quantity': st.session_state.wc_sliding_door_count, 'Unit Price (€)': FIYATLAR['wc_sliding_door_piece'], 'Total (€)': wc_sliding_door_cost})
            
            door_cost = st.session_state.door_count * FIYATLAR['door_piece']
            costs.append({'Item': f"Door ({st.session_state.door_size})", 'Quantity': st.session_state.door_count, 'Unit Price (€)': FIYATLAR['door_piece'], 'Total (€)': door_cost})
            
            total_doors_windows = st.session_state.window_count + st.session_state.sliding_door_count + st.session_state.wc_window_count + st.session_state.wc_sliding_door_count + st.session_state.door_count
            door_window_assembly_cost = total_doors_windows * FIYATLAR['door_window_assembly_labor_piece']
            costs.append({'Item': 'Door/Window Assembly Labor', 'Quantity': f"{total_doors_windows} adet", 'Unit Price (€)': FIYATLAR['door_window_assembly_labor_piece'], 'Total (€)': door_window_assembly_cost})

            # 5. Mutfak ve Banyo Tesisatları
            kitchen_cost = 0.0
            kitchen_type_display
# ==============================================================================
# BÖLÜM 3: Ek PDF Eki Oluşturma Fonksiyonları (Solar ve Yerden Isıtma)
# ==============================================================================

def _create_solar_appendix_elements_en_gr(solar_kw, solar_price, heading_style, normal_bilingual_style, price_total_style):
    """Güneş Enerjisi Sistemi eki için öğeleri oluşturur (İngilizce-Yunanca)."""
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
    solar_materials_p = [[Paragraph(clean_invisible_chars(cell), normal_bilingual_style) for cell in row] for row in solar_materials]
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
    """Güneş Enerjisi Sistemi eki için öğeleri oluşturur (Türkçe)."""
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
        ["Kablolama & Bağlantılar", "Tüm gerekli DC/AC kablolar, MC4 konnektörler ve güvenlik şalterleri"],
        ["Kurulum & Devreye Alma", "Tam profesyonel kurulum ve sistemin devreye alınması"],
    ]
    solar_materials_p = [[Paragraph(clean_invisible_chars(cell), normal_tr_style) for cell in row] for row in solar_materials]
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
    """Yerden Isıtma Sistemi eki için öğeleri oluşturur (İngilizce-Yunanca)."""
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
        ["Heating Elements / Στοιχεία Θέρμανσης", clean_invisible_chars(heating_materials_en_lines[0].strip()) + " / " + clean_invisible_chars(heating_materials_gr_lines[0].strip())],
        ["Transformer / Μετατροπέας", clean_invisible_chars(heating_materials_en_lines[1].strip()) + " / " + clean_invisible_chars(heating_materials_gr_lines[1].strip())],
        ["Thermostat / Θερμοστάτης", clean_invisible_chars(heating_materials_en_lines[2].strip()) + " / " + clean_invisible_chars(heating_materials_gr_lines[2].strip())],
        ["Wiring / Καλωδίωση", clean_invisible_chars(heating_materials_en_lines[3].strip()) + " / " + clean_invisible_chars(heating_materials_gr_lines[3].strip())],
        ["Insulation / Μόνωση", clean_invisible_chars(heating_materials_en_lines[4].strip()) + " / " + clean_invisible_chars(heating_materials_gr_lines[4].strip())],
        ["Subfloor Materials / Υλικά Υποδαπέδου", clean_invisible_chars(heating_materials_en_lines[5].strip()) + " / " + clean_invisible_chars(heating_materials_gr_lines[5].strip())],
    ]
    heating_table_p = [[Paragraph(clean_invisible_chars(cell), normal_bilingual_style) for cell in row] for row in heating_materials]
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
    """Yerden Isıtma Sistemi eki için öğeleri oluşturur (Türkçe)."""
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
        ["Isıtma Elemanları", clean_invisible_chars(heating_materials_tr_lines[0].strip())],
        ["Trafo", clean_invisible_chars(heating_materials_tr_lines[1].strip())],
        ["Termostat", clean_invisible_chars(heating_materials_tr_lines[2].strip())],
        ["Kablolama", clean_invisible_chars(heating_materials_tr_lines[3].strip())],
        ["Yalıtım Katmanları", clean_invisible_chars(heating_materials_tr_lines[4].strip())],
        ["Zemin Hazırlık Malzemeleri", clean_invisible_chars(heating_materials_tr_lines[5].strip())],
    ]
    heating_table_p = [[Paragraph(clean_invisible_chars(cell), normal_tr_style) for cell in row] for row in heating_materials]
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
    # ==============================================================================
# BÖLÜM 4.1: Müşteri Teklifi PDF Fonksiyonları - Ortak Ayarlar ve İngilizce/Yunanca PDF Başlangıcı
# ==============================================================================

def create_customer_proposal_pdf(house_price, solar_price, total_price, project_details, notes, customer_info):
    """Müşteri için profesyonel bir teklif PDF'i oluşturur (İngilizce ve Yunanca)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=40*mm, # Header için artırılmış margin
        bottomMargin=25*mm
    )

    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']
    # Logo verisini doc objesine ekle ki header/footer callback'leri erişebilsin
    doc.logo_data_b64 = st.session_state.get('logo_data_b64_global', None) 

    # Custom header/footer for proposals
    def _proposal_page_callback(canvas_obj, doc):
        draw_pdf_header_and_footer_common(canvas_obj, doc, doc.customer_name, doc.company_name, doc.logo_data_b64)
        # İmza çizgileri sadece son sayfada veya belirli sayfalarda olması daha mantıklı,
        # ancak önceki kodda _header_footer_for_proposal her çağrıldığında imzaları çiziyordu.
        # Bu yaklaşımı burada koruyorum, isterseniz değiştirilebilir.
        # Daha doğru bir yaklaşım için: Bu imzaları sadece doc.page == doc.pagesize[-1] olduğunda çizin.
        y_pos_signatures = 35 * mm
        line_length = 70 * mm
        canvas_obj.line(doc.leftMargin, y_pos_signatures, doc.leftMargin + line_length, y_pos_signatures)
        canvas_obj.setFont(MAIN_FONT, 7)
        canvas_obj.drawCentredString(doc.leftMargin + line_length / 2, y_pos_signatures - 4*mm, f"Buyer / {doc.customer_name.upper()}")
        canvas_obj.line(doc.width + doc.leftMargin - line_length, y_pos_signatures, doc.width + doc.leftMargin, y_pos_signatures)
        canvas_obj.setFont(MAIN_FONT, 7)
        canvas_obj.drawCentredString(doc.width + doc.leftMargin - line_length / 2, y_pos_signatures - 4*mm, f"Seller / {doc.company_name.upper()}")


    doc.onFirstPage = _proposal_page_callback
    doc.onLaterPages = _proposal_page_callback

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

    colored_table_header_style = ParagraphStyle(
        name='ColoredTableHeader', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.white, alignment=TA_LEFT
    )

    elements = []

    # --- Kapak Sayfası ---
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

    # --- Müşteri & Proje Bilgileri Bölümü (Tablolar halinde düzenlendi) ---
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

    # --- Teknik Özellikler Bölümü (Tablolar halinde düzenlendi) ---
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
        # İç duvar ve dış duvar özellikleri, eğer seçildiyse Yapı Malzemeleri altına eklendi
        if project_details['plasterboard_interior'] or project_details['plasterboard_all']: # Koşullu ekleme
            building_structure_table_data.append([Paragraph('<b>Interior Walls / Εσωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(INTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof / Στέγη</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        if project_details['facade_sandwich_panel_included']:
            building_structure_table_data.append([Paragraph('<b>Exterior Walls / Εξωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
    else: # Heavy Steel
        building_structure_table_data.append([Paragraph('<b>Construction Type / Τύπος Κατασκευής</b>', styles['NormalBilingual']), Paragraph('Heavy Steel', styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Steel Structure Details / Λεπτομέρειες Χαλύβδινης Κατασκευής</b>', styles['NormalBilingual']), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof / Στέγη</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        if project_details['facade_sandwich_panel_included']:
            building_structure_table_data.append([Paragraph('<b>Exterior Walls / Εξωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
    
    building_materials_table = Table(building_structure_table_data, colWidths=[60*mm, 110*mm])
    building_materials_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(building_materials_table)
    elements.append(Spacer(1, 5*mm))
    # ==============================================================================
# BÖLÜM 4.2: Müşteri Teklifi PDF Fonksiyonları - İngilizce/Yunanca Teklif Devamı ve Türkçe PDF Başlangıcı
# ==============================================================================

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
        [Paragraph('<b>Openings / Ανοίγματα</b>', styles['NormalBilingual']), Paragraph(f"Windows: {project_details['window_count']} ({project_details['window_size_val']} - {project_details['window_door_color']})<br/>Doors: {project_details['door_count']} ({project_details['door_size_val']} - {project_details['window_door_color']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size_val']} - {project_details['window_door_color']})<br/>WC Windows: {project_details['wc_window_count']} ({project_details['wc_window_size_val']} - {project_details['window_door_color']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sliding Doors: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size_val'] + ' - ' + project_details['window_door_color'] + ')'}<br/>Doors: {project_details['door_count']} ({project_details['door_size_val']})", styles['NormalBilingual'])],
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
    if project_details['kitchen_choice'] != 'No Kitchen': # check if kitchen was actually included in calculation
        other_features_table_data.append([Paragraph('<b>Kitchen Materials / Υλικά Κουζίνας</b>', styles['NormalBilingual']), Paragraph(KITCHEN_MATERIALS_EN, styles['NormalBilingual'])])

    other_features_table_data.append([Paragraph('<b>Shower/WC / Ντους/WC</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['shower_wc']), styles['NormalBilingual'])])
    if project_details['shower_wc']:
        other_features_table_data.append([Paragraph('<b>Shower/WC Materials / Υλικά Ντους/WC</b>', styles['NormalBilingual']), Paragraph(SHOWER_WC_MATERIALS_EN, styles['NormalBilingual'])])

    if project_details['electrical']:
        other_features_table_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph(ELECTRICAL_MATERIALS_EN.strip(), styles['NormalBilingual'])])
    else:
        other_features_table_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph('No / Όχι', styles['NormalBilingual'])])

    if project_details['plumbing']:
        other_features_table_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph(PLUMBING_MATERIALS_EN.strip(), styles['NormalBilingual'])])
    else:
        other_features_table_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph('No / Όχι', styles['NormalBilingual'])])
        # ==============================================================================
# BÖLÜM 4.2: create_customer_proposal_pdf - Kapak Sayfası, Müşteri & Proje Bilgileri (EN/GR)
# ==============================================================================

    # --- Kapak Sayfası ---
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

    # --- Müşteri & Proje Bilgileri Bölümü (Tablolar halinde düzenlendi) ---
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
    # ==============================================================================
# BÖLÜM 4.3: create_customer_proposal_pdf - İngilizce/Yunanca Teklif Teknik Özellikler (Yapı ve Malzeme)
# ==============================================================================

    # --- Teknik Özellikler Bölümü (Tablolar halinde düzenlendi) ---
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
        # İç duvar ve dış duvar özellikleri, eğer seçildiyse Yapı Malzemeleri altına eklendi
        if project_details['plasterboard_interior'] or project_details['plasterboard_all']: # Koşullu ekleme
            building_structure_table_data.append([Paragraph('<b>Interior Walls / Εσωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(INTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof / Στέγη</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        if project_details['facade_sandwich_panel_included']:
            building_structure_table_data.append([Paragraph('<b>Exterior Walls / Εξωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
    else: # Heavy Steel
        building_structure_table_data.append([Paragraph('<b>Construction Type / Τύπος Κατασκευής</b>', styles['NormalBilingual']), Paragraph('Heavy Steel', styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Steel Structure Details / Λεπτομέρειες Χαλύβδινης Κατασκευής</b>', styles['NormalBilingual']), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof / Στέγη</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        if project_details['facade_sandwich_panel_included']:
            building_structure_table_data.append([Paragraph('<b>Exterior Walls / Εξωτερικοί Τοίχοι</b>', styles['NormalBilingual']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
    
    building_materials_table = Table(building_structure_table_data, colWidths=[60*mm, 110*mm])
    building_materials_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(building_materials_table)
    elements.append(Spacer(1, 5*mm))
    # ==============================================================================
# BÖLÜM 4.4: create_customer_proposal_pdf - İngilizce/Yunanca Teklif Teknik Özellikler (İç Mekan, Yalıtım ve Doğramalar)
# ==============================================================================

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
        [Paragraph('<b>Openings / Ανοίγματα</b>', styles['NormalBilingual']), Paragraph(f"Windows: {project_details['window_count']} ({project_details['window_size_val']} - {project_details['window_door_color_val']})<br/>Doors: {project_details['door_count']} ({project_details['door_size_val']} - {project_details['window_door_color_val']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size_val']} - {project_details['window_door_color_val']})<br/>WC Windows: {project_details['wc_window_count']} ({project_details['wc_window_size_val']} - {project_details['window_door_color_val']}){'' if project_details['wc_sliding_door_count'] == 0 else '<br/>WC Sliding Doors: ' + str(project_details['wc_sliding_door_count']) + ' (' + project_details['wc_sliding_door_size_val'] + ' - ' + project_details['window_door_color_val'] + ')'}", styles['NormalBilingual'])],
    ]
    openings_table = Table(openings_table_data, colWidths=[60*mm, 110*mm])
    openings_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(openings_table)
    elements.append(Spacer(1, 5*mm))

    # --- Sayfa Sonu: Teknik Özellikler Bölümünün Kalanı Yeni Sayfada ---
    elements.append(PageBreak())
    # ==============================================================================
# BÖLÜM 4.5: create_customer_proposal_pdf - İngilizce/Yunanca Teklif Diğer Ek Özellikler (Aether Living Opsiyonları)
# ==============================================================================

    # Diğer Teknik Özellikler (Mutfak, Duş/WC, Elektrik, Sıhhi Tesisat, Ekstra Genel İlaveler)
    elements.append(Paragraph("ADDITIONAL TECHNICAL FEATURES / ΠΡΟΣΘΕΤΑ ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", styles['Heading'])) # Yeni başlık

    other_features_table_data = [
        [Paragraph('<b>Kitchen / Κουζίνα</b>', styles['NormalBilingual']), Paragraph(project_details['kitchen_type_display_en_gr'], styles['NormalBilingual'])],
    ]
    if project_details['kitchen_choice'] != 'No Kitchen': # check if kitchen was actually included in calculation
        other_features_table_data.append([Paragraph('<b>Kitchen Materials / Υλικά Κουζίνας</b>', styles['NormalBilingual']), Paragraph(KITCHEN_MATERIALS_EN, styles['NormalBilingual'])])

    other_features_table_data.append([Paragraph('<b>Shower/WC / Ντους/WC</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['shower_wc']), styles['NormalBilingual'])])
    if project_details['shower_wc']:
        other_features_table_data.append([Paragraph('<b>Shower/WC Materials / Υλικά Ντους/WC</b>', styles['NormalBilingual']), Paragraph(SHOWER_WC_MATERIALS_EN, styles['NormalBilingual'])])

    if project_details['electrical']:
        other_features_table_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph(ELECTRICAL_MATERIALS_EN.strip(), styles['NormalBilingual'])])
    else:
        other_features_table_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', styles['NormalBilingual']), Paragraph('No / Όχι', styles['NormalBilingual'])])

    if project_details['plumbing']:
        other_features_table_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph(PLUMBING_MATERIALS_EN.strip(), styles['NormalBilingual'])])
    else:
        other_features_table_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', styles['NormalBilingual']), Paragraph('No / Όχι', styles['NormalBilingual'])])

    # Ekstra Genel İlaveler (koşullu olarak ayrı tabloya)
    extra_general_additions_list_en_gr = []
    if project_details['heating']:
        extra_general_additions_list_en_gr.append(f"Floor Heating: {get_yes_no_empty(project_details['heating'])}")
    if project_details['solar']:
        extra_general_additions_list_en_gr.append(f"Solar System: {get_yes_no_empty(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '')
    if project_details['wheeled_trailer']:
        extra_general_additions_list_en_gr.append(f"Wheeled Trailer: {get_yes_no_empty(project_details['wheeled_trailer'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer'] else '')
    
    # Aether Living'e özel eklenenler (UI'dan kaldırılsa da raporlarda yer almalı)
    if project_details['smart_home_systems_option']:
        extra_general_additions_list_en_gr.append(f"Smart Home Systems: {get_yes_no_empty(project_details['smart_home_systems_option'])}")
    if project_details['white_goods_fridge_tv_option']:
        extra_general_additions_list_en_gr.append(f"White Goods (Fridge, TV): {get_yes_no_empty(project_details['white_goods_fridge_tv_option'])}")
    if project_details['sofa_option']:
        extra_general_additions_list_en_gr.append(f"Sofa: {get_yes_no_empty(project_details['sofa_option'])}")
    if project_details['security_camera_option']:
        extra_general_additions_list_en_gr.append(f"Security Camera Pre-Installation: {get_yes_no_empty(project_details['security_camera_option'])}")
    if project_details['exterior_cladding_m2_option'] and project_details['exterior_cladding_m2_val'] > 0:
        extra_general_additions_list_en_gr.append(f"Exterior Cladding (Knauf Aquapanel): Yes ({project_details['exterior_cladding_m2_val']:.2f} m²)")
    if project_details['bedroom_set_option']:
        extra_general_additions_list_en_gr.append(f"Bedroom Set: {get_yes_no_empty(project_details['bedroom_set_option'])}")
    if project_details['terrace_laminated_wood_flooring_option'] and project_details['terrace_laminated_wood_flooring_m2_val'] > 0:
        extra_general_additions_list_en_gr.append(f"Treated Pine Floor (Terrace Option): Yes ({project_details['terrace_laminated_wood_flooring_m2_val']:.2f} m²)")
    if project_details['porcelain_tiles_option'] and project_details['porcelain_tiles_m2_val'] > 0:
        extra_general_additions_list_en_gr.append(f"Porcelain Tiles: Yes ({project_details['porcelain_tiles_m2_val']:.2f} m²)")
    if project_details['concrete_panel_floor_option'] and project_details['concrete_panel_floor_m2_val'] > 0:
        extra_general_additions_list_en_gr.append(f"Concrete Panel Floor: Yes ({project_details['concrete_panel_floor_m2_val']:.2f} m²)")
    if project_details['premium_faucets_option']:
        extra_general_additions_list_en_gr.append(f"Premium Faucets: {get_yes_no_empty(project_details['premium_faucets_option'])}")
    if project_details['integrated_fridge_option']:
        extra_general_additions_list_en_gr.append(f"Integrated Refrigerator: {get_yes_no_empty(project_details['integrated_fridge_option'])}")
    if project_details['designer_furniture_option']:
        extra_general_additions_list_en_gr.append(f"Integrated Custom Design Furniture: {get_yes_no_empty(project_details['designer_furniture_option'])}")
    if project_details['italian_sofa_option']:
        extra_general_additions_list_en_gr.append(f"Italian Sofa: {get_yes_no_empty(project_details['italian_sofa_option'])}")
    if project_details['inclass_chairs_option'] and project_details['inclass_chairs_count'] > 0:
        extra_general_additions_list_en_gr.append(f"Inclass Chairs: Yes ({project_details['inclass_chairs_count']} pcs)")
    if project_details['brushed_granite_countertops_option'] and project_details['brushed_granite_countertops_m2_val'] > 0:
        extra_general_additions_list_en_gr.append(f"Brushed Granite Countertops: Yes ({project_details['brushed_granite_countertops_m2_val']:.2f} m²)")
    if project_details['exterior_wood_cladding_m2_option'] and project_details['exterior_wood_cladding_m2_val'] > 0:
        extra_general_additions_list_en_gr.append(f"Exterior Wood Cladding (Lambiri): Yes ({project_details['exterior_wood_cladding_m2_val']:.2f} m²)")


    if extra_general_additions_list_en_gr:
        other_features_table_data.append([Paragraph('<b>Extra General Additions / Έξτρα Γενικές Προσθήκες</b>', styles['NormalBilingual']), Paragraph("<br/>".join(extra_general_additions_list_en_gr), styles['NormalBilingual'])])

    other_features_table = Table(other_features_table_data, colWidths=[60*mm, 110*mm])
    other_features_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(other_features_table)
    elements.append(Spacer(1, 5*mm))
    # ==============================================================================
# BÖLÜM 4.6: create_customer_proposal_pdf - İngilizce/Yunanca Teslimat, Notlar, Fiyat ve Ödeme Planı (Başlangıç)
# ==============================================================================

    elements.append(Paragraph('<b>Estimated Delivery / Εκτιμώμενη Παράδοση</b>', styles['NormalBilingual']))
    elements.append(Paragraph(f"Approx. {project_details['delivery_duration_business_days']} business days / Περίπου {project_details['delivery_duration_business_days']} εργάσιμες ημέρες", styles['NormalBilingual']))
    elements.append(Spacer(1, 8*mm))

    if notes.strip():
        elements.append(Paragraph("CUSTOMER NOTES / ΣΗΜΕΙΩΣΕΙΣ ΠΕΛΑΤΗ", styles['Heading']))
        elements.append(Paragraph(notes, styles['NormalBilingual']))
        elements.append(Spacer(1, 8*mm))

    # --- Fiyat ve Ödeme Planı Bölümü ---
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
    final_page_elements.append(Paragraph(f"<b>Estimated Delivery / Εκτιμώμενη Παράδοση:</b> Approx. {project_details['delivery_duration_business_days']} business days / Περίπου {project_details['delivery_duration_business_days']} εργάσιμες ημέρες", payment_heading_style))
    final_page_elements.append(Spacer(1, 8*mm))
    # ==============================================================================
# BÖLÜM 4.7: create_customer_proposal_pdf - İngilizce/Yunanca Ödeme Planı Detayları ve Eklerin Çağrılması + PDF Kapanışı
# ==============================================================================

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
    # ==============================================================================
# BÖLÜM 4.8: create_customer_proposal_pdf_tr - Fonksiyon Tanımı, Doküman Ayarları ve Kapak Sayfası (Türkçe Teklif)
# ==============================================================================

def create_customer_proposal_pdf_tr(house_price, solar_price, total_price, project_details, notes, customer_info):
    """Müşteri için profesyonel bir teklif PDF'i oluşturur (Türkçe)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=40*mm, # Header için artırılmış margin
        bottomMargin=25*mm
    )

    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']
    # Logo verisini doc objesine ekle
    doc.logo_data_b64 = st.session_state.get('logo_data_b64_global', None) 

    # Custom header/footer for proposals (Türkçe)
    def _proposal_page_callback_tr(canvas_obj, doc):
        draw_pdf_header_and_footer_common(canvas_obj, doc, doc.customer_name, doc.company_name, doc.logo_data_b64)
        if doc.page % 2 == 1: # Sadece tek sayfalarda imza olursa diye örnek, isteğe bağlı
            y_pos_signatures = 35 * mm
            line_length = 70 * mm
            canvas_obj.line(doc.leftMargin, y_pos_signatures, doc.leftMargin + line_length, y_pos_signatures)
            canvas_obj.setFont(MAIN_FONT, 7)
            canvas_obj.drawCentredString(doc.leftMargin + line_length / 2, y_pos_signatures - 4*mm, f"Alıcı / {doc.customer_name.upper()}")
            canvas_obj.line(doc.width + doc.leftMargin - line_length, y_pos_signatures, doc.width + doc.leftMargin, y_pos_signatures)
            canvas_obj.setFont(MAIN_FONT, 7)
            canvas_obj.drawCentredString(doc.width + doc.leftMargin - line_length / 2, y_pos_signatures - 4*mm, f"Satıcı / {doc.company_name.upper()}")

    doc.onFirstPage = _proposal_page_callback_tr
    doc.onLaterPages = _proposal_page_callback_tr

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

    colored_table_header_style_tr = ParagraphStyle(
        name='ColoredTableHeaderTR', parent=styles['Normal'], fontSize=8, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.white, alignment=TA_LEFT
    )

    elements = []
    # --- Kapak Sayfası ---
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("PREFABRİK EV TEKLİFİ", title_style))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph(f"Müşteri: {customer_info['name']}", subtitle_style))
    if customer_info['company']:
        elements.append(Paragraph(f"Firma: {customer_info['company']}", subtitle_style))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d/%m/%Y')}", subtitle_style))
    elements.append(PageBreak())

    # --- Müşteri & Proje Bilgileri Bölümü ---
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
    # ==============================================================================
# BÖLÜM 5: Satış Sözleşmesi ve Dahili Rapor PDF Fonksiyonları
# ==============================================================================

def create_sales_contract_pdf(customer_info, house_sales_price, solar_sales_price, project_details, company_info):
    """Sağlanan şablon ve proje detaylarına göre bir satış sözleşmesi PDF'i oluşturur."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=40*mm, # Header için artırılmış margin
        bottomMargin=25*mm
    )
    doc.customer_name = customer_info['name']
    doc.company_name = COMPANY_INFO['name']
    doc.logo_data_b64 = st.session_state.get('logo_data_b64_global', None)

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

    # Başlık
    elements.append(Paragraph("SALES CONTRACT", contract_heading_style))
    elements.append(Spacer(1, 6*mm))

    # İlgili Taraflar (dinamik ID ve Şirket No ile güncellendi)
    today_date = datetime.now().strftime('%d')
    today_month = datetime.now().strftime('%B')
    today_year = datetime.now().year
    elements.append(Paragraph(f"This Agreement ('Agreement') is entered into as of this {today_date} day of {today_month}, {today_year} by and between,", contract_normal_style))
    elements.append(Paragraph(f"<b>{customer_info['name'].upper()}</b> (I.D. No: <b>{customer_info['id_no']}</b>) hereinafter referred to as the \"Buyer,\" and", contract_normal_style))
    elements.append(Paragraph(f"<b>{company_info['name'].upper()}</b>, Company No. <b>{company_info['company_no']}</b>, with a registered address at {company_info['address']}, hereinafter referred to as the \"Seller.\"", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Sözleşme Konusu
    elements.append(Paragraph("Subject of the Agreement:", contract_subheading_style))
    elements.append(Paragraph(f"A. The Seller agrees to complete and deliver to the Buyer the LIGHT STEEL STRUCTURE CONSTRUCTION (Tiny House) being constructed under its coordination at the address specified by the Buyer, in accordance with the specifications detailed in Appendix A.", contract_normal_style))
    elements.append(Paragraph("B. The details of the construction related to the Portable House project will be considered as appendixes to this agreement, which constitute integral parts of the present agreement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Tanımlar
    elements.append(Paragraph("1. Definitions:", contract_subheading_style))
    elements.append(Paragraph("1.1. \"Completion\" refers to the point at which the Light Steel Structure House is fully constructed, inspected, and ready for delivery.", contract_normal_style))
    elements.append(Paragraph("1.2. \"Delivery Date\" refers to the date on which the property is handed over to the Buyer, at which point the Buyer assumes full ownership and risk.", contract_normal_style))
    elements.append(Paragraph("1.3. \"Force Majeure Event\" means any event beyond the reasonable control of the Seller that prevents the timely delivery of the house, including but not limited to acts of God, war, terrorism, strikes, lockouts, natural disasters, or any other event recognized under law.", contract_normal_style))
    elements.append(Paragraph("1.4. \"House\" means the structure, as described in Appendix A.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Satış Fiyatı ve Ödeme Koşulları
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

    # Banka Detayları
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


    # Mülkün İncelemesi ve Kusurlar
    elements.append(Paragraph("3. Inspection of the Property and Defects:", contract_subheading_style))
    elements.append(Paragraph("3.1. The Buyer shall have the right to inspect the property during the construction process. The Buyer may request an inspection at any point with 7 days' notice.", contract_normal_style))
    elements.append(Paragraph("3.2. Any defects or concerns raised during inspections shall be addressed by the Seller at no additional cost to the Buyer. The buyer shall keep a written record of inspections which the byuer signs after each inspection, confirming the status of affairs.", contract_normal_style))
    elements.append(Paragraph("3.3. Final inspection of the completed house will occur within 10 days of the delivery date, after which the Buyer shall provide written a list of defects.", contract_normal_style))
    elements.append(Paragraph("3.4. If there are any possible defects, the seller will restore them within ........ days/months and notify the buyer. In such a case, the delivery of the house will be determined accordingly.", contract_normal_style))
    elements.append(Paragraph("3.5. The seller will repair and/or replace any possible defects, within ........ days/months.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Evin Tamamlanması
    elements.append(Paragraph("4. Completion of the House:", contract_subheading_style))
    elements.append(Paragraph("4.1. The Seller will issue an invoice and deliver the property to the Buyer after the full payment of the sales price and all amounts specified in Article 2, upon completion of the construction of the light steel structure house. Document procurement related to this matter is outside the specified time for delivery.", contract_normal_style))
    elements.append(Paragraph("4.2. In order to complete processes such as partitioning, transfer, etc., the Buyer agrees to assist the Seller and, for this purpose, to apply to official, semi-official, and other authorities jointly or individually with the Seller and/or other shareholder or shareholders, to sign necessary signatures, fill out forms, and/or, if necessary, appoint the Seller as a representative.", contract_normal_style))
    elements.append(Paragraph("4.3. The Buyer will be responsible for the Tax (VAT) of the house from the delivery of the light steel structure house.", contract_normal_style))
    elements.append(Paragraph("4.4. Despite the Seller's completion of the necessary legal procedures, the Seller will not be responsible for delays and extra transit expenses related to customs procedures and exit of the materials of this house.", contract_normal_style))
    
    # project_details['delivery_duration_business_days'] zaten calculate() içinde hesaplanmıştır
    elements.append(Paragraph(f"4.5. The House will be delivered within approximately {project_details['delivery_duration_business_days']} working days (excluding weekends and public holidays), as from the signing of this agreement.", contract_normal_style))
    elements.append(Paragraph("4.6. Any delays caused by Force Majeure events or by the Buyer shall extend the delivery period accordingly.", contract_normal_style))
    elements.append(Paragraph("4.7. If the seller fails to deliver the house within the set delivery date (4.5.), due to unforeseen delays, he is obliged to notify the buyer in writing, stating the reasons for the delay and proposing ways of overcoming the said delay.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Fesih
    elements.append(Paragraph("5. Termination:", contract_subheading_style))
    elements.append(Paragraph("5.1. In case the Buyer fails to fulfill any of the conditions of this agreement, the Seller has the right to terminate the agreement immediately, by sending a written notification explaining the reasons for such termination.", contract_normal_style))
    elements.append(Paragraph("5.2. If the Buyer decides not to purchase the house by the given date, the Buyer acknowledges and undertakes that they will lose the entire deposit given as compensation for damages. In the event of a problem caused by the Seller or if the Seller decides not to transfer to the Buyer, the Seller will refund the full deposit to the Buyer.", contract_normal_style))
    elements.append(Paragraph("5.3. All notices to be given under this agreement will be deemed to have been given or served by being left at the above-mentioned addresses of the parties or by being sent by post.", contract_normal_style))
    elements.append(Paragraph("5.4. This agreement is made in 2 copies, signed and initialed by the parties.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Bildirimler
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

    # Garanti ve Kusurlara İlişkin Sorumluluk
    elements.append(Paragraph("7. Warranty and Defects liability:", contract_subheading_style))
    elements.append(Paragraph("7.1. The seller warrants that the house will be free if defects in materials and workmanship, for a period of ........ (months/year), from the day of delivery.", contract_normal_style))
    elements.append(Paragraph("7.2. The said warrantee does not cover damages caused by misuse, negligence, or external factors (e.g. natural disasters).", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Uygulanacak Hukuk
    elements.append(Paragraph("8. Applicable Law:", contract_subheading_style))
    elements.append(Paragraph("This Agreement and any matter relating thereto shall be governed, construed and interpreted in accordance with the laws of the Republic of Cyprus any dispute arising under it shall be subject to the exclusive jurisdiction of the Cyprus courts.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Anlaşmazlık Çözümü - Arabuluculuk / Tahkim
    elements.append(Paragraph("9. Dispute Resolution - Mediation / Arbitration", contract_subheading_style))
    elements.append(Paragraph("9.1. Any disputes arising under this Agreement and prior to any litigation before the relevant Court, will first be addressed through negotiation between the parties.", contract_normal_style))
    elements.append(Paragraph("9.2. If the dispute cannot be resolved through negotiation, the parties agree to submit to mediation in the Republic of Cyprus, according to Mediation Act §159(1)/2012.", contract_normal_style))
    elements.append(Paragraph("9.3. If mediation fails, the dispute will be resolved through binding arbitration under the rules of [Arbitration Organization].", contract_normal_style))
    elements.append(Paragraph("9.4. The above alternative dispute resolution, do not conflict the Constitutional right of either party may seek relief in the courts of Cyprus if there will be no amicable settlement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Değişiklikler
    elements.append(Paragraph("10. Amendements:", contract_subheading_style))
    elements.append(Paragraph("Any amendements or modifications to this agreement, must be made in writing and signed by both parties prior to a written notification as above (term 6).", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    # Son Madde
    elements.append(Paragraph("11. This Agreement is made in two (2) identical copies in English language, with each party receiving one copy of the Agreement.", contract_normal_style))
    elements.append(Spacer(1, 6*mm)) # Reduced space

    elements.append(Paragraph("IN WITNESS THEREOF, the parties have caused their authorized representatives to sign this Agreement on their behalf, the day and year above written.", contract_normal_style))
    elements.append(Spacer(1, 25*mm)) # Yeterli boşluk

    # Son İmza Bloğu (belgenin en sonunda, ortalanmış, gerçek imzalar için daha büyük boşluk)
    final_signature_data = [
        [Paragraph(f"<b>THE SELLER</b><br/><br/><br/>________________________________________<br/>For and on behalf of<br/>{company_info['name'].upper()}", contract_signature_style),
         Paragraph(f"<b>THE BUYER</b><br/><br/><br/>________________________________________<br/>{customer_info['name'].upper()}<br/>I.D. No: {customer_info['id_no']}", contract_signature_style)]
    ]
    # Metnin sığmasını ve çizgilerin orantılı olmasını sağlamak için colWidths'i ayarla
    final_signature_table = Table(final_signature_data, colWidths=[80*mm, 80*mm], hAlign='CENTER')
    final_signature_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(final_signature_table)

    elements.append(Spacer(1, 10*mm)) # İmzalar ve tarih arası boşluk
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", contract_normal_style))

    # Tanıklar
    elements.append(Spacer(1, 8*mm)) # Tanıklar öncesi boşluk
    elements.append(Paragraph("Witnesses:", contract_normal_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("1 (Sgn.) _____________________________________", contract_normal_style))
    elements.append(Paragraph("(name and i.d.)", contract_normal_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("2 (Sgn.) _____________________________________", contract_normal_style))
    elements.append(Paragraph("(name and i.d.)", contract_normal_style))

    elements.append(PageBreak())

    # EK "A" - Çalışma Kapsamı (Tablolar halinde düzenlendi)
    elements.append(Paragraph("APPENDIX \"A\" - SCOPE OF WORK", contract_heading_style))
    elements.append(Paragraph("Within the scope of this sales agreement, the specified Light Steel Structure House will have the following features and materials:", contract_normal_style))
    elements.append(Spacer(1, 5*mm))

    def get_yes_no_en(value):
        return 'Yes' if value else ''

    # Boyutlar ve Alan
    dimensions_area_table_data = []
    dimensions_area_table_data.append([Paragraph("<b>Dimensions and Area:</b>", contract_subheading_style), Paragraph(f"The house has dimensions of {project_details['width']}m x {project_details['length']}m x {project_details['height']}m. It has a total area of {project_details['area']:.2f} m².", contract_normal_style)])
    dimensions_area_table = Table(dimensions_area_table_data, colWidths=[40*mm, 130*mm])
    dimensions_area_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(dimensions_area_table)
    elements.append(Spacer(1, 5*mm))

    # Yapı Malzemeleri
    construction_materials_table_data = []
    if project_details['structure_type'] == 'Light Steel':
        construction_materials_table_data.append([Paragraph('<b>Construction Type:</b>', contract_subheading_style), Paragraph('Light Steel', contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Steel Structure Details:</b>', contract_subheading_style), Paragraph(LIGHT_STEEL_BUILDING_STRUCTURE_EN_GR, contract_normal_style)])
        if project_details['plasterboard_interior'] or project_details['plasterboard_all']: # Koşullu ekleme
            construction_materials_table_data.append([Paragraph('<b>Interior Walls:</b>', contract_subheading_style), Paragraph(INTERIOR_WALLS_DESCRIPTION_EN_GR, contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Roof:</b>', contract_subheading_style), Paragraph(ROOF_DESCRIPTION_EN_GR, contract_normal_style)])
        if project_details['facade_sandwich_panel_included']:
            construction_materials_table_data.append([Paragraph('<b>Exterior Walls:</b>', contract_subheading_style), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, contract_normal_style)])
    else: # Heavy Steel
        construction_materials_table_data.append([Paragraph('<b>Construction Type:</b>', contract_subheading_style), Paragraph('Heavy Steel', contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Steel Structure Details:</b>', contract_subheading_style), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR, contract_normal_style)])
        construction_materials_table_data.append([Paragraph('<b>Roof:</b>', contract_subheading_style), Paragraph(ROOF_DESCRIPTION_EN_GR, contract_normal_style)])
        if project_details['facade_sandwich_panel_included']:
            construction_materials_table_data.append([Paragraph('<b>Exterior Walls:</b>', contract_subheading_style), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, contract_normal_style)])
    
    construction_materials_table = Table(construction_materials_table_data, colWidths=[40*mm, 130*mm])
    construction_materials_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(construction_materials_table)
    elements.append(Spacer(1, 5*mm))

    # İç Mekan ve Yalıtım (Interior and Insulation)
    interior_insulation_table_data_contract_en = [
        [Paragraph('<b>Interior Covering:</b>', contract_subheading_style), Paragraph(f"Floor Covering: {project_details['floor_covering_type']}. Inner Wall OSB: {get_yes_no_en(project_details['osb_inner_wall_option'])}. Interior Walls: Plasterboard {get_yes_no_en(project_details['plasterboard_interior_option'] or project_details['plasterboard_all_option'])}.", contract_normal_style)],
        [Paragraph('<b>Insulation:</b>', contract_subheading_style), Paragraph(f"Floor Insulation: {get_yes_no_en(project_details['insulation_floor'])}. Wall Insulation: {get_yes_no_en(project_details['insulation_wall'])}.", contract_normal_style)],
    ]
    # Zemin yalıtım malzemeleri listesi doğrudan yalıtım bölümünün altına (Sözleşme'de de)
    if project_details['insulation_floor']:
        floor_insulation_details_contract_en = []
        floor_insulation_details_contract_en.append(f"<b>Floor Insulation Materials:</b>")
        if project_details['skirting_length_val'] > 0:
            floor_insulation_details_contract_en.append(f"• Skirting ({project_details['skirting_length_val']:.2f} m)")
        if project_details['laminate_flooring_m2_val'] > 0:
            floor_insulation_details_contract_en.append(f"• Laminate Flooring 12mm ({project_details['laminate_flooring_m2_val']:.2f} m²)")
        if project_details['under_parquet_mat_m2_val'] > 0:
            floor_insulation_details_contract_en.append(f"• Under Parquet Mat 4mm ({project_details['under_parquet_mat_m2_val']:.2f} m²)")
        if project_details['osb2_18mm_count_val'] > 0:
            floor_insulation_details_contract_en.append(f"• OSB2 18mm or Concrete Panel 18mm ({project_details['osb2_18mm_count_val']} pcs)")
        if project_details['galvanized_sheet_m2_val'] > 0:
            floor_insulation_details_contract_en.append(f"• 5mm Galvanized Sheet ({project_details['galvanized_sheet_m2_val']:.2f} m²)")
        floor_insulation_details_contract_en.append("<i>Note: Insulation thickness can be increased. Ceramic coating can be preferred. (without concrete, special floor system)</i>")
        
        interior_insulation_table_data_contract_en.append([Paragraph("<b>Floor Insulation Details:</b>", contract_subheading_style), Paragraph("<br/>".join(floor_insulation_details_contract_en), contract_normal_style)])

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
    if project_details['plasterboard_interior_option'] or project_details['plasterboard_all_option']:
        additional_features_table_data.append([Paragraph("<b>Interior Plasterboard:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['plasterboard_interior_option'] or project_details['plasterboard_all_option']), contract_normal_style)])
    if project_details['osb_inner_wall_option']:
        additional_features_table_data.append([Paragraph("<b>Inner Wall OSB Material:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['osb_inner_wall_option']), contract_normal_style)])
    
    # Mutfak ve Duş/WC (eğer pakete dahil değilse ve seçiliyse)
    if project_details['kitchen_choice'] != 'No Kitchen':
        additional_features_table_data.append([Paragraph("<b>Kitchen:</b>", contract_subheading_style), Paragraph(project_details['kitchen_type_display_en_gr'], contract_normal_style)])
    if project_details['shower_wc']:
        additional_features_table_data.append([Paragraph("<b>Shower/WC:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['shower_wc']), contract_normal_style)])
    
    # Diğer Opsiyonel Özellikler (Aether Living'e özel olanlar dahil)
    if project_details['heating']:
        additional_features_table_data.append([Paragraph("<b>Floor Heating:</b>", contract_subheading_style), Paragraph(get_yes_no_en(project_details['heating']), contract_normal_style)])
    if project_details['solar']:
        additional_features_table_data.append([Paragraph("<b>Solar System:</b>", contract_subheading_style), Paragraph(f"{get_yes_no_en(project_details['solar'])} ({project_details['solar_kw']} kW)" if project_details['solar'] else '', contract_normal_style)])
    if project_details['wheeled_trailer']:
        additional_features_table_data.append([Paragraph("<b>Wheeled Trailer:</b>", contract_subheading_style), Paragraph(f"{get_yes_no_en(project_details['wheeled_trailer'])} ({format_currency(project_details['wheeled_trailer_price'])})" if project_details['wheeled_trailer'] else '', contract_normal_style)])
    
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

    # PDF oluştur
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
# ==============================================================================
# BÖLÜM 6: run_streamlit_app() - Uygulama Başlatma ve session_state Yönetimi
# ==============================================================================

# ====================== ANA UYGULAMA ======================
def run_streamlit_app():
    # Sayfa yapılandırması
    st.set_page_config(layout="wide", page_title="Premium Home Maliyet Hesaplayıcı")

    # Custom CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
        color: #000000; /* Yazı rengi siyah olarak ayarlandı */
    }
    
    html, body {
        background-color: #f8fafc; /* Açık Mod varsayılanı */
    }
    
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
        border: none;
        font-weight: 500;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        background-color: #2c5282;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .section-title {
        background-color: #3182ce;
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .warning {
        color: #e53e3e;
        background-color: #fff5f5;
        padding: 10px 15px;
        border-radius: 6px;
        border: 1px solid #fed7d7;
        margin-bottom: 1rem;
    }
    
    .stExpander > div {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .stDataFrame {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .stAlert {
        border-radius: 8px;
    }
    
    .footer {
        text-align: center;
        padding: 1rem;
        color: #718096;
        font-size: 0.9rem;
        margin-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🏠 Premium Home Maliyet Hesaplayıcı")

    # --- Oturum Durumu Başlatma ---
    # Tüm st.session_state anahtarları ve varsayılan değerleri
    session_state_defaults = {
        'customer_name': 'GENEL',
        'customer_company': '',
        'customer_address': '',
        'customer_city': '',
        'customer_phone': '',
        'customer_email': '',
        'customer_id_no': '',
        'aether_package_choice': 'None',
        'width_val': 10.0,
        'length_val': 8.0,
        'height_val': 2.6,
        'structure_type': 'Light Steel',
        'welding_type': 'Standard Welding (160€/m²)',
        'room_config': 'Empty Model',
        'profile_100x100_count': 0,
        'profile_100x50_count': 0,
        'profile_40x60_count': 0,
        'profile_50x50_count': 0,
        'profile_120x60x5mm_count': 0,
        'profile_HEA160_count': 0,
        'plasterboard_interior_option': False,
        'plasterboard_all_option': False,
        'osb_inner_wall_option': False,
        'facade_sandwich_panel_option': False,
        'window_count': 4,
        'window_size_val': "100x100 cm",
        'sliding_door_count': 0,
        'sliding_door_size_val': "200x200 cm",
        'wc_window_count': 1,
        'wc_window_size_val': "60x50 cm",
        'wc_sliding_door_count': 0,
        'wc_sliding_door_size_val': "140x70 cm",
        'door_count': 2,
        'door_size_val': "90x210 cm",
        'window_door_color_val': 'White',
        'kitchen_choice': 'No Kitchen',
        'shower_wc': False,
        'wc_ceramic': False,
        'wc_ceramic_area': 0.0,
        'electrical': False,
        'plumbing': False,
        'insulation_floor': False,
        'skirting_length_val': 0.0,
        'laminate_flooring_m2_val': 0.0,
        'under_parquet_mat_m2_val': 0.0,
        'osb2_18mm_count_val': 0,
        'galvanized_sheet_m2_val': 0.0,
        'insulation_material_type': 'Stone Wool', # Yeni yalıtım tipi
        'insulation_wall': False,
        'transportation': False,
        'heating': False,
        'solar': False,
        'solar_kw': 5,
        'wheeled_trailer': False,
        'wheeled_trailer_price': 0.0,
        'profit_rate': ('20%', 0.20), # Tuple olarak tanımlandı
        'customer_notes': "",
        'pdf_language': ('Turkish', 'tr'), # Varsayılan Türkçe

        # Aether Living seçenekleri (varsayılanlar UI'dan kaldırıldı, kodda yönetilecek)
        'exterior_cladding_m2_option': False,
        'exterior_cladding_m2_val': 0.0,
        'exterior_wood_cladding_m2_option': False,
        'exterior_wood_cladding_m2_val': 0.0,
        'porcelain_tiles_option': False,
        'porcelain_tiles_m2_val': 0.0,
        'concrete_panel_floor_option': False,
        'concrete_panel_floor_m2_val': 0.0,
        'bedroom_set_option': False,
        'sofa_option': False,
        'smart_home_systems_option': False,
        'security_camera_option': False,
        'security_camera_count': 1, # Default 1 adet kamera için
        'white_goods_fridge_tv_option': False,
        'premium_faucets_option': False,
        'integrated_fridge_option': False,
        'designer_furniture_option': False,
        'italian_sofa_option': False,
        'inclass_chairs_option': False,
        'inclass_chairs_count': 0,
        'brushed_granite_countertops_option': False,
        'brushed_granite_countertops_m2_val': 0.0,
        'terrace_laminated_wood_flooring_option': False,
        'terrace_laminated_wood_flooring_m2_val': 0.0,
        
        # Logo verisini bir kez çekip session state'te tut
        'logo_data_b64_global': None, 
    }

    # Streamlit oturum durumunu başlat veya güncelle
    for key, default_value in session_state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # Logo'yu uygulama başladığında bir kez çek ve session_state'e kaydet
    if st.session_state.logo_data_b64_global is None:
        st.session_state.logo_data_b64_global = get_company_logo_base64(COMPANY_INFO['logo_url'])

    # --- Paket seçimine göre varsayılan değerleri UI elementlerine uygula ---
    # Bu bölüm, paket seçimi değiştiğinde UI'daki bazı değerleri otomatik günceller.
    # Kullanıcılar daha sonra bu değerleri manuel olarak değiştirebilir.
    _kitchen_choice_default_val = st.session_state.kitchen_choice # Mevcut değeri koru
    _shower_wc_default_val = st.session_state.shower_wc
    _electrical_default_val = st.session_state.electrical
    _plumbing_default_val = st.session_state.plumbing
    _insulation_floor_default_val = st.session_state.insulation_floor
    _insulation_wall_default_val = st.session_state.insulation_wall
    _floor_covering_default_val = st.session_state.floor_covering
    _heating_default_val = st.session_state.heating
    _solar_default_val = st.session_state.solar
    _plasterboard_interior_default_val = st.session_state.plasterboard_interior_option_val
    _plasterboard_all_default_val = st.session_state.plasterboard_all_option_val
    _osb_inner_wall_default_val = st.session_state.osb_inner_wall_option_val
    _facade_sandwich_panel_default_val = st.session_state.facade_sandwich_panel_option_val
    _bedroom_set_default_val = st.session_state.bedroom_set_option
    _brushed_granite_countertops_default_val = st.session_state.brushed_granite_countertops_option
    _terrace_laminated_wood_flooring_default_val = st.session_state.terrace_laminated_wood_flooring_option
    _exterior_cladding_default_val = st.session_state.exterior_cladding_m2_option
    _concrete_panel_floor_default_val = st.session_state.concrete_panel_floor_option
    _premium_faucets_default_val = st.session_state.premium_faucets_option
    _integrated_fridge_default_val = st.session_state.integrated_fridge_option
    _designer_furniture_default_val = st.session_state.designer_furniture_option
    _italian_sofa_default_val = st.session_state.italian_sofa_option
    _inclass_chairs_default_val = st.session_state.inclass_chairs_option
    _inclass_chairs_count_default_val = st.session_state.inclass_chairs_count
    _smart_home_systems_default_val = st.session_state.smart_home_systems_option
    _security_camera_default_val = st.session_state.security_camera_option
    _white_goods_default_val = st.session_state.white_goods_fridge_tv_option
    _exterior_wood_cladding_default_val = st.session_state.exterior_wood_cladding_m2_option
    _porcelain_tiles_default_val = st.session_state.porcelain_tiles_option
    _solar_capacity_default_val = st.session_state.solar_kw # Solar kapasite de eklendi
    _insulation_material_type_default_val = st.session_state.insulation_material_type # Yalıtım malzeme tipi de eklendi

    # Paket seçimine göre varsayılanları güncelle
    if st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
        _kitchen_choice_default_val = 'Standard Kitchen'
        _shower_wc_default_val = True
        _electrical_default_val = True
        _plumbing_default_val = True
        _insulation_floor_default_val = True
        _insulation_wall_default_val = True
        _floor_covering_default_val = 'Laminate Parquet'
        _heating_default_val = False # Standard pakette ısıtma yok
        _solar_default_val = False # Standard pakette solar yok

        # Diğer Aether Living opsiyonlarını sıfırla
        _bedroom_set_default_val = False
        _brushed_granite_countertops_default_val = False
        _terrace_laminated_wood_flooring_default_val = False
        _exterior_cladding_default_val = False
        _concrete_panel_floor_default_val = False
        _premium_faucets_default_val = False
        _integrated_fridge_default_val = False
        _designer_furniture_default_val = False
        _italian_sofa_default_val = False
        _inclass_chairs_default_val = False
        _inclass_chairs_count_default_val = 0
        _smart_home_systems_default_val = False
        _security_camera_default_val = False
        _white_goods_default_val = False
        _exterior_wood_cladding_default_val = False
        _porcelain_tiles_default_val = False
        _plasterboard_interior_default_val = True # Standard pakette iç alçıpan var
        _plasterboard_all_default_val = False # Dış alçıpan yok
        _osb_inner_wall_default_val = True # Standard pakette OSB iç duvar var
        _facade_sandwich_panel_default_val = True # Standard pakette dış cephe sandviç panel var

    elif st.session_state.aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
        _kitchen_choice_default_val = 'Standard Kitchen'
        _shower_wc_default_val = True
        _electrical_default_val = True
        _plumbing_default_val = True
        _insulation_floor_default_val = True
        _insulation_wall_default_val = True
        _floor_covering_default_val = 'Laminate Parquet'
        _heating_default_val = False
        _solar_default_val = False
        
        _bedroom_set_default_val = True
        _brushed_granite_countertops_default_val = True
        _terrace_laminated_wood_flooring_default_val = True
        
        # Diğer Aether Living opsiyonlarını sıfırla
        _exterior_cladding_default_val = False
        _concrete_panel_floor_default_val = False
        _premium_faucets_default_val = False
        _integrated_fridge_default_val = False
        _designer_furniture_default_val = False
        _italian_sofa_default_val = False
        _inclass_chairs_default_val = False
        _inclass_chairs_count_default_val = 0
        _smart_home_systems_default_val = False
        _security_camera_default_val = False
        _white_goods_default_val = False
        _exterior_wood_cladding_default_val = False
        _porcelain_tiles_default_val = False
        _plasterboard_interior_default_val = True
        _plasterboard_all_default_val = False
        _osb_inner_wall_default_val = True
        _facade_sandwich_panel_default_val = True

    elif st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
        _kitchen_choice_default_val = 'Special Design Kitchen'
        _shower_wc_default_val = True
        _electrical_default_val = True
        _plumbing_default_val = True
        _insulation_floor_default_val = True
        _insulation_wall_default_val = True
        _floor_covering_default_val = 'Ceramic'
        _heating_default_val = True
        _solar_default_val = True
        _exterior_cladding_default_val = True 
        _concrete_panel_floor_default_val = True
        _premium_faucets_default_val = True
        _integrated_fridge_default_val = True
        _designer_furniture_default_val = True
        _italian_sofa_default_val = True
        _inclass_chairs_default_val = True
        _inclass_chairs_count_default_val = 1
        _smart_home_systems_default_val = True
        _security_camera_default_val = True
        _white_goods_default_val = True
        _bedroom_set_default_val = True
        _brushed_granite_countertops_default_val = True
        _terrace_laminated_wood_flooring_default_val = True # Elite'te de teras zemin var
        _plasterboard_all_default_val = True # Elite pakette iç ve dış alçıpan varsayılan
        _osb_inner_wall_default_val = True # Elite pakette OSB iç duvar varsayılan
        _facade_sandwich_panel_default_val = True # Elite pakette dış cephe sandviç panel varsayılan
        _exterior_wood_cladding_default_val = False # Ahşap kaplama manuel kalır
        _porcelain_tiles_default_val = True # Porselen fayans elite pakette otomatik seçili

    # Paket seçimi değiştiğinde, UI'da gösterilen değerleri otomatik olarak güncelle
    # Her bir widget'ın value parametresine doğrudan st.session_state'teki ilgili değişken atanır.
    # st.session_state'in kendi değeri de paket mantığı tarafından güncellenir.
    st.session_state.kitchen_choice = _kitchen_choice_default_val
    st.session_state.shower_wc = _shower_wc_default_val
    st.session_state.electrical = _electrical_default_val
    st.session_state.plumbing = _plumbing_default_val
    st.session_state.insulation_floor = _insulation_floor_default_val
    st.session_state.insulation_wall = _insulation_wall_default_val
    st.session_state.floor_covering = _floor_covering_default_val
    st.session_state.heating = _heating_default_val
    st.session_state.solar = _solar_default_val
    st.session_state.plasterboard_interior_option = _plasterboard_interior_default_val
    st.session_state.plasterboard_all_option = _plasterboard_all_default_val
    st.session_state.osb_inner_wall_option = _osb_inner_wall_default_val
    st.session_state.facade_sandwich_panel_option = _facade_sandwich_panel_default_val
    st.session_state.bedroom_set_option = _bedroom_set_default_val
    st.session_state.brushed_granite_countertops_option = _brushed_granite_countertops_default_val
    st.session_state.terrace_laminated_wood_flooring_option = _terrace_laminated_wood_flooring_default_val
    st.session_state.exterior_cladding_m2_option = _exterior_cladding_default_val
    st.session_state.concrete_panel_floor_option = _concrete_panel_floor_default_val
    st.session_state.premium_faucets_option = _premium_faucets_default_val
    st.session_state.integrated_fridge_option = _integrated_fridge_default_val
    st.session_state.designer_furniture_option = _designer_furniture_default_val
    st.session_state.italian_sofa_option = _italian_sofa_default_val
    st.session_state.inclass_chairs_option = _inclass_chairs_default_val
    st.session_state.inclass_chairs_count = _inclass_chairs_count_default_val
    st.session_state.smart_home_systems_option = _smart_home_systems_default_val
    st.session_state.security_camera_option = _security_camera_default_val
    st.session_state.white_goods_fridge_tv_option = _white_goods_default_val
    st.session_state.exterior_wood_cladding_m2_option = _exterior_wood_cladding_default_val
    st.session_state.porcelain_tiles_option = _porcelain_tiles_default_val
    st.session_state.solar_kw = _solar_capacity_default_val # Solar kapasite de güncellendi
    st.session_state.insulation_material_type = _insulation_material_type_default_val # Yalıtım malzeme tipi de güncellendi


    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-title'>BOYUTLAR</div>", unsafe_allow_html=True)
        st.session_state.width_val = st.number_input("Genişlik (m):", value=st.session_state.width_val, step=0.1)
        st.session_state.length_val = st.number_input("Uzunluk (m):", value=st.session_state.length_val, step=0.1)
        st.session_state.height_val = st.number_input("Yükseklik (m):", value=st.session_state.height_val, step=0.1)

        st.markdown("<div class='section-title'>YAPI</div>", unsafe_allow_html=True)
        st.session_state.structure_type = st.radio("Yapı Tipi:", ['Light Steel', 'Heavy Steel'], index=['Light Steel', 'Heavy Steel'].index(st.session_state.structure_type), key="structure_type_radio")
        st.session_state.welding_type = st.selectbox("Çelik Kaynak İşçiliği:", ['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'], index=['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'].index(st.session_state.welding_type), key="welding_labor_select")

        plasterboard_interior_disabled = (st.session_state.structure_type == 'Heavy Steel')
        plasterboard_all_disabled = (st.session_state.structure_type == 'Light Steel')

        st.session_state.plasterboard_interior_option = st.checkbox(
            "İç Alçıpan Dahil Et",
            value=st.session_state.plasterboard_interior_option,
            disabled=plasterboard_interior_disabled
        )
        st.session_state.plasterboard_all_option = st.checkbox(
            "İç ve Dış Alçıpan Dahil Et",
            value=st.session_state.plasterboard_all_option,
            disabled=plasterboard_all_disabled
        )
        
        osb_inner_wall_disabled = not (st.session_state.plasterboard_interior_option or st.session_state.plasterboard_all_option)
        st.session_state.osb_inner_wall_option = st.checkbox(
            "İç Duvar OSB Malzemesi Dahil Et",
            value=st.session_state.osb_inner_wall_option,
            disabled=osb_inner_wall_disabled
        )

        facade_sandwich_panel_disabled = (st.session_state.structure_type == 'Light Steel')
        st.session_state.facade_sandwich_panel_option = st.checkbox(
            "Dış Cephe Sandviç Panel Dahil Et (Ağır Çelik için)",
            value=st.session_state.facade_sandwich_panel_option,
            disabled=facade_sandwich_panel_disabled
        )
        
        with col2:
            st.markdown("<div class='section-title'>KONFİGÜRASYON</div>", unsafe_allow_html=True)
            st.session_state.room_config = st.selectbox(
                "Oda Konfigürasyonu:",
                ['Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
                 '1 Room + Kitchen + WC', '1 Room + Shower / WC + Kitchen',
                 '2 Rooms + Shower / WC + Kitchen', '3 Rooms + 2 Showers / WC + Kitchen'],
                index=['Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
                       '1 Room + Kitchen + WC', '1 Room + Shower / WC + Kitchen',
                       '2 Rooms + Shower / WC + Kitchen', '3 Rooms + 2 Showers / WC + Kitchen'].index(st.session_state.room_config)
            )
            
            st.session_state.kitchen_choice = st.radio(
                "Mutfak Tipi Seçimi:",
                ['No Kitchen', 'Standard Kitchen', 'Special Design Kitchen'],
                index=['No Kitchen', 'Standard Kitchen', 'Special Design Kitchen'].index(st.session_state.kitchen_choice)
            )
            
            st.session_state.floor_covering = st.selectbox(
                "Zemin Kaplama Tipi:",
                ['Laminate Parquet', 'Ceramic'],
                index=['Laminate Parquet', 'Ceramic'].index(st.session_state.floor_covering)
            )

            st.markdown("---")
            st.subheader("Yalıtım Türleri")
            # Yalıtım Tipi seçimi
            insulation_options = ['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool']
            st.session_state.insulation_material_type = st.radio(
                "Yalıtım Malzemesi Tipi:",
                options=insulation_options,
                index=insulation_options.index(st.session_state.insulation_material_type) if st.session_state.insulation_material_type in insulation_options else 0
            )

            # Yalıtım yapılmayacak seçildiyse ilgili checkbox'ları devre dışı bırak ve sıfırla
            if st.session_state.insulation_material_type == 'Yalıtım Yapılmayacak':
                if st.session_state.insulation_floor: # Sadece True ise False yap
                    st.session_state.insulation_floor = False
                if st.session_state.insulation_wall: # Sadece True ise False yap
                    st.session_state.insulation_wall = False
                st.warning("Yalıtım yapılmayacak seçildiği için zemin ve duvar yalıtım seçenekleri devre dışı bırakıldı.")

        # --- Çelik Profil Miktarları ---
        st.markdown("<div class='section-title'>ÇELİK PROFİL MİKTARLARI (Hafif Çelik için)</div>", unsafe_allow_html=True)
        st.markdown("<b>(Her 6m parça için - manuel olarak girin, aksi takdirde otomatik hesaplanır)</b>", unsafe_allow_html=True)

        steel_profile_disabled = (st.session_state.structure_type == 'Heavy Steel')

        col3, col4, col5 = st.columns(3)
        with col3:
            st.session_state.profile_100x100_count = st.number_input("100x100x3 Adet:", value=st.session_state.profile_100x100_count, min_value=0, disabled=steel_profile_disabled)
        with col4:
            st.session_state.profile_100x50_count = st.number_input("100x50x3 Adet:", value=st.session_state.profile_100x50_count, min_value=0, disabled=steel_profile_disabled)
        with col5:
            st.session_state.profile_40x60_count = st.number_input("40x60x2 Adet:", value=st.session_state.profile_40x60_count, min_value=0, disabled=steel_profile_disabled)

        col6, col7, col8 = st.columns(3)
        with col6:
            st.session_state.profile_50x50_count = st.number_input("50x50x2 Adet:", value=st.session_state.profile_50x50_count, min_value=0, disabled=steel_profile_disabled)
        with col7:
            st.session_state.profile_120x60x5mm_count = st.number_input("120x60x5mm Adet:", value=st.session_state.profile_120x60x5mm_count, min_value=0, disabled=steel_profile_disabled)
        with col8:
            st.session_state.profile_HEA160_count = st.number_input("HEA160 Adet:", value=st.session_state.profile_HEA160_count, min_value=0, disabled=steel_profile_disabled)


        # --- Pencereler ve Kapılar ---
        st.markdown("<div class='section-title'>PENCERELER VE KAPILAR</div>", unsafe_allow_html=True)
        col9, col10, col11 = st.columns(3)
        with col9:
            st.session_state.window_count = st.number_input("Pencere Adedi:", value=st.session_state.window_count, min_value=0)
        with col10:
            st.session_state.window_size = st.text_input("Pencere Boyutu:", value=st.session_state.window_size)
        with col11:
            st.session_state.window_door_color = st.selectbox("Pencere/Kapı Rengi:", ['White', 'Black', 'Grey'], index=['White', 'Black', 'Grey'].index(st.session_state.window_door_color))

        col_door1, col_door2, col_door3 = st.columns(3)
        with col_door1:
            st.session_state.sliding_door_count = st.number_input("Sürme Cam Kapı Adedi:", value=st.session_state.sliding_door_count, min_value=0)
        with col_door2:
            st.session_state.sliding_door_size = st.text_input("Sürme Kapı Boyutu:", value=st.session_state.sliding_door_size)
        with col_door3:
            pass

        col_wc_win1, col_wc_win2, col_wc_win3 = st.columns(3)
        with col_wc_win1:
            st.session_state.wc_window_count = st.number_input("WC Pencere Adedi:", value=st.session_state.wc_window_count, min_value=0)
        with col_wc_win2:
            st.session_state.wc_window_size = st.text_input("WC Pencere Boyutu:", value=st.session_state.wc_window_size)
        with col_wc_win3:
            pass

        col_wc_slid1, col_wc_slid2, col_wc_slid3 = st.columns(3)
        with col_wc_slid1:
            st.session_state.wc_sliding_door_count = st.number_input("WC Sürme Kapı Adedi:", value=st.session_state.wc_sliding_door_count, min_value=0)
        with col_wc_slid2:
            st.session_state.wc_sliding_door_size = st.text_input("WC Sürme Kapı Boyutu:", value=st.session_state.wc_sliding_door_size)
        with col_wc_slid3:
            pass
        
        col_door_main1, col_door_main2, col_door_main3 = st.columns(3)
        with col_door_main1:
            st.session_state.door_count = st.number_input("Ana Kapı Adedi:", value=st.session_state.door_count, min_value=0)
        with col_door_main2:
            st.session_state.door_size = st.text_input("Ana Kapı Boyutu:", value=st.session_state.door_size)
        with col_door_main3:
            pass

        # --- Ek Donanımlar ---
        st.markdown("<div class='section-title'>EK DONANIMLAR</div>", unsafe_allow_html=True)
        
        st.session_state.shower_wc = st.checkbox("Duş/WC Dahil Et", value=st.session_state.shower_wc)
        
        col_ceramic1, col_ceramic2 = st.columns(2)
        with col_ceramic1:
            wc_ceramic_disabled = not st.session_state.shower_wc # WC seramik sadece duş/WC seçiliyse etkin
            st.session_state.wc_ceramic = st.checkbox("WC Seramik Zemin/Duvar", value=st.session_state.wc_ceramic, disabled=wc_ceramic_disabled)
        with col_ceramic2:
            wc_ceramic_area_disabled = not st.session_state.wc_ceramic
            st.session_state.wc_ceramic_area = st.number_input("WC Seramik Alanı (m²):", value=st.session_state.wc_ceramic_area, step=0.1, min_value=0.0, disabled=wc_ceramic_area_disabled)
        
        st.session_state.electrical = st.checkbox("Elektrik Tesisatı (Malzemelerle)", value=st.session_state.electrical)
        st.session_state.plumbing = st.checkbox("Sıhhi Tesisat (Malzemelerle)", value=st.session_state.plumbing)
        
        st.markdown("---")
        st.subheader("Zemin Yalıtımı ve Malzemeleri")
        st.session_state.insulation_floor = st.checkbox("Zemin Yalıtımı Dahil Et (5€/m²)", value=st.session_state.insulation_floor)
        
        floor_insulation_material_disabled = not st.session_state.insulation_floor

        col_floor_mats = st.columns(3)
        with col_floor_mats[0]:
            st.session_state.skirting_length_val = st.number_input(f"Süpürgelik ({FIYATLAR['skirting_meter_price']}€/m) Uzunluğu (m):", value=st.session_state.skirting_length_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        with col_floor_mats[1]:
            st.session_state.laminate_flooring_m2_val = st.number_input(f"Laminat Parke 12mm ({FIYATLAR['laminate_flooring_m2_price']}€/m²) Alanı (m²):", value=st.session_state.laminate_flooring_m2_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        with col_floor_mats[2]:
            st.session_state.under_parquet_mat_m2_val = st.number_input(f"Parke Altı Şilte 4mm ({FIYATLAR['under_parquet_mat_m2_price']}€/m²) Alanı (m²):", value=st.session_state.under_parquet_mat_m2_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        
        col_floor_mats2 = st.columns(3)
        with col_floor_mats2[0]:
            st.session_state.osb2_18mm_count_val = st.number_input(f"OSB2 18mm/Beton Panel ({FIYATLAR['osb2_18mm_piece_price']}€/adet) Adet:", value=st.session_state.osb2_18mm_count_val, min_value=0, disabled=floor_insulation_material_disabled)
        with col_floor_mats2[1]:
            st.session_state.galvanized_sheet_m2_val = st.number_input(f"5mm Galvanizli Sac ({FIYATLAR['galvanized_sheet_m2_price']}€/m²) Alanı (m²):", value=st.session_state.galvanized_sheet_m2_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        with col_floor_mats2[2]:
            st.session_state.insulation_material_type = st.selectbox(
                "Duvar Yalıtım Malzemesi Tipi:",
                ['Stone Wool', 'Glass Wool'],
                index=['Stone Wool', 'Glass Wool'].index(st.session_state.insulation_material_type)
            )

        st.session_state.insulation_wall = st.checkbox("Duvar Yalıtımı Dahil Et (10€/m²)", value=st.session_state.insulation_wall)
        
        st.markdown("---")

        st.session_state.transportation = st.checkbox("Nakliye Dahil Et (350€)", value=st.session_state.transportation)
        st.session_state.heating = st.checkbox("Yerden Isıtma Dahil Et (50€/m²)", value=st.session_state.heating)
        st.session_state.solar = st.checkbox("Güneş Enerjisi Sistemi", value=st.session_state.solar)
        
        col14, col15 = st.columns(2)
        with col14:
            st.session_state.solar_kw = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not st.session_state.solar, index=[5, 7.2, 11].index(st.session_state.solar_kw))
        with col15:
            # Solar fiyatı hesaplama butonuna basıldığında yapılacağı için burada disabled=True kalmalı
            solar_price_display = st.session_state.solar_kw * FIYATLAR['solar_per_kw'] if st.session_state.solar else 0.0
            st.number_input("Güneş Enerjisi Fiyatı (€):", value=solar_price_display, disabled=True)

        st.session_state.wheeled_trailer = st.checkbox("Tekerlekli Römork", value=st.session_state.wheeled_trailer)
        st.session_state.wheeled_trailer_price = st.number_input("Römork Fiyatı (€):", value=st.session_state.wheeled_trailer_price, step=0.1, disabled=not st.session_state.wheeled_trailer)

        # --- Aether Living Opsiyonları (Pakete göre göster) ---
        if st.session_state.aether_package_choice != 'None':
            st.markdown("<div class='section-title'>AETHER LIVING EK OPSİYONLARI</div>", unsafe_allow_html=True)
            
            col_aether_1, col_aether_2 = st.columns(2)
            with col_aether_1:
                # Premium ve Elite Paketler
                if st.session_state.aether_package_choice in ['Aether Living | Loft Premium (ESSENTIAL)', 'Aether Living | Loft Elite (LUXURY)']:
                    st.session_state.bedroom_set_option = st.checkbox("Yatak Odası Takımı", value=st.session_state.bedroom_set_option)
                    
                    st.session_state.brushed_granite_countertops_option = st.checkbox("Fırçalanmış Granit Tezgahlar", value=st.session_state.brushed_granite_countertops_option)
                    if st.session_state.brushed_granite_countertops_option:
                        st.session_state.brushed_granite_countertops_m2_val = st.number_input("Granit Tezgah Alanı (m²):", value=st.session_state.brushed_granite_countertops_m2_val, min_value=0.0, step=0.1)
                    
                    st.session_state.terrace_laminated_wood_flooring_option = st.checkbox("Teras Laminat Ahşap Zemin Kaplaması", value=st.session_state.terrace_laminated_wood_flooring_option)
                    if st.session_state.terrace_laminated_wood_flooring_option:
                        st.session_state.terrace_laminated_wood_flooring_m2_val = st.number_input("Teras Zemin Alanı (m²):", value=st.session_state.terrace_laminated_wood_flooring_m2_val, min_value=0.0, step=0.1)
                
                    st.session_state.exterior_wood_cladding_m2_option = st.checkbox("Dış Cephe Ahşap Kaplama (Lambiri)", value=st.session_state.exterior_wood_cladding_m2_option)
                    if st.session_state.exterior_wood_cladding_m2_option:
                        st.session_state.exterior_wood_cladding_m2_val = st.number_input("Dış Ahşap Kaplama Alanı (m²):", value=st.session_state.exterior_wood_cladding_m2_val, min_value=0.0, step=0.1)
                
                    st.session_state.porcelain_tiles_option = st.checkbox("Porselen Fayans (Ekstra Zemin)", value=st.session_state.porcelain_tiles_option)
                    if st.session_state.porcelain_tiles_option:
                        st.session_state.porcelain_tiles_m2_val = st.number_input("Porselen Fayans Alanı (m²):", value=st.session_state.porcelain_tiles_m2_val, min_value=0.0, step=0.1)

            with col_aether_2:
                if st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                    st.session_state.exterior_cladding_m2_option = st.checkbox("Dış Cephe Kaplama (Knauf Aquapanel)", value=st.session_state.exterior_cladding_m2_option)
                    if st.session_state.exterior_cladding_m2_option:
                        st.session_state.exterior_cladding_m2_val = st.number_input("Dış Cephe Kaplama Alanı (m²):", value=st.session_state.exterior_cladding_m2_val, min_value=0.0, step=0.1)

                    st.session_state.concrete_panel_floor_option = st.checkbox("Beton Panel Zemin", value=st.session_state.concrete_panel_floor_option)
                    if st.session_state.concrete_panel_floor_option:
                        st.session_state.concrete_panel_floor_m2_val = st.number_input("Beton Zemin Alanı (m²):", value=st.session_state.concrete_panel_floor_m2_val, min_value=0.0, step=0.1)

                    st.session_state.premium_faucets_option = st.checkbox("Premium Bataryalar", value=st.session_state.premium_faucets_option)
                    st.session_state.integrated_fridge_option = st.checkbox("Entegre Buzdolabı", value=st.session_state.integrated_fridge_option)
                    st.session_state.designer_furniture_option = st.checkbox("Özel Tasarım Mobilyalar", value=st.session_state.designer_furniture_option)
                    st.session_state.italian_sofa_option = st.checkbox("İtalyan Kanepe", value=st.session_state.italian_sofa_option)
                    st.session_state.inclass_chairs_option = st.checkbox("Inclass Sandalyeler", value=st.session_state.inclass_chairs_option)
                    if st.session_state.inclass_chairs_option:
                        st.session_state.inclass_chairs_count = st.number_input("Sandalye Adedi:", value=st.session_state.inclass_chairs_count, min_value=0)
                    
                    st.session_state.smart_home_systems_option = st.checkbox("Akıllı Ev Sistemleri", value=st.session_state.smart_home_systems_option)
                    st.session_state.security_camera_option = st.checkbox("Güvenlik Kamerası Sistemi", value=st.session_state.security_camera_option)
                    st.session_state.white_goods_fridge_tv_option = st.checkbox("Beyaz Eşya (Buzdolabı/TV)", value=st.session_state.white_goods_fridge_tv_option)
                    st.session_state.sofa_option = st.checkbox("Kanepe", value=st.session_state.sofa_option)


        # --- Finansal Ayarlar ---
        st.markdown("<div class='section-title'>FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
        profit_rate_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
        st.session_state.profit_rate = st.selectbox("Kar Oranı:", options=profit_rate_options, format_func=lambda x: x[0], index=profit_rate_options.index(st.session_state.profit_rate), key="profit_rate_select")
        st.markdown(f"<div>KDV Oranı: {VAT_RATE*100:.0f}% (Sabit)</div>", unsafe_allow_html=True)

        # --- Müşteri Notları ---
        st.markdown("<div class='section-title'>MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR</div>", unsafe_allow_html=True)
        st.session_state.customer_notes = st.text_area("Müşteri Notları:", value=st.session_state.customer_notes, key="customer_notes_textarea")

        # --- PDF Dil Seçimi ---
        st.session_state.pdf_language = st.selectbox(
            "Teklif PDF Dili:",
            options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')],
            format_func=lambda x: x[0],
            index=[('English-Greek', 'en_gr'), ('Turkish', 'tr')].index(st.session_state.pdf_language)
        )

        submit_button = st.form_submit_button("Hesapla ve Teklifleri Oluştur")

if submit_button:
        try:
            # --- Hesaplama Mantığı ---
            # All your calculation code (width, length, areas, costs, etc.)
            # should be indented here.
            # Example:
            width, length, height = st.session_state.width_val, st.session_state.length_val, st.session_state.height_val
            areas = calculate_area(width, length, height)
            floor_area = areas["floor"]
            # ... and so on for all your calculation logic
        except Exception as e:
            print(f"Hata oluştu: {e}")
            st.error(f"Bir hata oluştu: {e}") # Streamlit'te hata göstermek için
            st.exception(e) # Detaylı traceback göstermek için
            width, length, height = st.session_state.width_val, st.session_state.length_val, st.session_state.height_val
            areas = calculate_area(width, length, height)
            floor_area = areas["floor"]
            wall_area = areas["wall"]
            roof_area = areas["roof"]

            costs = [] # Tüm maliyet kalemleri buraya eklenecek
            profile_analysis_details = [] # Çelik profil analiz detaylarını tutacak

            # Yapı (metal iskelet ve boya her zaman eklenir, maliyeti 0 olsa bile bilgi için)
            costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            if st.session_state.structure_type == 'Light Steel':
                # Hafif çelik profillerin manuel veya otomatik adetleri
                has_manual_steel_profiles = sum([st.session_state.profile_100x100_count, st.session_state.profile_100x50_count,
                                                        st.session_state.profile_40x60_count, st.session_state.profile_50x50_count,
                                                        st.session_state.profile_120x60x5mm_count, st.session_state.profile_HEA160_count]) > 0

                if has_manual_steel_profiles:
                    if st.session_state.profile_100x100_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (100x100x3)", 'Quantity': f"{st.session_state.profile_100x100_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                        profile_analysis_details.append({'Item': '100x100x3', 'Quantity': st.session_state.profile_100x100_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                    if st.session_state.profile_100x50_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (100x50x3)", 'Quantity': f"{st.session_state.profile_100x50_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_100x50x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x50_count * FIYATLAR['steel_profile_100x50x3'])})
                        profile_analysis_details.append({'Item': '100x50x3', 'Quantity': st.session_state.profile_100x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x50x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x50_count * FIYATLAR['steel_profile_100x50x3'])})
                    if st.session_state.profile_40x60_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (40x60x2)", 'Quantity': f"{st.session_state.profile_40x60_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_40x60x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_40x60_count * FIYATLAR['steel_profile_40x60x2'])})
                        profile_analysis_details.append({'Item': '40x60x2', 'Quantity': st.session_state.profile_40x60_count, 'Unit Price (€)': FIYATLAR['steel_profile_40x60x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_40x60_count * FIYATLAR['steel_profile_40x60x2'])})
                    if st.session_state.profile_50x50_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (50x50x2)", 'Quantity': f"{st.session_state.profile_50x50_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                        profile_analysis_details.append({'Item': '50x50x2', 'Quantity': st.session_state.profile_50x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                    if st.session_state.profile_120x60x5mm_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (120x60x5mm)", 'Quantity': f"{st.session_state.profile_120x60x5mm_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_120x60x5mm'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_120x60x5mm_count * FIYATLAR['steel_profile_120x60x5mm'])})
                        profile_analysis_details.append({'Item': '120x60x5mm', 'Quantity': st.session_state.profile_120x60x5mm_count, 'Unit Price (€)': FIYATLAR['steel_profile_120x60x5mm'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_120x60x5mm_count * FIYATLAR['steel_profile_120x60x5mm'])})
                    if st.session_state.profile_HEA160_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (HEA160)", 'Quantity': f"{st.session_state.profile_HEA160_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_HEA160'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_HEA160_count * FIYATLAR['steel_profile_HEA160'])})
                        profile_analysis_details.append({'Item': 'HEA160', 'Quantity': st.session_state.profile_HEA160_count, 'Unit Price (€)': FIYATLAR['steel_profile_HEA160'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_HEA160_count * FIYATLAR['steel_profile_HEA160'])})
                    else:
                        # Otomatik hesaplama (eğer manuel giriş yapılmadıysa)
                        auto_100x100_count = math.ceil(floor_area * (12 / 27.0))
                        auto_50x50_count = math.ceil(floor_area * (6 / 27.0))
                        if auto_100x100_count > 0:
                            costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (100x100x3) (Auto)', 'Quantity': f"{auto_100x100_count} adet ({auto_100x100_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(auto_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                            profile_analysis_details.append({'Item': '100x100x3 (Auto)', 'Quantity': auto_100x100_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(auto_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                        if auto_50x50_count > 0:
                            costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (50x50x2) (Auto)', 'Quantity': f"{auto_50x50_count} adet ({auto_50x50_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(auto_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                            profile_analysis_details.append({'Item': '50x50x2 (Auto)', 'Quantity': auto_50x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(auto_50x50_count * FIYATLAR['steel_profile_50x50x2'])})

                else: # Heavy Steel
                    heavy_steel_cost = floor_area * FIYATLAR['heavy_steel_m2']
                    costs.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
                    profile_analysis_details.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
                    costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

                # Kaynak işçiliği
            if st.session_state.welding_type == 'Standard Welding (160€/m²)':
                welding_labor_price = FIYATLAR['welding_labor_m2_standard']
            else: # TR Assembly Welding
                welding_labor_price = FIYATLAR['welding_labor_m2_trmontaj']
            
            welding_cost = floor_area * welding_labor_price
            costs.append({'Item': f"Steel Welding Labor ({st.session_state.welding_type.split(' ')[0]})", 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': welding_labor_price, 'Total (€)': calculate_rounded_up_cost(welding_cost)})
#=============================================================
# BÖLÜM 7: run_streamlit_app() - Kullanıcı Arayüzü Girişleri (Müşteri, Boyutlar, Yapı, Çelik Profiller, Kapılar/Pencereler)
# ==============================================================================

    # --- Sidebar - Müşteri Bilgileri ve Paket Seçimi --- with st.sidebar:
        st.header("Müşteri Bilgileri (İsteğe Bağlı)")
        st.session_state.customer_name = st.text_input("Ad Soyad:", value=st.session_state.customer_name, key="customer_name_input")
        st.session_state.customer_company = st.text_input("Şirket:", value=st.session_state.customer_company, key="customer_company_input")
        st.session_state.customer_address = st.text_input("Adres:", value=st.session_state.customer_address, key="customer_address_input")
        st.session_state.customer_city = st.text_input("Şehir:", value=st.session_state.customer_city, key="customer_city_input")
        st.session_state.customer_phone = st.text_input("Telefon:", value=st.session_state.customer_phone, key="customer_phone_input")
        st.session_state.customer_email = st.text_input("E-posta:", value=st.session_state.customer_email, key="customer_email_input")
        st.session_state.customer_id_no = st.text_input("Kimlik/Pasaport No:", value=st.session_state.customer_id_no, key="customer_id_input")
        st.markdown("<div class='warning'>Not: Müşteri bilgileri zorunlu değildir. Boş bırakılırsa 'GENEL' olarak işaretlenecektir.</div>", unsafe_allow_html=True)

        st.header("Paket Seçimi")
        prev_aether_package_choice = st.session_state.aether_package_choice
        st.session_state.aether_package_choice = st.selectbox(
            "Aether Living | Loft Serisi Paket Seçimi:",
            ['None', 'Aether Living | Loft Standard (BASICS)',
             'Aether Living | Loft Premium (ESSENTIAL)',
             'Aether Living | Loft Elite (LUXURY)'],
            index=['None', 'Aether Living | Loft Standard (BASICS)',
                   'Aether Living | Loft Premium (ESSENTIAL)',
                   'Aether Living | Loft Elite (LUXURY)'].index(st.session_state.aether_package_choice)
        )
        
        # Paket değiştiğinde varsayılanları uygula
        if st.session_state.aether_package_choice != prev_aether_package_choice:
            if st.session_state.aether_package_choice == 'None':
                # Tüm paket varsayılanlarını sıfırla, manuel girdileri koru
                for key, default_value in session_state_defaults.items():
                    if key not in ['customer_name', 'customer_company', 'customer_address', 'customer_city', 'customer_phone', 'customer_email', 'customer_id_no', 'aether_package_choice', 'width_val', 'length_val', 'height_val', 'structure_type', 'welding_type', 'room_config', 'profit_rate', 'customer_notes', 'pdf_language']:
                        st.session_state[key] = session_state_defaults[key] # İlk baştaki varsayılanlara geri dön
            elif st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
                st.session_state.kitchen_choice = 'Standard Kitchen'
                st.session_state.shower_wc = True
                st.session_state.electrical = True
                st.session_state.plumbing = True
                st.session_state.insulation_floor = True
                st.session_state.insulation_wall = True
                st.session_state.floor_covering = 'Laminate Parquet'
                st.session_state.heating = False
                st.session_state.solar = False

                # Diğer Aether Living opsiyonlarını sıfırla (eğer önceden Premium/Elite seçiliyse)
                st.session_state.bedroom_set_option = False
                st.session_state.brushed_granite_countertops_option = False
                st.session_state.terrace_laminated_wood_flooring_option = False
                st.session_state.exterior_cladding_m2_option = False
                st.session_state.concrete_panel_floor_option = False
                st.session_state.premium_faucets_option = False
                st.session_state.integrated_fridge_option = False
                st.session_state.designer_furniture_option = False
                st.session_state.italian_sofa_option = False
                st.session_state.inclass_chairs_option = False
                st.session_state.inclass_chairs_count = 0
                st.session_state.smart_home_systems_option = False
                st.session_state.security_camera_option = False
                st.session_state.white_goods_fridge_tv_option = False
                st.session_state.exterior_wood_cladding_m2_option = False
                st.session_state.porcelain_tiles_option = False
                st.session_state.plasterboard_interior_option = True 
                st.session_state.plasterboard_all_option = False
                st.session_state.osb_inner_wall_option = True
                st.session_state.facade_sandwich_panel_option = False # Standard pakette dış cephe sandviç panel default false

            elif st.session_state.aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
                # Standard paket özelliklerini uygula
                st.session_state.kitchen_choice = 'Standard Kitchen'
                st.session_state.shower_wc = True
                st.session_state.electrical = True
                st.session_state.plumbing = True
                st.session_state.insulation_floor = True
                st.session_state.insulation_wall = True
                st.session_state.floor_covering = 'Laminate Parquet'
                st.session_state.heating = False
                st.session_state.solar = False
                
                # Premium pakete özel eklemeler
                st.session_state.bedroom_set_option = True
                st.session_state.brushed_granite_countertops_option = True
                st.session_state.terrace_laminated_wood_flooring_option = True 
                
                # Diğer Aether Living opsiyonlarını sıfırla (eğer önceden Elite seçiliyse)
                st.session_state.exterior_cladding_m2_option = False
                st.session_state.concrete_panel_floor_option = False
                st.session_state.premium_faucets_option = False
                st.session_state.integrated_fridge_option = False
                st.session_state.designer_furniture_option = False
                st.session_state.italian_sofa_option = False
                st.session_state.inclass_chairs_option = False
                st.session_state.inclass_chairs_count = 0
                st.session_state.smart_home_systems_option = False
                st.session_state.security_camera_option = False
                st.session_state.white_goods_fridge_tv_option = False
                st.session_state.exterior_wood_cladding_m2_option = False
                st.session_state.porcelain_tiles_option = False
                st.session_state.plasterboard_interior_option = True
                st.session_state.plasterboard_all_option = False
                st.session_state.osb_inner_wall_option = True
                st.session_state.facade_sandwich_panel_option = False

            elif st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                # Premium paket özelliklerini uygula
                st.session_state.kitchen_choice = 'Special Design Kitchen'
                st.session_state.shower_wc = True
                st.session_state.electrical = True
                st.session_state.plumbing = True
                st.session_state.insulation_floor = True
                st.session_state.insulation_wall = True
                st.session_state.floor_covering = 'Ceramic'
                st.session_state.heating = True
                st.session_state.solar = True
                st.session_state.bedroom_set_option = True
                st.session_state.brushed_granite_countertops_option = True
                st.session_state.terrace_laminated_wood_flooring_option = True # Elite'te de teras zemin var
                
                # Elite pakete özel eklemeler
                st.session_state.exterior_cladding_m2_option = True 
                st.session_state.concrete_panel_floor_option = True
                st.session_state.premium_faucets_option = True
                st.session_state.integrated_fridge_option = True
                st.session_state.designer_furniture_option = True
                st.session_state.italian_sofa_option = True
                st.session_state.inclass_chairs_option = True
                st.session_state.inclass_chairs_count = 1 
                st.session_state.smart_home_systems_option = True
                st.session_state.security_camera_option = True
                st.session_state.white_goods_fridge_tv_option = True
                st.session_state.exterior_wood_cladding_m2_option = False # Ahşap kaplama manuel kalır
                st.session_state.porcelain_tiles_option = True 
                st.session_state.plasterboard_all_option = True 
                st.session_state.osb_inner_wall_option = True
                st.session_state.facade_sandwich_panel_option = True

            # NOT: Paket seçimi değiştiğinde UI'daki değerleri manuel olarak set etmiyoruz.
            # Bunun yerine, aşağıdaki UI elementleri st.session_state'ten kendi değerlerini okuyacaklar.
            # Paket seçimi, st.session_state'teki değerleri değiştirir, bu da UI'a bir sonraki rerun'da yansır.
            st.rerun() # Paket seçimi sonrası UI'ı yeniden çizmek için
    
    # --- Ana Form ---
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='section-title'>BOYUTLAR</div>", unsafe_allow_html=True)
            st.session_state.width_val = st.number_input("Genişlik (m):", value=st.session_state.width_val, step=0.1, key="width_input")
            st.session_state.length_val = st.number_input("Uzunluk (m):", value=st.session_state.length_val, step=0.1, key="length_input")
            st.session_state.height_val = st.number_input("Yükseklik (m):", value=st.session_state.height_val, step=0.1, key="height_input")

            st.markdown("<div class='section-title'>YAPI</div>", unsafe_allow_html=True)
            _temp_structure_type = st.session_state.structure_type
            st.session_state.structure_type = st.radio("Yapı Tipi:", ['Light Steel', 'Heavy Steel'], index=['Light Steel', 'Heavy Steel'].index(_temp_structure_type), key="structure_type_radio")
            
            _temp_welding_type = st.session_state.welding_type
            st.session_state.welding_type = st.selectbox("Çelik Kaynak İşçiliği:", ['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'], index=['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'].index(_temp_welding_type), key="welding_labor_select")

            # Alçıpan ve OSB kontrolleri
            plasterboard_interior_disabled = (st.session_state.structure_type == 'Heavy Steel')
            plasterboard_all_disabled = (st.session_state.structure_type == 'Light Steel')

            _temp_plasterboard_interior_option = st.session_state.plasterboard_interior_option
            st.session_state.plasterboard_interior_option = st.checkbox("İç Alçıpan Dahil Et", value=_temp_plasterboard_interior_option, disabled=plasterboard_interior_disabled, key="pb_int_checkbox")
            
            _temp_plasterboard_all_option = st.session_state.plasterboard_all_option
            st.session_state.plasterboard_all_option = st.checkbox("İç ve Dış Alçıpan Dahil Et", value=_temp_plasterboard_all_option, disabled=plasterboard_all_disabled, key="pb_all_checkbox")

            osb_inner_wall_disabled = not (st.session_state.plasterboard_interior_option or st.session_state.plasterboard_all_option)
            _temp_osb_inner_wall_option = st.session_state.osb_inner_wall_option
            st.session_state.osb_inner_wall_option = st.checkbox("İç Duvar OSB Malzemesi Dahil Et", value=_temp_osb_inner_wall_option, disabled=osb_inner_wall_disabled, key="osb_inner_checkbox")

            facade_sandwich_panel_disabled = (st.session_state.structure_type == 'Light Steel')
            _temp_facade_sandwich_panel_option = st.session_state.facade_sandwich_panel_option
            st.session_state.facade_sandwich_panel_option = st.checkbox("Dış Cephe Sandviç Panel Dahil Et (Ağır Çelik için)", value=_temp_facade_sandwich_panel_option, disabled=facade_sandwich_panel_disabled, key="facade_panel_checkbox")
            
        with col2:
            st.markdown("<div class='section-title'>KONFİGÜRASYON</div>", unsafe_allow_html=True)
            _temp_room_config = st.session_state.room_config
            st.session_state.room_config = st.selectbox(
                "Oda Konfigürasyonu:",
                ['Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
                 '1 Room + Kitchen + WC', '1 Room + Shower / WC + Kitchen',
                 '2 Rooms + Shower / WC + Kitchen', '3 Rooms + 2 Showers / WC + Kitchen'],
                index=['Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
                       '1 Room + Kitchen + WC', '1 Room + Shower / WC + Kitchen',
                       '2 Rooms + Shower / WC + Kitchen', '3 Rooms + 2 Showers / WC + Kitchen'].index(_temp_room_config),
                key="room_config_select"
            )
            
            _temp_kitchen_choice = st.session_state.kitchen_choice
            st.session_state.kitchen_choice = st.radio("Mutfak Tipi Seçimi:", ['No Kitchen', 'Standard Kitchen', 'Special Design Kitchen'], index=['No Kitchen', 'Standard Kitchen', 'Special Design Kitchen'].index(_temp_kitchen_choice), key="kitchen_type_radio_select")
            
            _temp_floor_covering = st.session_state.floor_covering
            st.session_state.floor_covering = st.selectbox(
                "Zemin Kaplama Tipi:",
                ['Laminate Parquet', 'Ceramic'],
                index=['Laminate Parquet', 'Ceramic'].index(_temp_floor_covering)
            )

            st.markdown("---")
            st.subheader("Yalıtım Türleri")
            _temp_insulation_material_type = st.session_state.insulation_material_type
            st.session_state.insulation_material_type = st.radio(
                "Yalıtım Malzemesi Tipi:",
                options=['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool'],
                index=['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool'].index(_temp_insulation_material_type) if _temp_insulation_material_type in ['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool'] else 0
            )

            # Yalıtım yapılmayacak seçildiyse ilgili checkbox'ları devre dışı bırak ve sıfırla
            if st.session_state.insulation_material_type == 'Yalıtım Yapılmayacak':
                if st.session_state.insulation_floor: 
                    st.session_state.insulation_floor = False
                if st.session_state.insulation_wall: 
                    st.session_state.insulation_wall = False
                st.warning("Yalıtım yapılmayacak seçildiği için zemin ve duvar yalıtım seçenekleri devre dışı bırakıldı.")

        st.markdown("<div class='section-title'>ÇELİK PROFİL MİKTARLARI (Hafif Çelik için)</div>", unsafe_allow_html=True)
        st.markdown("<b>(Her 6m parça için - manuel olarak girin, aksi takdirde otomatik hesaplanır)</b>", unsafe_allow_html=True)

        steel_profile_disabled = (st.session_state.structure_type == 'Heavy Steel')

        col3, col4, col5 = st.columns(3)
        with col3:
            _temp_profile_100x100_count = st.session_state.profile_100x100_count
            st.session_state.profile_100x100_count = st.number_input("100x100x3 Adet:", value=_temp_profile_100x100_count, min_value=0, disabled=steel_profile_disabled)
        with col4:
            _temp_profile_100x50_count = st.session_state.profile_100x50_count
            st.session_state.profile_100x50_count = st.number_input("100x50x3 Adet:", value=_temp_profile_100x50_count, min_value=0, disabled=steel_profile_disabled)
        with col5:
            _temp_profile_40x60_count = st.session_state.profile_40x60_count
            st.session_state.profile_40x60_count = st.number_input("40x60x2 Adet:", value=_temp_profile_40x60_count, min_value=0, disabled=steel_profile_disabled)

        col6, col7, col8 = st.columns(3)
        with col6:
            _temp_profile_50x50_count = st.session_state.profile_50x50_count
            st.session_state.profile_50x50_count = st.number_input("50x50x2 Adet:", value=_temp_profile_50x50_count, min_value=0, disabled=steel_profile_disabled)
        with col7:
            _temp_profile_120x60x5mm_count = st.session_state.profile_120x60x5mm_count
            st.session_state.profile_120x60x5mm_count = st.number_input("120x60x5mm Adet:", value=_temp_profile_120x60x5mm_count, min_value=0, disabled=steel_profile_disabled)
        with col8:
            _temp_profile_HEA160_count = st.session_state.profile_HEA160_count
            st.session_state.profile_HEA160_count = st.number_input("HEA160 Adet:", value=_temp_profile_HEA160_count, min_value=0, disabled=steel_profile_disabled)


        st.markdown("<div class='section-title'>PENCERELER VE KAPILAR</div>", unsafe_allow_html=True)
        col9, col10, col11 = st.columns(3)
        with col9:
            _temp_window_count = st.session_state.window_count
            st.session_state.window_count = st.number_input("Pencere Adedi:", value=_temp_window_count, min_value=0)
        with col10:
            _temp_window_size = st.session_state.window_size
            st.session_state.window_size = st.text_input("Pencere Boyutu:", value=_temp_window_size)
        with col11:
            _temp_window_door_color = st.session_state.window_door_color
            st.session_state.window_door_color = st.selectbox("Pencere/Kapı Rengi:", ['White', 'Black', 'Grey'], index=['White', 'Black', 'Grey'].index(_temp_window_door_color))

        col_door1, col_door2, col_door3 = st.columns(3)
        with col_door1:
            _temp_sliding_door_count = st.session_state.sliding_door_count
            st.session_state.sliding_door_count = st.number_input("Sürme Cam Kapı Adedi:", value=_temp_sliding_door_count, min_value=0)
        with col_door2:
            _temp_sliding_door_size = st.session_state.sliding_door_size
            st.session_state.sliding_door_size = st.text_input("Sürme Kapı Boyutu:", value=_temp_sliding_door_size)
        with col_door3:
            pass

        col_wc_win1, col_wc_win2, col_wc_win3 = st.columns(3)
        with col_wc_win1:
            _temp_wc_window_count = st.session_state.wc_window_count
            st.session_state.wc_window_count = st.number_input("WC Pencere Adedi:", value=_temp_wc_window_count, min_value=0)
        with col_wc_win2:
            _temp_wc_window_size = st.session_state.wc_window_size
            st.session_state.wc_window_size = st.text_input("WC Pencere Boyutu:", value=_temp_wc_window_size)
        with col_wc_win3:
            pass

        col_wc_slid1, col_wc_slid2, col_wc_slid3 = st.columns(3)
        with col_wc_slid1:
            _temp_wc_sliding_door_count = st.session_state.wc_sliding_door_count
            st.session_state.wc_sliding_door_count = st.number_input("WC Sürme Kapı Adedi:", value=_temp_wc_sliding_door_count, min_value=0)
        with col_wc_slid2:
            _temp_wc_sliding_door_size = st.session_state.wc_sliding_door_size
            st.session_state.wc_sliding_door_size = st.text_input("WC Sürme Kapı Boyutu:", value=_temp_wc_sliding_door_size)
        with col_wc_slid3:
            pass
        
        col_door_main1, col_door_main2, col_door_main3 = st.columns(3)
        with col_door_main1:
            _temp_door_count = st.session_state.door_count
            st.session_state.door_count = st.number_input("Ana Kapı Adedi:", value=_temp_door_count, min_value=0)
        with col_door_main2:
            _temp_door_size = st.session_state.door_size
            st.session_state.door_size = st.text_input("Ana Kapı Boyutu:", value=_temp_door_size)
        with col_door_main3:
            pass

        st.markdown("<div class='section-title'>EK DONANIMLAR</div>", unsafe_allow_html=True)
        
        _temp_shower_wc = st.session_state.shower_wc
        st.session_state.shower_wc = st.checkbox("Duş/WC Dahil Et", value=_temp_shower_wc)
        
        col_ceramic1, col_ceramic2 = st.columns(2)
        with col_ceramic1:
            wc_ceramic_disabled = not st.session_state.shower_wc # WC seramik sadece duş/WC seçiliyse etkin
            _temp_wc_ceramic = st.session_state.wc_ceramic
            st.session_state.wc_ceramic = st.checkbox("WC Seramik Zemin/Duvar", value=_temp_wc_ceramic, disabled=wc_ceramic_disabled)
        with col_ceramic2:
            wc_ceramic_area_disabled = not st.session_state.wc_ceramic
            _temp_wc_ceramic_area = st.session_state.wc_ceramic_area
            st.session_state.wc_ceramic_area = st.number_input("WC Seramik Alanı (m²):", value=_temp_wc_ceramic_area, step=0.1, min_value=0.0, disabled=wc_ceramic_area_disabled)
        
        _temp_electrical = st.session_state.electrical
        st.session_state.electrical = st.checkbox("Elektrik Tesisatı (Malzemelerle)", value=_temp_electrical)
        _temp_plumbing = st.session_state.plumbing
        st.session_state.plumbing = st.checkbox("Sıhhi Tesisat (Malzemelerle)", value=_temp_plumbing)
        
        st.markdown("---")
        st.subheader("Zemin Yalıtımı ve Malzemeleri")
        _temp_insulation_floor = st.session_state.insulation_floor
        st.session_state.insulation_floor = st.checkbox("Zemin Yalıtımı Dahil Et (5€/m²)", value=_temp_insulation_floor)
        
        floor_insulation_material_disabled = not st.session_state.insulation_floor

        col_floor_mats = st.columns(3)
        with col_floor_mats[0]:
            _temp_skirting_length = st.session_state.skirting_length_val
            st.session_state.skirting_length_val = st.number_input(f"Süpürgelik ({FIYATLAR['skirting_meter_price']}€/m) Uzunluğu (m):", value=_temp_skirting_length, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        with col_floor_mats[1]:
            _temp_laminate_flooring_m2 = st.session_state.laminate_flooring_m2_val
            st.session_state.laminate_flooring_m2_val = st.number_input(f"Laminat Parke 12mm ({FIYATLAR['laminate_flooring_m2_price']}€/m²) Alanı (m²):", value=_temp_laminate_flooring_m2, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        with col_floor_mats[2]:
            _temp_under_parquet_mat_m2 = st.session_state.under_parquet_mat_m2_val
            st.session_state.under_parquet_mat_m2_val = st.number_input(f"Parke Altı Şilte 4mm ({FIYATLAR['under_parquet_mat_m2_price']}€/m²) Alanı (m²):", value=_temp_under_parquet_mat_m2, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        
        col_floor_mats2 = st.columns(3)
        with col_floor_mats2[0]:
            _temp_osb2_18mm_count = st.session_state.osb2_18mm_count_val
            st.session_state.osb2_18mm_count_val = st.number_input(f"OSB2 18mm/Beton Panel ({FIYATLAR['osb2_18mm_piece_price']}€/adet) Adet:", value=_temp_osb2_18mm_count, min_value=0, disabled=floor_insulation_material_disabled)
        with col_floor_mats2[1]:
            _temp_galvanized_sheet_m2 = st.session_state.galvanized_sheet_m2_val
            st.session_state.galvanized_sheet_m2_val = st.number_input(f"5mm Galvanizli Sac ({FIYATLAR['galvanized_sheet_m2_price']}€/m²) Alanı (m²):", value=_temp_galvanized_sheet_m2, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled)
        with col_floor_mats2[2]:
            _temp_insulation_material_type = st.session_state.insulation_material_type
            st.session_state.insulation_material_type = st.selectbox(
                "Yalıtım Malzemesi Tipi:",
                options=['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool'],
                index=['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool'].index(_temp_insulation_material_type) if _temp_insulation_material_type in ['Yalıtım Yapılmayacak', 'Stone Wool', 'Glass Wool'] else 0
            )

        _temp_insulation_wall = st.session_state.insulation_wall
        st.session_state.insulation_wall = st.checkbox("Duvar Yalıtımı Dahil Et (10€/m²)", value=_temp_insulation_wall)
        
        st.markdown("---")

        _temp_transportation = st.session_state.transportation
        st.session_state.transportation = st.checkbox("Nakliye Dahil Et (350€)", value=_temp_transportation)
        _temp_heating = st.session_state.heating
        st.session_state.heating = st.checkbox("Yerden Isıtma Dahil Et (50€/m²)", value=_temp_heating)
        _temp_solar = st.session_state.solar
        st.session_state.solar = st.checkbox("Güneş Enerjisi Sistemi", value=_temp_solar)
        
        col14, col15 = st.columns(2)
        with col14:
            _temp_solar_kw = st.session_state.solar_kw
            st.session_state.solar_kw = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not st.session_state.solar, index=[5, 7.2, 11].index(_temp_solar_kw))
        with col15:
            solar_price_display = st.session_state.solar_kw * FIYATLAR['solar_per_kw'] if st.session_state.solar else 0.0
            st.number_input("Güneş Enerjisi Fiyatı (€):", value=solar_price_display, disabled=True)

        _temp_wheeled_trailer = st.session_state.wheeled_trailer
        st.session_state.wheeled_trailer = st.checkbox("Tekerlekli Römork", value=_temp_wheeled_trailer)
        _temp_wheeled_trailer_price = st.session_state.wheeled_trailer_price
        st.session_state.wheeled_trailer_price = st.number_input("Römork Fiyatı (€):", value=_temp_wheeled_trailer_price, step=0.1, disabled=not st.session_state.wheeled_trailer)


        # --- Aether Living Opsiyonları (Pakete göre görünür/gizlenir) ---
        if st.session_state.aether_package_choice != 'None':
            st.markdown("<div class='section-title'>AETHER LIVING EK OPSİYONLARI</div>", unsafe_allow_html=True)
            
            col_aether_1, col_aether_2 = st.columns(2)
            with col_aether_1:
                # Premium ve Elite Paketler
                if st.session_state.aether_package_choice in ['Aether Living | Loft Premium (ESSENTIAL)', 'Aether Living | Loft Elite (LUXURY)']:
                    _temp_bedroom_set_option = st.session_state.bedroom_set_option
                    st.session_state.bedroom_set_option = st.checkbox("Yatak Odası Takımı", value=_temp_bedroom_set_option)
                    
                    _temp_brushed_granite_countertops_option = st.session_state.brushed_granite_countertops_option
                    st.session_state.brushed_granite_countertops_option = st.checkbox("Fırçalanmış Granit Tezgahlar", value=_temp_brushed_granite_countertops_option)
                    if st.session_state.brushed_granite_countertops_option:
                        _temp_brushed_granite_countertops_m2 = st.session_state.brushed_granite_countertops_m2_val
                        st.session_state.brushed_granite_countertops_m2_val = st.number_input("Granit Tezgah Alanı (m²):", value=_temp_brushed_granite_countertops_m2, min_value=0.0, step=0.1)
                    
                    _temp_terrace_laminated_wood_flooring_option = st.session_state.terrace_laminated_wood_flooring_option
                    st.session_state.terrace_laminated_wood_flooring_option = st.checkbox("Teras Laminat Ahşap Zemin Kaplaması", value=_temp_terrace_laminated_wood_flooring_option)
                    if st.session_state.terrace_laminated_wood_flooring_option:
                        _temp_terrace_laminated_wood_flooring_m2 = st.session_state.terrace_laminated_wood_flooring_m2_val
                        st.session_state.terrace_laminated_wood_flooring_m2_val = st.number_input("Teras Zemin Alanı (m²):", value=_temp_terrace_laminated_wood_flooring_m2, min_value=0.0, step=0.1)
                    
                    _temp_exterior_wood_cladding_m2_option = st.session_state.exterior_wood_cladding_m2_option
                    st.session_state.exterior_wood_cladding_m2_option = st.checkbox("Dış Cephe Ahşap Kaplama (Lambiri)", value=_temp_exterior_wood_cladding_m2_option)
                    if st.session_state.exterior_wood_cladding_m2_option:
                        _temp_exterior_wood_cladding_m2 = st.session_state.exterior_wood_cladding_m2_val
                        st.session_state.exterior_wood_cladding_m2_val = st.number_input("Dış Ahşap Kaplama Alanı (m²):", value=_temp_exterior_wood_cladding_m2, min_value=0.0, step=0.1)
                    
                    _temp_porcelain_tiles_option = st.session_state.porcelain_tiles_option
                    st.session_state.porcelain_tiles_option = st.checkbox("Porselen Fayans (Ekstra Zemin)", value=_temp_porcelain_tiles_option)
                    if st.session_state.porcelain_tiles_option:
                        _temp_porcelain_tiles_m2 = st.session_state.porcelain_tiles_m2_val
                        st.session_state.porcelain_tiles_m2_val = st.number_input("Porselen Fayans Alanı (m²):", value=_temp_porcelain_tiles_m2, min_value=0.0, step=0.1)

                with col_aether_2:
                    if st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                        _temp_exterior_cladding_m2_option = st.session_state.exterior_cladding_m2_option
                        st.session_state.exterior_cladding_m2_option = st.checkbox("Dış Cephe Kaplama (Knauf Aquapanel)", value=_temp_exterior_cladding_m2_option)
                        if st.session_state.exterior_cladding_m2_option:
                            _temp_exterior_cladding_m2 = st.session_state.exterior_cladding_m2_val
                            st.session_state.exterior_cladding_m2_val = st.number_input("Dış Cephe Kaplama Alanı (m²):", value=_temp_exterior_cladding_m2, min_value=0.0, step=0.1)

                        _temp_concrete_panel_floor_option = st.session_state.concrete_panel_floor_option
                        st.session_state.concrete_panel_floor_option = st.checkbox("Beton Panel Zemin", value=_temp_concrete_panel_floor_option)
                        if st.session_state.concrete_panel_floor_option:
                            _temp_concrete_panel_floor_m2 = st.session_state.concrete_panel_floor_m2_val
                            st.session_state.concrete_panel_floor_m2_val = st.number_input("Beton Zemin Alanı (m²):", value=_temp_concrete_panel_floor_m2, min_value=0.0, step=0.1)

                        _temp_premium_faucets_option = st.session_state.premium_faucets_option
                        st.session_state.premium_faucets_option = st.checkbox("Premium Bataryalar", value=_temp_premium_faucets_option)
                        _temp_integrated_fridge_option = st.session_state.integrated_fridge_option
                        st.session_state.integrated_fridge_option = st.checkbox("Entegre Buzdolabı", value=_temp_integrated_fridge_option)
                        _temp_designer_furniture_option = st.session_state.designer_furniture_option
                        st.session_state.designer_furniture_option = st.checkbox("Özel Tasarım Mobilyalar", value=_temp_designer_furniture_option)
                        _temp_italian_sofa_option = st.session_state.italian_sofa_option
                        st.session_state.italian_sofa_option = st.checkbox("İtalyan Kanepe", value=_temp_italian_sofa_option)
                        _temp_inclass_chairs_option = st.session_state.inclass_chairs_option
                        st.session_state.inclass_chairs_option = st.checkbox("Inclass Sandalyeler", value=_temp_inclass_chairs_option)
                        if st.session_state.inclass_chairs_option:
                            _temp_inclass_chairs_count = st.session_state.inclass_chairs_count
                            st.session_state.inclass_chairs_count = st.number_input("Sandalye Adedi:", value=_temp_inclass_chairs_count, min_value=0)
                        
                        _temp_smart_home_systems_option = st.session_state.smart_home_systems_option
                        st.session_state.smart_home_systems_option = st.checkbox("Akıllı Ev Sistemleri", value=_temp_smart_home_systems_option)
                        _temp_security_camera_option = st.session_state.security_camera_option
                        st.session_state.security_camera_option = st.checkbox("Güvenlik Kamerası Sistemi", value=_temp_security_camera_option)
                        _temp_white_goods_fridge_tv_option = st.session_state.white_goods_fridge_tv_option
                        st.session_state.white_goods_fridge_tv_option = st.checkbox("Beyaz Eşya (Buzdolabı/TV)", value=_temp_white_goods_fridge_tv_option)
                        _temp_sofa_option = st.session_state.sofa_option
                        st.session_state.sofa_option = st.checkbox("Kanepe", value=_temp_sofa_option)


        # --- Finansal Ayarlar ---
        st.markdown("<div class='section-title'>FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
        profit_rate_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
        _temp_profit_rate = st.session_state.profit_rate
        st.session_state.profit_rate = st.selectbox("Kar Oranı:", options=profit_rate_options, format_func=lambda x: x[0], index=profit_rate_options.index(_temp_profit_rate))
        st.markdown(f"<div>KDV Oranı: {VAT_RATE*100:.0f}% (Sabit)</div>", unsafe_allow_html=True)

        # --- Müşteri Notları ---
        st.markdown("<div class='section-title'>MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR</div>", unsafe_allow_html=True)
        _temp_customer_notes = st.session_state.customer_notes
        st.session_state.customer_notes = st.text_area("Müşteri Notları:", value=_temp_customer_notes)

        # --- PDF Dil Seçimi ---
        _temp_pdf_language = st.session_state.pdf_language
        st.session_state.pdf_language = st.selectbox(
            "Teklif PDF Dili:",
            options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')],
            format_func=lambda x: x[0],
            index=[('English-Greek', 'en_gr'), ('Turkish', 'tr')].index(_temp_pdf_language)
        )

        submit_button = st.form_submit_button("Hesapla ve Teklifleri Oluştur")

    if submit_button:
        try:
            # --- Hesaplama Mantığı ---
        except Exception as e:
            print(f"Hata oluştu: {e}")
            width, length, height = st.session_state.width_val, st.session_state.length_val, st.session_state.height_val
            areas = calculate_area(width, length, height)
            floor_area = areas["floor"]
            wall_area = areas["wall"]
            roof_area = areas["roof"]

            costs = [] # Tüm maliyet kalemleri buraya eklenecek
            profile_analysis_details = [] # Çelik profil analiz detaylarını tutacak

            # Yapı (metal iskelet ve boya her zaman eklenir, maliyeti 0 olsa bile bilgi için)
            costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            if st.session_state.structure_type == 'Light Steel':
                # Hafif çelik profillerin manuel veya otomatik adetleri
                has_manual_steel_profiles = sum([st.session_state.profile_100x100_count, st.session_state.profile_100x50_count,
                                                 st.session_state.profile_40x60_count, st.session_state.profile_50x50_count,
                                                 st.session_state.profile_120x60x5mm_count, st.session_state.profile_HEA160_count]) > 0

                if has_manual_steel_profiles:
                    if st.session_state.profile_100x100_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (100x100x3)", 'Quantity': f"{st.session_state.profile_100x100_count} adet ({st.session_state.profile_100x100_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                        profile_analysis_details.append({'Item': '100x100x3', 'Quantity': st.session_state.profile_100x100_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                    if st.session_state.profile_100x50_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (100x50x3)", 'Quantity': f"{st.session_state.profile_100x50_count} adet ({st.session_state.profile_100x50_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_100x50x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x50_count * FIYATLAR['steel_profile_100x50x3'])})
                        profile_analysis_details.append({'Item': '100x50x3', 'Quantity': st.session_state.profile_100x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x50x3'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_100x50_count * FIYATLAR['steel_profile_100x50x3'])})
                    if st.session_state.profile_40x60_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (40x60x2)", 'Quantity': f"{st.session_state.profile_40x60_count} adet ({st.session_state.profile_40x60_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_40x60x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_40x60_count * FIYATLAR['steel_profile_40x60x2'])})
                        profile_analysis_details.append({'Item': '40x60x2', 'Quantity': st.session_state.profile_40x60_count, 'Unit Price (€)': FIYATLAR['steel_profile_40x60x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_40x60_count * FIYATLAR['steel_profile_40x60x2'])})
                    if st.session_state.profile_50x50_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (50x50x2)", 'Quantity': f"{st.session_state.profile_50x50_count} adet ({st.session_state.profile_50x50_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                        profile_analysis_details.append({'Item': '50x50x2', 'Quantity': st.session_state.profile_50x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                    if st.session_state.profile_120x60x5mm_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (120x60x5mm)", 'Quantity': f"{st.session_state.profile_120x60x5mm_count} adet ({st.session_state.profile_120x60x5mm_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_120x60x5mm'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_120x60x5mm_count * FIYATLAR['steel_profile_120x60x5mm'])})
                        profile_analysis_details.append({'Item': '120x60x5mm', 'Quantity': st.session_state.profile_120x60x5mm_count, 'Unit Price (€)': FIYATLAR['steel_profile_120x60x5mm'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_120x60x5mm_count * FIYATLAR['steel_profile_120x60x5mm'])})
                    if st.session_state.profile_HEA160_count > 0:
                        costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} (HEA160)", 'Quantity': f"{st.session_state.profile_HEA160_count} adet ({st.session_state.profile_HEA160_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_HEA160'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_HEA160_count * FIYATLAR['steel_profile_HEA160'])})
                        profile_analysis_details.append({'Item': 'HEA160', 'Quantity': st.session_state.profile_HEA160_count, 'Unit Price (€)': FIYATLAR['steel_profile_HEA160'], 'Total (€)': calculate_rounded_up_cost(st.session_state.profile_HEA160_count * FIYATLAR['steel_profile_HEA160'])})
                    else:
                        # Otomatik hesaplama (eğer manuel giriş yapılmadıysa)
                        auto_100x100_count = math.ceil(floor_area * (12 / 27.0))
                        auto_50x50_count = math.ceil(floor_area * (6 / 27.0))
                        if auto_100x100_count > 0:
                            costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (100x100x3) (Auto)', 'Quantity': f"{auto_100x100_count} adet ({auto_100x100_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(auto_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                            profile_analysis_details.append({'Item': '100x100x3 (Auto)', 'Quantity': auto_100x100_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(auto_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                        if auto_50x50_count > 0:
                            costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (50x50x2) (Auto)', 'Quantity': f"{auto_50x50_count} adet ({auto_50x50_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(auto_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                            profile_analysis_details.append({'Item': '50x50x2 (Auto)', 'Quantity': auto_50x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(auto_50x50_count * FIYATLAR['steel_profile_50x50x2'])})

            else: # Heavy Steel
                heavy_steel_cost = floor_area * FIYATLAR['heavy_steel_m2']
                costs.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
                profile_analysis_details.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
                costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # Kaynak işçiliği
            welding_labor_price = FIYATLAR['welding_labor_m2_standard'] if st.session_state.welding_type == 'Standard Welding (160€/m²)' else FIYATLAR['welding_labor_m2_trmontaj']
            welding_cost = floor_area * welding_labor_price
            costs.append({'Item': f"Steel Welding Labor ({st.session_state.welding_type.split(' ')[0]})", 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': welding_labor_price, 'Total (€)': calculate_rounded_up_cost(welding_cost)})

            # 2. Duvarlar (Sandviç Panel, Alçıpan, OSB, Kaplamalar ve Yalıtım)
            # Dış/İç Duvar Sandviç Panel (Hafif Çelikte varsayılan, Ağır Çelikte opsiyonel)
            if st.session_state.structure_type == 'Light Steel' or st.session_state.facade_sandwich_panel_option:
                sandwich_panel_total_area = wall_area + roof_area
                sandwich_panel_cost = sandwich_panel_total_area * FIYATLAR["sandwich_panel_m2"]
                costs.append({'Item': MATERIAL_INFO_ITEMS['60mm_eps_sandwich_panel_info'], 'Quantity': f"{sandwich_panel_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': calculate_rounded_up_cost(sandwich_panel_cost)})
                costs.append({'Item': 'Panel Assembly Labor', 'Quantity': f"{sandwich_panel_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR['panel_assembly_labor_m2'], 'Total (€)': sandwich_panel_total_area * FIYATLAR['panel_assembly_labor_m2']})

            # İç Alçıpan / İç ve Dış Alçıpan
            plasterboard_total_area = 0
            if st.session_state.plasterboard_interior_option:
                plasterboard_total_area = wall_area
                costs.append({'Item': 'Interior Plasterboard (White)', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["gypsum_board_white_per_unit_price"], 'Total (€)': plasterboard_total_area * FIYATLAR["gypsum_board_white_per_unit_price"]})
                costs.append({'Item': 'Plasterboard Labor', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': plasterboard_total_area * FIYATLAR["plasterboard_labor_m2_avg"]})
                costs.append({'Item': MATERIAL_INFO_ITEMS['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
            
            if st.session_state.plasterboard_all_option: # Hem iç hem dış
                plasterboard_total_area = wall_area * 2 # İç ve dış duvar
                costs.append({'Item': 'Interior & Exterior Plasterboard (White)', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["gypsum_board_white_per_unit_price"], 'Total (€)': plasterboard_total_area * FIYATLAR["gypsum_board_white_per_unit_price"]})
                costs.append({'Item': 'Plasterboard Labor', 'Quantity': f"{plasterboard_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': plasterboard_total_area * FIYATLAR["plasterboard_labor_m2_avg"]})
                costs.append({'Item': MATERIAL_INFO_ITEMS['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # İç Duvar OSB Malzemesi
            if st.session_state.osb_inner_wall_option:
                osb_inner_wall_pieces = math.ceil(wall_area / OSB_PANEL_AREA_M2)
                costs.append({'Item': 'OSB Inner Wall Material', 'Quantity': f"{osb_inner_wall_pieces} adet", 'Unit Price (€)': FIYATLAR["osb_piece"], 'Total (€)': osb_inner_wall_pieces * FIYATLAR["osb_piece"]})

            # Duvar Yalıtımı
            if st.session_state.insulation_wall:
                insulation_m2_cost = FIYATLAR["insulation_per_m2"]
                if st.session_state.insulation_material_type == 'Stone Wool':
                    insulation_m2_cost = FIYATLAR['otb_stone_wool_price']
                    costs.append({'Item': f"Wall Insulation ({st.session_state.insulation_material_type})", 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': insulation_m2_cost, 'Total (€)': wall_area * insulation_m2_cost})
                elif st.session_state.insulation_material_type == 'Glass Wool':
                    glass_wool_packets = math.ceil(wall_area / GLASS_WOOL_M2_PER_PACKET)
                    glass_wool_cost = glass_wool_packets * FIYATLAR['glass_wool_5cm_packet_price']
                    costs.append({'Item': f"Wall Insulation ({st.session_state.insulation_material_type})", 'Quantity': f"{glass_wool_packets} paket", 'Unit Price (€)': FIYATLAR['glass_wool_5cm_packet_price'], 'Total (€)': glass_wool_cost})
            
            # Dış Cephe Kaplaması (Knauf Aquapanel)
            if st.session_state.exterior_cladding_m2_option and st.session_state.exterior_cladding_m2_val > 0:
                exterior_cladding_cost = st.session_state.exterior_cladding_m2_val * FIYATLAR['exterior_cladding_price_per_m2']
                costs.append({'Item': MATERIAL_INFO_ITEMS['knauf_aquapanel_gypsum_board_info'], 'Quantity': f"{st.session_state.exterior_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_price_per_m2'], 'Total (€)': exterior_cladding_cost})
                costs.append({'Item': MATERIAL_INFO_ITEMS['eps_styrofoam_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': MATERIAL_INFO_ITEMS['knauf_mineralplus_insulation_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
            
            # Dış Ahşap Kaplama (Lambiri)
            if st.session_state.exterior_wood_cladding_m2_option and st.session_state.exterior_wood_cladding_m2_val > 0:
                wood_cladding_cost = st.session_state.exterior_wood_cladding_m2_val * FIYATLAR['exterior_wood_cladding_m2_price']
                costs.append({'Item': MATERIAL_INFO_ITEMS['exterior_wood_cladding_lambiri_info'], 'Quantity': f"{st.session_state.exterior_wood_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'], 'Total (€)': wood_cladding_cost})

            # 3. Zemin Maliyetleri (Yalıtım ve Kaplama)
            if st.session_state.insulation_floor:
                floor_insulation_cost = floor_area * FIYATLAR['insulation_per_m2']
                costs.append({'Item': 'Floor Insulation', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['insulation_per_m2'], 'Total (€)': floor_insulation_cost})
                
                # Zemin yalıtım malzemeleri
                if st.session_state.skirting_length_val > 0:
                    costs.append({'Item': 'Skirting', 'Quantity': f"{st.session_state.skirting_length_val:.2f} m", 'Unit Price (€)': FIYATLAR['skirting_meter_price'], 'Total (€)': st.session_state.skirting_length_val * FIYATLAR['skirting_meter_price']})
                if st.session_state.laminate_flooring_m2_val > 0:
                    costs.append({'Item': 'Laminate Flooring 12mm', 'Quantity': f"{st.session_state.laminate_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['laminate_flooring_m2_price'], 'Total (€)': st.session_state.laminate_flooring_m2_val * FIYATLAR['laminate_flooring_m2_price']})
                if st.session_state.under_parquet_mat_m2_val > 0:
                    costs.append({'Item': 'Under Parquet Mat 4mm', 'Quantity': f"{st.session_state.under_parquet_mat_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['under_parquet_mat_m2_price'], 'Total (€)': st.session_state.under_parquet_mat_m2_val * FIYATLAR['under_parquet_mat_m2_price']})
                if st.session_state.osb2_18mm_count_val > 0:
                    costs.append({'Item': 'OSB2 18mm Panel', 'Quantity': f"{st.session_state.osb2_18mm_count_val} adet", 'Unit Price (€)': FIYATLAR['osb2_18mm_piece_price'], 'Total (€)': st.session_state.osb2_18mm_count_val * FIYATLAR['osb2_18mm_piece_price']})
                if st.session_state.galvanized_sheet_m2_val > 0:
                    costs.append({'Item': '5mm Galvanized Sheet', 'Quantity': f"{st.session_state.galvanized_sheet_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['galvanized_sheet_m2_price'], 'Total (€)': st.session_state.galvanized_sheet_m2_val * FIYATLAR['galvanized_sheet_m2_price']})

                # Beton Panel Zemin (Elite pakete özel)
                if st.session_state.concrete_panel_floor_option and st.session_state.concrete_panel_floor_m2_val > 0:
                    concrete_panel_cost = st.session_state.concrete_panel_floor_m2_val * FIYATLAR['concrete_panel_floor_price_per_m2']
                    costs.append({'Item': MATERIAL_INFO_ITEMS['concrete_panel_floor_info'], 'Quantity': f"{st.session_state.concrete_panel_floor_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})

                # Teras Lamine Ahşap Zemin (Premium/Elite pakete özel)
                if st.session_state.terrace_laminated_wood_flooring_option and st.session_state.terrace_laminated_wood_flooring_m2_val > 0:
                    terrace_laminated_cost = st.session_state.terrace_laminated_wood_flooring_m2_val * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2']
                    costs.append({'Item': MATERIAL_INFO_ITEMS['treated_pine_floor_info'], 'Quantity': f"{st.session_state.terrace_laminated_wood_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_laminated_cost})

                # Porselen Fayans (Ekstra Zemin)
                if st.session_state.porcelain_tiles_option and st.session_state.porcelain_tiles_m2_val > 0:
                    porcelain_tiles_cost = st.session_state.porcelain_tiles_m2_val * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                    costs.append({'Item': MATERIAL_INFO_ITEMS['porcelain_tiles_info'], 'Quantity': f"{st.session_state.porcelain_tiles_m2_val:.2f} m²", 'Unit Price (€)': (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']), 'Total (€)': porcelain_tiles_cost})
                    
            # 4. Doğramalar (Pencere ve Kapılar)
            window_cost = st.session_state.window_count * FIYATLAR['aluminum_window_piece']
            costs.append({'Item': f"Window ({st.session_state.window_size})", 'Quantity': st.session_state.window_count, 'Unit Price (€)': FIYATLAR['aluminum_window_piece'], 'Total (€)': window_cost})
            
            sliding_door_cost = st.session_state.sliding_door_count * FIYATLAR['sliding_glass_door_piece']
            if st.session_state.sliding_door_count > 0:
                costs.append({'Item': f"Sliding Glass Door ({st.session_state.sliding_door_size})", 'Quantity': st.session_state.sliding_door_count, 'Unit Price (€)': FIYATLAR['sliding_glass_door_piece'], 'Total (€)': sliding_door_cost})

            wc_window_cost = st.session_state.wc_window_count * FIYATLAR['wc_window_piece']
            if st.session_state.wc_window_count > 0:
                costs.append({'Item': f"WC Window ({st.session_state.wc_window_size})", 'Quantity': st.session_state.wc_window_count, 'Unit Price (€)': FIYATLAR['wc_window_piece'], 'Total (€)': wc_window_cost})

            wc_sliding_door_cost = st.session_state.wc_sliding_door_count * FIYATLAR['wc_sliding_door_piece']
            if st.session_state.wc_sliding_door_count > 0:
                costs.append({'Item': f"WC Sliding Door ({st.session_state.wc_sliding_door_size})", 'Quantity': st.session_state.wc_sliding_door_count, 'Unit Price (€)': FIYATLAR['wc_sliding_door_piece'], 'Total (€)': wc_sliding_door_cost})
            
            door_cost = st.session_state.door_count * FIYATLAR['door_piece']
            costs.append({'Item': f"Door ({st.session_state.door_size})", 'Quantity': st.session_state.door_count, 'Unit Price (€)': FIYATLAR['door_piece'], 'Total (€)': door_cost})
            
            total_doors_windows = st.session_state.window_count + st.session_state.sliding_door_count + st.session_state.wc_window_count + st.session_state.wc_sliding_door_count + st.session_state.door_count
            door_window_assembly_cost = total_doors_windows * FIYATLAR['door_window_assembly_labor_piece']
            costs.append({'Item': 'Door/Window Assembly Labor', 'Quantity': f"{total_doors_windows} adet", 'Unit Price (€)': FIYATLAR['door_window_assembly_labor_piece'], 'Total (€)': door_window_assembly_cost})

            # 5. Mutfak ve Banyo Tesisatları
            kitchen_cost = 0.0
            kitchen_type_display
# ==============================================================================
# BÖLÜM 8: run_streamlit_app() - Kullanıcı Arayüzü Girişleri (Ek Donanımlar, Finansal Ayarlar, Notlar) ve Hesaplama/PDF Tetikleme
# ==============================================================================

        st.markdown("<div class='section-title'>EK DONANIMLAR</div>", unsafe_allow_html=True)
        
        _temp_shower_wc = st.session_state.shower_wc
        st.session_state.shower_wc = st.checkbox("Duş/WC Dahil Et", value=_temp_shower_wc, key="shower_checkbox")
        
        col_ceramic1, col_ceramic2 = st.columns(2)
        with col_ceramic1:
            wc_ceramic_disabled = not st.session_state.shower_wc # WC seramik sadece duş/WC seçiliyse etkin
            _temp_wc_ceramic = st.session_state.wc_ceramic
            st.session_state.wc_ceramic = st.checkbox("WC Seramik Zemin/Duvar", value=_temp_wc_ceramic, disabled=wc_ceramic_disabled, key="wc_ceramic_checkbox")
        with col_ceramic2:
            wc_ceramic_area_disabled = not st.session_state.wc_ceramic
            _temp_wc_ceramic_area = st.session_state.wc_ceramic_area
            st.session_state.wc_ceramic_area = st.number_input("WC Seramik Alanı (m²):", value=_temp_wc_ceramic_area, step=0.1, min_value=0.0, disabled=wc_ceramic_area_disabled, key="wc_ceramic_area_input")
        
        _temp_electrical = st.session_state.electrical
        st.session_state.electrical = st.checkbox("Elektrik Tesisatı (Malzemelerle)", value=_temp_electrical, key="electrical_checkbox")
        _temp_plumbing = st.session_state.plumbing
        st.session_state.plumbing = st.checkbox("Sıhhi Tesisat (Malzemelerle)", value=_temp_plumbing, key="plumbing_checkbox")
        
        st.markdown("---")
        st.subheader("Zemin Yalıtımı ve Malzemeleri")
        _temp_insulation_floor = st.session_state.insulation_floor
        st.session_state.insulation_floor = st.checkbox("Zemin Yalıtımı Dahil Et (5€/m²)", value=_temp_insulation_floor, key="floor_insulation_checkbox")
        
        floor_insulation_material_disabled = not st.session_state.insulation_floor

        col_floor_mats = st.columns(3)
        with col_floor_mats[0]:
            _temp_skirting_length = st.session_state.skirting_length_val
            st.session_state.skirting_length_val = st.number_input(f"Süpürgelik ({FIYATLAR['skirting_meter_price']}€/m) Uzunluğu (m):", value=_temp_skirting_length, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="skirting_input")
        with col_floor_mats[1]:
            _temp_laminate_flooring_m2 = st.session_state.laminate_flooring_m2_val
            st.session_state.laminate_flooring_m2_val = st.number_input(f"Laminat Parke 12mm ({FIYATLAR['laminate_flooring_m2_price']}€/m²) Alanı (m²):", value=_temp_laminate_flooring_m2, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="laminate_flooring_input")
        with col_floor_mats[2]:
            _temp_under_parquet_mat_m2 = st.session_state.under_parquet_mat_m2_val
            st.session_state.under_parquet_mat_m2_val = st.number_input(f"Parke Altı Şilte 4mm ({FIYATLAR['under_parquet_mat_m2_price']}€/m²) Alanı (m²):", value=_temp_under_parquet_mat_m2, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="under_parquet_mat_input")
        
        col_floor_mats2 = st.columns(3)
        with col_floor_mats2[0]:
            _temp_osb2_18mm_count = st.session_state.osb2_18mm_count_val
            st.session_state.osb2_18mm_count_val = st.number_input(f"OSB2 18mm/Beton Panel ({FIYATLAR['osb2_18mm_piece_price']}€/adet) Adet:", value=_temp_osb2_18mm_count, min_value=0, disabled=floor_insulation_material_disabled, key="osb2_input")
        with col_floor_mats2[1]:
            _temp_galvanized_sheet_m2 = st.session_state.galvanized_sheet_m2_val
            st.session_state.galvanized_sheet_m2_val = st.number_input(f"5mm Galvanizli Sac ({FIYATLAR['galvanized_sheet_m2_price']}€/m²) Alanı (m²):", value=_temp_galvanized_sheet_m2, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="galvanized_sheet_input")
        with col_floor_mats2[2]:
            # This space is left for the insulation material type selectbox, which is placed outside this column structure.
            pass

        _temp_insulation_wall = st.session_state.insulation_wall
        st.session_state.insulation_wall = st.checkbox("Duvar Yalıtımı Dahil Et (10€/m²)", value=_temp_insulation_wall, key="wall_insulation_checkbox")
        
        st.markdown("---")

        _temp_transportation = st.session_state.transportation
        st.session_state.transportation = st.checkbox("Nakliye Dahil Et (350€)", value=_temp_transportation, key="transportation_checkbox")
        _temp_heating = st.session_state.heating
        st.session_state.heating = st.checkbox("Yerden Isıtma Dahil Et (50€/m²)", value=_temp_heating, key="heating_checkbox")
        _temp_solar = st.session_state.solar
        st.session_state.solar = st.checkbox("Güneş Enerjisi Sistemi", value=_temp_solar, key="solar_checkbox")
        
        col14, col15 = st.columns(2)
        with col14:
            _temp_solar_kw = st.session_state.solar_kw
            st.session_state.solar_kw = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not st.session_state.solar, index=[5, 7.2, 11].index(_temp_solar_kw), key="solar_capacity_select")
        with col15:
            # Sadece görüntüleme, hesaplama butona basıldığında yapılır
            solar_price_display = st.session_state.solar_kw * FIYATLAR['solar_per_kw'] if st.session_state.solar else 0.0
            st.number_input("Güneş Enerjisi Fiyatı (€):", value=solar_price_display, disabled=True, key="solar_price_display")

        _temp_wheeled_trailer = st.session_state.wheeled_trailer
        st.session_state.wheeled_trailer = st.checkbox("Tekerlekli Römork", value=_temp_wheeled_trailer, key="trailer_checkbox")
        _temp_wheeled_trailer_price = st.session_state.wheeled_trailer_price
        st.session_state.wheeled_trailer_price = st.number_input("Römork Fiyatı (€):", value=_temp_wheeled_trailer_price, step=0.1, disabled=not st.session_state.wheeled_trailer, key="trailer_price_input")


        # --- Aether Living Opsiyonları (Pakete göre görünür/gizlenir) ---
        if st.session_state.aether_package_choice != 'None':
            st.markdown("<div class='section-title'>AETHER LIVING EK OPSİYONLARI</div>", unsafe_allow_html=True)
            
            col_aether_1, col_aether_2 = st.columns(2)
            with col_aether_1:
                # Premium ve Elite Paketler
                _disabled_prem_elite = (st.session_state.aether_package_choice != 'Aether Living | Loft Premium (ESSENTIAL)') and (st.session_state.aether_package_choice != 'Aether Living | Loft Elite (LUXURY)')

                _temp_bedroom_set_option = st.session_state.bedroom_set_option
                st.session_state.bedroom_set_option = st.checkbox("Yatak Odası Takımı", value=_temp_bedroom_set_option, disabled=_disabled_prem_elite, key="bedroom_set_cb")
                
                _temp_brushed_granite_countertops_option = st.session_state.brushed_granite_countertops_option
                st.session_state.brushed_granite_countertops_option = st.checkbox("Fırçalanmış Granit Tezgahlar", value=_temp_brushed_granite_countertops_option, disabled=_disabled_prem_elite, key="granite_cb")
                if st.session_state.brushed_granite_countertops_option or (_brushed_granite_countertops_default_val and _disabled_prem_elite): # _brushed_granite_countertops_default_val kullanıldı
                    _granite_area_default = st.session_state.width_val * st.session_state.length_val / 10 # Örnek m2
                    _temp_brushed_granite_countertops_m2 = st.session_state.brushed_granite_countertops_m2_val
                    st.session_state.brushed_granite_countertops_m2_val = st.number_input("Granit Tezgah Alanı (m²):", value=_granite_area_default if _brushed_granite_countertops_default_val else _temp_brushed_granite_countertops_m2, min_value=0.0, step=0.1, key="granite_area_input", disabled=_disabled_prem_elite)
                
                _temp_terrace_laminated_wood_flooring_option = st.session_state.terrace_laminated_wood_flooring_option
                st.session_state.terrace_laminated_wood_flooring_option = st.checkbox("Teras Laminat Ahşap Zemin Kaplaması", value=_temp_terrace_laminated_wood_flooring_option, disabled=_disabled_prem_elite, key="terrace_flooring_cb")
                if st.session_state.terrace_laminated_wood_flooring_option or (_terrace_laminated_wood_flooring_default_val and _disabled_prem_elite):
                    _terrace_area_default = st.session_state.width_val * st.session_state.length_val / 5 # Örnek m2
                    _temp_terrace_laminated_wood_flooring_m2 = st.session_state.terrace_laminated_wood_flooring_m2_val
                    st.session_state.terrace_laminated_wood_flooring_m2_val = st.number_input("Teras Zemin Alanı (m²):", value=_terrace_area_default if _terrace_laminated_wood_flooring_default_val else _temp_terrace_laminated_wood_flooring_m2, min_value=0.0, step=0.1, key="terrace_flooring_area_input", disabled=_disabled_prem_elite)
                
                _temp_exterior_wood_cladding_m2_option = st.session_state.exterior_wood_cladding_m2_option
                st.session_state.exterior_wood_cladding_m2_option = st.checkbox("Dış Cephe Ahşap Kaplama (Lambiri)", value=_temp_exterior_wood_cladding_m2_option, disabled=False, key="wood_cladding_cb") # Bu her zaman manuel seçilebilir, Elite'te otomatikleşmez
                if st.session_state.exterior_wood_cladding_m2_option:
                    _temp_exterior_wood_cladding_m2 = st.session_state.exterior_wood_cladding_m2_val
                    st.session_state.exterior_wood_cladding_m2_val = st.number_input("Dış Ahşap Kaplama Alanı (m²):", value=_temp_exterior_wood_cladding_m2, min_value=0.0, step=0.1, key="wood_cladding_area_input")
                
                _temp_porcelain_tiles_option = st.session_state.porcelain_tiles_option
                st.session_state.porcelain_tiles_option = st.checkbox("Porselen Fayans (Ekstra Zemin)", value=_temp_porcelain_tiles_option, disabled=False, key="porcelain_tiles_cb") # Bu da manuel seçilebilir
                if st.session_state.porcelain_tiles_option:
                    _porcelain_area_default = st.session_state.width_val * st.session_state.length_val # Tüm zemin alanı varsayılan
                    _temp_porcelain_tiles_m2 = st.session_state.porcelain_tiles_m2_val
                    st.session_state.porcelain_tiles_m2_val = st.number_input("Porselen Fayans Alanı (m²):", value=_porcelain_area_default if _porcelain_tiles_default_val else _temp_porcelain_tiles_m2, min_value=0.0, step=0.1, key="porcelain_tiles_area_input")

            with col_aether_2:
                # Elite paket için özel
                _disabled_elite = (st.session_state.aether_package_choice != 'Aether Living | Loft Elite (LUXURY)')
                
                _temp_exterior_cladding_m2_option = st.session_state.exterior_cladding_m2_option
                st.session_state.exterior_cladding_m2_option = st.checkbox("Dış Cephe Kaplama (Knauf Aquapanel)", value=_temp_exterior_cladding_m2_option, disabled=_disabled_elite, key="ext_cladding_cb")
                if st.session_state.exterior_cladding_m2_option or (_exterior_cladding_default_val and _disabled_elite):
                    _cladding_area_default = st.session_state.width_val * st.session_state.length_val # Tüm zemin alanı varsayılan
                    _temp_exterior_cladding_m2 = st.session_state.exterior_cladding_m2_val
                    st.session_state.exterior_cladding_m2_val = st.number_input("Dış Cephe Kaplama Alanı (m²):", value=_cladding_area_default if _exterior_cladding_default_val else _temp_exterior_cladding_m2, min_value=0.0, step=0.1, key="ext_cladding_area_input", disabled=_disabled_elite)

                _temp_concrete_panel_floor_option = st.session_state.concrete_panel_floor_option
                st.session_state.concrete_panel_floor_option = st.checkbox("Beton Panel Zemin", value=_temp_concrete_panel_floor_option, disabled=_disabled_elite, key="concrete_floor_cb")
                if st.session_state.concrete_panel_floor_option or (_concrete_panel_floor_default_val and _disabled_elite):
                    _concrete_floor_area_default = st.session_state.width_val * st.session_state.length_val # Tüm zemin alanı varsayılan
                    _temp_concrete_panel_floor_m2 = st.session_state.concrete_panel_floor_m2_val
                    st.session_state.concrete_panel_floor_m2_val = st.number_input("Beton Zemin Alanı (m²):", value=_concrete_floor_area_default if _concrete_panel_floor_default_val else _temp_concrete_panel_floor_m2, min_value=0.0, step=0.1, key="concrete_floor_area_input", disabled=_disabled_elite)

                _temp_premium_faucets_option = st.session_state.premium_faucets_option
                st.session_state.premium_faucets_option = st.checkbox("Premium Bataryalar", value=_temp_premium_faucets_option, disabled=_disabled_elite, key="premium_faucets_cb")
                _temp_integrated_fridge_option = st.session_state.integrated_fridge_option
                st.session_state.integrated_fridge_option = st.checkbox("Entegre Buzdolabı", value=_temp_integrated_fridge_option, disabled=_disabled_elite, key="integrated_fridge_cb")
                _temp_designer_furniture_option = st.session_state.designer_furniture_option
                st.session_state.designer_furniture_option = st.checkbox("Özel Tasarım Mobilyalar", value=_temp_designer_furniture_option, disabled=_disabled_elite, key="designer_furniture_cb")
                _temp_italian_sofa_option = st.session_state.italian_sofa_option
                st.session_state.italian_sofa_option = st.checkbox("İtalyan Kanepe", value=_temp_italian_sofa_option, disabled=_disabled_elite, key="italian_sofa_cb")
                _temp_inclass_chairs_option = st.session_state.inclass_chairs_option
                st.session_state.inclass_chairs_option = st.checkbox("Inclass Sandalyeler", value=_temp_inclass_chairs_option, disabled=_disabled_elite, key="inclass_chairs_cb")
                if st.session_state.inclass_chairs_option:
                    _temp_inclass_chairs_count = st.session_state.inclass_chairs_count
                    st.session_state.inclass_chairs_count = st.number_input("Sandalye Adedi:", value=_temp_inclass_chairs_count, min_value=0, disabled=_disabled_elite, key="chairs_count_input")
                
                _temp_smart_home_systems_option = st.session_state.smart_home_systems_option
                st.session_state.smart_home_systems_option = st.checkbox("Akıllı Ev Sistemleri", value=_temp_smart_home_systems_option, disabled=_disabled_elite, key="smart_home_cb")
                _temp_security_camera_option = st.session_state.security_camera_option
                st.session_state.security_camera_option = st.checkbox("Güvenlik Kamerası Sistemi", value=_temp_security_camera_option, disabled=_disabled_elite, key="security_cam_cb")
                _temp_white_goods_fridge_tv_option = st.session_state.white_goods_fridge_tv_option
                st.session_state.white_goods_fridge_tv_option = st.checkbox("Beyaz Eşya (Buzdolabı/TV)", value=_temp_white_goods_fridge_tv_option, disabled=_disabled_elite, key="white_goods_cb")
                _temp_sofa_option = st.session_state.sofa_option
                st.session_state.sofa_option = st.checkbox("Kanepe", value=_temp_sofa_option, disabled=_disabled_elite, key="sofa_cb")


        # --- Finansal Ayarlar ---
        st.markdown("<div class='section-title'>FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
        profit_rate_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
        _temp_profit_rate_tuple = st.session_state.profit_rate
        st.session_state.profit_rate = st.selectbox("Kar Oranı:", options=profit_rate_options, format_func=lambda x: x[0], index=profit_rate_options.index(_temp_profit_rate_tuple), key="profit_rate_select")
        st.markdown(f"<div>KDV Oranı: {VAT_RATE*100:.0f}% (Sabit)</div>", unsafe_allow_html=True)

        # --- Müşteri Notları ---
        st.markdown("<div class='section-title'>MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR</div>", unsafe_allow_html=True)
        _temp_customer_notes = st.session_state.customer_notes
        st.session_state.customer_notes = st.text_area("Müşteri Notları:", value=_temp_customer_notes, key="customer_notes_textarea")

        # --- PDF Dil Seçimi ---
        _temp_pdf_language_tuple = st.session_state.pdf_language
        st.session_state.pdf_language = st.selectbox(
            "Teklif PDF Dili:",
            options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')],
            format_func=lambda x: x[0],
            index=[('English-Greek', 'en_gr'), ('Turkish', 'tr')].index(_temp_pdf_language_tuple)
        )

        submit_button = st.form_submit_button("Hesapla ve Teklifleri Oluştur")

    if submitted:
        try:
            # --- Hesaplama Mantığı ---
        except Exception as e:
            print(f"Hata oluştu: {e}")
            width, length, height = st.session_state.width_val, st.session_state.length_val, st.session_state.height_val
            areas = calculate_area(width, length, height)
            floor_area = areas["floor"]
            wall_area = areas["wall"]
            roof_area = areas["roof"]

            costs = [] # Tüm maliyet kalemleri buraya eklenecek
            profile_analysis_details = [] # Çelik profil analiz detaylarını tutacak

            # Yapı (metal iskelet ve boya her zaman eklenir, maliyeti 0 olsa bile bilgi için)
            costs.append({'Item': MATERIAL_INFO_ITEMS['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # Hafif/Ağır Çelik Yapısal Maliyetler
            if st.session_state.structure_type == 'Light Steel':
                # Hafif çelik profillerin manuel veya otomatik adetleri
                # Bu bölüm sadece Light Steel ise çalışır
                profile_types_and_counts = {
                    "100x100x3": st.session_state.profile_100x100_count,
                    "100x50x3": st.session_state.profile_100x50_count,
                    "40x60x2": st.session_state.profile_40x60_count,
                    "50x50x2": st.session_state.profile_50x50_count, # UI'dan gelen key
                    "120x60x5mm": st.session_state.profile_120x60x5mm_count,
                    "HEA160": st.session_state.profile_HEA160_count,
                }
                
                # Manuel adetler sıfırdan büyükse onları kullan, aksi takdirde otomatik hesapla
                has_manual_steel_profiles = sum(profile_types_and_counts.values()) > 0
                
                if has_manual_steel_profiles:
                    for p_type, p_count in profile_types_and_counts.items():
                        if p_count > 0:
                            fiytlar_key = f"steel_profile_{p_type.replace('x', '_').lower()}" 
                            cost_per_piece = FIYATLAR.get(fiytlar_key, 0.0)
                            total_profile_cost = p_count * cost_per_piece
                            costs.append({'Item': f"{MATERIAL_INFO_ITEMS['steel_skeleton_info']} ({p_type})", 'Quantity': f"{p_count} adet", 'Unit Price (€)': cost_per_piece, 'Total (€)': calculate_rounded_up_cost(total_profile_cost)})
                            profile_analysis_details.append({'Item': p_type, 'Quantity': p_count, 'Unit Price (€)': cost_per_piece, 'Total (€)': calculate_rounded_up_cost(total_profile_cost)})
                else: # Otomatik hesaplama
                    auto_100x100_count = math.ceil(floor_area * (12 / 27.0))
                    auto_50x50_count = math.ceil(floor_area * (6 / 27.0))
                    if auto_100x100_count > 0:
                        costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (100x100x3) (Auto)', 'Quantity': f"{auto_100x100_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(auto_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                        profile_analysis_details.append({'Item': '100x100x3 (Auto)', 'Quantity': auto_100x100_count, 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(auto_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                    if auto_50x50_count > 0:
                        costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (50x50x2) (Auto)', 'Quantity': f"{auto_50x50_count} adet", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(auto_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                        profile_analysis_details.append({'Item': '50x50x2 (Auto)', 'Quantity': auto_50x50_count, 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(auto_50x50_count * FIYATLAR['steel_profile_50x50x2'])})

            else: # Heavy Steel
                heavy_steel_cost = floor_area * FIYATLAR['heavy_steel_m2']
                costs.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})
                profile_analysis_details.append({'Item': 'Heavy Steel Structure', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['heavy_steel_m2'], 'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)})

            # Kaynak işçiliği
            welding_labor_price = FIYATLAR['welding_labor_m2_standard'] if st.session_state.welding_type == 'Standard Welding (160€/m²)' else FIYATLAR['welding_labor_m2_trmontaj']
            welding_cost = floor_area * welding_labor_price
            costs.append({'Item': f"Steel Welding Labor ({st.session_state.welding_type.split(' ')[0]})", 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': welding_labor_price, 'Total (€)': calculate_rounded_up_cost(welding_cost)})
            
            # Duvarlar (Sandviç Panel, Alçıpan, OSB, Kaplamalar ve Yalıtım)
            # Dış/İç Duvar Sandviç Panel (Hafif Çelikte varsayılan, Ağır Çelikte opsiyonel)
            if st.session_state.structure_type == 'Light Steel' or st.session_state.facade_sandwich_panel_option:
                sandwich_panel_total_area = wall_area + roof_area
                sandwich_panel_cost = sandwich_panel_total_area * FIYATLAR["sandwich_panel_m2"]
                costs.append({'Item': MATERIAL_INFO_ITEMS['60mm_eps_sandwich_panel_info'], 'Quantity': f"{sandwich_panel_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': calculate_rounded_up_cost(sandwich_panel_cost)})
                costs.append({'Item': 'Panel Assembly Labor', 'Quantity': f"{sandwich_panel_total_area:.2f} m²", 'Unit Price (€)': FIYATLAR['panel_assembly_labor_m2'], 'Total (€)': sandwich_panel_total_area * FIYATLAR['panel_assembly_labor_m2']})

            # İç Alçıpan / İç ve Dış Alçıpan
            plasterboard_total_area_calc = 0
            if st.session_state.plasterboard_interior_option:
                plasterboard_total_area_calc = wall_area
                costs.append({'Item': 'Interior Plasterboard (White)', 'Quantity': f"{plasterboard_total_area_calc:.2f} m²", 'Unit Price (€)': FIYATLAR["gypsum_board_white_per_unit_price"], 'Total (€)': plasterboard_total_area_calc * FIYATLAR["gypsum_board_white_per_unit_price"]})
                costs.append({'Item': 'Plasterboard Labor', 'Quantity': f"{plasterboard_total_area_calc:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': plasterboard_total_area_calc * FIYATLAR["plasterboard_labor_m2_avg"]})
                costs.append({'Item': MATERIAL_INFO_ITEMS['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
            
            if st.session_state.plasterboard_all_option: # Hem iç hem dış
                plasterboard_total_area_calc = wall_area * 2 # İç ve dış duvar
                costs.append({'Item': 'Interior & Exterior Plasterboard (White)', 'Quantity': f"{plasterboard_total_area_calc:.2f} m²", 'Unit Price (€)': FIYATLAR["gypsum_board_white_per_unit_price"], 'Total (€)': plasterboard_total_area_calc * FIYATLAR["gypsum_board_white_per_unit_price"]})
                costs.append({'Item': 'Plasterboard Labor', 'Quantity': f"{plasterboard_total_area_calc:.2f} m²", 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': plasterboard_total_area_calc * FIYATLAR["plasterboard_labor_m2_avg"]})
                costs.append({'Item': MATERIAL_INFO_ITEMS['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

            # İç Duvar OSB Malzemesi
            if st.session_state.osb_inner_wall_option:
                osb_inner_wall_pieces = math.ceil(wall_area / OSB_PANEL_AREA_M2)
                costs.append({'Item': 'OSB Inner Wall Material', 'Quantity': f"{osb_inner_wall_pieces} adet", 'Unit Price (€)': FIYATLAR["osb_piece"], 'Total (€)': osb_inner_wall_pieces * FIYATLAR["osb_piece"]})

            # Duvar Yalıtımı
            if st.session_state.insulation_wall:
                insulation_m2_cost_for_wall = FIYATLAR["insulation_per_m2"]
                if st.session_state.insulation_material_type == 'Stone Wool':
                    insulation_m2_cost_for_wall = FIYATLAR['otb_stone_wool_price']
                    costs.append({'Item': f"Wall Insulation ({st.session_state.insulation_material_type})", 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': insulation_m2_cost_for_wall, 'Total (€)': wall_area * insulation_m2_cost_for_wall})
                elif st.session_state.insulation_material_type == 'Glass Wool':
                    glass_wool_packets_for_wall = math.ceil(wall_area / GLASS_WOOL_M2_PER_PACKET)
                    glass_wool_cost_for_wall = glass_wool_packets_for_wall * FIYATLAR['glass_wool_5cm_packet_price']
                    costs.append({'Item': f"Wall Insulation ({st.session_state.insulation_material_type})", 'Quantity': f"{glass_wool_packets_for_wall} paket", 'Unit Price (€)': FIYATLAR['glass_wool_5cm_packet_price'], 'Total (€)': glass_wool_cost_for_wall})
                elif st.session_state.insulation_material_type == 'Yalıtım Yapılmayacak':
                    # Maliyet sıfır olarak ele alınacak, zaten hesaplanmaz.
                    pass
            
            # Dış Cephe Kaplaması (Knauf Aquapanel)
            if st.session_state.exterior_cladding_m2_option and st.session_state.exterior_cladding_m2_val > 0:
                exterior_cladding_cost = st.session_state.exterior_cladding_m2_val * FIYATLAR['exterior_cladding_price_per_m2']
                costs.append({'Item': MATERIAL_INFO_ITEMS['knauf_aquapanel_gypsum_board_info'], 'Quantity': f"{st.session_state.exterior_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_price_per_m2'], 'Total (€)': exterior_cladding_cost})
                costs.append({'Item': MATERIAL_INFO_ITEMS['eps_styrofoam_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': MATERIAL_INFO_ITEMS['knauf_mineralplus_insulation_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
            
            # Dış Ahşap Kaplama (Lambiri)
            if st.session_state.exterior_wood_cladding_m2_option and st.session_state.exterior_wood_cladding_m2_val > 0:
                wood_cladding_cost = st.session_state.exterior_wood_cladding_m2_val * FIYATLAR['exterior_wood_cladding_m2_price']
                costs.append({'Item': MATERIAL_INFO_ITEMS['exterior_wood_cladding_lambiri_info'], 'Quantity': f"{st.session_state.exterior_wood_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'], 'Total (€)': wood_cladding_cost})

            # 3. Zemin Maliyetleri (Yalıtım ve Kaplama)
            if st.session_state.insulation_floor:
                floor_insulation_cost = floor_area * FIYATLAR['insulation_per_m2']
                costs.append({'Item': 'Floor Insulation', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['insulation_per_m2'], 'Total (€)': floor_insulation_cost})
                
                # Zemin yalıtım malzemeleri
                if st.session_state.skirting_length_val > 0:
                    costs.append({'Item': 'Skirting', 'Quantity': f"{st.session_state.skirting_length_val:.2f} m", 'Unit Price (€)': FIYATLAR['skirting_meter_price'], 'Total (€)': st.session_state.skirting_length_val * FIYATLAR['skirting_meter_price']})
                if st.session_state.laminate_flooring_m2_val > 0:
                    costs.append({'Item': 'Laminate Flooring 12mm', 'Quantity': f"{st.session_state.laminate_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['laminate_flooring_m2_price'], 'Total (€)': st.session_state.laminate_flooring_m2_val * FIYATLAR['laminate_flooring_m2_price']})
                if st.session_state.under_parquet_mat_m2_val > 0:
                    costs.append({'Item': 'Under Parquet Mat 4mm', 'Quantity': f"{st.session_state.under_parquet_mat_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['under_parquet_mat_m2_price'], 'Total (€)': st.session_state.under_parquet_mat_m2_val * FIYATLAR['under_parquet_mat_m2_price']})
                if st.session_state.osb2_18mm_count_val > 0:
                    costs.append({'Item': 'OSB2 18mm Panel', 'Quantity': f"{st.session_state.osb2_18mm_count_val} adet", 'Unit Price (€)': FIYATLAR['osb2_18mm_piece_price'], 'Total (€)': st.session_state.osb2_18mm_count_val * FIYATLAR['osb2_18mm_piece_price']})
                if st.session_state.galvanized_sheet_m2_val > 0:
                    costs.append({'Item': '5mm Galvanized Sheet', 'Quantity': f"{st.session_state.galvanized_sheet_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['galvanized_sheet_m2_price'], 'Total (€)': st.session_state.galvanized_sheet_m2_val * FIYATLAR['galvanized_sheet_m2_price']})

                # Beton Panel Zemin (Elite pakete özel)
                if st.session_state.concrete_panel_floor_option and st.session_state.concrete_panel_floor_m2_val > 0:
                    concrete_panel_cost = st.session_state.concrete_panel_floor_m2_val * FIYATLAR['concrete_panel_floor_price_per_m2']
                    costs.append({'Item': MATERIAL_INFO_ITEMS['concrete_panel_floor_info'], 'Quantity': f"{st.session_state.concrete_panel_floor_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})

                # Teras Lamine Ahşap Zemin (Premium/Elite pakete özel)
                if st.session_state.terrace_laminated_wood_flooring_option and st.session_state.terrace_laminated_wood_flooring_m2_val > 0:
                    terrace_laminated_cost = st.session_state.terrace_laminated_wood_flooring_m2_val * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2']
                    costs.append({'Item': MATERIAL_INFO_ITEMS['treated_pine_floor_info'], 'Quantity': f"{st.session_state.terrace_laminated_wood_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_laminated_cost})

                # Porselen Fayans (Ekstra Zemin)
                if st.session_state.porcelain_tiles_option and st.session_state.porcelain_tiles_m2_val > 0:
                    porcelain_tiles_cost = st.session_state.porcelain_tiles_m2_val * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                    costs.append({'Item': MATERIAL_INFO_ITEMS['porcelain_tiles_info'], 'Quantity': f"{st.session_state.porcelain_tiles_m2_val:.2f} m²", 'Unit Price (€)': (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']), 'Total (€)': porcelain_tiles_cost})
                    
            # 4. Doğramalar (Pencere ve Kapılar)
            window_cost = st.session_state.window_count * FIYATLAR['aluminum_window_piece']
            costs.append({'Item': f"Window ({st.session_state.window_size})", 'Quantity': st.session_state.window_count, 'Unit Price (€)': FIYATLAR['aluminum_window_piece'], 'Total (€)': window_cost})
            
            sliding_door_cost = st.session_state.sliding_door_count * FIYATLAR['sliding_glass_door_piece']
            if st.session_state.sliding_door_count > 0:
                costs.append({'Item': f"Sliding Glass Door ({st.session_state.sliding_door_size})", 'Quantity': st.session_state.sliding_door_count, 'Unit Price (€)': FIYATLAR['sliding_glass_door_piece'], 'Total (€)': sliding_door_cost})

            wc_window_cost = st.session_state.wc_window_count * FIYATLAR['wc_window_piece']
            if st.session_state.wc_window_count > 0:
                costs.append({'Item': f"WC Window ({st.session_state.wc_window_size})", 'Quantity': st.session_state.wc_window_count, 'Unit Price (€)': FIYATLAR['wc_window_piece'], 'Total (€)': wc_window_cost})

            wc_sliding_door_cost = st.session_state.wc_sliding_door_count * FIYATLAR['wc_sliding_door_piece']
            if st.session_state.wc_sliding_door_count > 0:
                costs.append({'Item': f"WC Sliding Door ({st.session_state.wc_sliding_door_size})", 'Quantity': st.session_state.wc_sliding_door_count, 'Unit Price (€)': FIYATLAR['wc_sliding_door_piece'], 'Total (€)': wc_sliding_door_cost})
            
            door_cost = st.session_state.door_count * FIYATLAR['door_piece']
            costs.append({'Item': f"Door ({st.session_state.door_size})", 'Quantity': st.session_state.door_count, 'Unit Price (€)': FIYATLAR['door_piece'], 'Total (€)': door_cost})
            
            total_doors_windows = st.session_state.window_count + st.session_state.sliding_door_count + st.session_state.wc_window_count + st.session_state.wc_sliding_door_count + st.session_state.door_count
            door_window_assembly_cost = total_doors_windows * FIYATLAR['door_window_assembly_labor_piece']
            costs.append({'Item': 'Door/Window Assembly Labor', 'Quantity': f"{total_doors_windows} adet", 'Unit Price (€)': FIYATLAR['door_window_assembly_labor_piece'], 'Total (€)': door_window_assembly_cost})

            # 5. Mutfak ve Banyo Tesisatları
            kitchen_cost_calc = 0.0
            kitchen_type_display_en_gr = ""
            kitchen_type_display_tr = ""
            kitchen_included_in_calc = False

            if st.session_state.kitchen_choice == 'Standard Kitchen':
                kitchen_cost_calc = FIYATLAR['kitchen_installation_standard_piece']
                kitchen_type_display_en_gr = "Yes (Standard)"
                kitchen_type_display_tr = "Var (Standart)"
                kitchen_included_in_calc = True
                costs.append({'Item': 'Standard Kitchen Installation', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['kitchen_installation_standard_piece'], 'Total (€)': kitchen_cost_calc})
            elif st.session_state.kitchen_choice == 'Special Design Kitchen':
                kitchen_cost_calc = FIYATLAR['kitchen_installation_special_piece']
                kitchen_type_display_en_gr = "Yes (Special Design)"
                kitchen_type_display_tr = "Var (Özel Tasarım)"
                kitchen_included_in_calc = True
                costs.append({'Item': 'Special Design Kitchen Installation', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['kitchen_installation_special_piece'], 'Total (€)': kitchen_cost_calc})
            else:
                kitchen_type_display_en_gr = "No"
                kitchen_type_display_tr = "Yok"

            if st.session_state.shower_wc:
                shower_wc_cost = FIYATLAR['shower_wc_installation_piece']
                costs.append({'Item': 'Shower/WC Installation', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['shower_wc_installation_piece'], 'Total (€)': shower_wc_cost})
                if st.session_state.wc_ceramic and st.session_state.wc_ceramic_area > 0:
                    wc_ceramic_cost = st.session_state.wc_ceramic_area * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                    costs.append({'Item': 'WC Ceramic Tiles', 'Quantity': f"{st.session_state.wc_ceramic_area:.2f} m²", 'Unit Price (€)': FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'], 'Total (€)': wc_ceramic_cost})

            if st.session_state.electrical:
                electrical_cost = floor_area * FIYATLAR['electrical_per_m2']
                costs.append({'Item': 'Electrical Installation', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['electrical_per_m2'], 'Total (€)': electrical_cost})

            if st.session_state.plumbing:
                plumbing_cost = floor_area * FIYATLAR['plumbing_per_m2']
                costs.append({'Item': 'Plumbing Installation', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['plumbing_per_m2'], 'Total (€)': plumbing_cost})

            if st.session_state.transportation:
                costs.append({'Item': 'Transportation', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['transportation'], 'Total (€)': FIYATLAR['transportation']})

            if st.session_state.heating:
                heating_cost = floor_area * FIYATLAR['floor_heating_m2']
                costs.append({'Item': 'Floor Heating System', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['floor_heating_m2'], 'Total (€)': heating_cost})

            solar_cost = 0.0 # Varsayılan olarak 0
            if st.session_state.solar:
                solar_cost = st.session_state.solar_kw * FIYATLAR['solar_per_kw']
                costs.append({'Item': f'Solar Energy System ({st.session_state.solar_kw} kW)', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['solar_per_kw'], 'Total (€)': solar_cost})

            if st.session_state.wheeled_trailer:
                costs.append({'Item': 'Wheeled Trailer', 'Quantity': '1', 'Unit Price (€)': st.session_state.wheeled_trailer_price, 'Total (€)': st.session_state.wheeled_trailer_price})

            # Aether Living Paketlerine Özel Maliyetler
            # Bu bölüm, st.session_state'teki aktif package_choice ve kullanıcı seçimlerine göre maliyetleri ekler.
            if st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
                # Standard paketteki genel maliyetler zaten yukarıda işleniyor
                pass
            elif st.session_state.aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
                # Premium pakete özel eklemeler (UI'da seçiliyse eklenir)
                if st.session_state.bedroom_set_option:
                    costs.append({'Item': 'Bedroom Set', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['bedroom_set_total_price'], 'Total (€)': FIYATLAR['bedroom_set_total_price']})
                if st.session_state.brushed_granite_countertops_option and st.session_state.brushed_granite_countertops_m2_val > 0:
                    granite_cost = st.session_state.brushed_granite_countertops_m2_val * FIYATLAR['brushed_grey_granite_countertops_price_m2_avg']
                    costs.append({'Item': 'Brushed Granite Countertops', 'Quantity': f"{st.session_state.brushed_granite_countertops_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'], 'Total (€)': granite_cost})
                if st.session_state.terrace_laminated_wood_flooring_option and st.session_state.terrace_laminated_wood_flooring_m2_val > 0:
                    terrace_laminated_cost = st.session_state.terrace_laminated_wood_flooring_m2_val * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2']
                    costs.append({'Item': 'Terrace Laminated Wood Flooring', 'Quantity': f"{st.session_state.terrace_laminated_wood_flooring_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_laminated_cost})

            elif st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                # Elite pakete özel eklemeler (UI'da seçiliyse eklenir)
                if st.session_state.exterior_cladding_m2_option and st.session_state.exterior_cladding_m2_val > 0:
                    cladding_material_cost = st.session_state.exterior_cladding_m2_val * (FIYATLAR['gypsum_board_blue_per_unit_price'] / GYPSUM_BOARD_UNIT_AREA_M2)
                    cladding_labor_cost = st.session_state.exterior_cladding_m2_val * FIYATLAR['exterior_cladding_labor_price_per_m2']
                    costs.append({'Item': 'Exterior Cladding Material (Knauf Aquapanel)', 'Quantity': f"{st.session_state.exterior_cladding_m2_val:.2f} m²", 'Unit Price (€)': (FIYATLAR['gypsum_board_blue_per_unit_price'] / GYPSUM_BOARD_UNIT_AREA_M2), 'Total (€)': cladding_material_cost})
                    costs.append({'Item': 'Exterior Cladding Labor', 'Quantity': f"{st.session_state.exterior_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_labor_price_per_m2'], 'Total (€)': cladding_labor_cost})
                
                if st.session_state.concrete_panel_floor_option and st.session_state.concrete_panel_floor_m2_val > 0:
                    concrete_panel_cost = st.session_state.concrete_panel_floor_m2_val * FIYATLAR['concrete_panel_floor_price_per_m2']
                    costs.append({'Item': 'Concrete Panel Floor', 'Quantity': f"{st.session_state.concrete_panel_floor_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})
                
                if st.session_state.premium_faucets_option:
                    costs.append({'Item': 'Premium Faucets', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['premium_faucets_total_price'], 'Total (€)': FIYATLAR['premium_faucets_total_price']})
                if st.session_state.integrated_fridge_option:
                    costs.append({'Item': 'Integrated Refrigerator', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['white_goods_total_price'], 'Total (€)': FIYATLAR['white_goods_total_price']})
                if st.session_state.designer_furniture_option:
                    costs.append({'Item': 'Designer Furniture', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['designer_furniture_total_price'], 'Total (€)': FIYATLAR['designer_furniture_total_price']})
                if st.session_state.italian_sofa_option:
                    costs.append({'Item': 'Italian Sofa', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['italian_sofa_total_price'], 'Total (€)': FIYATLAR['italian_sofa_total_price']})
                if st.session_state.inclass_chairs_option and st.session_state.inclass_chairs_count > 0:
                    chairs_cost = st.session_state.inclass_chairs_count * FIYATLAR['inclass_chairs_unit_price']
                    costs.append({'Item': 'Inclass Chairs', 'Quantity': f"{st.session_state.inclass_chairs_count} pcs", 'Unit Price (€)': FIYATLAR['inclass_chairs_unit_price'], 'Total (€)': chairs_cost})
                if st.session_state.smart_home_systems_option:
                    costs.append({'Item': 'Smart Home Systems', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['smart_home_systems_total_price'], 'Total (€)': FIYATLAR['smart_home_systems_total_price']})
                if st.session_state.security_camera_option:
                    costs.append({'Item': 'Security Camera System', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['security_camera_total_price'], 'Total (€)': FIYATLAR['security_camera_total_price']})
                if st.session_state.white_goods_fridge_tv_option:
                    costs.append({'Item': 'White Goods (Fridge/TV)', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['white_goods_total_price'], 'Total (€)': FIYATLAR['white_goods_total_price']})
                if st.session_state.sofa_option:
                    costs.append({'Item': 'Sofa', 'Quantity': '1', 'Unit Price (€)': FIYATLAR['sofa_total_price'], 'Total (€)': FIYATLAR['sofa_total_price']})
                if st.session_state.exterior_wood_cladding_m2_option and st.session_state.exterior_wood_cladding_m2_val > 0:
                    wood_cladding_cost = st.session_state.exterior_wood_cladding_m2_val * FIYATLAR['exterior_wood_cladding_m2_price']
                    costs.append({'Item': 'Exterior Wood Cladding (Lambiri)', 'Quantity': f"{st.session_state.exterior_wood_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'], 'Total (€)': wood_cladding_cost})
                if st.session_state.porcelain_tiles_option and st.session_state.porcelain_tiles_m2_val > 0:
                    porcelain_tiles_cost = st.session_state.porcelain_tiles_m2_val * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                    costs.append({'Item': 'Porcelain Tiles', 'Quantity': f"{st.session_state.porcelain_tiles_m2_val:.2f} m²", 'Unit Price (€)': (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']), 'Total (€)': porcelain_tiles_cost})
                
            # Finansal Hesaplamalar
            material_subtotal = sum(item['Total (€)'] for item in costs if 'Total (€)' in item)
            waste_cost = calculate_rounded_up_cost(material_subtotal * FIRE_RATE)
            total_cost_no_profit = material_subtotal + waste_cost # Karsız toplam maliyet
            profit_amount = calculate_rounded_up_cost(total_cost_no_profit * st.session_state.profit_rate[1])
            
            vat_base = total_cost_no_profit + profit_amount
            vat_amount = calculate_rounded_up_cost(vat_base * VAT_RATE)
            final_sales_price = calculate_rounded_up_cost(vat_base + vat_amount)

            # Proje detayları (raporlar için)
            project_details_result = {
                'width': width, 'length': length, 'height': height, 'area': floor_area,
                'structure_type': st.session_state.structure_type,
                'plasterboard_interior': st.session_state.plasterboard_interior_option,
                'plasterboard_all': st.session_state.plasterboard_all_option,
                'osb_inner_wall': st.session_state.osb_inner_wall_option,
                'insulation_floor': st.session_state.insulation_floor,
                'insulation_wall': st.session_state.insulation_wall,
                'window_count': st.session_state.window_count, 'window_size_val': st.session_state.window_size,
                'window_door_color': st.session_state.window_door_color,
                'sliding_door_count': st.session_state.sliding_door_count, 'sliding_door_size_val': st.session_state.sliding_door_size,
                'wc_window_count': st.session_state.wc_window_count, 'wc_window_size_val': st.session_state.wc_window_size,
                'wc_sliding_door_count': st.session_state.wc_sliding_door_count, 'wc_sliding_door_size_val': st.session_state.wc_sliding_door_size,
                'door_count': st.session_state.door_count, 'door_size_val': st.session_state.door_size,
                'kitchen_choice': st.session_state.kitchen_choice,
                'kitchen_type_display_en_gr': kitchen_type_display_en_gr, # Hesaplamadan gelen değer
                'kitchen_type_display_tr': kitchen_type_display_tr, # Hesaplamadan gelen değer
                'kitchen_included_in_calc': kitchen_included_in_calc, # Hesaplamadan gelen değer
                'shower_wc': st.session_state.shower_wc,
                'wc_ceramic': st.session_state.wc_ceramic, 'wc_ceramic_area': st.session_state.wc_ceramic_area,
                'electrical': st.session_state.electrical, 'plumbing': st.session_state.plumbing,
                'transportation': st.session_state.transportation, 'heating': st.session_state.heating,
                'solar': st.session_state.solar, 'solar_kw': st.session_state.solar_kw, 'solar_price': solar_cost, # Solar fiyatı burada hesaplanan değer
                'wheeled_trailer': st.session_state.wheeled_trailer,
                'wheeled_trailer_price': st.session_state.wheeled_trailer_price,
                'vat_rate': VAT_RATE, 'profit_rate': st.session_state.profit_rate[1],
                'room_configuration': st.session_state.room_config,
                'delivery_duration_business_days': math.ceil((floor_area / 27.0) * 35), # Hesaplanan teslimat süresi
                'welding_labor_type': st.session_state.welding_type,
                'facade_sandwich_panel_included': st.session_state.facade_sandwich_panel_option,
                'floor_covering_type': st.session_state.floor_covering,
                'skirting_length_val': st.session_state.skirting_length_val,
                'laminate_flooring_m2_val': st.session_state.laminate_flooring_m2_val,
                'under_parquet_mat_m2_val': st.session_state.under_parquet_mat_m2_val,
                'osb2_18mm_count_val': st.session_state.osb2_18mm_count_val,
                'galvanized_sheet_m2_val': st.session_state.galvanized_sheet_m2_val,
                'insulation_material_type': st.session_state.insulation_material_type,
                # Aether Living detayları (hesaplamalar için)
                'aether_package_choice': st.session_state.aether_package_choice,
                'exterior_cladding_m2_option': st.session_state.exterior_cladding_m2_option,
                'exterior_cladding_m2_val': st.session_state.exterior_cladding_m2_val,
                'exterior_wood_cladding_m2_option': st.session_state.exterior_wood_cladding_m2_option,
                'exterior_wood_cladding_m2_val': st.session_state.exterior_wood_cladding_m2_val,
                'porcelain_tiles_option': st.session_state.porcelain_tiles_option,
                'porcelain_tiles_m2_val': st.session_state.porcelain_tiles_m2_val,
                'concrete_panel_floor_option': st.session_state.concrete_panel_floor_option,
                'concrete_panel_floor_m2_val': st.session_state.concrete_panel_floor_m2_val,
                'bedroom_set_option': st.session_state.bedroom_set_option,
                'sofa_option': st.session_state.sofa_option,
                'smart_home_systems_option': st.session_state.smart_home_systems_option,
                'security_camera_option': st.session_state.security_camera_option,
                'white_goods_fridge_tv_option': st.session_state.white_goods_fridge_tv_option,
                'premium_faucets_option': st.session_state.premium_faucets_option,
                'integrated_fridge_option': st.session_state.integrated_fridge_option,
                'designer_furniture_option': st.session_state.designer_furniture_option,
                'italian_sofa_option': st.session_state.italian_sofa_option,
                'inclass_chairs_option': st.session_state.inclass_chairs_option,
                'inclass_chairs_count': st.session_state.inclass_chairs_count,
                'brushed_granite_countertops_option': st.session_state.brushed_granite_countertops_option,
                'brushed_granite_countertops_m2_val': st.session_state.brushed_granite_countertops_m2_val,
                'terrace_laminated_wood_flooring_option': st.session_state.terrace_laminated_wood_flooring_option,
                'terrace_laminated_wood_flooring_m2_val': st.session_state.terrace_laminated_wood_flooring_m2_val,
                # Profil adetleri de project_details'e eklendi
                'profile_100x100_count_val': st.session_state.profile_100x100_count,
                'profile_100x50_count_val': st.session_state.profile_100x50_count,
                'profile_40x60_count_val': st.session_state.profile_40x60_count,
                'profile_50x50_count_val': st.session_state.profile_50x50_count,
                'profile_120x60x5mm_count_val': st.session_state.profile_120x60x5mm_count,
                'profile_HEA160_count_val': st.session_state.profile_HEA160_count,
            }

            # Müşteri bilgileri (raporlar için)
            customer_info_result = {
                'name': st.session_state.customer_name.strip() or "GENEL",
                'company': st.session_state.customer_company.strip() or "",
                'address': st.session_state.customer_address.strip() or "",
                'city': st.session_state.customer_city.strip() or "",
                'phone': st.session_state.customer_phone.strip() or "",
                'email': st.session_state.customer_email.strip() or "",
                'id_no': st.session_state.customer_id_no.strip() or ""
            }

            # --- Streamlit'te Sonuçları Göster ---
            st.subheader("Hesaplama Sonuçları")
            st.dataframe(pd.DataFrame(financial_summary_data).set_index('Item'), use_container_width=True) # Zaten formatlı veri
            st.dataframe(pd.DataFrame(costs).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            if project_details_result['structure_type'] == 'Light Steel': # Sadece Hafif Çelik ise profil analizi göster
                st.subheader("Çelik Profil Detaylı Analizi")
                st.dataframe(pd.DataFrame(profile_analysis_details).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            # --- PDF Oluşturma ve İndirme Bağlantıları ---
            st.markdown("---")
            st.subheader("PDF Çıktıları")

            logo_data_b64 = get_company_logo_base64(COMPANY_INFO['logo_url'])

            col_pdf1, col_pdf2, col_pdf3 = st.columns(3)

            with col_pdf1:
                # Dahili Maliyet Raporu PDF
                internal_pdf_buffer = create_internal_cost_report_pdf(
                    pd.DataFrame(costs),
                    pd.DataFrame(financial_summary_data),
                    pd.DataFrame(profile_analysis_details),
                    project_details_result,
                    customer_info_result,
                    logo_data_b64
                )
                st.download_button(
                    label="Dahili Maliyet Raporu İndir (TR)",
                    data=internal_pdf_buffer, # buffer'ın kendisi de kabul ediliyor
                    file_name=f"Internal_Cost_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )

            with col_pdf2:
                # Müşteri Teklifi PDF (Dile göre)
                if st.session_state.pdf_language[1] == 'en_gr':
                    customer_proposal_pdf_buffer = create_customer_proposal_pdf(
                        final_sales_price,
                        solar_cost,
                        final_sales_price, # Total price here should be final_sales_price
                        project_details_result,
                        st.session_state.customer_notes,
                        customer_info_result,
                        logo_data_b64
                    )
                    st.download_button(
                        label="Müşteri Teklifi İndir (EN/GR)",
                        data=customer_proposal_pdf_buffer,
                        file_name=f"Customer_Proposal_EN_GR_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                else: # Turkish
                    customer_proposal_pdf_buffer = create_customer_proposal_pdf_tr(
                        final_sales_price,
                        solar_cost,
                        final_sales_price, # Total price here should be final_sales_price
                        project_details_result,
                        st.session_state.customer_notes,
                        customer_info_result,
                        logo_data_b64
                    )
                    st.download_button(
                        label="Müşteri Teklifi İndir (TR)",
                        data=customer_proposal_pdf_buffer,
                        file_name=f"Customer_Proposal_TR_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
            with col_pdf3:
                # Satış Sözleşmesi PDF (İngilizce olması isteniyor)
                sales_contract_pdf_buffer = create_sales_contract_pdf(
                    customer_info_result,
                    final_sales_price, # Evin fiyatı
                    solar_cost, # Solar fiyatı
                    project_details_result,
                    COMPANY_INFO,
                    logo_data_b64
                )
                st.download_button(
                    label="Satış Sözleşmesi İndir (EN)", # Başlıkta EN belirtildi
                    data=sales_contract_pdf_buffer,
                    file_name=f"Sales_Contract_EN_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            st.exception(e) # Detaylı traceback göster

# Uygulamanın ana giriş noktası
if __name__ == "__main__":
    run_streamlit_app()
