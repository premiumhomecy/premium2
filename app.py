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

# ==============================================================================
# GÖRÜNMEZ KARAKTER TEMİZLEME VE FONT AYARLARI
# ==============================================================================

# --- Görünmez Karakter Temizleme Fonksiyonu ---
def clean_invisible_chars(text):
    """Metindeki görünmez karakterleri temizler (U+00A0, U+200B vb. dahil)."""
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
    st.warning(f"Font yükleme hatası: {e}. PDF'lerde 'Helvetica' fontu kullanılacak.")
    MAIN_FONT = "Helvetica"

# ==============================================================================
# ŞİRKET BİLGİLERİ VE FİYAT TANIMLARI
# ==============================================================================

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
    "account_number": "357042392044", 
    "currency_type": "EURO",
    "swift_bic": "BCYPCY2N",
    "logo_url": LOGO_URL 
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
    "sandwich_panel_m2": 22.00, # Standart Sandviç Panel m2 fiyatı (60mm EPS için)
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
    "connection_element_m2": 1.50, # Bağlantı elemanları m2 fiyatı
    "transportation": 350.00, # Nakliye fiyatı
    "floor_heating_m2": 50.00, # Yerden ısıtma m2 fiyatı
    "wc_ceramic_m2_material": 20.00, # WC Seramik malzeme m2 fiyatı
    "wc_ceramic_m2_labor": 20.00,     # WC Seramik işçilik m2 fiyatı
    "electrical_per_m2": 25.00, # Elektrik tesisatı m2 fiyatı
    "plumbing_per_m2": 25.00, # Sıhhi tesisat m2 fiyatı
    "osb_piece": 12.00, # OSB levha fiyatı (duvar için)
    "insulation_per_m2": 5.00, # Genel Yalıtım m2 fiyatı (5cm EPS gibi)
    "welding_labor_m2_standard": 160.00, # Standart kaynak işçiliği m2 fiyatı
    "welding_labor_m2_trmontaj": 20.00, # TR montaj kaynak işçiliği m2 fiyatı
    "panel_assembly_labor_m2": 5.00, # Panel montaj işçiliği m2 fiyatı
    "plasterboard_material_m2": 20.00, # Alçıpan genel malzeme m2 fiyatı (Guardex için kullanılabilir)
    "plasterboard_labor_m2_avg": 80.00, # Alçıpan işçilik m2 fiyatı
    "plywood_flooring_labor_m2": 11.11, # Kontraplak döşeme işçiliği m2 fiyatı
    "door_window_assembly_labor_piece": 10.00, # Kapı/pencere montaj işçiliği adet fiyatı
    "solar_per_kw": 1250.00, # Solar enerji kW başına fiyat

    # Yeni Zemin Sistemi Malzemeleri Fiyatları (Premium/Elite)
    "skirting_meter_price": 2.00, # Süpürgelik metre fiyatı
    "laminate_flooring_m2_price": 15.00, # Laminat parke m2 fiyatı
    "under_parquet_mat_m2_price": 3.00, # Parke altı şilte m2 fiyatı
    "osb2_18mm_piece_price": 30.00, # OSB2 18mm levha adet fiyatı
    "galvanized_sheet_m2_price": 10.00, # Galvanizli sac m2 fiyatı

    # Aether Living Ekipman/Yükseltme Fiyatları
    "smart_home_systems_total_price": 350.00,
    "white_goods_total_price": 800.00, # Buzdolabı ve TV dahil
    "sofa_total_price": 400.00,
    "security_camera_total_price": 650.00,
    "exterior_cladding_labor_price_per_m2": 150.00, # Dış cephe kaplama işçiliği M2 bazlı (Knauf Aquapanel, vb.)
    "bedroom_set_total_price": 800.00,
    "terrace_laminated_wood_flooring_price_per_m2": 40.00, # İşlenmiş çam zemin kaplama (teras) m2 fiyatı
    "concrete_panel_floor_price_per_m2": 50.00, # Beton panel zemin m2 fiyatı
    "premium_faucets_total_price": 200.00,
    "designer_furniture_total_price": 1000.00,
    "italian_sofa_total_price": 800.00,
    "inclass_chairs_unit_price": 150.00,
    "exterior_wood_cladding_m2_price": 150.00, # Dış cephe ahşap kaplama (işçilik ve malzeme dahil m2)
    "brushed_grey_granite_countertops_price_m2_avg": 425.00, # Fırçalanmış gri granit tezgah m2 fiyatı
    "100mm_eps_isothermal_panel_unit_price": 27.00, # 100mm Yüksek Performanslı Panellerin m2 fiyatı

    # Alçıpan modellerinin birim fiyatları (Ivan'dan)
    "gypsum_board_white_per_unit_price": 8.65, # Beyaz alçıpan adet fiyatı
    "gypsum_board_green_per_unit_price": 11.95, # Yeşil alçıpan adet fiyatı
    "gypsum_board_blue_per_unit_price": 22.00, # Mavi alçıpan (Knauf Aquapanel) adet fiyatı
    
    # Diğer malzeme birim fiyatları (Ivan'dan)
    "otb_stone_wool_price": 19.80, # OTB taşyünü fiyatı
    "glass_wool_5cm_packet_price": 19.68, # Cam yünü 5cm paket fiyatı (10m2 için)
    "tn25_screws_price_per_unit": 5.58, # TN25 vidalar adet fiyatı
    "cdx400_material_price": 3.40, # CDX400 malzeme adet fiyatı
    "ud_material_price": 1.59, # UD malzeme adet fiyatı
    "oc50_material_price": 2.20, # OC50 malzeme adet fiyatı
    "oc100_material_price": 3.96, # OC100 malzeme adet fiyatı
    "ch100_material_price": 3.55, # CH100 malzeme adet fiyatı

    # Material Info Keys (raporlama için bilgi metinleri)
    "steel_skeleton_info": "Metal İskelet",
    "protective_automotive_paint_info": "Koruyucu Otomotiv Boyası",
    "insulation_info_general": "Genel Yalıtım (EPS/Poliüretan)",
    "60mm_eps_sandwich_panel_info": "Standart 60mm EPS veya Poliüretan Sandviç Paneller (beyaz)",
    "100mm_eps_isothermal_panel_info": "Yüksek Performanslı 100mm EPS veya Poliüretan İzotermik Paneller",
    "galvanized_sheet_info": "Galvanizli Sac (Zemin)",
    "plywood_osb_floor_panel_info": "Kontraplak/OSB Zemin Paneli",
    "12mm_laminate_parquet_info": "12mm Laminat Parke",
    "induction_hob_info": "İndüksiyonlu Ocak",
    "electric_faucet_info": "Elektrikli Batarya",
    "kitchen_sink_info": "Mutfak Evyesi",
    "fully_functional_bathroom_fixtures_info": "Tam Fonksiyonel Banyo Armatürleri",
    "kitchen_bathroom_countertops_info": "Mutfak ve Banyo Tezgahları",
    "treated_pine_floor_info": "İşlenmiş Çam Zemin Kaplaması (Teras)",
    "porcelain_tiles_info": "Porselen Fayans",
    "concrete_panel_floor_info": "Beton Panel Zemin",
    "premium_faucets_info": "Premium Bataryalar (örn. Hansgrohe)",
    "integrated_refrigerator_info": "Entegre Buzdolabı",
    "integrated_custom_furniture_info": "Entegre Özel Tasarım Mobilyalar (yüksek kaliteli MDF/lake)",
    "italian_sofa_info": "İtalyan Kanepe",
    "inclass_chairs_info": "Inclass Sandalyeler",
    "smart_home_systems_info": "Akıllı Ev Sistemleri",
    "advanced_security_camera_pre_installation_info": "Gelişmiş Güvenlik Kamerası Ön Kurulumu",
    "exterior_wood_cladding_lambiri_info": "Dış Cephe Ahşap Kaplama - Lambiri",
    "brushed_grey_granite_countertops_info": "Fırçalanmış Gri Kale Granit Mutfak/Banyo Tezgahları",
    
    "gypsum_board_white_info": "İç Alçıpan (Beyaz)",
    "gypsum_board_green_info": "Yeşil Alçıpan (Banyo/WC)",
    "gypsum_board_blue_info": "Mavi Alçıpan (Dış Cephe / Knauf Aquapanel)",
    "knauf_aquapanel_gypsum_board_info": "Knauf Aquapanel Alçıpan",
    "exterior_cladding_labor_info": "Dış Cephe Kaplama İşçiliği",
    "exterior_cladding_material_info": "Dış Cephe Kaplama Malzemesi (Knauf Aquapanel / Mavi Alçıpan)",
    "eps_styrofoam_info": "EPS STYROFOAM",
    "knauf_mineralplus_insulation_info": "Knauf MineralPlus İzolasyon (Taşyünü)",
    "knauf_guardex_gypsum_board_info": "Knauf Guardex Alçıpan",
    "satin_plaster_paint_info": "Saten Sıva ve Boya",
    "otb_stone_wool_info_report": "OTB (Taşyünü)",
    "glass_wool_5cm_packet_info_report": "Cam Yünü 5cm Paket",
    "tn25_screws_info_report": "TN25 Vidalar",
    "cdx400_material_info_report": "CDX400 Malzeme",
    "ud_material_info_report": "UD Malzeme",
    "oc50_material_info_report": "OC50 Malzeme",
    "oc100_material_info_report": "OC100 Malzeme",
    "ch100_material_info_report": "ch100 Malzeme",

    "electrical_cable_info": "Elektrik Kabloları (3x2.5 mm², 3x1.5 mm²)",
    "electrical_conduits_info": "Kablolama için Spiral Borular ve Kanallar",
    "electrical_junction_boxes_info": "Buatlar",
    "electrical_distribution_board_info": "Sigorta Kutusu (Dağıtım Panosu)",
    "electrical_circuit_breakers_info": "Sigortalar & Kaçak Akım Rölesi",
    "electrical_sockets_switches_info": "Prizler ve Anahtarlar",
    "electrical_lighting_fixtures_info": "İç Aydınlatma Armatürleri (LED Spots / Tavan Lambası)",
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
    "wc_shower_unit_info": "Duş Ünitesi (Duş Başlığı ve Bataryası)",

    "kitchen_mdf_info": "Parlak Beyaz Renk MDF Malzeme",
    "kitchen_cabinets_info": "Özel Üretim Mutfak Dolapları (özel ölçülerde)",
    "kitchen_countertop_info": "Tezgah (Laminat veya belirtilen eşdeğeri)",
    "kitchen_sink_faucet_info": "Evye ve Batarya",
}

