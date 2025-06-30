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

# ====================== CONSTANTS AND CONFIGURATION ======================
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
    "logo_url": "https://drive.google.com/uc?export=download&id=1RD27Gas035iUqe4Ucl3phFwxZPWZPWzn"
}

FIYATLAR = {
    # Steel profiles
    "steel_profile_100x100x3": 45.00,
    "steel_profile_100x50x3": 33.00,
    "steel_profile_40x60x2": 14.00,
    "steel_profile_120x60x5mm": 60.00,
    "steel_profile_50x50x2": 11.00,
    "steel_profile_HEA160": 155.00,
    
    # Materials
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
    
    # Labor costs
    "welding_labor_m2_standard": 160.00,
    "welding_labor_m2_trmontaj": 20.00,
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00,
    "plasterboard_labor_m2_avg": 80.00,
    "plywood_flooring_labor_m2": 11.11,
    "door_window_assembly_labor_piece": 10.00,
    "solar_per_kw": 1250.00,
    
    # Floor system materials
    "skirting_meter_price": 2.00,
    "laminate_flooring_m2_price": 15.00,
    "under_parquet_mat_m2_price": 3.00,
    "osb2_18mm_piece_price": 30.00,
    "galvanized_sheet_m2_price": 10.00,

    # Aether Living materials
    "smart_home_systems_total_price": 350.00,
    "white_goods_total_price": 800.00,
    "sofa_total_price": 400.00,
    "security_camera_total_price": 650.00,
    "exterior_cladding_labor_price_per_m2": 150.00,
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
    "gypsum_board_white_per_unit_price": 8.65,
    "gypsum_board_green_per_unit_price": 11.95,
    "gypsum_board_blue_per_unit_price": 22.00,
    "otb_stone_wool_price": 19.80,
    "glass_wool_5cm_packet_price": 19.68,
    "tn25_screws_price_per_unit": 5.58,
    "cdx400_material_price": 3.40,
    "ud_material_price": 1.59,
    "oc50_material_price": 2.20,
    "oc100_material_price": 3.96,
    "ch100_material_price": 3.55
}

# Constants
FIRE_RATE = 0.05
VAT_RATE = 0.19
MONTHLY_ACCOUNTING_EXPENSES = 180.00
MONTHLY_OFFICE_RENT = 280.00
ANNUAL_INCOME_TAX_RATE = 0.235
OSB_PANEL_AREA_M2 = 1.22 * 2.44
GYPSUM_BOARD_UNIT_AREA_M2 = 2.88
GLASS_WOOL_M2_PER_PACKET = 10.0
EUR_TO_TL_RATE = 47.5
USD_TO_TL_RATE = 40.0

# ====================== UTILITY FUNCTIONS ======================
def clean_invisible_chars(text):
    """Remove invisible characters from text"""
    return re.sub(r'[\u00A0\u200B]', ' ', text)

def calculate_area(width, length, height):
    """Calculate floor, wall and roof areas"""
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Format value as Euro currency"""
    return f"€{value:,.2f}"

def calculate_rounded_up_cost(value):
    """Round up cost to 2 decimal places"""
    return math.ceil(value * 100) / 100.0

# ====================== PDF GENERATION FUNCTIONS ======================
def get_company_logo_base64(url, width=180):
    """Fetch company logo and return as base64 string"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        img = PILImage.open(io.BytesIO(response.content))
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width, h_size), PILImage.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        st.warning(f"Logo error: {e}")
        return None

def draw_pdf_header(canvas_obj, doc, logo_data_b64, company_info):
    """Draw PDF header with logo and company info"""
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
    """Draw PDF footer with company info and page number"""
    footer_text = f"{company_info['address']} | {company_info['email']} | {company_info['phone']} | {company_info['website']}"
    canvas_obj.setFont(f"{MAIN_FONT}-Bold", 8)
    canvas_obj.drawCentredString(A4[0] / 2, 15*mm, footer_text)
    
    page_num = canvas_obj.getPageNumber()
    canvas_obj.setFont(MAIN_FONT, 8)
    canvas_obj.drawString(A4[0] - doc.rightMargin, 10*mm, f"Page {page_num}")

