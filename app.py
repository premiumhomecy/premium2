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
LOGO_URL = "https://drive.google.com/uc?export=download&id=1RD27Gas035iUqe4Ucl3phFwxZPWZPWzn"
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
    "steel_profile_hea160": 155.00,
    # Material Prices (Base)
    "heavy_steel_m2": 400.00,
    "sandwich_panel_m2": 22.00, # PM'deki genel Sandviç Panel m2 fiyatı (60mm EPS için kullanılabilir)
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
    "wc_ceramic_m2_labor": 20.00,   # Porselen fayans için de kullanılacak işçilik m2 fiyatı
    "electrical_per_m2": 25.00,
    "plumbing_per_m2": 25.00,
    "osb_piece": 12.00, # OSB (plywood türü duvar ürünü) için parça fiyatı
    "insulation_per_m2": 5.00, # Genel Yalıtım
    # Labor Prices
    "welding_labor_m2_standard": 160.00,
    "welding_labor_m2_trmontaj": 20.00,
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00, # Alçıpan malzeme m2 fiyatı (genel)
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
    "white_goods_total_price": 800.00, # Buzdolabı ve TV dahil
    "sofa_total_price": 400.00,
    "security_camera_total_price": 650.00,
    "exterior_cladding_labor_price_per_m2": 150.00, # Knauf Aquapanel, vb. için M2 bazlı İŞÇİLİK fiyatı
    "bedroom_set_total_price": 800.00,
    "terrace_laminated_wood_flooring_price_per_m2": 40.00, # İşlenmiş çam zemin kaplama (teras) m2 fiyatı
    "concrete_panel_floor_price_per_m2": 50.00,
    "premium_faucets_total_price": 200.00,
    "designer_furniture_total_price": 1000.00,
    "italian_sofa_total_price": 800.00,
    "inclass_chairs_unit_price": 150.00, # Tane başı fiyat
    "exterior_wood_cladding_m2_price": 150.00, # Dış cephe ahşap kaplama (işçilik ve malzeme dahil m2)
    "brushed_grey_granite_countertops_price_m2_avg": 425.00, # Ortalama m2 fiyatı
    "100mm_eps_isothermal_panel_unit_price": 27.00, # 100mm Yüksek Performanslı Panellerin m2 fiyatı (tahmini)

    # Alçıpan modellerinin birim fiyatları (Ivan'dan gelen ve güncellenen)
    "gypsum_board_white_per_unit_price": 8.65, # adet. İç cephe için kullanılacak
    "gypsum_board_green_per_unit_price": 11.95, # adet. Banyo/WC için kullanılacak
    "gypsum_board_blue_per_unit_price": 22.00, # Knauf Aquapanel Mavi Alçıpan adet fiyatı
    
    # Diğer malzeme birim fiyatları (ön ek kaldırıldı)
    "otb_stone_wool_price": 19.80, # Taşyünü fiyatı (birim/adet), OTB
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
    "gypsum_board_blue_info": "Mavi Alçıpan (Dış Cephe / Knauf Aquapanel)", # Bilgi güncellendi
    "knauf_aquapanel_gypsum_board_info": "Knauf Aquapanel Alçıpan", # Ayrı bir bilgi kalemi olarak kalabilir
    "exterior_cladding_labor_info": "Dış Cephe Kaplama İşçiliği", # Yeni bilgi kalemi
    "exterior_cladding_material_info": "Dış Cephe Kaplama Malzemesi (Knauf Aquapanel / Mavi Alçıpan)", # Yeni bilgi kalemi
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
    "electrical_lighting_fixtures_info": "İç Aydınlatma Armutürleri (LED Spots / Tavan Lambası)",
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
    canvas.drawCentredString(doc.width/2 + 15*mm + doc.leftMargin, 14*mm, catalog_text) # Adjusted position
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