# Sabit Oranlar
FIRE_RATE = 0.05
VAT_RATE = 0.19
MONTHLY_ACCOUNTING_EXPENSES = 180.00
MONTHLY_OFFICE_RENT = 280.00
ANNUAL_INCOME_TAX_RATE = 0.235
OSB_PANEL_AREA_M2 = 1.22 * 2.44
GYPSUM_BOARD_UNIT_AREA_M2 = 2.88 # 1.2m x 2.4m standart alçıpan levha alanı
GLASS_WOOL_M2_PER_PACKET = 10.0 # Cam yünü paketi 10m2 alan için

# Döviz Kurları (Sabit)
EUR_TO_TL_RATE = 47.5
USD_TO_TL_RATE = 40.0

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
• Countertop (Laminat veya belirtilen eşdeğeri)
• Sink and Faucet
Note: Final material selection and detailed list will be provided upon design approval.
"""
KITCHEN_MATERIALS_GR = """
Τυπικά υλικά περιλαμβάνουν:
• Υλικό MDF Γυαλιστερό Λευκό Χρώμα
• Ειδικές Κατασκευές Ντουλαπιών Κουζίνας (προσαρμοσμένες διαστάσεις)
• Πάγκος (Laminat ή καθορισμένο ισοδύναμο)
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

