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
    """Metindeki görünmez karakterleri temizler"""
    # U+00A0 (non-breaking space) ve U+200B (zero width space) gibi karakterleri temizler
    return re.sub(r'[\u00A0\u200B]', ' ', text)

# --- Font Kaydı (Türkçe karakter desteği) ---
try:
    if not os.path.exists("fonts"):
        os.makedirs("fonts")
    # Kontrol ve indirme: FreeSans.ttf
    if not os.path.exists("fonts/FreeSans.ttf"):
        st.cache_resource
        def download_font(url, path):
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        # Genellikle google fonts'tan indirilebilir bir URL kullanılır
        # Bu URL'ler geçici olabilir, gerçek bir font CDN'i veya github linki kullanılmalı
        # Şimdilik örnek bir font linki bırakıyorum, gerçek bir linkle değiştirilmeli
        # Örneğin: https://github.com/googlefonts/opensans/blob/main/fonts/ttf/OpenSans-Regular.ttf
        # Test için Google Fonts üzerinden doğrudan bir ttf dosyası bulmak zor olabilir.
        # Bu yüzden, kullanıcıdan fonts klasörünü manuel olarak eklemesini isteyeceğiz.
        st.warning("fonts/FreeSans.ttf bulunamadı. Lütfen gerekli font dosyalarını 'fonts/' klasörüne ekleyin.")
        raise FileNotFoundError # Hata fırlatarak try bloğundan çık
    
    pdfmetrics.registerFont(TTFont("FreeSans", "fonts/FreeSans.ttf"))
    pdfmetrics.registerFont(TTFont("FreeSans-Bold", "fonts/FreeSansBold.ttf"))
    pdfmetrics.registerFontFamily('FreeSans', normal='FreeSans', bold='FreeSans-Bold')
    MAIN_FONT = "FreeSans"
except Exception as e:
    st.warning(f"Font yükleme hatası: {e}. Helvetica kullanılacak. Lütfen 'fonts' klasöründe 'FreeSans.ttf' ve 'FreeSansBold.ttf' dosyalarının olduğundan emin olun.")
    MAIN_FONT = "Helvetica"

# --- Şirket Bilgileri ---
LOGO_URL = "https://drive.google.com/uc?export=download&id=1RD27Gas035iUqe4Ucl3phFwxZPWZPWzn" # Google Drive'dan genel erişimli bir logo URL'si
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
    "swift_bic": "BCYPCY2N"
}