def _create_solar_appendix_elements_tr(styles):
    """Generates elements for Solar Energy System appendix (Turkish)."""
    heading_style = styles['Heading']
    normal_tr_style = styles['NormalTR']
    elements = [
        PageBreak(),
        Paragraph("EK B: GÜNEŞ ENERJİ SİSTEMİ", heading_style),
        Spacer(1, 8*mm),
        Paragraph(f"Projeye dahil edilen <b>{st.session_state.solar_capacity_val} kW</b> Güneş Enerji Sistemi'nin detayları aşağıdadır. Bu sistemin bedeli, ana ev ödeme planından ayrı olarak faturalandırılacaktır.", normal_tr_style), # Use session_state
        Spacer(1, 8*mm),
    ]
    solar_materials = [
        ["<b>Bileşen</b>", "<b>Açıklama</b>"],
        ["Güneş Panelleri", f"{st.session_state.solar_capacity_val} kW Yüksek Verimli Monokristal Panel"], # Use session_state
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
    elements.append(Paragraph(format_currency(st.session_state.solar_price_val), price_total_style)) # Use session_state
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
            building_structure_table_data.append([Paragraph('<b>Interior Walls:</b>', styles['NormalBilingual']), Paragraph(INTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Roof:</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Exterior Walls:</b>', styles['NormalBilingual']), Paragraph(EXTERIOR_WALLS_DESCRIPTION_EN_GR, styles['NormalBilingual'])]) # Changed from normal style to bilingual
    else: # Heavy Steel
        building_structure_table_data.append([Paragraph('<b>Construction Type / Τύπος Κατασκευής</b>', styles['NormalBilingual']), Paragraph('Heavy Steel', styles['NormalBilingual'])])
        building_structure_table_data.append([Paragraph('<b>Steel Structure Details:</b>', styles['NormalBilingual']), Paragraph(HEAVY_STEEL_BUILDING_STRUCTURE_EN_GR, styles['NormalBilingual'])]) # Changed to normal style to bilingual
        building_structure_table_data.append([Paragraph('<b>Roof:</b>', styles['NormalBilingual']), Paragraph(ROOF_DESCRIPTION_EN_GR, styles['NormalBilingual'])]) # Changed to normal style to bilingual
    
    construction_materials_table = Table(building_structure_table_data, colWidths=[60*mm, 110*mm])
    construction_materials_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
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

    # --- Sayfa Sonu: Teknik Özellikler Bölümünün Kalanı Yeni Sayfada ---
    elements.append(PageBreak())

    # Diğer Teknik Özellikler (Mutfak, Duş/WC, Elektrik, Sıhhi Tesisat, Ekstra Genel İlaveler)
    elements.append(Paragraph("ADDITIONAL TECHNICAL FEATURES / ΠΡΟΣΘΕΤΑ ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", styles['Heading'])) # Yeni başlık

    other_features_table_data = []
    
    # Mutfak ve Duş/WC (eğer pakete dahil değilse ve seçiliyse)
    if project_details['kitchen']:
        other_features_table_data.append([Paragraph('<b>Kitchen / Κουζίνα</b>', styles['NormalBilingual']), Paragraph(project_details['kitchen_type_display_en_gr'], styles['NormalBilingual'])])
    if project_details['shower']:
        other_features_table_data.append([Paragraph('<b>Shower/WC / Ντους/WC</b>', styles['NormalBilingual']), Paragraph(get_yes_no_empty(project_details['shower']), styles['NormalBilingual'])])
    
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
    
    # Aether Living'e özel eklenenler (UI'dan kaldırılsa da raporlarda yer almalı)
    if project_details['smart_home_systems_option']:
        extra_general_additions_list_en_gr.append(f"Smart Home Systems: {get_yes_no_en(project_details['smart_home_systems_option'])}")
    if project_details['white_goods_fridge_tv_option']:
        extra_general_additions_list_en_gr.append(f"White Goods (Fridge, TV): {get_yes_no_en(project_details['white_goods_fridge_tv_option'])}")
    if project_details['sofa_option']:
        extra_general_additions_list_en_gr.append(f"Sofa: {get_yes_no_en(project_details['sofa_option'])}")
    if project_details['security_camera_option']:
        extra_general_additions_list_en_gr.append(f"Security Camera Pre-Installation: {get_yes_no_en(project_details['security_camera_option'])}")
    if project_details['exterior_cladding_m2_option']:
        extra_general_additions_list_en_gr.append(f"Exterior Cladding: Yes ({project_details['exterior_cladding_m2_val']:.2f} m²)")
    if project_details['bedroom_set_option']:
        extra_general_additions_list_en_gr.append(f"Bedroom Set: {get_yes_no_en(project_details['bedroom_set_option'])}")
    if project_details['terrace_laminated_wood_flooring_option']:
        extra_general_additions_list_en_gr.append(f"Treated Pine Floor (Terrace Option): Yes ({project_details['terrace_laminated_wood_flooring_m2_val']:.2f} m²)")
    if project_details['porcelain_tiles_option']:
        extra_general_additions_list_en_gr.append(f"Porcelain Tiles: Yes ({project_details['porcelain_tiles_m2_val']:.2f} m²)")
    if project_details['concrete_panel_floor_option']:
        extra_general_additions_list_en_gr.append(f"Concrete Panel Floor: Yes ({project_details['concrete_panel_floor_m2_val']:.2f} m²)", )
    if project_details['premium_faucets_option']:
        extra_general_additions_list_en_gr.append(f"Premium Faucets: {get_yes_no_en(project_details['premium_faucets_option'])}")
    if project_details['integrated_fridge_option']:
        extra_general_additions_list_en_gr.append(f"Integrated Refrigerator: {get_yes_no_en(project_details['integrated_fridge_option'])}")
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
    
    # === st.session_state değişkenlerinin koşulsuz başlatılması ===
    # Bu blok, uygulamanın her yeniden çalışmasında tüm anahtarların var olmasını sağlar.
    # Bu, UnboundLocalError'ı kesin olarak çözen ana yaklaşımdır.
    if 'aether_package_choice' not in st.session_state: st.session_state.aether_package_choice = 'Yok'
    if 'kitchen_choice_radio' not in st.session_state: st.session_state.kitchen_choice_radio = 'Mutfak Yok'
    if 'shower_val' not in st.session_state: st.session_state.shower_val = False
    if 'wc_ceramic_val' not in st.session_state: st.session_state.wc_ceramic_val = False
    if 'wc_ceramic_area_val' not in st.session_state: st.session_state.wc_ceramic_area_val = 0.0
    if 'electrical_val' not in st.session_state: st.session_state.electrical_val = False
    if 'plumbing_val' not in st.session_state: st.session_state.plumbing_val = False
    if 'insulation_floor_val' not in st.session_state: st.session_state.insulation_floor_val = False
    if 'insulation_wall_val' not in st.session_state: st.session_state.insulation_wall_val = False
    if 'floor_covering_val' not in st.session_state: st.session_state.floor_covering_val = 'Laminate Parquet'
    if 'heating_val' not in st.session_state: st.session_state.heating_val = False
    if 'solar_val' not in st.session_state: st.session_state.solar_val = False
    if 'wheeled_trailer_val' not in st.session_state: st.session_state.wheeled_trailer_val = False
    if 'wheeled_trailer_price_input_val' not in st.session_state: st.session_state.wheeled_trailer_price_input_val = 0.0
    
    # Aether Living'e özel UI elementleri için varsayılanlar (artık manuel olarak kontrol edilecek)
    if 'exterior_cladding_m2_option_val' not in st.session_state: st.session_state.exterior_cladding_m2_option_val = False
    if 'exterior_cladding_m2_val' not in st.session_state: st.session_state.exterior_cladding_m2_val = 0.0
    if 'exterior_wood_cladding_m2_option_val' not in st.session_state: st.session_state.exterior_wood_cladding_m2_option_val = False
    if 'exterior_wood_cladding_m2_val' not in st.session_state: st.session_state.exterior_wood_cladding_m2_val = 0.0
    if 'porcelain_tiles_option_val' not in st.session_state: st.session_state.porcelain_tiles_option_val = False
    if 'porcelain_tiles_m2_val' not in st.session_state: st.session_state.porcelain_tiles_m2_val = 0.0
    if 'concrete_panel_floor_option_val' not in st.session_state: st.session_state.concrete_panel_floor_option_val = False
    if 'concrete_panel_floor_m2_val' not in st.session_state: st.session_state.concrete_panel_floor_m2_val = 0.0
    if 'bedroom_set_option_val' not in st.session_state: st.session_state.bedroom_set_option_val = False
    if 'sofa_option_val' not in st.session_state: st.session_state.sofa_option_val = False
    if 'smart_home_systems_option_val' not in st.session_state: st.session_state.smart_home_systems_option_val = False
    if 'security_camera_option_val' not in st.session_state: st.session_state.security_camera_option_val = False
    if 'white_goods_fridge_tv_option_val' not in st.session_state: st.session_state.white_goods_fridge_tv_option_val = False
    if 'premium_faucets_option_val' not in st.session_state: st.session_state.premium_faucets_option_val = False
    if 'integrated_fridge_option_val' not in st.session_state: st.session_state.integrated_fridge_option_val = False
    if 'designer_furniture_option_val' not in st.session_state: st.session_state.designer_furniture_option_val = False
    if 'italian_sofa_option_val' not in st.session_state: st.session_state.italian_sofa_option_val = False
    if 'inclass_chairs_option_val' not in st.session_state: st.session_state.inclass_chairs_option_val = False
    if 'inclass_chairs_count_val' not in st.session_state: st.session_state.inclass_chairs_count_val = 0
    if 'brushed_granite_countertops_option_val' not in st.session_state: st.session_state.brushed_granite_countertops_option_val = False
    if 'brushed_granite_countertops_m2_val' not in st.session_state: st.session_state.brushed_granite_countertops_m2_val = 0.0
    if 'insulation_material_type_val' not in st.session_state: st.session_state.insulation_material_type_val = 'Taş Yünü'
    
    if 'skirting_count_val' not in st.session_state: st.session_state.skirting_count_val = 0.0
    if 'laminate_flooring_m2_val' not in st.session_state: st.session_state.laminate_flooring_m2_val = 0.0
    if 'under_parquet_mat_m2_val' not in st.session_state: st.session_state.under_parquet_mat_m2_val = 0.0
    if 'osb2_18mm_count_val' not in st.session_state: st.session_state.osb2_18mm_count_val = 0
    if 'galvanized_sheet_m2_val' not in st.session_state: st.session_state.galvanized_sheet_m2_val = 0.0
    
    # --- Aether Living Paketlerine göre st.session_state değerlerini güncelle ---
    # Bu blok, st.session_state'in başlangıç değerlerini paketin özelliklerine göre override eder.
    # Sadece aether_package_choice'a göre varsayılanlar belirlenir, UI elemanları bu değerleri doğrudan kullanır.
    if st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
        st.session_state.kitchen_choice_radio = 'Standart Mutfak'
        st.session_state.shower_val = True
        st.session_state.electrical_val = True
        st.session_state.plumbing_val = True
        st.session_state.insulation_floor_val = True 
        st.session_state.insulation_wall_val = True
        st.session_state.floor_covering_val = 'Laminate Parquet'
        st.session_state.insulation_material_type_val = 'Taş Yünü' # Standard pakette taş yünü varsayım

        # Ek donanımlar için paket varsayılanları (True/False değerleri doğrudan atanır)
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
        
        # Premium pakete özel ek donanım varsayılanları
        st.session_state.bedroom_set_option_val = True
        st.session_state.brushed_granite_countertops_option_val = True
        st.session_state.terrace_laminated_wood_flooring_option_val = True # Premium Pakette geliyorsa
        
        # Diğer ek donanımlar varsayılan olarak kapalı
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

        # Elite pakete özel ek donanım varsayılanları
        st.session_state.exterior_cladding_m2_option_val = True # Knauf Aquapanel
        st.session_state.exterior_wood_cladding_m2_option_val = False # Ahşap kaplama isteğe bağlı
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
        
        # Elite pakette Premium'daki ek donanımlar da True olur (eğer çakışmıyorsa)
        st.session_state.bedroom_set_option_val = True
        st.session_state.brushed_granite_countertops_option_val = True
        # Teras laminat çam zemin, Elite'de beton zemin varsa default kapalı kalır
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

        # Değişkenler doğrudan st.session_state'ten okunup güncelleniyor
        _temp_plasterboard_interior_option_val = st.session_state.plasterboard_interior_option_val # Geçici yerel değişken
        st.session_state.plasterboard_interior_option_val = st.checkbox("İç Alçıpan Dahil Et", value=_temp_plasterboard_interior_option_val, disabled=plasterboard_interior_disabled, key="pb_int_checkbox")
        
        _temp_plasterboard_all_option_val = st.session_state.plasterboard_all_option_val # Geçici yerel değişken
        st.session_state.plasterboard_all_option_val = st.checkbox("İç ve Dış Alçıpan Dahil Et", value=_temp_plasterboard_all_option_val, disabled=plasterboard_all_disabled, key="pb_all_checkbox")
        
        # Calculation variables should directly read from session state
        plasterboard_interior_calc = st.session_state.plasterboard_interior_option_val
        plasterboard_all_calc = st.session_state.plasterboard_all_option_val

        # Logic for disabling Alçıpan types based on Structure Type
        if structure_type_val == 'Light Steel':
            plasterboard_all_calc = False 
        elif structure_type_val == 'Heavy Steel':
            plasterboard_interior_calc = False 

        osb_inner_wall_disabled = not (plasterboard_interior_calc or plasterboard_all_calc)
        _temp_osb_inner_wall_val = st.session_state.osb_inner_wall_option_val # Geçici yerel değişken
        st.session_state.osb_inner_wall_option_val = st.checkbox("İç Duvar OSB Malzemesi Dahil Et", value=_temp_osb_inner_wall_val, disabled=osb_inner_wall_disabled, key="osb_inner_checkbox")
        
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
        _temp_facade_sandwich_panel_val = st.session_state.facade_sandwich_panel_option_val # Geçici yerel değişken
        st.session_state.facade_sandwich_panel_option_val = st.checkbox("Dış Cephe Sandviç Panel Dahil Et (Ağır Çelik için)", value=_temp_facade_sandwich_panel_val, disabled=facade_sandwich_panel_disabled, key="facade_panel_checkbox")
        
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
        solar_capacity_val = st.selectbox("Güneş Enerjisi Kapasitesi (kW):", [5, 7.2, 11], disabled=not st.session_state.solar_val, key="solar_capacity_select")
    with col15:
        solar_price_val = solar_capacity_val * FIYATLAR['solar_per_kw'] if st.session_state.solar_val else 0.0
        st.number_input("Güneş Enerjisi Fiyatı (€):", value=solar_price_val, disabled=True, key="solar_price_display")

    _temp_wheeled_trailer_val = st.session_state.wheeled_trailer_val
    st.session_state.wheeled_trailer_val = st.checkbox("Tekerlekli Römork", value=_temp_wheeled_trailer_val, key="trailer_checkbox")
    _temp_wheeled_trailer_price_input_val = st.session_state.wheeled_trailer_price_input_val
    st.session_state.wheeled_trailer_price_input_val = st.number_input("Römork Fiyatı (€):", value=_temp_wheeled_trailer_price_input_val, step=0.1, min_value=0.0, disabled=not st.session_state.wheeled_trailer_val, key="trailer_price_input")

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
                    # insulation_per_m2 (genel) + otb_stone_wool_price (taşyünü birim/adet, m2'ye çevrilmeli)
                    # Buradaki otb_stone_wool_price'ın birimini kontrol etmek lazım. Eğer m2 ise direkt toplanır.
                    # Eğer adet ise, adet başına düşen maliyetin m2'ye çevrilmesi gerekir. Şu anki fiyatlar bölümünde 19.80 olarak adet/birim gözüküyor.
                    # Eğer bu maliyet tüm zemin alanına uygulanacaksa (insulation_per_m2 gibi), o zaman birimini m2 olarak kabul etmek daha mantıklı.
                    # Veya, sadece bir bilgi kalemi ise maliyete eklenmemeli. Kullanıcı daha önce "5cm probu clisteden çıkar. ) ile ayrılmış numaralar toplam adet fiyatlaridir silebilirsin(70,15,7,80,3,5).otb tasyunu bizde karşılığı mineralplus insulation olması gerekiyor." demişti.
                    # Bu durumda, otb_stone_wool_price (19.80) bir adet/birim fiyatı değil, m2 fiyatına eklenen bir "ek maliyet" olabilir.
                    # Geçici olarak insulation_per_m2 ile toplanır varsayıyorum, aksi takdirde maliyet çok düşük kalır.
                    insulation_cost_specific = calculate_rounded_up_cost(floor_area * (FIYATLAR["insulation_per_m2"] + FIYATLAR["otb_stone_wool_price"])) 
                    costs.append({'Item': FIYATLAR['otb_stone_wool_info_report'], 'Quantity': f"{floor_area:.2f} m²", 'Unit Price (€)': (FIYATLAR["insulation_per_m2"] + FIYATLAR["otb_stone_wool_price"]), 'Total (€)': insulation_cost_specific})
                    aether_package_total_cost += insulation_cost_specific
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

                # Mutfak/Banyo (İndüksiyonlu ocak, elektrikli batarya, mutfak evyesi, tam fonksiyonel banyo armatürleri)
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
                    # Mavi Alçıpan (Malzeme) maliyeti
                    mavi_alcipan_adet = math.ceil(wall_area / GYPSUM_BOARD_UNIT_AREA_M2)
                    mavi_alcipan_malzeme_cost = calculate_rounded_up_cost(mavi_alcipan_adet * FIYATLAR['gypsum_board_blue_per_unit_price'])
                    costs.append({'Item': FIYATLAR['exterior_cladding_material_info'], 'Quantity': f"{mavi_alcipan_adet} adet ({wall_area:.2f} m²)", 'Unit Price (€)': FIYATLAR['gypsum_board_blue_per_unit_price'], 'Total (€)': mavi_alcipan_malzeme_cost})
                    aether_package_total_cost += mavi_alcipan_malzeme_cost

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
                    if plasterboard_interior_calc:
                        interior_alcipan_area += (wall_area / 2) + roof_area # Duvarların yarısı + tavan
                    if plasterboard_all_calc:
                        interior_alcipan_area += wall_area + roof_area # Duvarların tamamı + tavan

                    guardex_adet = math.ceil(interior_alcipan_area / GYPSUM_BOARD_UNIT_AREA_M2)
                    guardex_material_cost = calculate_rounded_up_cost(guardex_adet * FIYATLAR["plasterboard_material_m2"]) # plasterboard_material_m2 kullanıldı
                    costs.append({'Item': FIYATLAR['knauf_guardex_gypsum_board_info'], 'Quantity': f"{guardex_adet} adet ({interior_alcipan_area:.2f} m²)", 'Unit Price (€)': FIYATLAR["plasterboard_material_m2"], 'Total (€)': guardex_material_cost})
                    costs.append({'Item': FIYATLAR['satin_plaster_paint_info'], 'Quantity': 'N/A', 'Unit Price (€)': 0.0, 'Total (€)': 0.0})
                    aether_package_total_cost += guardex_material_cost

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
                solar_cost = calculate_rounded_up_cost(solar_capacity_val * FIYATLAR['solar_per_kw'])
                costs.append({'Item': f'Güneş Enerjisi Sistemi ({solar_capacity_val} kW)', 'Quantity': 1, 'Unit Price (€)': solar_cost, 'Total (€)': solar_cost})

            total_sales_price = calculate_rounded_up_cost(house_sales_price + solar_cost)

            delivery_duration_business_days = math.ceil((floor_area / 27.0) * 35)
            if delivery_duration_business_days < 10: delivery_duration_business_days = 10
            
            annual_income_tax_calc = calculate_rounded_up_cost((profit + waste_cost) * ANNUAL_INCOME_TAX_RATE)

            financial_summary_data = [
                ["Ara Toplam (Tüm Kalemler, Güneş Dahil)", sum([item['Total (€)'] for item in costs])],
                [f"Atık Maliyeti ({FIRE_RATE*100:.0f}%) (Sadece Ev için)", waste_cost],
                ["Toplam Maliyet (Ev + Atık + + Güneş)", total_house_cost + solar_cost],
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
                'osb2_18mm_count_val': st.session_state.osb2_18mm_count_val,
                'galvanized_sheet_m2_val': st.session_state.galvanized_sheet_m2_val,
                
                # Yeni Aether Living Opsiyonları için değerler (UI'dan kaldırılsa da mantıkta kullanılacak ve rapora eklenecek)
                'aether_package_choice': st.session_state.aether_package_choice,
                'exterior_cladding_m2_option': st.session_state.exterior_cladding_m2_option_val,
                'exterior_cladding_m2_val': st.session_state.exterior_cladding_m2_val,
                'exterior_wood_cladding_m2_option': st.session_state.exterior_wood_cladding_m2_option_val,
                'exterior_wood_cladding_m2_val': st.session_state.exterior_wood_cladding_m2_val,
                'porcelain_tiles_option': st.session_state.porcelain_tiles_option_val,
                'porcelain_tiles_m2_val': st.session_state.porcelain_tiles_m2_val,
                'concrete_panel_floor_option': st.session_state.concrete_panel_floor_option_val,
                'concrete_panel_floor_m2_val': st.session_state.concrete_panel_floor_m2_val,
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