# PDF özellikleri açıklamaları (İsteğe Bağlı Özellikler kaldırıldı ve format düzeltildi)
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

# ==============================================================================
# YARDIMCI VE HESAPLAMA FONKSİYONLARI
# ==============================================================================

def calculate_area(width, length, height):
    """Calculates floor, wall, and roof areas based on dimensions."""
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Formats a monetary value as Euro currency."""
    return f"€{value:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',') # Euro formatı için nokta ve virgül değişimi

def calculate_rounded_up_cost(value):
    """Maliyeti yukarı yuvarlar"""
    return math.ceil(value * 100) / 100.0

def calculate_recommended_profiles(floor_area):
    """Proje alanına göre önerilen çelik profil adetlerini hesaplar (kaba tahmin)."""
    # Bu faktörler örnek içindir ve gerçek mühendislik tasarımına göre ayarlanabilir.
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

    costs = [] # Detaylı maliyet kalemlerini tutacak liste
    profile_analysis_details = [] # Çelik profil analiz detaylarını tutacak liste
    
    # Aether Living Paket maliyetlerini toplamak için
    aether_package_total_cost = 0.0 
    
    # --- Yapısal Maliyetler ---
    if project_inputs['structure_type'] == 'Light Steel':
        # Kullanıcı girdisine göre çelik profil maliyetleri
        profile_types_and_counts = {
            "100x100x3": project_inputs['profile_100x100_count_val'],
            "100x50x3": project_inputs['profile_100x50_count_val'],
            "40x60x2": project_inputs['profile_40x60_count_val'],
            "50x50x2": project_inputs['profile_50x50_count_val'],
            "120x60x5mm": project_inputs['profile_120x60x5mm_count_val'],
            "HEA160": project_inputs['profile_HEA160_count_val'],
        }
        
        for p_type, p_count in profile_types_and_counts.items():
            if p_count > 0:
                fiytlar_key = f"steel_profile_{p_type.replace('x', '_').lower()}" 
                cost_per_piece = FIYATLAR.get(fiytlar_key, 0.0)
                total_profile_cost = p_count * cost_per_piece
                costs.append({
                    'Item': f"Çelik Profil ({p_type})",
                    'Quantity': f"{p_count} adet",
                    'Unit Price (€)': cost_per_piece,
                    'Total (€)': calculate_rounded_up_cost(total_profile_cost)
                })
                aether_package_total_cost += calculate_rounded_up_cost(total_profile_cost) # Pakete dahilse buraya eklenir
        
        # Hafif Çelik için Kaynak İşçiliği
        welding_cost = wall_area * FIYATLAR['welding_labor_m2_trmontaj']
        costs.append({
            'Item': 'Çelik Kaynak İşçiliği (Hafif Çelik)',
            'Quantity': f"{wall_area:.2f} m²",
            'Unit Price (€)': FIYATLAR['welding_labor_m2_trmontaj'],
            'Total (€)': calculate_rounded_up_cost(welding_cost)
        })
        aether_package_total_cost += calculate_rounded_up_cost(welding_cost) # Pakete dahilse
        

    else: # Ağır Çelik
        heavy_steel_cost = floor_area * FIYATLAR["heavy_steel_m2"]
        costs.append({
            'Item': FIYATLAR['steel_skeleton_info'] + ' (Ağır Çelik)',
            'Quantity': f"{floor_area:.2f} m²",
            'Unit Price (€)': FIYATLAR['heavy_steel_m2'],
            'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)
        })
        aether_package_total_cost += calculate_rounded_up_cost(heavy_steel_cost)

        welding_cost = floor_area * FIYATLAR['welding_labor_m2_standard']
        costs.append({
            'Item': 'Çelik Kaynak İşçiliği (Ağır Çelik)',
            'Quantity': f"{floor_area:.2f} m²",
            'Unit Price (€)': FIYATLAR['welding_labor_m2_standard'],
            'Total (€)': calculate_rounded_up_cost(welding_cost)
        })
        aether_package_total_cost += calculate_rounded_up_cost(welding_cost)
    
    # --- Dış Cephe ve Çatı Kaplaması (Sandviç Panel veya Özel) ---
    # Eğer özel dış kaplama seçilmemişse standart sandviç panel eklenir
    if not project_inputs['exterior_cladding_m2_option_val'] and not project_inputs['exterior_wood_cladding_m2_option_val']:
        sandwich_panel_total_area = wall_area + roof_area
        sandwich_panel_cost = sandwich_panel_total_area * FIYATLAR["sandwich_panel_m2"]
        costs.append({
            'Item': FIYATLAR['60mm_eps_sandwich_panel_info'],
            'Quantity': f"{sandwich_panel_total_area:.2f} m²",
            'Unit Price (€)': FIYATLAR["sandwich_panel_m2"],
            'Total (€)': calculate_rounded_up_cost(sandwich_panel_cost)
        })
        aether_package_total_cost += calculate_rounded_up_cost(sandwich_panel_cost)

        panel_assembly_cost = sandwich_panel_total_area * FIYATLAR["panel_assembly_labor_m2"]
        costs.append({
            'Item': 'Panel Montaj İşçiliği',
            'Quantity': f"{sandwich_panel_total_area:.2f} m²",
            'Unit Price (€)': FIYATLAR["panel_assembly_labor_m2"],
            'Total (€)': calculate_rounded_up_cost(panel_assembly_cost)
        })
        aether_package_total_cost += calculate_rounded_up_cost(panel_assembly_cost)

    # --- Özel Dış Cephe Kaplamaları (seçildiyse) ---
    if project_inputs['exterior_cladding_m2_option_val'] and project_inputs['exterior_cladding_m2_val'] > 0:
        # Knauf Aquapanel / Mavi Alçıpan malzeme maliyeti (adet fiyatından m2'ye çevirme)
        mavi_alcipan_m2_price_converted = FIYATLAR['gypsum_board_blue_per_unit_price'] / GYPSUM_BOARD_UNIT_AREA_M2
        mavi_alcipan_material_cost = calculate_rounded_up_cost(project_inputs['exterior_cladding_m2_val'] * mavi_alcipan_m2_price_converted)
        costs.append({
            'Item': FIYATLAR['exterior_cladding_material_info'],
            'Quantity': f"{project_inputs['exterior_cladding_m2_val']:.2f} m²",
            'Unit Price (€)': mavi_alcipan_m2_price_converted,
            'Total (€)': mavi_alcipan_material_cost
        })
        aether_package_total_cost += mavi_alcipan_material_cost

        # Dış Cephe Kaplama İşçiliği maliyeti
        exterior_cladding_labor_cost = calculate_rounded_up_cost(project_inputs['exterior_cladding_m2_val'] * FIYATLAR['exterior_cladding_labor_price_per_m2'])
        costs.append({
            'Item': FIYATLAR['exterior_cladding_labor_info'],
            'Quantity': f"{project_inputs['exterior_cladding_m2_val']:.2f} m²",
            'Unit Price (€)': FIYATLAR['exterior_cladding_labor_price_per_m2'],
            'Total (€)': exterior_cladding_labor_cost
        })
        aether_package_total_cost += exterior_cladding_labor_cost
    
    if project_inputs['exterior_wood_cladding_m2_option_val'] and project_inputs['exterior_wood_cladding_m2_val'] > 0:
        wood_cladding_cost = calculate_rounded_up_cost(project_inputs['exterior_wood_cladding_m2_val'] * FIYATLAR['exterior_wood_cladding_m2_price'])
        costs.append({
            'Item': FIYATLAR['exterior_wood_cladding_lambiri_info'],
            'Quantity': f"{project_inputs['exterior_wood_cladding_m2_val']:.2f} m²",
            'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'],
            'Total (€)': wood_cladding_cost
        })
        aether_package_total_cost += wood_cladding_cost

    # --- İç Duvarlar (Alçıpan) ---
    if project_inputs['plasterboard_interior'] or project_inputs['plasterboard_all']:
        
        # İç alçıpan alanı (duvarların yarısı + tavan veya tüm duvar + tavan)
        interior_alcipan_area_for_material = 0
        if project_inputs['plasterboard_interior']:
            interior_alcipan_area_for_material = (wall_area / 2) + roof_area 
        elif project_inputs['plasterboard_all']:
            interior_alcipan_area_for_material = wall_area + roof_area

        # Yeşil Alçıpan (WC)
        green_alcipan_area = 0
        if project_inputs['wc_ceramic'] and project_inputs['wc_ceramic_area'] > 0:
            green_alcipan_area = project_inputs['wc_ceramic_area']
            green_gypsum_board_adet = math.ceil(green_alcipan_area / GYPSUM_BOARD_UNIT_AREA_M2)
            green_gypsum_board_material_cost = calculate_rounded_up_cost(green_gypsum_board_adet * FIYATLAR['gypsum_board_green_per_unit_price'])
            costs.append({
                'Item': FIYATLAR['gypsum_board_green_info'],
                'Quantity': f"{green_gypsum_board_adet} adet ({green_alcipan_area:.2f} m²)",
                'Unit Price (€)': FIYATLAR['gypsum_board_green_per_unit_price'],
                'Total (€)': green_gypsum_board_material_cost
            })
        
        # Kalan iç alçıpan alanı için Beyaz Alçıpan veya Guardex (genel alçıpan malzeme fiyatı)
        remaining_interior_alcipan_area = interior_alcipan_area_for_material - green_alcipan_area
        if remaining_interior_alcipan_area > 0:
            general_gypsum_board_adet = math.ceil(remaining_interior_alcipan_area / GYPSUM_BOARD_UNIT_AREA_M2)
            general_gypsum_board_material_cost = calculate_rounded_up_cost(general_gypsum_board_adet * FIYATLAR["plasterboard_material_m2"])
            costs.append({
                'Item': FIYATLAR['gypsum_board_white_info'] + " / " + FIYATLAR['knauf_guardex_gypsum_board_info'], # Genelleştirilmiş isim
                'Quantity': f"{general_gypsum_board_adet} adet ({remaining_interior_alcipan_area:.2f} m²)",
                'Unit Price (€)': FIYATLAR["plasterboard_material_m2"],
                'Total (€)': general_gypsum_board_material_cost
            })
        
        # Alçıpan İşçiliği (Tüm iç ve/veya dış alçıpan alanı için)
        total_alcipan_labor_area = wall_area + roof_area # İşçilik için tüm duvar ve tavan alanı baz alınır
        alcipan_labor_cost = calculate_rounded_up_cost(total_alcipan_labor_area * FIYATLAR["plasterboard_labor_m2_avg"])
        costs.append({
            'Item': 'Alçıpan İşçiliği',
            'Quantity': f'{total_alcipan_labor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"],
            'Total (€)': alcipan_labor_cost
        })

        # Alçıpan detay malzemeleri (Örnek miktarlar, gerçek projeye göre ayarlanabilir)
        costs.append({'Item': FIYATLAR['tn25_screws_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['tn25_screws_price_per_unit'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['tn25_screws_price_per_unit'] * (total_alcipan_labor_area / 10))})
        costs.append({'Item': FIYATLAR['cdx400_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['cdx400_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['cdx400_material_price'] * (total_alcipan_labor_area / 20))})
        costs.append({'Item': FIYATLAR['ud_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['ud_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['ud_material_price'] * (total_alcipan_labor_area / 5))})
        costs.append({'Item': FIYATLAR['oc50_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['oc50_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['oc50_material_price'] * (total_alcipan_area_for_labor / 15))})
        costs.append({'Item': FIYATLAR['oc100_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['oc100_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['oc100_material_price'] * (total_alcipan_area_for_labor / 25))})
        costs.append({'Item': FIYATLAR['ch100_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['ch100_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['ch100_material_price'] * (total_alcipan_area_for_labor / 25))})
        costs.append({'Item': FIYATLAR['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0}) # Saten sıva ve boya (bilgi kalemi)


    # --- Zemin Yalıtım ve Malzemeleri ---
    if project_inputs['insulation_floor']:
        if project_inputs['insulation_material_type'] == 'Taş Yünü':
            insulation_cost_specific = calculate_rounded_up_cost(floor_area * FIYATLAR["otb_stone_wool_price"]) 
            costs.append({'Item': FIYATLAR['otb_stone_wool_info_report'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["otb_stone_wool_price"], 'Total (€)': insulation_cost_specific})
        elif project_inputs['insulation_material_type'] == 'Cam Yünü':
            num_glass_wool_packets = math.ceil(floor_area / GLASS_WOOL_M2_PER_PACKET)
            insulation_cost_specific = calculate_rounded_up_cost(num_glass_wool_packets * FIYATLAR["glass_wool_5cm_packet_price"])
            costs.append({'Item': FIYATLAR['glass_wool_5cm_packet_info_report'], 'Quantity': f"{num_glass_wool_packets} paket ({floor_area:.2f} m²)", 'Unit Price (€)': FIYATLAR["glass_wool_5cm_packet_price"], 'Total (€)': insulation_cost_specific})
    
    # Duvar Yalıtımı
    if project_inputs['insulation_wall']:
        wall_insulation_cost = calculate_rounded_up_cost(wall_area * FIYATLAR["insulation_per_m2"])
        costs.append({'Item': FIYATLAR['insulation_info_general'] + ' (Duvar)', 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': wall_insulation_cost})


    # Ek Zemin Malzemeleri (Süpürgelik, Laminat, Şilte, OSB2, Galvanizli Sac)
    if project_inputs['skirting_length'] > 0:
        skirting_cost = calculate_rounded_up_cost(project_inputs['skirting_length'] * FIYATLAR['skirting_meter_price'])
        costs.append({'Item': 'Süpürgelik', 'Quantity': f"{project_inputs['skirting_length']:.2f} m", 'Unit Price (€)': FIYATLAR['skirting_meter_price'], 'Total (€)': skirting_cost})
    
    if project_inputs['laminate_flooring'] > 0:
        laminate_cost = calculate_rounded_up_cost(project_inputs['laminate_flooring'] * FIYATLAR['laminate_flooring_m2_price'])
        costs.append({'Item': 'Laminat Parke', 'Quantity': f"{project_inputs['laminate_flooring']:.2f} m²", 'Unit Price (€)': FIYATLAR['laminate_flooring_m2_price'], 'Total (€)': laminate_cost})
    
    if project_inputs['under_parquet_mat'] > 0:
        under_parquet_cost = calculate_rounded_up_cost(project_inputs['under_parquet_mat'] * FIYATLAR['under_parquet_mat_m2_price'])
        costs.append({'Item': 'Parke Altı Şilte', 'Quantity': f"{project_inputs['under_parquet_mat']:.2f} m²", 'Unit Price (€)': FIYATLAR['under_parquet_mat_m2_price'], 'Total (€)': under_parquet_cost})
    
    if project_inputs['osb2_18mm_count_val'] > 0:
        osb2_cost = calculate_rounded_up_cost(project_inputs['osb2_18mm_count_val'] * FIYATLAR['osb2_18mm_piece_price'])
        costs.append({'Item': 'OSB2 Panel', 'Quantity': f"{project_inputs['osb2_18mm_count_val']} adet", 'Unit Price (€)': FIYATLAR['osb2_18mm_piece_price'], 'Total (€)': osb2_cost})
    
    if project_inputs['galvanized_sheet'] > 0:
        galvanized_cost = calculate_rounded_up_cost(project_inputs['galvanized_sheet'] * FIYATLAR['galvanized_sheet_m2_price'])
        costs.append({'Item': 'Galvanizli Sac', 'Quantity': f"{project_inputs['galvanized_sheet']:.2f} m²", 'Unit Price (€)': FIYATLAR['galvanized_sheet_m2_price'], 'Total (€)': galvanized_cost})

    # --- Kapı ve Pencere Maliyetleri (calculate_costs_detailed içinde hesaplanacak) ---
    # Not: Bu maliyetler calculate_costs_detailed fonksiyonu içinde hesaplanıp maliyet listesine eklenir.
    # Burada sadece proje_inputs'tan değerler alınır.

    # --- Ekipman ve Tesisatlar ---
    if project_inputs['kitchen_choice'] == 'Standard Mutfak':
        kitchen_cost = FIYATLAR['kitchen_installation_standard_piece']
        costs.append({'Item': 'Standart Mutfak Kurulumu', 'Quantity': '1 adet', 'Unit Price (€)': FIYATLAR['kitchen_installation_standard_piece'], 'Total (€)': kitchen_cost})
    elif project_inputs['kitchen_choice'] == 'Special Design Mutfak':
        kitchen_cost = FIYATLAR['kitchen_installation_special_piece']
        costs.append({'Item': 'Özel Tasarım Mutfak Kurulumu', 'Quantity': '1 adet', 'Unit Price (€)': FIYATLAR['kitchen_installation_special_piece'], 'Total (€)': kitchen_cost})

    if project_inputs['shower_wc']:
        shower_wc_cost = FIYATLAR['shower_wc_installation_piece']
        costs.append({'Item': 'Duş/WC Kurulumu', 'Quantity': '1 adet', 'Unit Price (€)': FIYATLAR['shower_wc_installation_piece'], 'Total (€)': shower_wc_cost})
        if project_inputs['wc_ceramic'] and project_inputs['wc_ceramic_area'] > 0:
            wc_ceramic_total_cost = project_inputs['wc_ceramic_area'] * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
            costs.append({'Item': 'WC Seramik Malzeme ve İşçilik', 'Quantity': f"{project_inputs['wc_ceramic_area']:.2f} m²", 'Unit Price (€)': FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'], 'Total (€)': wc_ceramic_total_cost})

    if project_inputs['electrical']:
        electrical_cost = floor_area * FIYATLAR['electrical_per_m2']
        costs.append({'Item': 'Elektrik Tesisatı', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['electrical_per_m2'], 'Total (€)': electrical_cost})

    if project_inputs['plumbing']:
        plumbing_cost = floor_area * FIYATLAR['plumbing_per_m2']
        costs.append({'Item': 'Sıhhi Tesisat', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['plumbing_per_m2'], 'Total (€)': plumbing_cost})

    if project_inputs['transportation']:
        costs.append({'Item': 'Nakliye', 'Quantity': '1 sefer', 'Unit Price (€)': FIYATLAR['transportation'], 'Total (€)': FIYATLAR['transportation']})

    if project_inputs['heating']:
        heating_cost = floor_area * FIYATLAR['floor_heating_m2']
        costs.append({'Item': 'Yerden Isıtma Sistemi', 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['floor_heating_m2'], 'Total (€)': heating_cost})

    if project_inputs['solar']:
        solar_cost = project_inputs['solar_kw'] * FIYATLAR['solar_per_kw']
        costs.append({'Item': f'Güneş Enerjisi Sistemi ({project_inputs["solar_kw"]} kW)', 'Quantity': '1 sistem', 'Unit Price (€)': FIYATLAR['solar_per_kw'], 'Total (€)': solar_cost})

    if project_inputs['wheeled_trailer'] and project_inputs['wheeled_trailer_price'] > 0:
        costs.append({'Item': 'Tekerlekli Römork', 'Quantity': '1 adet', 'Unit Price (€)': project_inputs['wheeled_trailer_price'], 'Total (€)': project_inputs['wheeled_trailer_price']})

    # --- Aether Living Paketlerine Özel Maliyetler ---
    # Bu bölüm, hesaplamalarda st.session_state.aether_package_choice baz alınarak fiyatları ekler.
    # UI'daki checkbox'lar ayrı ayrı manuel olarak kontrol edilir. (bu bölüm eksikti, eklendi)
    if project_inputs['aether_package_choice'] == 'Aether Living | Loft Premium (ESSENTIAL)':
        if project_inputs['bedroom_set_option']:
            costs.append({'Item': FIYATLAR['bedroom_set_total_price'], 'Quantity': '1 adet', 'Unit Price (€)': FIYATLAR['bedroom_set_total_price'], 'Total (€)': FIYATLAR['bedroom_set_total_price']})
        if project_inputs['brushed_granite_countertops_option'] and project_inputs['brushed_granite_countertops_m2_val'] > 0:
            granite_cost = project_inputs['brushed_granite_countertops_m2_val'] * FIYATLAR['brushed_grey_granite_countertops_price_m2_avg']
            costs.append({'Item': FIYATLAR['brushed_grey_granite_countertops_info'], 'Quantity': f"{project_inputs['brushed_granite_countertops_m2_val']:.2f} m²", 'Unit Price (€)': FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'], 'Total (€)': granite_cost})
        if project_inputs['terrace_laminated_wood_flooring_option'] and project_inputs['terrace_laminated_wood_flooring_m2_val'] > 0:
            terrace_flooring_cost = project_inputs['terrace_laminated_wood_flooring_m2_val'] * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2']
            costs.append({'Item': FIYATLAR['treated_pine_floor_info'], 'Quantity': f"{project_inputs['terrace_laminated_wood_flooring_m2_val']:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_flooring_cost})
    
    elif project_inputs['aether_package_choice'] == 'Aether Living | Loft Elite (LUXURY)':
        # Elite paketinde Premium'daki tüm özellikler varsa buraya da eklenmeli (veya yukarıda işlenmeli)
        # Sadece Elite'e özgü ekstralar buraya yazılır
        # Not: Elite paketi seçildiğinde Premium paketin özelliklerinin de eklenmesi gerekiyorsa,
        # bu mantık daha geniş bir 'if/elif' zincirinde veya ayrı bir fonksiyonda toplanabilir.

        if project_inputs['exterior_cladding_m2_option'] and project_inputs['exterior_cladding_m2_val'] > 0:
            # Mavi Alçıpan malzeme maliyeti
            mavi_alcipan_m2_price_converted = FIYATLAR['gypsum_board_blue_per_unit_price'] / GYPSUM_BOARD_UNIT_AREA_M2
            mavi_alcipan_material_cost = calculate_rounded_up_cost(project_inputs['exterior_cladding_m2_val'] * mavi_alcipan_m2_price_converted)
            costs.append({'Item': FIYATLAR['exterior_cladding_material_info'], 'Quantity': f"{project_inputs['exterior_cladding_m2_val']:.2f} m²", 'Unit Price (€)': mavi_alcipan_m2_price_converted, 'Total (€)': mavi_alcipan_material_cost})
            
            # Dış Cephe Kaplama İşçiliği
            exterior_cladding_labor_cost = calculate_rounded_up_cost(project_inputs['exterior_cladding_m2_val'] * FIYATLAR['exterior_cladding_labor_price_per_m2'])
            costs.append({'Item': FIYATLAR['exterior_cladding_labor_info'], 'Quantity': f"{project_inputs['exterior_cladding_m2_val']:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_labor_price_per_m2'], 'Total (€)': exterior_cladding_labor_cost})

        if project_inputs['concrete_panel_floor_option'] and project_inputs['concrete_panel_floor_m2_val'] > 0:
            concrete_panel_cost = calculate_rounded_up_cost(project_inputs['concrete_panel_floor_m2_val'] * FIYATLAR['concrete_panel_floor_price_per_m2'])
            costs.append({'Item': FIYATLAR['concrete_panel_floor_info'], 'Quantity': f"{project_inputs['concrete_panel_floor_m2_val']:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})
        
        if project_inputs['premium_faucets_option']:
            costs.append({'Item': FIYATLAR['premium_faucets_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['premium_faucets_total_price'], 'Total (€)': FIYATLAR['premium_faucets_total_price']})
        
        if project_inputs['integrated_fridge_option']:
            costs.append({'Item': FIYATLAR['integrated_refrigerator_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['white_goods_total_price'], 'Total (€)': FIYATLAR['white_goods_total_price']}) # Buzdolabı beyaz eşya fiyatından
        
        if project_inputs['designer_furniture_option']:
            costs.append({'Item': FIYATLAR['designer_furniture_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['designer_furniture_total_price'], 'Total (€)': FIYATLAR['designer_furniture_total_price']})
        
        if project_inputs['italian_sofa_option']:
            costs.append({'Item': FIYATLAR['italian_sofa_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['italian_sofa_total_price'], 'Total (€)': FIYATLAR['italian_sofa_total_price']})
        
        if project_inputs['inclass_chairs_option'] and project_inputs['inclass_chairs_count'] > 0:
            chairs_cost = project_inputs['inclass_chairs_count'] * FIYATLAR['inclass_chairs_unit_price']
            costs.append({'Item': FIYATLAR['inclass_chairs_info'], 'Quantity': f"{project_inputs['inclass_chairs_count']}", 'Unit Price (€)': FIYATLAR['inclass_chairs_unit_price'], 'Total (€)': chairs_cost})
        
        if project_inputs['smart_home_systems_option']:
            costs.append({'Item': FIYATLAR['smart_home_systems_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['smart_home_systems_total_price'], 'Total (€)': FIYATLAR['smart_home_systems_total_price']})
        
        if project_inputs['security_camera_option']:
            costs.append({'Item': FIYATLAR['security_camera_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['security_camera_total_price'], 'Total (€)': FIYATLAR['security_camera_total_price']})
        
        if project_inputs['white_goods_fridge_tv_option']:
            costs.append({'Item': FIYATLAR['white_goods_fridge_tv_option_info'], 'Quantity': '1', 'Unit Price (€)': FIYATLAR['white_goods_total_price'], 'Total (€)': FIYATLAR['white_goods_total_price']})
            # Assuming info key added in FIYATLAR

                # Final calculations
                material_subtotal = sum(item['Total (€)'] for item in costs if 'Total (€)' in item)
                waste_cost = material_subtotal * FIRE_RATE
                total_cost = material_subtotal + waste_cost
                profit_amount = total_cost * st.session_state.profit_rate[1]
                vat_base = total_cost + profit_amount
                vat_amount = vat_base * VAT_RATE
                final_price = vat_base + vat_amount
                
                financial_summary = [
                    {"Item": "Material Subtotal", "Amount (€)": format_currency(material_subtotal)},
                    {"Item": f"Waste Cost ({FIRE_RATE*100:.0f}%)", "Amount (€)": format_currency(waste_cost)},
                    {"Item": "Total Cost", "Amount (€)": format_currency(total_cost)},
                    {"Item": f"Profit ({st.session_state.profit_rate[0]})", "Amount (€)": format_currency(profit_amount)},
                    {"Item": "VAT Base", "Amount (€)": format_currency(vat_base)},
                    {"Item": f"VAT ({VAT_RATE*100:.0f}%)", "Amount (€)": format_currency(vat_amount)},
                    {"Item": "FINAL SALES PRICE", "Amount (€)": format_currency(final_price)}
                ]
                
                # Display results
                st.subheader("Calculation Results")
                st.dataframe(pd.DataFrame(financial_summary_data))
                
                # PDF generation
                logo_data = get_company_logo_base64(COMPANY_INFO['logo_url'])
                
                # Internal report
                internal_pdf = create_internal_cost_report_pdf(
                    pd.DataFrame(costs),
                    pd.DataFrame(financial_summary_data, columns=['Item', 'Amount (€)']),
                    project_details,
                    customer_info,
                    logo_data
                )
                
                # Download buttons
                st.download_button(
                    "Download Internal Report",
                    data=internal_pdf.getvalue(),
                    file_name=f"internal_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
                # Placeholder for customer proposal PDF
                st.download_button(
                    "Download Customer Proposal",
                    data=internal_pdf.getvalue(),  # In a real app, this would be a different PDF
                    file_name=f"customer_proposal_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.exception(e)
    
    
if __name__ == "__main__":
    run_streamlit_app()
