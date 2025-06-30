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
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate, PageBreak
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
    return re.sub(r'[\u00A0\u200B]', ' ', text)

# --- Font Kaydı (Türkçe karakter desteği) ---
try:
    # FreeSans fontlarını kaydet
    pdfmetrics.registerFont(TTFont("FreeSans", "fonts/FreeSans.ttf"))
    pdfmetrics.registerFont(TTFont("FreeSans-Bold", "fonts/FreeSansBold.ttf"))
    pdfmetrics.registerFontFamily('FreeSans', normal='FreeSans', bold='FreeSans-Bold')
    MAIN_FONT = "FreeSans"
except Exception as e:
    st.warning(f"Font yükleme hatası: {e}. Helvetica kullanılacak.")
    MAIN_FONT = "Helvetica"

# --- Şirket Bilgileri ---
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
    "wc_ceramic_m2_material": 20.00,
    "wc_ceramic_m2_labor": 20.00,
    "electrical_per_m2": 25.00,
    "plumbing_per_m2": 25.00,
    "osb_piece": 12.00,
    "insulation_per_m2": 5.00,
    
    # Alçıpan Fiyatları
    "gypsum_board_white_per_unit_price": 8.65,
    "gypsum_board_green_per_unit_price": 11.95,
    "gypsum_board_blue_per_unit_price": 22.00,
    
    # Diğer Malzemeler
    "otb_stone_wool_price": 19.80,
    "glass_wool_5cm_packet_price": 19.68,
    "tn25_screws_price_per_unit": 5.58,
    "cdx400_material_price": 3.40,
    "ud_material_price": 1.59,
    "oc50_material_price": 2.20,
    "oc100_material_price": 3.96,
    "ch100_material_price": 3.55,
    
    # Bilgi Metinleri
    "steel_skeleton_info": "Metal iskelet",
    "protective_automotive_paint_info": "Koruyucu otomotiv boyası",
    "gypsum_board_white_info": "İç Alçıpan (Beyaz)",
    "gypsum_board_green_info": "Yeşil Alçıpan (Banyo/WC)",
    "gypsum_board_blue_info": "Mavi Alçıpan (Dış Cephe / Knauf Aquapanel)",
}

# Sabitler
FIRE_RATE = 0.05
VAT_RATE = 0.19
GYPSUM_BOARD_UNIT_AREA_M2 = 2.88  # 1.2m x 2.4m
GLASS_WOOL_M2_PER_PACKET = 10.0   # 1 paket cam yünü 10m² alan için
OSB_PANEL_AREA_M2 = 1.22 * 2.44   # OSB panel alanı

# --- Yardımcı Fonksiyonlar ---
def calculate_area(width, length, height):
    """Alan hesaplar: zemin, duvar, çatı"""
    floor_area = width * length
    wall_area = 2 * (width + length) * height
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Para birimini formatlar"""
    return f"€{value:,.2f}"

def calculate_rounded_up_cost(value):
    """Maliyeti yukarı yuvarlar"""
    return math.ceil(value * 100) / 100.0

# --- PDF Oluşturma Fonksiyonları ---
def create_internal_cost_report_pdf(costs_df, financial_df, project_details, customer_info):
    """Dahili maliyet raporu PDF'i oluşturur"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontName=f'{MAIN_FONT}-Bold',
        fontSize=16,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName=f'{MAIN_FONT}-Bold',
        fontSize=12,
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=MAIN_FONT,
        fontSize=10
    )
    
    elements = []
    
    # Başlık
    title = Paragraph("PREMIUM HOME - DAHİLİ MALİYET RAPORU", title_style)
    elements.append(title)
    
    # Müşteri bilgileri
    customer_text = f"<b>Müşteri:</b> {customer_info.get('name', 'GENEL')}"
    if customer_info.get('company'):
        customer_text += f" | <b>Şirket:</b> {customer_info['company']}"
    elements.append(Paragraph(customer_text, normal_style))
    
    elements.append(Spacer(1, 10))
    
    # Proje bilgileri
    project_text = (f"<b>Proje:</b> {project_details['width']}m x {project_details['length']}m x {project_details['height']}m "
                    f"| <b>Yapı Tipi:</b> {project_details['structure_type']} "
                    f"| <b>Konfigürasyon:</b> {project_details['room_config']}")
    elements.append(Paragraph(project_text, normal_style))
    
    elements.append(Spacer(1, 15))
    
    # Maliyet tablosu
    if not costs_df.empty:
        elements.append(Paragraph("MALİYET DETAYLARI", heading_style))
        
        cost_table_data = [['Kalem', 'Miktar', 'Birim Fiyat (€)', 'Toplam (€)']]
        for _, row in costs_df.iterrows():
            cost_table_data.append([
                row['Item'],
                row['Quantity'],
                format_currency(row['Unit Price (€)']) if row['Unit Price (€)'] != '' else '',
                format_currency(row['Total (€)'])
            ])
        
        # Tablo stilini ayarla
        cost_table = Table(cost_table_data, colWidths=[90*mm, 40*mm, 30*mm, 30*mm])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), f'{MAIN_FONT}-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(cost_table)
        elements.append(Spacer(1, 15))
    
    # Finansal özet
    elements.append(Paragraph("FİNANSAL ÖZET", heading_style))
    financial_data = [['Açıklama', 'Tutar (€)']]
    for _, row in financial_df.iterrows():
        financial_data.append([row['Item'], row['Amount (€)']])
    
    financial_table = Table(financial_data, colWidths=[120*mm, 40*mm])
    financial_table.setStyle(TableStyle([
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
    ]))
    elements.append(financial_table)
    
    # Alt bilgi
    elements.append(Spacer(1, 20))
    footer = Paragraph(
        f"<font size=8><i>{COMPANY_INFO['name']} | {COMPANY_INFO['phone']} | {COMPANY_INFO['website']}</i></font>", 
        normal_style
    )
    elements.append(footer)
    
    # PDF oluştur
    doc.build(elements)
    buffer.seek(0)
    return buffer