def create_internal_cost_report_pdf(cost_breakdown_df, financial_summary_df, project_details, customer_info, logo_data_b64):
    """Generate internal cost report PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=15*mm, leftMargin=15*mm,
                          topMargin=40*mm, bottomMargin=25*mm)
    
    styles = getSampleStyleSheet()
    custom_styles = {
        'Normal': ParagraphStyle('Normal', parent=styles['Normal'], 
                               fontName=MAIN_FONT, fontSize=9, leading=12),
        'Bold': ParagraphStyle('Bold', parent=styles['Normal'], 
                            fontName=f'{MAIN_FONT}-Bold', fontSize=9, leading=12),
        'Heading': ParagraphStyle('Heading', parent=styles['Heading2'],
                               fontName=f'{MAIN_FONT}-Bold', fontSize=12, 
                               spaceAfter=6, textColor=colors.HexColor('#34495E')),
        'Title': ParagraphStyle('Title', parent=styles['Heading1'],
                             fontName=f'{MAIN_FONT}-Bold', fontSize=16,
                             alignment=TA_CENTER, spaceAfter=12,
                             textColor=colors.HexColor('#2C3E50'))
    }
    
    elements = []
    
    # Title
    elements.append(Paragraph("PREMIUM HOME - INTERNAL COST REPORT", custom_styles['Title']))
    elements.append(Spacer(1, 5*mm))
    
    # Customer and project info
    elements.append(Paragraph(f"<b>Client:</b> {customer_info.get('name', 'GENERAL')}", custom_styles['Normal']))
    elements.append(Paragraph(f"<b>Project Area:</b> {project_details['area']:.2f} m²", custom_styles['Normal']))
    elements.append(Spacer(1, 10*mm))
    
    # Cost breakdown table
    if not cost_breakdown_df.empty:
        data = [cost_breakdown_df.columns.tolist()] + cost_breakdown_df.values.tolist()
        table = Table(data, colWidths=[90*mm, 30*mm, 35*mm, 30*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4a5568")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), f'{MAIN_FONT}-Bold'),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(table)
    
    # Financial summary
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("FINANCIAL SUMMARY", custom_styles['Heading']))
    
    if not financial_summary_df.empty:
        data = [financial_summary_df.columns.tolist()] + financial_summary_df.values.tolist()
        table = Table(data, colWidths=[120*mm, 40*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#3182ce")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#ebf8ff")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#90cdf4")),
        ]))
        elements.append(table)
    
    doc.build(elements, 
             onLaterPages=lambda c, d: draw_pdf_header(c, d, logo_data_b64, COMPANY_INFO),
             onFirstPage=lambda c, d: draw_pdf_footer(c, d, COMPANY_INFO))
    
    return buffer

# ====================== MAIN APPLICATION ======================
def run_streamlit_app():
    # Initialize session state
    session_state_defaults = {
        'aether_package_choice': 'None',
        'width_val': 10.0,
        'length_val': 8.0,
        'height_val': 2.6,
        'structure_type': 'Light Steel',
        'welding_type': 'Standard Welding (160€/m²)',
        'room_config': '1 Room',
        'window_count': 4,
        'sliding_door_count': 0,
        'wc_window_count': 1,
        'wc_sliding_door_count': 0,
        'door_count': 1,
        'kitchen_choice': 'No Kitchen',
        'shower_wc': False,
        'wc_ceramic': False,
        'wc_ceramic_area': 0.0,
        'electrical': False,
        'plumbing': False,
        'insulation_floor': False,
        'insulation_wall': False,
        'floor_covering': 'Laminate Parquet',
        'transportation': False,
        'heating': False,
        'solar': False,
        'solar_kw': 5,
        'wheeled_trailer': False,
        'wheeled_trailer_price': 0.0,
        'profit_rate': (f'{20}%', 0.20),
        'customer_notes': "",
        'pdf_language': ('Turkish', 'tr'),
        'customer_city': "",
        # Aether Living options
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
        'insulation_material_type': 'Stone Wool'
    }

    for key, default_value in session_state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

    # UI Configuration
    st.set_page_config(layout="wide", page_title="Premium Home Cost Calculator")
    
    # Custom CSS
    st.markdown("""
    <style>
    .section-title {
        background-color: #3182ce;
        color: white;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #3182ce;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🏠 Premium Home Cost Calculator")

    # Sidebar - Customer Information
    with st.sidebar:
        st.header("Customer Information")
        customer_name = st.text_input("Full Name", key="customer_name")
        customer_company = st.text_input("Company", key="customer_company")
        customer_address = st.text_area("Address", key="customer_address")
        customer_city = st.text_input("City", key="customer_city")
        customer_phone = st.text_input("Phone", key="customer_phone")
        customer_email = st.text_input("Email", key="customer_email")
        customer_id_no = st.text_input("ID/Passport No", key="customer_id_no")
        
        st.header("Package Selection")
        st.session_state.aether_package_choice = st.selectbox(
            "Aether Living Package",
            ['None', 'Aether Living | Loft Standard (BASICS)', 
             'Aether Living | Loft Premium (ESSENTIAL)',
             'Aether Living | Loft Elite (LUXURY)'],
            index=['None', 'Aether Living | Loft Standard (BASICS)',
                  'Aether Living | Loft Premium (ESSENTIAL)',
                  'Aether Living | Loft Elite (LUXURY)'].index(st.session_state.aether_package_choice)
        )

    # Main Form
    with st.form("main_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='section-title'>DIMENSIONS</div>", unsafe_allow_html=True)
            st.session_state.width_val = st.number_input("Width (m)", value=st.session_state.width_val, step=0.1)
            st.session_state.length_val = st.number_input("Length (m)", value=st.session_state.length_val, step=0.1)
            st.session_state.height_val = st.number_input("Height (m)", value=st.session_state.height_val, step=0.1)
            
            st.markdown("<div class='section-title'>STRUCTURE</div>", unsafe_allow_html=True)
            st.session_state.structure_type = st.radio(
                "Structure Type",
                ['Light Steel', 'Heavy Steel'],
                index=['Light Steel', 'Heavy Steel'].index(st.session_state.structure_type)
            )
            
            st.session_state.welding_type = st.selectbox(
                "Welding Type",
                ['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'],
                index=['Standard Welding (160€/m²)', 'TR Assembly Welding (20€/m²)'].index(st.session_state.welding_type)
            )
            
        with col2:
            st.markdown("<div class='section-title'>CONFIGURATION</div>", unsafe_allow_html=True)
            st.session_state.room_config = st.selectbox(
                "Room Configuration",
                ['Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
                 '1 Room + Kitchen + WC', '1 Room + Shower / WC + Kitchen',
                 '2 Rooms + Shower / WC + Kitchen', '3 Rooms + 2 Showers / WC + Kitchen'],
                index=['Empty Model', '1 Room', '1 Room + Shower / WC', '1 Room + Kitchen',
                      '1 Room + Kitchen + WC', '1 Room + Shower / WC + Kitchen',
                      '2 Rooms + Shower / WC + Kitchen', '3 Rooms + 2 Showers / WC + Kitchen'].index(st.session_state.room_config)
            )
            
            st.session_state.kitchen_choice = st.radio(
                "Kitchen Type",
                ['No Kitchen', 'Standard Kitchen', 'Special Design Kitchen'],
                index=['No Kitchen', 'Standard Kitchen', 'Special Design Kitchen'].index(st.session_state.kitchen_choice)
            )
            
            st.session_state.floor_covering = st.selectbox(
                "Floor Covering Type",
                ['Laminate Parquet', 'Ceramic'],
                index=['Laminate Parquet', 'Ceramic'].index(st.session_state.floor_covering)
            )

        # Additional Options
        st.markdown("<div class='section-title'>ADDITIONAL EQUIPMENT</div>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        
        with col3:
            st.session_state.shower_wc = st.checkbox("Include Shower/WC", value=st.session_state.shower_wc)
            st.session_state.wc_ceramic = st.checkbox("WC Ceramic Floor/Walls", value=st.session_state.wc_ceramic)
            if st.session_state.wc_ceramic:
                st.session_state.wc_ceramic_area = st.number_input("WC Ceramic Area (m²)", value=st.session_state.wc_ceramic_area, min_value=0.0, step=0.1)
            
            st.session_state.electrical = st.checkbox("Electrical Installation", value=st.session_state.electrical)
            st.session_state.plumbing = st.checkbox("Plumbing Installation", value=st.session_state.plumbing)
            
        with col4:
            st.session_state.insulation_floor = st.checkbox("Floor Insulation", value=st.session_state.insulation_floor)
            st.session_state.insulation_wall = st.checkbox("Wall Insulation", value=st.session_state.insulation_wall)
            st.session_state.heating = st.checkbox("Floor Heating", value=st.session_state.heating)
            st.session_state.transportation = st.checkbox("Include Transportation", value=st.session_state.transportation)
        
        # Solar Energy
        st.session_state.solar = st.checkbox("Solar Energy System", value=st.session_state.solar)
        if st.session_state.solar:
            st.session_state.solar_kw = st.selectbox(
                "Solar Capacity (kW)",
                [5, 7.2, 11],
                index=[5, 7.2, 11].index(st.session_state.solar_kw)
            )
        
        # Aether Living Options
        if st.session_state.aether_package_choice != 'None':
            st.markdown("<div class='section-title'>AETHER LIVING OPTIONS</div>", unsafe_allow_html=True)
            
            col5, col6 = st.columns(2)
            
            with col5:
                if st.session_state.aether_package_choice in ['Aether Living | Loft Premium (ESSENTIAL)', 'Aether Living | Loft Elite (LUXURY)']:
                    st.session_state.bedroom_set_option = st.checkbox("Bedroom Set", value=st.session_state.bedroom_set_option)
                    st.session_state.brushed_granite_countertops_option = st.checkbox("Brushed Granite Countertops", value=st.session_state.brushed_granite_countertops_option)
                    if st.session_state.brushed_granite_countertops_option:
                        st.session_state.brushed_granite_countertops_m2_val = st.number_input("Granite Countertop Area (m²)", value=st.session_state.brushed_granite_countertops_m2_val, min_value=0.0, step=0.1)
                    
                    st.session_state.terrace_laminated_wood_flooring_option = st.checkbox("Terrace Laminated Wood Flooring", value=st.session_state.terrace_laminated_wood_flooring_option)
                    if st.session_state.terrace_laminated_wood_flooring_option:
                        st.session_state.terrace_laminated_wood_flooring_m2_val = st.number_input("Terrace Flooring Area (m²)", value=st.session_state.terrace_laminated_wood_flooring_m2_val, min_value=0.0, step=0.1)
            
            with col6:
                if st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                    st.session_state.exterior_cladding_m2_option = st.checkbox("Exterior Cladding (Knauf Aquapanel)", value=st.session_state.exterior_cladding_m2_option)
                    if st.session_state.exterior_cladding_m2_option:
                        st.session_state.exterior_cladding_m2_val = st.number_input("Exterior Cladding Area (m²)", value=st.session_state.exterior_cladding_m2_val, min_value=0.0, step=0.1)
                    
                    st.session_state.concrete_panel_floor_option = st.checkbox("Concrete Panel Floor", value=st.session_state.concrete_panel_floor_option)
                    if st.session_state.concrete_panel_floor_option:
                        st.session_state.concrete_panel_floor_m2_val = st.number_input("Concrete Floor Area (m²)", value=st.session_state.concrete_panel_floor_m2_val, min_value=0.0, step=0.1)
                    
                    st.session_state.premium_faucets_option = st.checkbox("Premium Faucets", value=st.session_state.premium_faucets_option)
                    st.session_state.integrated_fridge_option = st.checkbox("Integrated Refrigerator", value=st.session_state.integrated_fridge_option)
                    st.session_state.designer_furniture_option = st.checkbox("Designer Furniture", value=st.session_state.designer_furniture_option)
                    st.session_state.italian_sofa_option = st.checkbox("Italian Sofa", value=st.session_state.italian_sofa_option)
                    st.session_state.inclass_chairs_option = st.checkbox("Inclass Chairs", value=st.session_state.inclass_chairs_option)
                    if st.session_state.inclass_chairs_option:
                        st.session_state.inclass_chairs_count = st.number_input("Number of Chairs", value=st.session_state.inclass_chairs_count, min_value=0, step=1)
                    st.session_state.smart_home_systems_option = st.checkbox("Smart Home Systems", value=st.session_state.smart_home_systems_option)
                    st.session_state.security_camera_option = st.checkbox("Security Camera System", value=st.session_state.security_camera_option)
                    st.session_state.white_goods_fridge_tv_option = st.checkbox("White Goods (Fridge/TV)", value=st.session_state.white_goods_fridge_tv_option)

        # Financial Settings
        st.markdown("<div class='section-title'>FINANCIAL SETTINGS</div>", unsafe_allow_html=True)
        profit_options = [(f'{i}%', i/100) for i in range(5, 45, 5)]
        st.session_state.profit_rate = st.selectbox(
            "Profit Rate",
            options=profit_options,
            format_func=lambda x: x[0],
            index=profit_options.index(st.session_state.profit_rate)
        )
        
        # Customer Notes
        st.session_state.customer_notes = st.text_area("Customer Notes", value=st.session_state.customer_notes)
        
        # PDF Language
        st.session_state.pdf_language = st.selectbox(
            "Proposal PDF Language",
            options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')],
            format_func=lambda x: x[0],
            index=[('English-Greek', 'en_gr'), ('Turkish', 'tr')].index(st.session_state.pdf_language)
        )

        if st.form_submit_button("Calculate and Generate Proposals"):
            try:
                # Perform calculations
                areas = calculate_area(
                    st.session_state.width_val,
                    st.session_state.length_val,
                    st.session_state.height_val
                )
                
                # Prepare customer info
                customer_info = {
                    'name': customer_name.strip(),
                    'company': customer_company.strip(),
                    'address': customer_address.strip(),
                    'city': customer_city.strip(),
                    'phone': customer_phone.strip(),
                    'email': customer_email.strip(),
                    'id_no': customer_id_no.strip()
                }
                
                # Prepare project details
                project_details = {
                    'width': st.session_state.width_val,
                    'length': st.session_state.length_val,
                    'height': st.session_state.height_val,
                    'area': areas['floor'],
                    'structure_type': st.session_state.structure_type,
                    'room_configuration': st.session_state.room_config,
                    'welding_type': st.session_state.welding_type,
                    'kitchen_choice': st.session_state.kitchen_choice,
                    'shower_wc': st.session_state.shower_wc,
                    'wc_ceramic': st.session_state.wc_ceramic,
                    'wc_ceramic_area': st.session_state.wc_ceramic_area,
                    'electrical': st.session_state.electrical,
                    'plumbing': st.session_state.plumbing,
                    'insulation_floor': st.session_state.insulation_floor,
                    'insulation_wall': st.session_state.insulation_wall,
                    'floor_covering': st.session_state.floor_covering,
                    'transportation': st.session_state.transportation,
                    'heating': st.session_state.heating,
                    'solar': st.session_state.solar,
                    'solar_kw': st.session_state.solar_kw,
                    'wheeled_trailer': st.session_state.wheeled_trailer,
                    'wheeled_trailer_price': st.session_state.wheeled_trailer_price,
                    'customer_notes': st.session_state.customer_notes,
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
                    'insulation_material_type': st.session_state.insulation_material_type
                }
                
                # Calculate costs based on selections
                costs = []
                
                # Structure costs
                if st.session_state.structure_type == 'Light Steel':
                    steel_cost = areas['floor'] * FIYATLAR['steel_profile_100x100x3']
                    costs.append({
                        'Item': 'Steel Structure (100x100x3)',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['steel_profile_100x100x3'],
                        'Total (€)': steel_cost
                    })
                else:  # Heavy Steel
                    steel_cost = areas['floor'] * FIYATLAR['heavy_steel_m2']
                    costs.append({
                        'Item': 'Heavy Steel Structure',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['heavy_steel_m2'],
                        'Total (€)': steel_cost
                    })
                
                # Welding labor
                if st.session_state.welding_type == 'Standard Welding (160€/m²)':
                    welding_cost = areas['floor'] * FIYATLAR['welding_labor_m2_standard']
                    costs.append({
                        'Item': 'Standard Welding Labor',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['welding_labor_m2_standard'],
                        'Total (€)': welding_cost
                    })
                else:
                    welding_cost = areas['floor'] * FIYATLAR['welding_labor_m2_trmontaj']
                    costs.append({
                        'Item': 'TR Assembly Welding Labor',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['welding_labor_m2_trmontaj'],
                        'Total (€)': welding_cost
                    })
                
                # Kitchen costs
                if st.session_state.kitchen_choice == 'Standard Kitchen':
                    costs.append({
                        'Item': 'Standard Kitchen Installation',
                        'Quantity': '1',
                        'Unit Price (€)': FIYATLAR['kitchen_installation_standard_piece'],
                        'Total (€)': FIYATLAR['kitchen_installation_standard_piece']
                    })
                elif st.session_state.kitchen_choice == 'Special Design Kitchen':
                    costs.append({
                        'Item': 'Special Design Kitchen Installation',
                        'Quantity': '1',
                        'Unit Price (€)': FIYATLAR['kitchen_installation_special_piece'],
                        'Total (€)': FIYATLAR['kitchen_installation_special_piece']
                    })
                
                # Shower/WC costs
                if st.session_state.shower_wc:
                    costs.append({
                        'Item': 'Shower/WC Installation',
                        'Quantity': '1',
                        'Unit Price (€)': FIYATLAR['shower_wc_installation_piece'],
                        'Total (€)': FIYATLAR['shower_wc_installation_piece']
                    })
                
                    if st.session_state.wc_ceramic and st.session_state.wc_ceramic_area > 0:
                        ceramic_cost = st.session_state.wc_ceramic_area * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                        costs.append({
                            'Item': 'WC Ceramic Tiles',
                            'Quantity': f"{st.session_state.wc_ceramic_area:.2f} m²",
                            'Unit Price (€)': FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'],
                            'Total (€)': ceramic_cost
                        })
                
                # Electrical and plumbing
                if st.session_state.electrical:
                    electrical_cost = areas['floor'] * FIYATLAR['electrical_per_m2']
                    costs.append({
                        'Item': 'Electrical Installation',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['electrical_per_m2'],
                        'Total (€)': electrical_cost
                    })
                
                if st.session_state.plumbing:
                    plumbing_cost = areas['floor'] * FIYATLAR['plumbing_per_m2']
                    costs.append({
                        'Item': 'Plumbing Installation',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['plumbing_per_m2'],
                        'Total (€)': plumbing_cost
                    })
                
                # Insulation
                if st.session_state.insulation_floor:
                    insulation_cost = areas['floor'] * FIYATLAR['insulation_per_m2']
                    costs.append({
                        'Item': 'Floor Insulation',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['insulation_per_m2'],
                        'Total (€)': insulation_cost
                    })
                
                if st.session_state.insulation_wall:
                    insulation_cost = areas['wall'] * FIYATLAR['insulation_per_m2']
                    costs.append({
                        'Item': 'Wall Insulation',
                        'Quantity': f"{areas['wall']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['insulation_per_m2'],
                        'Total (€)': insulation_cost
                    })
                
                # Floor covering
                if st.session_state.floor_covering == 'Laminate Parquet':
                    laminate_cost = areas['floor'] * FIYATLAR['laminate_flooring_m2_price']
                    costs.append({
                        'Item': 'Laminate Flooring',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['laminate_flooring_m2_price'],
                        'Total (€)': laminate_cost
                    })
                else:  # Ceramic
                    ceramic_cost = areas['floor'] * (FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'])
                    costs.append({
                        'Item': 'Ceramic Flooring',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['wc_ceramic_m2_material'] + FIYATLAR['wc_ceramic_m2_labor'],
                        'Total (€)': ceramic_cost
                    })
                
                # Heating
                if st.session_state.heating:
                    heating_cost = areas['floor'] * FIYATLAR['floor_heating_m2']
                    costs.append({
                        'Item': 'Floor Heating System',
                        'Quantity': f"{areas['floor']:.2f} m²",
                        'Unit Price (€)': FIYATLAR['floor_heating_m2'],
                        'Total (€)': heating_cost
                    })
                
                # Solar
                if st.session_state.solar:
                    solar_cost = st.session_state.solar_kw * FIYATLAR['solar_per_kw']
                    costs.append({
                        'Item': f'Solar Energy System ({st.session_state.solar_kw} kW)',
                        'Quantity': '1',
                        'Unit Price (€)': FIYATLAR['solar_per_kw'],
                        'Total (€)': solar_cost
                    })
                
                # Transportation
                if st.session_state.transportation:
                    costs.append({
                        'Item': 'Transportation',
                        'Quantity': '1',
                        'Unit Price (€)': FIYATLAR['transportation'],
                        'Total (€)': FIYATLAR['transportation']
                    })
                
                # Aether Living Package additions
                if st.session_state.aether_package_choice != 'None':
                    if st.session_state.aether_package_choice == 'Aether Living | Loft Standard (BASICS)':
                        # Basic package inclusions
                        pass
                    
                    elif st.session_state.aether_package_choice == 'Aether Living | Loft Premium (ESSENTIAL)':
                        if st.session_state.bedroom_set_option:
                            costs.append({
                                'Item': 'Bedroom Set',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['bedroom_set_total_price'],
                                'Total (€)': FIYATLAR['bedroom_set_total_price']
                            })
                        
                        if st.session_state.brushed_granite_countertops_option and st.session_state.brushed_granite_countertops_m2_val > 0:
                            granite_cost = st.session_state.brushed_granite_countertops_m2_val * FIYATLAR['brushed_grey_granite_countertops_price_m2_avg']
                            costs.append({
                                'Item': 'Brushed Granite Countertops',
                                'Quantity': f"{st.session_state.brushed_granite_countertops_m2_val:.2f} m²",
                                'Unit Price (€)': FIYATLAR['brushed_grey_granite_countertops_price_m2_avg'],
                                'Total (€)': granite_cost
                            })
                        
                        if st.session_state.terrace_laminated_wood_flooring_option and st.session_state.terrace_laminated_wood_flooring_m2_val > 0:
                            terrace_cost = st.session_state.terrace_laminated_wood_flooring_m2_val * FIYATLAR['terrace_laminated_wood_flooring_price_per_m2']
                            costs.append({
                                'Item': 'Terrace Laminated Wood Flooring',
                                'Quantity': f"{st.session_state.terrace_laminated_wood_flooring_m2_val:.2f} m²",
                                'Unit Price (€)': FIYATLAR['terrace_laminated_wood_flooring_price_per_m2'],
                                'Total (€)': terrace_cost
                            })
                    
                    elif st.session_state.aether_package_choice == 'Aether Living | Loft Elite (LUXURY)':
                        if st.session_state.exterior_cladding_m2_option and st.session_state.exterior_cladding_m2_val > 0:
                            cladding_cost = st.session_state.exterior_cladding_m2_val * FIYATLAR['exterior_cladding_labor_price_per_m2']
                            costs.append({
                                'Item': 'Exterior Cladding (Knauf Aquapanel)',
                                'Quantity': f"{st.session_state.exterior_cladding_m2_val:.2f} m²",
                                'Unit Price (€)': FIYATLAR['exterior_cladding_labor_price_per_m2'],
                                'Total (€)': cladding_cost
                            })
                        
                        if st.session_state.concrete_panel_floor_option and st.session_state.concrete_panel_floor_m2_val > 0:
                            concrete_cost = st.session_state.concrete_panel_floor_m2_val * FIYATLAR['concrete_panel_floor_price_per_m2']
                            costs.append({
                                'Item': 'Concrete Panel Floor',
                                'Quantity': f"{st.session_state.concrete_panel_floor_m2_val:.2f} m²",
                                'Unit Price (€)': FIYATLAR['concrete_panel_floor_price_per_m2'],
                                'Total (€)': concrete_cost
                            })
                        
                        if st.session_state.premium_faucets_option:
                            costs.append({
                                'Item': 'Premium Faucets',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['premium_faucets_total_price'],
                                'Total (€)': FIYATLAR['premium_faucets_total_price']
                            })
                        
                        if st.session_state.integrated_fridge_option:
                            costs.append({
                                'Item': 'Integrated Refrigerator',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['white_goods_total_price'],
                                'Total (€)': FIYATLAR['white_goods_total_price']
                            })
                        
                        if st.session_state.designer_furniture_option:
                            costs.append({
                                'Item': 'Designer Furniture',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['designer_furniture_total_price'],
                                'Total (€)': FIYATLAR['designer_furniture_total_price']
                            })
                        
                        if st.session_state.italian_sofa_option:
                            costs.append({
                                'Item': 'Italian Sofa',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['italian_sofa_total_price'],
                                'Total (€)': FIYATLAR['italian_sofa_total_price']
                            })
                        
                        if st.session_state.inclass_chairs_option and st.session_state.inclass_chairs_count > 0:
                            chairs_cost = st.session_state.inclass_chairs_count * FIYATLAR['inclass_chairs_unit_price']
                            costs.append({
                                'Item': 'Inclass Chairs',
                                'Quantity': f"{st.session_state.inclass_chairs_count}",
                                'Unit Price (€)': FIYATLAR['inclass_chairs_unit_price'],
                                'Total (€)': chairs_cost
                            })
                        
                        if st.session_state.smart_home_systems_option:
                            costs.append({
                                'Item': 'Smart Home Systems',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['smart_home_systems_total_price'],
                                'Total (€)': FIYATLAR['smart_home_systems_total_price']
                            })
                        
                        if st.session_state.security_camera_option:
                            costs.append({
                                'Item': 'Security Camera System',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['security_camera_total_price'],
                                'Total (€)': FIYATLAR['security_camera_total_price']
                            })
                        
                        if st.session_state.white_goods_fridge_tv_option:
                            costs.append({
                                'Item': 'White Goods (Fridge/TV)',
                                'Quantity': '1',
                                'Unit Price (€)': FIYATLAR['white_goods_total_price'],
                                'Total (€)': FIYATLAR['white_goods_total_price']
                            })
                
                # Calculate financial summary
                subtotal = sum(item['Total (€)'] for item in costs)
                waste_cost = subtotal * FIRE_RATE
                total_cost = subtotal + waste_cost
                profit = total_cost * st.session_state.profit_rate[1]
                vat = (total_cost + profit) * VAT_RATE
                total_price = total_cost + profit + vat
                
                financial_summary = [
                    ["Subtotal", subtotal],
                    [f"Waste Cost ({FIRE_RATE*100:.0f}%)", waste_cost],
                    ["Total Cost", total_cost],
                    [f"Profit ({st.session_state.profit_rate[0]})", profit],
                    ["VAT (19%)", vat],
                    ["TOTAL SALES PRICE", total_price]
                ]
                
                # Generate PDFs
                logo_data = get_company_logo_base64(COMPANY_INFO['logo_url'])
                
                # Internal cost report
                internal_pdf = create_internal_cost_report_pdf(
                    pd.DataFrame(costs),
                    pd.DataFrame(financial_summary, columns=['Item', 'Amount (€)']),
                    project_details,
                    customer_info,
                    logo_data
                )
                
                # Display results and download buttons
                st.success("Calculation completed! You can download the reports below.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        "Download Internal Cost Report",
                        data=internal_pdf.getvalue(),
                        file_name=f"premium_home_cost_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                
                with col2:
                    # Placeholder for customer proposal PDF
                    st.download_button(
                        "Download Customer Proposal",
                        data=internal_pdf.getvalue(),  # In a real app, this would be a different PDF
                        file_name=f"customer_proposal_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                
                # Display cost breakdown
                st.subheader("Cost Breakdown")
                st.dataframe(pd.DataFrame(costs))
                
                # Display financial summary
                st.subheader("Financial Summary")
                st.dataframe(pd.DataFrame(financial_summary, columns=['Item', 'Amount (€)']))
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    # Initialize fonts
    try:
        pdfmetrics.registerFont(TTFont("FreeSans", "fonts/FreeSans.ttf"))
        pdfmetrics.registerFont(TTFont("FreeSans-Bold", "fonts/FreeSansBold.ttf"))
        MAIN_FONT = "FreeSans"
    except:
        MAIN_FONT = "Helvetica"
    
    run_streamlit_app()