# --- Güncel Fiyat Tanımları ---
# Fiyatlar KDV hariç maliyet fiyatlarıdır.
FIYATLAR = {
    # Çelik Profil Fiyatları (6m parça başı)
    "steel_profile_100x100x3": 45.00,
    "steel_profile_100x50x3": 33.00,
    "steel_profile_40x60x2": 14.00,
    "steel_profile_120x60x5mm": 60.00,
    "steel_profile_50x50x2": 11.00,
    "steel_profile_HEA160": 155.00,
    
    # Malzeme Fiyatları
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
    "wc_ceramic_m2_material": 20.00, # Porselen fayans için de kullanılacak malzeme m2 fiyatı
    "wc_ceramic_m2_labor": 20.00,     # Porselen fayans için de kullanılacak işçilik m2 fiyatı
    "electrical_per_m2": 25.00,
    "plumbing_per_m2": 25.00,
    "osb_piece": 12.00,
    "insulation_per_m2": 5.00, # Genel Yalıtım (5cm probu gibi)
    
    # İşçilik Fiyatları
    "welding_labor_m2_standard": 160.00,
    "welding_labor_m2_trmontaj": 20.00,
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00, # Alçıpan genel malzeme m2 fiyatı (Guardex için kullanılabilir)
    "plasterboard_labor_m2_avg": 80.00, # Alçıpan işçilik m2 fiyatı
    "plywood_flooring_labor_m2": 11.11,
    "door_window_assembly_labor_piece": 10.00,
    "solar_per_kw": 1250.00,
    
    # Yeni Zemin Sistemi Malzemeleri Fiyatları
    "skirting_meter_price": 2.00,
    "laminate_flooring_m2_price": 15.00,
    "under_parquet_mat_m2_price": 3.00,
    "osb2_18mm_piece_price": 30.00,
    "galvanized_sheet_m2_price": 10.00,

    # Aether Living/Yeni Ürün ve Diğer Yeni Eklenen Kalemler Fiyatları
    "smart_home_systems_total_price": 350.00,
    "white_goods_total_price": 800.00,
    "sofa_total_price": 400.00,
    "security_camera_total_price": 650.00,
    "exterior_cladding_labor_price_per_m2": 150.00, # Knauf Aquapanel gibi dış cephe işçiliği M2 bazlı
    "bedroom_set_total_price": 800.00,
    "terrace_laminated_wood_flooring_price_per_m2": 40.00,
    "concrete_panel_floor_price_per_m2": 50.00,
    "premium_faucets_total_price": 200.00,
    "designer_furniture_total_price": 1000.00,
    "italian_sofa_total_price": 800.00,
    "inclass_chairs_unit_price": 150.00,
    "exterior_wood_cladding_m2_price": 150.00,
    "brushed_grey_granite_countertops_price_m2_avg": 425.00,
    "100mm_eps_isothermal_panel_unit_price": 27.00,

    # Alçıpan modellerinin birim fiyatları (Ivan'dan gelen ve güncellenen)
    "gypsum_board_white_per_unit_price": 8.65, # adet. İç cephe için kullanılacak
    "gypsum_board_green_per_unit_price": 11.95, # adet. Banyo/WC için kullanılacak
    "gypsum_board_blue_per_unit_price": 22.00, # Knauf Aquapanel Mavi Alçıpan adet fiyatı
    
    # Diğer malzeme birim fiyatları (Ivan'dan)
    "otb_stone_wool_price": 19.80, # Taşyünü fiyatı (birim/adet)
    "glass_wool_5cm_packet_price": 19.68, # Cam yünü 5cm paket fiyatı (10m2 için)
    "tn25_screws_price_per_unit": 5.58, # TN25 vidalar fiyatı (adet)
    "cdx400_material_price": 3.40, # CDX400 malzeme fiyatı (adet)
    "ud_material_price": 1.59, # UD malzeme fiyatı (adet)
    "oc50_material_price": 2.20, # OC50 malzeme fiyatı (adet)
    "oc100_material_price": 3.96, # OC100 malzeme fiyatı (adet)
    "ch100_material_price": 3.55, # ch100 malzeme fiyatı (adet)

    # Material Info Keys (for reporting purposes)
    "steel_skeleton_info": "Metal iskelet",
    "protective_automotive_paint_info": "Koruyucu otomotiv boyası",
    "insulation_info_general": "Genel Yalıtım (EPS/Poliüretan)",
    "60mm_eps_sandwich_panel_info": "Standart 60mm EPS veya Poliüretan Sandviç Paneller (beyaz)",
    "100mm_eps_isothermal_panel_info": "Yüksek performanslı 100mm EPS veya Poliüretan İzotermik Paneller",
    "galvanized_sheet_info": "Galvanizli sac (Zemin)",
    "plywood_osb_floor_panel_info": "Kontraplak/OSB zemin paneli",
    "12mm_laminate_parquet_info": "12mm Laminat Parke",
    "induction_hob_info": "İndüksiyonlu ocak",
    "electric_faucet_info": "Elektrikli batarya",
    "kitchen_sink_info": "Mutfak evyesi",
    "fully_functional_bathroom_fixtures_info": "Tam fonksiyonel banyo armatürleri",
    "kitchen_bathroom_countertops_info": "Mutfak ve banyo tezgahları",
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
    "exterior_wood_cladding_lambiri_info": "Dış cephe ahşap kaplama - Lambiri",
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
    "satin_plaster_paint_info": "Saten sıva ve boya",
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
    """Maliyeti yukarı yuvarlar"""
    return math.ceil(value * 100) / 100.0

# --- PDF Oluşturma Fonksiyonları ---
def get_company_logo_base64(url, width=180):
    """Fetches the company logo from URL and returns it as base64 encoded string."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(io.BytesIO(response.content))
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width, h_size), Image.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG") 
        return base64.b64encode(buffered.getvalue()).decode()
    except requests.exceptions.RequestException as e:
        st.warning(f"Logo URL'den alınırken hata oluştu: {e}")
        return None
    except Exception as e:
        st.warning(f"Logo işlenirken hata oluştu: {e}")
        return None

def draw_pdf_header(canvas_obj, doc, logo_data_b64, company_info):
    """Draws the page header with logo and company info for PDFs."""
    if logo_data_b64:
        logo = Image(io.BytesIO(base64.b64decode(logo_data_b64)))
        logo.drawHeight = 25 * mm
        logo.drawWidth = 80 * mm 
        logo.drawOn(canvas_obj, doc.leftMargin, A4[1] - doc.topMargin + 5*mm)

    canvas_obj.setFont(MAIN_FONT, 8)
    canvas_obj.setFillColor(colors.HexColor('#2C3E50'))
    canvas_obj.drawString(A4[0] - doc.rightMargin - 60*mm, A4[1] - doc.topMargin + 20*mm, company_info['phone'])
    canvas_obj.drawString(A4[0] - doc.rightMargin - 60*mm, A4[1] - doc.topMargin + 15*mm, company_info['email'])
    canvas_obj.drawString(A4[0] - doc.rightMargin - 60*mm, A4[1] - doc.topMargin + 10*mm, company_info['website'])

def draw_pdf_footer(canvas_obj, doc, company_info):
    """Draws the page footer with company info and page number for PDFs."""
    footer_text = f"{company_info['address']} | {company_info['email']} | {company_info['phone']} | {company_info['website']} | Linktree: {company_info['linktree']}"
    canvas_obj.setFont(f"{MAIN_FONT}-Bold", 8)
    canvas_obj.drawCentredString(A4[0] / 2, 15*mm, footer_text)
    
    page_num = canvas_obj.getPageNumber()
    canvas_obj.setFont(MAIN_FONT, 8)
    canvas_obj.drawString(A4[0] - doc.rightMargin, 10*mm, f"Page {page_num}")

def create_internal_cost_report_pdf(cost_breakdown_df, financial_summary_df, project_details, customer_info, logo_data_b64):
    """Dahili maliyet raporu PDF'i oluşturur"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=40*mm, bottomMargin=25*mm) # Increased margins for header/footer
    
    styles = getSampleStyleSheet()
    custom_styles = {
        'Normal': ParagraphStyle('Normal', parent=styles['Normal'], fontName=MAIN_FONT, fontSize=9, leading=12),
        'Bold': ParagraphStyle('Bold', parent=styles['Normal'], fontName=f'{MAIN_FONT}-Bold', fontSize=9, leading=12),
        'Heading': ParagraphStyle('Heading', parent=styles['Heading2'], fontName=f'{MAIN_FONT}-Bold', fontSize=12, spaceAfter=6, textColor=colors.HexColor('#34495E')),
        'SubHeading': ParagraphStyle('SubHeading', parent=styles['Heading3'], fontName=f'{MAIN_FONT}-Bold', fontSize=10, spaceAfter=4, textColor=colors.HexColor('#2C3E50')),
        'Title': ParagraphStyle('Title', parent=styles['Heading1'], fontName=f'{MAIN_FONT}-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=12, textColor=colors.HexColor('#2C3E50'))
    }
    
    elements = []
    
    # Başlık
    elements.append(Paragraph("PREMIUM HOME - DAHİLİ MALİYET RAPORU", custom_styles['Title']))
    elements.append(Spacer(1, 5*mm))
    
    # Müşteri ve Proje Bilgileri
    elements.append(Paragraph(f"<b>Müşteri:</b> {customer_info.get('name', 'GENEL')} ({customer_info.get('company', '')})", custom_styles['Normal']))
    elements.append(Paragraph(f"<b>Proje Alanı:</b> {project_details['area']:.2f} m² | <b>Yapı Tipi:</b> {project_details['structure_type']}", custom_styles['Normal']))
    elements.append(Paragraph(f"<b>Oda Konfigürasyonu:</b> {project_details['room_configuration']}", custom_styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Maliyet Dökümü
    elements.append(Paragraph("MALİYET DETAYLARI", custom_styles['Heading']))
    if not cost_breakdown_df.empty:
        # Convert DataFrame to list of lists for ReportLab Table
        data = [cost_breakdown_df.columns.tolist()] + cost_breakdown_df.values.tolist()
        table = Table(data, colWidths=[90*mm, 30*mm, 35*mm, 30*mm]) # Adjusted colWidths
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'), # Birim Fiyat ve Toplam sağa hizalı
            ('FONTNAME', (0,0), (-1,0), f'{MAIN_FONT}-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,1), (-1,-1), MAIN_FONT),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('TOPPADDING', (0,1), (-1,-1), 4),
            ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Maliyet dökümü bulunmamaktadır.", custom_styles['Normal']))
    elements.append(Spacer(1, 15*mm))
    
    # Finansal Özet
    elements.append(Paragraph("FİNANSAL ÖZET", custom_styles['Heading']))
    if not financial_summary_df.empty:
        data = [financial_summary_df.columns.tolist()] + financial_summary_df.values.tolist()
        table = Table(data, colWidths=[120*mm, 40*mm]) # Adjusted colWidths
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,0), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), f'{MAIN_FONT}-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#ebf8ff")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#90cdf4")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,1), (-1,-1), MAIN_FONT),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('TOPPADDING', (0,1), (-1,-1), 4),
            ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Finansal özet bulunmamaktadır.", custom_styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    doc.build(elements, onLaterPages=lambda canvas_obj, doc: draw_pdf_header(canvas_obj, doc, logo_data_b64, COMPANY_INFO),
              onFirstPage=lambda canvas_obj, doc: draw_pdf_footer(canvas_obj, doc, COMPANY_INFO)) 
    return buffer

def create_customer_proposal_pdf_tr(house_price, solar_price, total_price, project_details, notes, customer_info, logo_data_b64):
    """Creates a professional proposal PDF for the customer (Turkish)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=40*mm, 
        bottomMargin=25*mm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='NormalTR', parent=styles['Normal'], fontSize=9, leading=12, fontName=MAIN_FONT
    ))
    styles.add(ParagraphStyle(
        name='HeadingTR', parent=styles['Heading2'], fontSize=12, spaceAfter=6, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        name='PriceTotalTR', parent=styles['Heading1'], fontSize=21, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#c53030")
    ))
    styles.add(ParagraphStyle(
        name='SectionSubheadingTR', parent=styles['Heading3'], fontSize=10, spaceAfter=4, spaceBefore=8,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568")
    ))
    title_style_tr = ParagraphStyle(
        name='TitleTR', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER,
        spaceAfter=12, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )

    elements = []

    # Cover Page
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph("PREFABRİK EV TEKLİFİ", title_style_tr))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph(f"Müşteri: {customer_info['name']}", styles['NormalTR']))
    if customer_info['company']:
        elements.append(Paragraph(f"Firma: {customer_info['company']}", styles['NormalTR']))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d/%m/%Y')}", styles['NormalTR']))
    elements.append(PageBreak())

    # Customer & Project Information
    elements.append(Paragraph("MÜŞTERİ VE PROJE BİLGİLERİ", styles['HeadingTR']))
    elements.append(Paragraph(f"<b>Oda Konfigürasyonu:</b> {project_details['room_configuration']}", styles['NormalTR']))
    elements.append(Paragraph(f"<b>Boyutlar:</b> {project_details['width']}m x {project_details['length']}m x {project_details['height']}m | <b>Toplam Alan:</b> {project_details['area']:.2f} m² | <b>Yapı Tipi:</b> {project_details['structure_type']}", styles['NormalTR']))
    elements.append(Spacer(1, 8*mm))

    customer_info_table_data_tr = [
        [Paragraph("<b>Adı Soyadı:</b>", styles['NormalTR']), Paragraph(f"{customer_info['name']}", styles['NormalTR'])],
        [Paragraph("<b>Firma:</b>", styles['NormalTR']), Paragraph(f"{customer_info['company'] or ''}", styles['NormalTR'])],
        [Paragraph("<b>Adres:</b>", styles['NormalTR']), Paragraph(f"{customer_info['address'] or ''}", styles['NormalTR'])],
        [Paragraph("<b>Telefon:</b>", styles['NormalTR']), Paragraph(f"{customer_info['phone'] or ''}", styles['NormalTR'])],
        [Paragraph("<b>Kimlik/Pasaport No:</b>", styles['NormalTR']), Paragraph(f"{customer_info['id_no'] or ''}", styles['NormalTR'])],
    ]
    customer_info_table_tr = Table(customer_info_table_data_tr, colWidths=[65*mm, 105*mm])
    customer_info_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(customer_info_table_tr)
    elements.append(Spacer(1, 8*mm))

    # Technical Specifications Section
    elements.append(Paragraph("TEKNİK ÖZELLİKLER", styles['HeadingTR']))
    
    # Yapı ve Malzemeler
    building_structure_table_data_tr = []
    building_structure_table_data_tr.append([Paragraph('<b>Yapı Tipi</b>', styles['NormalTR']), Paragraph(project_details['structure_type'], styles['NormalTR'])])
    if project_details['structure_type'] == 'Light Steel':
        building_structure_table_data_tr.append([Paragraph('<b>Çelik Yapı Detayları</b>', styles['NormalTR']), Paragraph(LIGHT_STEEL_BUILDING_STRUCTURE_TR, styles['NormalTR'])])
    else:
        building_structure_table_data_tr.append([Paragraph('<b>Çelik Yapı Detayları</b>', styles['NormalTR']), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_TR, styles['NormalTR'])])
    
    building_structure_table_tr = Table(building_structure_table_data_tr, colWidths=[60*mm, 110*mm])
    building_structure_table_tr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(building_structure_table_tr)
    elements.append(Spacer(1, 5*mm))

    elements.append(Paragraph("FİYAT VE ÖDEME PLANI", styles['HeadingTR']))
    price_table_data_tr = []
    price_table_data_tr.append([
        Paragraph("Ana Ev Bedeli", styles['NormalTR']),
        Paragraph(format_currency(house_price), styles['NormalTR'])
    ])
    if solar_price > 0:
        price_table_data_tr.append([
            Paragraph("Güneş Enerjisi Sistemi Bedeli", styles['NormalTR']),
            Paragraph(format_currency(solar_price), styles['NormalTR'])
        ])
    price_table_data_tr.append([
        Paragraph("<b>TOPLAM BEDEL</b>", styles['NormalTR']),
        Paragraph(f"<b>{format_currency(total_price)}</b>", styles['NormalTR'])
    ])
    
    price_summary_table_tr = Table(price_table_data_tr, colWidths=[120*mm, 50*mm])
    price_summary_table_tr.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#ccc")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(price_summary_table_tr)
    elements.append(Spacer(1, 8*mm))

    doc.build(elements, onLaterPages=lambda canvas_obj, doc: draw_pdf_header(canvas_obj, doc, logo_data_b64, COMPANY_INFO),
              onFirstPage=lambda canvas_obj, doc: draw_pdf_footer(canvas_obj, doc, COMPANY_INFO))
    return buffer

def create_sales_contract_pdf(customer_info, house_sales_price, solar_sales_price, project_details, company_info, logo_data_b64):
    """Creates a sales contract PDF (Turkish)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=40*mm,
        bottomMargin=25*mm
    )

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
        name='ContractNormal', parent=styles['Normal'], fontSize=9, leading=12,
        spaceAfter=4, fontName=MAIN_FONT, alignment=TA_LEFT
    )
    contract_list_style = ParagraphStyle(
        name='ContractList', parent=styles['Normal'], fontSize=9, leading=12,
        spaceAfter=2, leftIndent=8*mm, fontName=MAIN_FONT
    )
    contract_signature_style = ParagraphStyle(
        name='ContractSignature', parent=styles['Normal'], fontSize=9, leading=12,
        alignment=TA_CENTER
    )

    elements = []

    # Title
    elements.append(Paragraph("SATIŞ SÖZLEŞMESİ", contract_heading_style))
    elements.append(Spacer(1, 6*mm))

    # Parties involved
    today_date = datetime.now().strftime('%d')
    today_month = datetime.now().strftime('%B')
    today_year = datetime.now().year
    elements.append(Paragraph(f"Bu Sözleşme ('Sözleşme'), bu {today_date} {today_month}, {today_year} tarihinde aşağıda belirtilen taraflar arasında yapılmıştır:", contract_normal_style))
    elements.append(Paragraph(f"<b>{customer_info['name'].upper()}</b> (T.C. Kimlik No: <b>{customer_info['id_no']}</b>) bundan böyle 'Alıcı' olarak anılacaktır, ve", contract_normal_style))
    elements.append(Paragraph(f"<b>{company_info['name'].upper()}</b>, Şirket No. <b>{company_info['company_no']}</b>, adresi {company_info['address']} olan, bundan böyle 'Satıcı' olarak anılacaktır.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Subject of the Agreement
    elements.append(Paragraph("Sözleşmenin Konusu:", contract_subheading_style))
    elements.append(Paragraph(f"A. Satıcı, Alıcıya LIGHT STEEL STRUCTURE CONSTRUCTION (Tiny House) yapısını, Alıcı tarafından belirtilen adreste kendi koordinasyonu altında, Ek A'da detaylandırılan şartnamelere uygun olarak tamamlamayı ve teslim etmeyi kabul eder.", contract_normal_style))
    elements.append(Paragraph("B. Taşınabilir Ev projesi ile ilgili inşaat detayları, işbu sözleşmenin ayrılmaz bir parçası olan ekler olarak kabul edilecektir.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Sales Price and Payment Terms
    total_sales_price_for_contract = house_sales_price + solar_sales_price
    total_sales_price_formatted = format_currency(total_sales_price_for_contract)
    
    down_payment = house_sales_price * 0.40
    remaining_balance = house_sales_price - down_payment
    installment_amount = remaining_balance / 3

    elements.append(Paragraph("2. Satış Fiyatı ve Ödeme Koşulları:", contract_subheading_style))
    elements.append(Paragraph(f"2.1. Taşınabilir Konteyner Ev'in (bundan böyle 'ev' olarak anılacaktır) satış fiyatı, işbu sözleşmenin ayrılmaz bir parçası olan EK 'A'da açıklanan şartnamelere göre KDV dahil <b>{format_currency(house_sales_price)}</b>'dır.", contract_list_style))
    elements.append(Paragraph(f"2.2. Toplam satış fiyatı (varsa güneş enerjisi dahil) <b>{total_sales_price_formatted}</b> (KDV Dahil)'dir.", contract_list_style))
    elements.append(Paragraph("2.3. Alıcı, aşağıdaki tutarları programa göre ödeyecektir:", contract_list_style))

    elements.append(Paragraph(f"- Ana Ev (Toplam: {format_currency(house_sales_price)})", contract_list_style, bulletText=''))
    elements.append(Paragraph(f" - %40 Peşinat: {format_currency(down_payment)} sözleşme imzalanınca.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f" - 1. Taksit: {format_currency(installment_amount)} yapı tamamlandığında.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f" - 2. Taksit: {format_currency(installment_amount)} iç imalatlar tamamlandığında.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f" - Son Ödeme: {format_currency(installment_amount)} nihai teslimatta.", contract_list_style, bulletText='-'))

    if solar_sales_price > 0:
        elements.append(Paragraph(f"- Güneş Enerjisi Sistemi: {format_currency(solar_sales_price)} sözleşme imzalanınca.", contract_list_style, bulletText=''))

    elements.append(Paragraph("2.4. Herhangi bir ödeme gecikmesi, aylık %2 yasal faiz ile sonuçlanacaktır.", contract_list_style))
    elements.append(Paragraph("2.5. Alıcı, yazılı bildirime rağmen herhangi bir taksiti 20 günden fazla geciktirirse, satıcı sözleşmeyi feshetme ve sebep olduğu zararlar için depozitoyu tutma hakkını saklı tutar.", contract_list_style))
    elements.append(Paragraph("2.6. Yukarıdaki satış fiyatı, ödeme koşulları ve teslimat başlıkları altında öngörülen ödeme koşulları ve tarihleri, bu satış sözleşmesinin özünü ve temelini oluşturur.", contract_list_style))
    elements.append(Spacer(1, 6*mm))

    # Bank Details
    elements.append(Paragraph("2.7. Banka Bilgileri:", contract_subheading_style))
    bank_details_data = [
        [Paragraph("Banka Adı:", contract_normal_style), Paragraph(company_info['bank_name'], contract_normal_style)],
        [Paragraph("Banka Adresi:", contract_normal_style), Paragraph(company_info['bank_address'], contract_normal_style)],
        [Paragraph("Hesap Adı:", contract_normal_style), Paragraph(company_info['account_name'], contract_normal_style)],
        [Paragraph("IBAN:", contract_normal_style), Paragraph(company_info['iban'], contract_normal_style)],
        [Paragraph("Hesap Numarası:", contract_normal_style), Paragraph(company_info['account_number'], contract_normal_style)],
        [Paragraph("Para Birimi:", contract_normal_style), Paragraph(company_info['currency_type'], contract_normal_style)],
        [Paragraph("SWIFT/BIC:", contract_normal_style), Paragraph(company_info['swift_bic'], contract_normal_style)],
    ]
    bank_details_table = Table(bank_details_data, colWidths=[40*mm, 130*mm])
    bank_details_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(bank_details_table)
    elements.append(Spacer(1, 6*mm))

    # Inspection of the Property and Defects
    elements.append(Paragraph("3. Mülkün Muayenesi ve Kusurlar:", contract_subheading_style))
    elements.append(Paragraph("3.1. Alıcı, inşaat süreci boyunca mülkü denetleme hakkına sahiptir. Alıcı, 7 gün önceden bildirimde bulunarak herhangi bir zamanda denetim talep edebilir.", contract_normal_style))
    elements.append(Paragraph("3.2. Denetimler sırasında ortaya çıkan herhangi bir kusur veya endişe, Satıcı tarafından Alıcıya ek bir maliyet olmaksızın giderilecektir. Alıcı, her denetimden sonra durumu onaylayan yazılı bir denetim kaydı tutacaktır.", contract_normal_style))
    elements.append(Paragraph("3.3. Tamamlanan evin son denetimi, teslimat tarihinden itibaren 10 gün içinde gerçekleşecek ve Alıcı yazılı bir kusur listesi sunacaktır.", contract_normal_style))
    elements.append(Paragraph("3.4. Herhangi bir olası kusur olması durumunda, satıcı bunları ........ gün/ay içinde restore edecek ve alıcıyı bilgilendirecektir. Böyle bir durumda, evin teslimatı buna göre belirlenecektir.", contract_normal_style))
    elements.append(Paragraph("3.5. Satıcı, herhangi bir olası kusuru ........ gün/ay içinde onaracak ve/veya değiştirecektir.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Completion of the House
    elements.append(Paragraph("4. Evin Tamamlanması:", contract_subheading_style))
    elements.append(Paragraph("4.1. Satıcı, hafif çelik yapı evin inşaatının tamamlanmasının ardından, satış fiyatının ve Madde 2'de belirtilen tüm tutarların tam ödenmesi üzerine Alıcıya fatura düzenleyecek ve mülkü teslim edecektir. Bu konuyla ilgili belge temini, teslimat için belirtilen sürenin dışındadır.", contract_normal_style))
    elements.append(Paragraph("4.2. Bölme, devir vb. işlemlerin tamamlanabilmesi için Alıcı, Satıcıya yardımcı olmayı ve bu amaçla resmi, yarı resmi ve diğer makamlara Satıcı ve/veya diğer hissedar(lar) ile birlikte veya ayrı ayrı başvurmayı, gerekli imzaları atmayı, formları doldurmayı ve/veya gerekirse Satıcıyı temsilci olarak atamayı kabul eder.", contract_normal_style))
    elements.append(Paragraph("4.3. Alıcı, hafif çelik yapı evin teslimatından itibaren evin KDV'sinden sorumlu olacaktır.", contract_normal_style))
    elements.append(Paragraph("4.4. Satıcının gerekli yasal prosedürleri tamamlamasına rağmen, Satıcı bu evin malzemelerinin gümrük prosedürleri ve çıkışıyla ilgili gecikmelerden ve ek transit masraflarından sorumlu olmayacaktır.", contract_normal_style))
    elements.append(Paragraph(f"4.5. Ev, bu sözleşmenin imzalanmasından itibaren yaklaşık {project_details['delivery_duration_business_days']} iş günü içinde (hafta sonları ve resmi tatiller hariç) teslim edilecektir.", contract_normal_style))
    elements.append(Paragraph("4.6. Mücbir sebep olaylarından veya Alıcıdan kaynaklanan herhangi bir gecikme, teslimat süresini buna göre uzatacaktır.", contract_normal_style))
    elements.append(Paragraph("4.7. Satıcı, belirlenen teslimat tarihinde (4.5.) evi teslim edemezse, öngörülemeyen gecikmeler nedeniyle, gecikmenin nedenlerini belirten ve söz konusu gecikmenin üstesinden gelme yollarını öneren yazılı bir bildirimle alıcıya bildirmekle yükümlüdür.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Termination
    elements.append(Paragraph("5. Fesih:", contract_subheading_style))
    elements.append(Paragraph("5.1. Alıcı, bu sözleşmenin herhangi bir koşulunu yerine getirmezse, Satıcı, bu fesih nedenlerini açıklayan yazılı bir bildirim göndererek sözleşmeyi derhal feshetme hakkına sahiptir.", contract_normal_style))
    elements.append(Paragraph("5.2. Alıcı, belirlenen tarihte evi satın almamaya karar verirse, Alıcı, zararların tazminatı olarak verilen depozitonun tamamını kaybedeceğini kabul ve taahhüt eder. Satıcıdan kaynaklanan bir sorun olması veya Satıcının Alıcıya devretmemeye karar vermesi durumunda, Satıcı depozitonun tamamını Alıcıya iade edecektir.", contract_normal_style))
    elements.append(Paragraph("5.3. Bu sözleşme kapsamında verilecek tüm bildirimler, tarafların yukarıda belirtilen adreslerine bırakılarak veya posta yoluyla gönderilerek verilmiş veya tebliğ edilmiş sayılacaktır.", contract_normal_style))
    elements.append(Paragraph("5.4. Bu sözleşme, taraflarca imzalanmış ve paraflanmış 2 nüsha olarak düzenlenmiştir.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Notifications
    elements.append(Paragraph("6. Bildirimler:", contract_subheading_style))
    elements.append(Paragraph("Aşağıdakiler geçerli bildirimler olarak kabul edilecektir:", contract_normal_style))
    elements.append(Paragraph("6.1. Normal posta ile", contract_list_style))
    elements.append(Paragraph("6.2. Kayıtlı posta ile", contract_list_style))
    elements.append(Paragraph("6.3. Çift kayıtlı posta ile", contract_list_style))
    elements.append(Paragraph("6.4. Taraflarca kullanılan olağan elektronik posta ile", contract_list_style))
    elements.append(Paragraph("6.5. Bir icra memuru aracılığıyla tebligat ile", contract_list_style))
    elements.append(Paragraph("6.6. Faks ile", contract_list_style))
    elements.append(Paragraph("6.7. Telefon görüşmeleri, telefon mesajları (SMS), viber, whats'app, facebook messenger ve bu paragrafta belirtilmeyen diğer herhangi bir uygulama/uygulamalar, yukarıdaki paragraf (4c) uyarınca geçerli bir bildirim teşkil etmeyecektir.", contract_list_style))
    elements.append(Spacer(1, 6*mm))

    # Warranty and Defects liability
    elements.append(Paragraph("7. Garanti ve Ayıp Sorumluluğu:", contract_subheading_style))
    elements.append(Paragraph("7.1. Satıcı, evin malzeme ve işçilik kusurlarından arî olacağını, teslimat gününden itibaren ........ (ay/yıl) süreyle garanti eder.", contract_normal_style))
    elements.append(Paragraph("7.2. Söz konusu garanti, yanlış kullanım, ihmal veya harici faktörlerden (örn. doğal afetler) kaynaklanan hasarları kapsamaz.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Applicable Law
    elements.append(Paragraph("8. Uygulanacak Hukuk:", contract_subheading_style))
    elements.append(Paragraph("Bu Sözleşme ve bununla ilgili herhangi bir konu, Kıbrıs Cumhuriyeti yasalarına göre yönetilecek, yorumlanacak ve uygulanacaktır. Bu kapsamda doğabilecek herhangi bir anlaşmazlık, Kıbrıs mahkemelerinin münhasır yargı yetkisine tabi olacaktır.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Dispute Resolution - Mediation / Arbitration
    elements.append(Paragraph("9. Anlaşmazlık Çözümü - Arabuluculuk / Tahkim", contract_subheading_style))
    elements.append(Paragraph("9.1. Bu Sözleşme kapsamında ortaya çıkan ve ilgili Mahkeme önünde herhangi bir dava açılmadan önce, tüm anlaşmazlıklar öncelikle taraflar arasında müzakere yoluyla ele alınacaktır.", contract_normal_style))
    elements.append(Paragraph("9.2. Anlaşmazlığın müzakere yoluyla çözülememesi halinde, taraflar, Arabuluculuk Yasası §159(1)/2012'ye göre Kıbrıs Cumhuriyeti'nde arabuluculuğa başvurmayı kabul ederler.", contract_normal_style))
    elements.append(Paragraph("9.3. Arabuluculuğun başarısız olması halinde, anlaşmazlık [Tahkim Kuruluşu] kurallarına göre bağlayıcı tahkim yoluyla çözülecektir.", contract_normal_style))
    elements.append(Paragraph("9.4. Yukarıdaki alternatif uyuşmazlık çözümü, uzlaşmacı bir çözüm olmaması halinde taraflardan herhangi birinin Kıbrıs mahkemelerinde hukuki yollara başvurma anayasal hakkı ile çelişmez.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Amendments
    elements.append(Paragraph("10. Değişiklikler:", contract_subheading_style))
    elements.append(Paragraph("Bu sözleşmede yapılacak herhangi bir değişiklik veya tadilat, yukarıdaki (madde 6) yazılı bildirimden önce her iki tarafça yazılı olarak yapılmalı ve imzalanmalıdır.", contract_normal_style))
    elements.append(Spacer(1, 6*mm))

    # Final Clause
    elements.append(Paragraph("11. Bu Sözleşme, her bir tarafın birer nüshasını alacağı, İngilizce olarak iki (2) adet özdeş nüsha halinde yapılmıştır.", contract_normal_style))
    elements.append(Spacer(1, 25*mm))

    # Final Signature Block
    final_signature_data = [
        [Paragraph(f"<b>SATICI</b><br/><br/><br/>________________________________________<br/>Adına ve namına<br/>{company_info['name'].upper()}", contract_signature_style),
         Paragraph(f"<b>ALICI</b><br/><br/><br/>________________________________________<br/>{customer_info['name'].upper()}<br/>Kimlik No: {customer_info['id_no']}", contract_signature_style)]
    ]
    final_signature_table = Table(final_signature_data, colWidths=[80*mm, 80*mm], hAlign='CENTER')
    final_signature_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(final_signature_table)

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"Tarih: {datetime.now().strftime('%d/%m/%Y')}", contract_normal_style))

    # Witnesses
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph("Tanıklar:", contract_normal_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("1 (İmza) _____________________________________", contract_normal_style))
    elements.append(Paragraph("(Adı ve Kimlik No)", contract_normal_style))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("2 (İmza) _____________________________________", contract_normal_style))
    elements.append(Paragraph("(Adı ve Kimlik No)", contract_normal_style))

    doc.build(elements, onLaterPages=lambda canvas_obj, doc: draw_pdf_header(canvas_obj, doc, logo_data_b64, COMPANY_INFO),
              onFirstPage=lambda canvas_obj, doc: draw_pdf_footer(canvas_obj, doc, COMPANY_INFO))
    return buffer

# === Streamlit Uygulaması ===
def run_streamlit_app():
    # Sayfa konfigürasyonu
    st.set_page_config(
        layout="wide", 
        page_title="Premium Home Cost Calculator",
        initial_sidebar_state="expanded" # Default sidebar state
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background-color: #f8fafc; /* Light mode default */
    }
    
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
        border: none;
        font-weight: 500;
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
    
    st.title("🏠 Premium Home Cost Calculator")
    
    # === st.session_state değişkenlerinin koşulsuz başlatılması ===
    # Bu blok, uygulamanın her yeniden çalışmasında tüm anahtarların var olmasını sağlar.
    # Bu, UnboundLocalError/AttributeError'ı kesin olarak çözen ana yaklaşımdır.
    
    session_state_defaults = {
        'aether_package_choice': 'Yok',
        'kitchen_choice_radio': 'Mutfak Yok',
        'shower_val': False,
        'wc_ceramic_val': False,
        'wc_ceramic_area_val': 0.0,
        'electrical_val': False,
        'plumbing_val': False,
        'insulation_floor_val': False,
        'insulation_wall_val': False,
        'floor_covering_val': 'Laminate Parquet',
        'heating_val': False,
        'solar_val': False,
        'wheeled_trailer_val': False,
        'wheeled_trailer_price_input_val': 0.0,
        'exterior_cladding_m2_option_val': False,
        'exterior_cladding_m2_val': 0.0,
        'exterior_wood_cladding_m2_option_val': False,
        'exterior_wood_cladding_m2_val': 0.0,
        'porcelain_tiles_option_val': False,
        'porcelain_tiles_m2_val': 0.0,
        'concrete_panel_floor_option_val': False,
        'concrete_panel_floor_m2_val': 0.0,
        'bedroom_set_option_val': False,
        'sofa_option_val': False,
        'smart_home_systems_option_val': False,
        'security_camera_option_val': False,
        'white_goods_fridge_tv_option_val': False,
        'premium_faucets_option_val': False,
        'integrated_fridge_option_val': False,
        'designer_furniture_option_val': False,
        'italian_sofa_option_val': False,
        'inclass_chairs_option_val': False,
        'inclass_chairs_count_val': 0,
        'brushed_granite_countertops_option_val': False,
        'brushed_granite_countertops_m2_val': 0.0,
        'insulation_material_type_val': 'Taş Yünü',
        'skirting_count_val': 0.0,
        'laminate_flooring_m2_val': 0.0,
        'under_parquet_mat_m2_val': 0.0,
        'osb2_count_val': 0,
        'galvanized_sheet_m2_val': 0.0,
        'solar_capacity_val': 5, # Default first option
        'solar_price_val': 0.0, # Derived, but good to have default
        'customer_notes_val': "",
        'pdf_language_selector_val_tuple': ('Turkish', 'tr'),
        'profit_rate_val_tuple': (f'{20}%', 0.20) # Default index 3 of range(5,45,5)
    }

    # Session state'i başlat veya mevcut değerini kullan
    for key, default_value in session_state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # --- Aether Living Paketlerine göre st.session_state değerlerini güncelle ---
    # Bu blok, st.session_state'in başlangıç değerlerini paketin özelliklerine göre override eder.
    # Ancak UI widget'ları value parametresi için buradaki değeri doğrudan okuyamaz (AttributeError nedeniyle).
    # Bunun yerine, bu block sadece hesaplama mantığı ve PDF'ler için st.session_state değerlerini ayarlar.
    # UI'daki widget'lar ise kendi sabit varsayılanlarıyla başlar ve manuel etkileşimle değişir.
    if st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
        st.session_state.kitchen_choice_radio = 'Standart Mutfak'
        st.session_state.shower_val = True
        st.session_state.electrical_val = True
        st.session_state.plumbing_val = True
        st.session_state.insulation_floor_val = True 
        st.session_state.insulation_wall_val = True
        st.session_state.floor_covering_val = 'Laminate Parquet'
        st.session_state.insulation_material_type_val = 'Taş Yünü' # Standard pakette taş yünü varsayım

        st.session_state.exterior_cladding_m2_option_val = False
        st.session_state.exterior_wood_cladding_m2_option_val = False
        st.session_state.porcelain_tiles_option_val = False
        st.session_state.concrete_panel_floor_option_val = False
        st.session_state.bedroom_set_option_val = False
        st.session_state.sofa_option_val = False
        st.session_state.smart_home_systems_option_val = False
        st.session_state.security_camera_option_val = False
        st.session_state.white_goods_fridge_tv_option_val = False
        st.session_state.premium_faucets_option_val = False
        st.session_state.integrated_fridge_option_val = False
        st.session_state.designer_furniture_option_val = False
        st.session_state.italian_sofa_option_val = False
        st.session_state.inclass_chairs_option_val = False
        st.session_state.brushed_granite_countertops_option_val = False
        st.session_state.terrace_laminated_wood_flooring_option_val = False


    elif st.session_state.aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
        st.session_state.kitchen_choice_radio = 'Standart Mutfak' 
        st.session_state.shower_val = True
        st.session_state.electrical_val = True
        st.session_state.plumbing_val = True
        st.session_state.insulation_floor_val = True
        st.session_state.insulation_wall_val = True
        st.session_state.floor_covering_val = 'Laminate Parquet' 
        st.session_state.insulation_material_type_val = 'Taş Yünü'
        
        st.session_state.bedroom_set_option_val = True
        st.session_state.brushed_granite_countertops_option_val = True
        st.session_state.terrace_laminated_wood_flooring_option_val = True 
        
        st.session_state.exterior_cladding_m2_option_val = False
        st.session_state.exterior_wood_cladding_m2_option_val = False
        st.session_state.porcelain_tiles_option_val = False
        st.session_state.concrete_panel_floor_option_val = False
        st.session_state.sofa_option_val = False
        st.session_state.smart_home_systems_option_val = False
        st.session_state.security_camera_option_val = False
        st.session_state.white_goods_fridge_tv_option_val = False
        st.session_state.premium_faucets_option_val = False
        st.session_state.integrated_fridge_option_val = False
        st.session_state.designer_furniture_option_val = False
        st.session_state.italian_sofa_option_val = False
        st.session_state.inclass_chairs_option_val = False


    elif st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
        st.session_state.kitchen_choice_radio = 'Special Design Mutfak'
        st.session_state.shower_val = True
        st.session_state.electrical_val = True
        st.session_state.plumbing_val = True
        st.session_state.insulation_floor_val = True
        st.session_state.insulation_wall_val = True
        st.session_state.floor_covering_val = 'Ceramic'
        st.session_state.heating_val = True
        st.session_state.solar_val = True
        st.session_state.insulation_material_type_val = 'Cam Yünü'

        st.session_state.exterior_cladding_m2_option_val = True # Knauf Aquapanel
        st.session_state.exterior_wood_cladding_m2_option_val = False 
        st.session_state.concrete_panel_floor_option_val = True # Beton panel zemin
        st.session_state.premium_faucets_option_val = True
        st.session_state.integrated_fridge_option_val = True
        st.session_state.designer_furniture_option_val = True
        st.session_state.italian_sofa_option_val = True
        st.session_state.inclass_chairs_option_val = True
        st.session_state.inclass_chairs_count_val = 1 # Varsayılan 1 adet sandalye
        st.session_state.smart_home_systems_option_val = True
        st.session_state.security_camera_option_val = True
        st.session_state.white_goods_fridge_tv_option_val = True
        
        st.session_state.bedroom_set_option_val = True
        st.session_state.brushed_granite_countertops_option_val = True
        st.session_state.terrace_laminated_wood_flooring_option_val = False 


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

        # === Value parametresi için sabit varsayılanlar ve Session State'e yazma ===
        # AttributeError'ı çözmek için bu yaklaşım kullanılır.
        st.session_state.plasterboard_interior_option_val = st.checkbox(
            "İç Alçıpan Dahil Et", 
            value=False, # Sabit varsayılan
            disabled=plasterboard_interior_disabled, 
            key="pb_int_checkbox"
        )
        
        st.session_state.plasterboard_all_option_val = st.checkbox(
            "İç ve Dış Alçıpan Dahil Et", 
            value=False, # Sabit varsayılan
            disabled=plasterboard_all_disabled, 
            key="pb_all_checkbox"
        )
        
        # Calculation variables should directly read from session state
        plasterboard_interior_calc = st.session_state.plasterboard_interior_option_val
        plasterboard_all_calc = st.session_state.plasterboard_all_option_val

        # Logic for disabling Alçıpan types based on Structure Type
        if structure_type_val == 'Light Steel':
            plasterboard_all_calc = False 
        elif structure_type_val == 'Heavy Steel':
            plasterboard_interior_calc = False 

        osb_inner_wall_disabled = not (plasterboard_interior_calc or plasterboard_all_calc)
        st.session_state.osb_inner_wall_option_val = st.checkbox(
            "İç Duvar OSB Malzemesi Dahil Et", 
            value=False, # Sabit varsayılan
            disabled=osb_inner_wall_disabled, 
            key="osb_inner_checkbox"
        )
        
        osb_inner_wall_calc = st.session_state.osb_inner_wall_option_val
        if osb_inner_wall_disabled:
            osb_inner_wall_calc = False


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
        st.session_state.facade_sandwich_panel_option_val = st.checkbox(
            "Dış Cephe Sandviç Panel Dahil Et (Ağır Çelik için)", 
            value=False, # Sabit varsayılan
            disabled=facade_sandwich_panel_disabled, 
            key="facade_panel_checkbox"
        )
        
        facade_sandwich_panel_calc = st.session_state.facade_sandwich_panel_option_val
        if facade_sandwich_panel_disabled:
            facade_sandwich_panel_calc = False


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
    with col_wc_win2:
        wc_sliding_door_size_val = st.text_input("WC Sürme Kapı Boyutu:", value="140x70 cm", key="wc_sliding_door_size_input")
    with col_wc_win3:
        pass
    
    col_door_main1, col_door_main2, col_door_main3 = st.columns(3)
    with col_door_main1:
        door_input_val = st.number_input("Ana Kapı Adedi:", value=1, min_value=0, key="door_count_input")
    with col_door_main2:
        door_size_val = st.text_input("Ana Kapı Boyutu:", value="90x210 cm", key="door_size_input")
    with col_door_main3:
        pass

    # --- Additional Equipment Section ---
    st.markdown("<div class='section-title'>EK DONANIMLAR</div>", unsafe_allow_html=True)
    
    _temp_kitchen_choice_radio = st.session_state.kitchen_choice_radio
    st.session_state.kitchen_choice_radio = st.radio("Mutfak Tipi Seçimi:", ['Mutfak Yok', 'Standart Mutfak', 'Special Design Mutfak'], index=['Mutfak Yok', 'Standart Mutfak', 'Special Design Mutfak'].index(_temp_kitchen_choice_radio), key="kitchen_type_radio_select")
    
    kitchen_input_val = False
    kitchen_cost_val = 0.0
    kitchen_type_display_en_gr = "No"
    kitchen_type_display_tr = "Yok"

    if st.session_state.kitchen_choice_radio == 'Standart Mutfak':
        kitchen_input_val = True
        kitchen_cost_val = FIYATLAR["kitchen_installation_standard_piece"]
        kitchen_type_display_en_gr = "Yes (Standard)"
        kitchen_type_display_tr = "Var (Standart)"
    elif st.session_state.kitchen_choice_radio == 'Special Design Mutfak':
        kitchen_input_val = True
        kitchen_cost_val = FIYATLAR["kitchen_installation_special_piece"]
        kitchen_type_display_en_gr = "Yes (Special Design)"
        kitchen_type_display_tr = "Var (Özel Tasarım)"
    
    _temp_shower_val = st.session_state.shower_val
    st.session_state.shower_val = st.checkbox("Duş/WC Dahil Et", value=_temp_shower_val, key="shower_checkbox")
    
    col_ceramic1, col_ceramic2 = st.columns(2)
    with col_ceramic1:
        _temp_wc_ceramic_val = st.session_state.wc_ceramic_val
        st.session_state.wc_ceramic_val = st.checkbox("WC Seramik Zemin/Duvar", value=_temp_wc_ceramic_val, key="wc_ceramic_checkbox")
    with col_ceramic2:
        wc_ceramic_area_disabled = not st.session_state.wc_ceramic_val
        _temp_wc_ceramic_area_val = st.session_state.wc_ceramic_area_val
        st.session_state.wc_ceramic_area_val = st.number_input("WC Seramik Alanı (m²):", value=_temp_wc_ceramic_area_val, step=0.1, min_value=0.0, disabled=wc_ceramic_area_disabled, key="wc_ceramic_area_input")
    
    _temp_electrical_val = st.session_state.electrical_val
    st.session_state.electrical_val = st.checkbox("Elektrik Tesisatı (Malzemelerle)", value=_temp_electrical_val, key="electrical_checkbox")
    _temp_plumbing_val = st.session_state.plumbing_val
    st.session_state.plumbing_val = st.checkbox("Sıhhi Tesisat (Malzemelerle)", value=_temp_plumbing_val, key="plumbing_checkbox")
    
    # Zemin yalıtım malzemeleri girişleri
    st.markdown("---")
    st.subheader("Zemin Yalıtımı ve Malzemeleri")
    _temp_insulation_floor_val = st.session_state.insulation_floor_val
    st.session_state.insulation_floor_val = st.checkbox("Zemin Yalıtımı Dahil Et (5€/m²)", value=_temp_insulation_floor_val, key="floor_insulation_checkbox")
    
    floor_insulation_material_disabled = not st.session_state.insulation_floor_val

    col_floor_mats = st.columns(3)
    with col_floor_mats[0]:
        _temp_skirting_count_val = st.session_state.skirting_count_val
        st.session_state.skirting_count_val = st.number_input(f"Süpürgelik ({FIYATLAR['skirting_meter_price']}€/m) Uzunluğu (m):", value=_temp_skirting_count_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="skirting_input")
    with col_floor_mats[1]:
        _temp_laminate_flooring_m2_val = st.session_state.laminate_flooring_m2_val
        st.session_state.laminate_flooring_m2_val = st.number_input(f"Laminat Parke 12mm ({FIYATLAR['laminate_flooring_m2_price']}€/m²) Alanı (m²):", value=_temp_laminate_flooring_m2_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="laminate_flooring_input")
    with col_floor_mats[2]:
        _temp_under_parquet_mat_m2_val = st.session_state.under_parquet_mat_m2_val
        st.session_state.under_parquet_mat_m2_val = st.number_input(f"Parke Altı Şilte 4mm ({FIYATLAR['under_parquet_mat_m2_price']}€/m²) Alanı (m²):", value=_temp_under_parquet_mat_m2_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="under_parquet_mat_input")
    
    col_floor_mats2 = st.columns(3)
    with col_floor_mats2[0]:
        _temp_osb2_18mm_count_val = st.session_state.osb2_18mm_count_val
        st.session_state.osb2_18mm_count_val = st.number_input(f"OSB2 18mm/Beton Panel ({FIYATLAR['osb2_18mm_piece_price']}€/adet) Adet:", value=_temp_osb2_18mm_count_val, min_value=0, disabled=floor_insulation_material_disabled, key="osb2_input")
    with col_floor_mats2[1]:
        _temp_galvanized_sheet_m2_val = st.session_state.galvanized_sheet_m2_val
        st.session_state.galvanized_sheet_m2_val = st.number_input(f"5mm Galvanizli Sac ({FIYATLAR['galvanized_sheet_m2_price']}€/m²) Alanı (m²):", value=_temp_galvanized_sheet_m2_val, step=0.1, min_value=0.0, disabled=floor_insulation_material_disabled, key="galvanized_sheet_input")
    with col_floor_mats2[2]:
        pass

    _temp_insulation_wall_val = st.session_state.insulation_wall_val
    st.session_state.insulation_wall_val = st.checkbox("Duvar Yalıtımı Dahil Et (10€/m²)", value=_temp_insulation_wall_val, key="wall_insulation_checkbox")
    
    # Yalıtım Malzemesi Seçimi (Taş Yünü / Cam Yünü)
    st.markdown("---")
    st.subheader("Yalıtım Malzemesi Seçimi")
    _temp_insulation_material_type_val = st.session_state.insulation_material_type_val
    st.session_state.insulation_material_type_val = st.radio(
        "Yalıtım Malzeme Tipi:",
        ['Taş Yünü', 'Cam Yünü'],
        index=['Taş Yünü', 'Cam Yünü'].index(_temp_insulation_material_type_val),
        key="insulation_material_type_select"
    )

    st.markdown("---")

    _temp_transportation_input_val = st.session_state.transportation_input_val
    st.session_state.transportation_input_val = st.checkbox("Nakliye Dahil Et (350€)", value=_temp_transportation_input_val, key="transportation_checkbox")
    _temp_heating_val = st.session_state.heating_val
    st.session_state.heating_val = st.checkbox("Yerden Isıtma Dahil Et (50€/m²)", value=_temp_heating_val, key="heating_checkbox")
    _temp_solar_val = st.session_state.solar_val
    st.session_state.solar_val = st.checkbox("Güneş Enerjisi Sistemi", value=_temp_solar_val, key="solar_checkbox")
    
    _temp_floor_covering_val = st.session_state.floor_covering_val
    st.session_state.floor_covering_val = st.selectbox("Zemin Kaplama Tipi:", ['Laminate Parquet', 'Ceramic'], index=['Laminate Parquet', 'Ceramic'].index(_temp_floor_covering_val), key="floor_covering_select")

    col14, col15 = st.columns(2)
    with col14:
        _temp_solar_capacity_val = st.session_state.solar_capacity_val # solar_capacity_val init at top
        solar_capacity_val = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not st.session_state.solar_val, key="solar_capacity_select", index=[5, 7.2, 11].index(_temp_solar_capacity_val)) # Use temp for value
    with col15:
        # solar_price_val is derived, not directly user input
        solar_price_val = solar_capacity_val * FIYATLAR['solar_per_kw'] if st.session_state.solar_val else 0.0
        st.session_state.solar_price_val = solar_price_val # Update session state
        st.number_input("Güneş Enerjisi Fiyatı (€):", value=st.session_state.solar_price_val, disabled=True, key="solar_price_display")

    _temp_wheeled_trailer_val = st.session_state.wheeled_trailer_val
    st.session_state.wheeled_trailer_val = st.checkbox("Tekerlekli Römork", value=_temp_wheeled_trailer_val, key="trailer_checkbox")
    _temp_wheeled_trailer_price_input_val = st.session_state.wheeled_trailer_price_input_val
    st.session_state.wheeled_trailer_price_input_val = st.number_input("Römork Fiyatı (€):", value=_temp_wheeled_trailer_price_input_val, step=0.1, min_value=0.0, disabled=not st.session_state.wheeled_trailer_val, key="trailer_price_input")

    # --- Financial Settings Section ---
    st.markdown("<div class='section-title'>FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
    profit_rate_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
    _temp_profit_rate_val_tuple = st.session_state.profit_rate_val_tuple 
    _temp_profit_rate_index = profit_rate_options.index(_temp_profit_rate_val_tuple)
    st.session_state.profit_rate_val_tuple = st.selectbox("Kar Oranı:", options=profit_rate_options, format_func=lambda x: x[0], index=_temp_profit_rate_index, key="profit_rate_select")
    profit_rate_val = st.session_state.profit_rate_val_tuple[1]
    st.markdown(f"<div>KDV Oranı: {VAT_RATE*100:.0f}% (Sabit)</div>", unsafe_allow_html=True)

    # --- Customer Notes Section ---
    st.markdown("<div class='section-title'>MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR</div>", unsafe_allow_html=True)
    _temp_customer_notes_val = st.session_state.customer_notes_val
    st.session_state.customer_notes_val = st.text_area("Müşteri Notları:", value=_temp_customer_notes_val, key="customer_notes_textarea")

    # --- PDF Language Selection ---
    _temp_pdf_language_selector_val_tuple = st.session_state.pdf_language_selector_val_tuple 
    _temp_pdf_language_index = [('English-Greek', 'en_gr'), ('Turkish', 'tr')].index(_temp_pdf_language_selector_val_tuple)
    st.session_state.pdf_language_selector_val_tuple = st.selectbox("Teklif PDF Dili:", options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')], format_func=lambda x: x[0], index=_temp_pdf_language_index, key="pdf_language_select")
    pdf_language_selector_val = st.session_state.pdf_language_selector_val_tuple[1]


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
            aether_package_total_cost = 0.0

            # --- Aether Living Paket Seçimine Göre Maliyet Ekleme Mantığı ---
            # Hesaplamalar artık st.session_state'ten gelen değerlere göre yapılacak
            if st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
                # Yapı (Metal iskelet, koruyucu otomotiv boyası)
                basics_100x100_count = math.ceil(floor_area * (12 / 27.0))
                basics_50x50_count = math.ceil(floor_area * (6 / 27.0))
                
                if basics_100x100_count > 0:
                    costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (100x100x3)', 'Quantity': f"{basics_100x100_count} adet ({basics_100x100_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'], 'Total (€)': calculate_rounded_up_cost(basics_100x100_count * FIYATLAR['steel_profile_100x100x3'])})
                    aether_package_total_cost += calculate_rounded_up_cost(basics_100x100_count * FIYATLAR['steel_profile_100x100x3'])
                if basics_50x50_count > 0:
                    costs.append({'Item': FIYATLAR['steel_skeleton_info'] + ' (50x50x2)', 'Quantity': f"{basics_50x50_count} adet ({basics_50x50_count * 6:.1f}m)", 'Unit Price (€)': FIYATLAR['steel_profile_50x50x2'], 'Total (€)': calculate_rounded_up_cost(basics_50x50_count * FIYATLAR['steel_profile_50x50x2'])})
                    aether_package_total_cost += calculate_rounded_up_cost(basics_50x50_count * FIYATLAR['steel_profile_50x50x2'])
                costs.append({'Item': FIYATLAR['protective_automotive_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

                # Dış/İç Kaplamalar (60mm EPS veya Poliüretan Sandviç Paneller (beyaz))
                sandwich_panel_60mm_cost = calculate_rounded_up_cost((wall_area + roof_area) * FIYATLAR["sandwich_panel_m2"])
                costs.append({'Item': FIYATLAR['60mm_eps_sandwich_panel_info'], 'Quantity': f"{wall_area + roof_area:.2f} m²", 'Unit Price (€)': FIYATLAR["sandwich_panel_m2"], 'Total (€)': sandwich_panel_60mm_cost})
                aether_package_total_cost += sandwich_panel_60mm_cost
                
                # Zemin (Galvanizli sac, yalıtım, Kontraplak/OSB zemin paneli, 12mm Laminat Parke)
                # Yalıtım seçimine göre Taşyünü veya Cam Yünü
                if st.session_state.insulation_material_type_val == 'Taş Yünü':
                    insulation_cost_general = calculate_rounded_up_cost(floor_area * FIYATLAR["insulation_per_m2"])
                    costs.append({'Item': FIYATLAR['insulation_info_general'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["insulation_per_m2"], 'Total (€)': insulation_cost_general})
                    aether_package_total_cost += insulation_cost_general

                    otb_stone_wool_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["otb_stone_wool_price"]) 
                    costs.append({'Item': FIYATLAR['otb_stone_wool_info_report'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["otb_stone_wool_price"], 'Total (€)': otb_stone_wool_cost})
                    aether_package_total_cost += otb_stone_wool_cost

                elif st.session_state.insulation_material_type_val == 'Cam Yünü':
                    num_glass_wool_packets = math.ceil(floor_area / GLASS_WOOL_M2_PER_PACKET)
                    insulation_cost_specific = calculate_rounded_up_cost(num_glass_wool_packets * FIYATLAR["glass_wool_5cm_packet_price"])
                    costs.append({'Item': FIYATLAR['glass_wool_5cm_packet_info_report'], 'Quantity': f"{num_glass_wool_packets} paket ({floor_area:.2f} m²)", 'Unit Price (€)': FIYATLAR["glass_wool_5cm_packet_price"], 'Total (€)': insulation_cost_specific})
                    aether_package_total_cost += insulation_cost_specific
                
                costs.append({'Item': FIYATLAR['galvanized_sheet_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["galvanized_sheet_m2_price"], 'Total (€)': calculate_rounded_up_cost(floor_area * FIYATLAR["galvanized_sheet_m2_price"])})
                costs.append({'Item': FIYATLAR['plywood_osb_floor_panel_info'], 'Quantity': f"{plywood_pieces_needed} adet", 'Unit Price (€)': FIYATLAR["plywood_piece"], 'Total (€)': calculate_rounded_up_cost(plywood_pieces_needed * FIYATLAR["plywood_piece"])})
                costs.append({'Item': FIYATLAR['12mm_laminate_parquet_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["laminate_flooring_m2_price"], 'Total (€)': calculate_rounded_up_cost(floor_area * FIYATLAR["laminate_flooring_m2_price"])})
                
                aether_package_total_cost += calculate_rounded_up_cost(floor_area * FIYATLAR["galvanized_sheet_m2_price"])
                aether_package_total_cost += calculate_rounded_up_cost(plywood_pieces_needed * FIYATLAR["plywood_piece"])
                aether_package_total_cost += calculate_rounded_up_cost(floor_area * FIYATLAR["laminate_flooring_m2_price"])

                # Mutfak/Banyo (İndüksiyonlu ocak, elektrikli batarya, mutfak evyesi, tam fonksiyonel banyo armutürleri)
                costs.append({'Item': FIYATLAR['induction_hob_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['electric_faucet_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['kitchen_sink_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['fully_functional_bathroom_fixtures_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                costs.append({'Item': FIYATLAR['kitchen_bathroom_countertops_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})


            elif st.session_state.aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
                # Premium pakete özel eklemeler (Standard özelliklere ek olarak)
                # Dış/İç Kaplamalar (Yüksek performanslı 100mm EPS veya Poliüretan İzotermik Paneller)
                sandwich_panel_100mm_cost = calculate_rounded_up_cost((wall_area + roof_area) * FIYATLAR["100mm_eps_isothermal_panel_unit_price"])
                costs.append({'Item': FIYATLAR['100mm_eps_isothermal_panel_info'], 'Quantity': f"{wall_area + roof_area:.2f} m²", 'Unit Price (€)': FIYATLAR["100mm_eps_isothermal_panel_unit_price"], 'Total (€)': sandwich_panel_100mm_cost})
                aether_package_total_cost += sandwich_panel_100mm_cost
                
                # Zemin: İşlenmiş çam zemin kaplaması (teras seçeneği) veya porselen fayans
                if st.session_state.terrace_laminated_wood_flooring_option_val:
                    terrace_laminated_cost = calculate_rounded_up_cost(floor_area * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'])
                    costs.append({'Item': FIYATLAR['treated_pine_floor_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'], 'Total (€)': terrace_laminated_cost})
                    aether_package_total_cost += terrace_laminated_cost
                elif st.session_state.porcelain_tiles_option_val:
                    porcelain_tiles_cost = calculate_rounded_up_cost(floor_area * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']))
                    costs.append({'Item': FIYATLAR['porcelain_tiles_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor']), 'Total (€)': porcelain_tiles_cost})
                    aether_package_total_cost += porcelain_tiles_cost
                else: # Varsayılan laminat parke
                    laminate_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["laminate_flooring_m2_price"])
                    costs.append({'Item': FIYATLAR['12mm_laminate_parquet_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR["laminate_flooring_m2_price"], 'Total (€)': laminate_cost})
                    aether_package_total_cost += laminate_cost
                
                # Mobilyalar: Destekleyici mobilyalı yatak başlığı
                if st.session_state.bedroom_set_option_val:
                    costs.append({'Item': FIYATLAR['supportive_headboard_furniture_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['bedroom_set_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['bedroom_set_total_price'])})
                    aether_package_total_cost += calculate_rounded_up_cost(FIYATLAR['bedroom_set_total_price'])
                
                # Tezgahlar: Fırçalanmış gri kale granit
                if st.session_state.brushed_granite_countertops_option_val:
                    granite_area_default = floor_area / 10 # Örnek m2
                    granite_cost = calculate_rounded_up_cost(granite_area_default * FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'])
                    costs.append({'Item': FIYATLAR['brushed_grey_granite_countertops_info'], 'Quantity': f"{granite_area_default:.2f} m²", 'Unit Price (€)': FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'], 'Total (€)': granite_cost})
                    aether_package_total_cost += granite_cost


            elif st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                # Elite pakete özel eklemeler (Premium özellikleri de içerir)
                # Dış Cephe (Knauf Aquapanel / Mavi Alçıpan + İşçilik)
                if st.session_state.exterior_cladding_m2_option_val:
                    # Mavi Alçıpan (Malzeme) maliyeti - Adet fiyatından m2'ye çevirme
                    mavi_alcipan_m2_price_converted = FIYATLAR['gypsum_board_blue_per_unit_price'] / GYPSUM_BOARD_UNIT_AREA_M2
                    mavi_alcipan_material_cost = calculate_rounded_up_cost(wall_area * mavi_alcipan_m2_price_converted)
                    costs.append({'Item': FIYATLAR['exterior_cladding_material_info'], 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': mavi_alcipan_m2_price_converted, 'Total (€)': mavi_alcipan_material_cost})
                    aether_package_total_cost += mavi_alcipan_material_cost

                    # Dış Cephe Kaplama İşçiliği maliyeti
                    exterior_cladding_labor_cost = calculate_rounded_up_cost(wall_area * FIYATLAR['exterior_cladding_labor_price_per_m2'])
                    costs.append({'Item': FIYATLAR['exterior_cladding_labor_info'], 'Quantity': f"{wall_area:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_cladding_labor_price_per_m2'], 'Total (€)': exterior_cladding_labor_cost})
                    aether_package_total_cost += exterior_cladding_labor_cost

                    costs.append({'Item': FIYATLAR['eps_styrofoam_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0}) # Bilgi kalemi
                    costs.append({'Item': FIYATLAR['knauf_mineralplus_insulation_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0}) # Bilgi kalemi
                
                # Dış cephe ahşap kaplama (Lambiri)
                if st.session_state.exterior_wood_cladding_m2_option_val and st.session_state.exterior_wood_cladding_m2_val > 0:
                    wood_cladding_cost = calculate_rounded_up_cost(st.session_state.exterior_wood_cladding_m2_val * FIYATLAR['exterior_wood_cladding_m2_price'])
                    costs.append({'Item': FIYATLAR['exterior_wood_cladding_lambiri_info'], 'Quantity': f"{st.session_state.exterior_wood_cladding_m2_val:.2f} m²", 'Unit Price (€)': FIYATLAR['exterior_wood_cladding_m2_price'], 'Total (€)': wood_cladding_cost})
                    aether_package_total_cost += wood_cladding_cost

                # İç Duvarlar (Knauf Guardex Alçıpan, saten sıva ve boya)
                if plasterboard_interior_calc or plasterboard_all_calc:
                    # Hesaplanan alçıpan alanı
                    interior_alcipan_area = 0
                    if plasterboard_interior_calc: # Eğer iç alçıpan seçiliyse
                        interior_alcipan_area += (wall_area / 2) + roof_area # Duvarların yarısı + tavan
                    if plasterboard_all_calc: # Eğer iç ve dış alçıpan seçiliyse (Heavy Steel için)
                        interior_alcipan_area += wall_area + roof_area # Duvarların tamamı + tavan

                    # Yeşil Alçıpan WC için kullanılıyorsa, toplam iç alçıpan alanından düşmeli
                    green_alcipan_area_for_elite = 0
                    if st.session_state.wc_ceramic_val and st.session_state.wc_ceramic_area_val > 0:
                        green_alcipan_area_for_elite = st.session_state.wc_ceramic_area_val
                        # Add green gypsum board specific cost
                        green_gypsum_board_adet = math.ceil(green_alcipan_area_for_elite / GYPSUM_BOARD_UNIT_AREA_M2)
                        green_gypsum_board_material_cost = calculate_rounded_up_cost(green_gypsum_board_adet * FIYATLAR['gypsum_board_green_per_unit_price'])
                        costs.append({'Item': FIYATLAR['gypsum_board_green_info'], 'Quantity': f"{green_gypsum_board_adet} adet ({green_alcipan_area_for_elite:.2f} m²)", 'Unit Price (€)': FIYATLAR['gypsum_board_green_per_unit_price'], 'Total (€)': green_gypsum_board_material_cost})
                        aether_package_total_cost += green_gypsum_board_material_cost

                    # Kalan iç alçıpan alanı için beyaz alçıpan veya Guardex kullanılır
                    remaining_interior_alcipan_area = interior_alcipan_area - green_alcipan_area_for_elite
                    if remaining_interior_alcipan_area > 0:
                        guardex_adet = math.ceil(remaining_interior_alcipan_area / GYPSUM_BOARD_UNIT_AREA_M2)
                        guardex_material_cost = calculate_rounded_up_cost(guardex_adet * FIYATLAR["plasterboard_material_m2"]) # plasterboard_material_m2 kullanıldı
                        costs.append({'Item': FIYATLAR['knauf_guardex_gypsum_board_info'], 'Quantity': f"{guardex_adet} adet ({remaining_interior_alcipan_area:.2f} m²)", 'Unit Price (€)': FIYATLAR["plasterboard_material_m2"], 'Total (€)': guardex_material_cost})
                        aether_package_total_cost += guardex_material_cost

                    costs.append({'Item': FIYATLAR['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                    # Alçıpan işçiliği (tüm alçıpan alanı için)
                    total_alcipan_labor_area = wall_area + roof_area # Basitçe duvar ve tavan alanı olarak alalım
                    alcipan_labor_cost = calculate_rounded_up_cost(total_alcipan_labor_area * FIYATLAR["plasterboard_labor_m2_avg"])
                    costs.append({'Item': 'Alçıpan İşçiliği', 'Quantity': f'{total_alcipan_labor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["plasterboard_labor_m2_avg"], 'Total (€)': alcipan_labor_cost})
                    aether_package_total_cost += alcipan_labor_cost

                    # Alçıpan detay malzemeleri
                    costs.append({'Item': FIYATLAR['tn25_screws_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['tn25_screws_price_per_unit'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['tn25_screws_price_per_unit'] * (total_alcipan_labor_area / 10))}) # Örnek miktar
                    costs.append({'Item': FIYATLAR['cdx400_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['cdx400_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['cdx400_material_price'] * (total_alcipan_labor_area / 20))}) # Örnek miktar
                    costs.append({'Item': FIYATLAR['ud_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['ud_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['ud_material_price'] * (total_alcipan_labor_area / 5))}) # Örnek miktar
                    costs.append({'Item': FIYATLAR['oc50_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['oc50_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['oc50_material_price'] * (total_alcipan_labor_area / 15))}) # Örnek miktar
                    costs.append({'Item': FIYATLAR['oc100_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['oc100_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['oc100_material_price'] * (total_alcipan_labor_area / 25))}) # Örnek miktar
                    costs.append({'Item': FIYATLAR['ch100_material_info_report'], 'Quantity': 'N/A', 'Unit Price (€)': FIYATLAR['ch100_material_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['ch100_material_price'] * (total_alcipan_labor_area / 25))}) # Örnek miktar

                # Zemin: Beton panel zemin (isteğe bağlı yerden ısıtma)
                if st.session_state.concrete_panel_floor_option_val:
                    concrete_panel_cost = calculate_rounded_up_cost(floor_area * FIYATLAR['concrete_panel_floor_price_per_m2'])
                    costs.append({'Item': FIYATLAR['concrete_panel_floor_info'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'], 'Total (€)': concrete_panel_cost})
                    aether_package_total_cost += concrete_panel_cost
                if st.session_state.heating_val:
                    total_heating_cost = calculate_rounded_up_cost(floor_area * FIYATLAR["floor_heating_m2"])
                    costs.append({'Item': 'Yerden Isıtma Sistemi', 'Quantity': f'{floor_area:.2f} m²', 'Unit Price (€)': FIYATLAR["floor_heating_m2"], 'Total (€)': total_heating_cost})
                    aether_package_total_cost += total_heating_cost
                
                # Armatürler: Premium bataryalar
                if st.session_state.premium_faucets_option_val:
                    costs.append({'Item': FIYATLAR['premium_faucets_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['premium_faucets_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['premium_faucets_total_price'])})
                    aether_package_total_cost += calculate_rounded_up_cost(FIYATLAR['premium_faucets_total_price'])

                # Yükseltilmiş mutfak cihazları (örn. entegre buzdolabı) - Zaten beyaz eşya içinde değerlendiriliyor, ayrıca eklenmeyecek.
                if st.session_state.integrated_fridge_option_val:
                    costs.append({'Item': FIYATLAR['integrated_refrigerator_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})

                # Mobilyalar: Entegre özel tasarım mobilyalar, seçkin oturma grupları
                if st.session_state.designer_furniture_option_val:
                    costs.append({'Item': FIYATLAR['integrated_custom_furniture_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['designer_furniture_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['designer_furniture_total_price'])})
                    aether_package_total_cost += calculate_rounded_up_cost(FIYATLAR['designer_furniture_total_price'])
                if st.session_state.italian_sofa_option_val:
                    costs.append({'Item': FIYATLAR['italian_sofa_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['italian_sofa_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['italian_sofa_total_price'])})
                    aether_package_total_cost += calculate_rounded_up_cost(FIYATLAR['italian_sofa_total_price'])
                if st.session_state.inclass_chairs_option_val and st.session_state.inclass_chairs_count_val > 0:
                    inclass_chairs_cost = calculate_rounded_up_cost(st.session_state.inclass_chairs_count_val * FIYATLAR['inclass_chairs_unit_price'])
                    costs.append({'Item': FIYATLAR['inclass_chairs_info'], 'Quantity': f"{st.session_state.inclass_chairs_count_val} adet", 'Unit Price (€)': FIYATLAR['inclass_chairs_unit_price'], 'Total (€)': inclass_chairs_cost})
                    aether_package_total_cost += inclass_chairs_cost
                
                # Teknoloji: Akıllı ev sistemleri, gelişmiş güvenlik kamerası ön kurulumu
                if st.session_state.smart_home_systems_option_val:
                    costs.append({'Item': FIYATLAR['smart_home_systems_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['smart_home_systems_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['smart_home_systems_total_price'])})
                    aether_package_total_cost += calculate_rounded_up_cost(FIYATLAR['smart_home_systems_total_price'])
                if st.session_state.security_camera_option_val:
                    costs.append({'Item': FIYATLAR['security_camera_info'], 'Quantity': 1, 'Unit Price (€)': FIYATLAR['security_camera_total_price'], 'Total (€)': calculate_rounded_up_cost(FIYATLAR['security_camera_total_price'])})
                    aether_package_total_cost += calculate_rounded_up_cost(FIYATLAR['security_camera_total_price'])
            
            # Ana Maliyet Hesaplamaları
            # Paket seçiliyse house_subtotal, paketin otomatik toplanan maliyeti olur.
            # Aksi takdirde, diğer manuel seçilenlerin toplamı olur.
            if st.session_state.aether_package_choice != 'Yok':
                house_subtotal = aether_package_total_cost
            else: # Eğer Aether Living paketi seçili değilse, mevcut manuel seçimlere göre topla
                house_subtotal = sum([item['Total (€)'] for item in costs if 'Solar' not in item['Item']])

            waste_cost = calculate_rounded_up_cost(house_subtotal * FIRE_RATE)
            total_house_cost = calculate_rounded_up_cost(house_subtotal + waste_cost)
            profit = calculate_rounded_up_cost(total_house_cost * profit_rate_val)
            house_vat_base = calculate_rounded_up_cost(total_house_cost + profit)
            house_vat = calculate_rounded_up_cost(house_vat_base * VAT_RATE)
            house_sales_price = calculate_rounded_up_cost(house_vat_base + house_vat)
            
            solar_cost = 0 # solar_cost'u her zaman tanımlı hale getir (NameError düzeltmesi)
            if st.session_state.solar_val:
                solar_cost = calculate_rounded_up_cost(st.session_state.solar_capacity_val * FIYATLAR['solar_per_kw']) # Use st.session_state.solar_capacity_val
                costs.append({'Item': f'Güneş Enerjisi Sistemi ({st.session_state.solar_capacity_val} kW)', 'Quantity': 1, 'Unit Price (€)': FIYATLAR['solar_per_kw'], 'Total (€)': solar_cost}) # Unit Price is per kW

            total_sales_price = calculate_rounded_up_cost(house_sales_price + solar_cost)

            delivery_duration_business_days = math.ceil((floor_area / 27.0) * 35)
            if delivery_duration_business_days < 10: delivery_duration_business_days = 10
            
            annual_income_tax_calc = calculate_rounded_up_cost((profit + waste_cost) * ANNUAL_INCOME_TAX_RATE)

            financial_summary_data = [
                ["Ara Toplam (Tüm Kalemler, Güneş Dahil)", sum([item['Total (€)'] for item in costs])],
                [f"Atık Maliyeti ({FIRE_RATE*100:.0f}%) (Sadece Ev için)", waste_cost],
                ["Toplam Maliyet (Ev + Atık + + Güneş)", total_house_cost + solar_cost],
                [f"Kar ({st.session_state.profit_rate_val_tuple[0]}) (Sadece Ev için)", profit], # Use st.session_state for profit rate display
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
                'address': customer_address.strip() or "", 'phone': customer_phone.strip() or "",
                'email': customer_email.strip() or "", 'id_no': customer_id_no.strip() or "" # customer_city eksikti
            }

            project_details_result = {
                'width': width_val, 'length': length_val, 'height': height_val, 'area': floor_area,
                'structure_type': structure_type_val,
                'plasterboard_interior': plasterboard_interior_calc,
                'plasterboard_all': plasterboard_all_calc,
                'osb_inner_wall': osb_inner_wall_calc,
                'insulation_floor': st.session_state.insulation_floor_val,
                'insulation_wall': st.session_state.insulation_wall_val,
                'window_count': window_input_val, 'window_size': window_size_val,
                'window_door_color': window_door_color_val,
                'sliding_door_count': sliding_door_input_val, 'sliding_door_size': sliding_door_size_val,
                'wc_window_count': wc_window_input_val, 'wc_window_size': wc_window_size_val,
                'wc_sliding_door_count': wc_sliding_door_input_val, 'wc_sliding_door_size': wc_sliding_door_size_val,
                'door_count': door_input_val, 'door_size': door_size_val,
                'kitchen_type_display_en_gr': kitchen_type_display_en_gr,
                'kitchen_type_display_tr': kitchen_type_display_tr,
                'kitchen': kitchen_input_val,
                'shower': shower_input_val,
                'wc_ceramic': wc_ceramic_input_val, 'wc_ceramic_area': wc_ceramic_area_val,
                'electrical': electrical_installation_input_val, 'plumbing': plumbing_installation_input_val,
                'transportation': st.session_state.transportation_input_val, 'heating': st.session_state.heating_val,
                'solar': st.session_state.solar_val, 'solar_kw': solar_capacity_val, 'solar_price': solar_cost,
                'vat_rate': VAT_RATE, 'profit_rate': profit_rate_val,
                'room_configuration': room_config_val,
                'wheeled_trailer_included': st.session_state.wheeled_trailer_val,
                'wheeled_trailer_price': st.session_state.wheeled_trailer_price_input_val,
                'sales_price': total_sales_price,
                'delivery_duration_business_days': delivery_duration_business_days,
                'welding_labor_type': welding_labor_option_val,
                'facade_sandwich_panel_included': facade_sandwich_panel_calc,
                'floor_covering_type': st.session_state.floor_covering_val,
                'skirting_length_val': st.session_state.skirting_count_val,
                'laminate_flooring_m2_val': st.session_state.laminate_flooring_m2_val,
                'under_parquet_mat_m2_val': st.session_state.under_parquet_mat_m2_val,
                'osb2_count_val': st.session_state.osb2_count_val, # Changed from osb2_18mm_count_val
                'galvanized_sheet_m2_val': st.session_state.galvanized_sheet_m2_val,
                
                # Yeni Aether Living Opsiyonları için değerler (UI'dan kaldırılsa da mantıkta kullanılacak ve rapora eklenecek)
                'aether_package_choice': st.session_state.aether_package_choice,
                'exterior_cladding_m2_option': st.session_state.exterior_cladding_m2_option_val,
                'exterior_cladding_m2_val': exterior_cladding_m2_val,
                'exterior_wood_cladding_m2_option': st.session_state.exterior_wood_cladding_m2_option_val,
                'exterior_wood_cladding_m2_val': exterior_wood_cladding_m2_val,
                'porcelain_tiles_option': st.session_state.porcelain_tiles_option_val,
                'porcelain_tiles_m2_val': porcelain_tiles_m2_val,
                'concrete_panel_floor_option': st.session_state.concrete_panel_floor_option_val,
                'concrete_panel_floor_m2_val': concrete_panel_floor_m2_val,
                'bedroom_set_option': st.session_state.bedroom_set_option_val,
                'sofa_option': st.session_state.sofa_option_val,
                'smart_home_systems_option': st.session_state.smart_home_systems_option_val,
                'security_camera_option': st.session_state.security_camera_option_val,
                'white_goods_fridge_tv_option': st.session_state.white_goods_fridge_tv_option_val,
                'premium_faucets_option': st.session_state.premium_faucets_option_val,
                'integrated_fridge_option': st.session_state.integrated_fridge_option_val,
                'designer_furniture_option': st.session_state.designer_furniture_option_val,
                'italian_sofa_option': st.session_state.italian_sofa_option_val,
                'inclass_chairs_option': st.session_state.inclass_chairs_option_val,
                'inclass_chairs_count': st.session_state.inclass_chairs_count_val,
                'brushed_granite_countertops_option': st.session_state.brushed_granite_countertops_option_val,
                'brushed_granite_countertops_m2_val': st.session_state.brushed_granite_countertops_m2_val,
                'terrace_laminated_wood_flooring_option': terrace_laminated_wood_flooring_option_val,
                'terrace_laminated_wood_flooring_m2_val': terrace_laminated_wood_flooring_m2_val,
                'insulation_material_type': insulation_material_type_val,
            }

            # --- Display Results in Streamlit ---
            st.subheader("Maliyet Detayları (Dahili Rapor)")
            st.dataframe(pd.DataFrame(costs).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            if not pd.DataFrame(profile_analysis_details).empty and project_details_result['structure_type'] == 'Light Steel':
                st.subheader("Çelik Profil Detaylı Analizi (Dahili Rapor)")
                st.dataframe(pd.DataFrame(profile_analysis_details).style.format({'Unit Price (€)': "€{:,.2f}", 'Total (€)': "€{:,.2f}"}), use_container_width=True)

            st.subheader("Finansal Özet (Dahili Rapor)")
            st.dataframe(pd.DataFrame(financial_summary_data).set_index('Item'), use_container_width=True) # financial_summary_data is already formatted

            # --- PDF Generation and Download Links ---
            st.markdown("---")
            st.subheader("PDF Çıktıları")
            
            logo_data_b64 = get_company_logo_base64(COMPANY_INFO["logo_url"]) # Assuming logo_url is in COMPANY_INFO

            col_pdf1, col_pdf2, col_pdf3 = st.columns(3)

            with col_pdf1:
                internal_pdf_buffer = create_internal_cost_report_pdf(
                    pd.DataFrame(costs),
                    pd.DataFrame(financial_summary_data), # Pass the DataFrame directly
                    pd.DataFrame(profile_analysis_details),
                    project_details_result,
                    customer_info_result,
                    logo_data_b64
                )
                st.download_button(
                    label="Dahili Maliyet Raporu İndir (Türkçe)",
                    data=internal_pdf_buffer.getvalue(), # Get value from buffer
                    file_name=f"Internal_Cost_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

            with col_pdf2:
                # Musteri teklifi PDF
                customer_pdf_buffer = create_customer_proposal_pdf_tr(
                    house_sales_price,
                    solar_cost, # Already derived as solar_cost, not solar_price_val from session_state
                    total_sales_price,
                    project_details_result,
                    customer_notes_val,
                    customer_info_result,
                    logo_data_b64
                )
                st.download_button(
                    label="Müşteri Teklifi İndir (Türkçe)",
                    data=customer_pdf_buffer.getvalue(), # Get value from buffer
                    file_name=f"Customer_Proposal_TR_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            with col_pdf3:
                # Sales contract PDF
                sales_contract_pdf_buffer = create_sales_contract_pdf(
                    customer_info_result,
                    house_sales_price,
                    solar_cost, # Already derived as solar_cost
                    project_details_result,
                    COMPANY_INFO,
                    logo_data_b64
                )
                st.download_button(
                    label="Satış Sözleşmesi İndir",
                    data=sales_contract_pdf_buffer.getvalue(), # Get value from buffer
                    file_name=f"Sales_Contract_{customer_info_result['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Bir hata oluştu: {e}")
            st.exception(e) # Display full traceback for debugging

# --- Start the Streamlit app ---
if __name__ == "__main__":
    run_streamlit_app()