def create_customer_proposal_pdf_tr(house_price, solar_price, total_price, project_details, notes, customer_info):
    # Türkçe teklif PDF'i oluşturma
    pass

def create_sales_contract_pdf(customer_info, house_price, solar_price, project_details, company_info):
    # Satış sözleşmesi PDF'i oluşturma
    pass

# --- Streamlit Uygulaması ---
def run_streamlit_app():
    # Sayfa konfigürasyonu
    st.set_page_config(
        layout="wide", 
        page_title="Premium Home Cost Calculator",
        page_icon="🏠"
    )
    
    # Özel CSS
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif !important;
    }}
    
    .stApp {{
        background-color: #f8fafc;
    }}
    
    .stButton>button {{
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
        border: none;
        font-weight: 500;
    }}
    
    .stButton>button:hover {{
        background-color: #2c5282;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .section-title {{
        background-color: #3182ce;
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }}
    
    .warning {{
        color: #e53e3e;
        background-color: #fff5f5;
        padding: 10px 15px;
        border-radius: 6px;
        border: 1px solid #fed7d7;
        margin-bottom: 1rem;
    }}
    
    .stExpander > div {{
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    .stDataFrame {{
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    
    .stAlert {{
        border-radius: 8px;
    }}
    
    .footer {{
        text-align: center;
        padding: 1rem;
        color: #718096;
        font-size: 0.9rem;
        margin-top: 2rem;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🏠 Premium Home Cost Calculator")
    
    # --- Session State Başlatma ---
    INITIAL_STATE = {
        # Müşteri bilgileri
        'customer_name': "GENEL", 
        'customer_company': "", 
        'customer_address': "",
        'customer_phone': "", 
        'customer_email': "", 
        'customer_id_no': "",
        
        # Proje detayları
        'width': 10.0, 
        'length': 8.0, 
        'height': 2.6,
        'structure_type': 'Light Steel', 
        'room_config': 'Empty Model',
        'plasterboard_interior': False, 
        'plasterboard_all': False, 
        'osb_inner_wall': False,
        'facade_sandwich_panel': False, 
        'window_count': 4, 
        'window_size': "100x100 cm",
        'sliding_door_count': 0, 
        'sliding_door_size': "200x200 cm",
        'wc_window_count': 1, 
        'wc_window_size': "60x50 cm",
        'wc_sliding_door_count': 0, 
        'wc_sliding_door_size': "140x70 cm",
        'door_count': 2, 
        'door_size': "90x210 cm",
        
        # Ekipmanlar
        'kitchen_type': 'Mutfak Yok', 
        'shower': False, 
        'wc_ceramic': False, 
        'wc_ceramic_area': 0.0,
        'electrical': False, 
        'plumbing': False, 
        'insulation_floor': False, 
        'insulation_wall': False,
        'floor_covering': 'Laminate Parquet', 
        'heating': False, 
        'solar': False, 
        'solar_capacity': 5, 
        'transportation': False, 
        'wheeled_trailer': False, 
        'wheeled_trailer_price': 0.0, 
        
        # Finansal ayarlar
        'profit_rate': 0.20, 
        'customer_notes': "",
        
        # Malzeme seçimleri
        'insulation_material': 'Taş Yünü', 
        'skirting_length': 0.0, 
        'laminate_flooring': 0.0,
        'under_parquet_mat': 0.0, 
        'osb2_count': 0, 
        'galvanized_sheet': 0.0,
        
        # Aether Living paket
        'aether_package': 'Yok',
        
        # Çelik profil miktarları (Light Steel için)
        'profile_100x100': 0,
        'profile_100x50': 0,
        'profile_40x60': 0,
        'profile_50x50': 0,
        'profile_120x60x5mm': 0,
        'profile_HEA160': 0
    }
    
    # Session state'i başlat
    for key, value in INITIAL_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # --- Müşteri Bilgileri ---
    st.header("👤 Müşteri Bilgileri")
    with st.expander("Müşteri Detayları", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.customer_name = st.text_input("Ad Soyad*:", value=st.session_state.customer_name)
            st.session_state.customer_company = st.text_input("Şirket:", value=st.session_state.customer_company)
            st.session_state.customer_address = st.text_input("Adres:", value=st.session_state.customer_address)
        with col2:
            st.session_state.customer_phone = st.text_input("Telefon*:", value=st.session_state.customer_phone)
            st.session_state.customer_email = st.text_input("E-posta:", value=st.session_state.customer_email)
            st.session_state.customer_id_no = st.text_input("Kimlik/Pasaport No:", value=st.session_state.customer_id_no)
        
        st.markdown("<div class='warning'>* İşaretli alanlar zorunludur</div>", unsafe_allow_html=True)

    # --- Proje Detayları ---
    st.markdown("<div class='section-title'>🏗️ PROJE DETAYLARI</div>", unsafe_allow_html=True)
    
    with st.expander("Temel Ölçüler ve Yapı Tipi", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.width = st.number_input("Genişlik (m):", 
                                                    value=st.session_state.width, 
                                                    step=0.1, 
                                                    min_value=1.0)
            st.session_state.length = st.number_input("Uzunluk (m):", 
                                                     value=st.session_state.length, 
                                                     step=0.1, 
                                                     min_value=1.0)
            st.session_state.height = st.number_input("Yükseklik (m):", 
                                                     value=st.session_state.height, 
                                                     step=0.1, 
                                                     min_value=2.0)
            
        with col2:
            st.session_state.structure_type = st.radio("Yapı Tipi:", 
                ['Light Steel', 'Heavy Steel'], 
                index=0 if st.session_state.structure_type == 'Light Steel' else 1
            )
            
            room_options = [
                'Empty Model', '1 Room', '1 Room + Shower / WC', 
                '1 Room + Kitchen', '1 Room + Kitchen + WC',
                '1 Room + Shower / WC + Kitchen', '2 Rooms + Shower / WC + Kitchen',
                '3 Rooms + 2 Showers / WC + Kitchen'
            ]
            st.session_state.room_config = st.selectbox(
                "Oda Konfigürasyonu:", 
                room_options,
                index=room_options.index(st.session_state.room_config)
            )
    
    # --- Çelik Profil Miktarları ---
    if st.session_state.structure_type == 'Light Steel':
        st.markdown("<div class='section-title'>🔩 ÇELİK PROFİL MİKTARLARI</div>", unsafe_allow_html=True)
        with st.expander("Profil Detayları", expanded=True):
            cols = st.columns(3)
            with cols[0]:
                st.session_state.profile_100x100 = st.number_input("100x100x3 Adet:", 
                                                                   value=st.session_state.profile_100x100, 
                                                                   min_value=0)
            with cols[1]:
                st.session_state.profile_100x50 = st.number_input("100x50x3 Adet:", 
                                                                  value=st.session_state.profile_100x50, 
                                                                  min_value=0)
            with cols[2]:
                st.session_state.profile_40x60 = st.number_input("40x60x2 Adet:", 
                                                                 value=st.session_state.profile_40x60, 
                                                                 min_value=0)
            
            cols = st.columns(3)
            with cols[0]:
                st.session_state.profile_50x50 = st.number_input("50x50x2 Adet:", 
                                                                 value=st.session_state.profile_50x50, 
                                                                 min_value=0)
            with cols[1]:
                st.session_state.profile_120x60x5mm = st.number_input("120x60x5mm Adet:", 
                                                                      value=st.session_state.profile_120x60x5mm, 
                                                                      min_value=0)
            with cols[2]:
                st.session_state.profile_HEA160 = st.number_input("HEA160 Adet:", 
                                                                  value=st.session_state.profile_HEA160, 
                                                                  min_value=0)
    
    # --- Pencere ve Kapılar ---
    st.markdown("<div class='section-title'>🚪 PENCERELER VE KAPILAR</div>", unsafe_allow_html=True)
    with st.expander("Pencere ve Kapı Detayları", expanded=True):
        cols = st.columns(3)
        with cols[0]:
            st.session_state.window_count = st.number_input("Pencere Adedi:", 
                                                           value=st.session_state.window_count, 
                                                           min_value=0)
            st.session_state.window_size = st.text_input("Pencere Boyutu:", 
                                                        value=st.session_state.window_size)
        with cols[1]:
            st.session_state.sliding_door_count = st.number_input("Sürme Cam Kapı Adedi:", 
                                                                 value=st.session_state.sliding_door_count, 
                                                                 min_value=0)
            st.session_state.sliding_door_size = st.text_input("Sürme Kapı Boyutu:", 
                                                              value=st.session_state.sliding_door_size)
        with cols[2]:
            st.session_state.door_count = st.number_input("Ana Kapı Adedi:", 
                                                         value=st.session_state.door_count, 
                                                         min_value=0)
            st.session_state.door_size = st.text_input("Ana Kapı Boyutu:", 
                                                      value=st.session_state.door_size)
        
        cols = st.columns(2)
        with cols[0]:
            st.session_state.wc_window_count = st.number_input("WC Pencere Adedi:", 
                                                              value=st.session_state.wc_window_count, 
                                                              min_value=0)
            st.session_state.wc_window_size = st.text_input("WC Pencere Boyutu:", 
                                                           value=st.session_state.wc_window_size)
        with cols[1]:
            st.session_state.wc_sliding_door_count = st.number_input("WC Sürme Kapı Adedi:", 
                                                                    value=st.session_state.wc_sliding_door_count, 
                                                                    min_value=0)
            st.session_state.wc_sliding_door_size = st.text_input("WC Sürme Kapı Boyutu:", 
                                                                 value=st.session_state.wc_sliding_door_size)
    
    # --- Ek Donanımlar ---
    st.markdown("<div class='section-title'>⚙️ EK DONANIMLAR</div>", unsafe_allow_html=True)
    with st.expander("Ekipman Seçenekleri", expanded=True):
        # Aether Living Paket Seçimi
        aether_options = ['Yok', 'Aether Living | Loft Standard (BASICS)', 
                         'Aether Living | Loft Premium (ESSENTIAL)', 
                         'Aether Living | Loft Elite (LUXURY)']
        st.session_state.aether_package = st.radio(
            "Aether Living Paket Seçimi:", 
            aether_options,
            index=aether_options.index(st.session_state.aether_package),
            horizontal=True
        )
        
        # Paket seçimine göre otomatik ayarlamalar
        if st.session_state.aether_package == 'Aether Living | Loft Standard (BASICS)':
            st.session_state.kitchen_type = 'Standart Mutfak'
            st.session_state.shower = True
            st.session_state.electrical = True
            st.session_state.plumbing = True
            st.session_state.insulation_floor = True
            st.session_state.insulation_wall = True
        elif st.session_state.aether_package == 'Aether Living | Loft Premium (ESSENTIAL)':
            st.session_state.kitchen_type = 'Standart Mutfak'
            st.session_state.shower = True
            st.session_state.insulation_floor = True
            st.session_state.insulation_wall = True
        elif st.session_state.aether_package == 'Aether Living | Loft Elite (LUXURY)':
            st.session_state.kitchen_type = 'Special Design Mutfak'
            st.session_state.shower = True
            st.session_state.electrical = True
            st.session_state.plumbing = True
            st.session_state.insulation_floor = True
            st.session_state.insulation_wall = True
            st.session_state.heating = True
            st.session_state.solar = True
        
        # Temel ekipmanlar
        cols = st.columns(2)
        with cols[0]:
            st.session_state.kitchen_type = st.selectbox(
                "Mutfak Tipi:", 
                ['Mutfak Yok', 'Standart Mutfak', 'Special Design Mutfak'],
                index=['Mutfak Yok', 'Standart Mutfak', 'Special Design Mutfak'].index(st.session_state.kitchen_type)
            )
            
            st.session_state.shower = st.checkbox(
                "Duş/WC Dahil Et", 
                value=st.session_state.shower
            )
            
            st.session_state.wc_ceramic = st.checkbox(
                "WC Seramik Zemin/Duvar", 
                value=st.session_state.wc_ceramic
            )
            
            if st.session_state.wc_ceramic:
                st.session_state.wc_ceramic_area = st.number_input(
                    "WC Seramik Alanı (m²):", 
                    value=st.session_state.wc_ceramic_area, 
                    min_value=0.0, step=0.1
                )
        
        with cols[1]:
            st.session_state.electrical = st.checkbox(
                "Elektrik Tesisatı", 
                value=st.session_state.electrical
            )
            
            st.session_state.plumbing = st.checkbox(
                "Sıhhi Tesisat", 
                value=st.session_state.plumbing
            )
            
            st.session_state.heating = st.checkbox(
                "Yerden Isıtma", 
                value=st.session_state.heating
            )
            
            st.session_state.solar = st.checkbox(
                "Güneş Enerjisi Sistemi", 
                value=st.session_state.solar
            )
            
            if st.session_state.solar:
                st.session_state.solar_capacity = st.selectbox(
                    "Güneş Enerjisi Kapasitesi (kW):", 
                    [5, 7.2, 11],
                    index=[5, 7.2, 11].index(st.session_state.solar_capacity)
                )
    
    # --- Zemin Yalıtımı ve Malzemeleri ---
    st.markdown("<div class='section-title'>🛠️ ZEMİN YALITIMI VE MALZEMELERİ</div>", unsafe_allow_html=True)
    with st.expander("Yalıtım ve Zemin Malzemeleri", expanded=True):
        st.session_state.insulation_floor = st.checkbox(
            "Zemin Yalıtımı Dahil Et", 
            value=st.session_state.insulation_floor
        )
        
        insulation_disabled = not st.session_state.insulation_floor
        
        cols = st.columns(2)
        with cols[0]:
            st.session_state.insulation_material = st.radio(
                "Yalıtım Malzemesi:", 
                ['Taş Yünü', 'Cam Yünü'],
                index=0 if st.session_state.insulation_material == 'Taş Yünü' else 1,
                disabled=insulation_disabled
            )
            
            st.session_state.skirting_length = st.number_input(
                "Süpürgelik Uzunluğu (m):", 
                value=st.session_state.skirting_length, 
                min_value=0.0, step=0.1,
                disabled=insulation_disabled
            )
            
            st.session_state.osb2_count = st.number_input(
                "OSB2 Panel Adedi:", 
                value=st.session_state.osb2_count, 
                min_value=0, step=1,
                disabled=insulation_disabled
            )
        
        with cols[1]:
            st.session_state.laminate_flooring = st.number_input(
                "Laminat Parke Alanı (m²):", 
                value=st.session_state.laminate_flooring, 
                min_value=0.0, step=0.1,
                disabled=insulation_disabled
            )
            
            st.session_state.under_parquet_mat = st.number_input(
                "Parke Altı Şilte Alanı (m²):", 
                value=st.session_state.under_parquet_mat, 
                min_value=0.0, step=0.1,
                disabled=insulation_disabled
            )
            
            st.session_state.galvanized_sheet = st.number_input(
                "Galvanizli Sac Alanı (m²):", 
                value=st.session_state.galvanized_sheet, 
                min_value=0.0, step=0.1,
                disabled=insulation_disabled
            )
    
    # --- Ek Özellikler ---
    st.markdown("<div class='section-title'>✨ EK ÖZELLİKLER</div>", unsafe_allow_html=True)
    with st.expander("Diğer Seçenekler", expanded=False):
        cols = st.columns(2)
        with cols[0]:
            st.session_state.transportation = st.checkbox(
                "Nakliye Dahil Et (350€)", 
                value=st.session_state.transportation
            )
            
            st.session_state.wheeled_trailer = st.checkbox(
                "Tekerlekli Römork Dahil Et", 
                value=st.session_state.wheeled_trailer
            )
            
            if st.session_state.wheeled_trailer:
                st.session_state.wheeled_trailer_price = st.number_input(
                    "Römork Fiyatı (€):", 
                    value=st.session_state.wheeled_trailer_price, 
                    min_value=0.0, step=1.0
                )
        
        with cols[1]:
            st.session_state.insulation_wall = st.checkbox(
                "Duvar Yalıtımı Dahil Et", 
                value=st.session_state.insulation_wall
            )
            
            st.session_state.floor_covering = st.selectbox(
                "Zemin Kaplama Tipi:", 
                ['Laminate Parquet', 'Ceramic'],
                index=0 if st.session_state.floor_covering == 'Laminate Parquet' else 1
            )
    
    # --- Finansal Ayarlar ---
    st.markdown("<div class='section-title'>💰 FİNANSAL AYARLAR</div>", unsafe_allow_html=True)
    with st.expander("Finansal Parametreler", expanded=True):
        profit_rates = [(f"{i}%", i/100) for i in range(5, 45, 5)]
        selected_profit = st.selectbox(
            "Kar Oranı:", 
            options=profit_rates,
            format_func=lambda x: x[0],
            index=3  # %20 varsayılan
        )
        st.session_state.profit_rate = selected_profit[1]
        
        st.session_state.customer_notes = st.text_area(
            "Müşteri Notları:", 
            value=st.session_state.customer_notes,
            height=100
        )
    
    # --- Hesaplama Butonu ---
    if st.button("📊 HESAPLA VE TEKLİF OLUŞTUR", use_container_width=True):
        try:
            # Alan hesaplama
            areas = calculate_area(
                st.session_state.width, 
                st.session_state.length, 
                st.session_state.height
            )
            
            # Maliyet listesi
            costs = []
            
            # 1. Çelik yapı maliyeti
            if st.session_state.structure_type == 'Light Steel':
                steel_cost = (
                    st.session_state.profile_100x100 * FIYATLAR['steel_profile_100x100x3'] +
                    st.session_state.profile_100x50 * FIYATLAR['steel_profile_100x50x3'] +
                    st.session_state.profile_40x60 * FIYATLAR['steel_profile_40x60x2'] +
                    st.session_state.profile_50x50 * FIYATLAR['steel_profile_50x50x2'] +
                    st.session_state.profile_120x60x5mm * FIYATLAR['steel_profile_120x60x5mm'] +
                    st.session_state.profile_HEA160 * FIYATLAR['steel_profile_HEA160']
                )
                costs.append({
                    'Item': 'Çelik Yapı Malzemeleri', 
                    'Quantity': 'Çeşitli profiller',
                    'Unit Price (€)': '',
                    'Total (€)': calculate_rounded_up_cost(steel_cost)
                })
            else:
                heavy_steel_cost = areas['floor'] * FIYATLAR['heavy_steel_m2']
                costs.append({
                    'Item': 'Ağır Çelik Yapı', 
                    'Quantity': f"{areas['floor']:.2f} m²",
                    'Unit Price (€)': FIYATLAR['heavy_steel_m2'],
                    'Total (€)': calculate_rounded_up_cost(heavy_steel_cost)
                })
            
            # 2. Dış cephe malzemeleri
            sandwich_panel_cost = (areas['wall'] + areas['roof']) * FIYATLAR['sandwich_panel_m2']
            costs.append({
                'Item': 'Sandviç Panel', 
                'Quantity': f"{(areas['wall'] + areas['roof']):.2f} m²",
                'Unit Price (€)': FIYATLAR['sandwich_panel_m2'],
                'Total (€)': calculate_rounded_up_cost(sandwich_panel_cost)
            })
            
            # 3. Alçıpan maliyetleri
            if st.session_state.plasterboard_interior or st.session_state.plasterboard_all:
                # Beyaz alçıpan (iç cephe)
                white_boards = math.ceil((areas['wall'] * 0.7) / GYPSUM_BOARD_UNIT_AREA_M2)
                white_gypsum_cost = white_boards * FIYATLAR['gypsum_board_white_per_unit_price']
                
                # Yeşil alçıpan (banyo)
                green_boards = math.ceil((st.session_state.wc_ceramic_area) / GYPSUM_BOARD_UNIT_AREA_M2)
                green_gypsum_cost = green_boards * FIYATLAR['gypsum_board_green_per_unit_price']
                
                # Mavi alçıpan (dış cephe)
                blue_boards = 0
                if st.session_state.plasterboard_all:
                    blue_boards = math.ceil((areas['wall'] * 0.3) / GYPSUM_BOARD_UNIT_AREA_M2)
                blue_gypsum_cost = blue_boards * FIYATLAR['gypsum_board_blue_per_unit_price']
                
                total_gypsum_cost = white_gypsum_cost + green_gypsum_cost + blue_gypsum_cost
                
                costs.append({
                    'Item': 'Alçıpan Malzemeleri', 
                    'Quantity': f"{white_boards} Beyaz, {green_boards} Yeşil, {blue_boards} Mavi",
                    'Unit Price (€)': '',
                    'Total (€)': calculate_rounded_up_cost(total_gypsum_cost)
                })
            
            # 4. Yalıtım maliyetleri
            if st.session_state.insulation_floor:
                if st.session_state.insulation_material == 'Cam Yünü':
                    packets = math.ceil(areas['floor'] / GLASS_WOOL_M2_PER_PACKET)
                    insulation_cost = packets * FIYATLAR['glass_wool_5cm_packet_price']
                    costs.append({
                        'Item': 'Cam Yünü Yalıtım', 
                        'Quantity': f"{packets} paket ({areas['floor']:.2f} m²)",
                        'Unit Price (€)': FIYATLAR['glass_wool_5cm_packet_price'],
                        'Total (€)': calculate_rounded_up_cost(insulation_cost)
                    })
                else:  # Taş Yünü
                    insulation_cost = areas['floor'] * FIYATLAR['otb_stone_wool_price']
                    costs.append({
                        'Item': 'Taş Yünü Yalıtım', 
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['otb_stone_wool_price'],
                        'Total (€)': calculate_rounded_up_cost(insulation_cost)
                    })
            
            # 5. Kapı ve pencere maliyetleri
            windows_cost = st.session_state.window_count * FIYATLAR['aluminum_window_piece']
            sliding_doors_cost = st.session_state.sliding_door_count * FIYATLAR['sliding_glass_door_piece']
            doors_cost = st.session_state.door_count * FIYATLAR['door_piece']
            wc_windows_cost = st.session_state.wc_window_count * FIYATLAR['wc_window_piece']
            wc_sliding_doors_cost = st.session_state.wc_sliding_door_count * FIYATLAR['wc_sliding_door_piece']
            
            total_openings_cost = windows_cost + sliding_doors_cost + doors_cost + wc_windows_cost + wc_sliding_doors_cost
            
            costs.append({
                'Item': 'Kapı ve Pencereler', 
                'Quantity': f"""
                    {st.session_state.window_count} Pencere, 
                    {st.session_state.sliding_door_count} Sürme Kapı, 
                    {st.session_state.door_count} Ana Kapı,
                    {st.session_state.wc_window_count} WC Pencere,
                    {st.session_state.wc_sliding_door_count} WC Sürme Kapı
                """,
                'Unit Price (€)': '',
                'Total (€)': calculate_rounded_up_cost(total_openings_cost)
            })
            
            # 6. Mutfak maliyeti
            if st.session_state.kitchen_type == 'Standart Mutfak':
                kitchen_cost = FIYATLAR['kitchen_installation_standard_piece']
                costs.append({
                    'Item': 'Standart Mutfak', 
                    'Quantity': '1 adet',
                    'Unit Price (€)': FIYATLAR['kitchen_installation_standard_piece'],
                    'Total (€)': calculate_rounded_up_cost(kitchen_cost)
                })
            elif st.session_state.kitchen_type == 'Special Design Mutfak':
                kitchen_cost = FIYATLAR['kitchen_installation_special_piece']
                costs.append({
                    'Item': 'Özel Tasarım Mutfak', 
                    'Quantity': '1 adet',
                    'Unit Price (€)': FIYATLAR['kitchen_installation_special_piece'],
                    'Total (€)': calculate_rounded_up_cost(kitchen_cost)
                })
            
            # 7. Duş/WC maliyeti
            if st.session_state.shower:
                shower_cost = FIYATLAR['shower_wc_installation_piece']
                costs.append({
                    'Item': 'Duş/WC Ünitesi', 
                    'Quantity': '1 adet',
                    'Unit Price (€)': FIYATLAR['shower_wc_installation_piece'],
                    'Total (€)': calculate_rounded_up_cost(shower_cost)
                })
            
            # 8. Diğer maliyetler
            if st.session_state.transportation:
                costs.append({
                    'Item': 'Nakliye', 
                    'Quantity': '1 sefer',
                    'Unit Price (€)': FIYATLAR['transportation'],
                    'Total (€)': FIYATLAR['transportation']
                })
                
            if st.session_state.wheeled_trailer:
                costs.append({
                    'Item': 'Tekerlekli Römork', 
                    'Quantity': '1 adet',
                    'Unit Price (€)': st.session_state.wheeled_trailer_price,
                    'Total (€)': calculate_rounded_up_cost(st.session_state.wheeled_trailer_price)
                })
                
            if st.session_state.heating:
                heating_cost = areas['floor'] * FIYATLAR['floor_heating_m2']
                costs.append({
                    'Item': 'Yerden Isıtma Sistemi', 
                    'Quantity': f"{areas['floor']:.2f} m²",
                    'Unit Price (€)': FIYATLAR['floor_heating_m2'],
                    'Total (€)': calculate_rounded_up_cost(heating_cost)
                })
                
            if st.session_state.solar:
                solar_cost = st.session_state.solar_capacity * FIYATLAR['solar_per_kw']
                costs.append({
                    'Item': f'Güneş Enerjisi Sistemi ({st.session_state.solar_capacity} kW)', 
                    'Quantity': '1 sistem',
                    'Unit Price (€)': FIYATLAR['solar_per_kw'],
                    'Total (€)': calculate_rounded_up_cost(solar_cost)
                })
            
            # Maliyetleri DataFrame'e dönüştür
            costs_df = pd.DataFrame(costs)
            
            # Finansal özet hesaplamaları
            material_subtotal = costs_df['Total (€)'].sum()
            waste_cost = material_subtotal * FIRE_RATE
            total_cost = material_subtotal + waste_cost
            profit = total_cost * st.session_state.profit_rate
            vat_base = total_cost + profit
            vat = vat_base * VAT_RATE
            total_price = vat_base + vat
            
            # Finansal özet DataFrame'i
            financial_data = [
                {'Item': 'Malzeme Ara Toplam', 'Amount (€)': format_currency(material_subtotal)},
                {'Item': f'Atık Maliyeti (%{FIRE_RATE*100:.0f})', 'Amount (€)': format_currency(waste_cost)},
                {'Item': 'Toplam Maliyet', 'Amount (€)': format_currency(total_cost)},
                {'Item': f'Kar (%{st.session_state.profit_rate*100:.0f})', 'Amount (€)': format_currency(profit)},
                {'Item': 'KDV Matrahı', 'Amount (€)': format_currency(vat_base)},
                {'Item': f'KDV (%{VAT_RATE*100:.0f})', 'Amount (€)': format_currency(vat)},
                {'Item': 'TOPLAM SATIŞ FİYATI', 'Amount (€)': format_currency(total_price)}
            ]
            financial_df = pd.DataFrame(financial_data)
            
            # Sonuçları göster
            st.success("✅ Hesaplama başarıyla tamamlandı!")
            
            st.subheader("Maliyet Detayları")
            st.dataframe(costs_df.style.format({
                'Unit Price (€)': lambda x: format_currency(x) if x != '' else '',
                'Total (€)': lambda x: format_currency(x)
            }), use_container_width=True)
            
            st.subheader("Finansal Özet")
            st.dataframe(financial_df.set_index('Item'), use_container_width=True)
            
            # PDF oluşturma
            with st.spinner("PDF raporları oluşturuluyor..."):
                # Proje detaylarını hazırla
                project_details_data = {
                    'width': st.session_state.width,
                    'length': st.session_state.length,
                    'height': st.session_state.height,
                    'structure_type': st.session_state.structure_type,
                    'room_config': st.session_state.room_config
                }
                
                # Müşteri bilgilerini hazırla
                customer_info_data = {
                    'name': st.session_state.customer_name,
                    'company': st.session_state.customer_company,
                    'address': st.session_state.customer_address,
                    'phone': st.session_state.customer_phone,
                    'email': st.session_state.customer_email,
                    'id_no': st.session_state.customer_id_no
                }
                
                internal_pdf = create_internal_cost_report_pdf(
                    costs_df,
                    financial_df,
                    project_details_data,
                    customer_info_data
                )
                
                st.download_button(
                    label="📥 Dahili Maliyet Raporunu İndir",
                    data=internal_pdf,
                    file_name=f"premium_home_cost_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"❌ Hesaplama sırasında hata oluştu: {str(e)}")
            st.error("Lütfen girdilerinizi kontrol edip tekrar deneyin")
    
    # Alt bilgi
    st.markdown("---")
    st.markdown(f'<div class="footer">{COMPANY_INFO["name"]} © {datetime.now().year} | {COMPANY_INFO["phone"]} | {COMPANY_INFO["website"]}</div>', unsafe_allow_html=True)

# Uygulamayı çalıştır
if __name__ == "__main__":
    run_streamlit_app()
