# --- Setup for Google Colab ---
# Check and install reportlab if not present
try:
    from reportlab.platypus import SimpleDocTemplate
except ImportError:
    print("Required 'reportlab' library is being installed...")
    import sys
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    print("Installation complete. Please re-run the cell.")
    
# Mount Google Drive
try:
    import google.colab.drive
    if not hasattr(google.colab.drive, '_mounts') or '/content/drive' not in google.colab.drive._mounts:
        print("Google Drive is being mounted...")
        google.colab.drive.mount('/content/drive')
    else:
        print("Google Drive is already mounted.")
except ImportError:
    print("Not in Google Colab environment. Skipping Google Drive connection.")
import math
import pandas as pd
import base64
import io
import ipywidgets as widgets
from datetime import datetime
from IPython.display import display, clear_output, HTML
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


# === THEME AND FONT SETTINGS ===
DARK_MODE = False  # User can toggle dark mode

# Register a font that supports Greek and Turkish characters (e.g., DejaVuSans or FreeSans)
# IMPORTANT: Ensure FreeSans.ttf and FreeSansBold.ttf are in your Google Drive,
# for example, in a folder named 'fonts' directly under 'My Drive'.
try:
    pdfmetrics.registerFont(TTFont("FreeSans", "/content/drive/My Drive/fonts/FreeSans.ttf"))
    pdfmetrics.registerFont(TTFont("FreeSans-Bold", "/content/drive/My Drive/fonts/FreeSansBold.ttf"))
    pdfmetrics.registerFontFamily('FreeSans',
                                  normal='FreeSans',
                                  bold='FreeSans-Bold',
                                  italic='FreeSans', # Fallback to normal if no italic font is available
                                  boldItalic='FreeSans-Bold') # Fallback to bold if no bold-italic font is available
    MAIN_FONT = "FreeSans"
except Exception as e:
    print(f"WARNING: Could not register FreeSans fonts. Please ensure FreeSans.ttf and FreeSansBold.ttf are in '/content/drive/My Drive/fonts/' in your Google Drive. Using Helvetica. Error: {e}")
    MAIN_FONT = "Helvetica" # Fallback font

def set_theme(dark_mode=False):
    """Sets the UI theme (light or dark)"""
    global DARK_MODE
    DARK_MODE = dark_mode

    bg_color = "#f8f9fa" if not dark_mode else "#1a202c"
    text_color = "#2d3748" if not dark_mode else "#e2e8f0"
    primary_color = "#3182ce" if not dark_mode else "#63b3ed"
    secondary_color = "#e2e8f0" if not dark_mode else "#4a5568"
    card_bg = "#ffffff" if not dark_mode else "#2d3748"
    border_color = "#e2e8f0" if not dark_mode else "#4a5568"

    display(HTML(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        * {{
            font-family: 'Inter', sans-serif !important;
        }}

        .widget-label {{
            font-weight: 500;
            margin-top: 10px;
            color: {text_color} !important;
        }}

        h3 {{
            color: {primary_color};
            border-bottom: 2px solid {primary_color};
            padding-bottom: 5px;
            margin-top: 20px;
            font-weight: 600 !important;
        }}

        .dataframe {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
            background-color: {card_bg};
            color: {text_color};
        }}

        .dataframe th, .dataframe td {{
            border: 1px solid {border_color};
            padding: 8px;
            text-align: left;
        }}

        .dataframe th {{
            background-color: {primary_color};
            color: white;
            font-weight: 600 !important;
        }}

        .pdf-button {{
            background-color: {primary_color};
            border: none;
            color: white;
            padding: 12px 24px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 15px;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s;
            font-weight: 500 !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .pdf-button:hover {{
            background-color: {'#2c5282' if not dark_mode else '#90cdf4'};
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}

        .pdf-container {{
            margin: 25px 0;
            padding: 20px;
            background-color: {'#edf2f7' if not dark_mode else '#1a202c'};
            border-radius: 10px;
            text-align: center;
            border: 1px solid {border_color};
        }}

        .customer-section {{
            background-color: {'#ebf8ff' if not dark_mode else '#2b6cb0'};
            border: 1px solid {primary_color};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }}

        .warning {{
            color: {'#e53e3e' if not dark_mode else '#fc8181'};
            font-weight: 500;
            background-color: {'#fff5f5' if not dark_mode else '#742a2a'};
            padding: 10px;
            border-radius: 5px;
            border: 1px solid {'#fed7d7' if not dark_mode else '#9b2c2c'};
        }}

        .section-title {{
            background-color: {primary_color};
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-weight: 600 !important;
            margin-top: 20px;
        }}

        .price-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
            background-color: {card_bg};
            color: {text_color};
        }}

        .price-table th, .price-table td {{
            border: 1px solid {border_color};
            padding: 10px;
            text-align: left;
        }}

        .price-table th {{
            background-color: {primary_color};
            color: white;
        }}

        .price-table tr:nth-child(even) {{
            background-color: {'#f7fafc' if not dark_mode else '#2d3748'};
        }}

        body {{
            background-color: {bg_color};
            color: {text_color};
        }}

        .widget-text input, .widget-dropdown select {{
            background-color: {card_bg};
            color: {text_color};
            border: 1px solid {border_color};
        }}

        .widget-checkbox input[type="checkbox"] {{
            filter: {'none' if not dark_mode else 'invert(80%)'};
        }}

        .card {{
            background-color: {card_bg};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid {border_color};
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
    </style>
    """))

# Initialize theme
set_theme(DARK_MODE)

# Dark mode toggle button
def toggle_dark_mode(b):
    set_theme(not DARK_MODE)

dark_mode_button = widgets.ToggleButton(
    value=DARK_MODE,
    description=' 🌙  Dark Mode' if DARK_MODE else ' ☀️  Light Mode',
    tooltip='Toggle dark/light mode',
    button_style='',
    icon='moon' if DARK_MODE else 'sun'
)
dark_mode_button.observe(lambda change: toggle_dark_mode(change.new), 'value')

# === COMPANY INFORMATION ===
# UPDATED LOGO URL
LOGO_URL = "https://drive.google.com/uc?export=download&id=1RD27Gas035iUqe4Ucl3phFwxZPWfzlzn"
LINKTREE_URL = "https://linktr.ee/premiumplushome?utm_source=linktree_admin_share"
COMPANY_INFO = {
    "name": "PREMIUM HOME LTD",
    "address": "Iasonos 1, 1082, Nicosia Cyprus",
    "email": "info@premiumpluscy.eu",
    "phone": "+35722584081, +35797550946",
    "website": "www.premiumpluscy.eu",
    "linktree": LINKTREE_URL
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
    "floor_heating_m2": 50.00,
    "wc_ceramic_m2_material": 20.00 + (650/45.5), # Material cost per m2
    "wc_ceramic_m2_labor": 20.00, # Labor cost per m2
    "electrical_per_m2": 75.00, # New dynamic price per m2
    "plumbing_per_m2": 75.00, # New dynamic price per m2
    # Labor Prices
    "welding_labor_m2": 160.00,
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00,
    "plasterboard_labor_m2": 80.00,
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

# === CUSTOMER INFORMATION WIDGETS (Translated to English) ===
customer_title = widgets.HTML(value="<div class='section-title'>CUSTOMER INFORMATION (Optional)</div>")
customer_note = widgets.HTML(value="<div class='warning'>Note: Customer information is not mandatory. If left blank, it will be marked as 'GENERAL'.</div>")
customer_name = widgets.Text(
    description="Full Name:",
    value="GENERAL",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)
customer_company = widgets.Text(
    description="Company:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)
customer_address = widgets.Text(
    description="Address:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)
customer_city = widgets.Text(
    description="City:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)
customer_phone = widgets.Text(
    description="Phone:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)
customer_email = widgets.Text(
    description="Email:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)

# === PROJECT INFORMATION WIDGETS (Translated to English) ===
structure_type = widgets.ToggleButtons(
    options=['Light Steel', 'Heavy Steel'],
    description='Structure Type:',
    button_style='primary',
    style={'description_width': '120px'},
    layout={'width': '400px'}
)
plasterboard_option = widgets.Checkbox(
    value=True,
    description="Include Interior Plasterboard",
    indent=False,
    style={'description_width': '120px'}
)
width_input = widgets.FloatText(
    value=10,
    description="Width (m):",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
length_input = widgets.FloatText(
    value=8,
    description="Length (m):",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
height_input = widgets.FloatText(
    value=2.6,
    description="Height (m):",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
# Updated room configuration to Dropdown (Translated to English)
room_config_input = widgets.Dropdown(
    options=[
        'Empty Model',
        '1 Room',
        '1 Room + Shower / WC',
        '1 Room + Kitchen',
        '1 Room + Shower / WC + Kitchen',
        '2 Rooms + Shower / WC + Kitchen',
        '3 Rooms + 2 Showers / WC + Kitchen'
    ],
    value='1 Room + Shower / WC + Kitchen', # Set a default value
    description="Room Configuration:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)

# Steel Profile Quantities (Translated to English)
profile_count_label = widgets.HTML(
    value="<div class='section-title'>STEEL PROFILE QUANTITIES (For Light Steel)</div>"
       "<b>(per 6m piece)</b>"
)
profile_100x100_count = widgets.IntText(
    value=0,
    description="100x100x3 Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
profile_100x50_count = widgets.IntText(
    value=0,
    description="100x50x3 Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
profile_40x60_count = widgets.IntText(
    value=0,
    description="40x60x2 Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
profile_50x50_count = widgets.IntText(
    value=0,
    description="50x50x2 Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
profile_30x30_count = widgets.IntText(
    value=0,
    description="30x30x2 Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
profile_HEA160_count = widgets.IntText(
    value=0,
    description="HEA160 Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

# Additional Features (Translated to English)
heating_option = widgets.Checkbox(
    value=False,
    description="Include Floor Heating (50€/m²)",
    indent=False,
    style={'description_width': '120px'}
)
solar_option = widgets.Checkbox(
    value=False,
    description="Solar Energy System",
    indent=False,
    style={'description_width': '120px'}
)
solar_capacity = widgets.Dropdown(
    options=[('5 kW', 5), ('7.2 kW', 7.2), ('11 kW', 11)],
    value=5,
    description="Capacity:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
solar_price = widgets.FloatText(
    value=5 * FIYATLAR['solar_per_kw'], # Updated to use FIYATLAR
    description="Solar Price (€):",
    disabled=True,
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

# Windows and Doors Section (Translated to English)
window_input = widgets.IntText(
    value=4,
    description="Window Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
window_size = widgets.Text(
    value="100x100 cm",
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
sliding_door_input = widgets.IntText(
    value=0,
    description="Sliding Glass Door:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
sliding_door_size = widgets.Text(
    value="200x200 cm",
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
wc_window_input = widgets.IntText(
    value=1,
    description="WC Window Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
wc_window_size = widgets.Text(
    value="60x50 cm", # Updated WC window size
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
wc_sliding_door_input = widgets.IntText(
    value=0,
    description="WC Sliding Door:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
wc_sliding_door_size = widgets.Text(
    value="140x70 cm",
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
door_input = widgets.IntText(
    value=2,
    description="Door Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
door_size = widgets.Text(
    value="90x210 cm",
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

# Additional Equipment (Translated to English)
kitchen_input = widgets.Checkbox(
    value=True,
    description="Include Kitchen",
    indent=False,
    style={'description_width': '120px'}
)
shower_input = widgets.Checkbox(
    value=True,
    description="Include Shower/WC",
    indent=False,
    style={'description_width': '120px'}
)
wc_ceramic_input = widgets.Checkbox(
    value=False,
    description="WC Ceramic Floor/Walls", # Labor cost added
    indent=False,
    style={'description_width': '120px'}
)
wc_ceramic_area = widgets.FloatText(
    value=0,
    description="WC Ceramic Area (m²):",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
electrical_installation_input = widgets.Checkbox(
    value=False,
    description="Electrical Installation (with Materials)", # Dynamic price, materials included
    indent=False,
    style={'description_width': '120px'}
)
plumbing_installation_input = widgets.Checkbox(
    value=False,
    description="Plumbing Installation (with Materials)", # Dynamic price, materials included
    indent=False,
    style={'description_width': '120px'}
)
transportation_input = widgets.Checkbox(
    value=False,
    description="Include Transportation (500€)",
    indent=False,
    style={'description_width': '120px'}
)
wheeled_trailer_option = widgets.Checkbox(
    value=False,
    description="Wheeled Trailer", # Kept "Tekerlekli Römork (Wheeled Trailer)" as is
    indent=False,
    style={'description_width': '220px'}
)
wheeled_trailer_price_input = widgets.FloatText(
    value=0.0,
    description="Trailer Price (€):",
    disabled=True, # Initially disabled, enabled if checkbox is true
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
def update_trailer_price_input(change):
    wheeled_trailer_price_input.disabled = not change.new
wheeled_trailer_option.observe(update_trailer_price_input, names='value')

# Financial Settings (Translated to English)
profit_rate_input = widgets.Dropdown(
    options=[(f'{i}%', i/100) for i in range(5, 40, 5)], # 5, 10, ..., 35
    value=0.20,
    description="Profit Rate:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)
# Display VAT Rate directly
vat_rate_display = widgets.HTML(f"<div class='widget-label'>VAT Rate: {VAT_RATE*100:.0f}% (Fixed)</div>")

# Customer Notes (Translated to English)
customer_notes = widgets.Textarea(
    value='',
    description='Customer Notes:',
    style={'description_width': '120px'},
    layout={'width': '95%', 'height': '100px'}
)
# New Widget for PDF Language Selection
pdf_language_selector = widgets.Dropdown(
    options=[('English-Greek', 'en_gr'), ('Turkish', 'tr')],
    value='en_gr',
    description='Proposal PDF Language:',
    style={'description_width': '150px'},
    layout={'width': '300px'}
)

# === CALCULATION FUNCTIONS ===
def calculate_area(width, length, height):
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Formats currency professionally: €32,500.00"""
    if value >= 0:
        return f"€{value:,.2f}"
    return f"-€{-value:,.2f}" # Handle negative values

def calculate():
    width, length, height = width_input.value, length_input.value, height_input.value
    window_count, sliding_door_count = window_input.value, sliding_door_input.value
    wc_window_count, wc_sliding_door_count = wc_window_input.value, wc_sliding_door_input.value
    door_count = door_input.value

    # These keys (e.g., "100x100x3") match the 'description' of the IntText widgets
    manual_profile_counts = {
        "100x100x3": profile_100x100_count.value,
        "100x50x3": profile_100x50_count.value,
        "40x60x2": profile_40x60_count.value,
        "50x50x2": profile_50x50_count.value,
        "30x30x2": profile_30x30_count.value,
        "HEA160": profile_HEA160_count.value,
    }

    default_piece_length = 6.0
    areas = calculate_area(width, length, height)
    floor_area = areas["floor"]
    wall_area = areas["wall"]
    roof_area = areas["roof"]

    costs = []
    profile_analysis_details = []

    # Steel Structure
    if structure_type.value == 'Heavy Steel':
        total_price = floor_area * FIYATLAR["heavy_steel_m2"]
        costs.append({
            'Item': 'Heavy Steel Construction',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["heavy_steel_m2"],
            'Total (€)': total_price
        })

        total_price = floor_area * FIYATLAR["welding_labor_m2"]
        costs.append({
            'Item': 'Steel Welding Labor',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["welding_labor_m2"],
            'Total (€)': total_price
        })
    else: # Light Steel
        for profile_type_key, piece_count in manual_profile_counts.items():
            if piece_count > 0:
                profile_dict_key = f"steel_profile_{profile_type_key.lower()}"
                if profile_type_key == "HEA160": # Special case for HEA160 if its key is just 'hea160' in FIYATLAR
                    profile_dict_key = "steel_profile_hea160"

                unit_price_6m_piece = FIYATLAR.get(profile_dict_key)

                if unit_price_6m_piece is None:
                    print(f"Warning: Price for {profile_type_key} not found in FIYATLAR.")
                    continue

                total_price = piece_count * unit_price_6m_piece
                report_length_meters = piece_count * default_piece_length

                profile_analysis_details.append({
                    'Profile Type': profile_type_key,
                    'Count': piece_count,
                    'Unit Price (€)': unit_price_6m_piece,
                    'Total (€)': total_price
                })
                costs.append({
                    'Item': f"Steel Profile ({profile_type_key})",
                    'Quantity': f"{piece_count} pieces ({report_length_meters:.1f}m)",
                    'Unit Price (€)': unit_price_6m_piece,
                    'Total (€)': total_price
                })

        total_price = floor_area * FIYATLAR["welding_labor_m2"]
        costs.append({
            'Item': 'Steel Welding Labor',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["welding_labor_m2"],
            'Total (€)': total_price
        })

    # Cladding and Insulation
    total_price = roof_area * FIYATLAR["sandwich_panel_m2"]
    costs.append({
        'Item': 'Roof (Sandwich Panel)',
        'Quantity': f'{roof_area:.2f} m²',
        'Unit Price (€)': FIYATLAR["sandwich_panel_m2"],
        'Total (€)': total_price
    })

    total_price = wall_area * FIYATLAR["sandwich_panel_m2"]
    costs.append({
        'Item': 'Facade (Sandwich Panel)',
        'Quantity': f'{wall_area:.2f} m²',
        'Unit Price (€)': FIYATLAR["sandwich_panel_m2"],
        'Total (€)': total_price
    })

    total_price = (wall_area + roof_area) * FIYATLAR["panel_assembly_labor_m2"]
    costs.append({
        'Item': "Panel Assembly Labor",
        'Quantity': f"{(wall_area + roof_area):.2f} m²",
        'Unit Price (€)': FIYATLAR["panel_assembly_labor_m2"],
        'Total (€)': total_price
    })

    # Interior and Flooring
    if plasterboard_option.value:
        plasterboard_area = wall_area + roof_area
        total_price = plasterboard_area * FIYATLAR["plasterboard_material_m2"]
        costs.append({
            'Item': 'Plasterboard Material',
            'Quantity': f'{plasterboard_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["plasterboard_material_m2"],
            'Total (€)': total_price
        })

        total_price = plasterboard_area * FIYATLAR["plasterboard_labor_m2"]
        costs.append({
            'Item': 'Plasterboard Labor',
            'Quantity': f'{plasterboard_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["plasterboard_labor_m2"],
            'Total (€)': total_price
        })

    plywood_pieces_needed = math.ceil(floor_area / (1.22 * 2.44))
    total_price = plywood_pieces_needed * FIYATLAR["plywood_piece"]
    costs.append({
        'Item': 'Floor (Plywood Material)',
        'Quantity': plywood_pieces_needed,
        'Unit Price (€)': FIYATLAR["plywood_piece"],
        'Total (€)': total_price
    })

    total_price = floor_area * FIYATLAR["plywood_flooring_labor_m2"]
    costs.append({
        'Item': 'Floor (Plywood Labor)',
        'Quantity': f'{floor_area:.2f} m²',
        'Unit Price (€)': FIYATLAR["plywood_flooring_labor_m2"],
        'Total (€)': total_price
    })

    # Floor Heating
    if heating_option.value:
        total_price = floor_area * FIYATLAR["floor_heating_m2"]
        costs.append({
            'Item': 'Floor Heating System',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["floor_heating_m2"],
            'Total (€)': total_price
        })

    # Solar Energy System Cost (always add to cost breakdown if selected, but handle separately in final price)
    solar_cost = 0
    if solar_option.value:
        solar_cost = solar_capacity.value * FIYATLAR['solar_per_kw']
        costs.append({
            'Item': f'Solar Energy System ({solar_capacity.value} kW)',
            'Quantity': 1,
            'Unit Price (€)': solar_cost,
            'Total (€)': solar_cost
        })

    # Windows and Doors
    if window_count > 0:
        total_price = window_count * FIYATLAR["aluminum_window_piece"]
        costs.append({
            'Item': f'Window ({window_size.value})',
            'Quantity': window_count,
            'Unit Price (€)': FIYATLAR["aluminum_window_piece"],
            'Total (€)': total_price
        })

    if sliding_door_count > 0:
        total_price = sliding_door_count * FIYATLAR["sliding_glass_door_piece"]
        costs.append({
            'Item': f'Sliding Glass Door ({sliding_door_size.value})',
            'Quantity': sliding_door_count,
            'Unit Price (€)': FIYATLAR["sliding_glass_door_piece"],
            'Total (€)': total_price
        })

    if wc_window_count > 0:
        total_price = wc_window_count * FIYATLAR["wc_window_piece"]
        costs.append({
            'Item': f'WC Window ({wc_window_size.value})',
            'Quantity': wc_window_count,
            'Unit Price (€)': FIYATLAR["wc_window_piece"],
            'Total (€)': total_price
        })

    if wc_sliding_door_count > 0:
        total_price = wc_sliding_door_count * FIYATLAR["wc_sliding_door_piece"]
        costs.append({
            'Item': f'WC Sliding Door ({wc_sliding_door_size.value})',
            'Quantity': wc_sliding_door_count,
            'Unit Price (€)': FIYATLAR["wc_sliding_door_piece"],
            'Total (€)': total_price
        })

    if door_count > 0:
        total_price = door_count * FIYATLAR["door_piece"]
        costs.append({
            'Item': f'Door ({door_size.value})',
            'Quantity': door_count,
            'Unit Price (€)': FIYATLAR["door_piece"],
            'Total (€)': total_price
        })

    total_door_window_count = window_count + sliding_door_count + wc_window_count + wc_sliding_door_count + door_count
    if total_door_window_count > 0:
        total_price = total_door_window_count * FIYATLAR["door_window_assembly_labor_piece"]
        costs.append({
            'Item': 'Door/Window Assembly Labor',
            'Quantity': total_door_window_count,
            'Unit Price (€)': FIYATLAR["door_window_assembly_labor_piece"],
            'Total (€)': total_price
        })

    # Other Items
    total_price = floor_area * FIYATLAR["connection_element_m2"]
    costs.append({
        'Item': "Connection Elements",
        'Quantity': f"{floor_area:.2f} m²",
        'Unit Price (€)': FIYATLAR["connection_element_m2"],
        'Total (€)': total_price
    })

    if kitchen_input.value:
        costs.append({
            'Item': 'Kitchen Installation',
            'Quantity': 1,
            'Unit Price (€)': FIYATLAR["kitchen_installation_piece"],
            'Total (€)': FIYATLAR["kitchen_installation_piece"]
        })

    if shower_input.value:
        costs.append({
            'Item': 'Shower/WC Installation',
            'Quantity': 1,
            'Unit Price (€)': FIYATLAR["shower_wc_installation_piece"],
            'Total (€)': FIYATLAR["shower_wc_installation_piece"]
        })

    if wc_ceramic_input.value and wc_ceramic_area.value > 0:
        total_material_cost = wc_ceramic_area.value * FIYATLAR["wc_ceramic_m2_material"]
        total_labor_cost = wc_ceramic_area.value * FIYATLAR["wc_ceramic_m2_labor"]
        total_wc_ceramic_cost = total_material_cost + total_labor_cost
        costs.append({
            'Item': 'WC Ceramic (Material & Labor)',
            'Quantity': f"{wc_ceramic_area.value:.2f} m²",
            'Unit Price (€)': FIYATLAR["wc_ceramic_m2_material"] + FIYATLAR["wc_ceramic_m2_labor"],
            'Total (€)': total_wc_ceramic_cost
        })

    if electrical_installation_input.value:
        electrical_cost = floor_area * FIYATLAR["electrical_per_m2"]
        costs.append({
            'Item': 'Electrical Installation (with Materials)',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["electrical_per_m2"],
            'Total (€)': electrical_cost
        })

    if plumbing_installation_input.value:
        plumbing_cost = floor_area * FIYATLAR["plumbing_per_m2"]
        costs.append({
            'Item': 'Plumbing Installation (with Materials)',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': FIYATLAR["plumbing_per_m2"],
            'Total (€)': plumbing_cost
        })

    if transportation_input.value:
        costs.append({
            'Item': 'Transportation',
            'Quantity': 1,
            'Unit Price (€)': FIYATLAR["transportation"],
            'Total (€)': FIYATLAR["transportation"]
        })

    if wheeled_trailer_option.value and wheeled_trailer_price_input.value > 0:
        trailer_price = wheeled_trailer_price_input.value
        costs.append({
            'Item': 'Wheeled Trailer',
            'Quantity': 1,
            'Unit Price (€)': trailer_price,
            'Total (€)': trailer_price
        })

    # Financial Calculations
    # Calculate subtotal for the house only (excluding solar)
    house_subtotal = sum([item['Total (€)'] for item in costs if 'Solar' not in item['Item']])

    waste_cost = house_subtotal * FIRE_RATE
    total_house_cost = house_subtotal + waste_cost # Cost of house before profit/VAT

    profit = total_house_cost * profit_rate_input.value
    house_vat_base = total_house_cost + profit # Base for VAT for the house
    house_vat = house_vat_base * VAT_RATE
    house_sales_price = house_vat_base + house_vat # Final sales price for the house

    # The final sales price is the house price + the separate solar cost
    total_sales_price = house_sales_price + solar_cost

    # Additional financial details for internal report
    # Subtotal now includes solar for the internal report's accuracy
    subtotal = sum([item['Total (€)'] for item in costs])

    financial_summary_data = [
        ["Subtotal (All Items, Incl. Solar)", subtotal],
        [f"Waste Cost ({FIRE_RATE*100:.0f}%) (on House only)", waste_cost],
        ["Total Cost (House + Waste + Solar)", total_house_cost + solar_cost],
        [f"Profit ({profit_rate_input.value*100:.0f}%) (on House only)", profit],
        ["", ""], # Spacer
        ["House Price (VAT Included)", house_sales_price],
        ["Solar System Price (VAT Included)", solar_cost],
        ["TOTAL SALES PRICE", total_sales_price],
        ["", ""], # Spacer
        [f"VAT ({VAT_RATE*100:.0f}%)", house_vat], # Only show house VAT as solar is pre-calculated
        ["Annual Income Tax (23.5%) (approx.)", (total_house_cost + profit) * ANNUAL_INCOME_TAX_RATE],
        ["Monthly Accounting Expenses", MONTHLY_ACCOUNTING_EXPENSES],
        ["Monthly Office Rent", MONTHLY_OFFICE_RENT]
    ]

    # Formatted financial summary
    formatted_financial_summary = []
    for item, amount in financial_summary_data:
        if isinstance(amount, (int, float)):
            formatted_amount = format_currency(amount)
        else:
            formatted_amount = amount

        formatted_financial_summary.append({
            'Item': item,
            'Amount (€)': formatted_amount
        })

    # Process customer information
    customer_name_value = customer_name.value.strip() or "GENERAL"

    customer_info = {
        'name': customer_name_value,
        'company': customer_company.value or "",
        'address': customer_address.value or "",
        'city': customer_city.value or "",
        'phone': customer_phone.value or "",
        'email': customer_email.value or ""
    }

    return {
        'cost_breakdown': pd.DataFrame(costs),
        'financial_summary': pd.DataFrame(formatted_financial_summary),
        'profile_analysis': pd.DataFrame(profile_analysis_details),
        'notes': customer_notes.value,
        'total_sales_price': total_sales_price, # Total price
        'house_sales_price': house_sales_price, # Price for installments
        'solar_sales_price': solar_cost,      # Price for separate payment
        'area': floor_area,
        'width': width,
        'length': length,
        'height': height,
        'customer_info': customer_info,
        'project_details': {
            'width': width,
            'length': length,
            'height': height,
            'area': floor_area,
            'structure_type': structure_type.value,
            'plasterboard': plasterboard_option.value,
            'window_count': window_input.value,
            'window_size': window_size.value,
            'sliding_door_count': sliding_door_input.value,
            'sliding_door_size': sliding_door_size.value,
            'wc_window_count': wc_window_input.value,
            'wc_window_size': wc_window_size.value,
            'wc_sliding_door_count': wc_sliding_door_input.value,
            'wc_sliding_door_size': wc_sliding_door_size.value,
            'door_count': door_input.value,
            'door_size': door_size.value,
            'kitchen': kitchen_input.value,
            'shower': shower_input.value,
            'wc_ceramic': wc_ceramic_input.value,
            'wc_ceramic_area': wc_ceramic_area.value,
            'electrical': electrical_installation_input.value,
            'plumbing': plumbing_installation_input.value,
            'transportation': transportation_input.value,
            'heating': heating_option.value,
            'solar': solar_option.value,
            'solar_kw': solar_capacity.value,
            'solar_price': solar_cost,
            'vat_rate': VAT_RATE, # Fixed VAT
            'profit_rate': profit_rate_input.value,
            'room_configuration': room_config_input.value,
            'wheeled_trailer_included': wheeled_trailer_option.value,
            'wheeled_trailer_price': wheeled_trailer_price_input.value,
            'sales_price': total_sales_price # This is used for the contract
        }
    }

# === PDF CREATION FUNCTIONS ===
def create_pdf_download_link(pdf_bytes, filename):
    """Creates a download link for PDF files"""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a class="pdf-button" href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'

def get_company_logo(width_mm=35):
    """Gets the company logo and returns it as a ReportLab Image object."""
    try:
        response = requests.get(LOGO_URL, stream=True, allow_redirects=True)
        response.raise_for_status()

        img_buffer = io.BytesIO(response.content)
        logo_img = Image(img_buffer, width=width_mm*mm, height=width_mm*mm)
        logo_img.hAlign = 'RIGHT'
        return logo_img

    except requests.exceptions.RequestException as e:
        print(f"Error fetching logo from URL: {e}")
        return None
    except Exception as e:
        print(f"Error processing logo image: {e}")
        return None

def draw_footer(canvas, doc):
    """Draws the page footer with company info and Linktree catalog link"""
    canvas.saveState()
    # Company contact information
    footer_text = f"{COMPANY_INFO['address']} | {COMPANY_INFO['email']} | {COMPANY_INFO['phone']} | {COMPANY_INFO['website']}"
    canvas.setFont(f"{MAIN_FONT}", 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 18*mm, footer_text)
    # Linktree catalog link
    catalog_text = f"Catalog: {COMPANY_INFO['linktree']}"
    canvas.setFont(MAIN_FONT, 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 14*mm, catalog_text)
    # Page number
    page_num = canvas.getPageNumber()
    canvas.setFont(MAIN_FONT, 8)
    canvas.drawRightString(doc.width + doc.leftMargin, 10*mm, f"Page {page_num}")
    canvas.restoreState()

def _create_solar_appendix_elements_en_gr(solar_kw, solar_price, styles):
    """Generates the flowable elements for the solar system appendix (EN/GR)."""
    heading_style = styles['Heading']
    normal_bilingual_style = styles['NormalBilingual']
    price_total_style = styles['PriceTotal']

    elements = [
        PageBreak(),
        Paragraph("APPENDIX B: SOLAR ENERGY SYSTEM / ΠΑΡΑΡΤΗΜΑ Β: ΣΥΣΤΗΜΑ ΗΛΙΑΚΗΣ ΕΝΕΡΓΕΙΑΣ", heading_style),
        Spacer(1, 8*mm),
        Paragraph(f"Below are the details for the included <b>{solar_kw} kW</b> Solar Energy System. "
                  f"The price for this system is handled separately from the main house payment plan.<br/><br/>"
                  f"Ακολουθούν οι λεπτομέρειες για το συμπεριλαμβανόμενο Σύστημα Ηλιακής Ενέργειας <b>{solar_kw} kW</b>. "
                  f"Η τιμή για αυτό το σύστημα διαχειρίζεται ξεχωριστά από το πρόγραμμα πληρωμών του κυρίως σπιτιού.", normal_bilingual_style),
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

    # Wrap content in Paragraphs
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

def _create_solar_appendix_elements_tr(solar_kw, solar_price, styles):
    """Generates the flowable elements for the solar system appendix (TR)."""
    heading_style = styles['Heading']
    normal_tr_style = styles['NormalTR']
    price_total_style = styles['PriceTotal']

    elements = [
        PageBreak(),
        Paragraph("EK B: GÜNEŞ ENERJİ SİSTEMİ", heading_style),
        Spacer(1, 8*mm),
        Paragraph(f"Projeye dahil edilen <b>{solar_kw} kW</b> Güneş Enerji Sistemi'nin detayları aşağıdadır. "
                  f"Bu sistemin bedeli, ana ev ödeme planından ayrı olarak faturalandırılacaktır.", normal_tr_style),
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

def create_customer_proposal_pdf(house_price, solar_price, total_price, project_details, notes, customer_info, logo_img):
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

    def _header_footer(canvas, doc):
        canvas.saveState()
        # Header Logo
        if logo_img:
            logo_img.drawOn(canvas, doc.width + doc.leftMargin - logo_img.drawWidth, doc.height + doc.topMargin - logo_img.drawHeight)
        canvas.restoreState()
        # Footer
        draw_footer(canvas, doc)

    doc.onFirstPage = _header_footer
    doc.onLaterPages = _header_footer

    styles = getSampleStyleSheet()
    # Add custom bilingual style to the styles dictionary
    styles.add(ParagraphStyle(
        name='NormalBilingual', parent=styles['Normal'], fontSize=9, leading=12,
        spaceAfter=3, fontName=MAIN_FONT
    ))
    title_style = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER,
        spaceAfter=8, fontName=MAIN_FONT, textColor=colors.HexColor("#4a5568")
    )
    heading_style = ParagraphStyle(
        name='Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6, spaceBefore=12,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    )
    price_total_style = ParagraphStyle(
        name='PriceTotal', parent=styles['Heading1'], fontSize=22, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#c53030")
    )
    payment_heading_style = ParagraphStyle(
        name='PaymentHeading', parent=styles['Heading3'], fontSize=10, spaceAfter=4,
        spaceBefore=8, fontName=f"{MAIN_FONT}-Bold"
    )
    signature_style = ParagraphStyle(
        name='Signature', parent=styles['Normal'], fontSize=9, fontName=MAIN_FONT,
        alignment=TA_CENTER, leading=12
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
    elements.append(Paragraph("CUSTOMER & PROJECT INFORMATION / ΠΛΗΡΟΦΟΡΙΕΣ ΠΕΛΑΤΗ & ΕΡΓΟΥ", heading_style))

    customer_project_data = [
        [Paragraph("<b>Name / Όνομα:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['name']}", styles['NormalBilingual'])],
        [Paragraph("<b>Company / Εταιρεία:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['company'] or 'N/A'}", styles['NormalBilingual'])],
        [Paragraph("<b>Address / Διεύθυνση:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['address'] or 'N/A'}", styles['NormalBilingual'])],
        [Paragraph("<b>Phone / Τηλέφωνο:</b>", styles['NormalBilingual']), Paragraph(f"{customer_info['phone'] or 'N/A'}", styles['NormalBilingual'])],
    ]
    info_table = Table(customer_project_data, colWidths=[50*mm, 120*mm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # --- Technical Specifications Table ---
    elements.append(Paragraph("TECHNICAL SPECIFICATIONS / ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", heading_style))

    # Define styles for the spec table
    spec_heading_style = ParagraphStyle(name='SpecHead', parent=styles['Normal'], fontName=f"{MAIN_FONT}-Bold", fontSize=9)
    spec_text_style = styles['NormalBilingual']

    def get_yes_no(value):
        return 'Yes / Ναι' if value else 'No / Όχι'

    # Build the table data dynamically
    spec_data = [
        [Paragraph('<b>Dimension / Διαστάσεις</b>', spec_text_style), Paragraph(f"{project_details['width']}m x {project_details['length']}m x {project_details['height']}m ({project_details['area']:.2f} m²)", spec_text_style)],
        [Paragraph('<b>Structure / Δομή</b>', spec_text_style), Paragraph(f"{project_details['structure_type']} with Sandwich Panel facade & roof.", spec_text_style)],
        [Paragraph('<b>Interior / Εσωτερικό</b>', spec_text_style), Paragraph(f"Plywood Flooring. Plasterboard: {get_yes_no(project_details['plasterboard'])}", spec_text_style)],
        [Paragraph('<b>Openings / Ανοίγματα</b>', spec_text_style), Paragraph(f"Windows: {project_details['window_count']} ({project_details['window_size']})<br/>Doors: {project_details['door_count']} ({project_details['door_size']})<br/>Sliding Doors: {project_details['sliding_door_count']} ({project_details['sliding_door_size']})", spec_text_style)],
        [Paragraph('<b>Kitchen / Κουζίνα</b>', spec_text_style), Paragraph(get_yes_no(project_details['kitchen']), spec_text_style)],
        [Paragraph('<b>Shower/WC / Ντους/WC</b>', spec_text_style), Paragraph(get_yes_no(project_details['shower']), spec_text_style)],
    ]

    # Add electrical materials if included
    if project_details['electrical']:
        electrical_materials_en = "• Electrical Cables (3x2.5, 3x1.5 mm²)<br/>• Conduits and Pipes<br/>• Junction Boxes<br/>• Distribution Board (Fuse Box)<br/>• Circuit Breakers & RCD<br/>• Sockets and Switches<br/>• LED Spot Lighting<br/>• Grounding System"
        electrical_materials_gr = "• Ηλεκτρικά Καλώδια (3x2.5, 3x1.5 mm²)<br/>• Σωλήνες & Κανάλια<br/>• Κουτιά Διακλάδωσης<br/>• Πίνακας Ασφαλειών<br/>• Ασφάλειες & Ρελέ Διαρροής<br/>• Πρίζες & Διακόπτες<br/>• Φωτισμός LED Spot<br/>• Σύστημα Γείωσης"
        spec_data.append([Paragraph('<b>Electrical / Ηλεκτρολογικά</b>', spec_text_style), Paragraph(f"{electrical_materials_en}<br/><br/>{electrical_materials_gr}", spec_text_style)])

    # Add plumbing materials if included
    if project_details['plumbing']:
        plumbing_materials_en = "<b>Clean Water:</b><br/>• PPRC Pipes<br/>• Faucets, Shower Head<br/><b>Wastewater:</b><br/>• PVC Pipes (50/100mm)<br/>• Siphons & drains"
        plumbing_materials_gr = "<b>Καθαρό Νερό:</b><br/>• Σωλήνες PPRC<br/>• Μπαταρίες, Κεφαλή Ντους<br/><b>Ακάθαρτο Νερό:</b><br/>• Σωλήνες PVC (50/100mm)<br/>• Σιφώνια & αποχετεύσεις"
        spec_data.append([Paragraph('<b>Plumbing / Υδραυλικά</b>', spec_text_style), Paragraph(f"{plumbing_materials_en}<br/><br/>{plumbing_materials_gr}", spec_text_style)])

    spec_data.extend([
        [Paragraph('<b>Floor Heating / Ενδοδαπέδια</b>', spec_text_style), Paragraph(get_yes_no(project_details['heating']), spec_text_style)],
        [Paragraph('<b>Solar System / Ηλιακό Σύστημα</b>', spec_text_style), Paragraph(f"{get_yes_no(project_details['solar'])} ({project_details['solar_kw']} kW)", spec_text_style)],
    ])

    spec_table = Table(spec_data, colWidths=[50*mm, 120*mm])
    spec_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f4f4f4")),
    ]))
    elements.append(spec_table)

    if notes.strip():
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("CUSTOMER NOTES / ΣΗΜΕΙΩΣΕΙΣ ΠΕΛΑΤΗ", heading_style))
        elements.append(Paragraph(notes, styles['NormalBilingual']))

    # --- Final Page Content (Price, Payment, Signatures) ---
    final_page_elements = [Spacer(1, 12*mm)]

    # New payment plan logic
    if solar_price > 0:
        final_page_elements.append(Paragraph("PRICE & PAYMENT SCHEDULE / ΤΙΜΗ & ΠΡΟΓΡΑΜΜΑ ΠΛΗΡΩΜΩΝ", heading_style))
        payment_data_h = [
            [Paragraph("<b>Main House Price / Τιμή Κυρίως Σπιτιού</b>", payment_heading_style), Paragraph(f"<b>{format_currency(house_price)}</b>", payment_heading_style)],
            [Paragraph("<b>Solar System Price / Τιμή Ηλιακού Συστήματος</b>", payment_heading_style), Paragraph(f"<b>{format_currency(solar_price)}</b>", payment_heading_style)],
            [Paragraph("<b>TOTAL PRICE / ΣΥΝΟΛΙΚΗ ΤΙΜΗ</b>", payment_heading_style), Paragraph(f"<b>{format_currency(total_price)}</b>", payment_heading_style)],
        ]
        payment_table_h = Table(payment_data_h, colWidths=[120*mm, 50*mm])
        payment_table_h.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        final_page_elements.append(payment_table_h)
        final_page_elements.append(Spacer(1, 8*mm))
        final_page_elements.append(Paragraph("Main House Payment Plan / Πρόγραμμα Πληρωμών Κυρίως Σπιτιού", payment_heading_style))
    else:
        final_page_elements.append(Paragraph("TOTAL SALES PRICE (VAT Included) / ΣΥΝΟΛΙΚΗ ΤΙΜΗ ΠΩΛΗΣΗΣ (με ΦΠΑ)", heading_style))
        final_page_elements.append(Paragraph(format_currency(total_price), price_total_style))
        final_page_elements.append(Spacer(1, 8*mm))
        final_page_elements.append(Paragraph("PAYMENT SCHEDULE / ΠΡΟΓΡΑΜΜΑ ΠΛΗΡΩΜΩΝ", heading_style))

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
    final_page_elements.append(Spacer(1, 25*mm))

    signature_data = [
        [Paragraph("_____________________________<br/>Buyer / Αγοραστής", signature_style),
         Paragraph("_____________________________<br/>Seller / Πωλητής", signature_style)]
    ]
    signature_table = Table(signature_data, colWidths=[doc.width/2, doc.width/2], hAlign='CENTER')
    signature_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
    final_page_elements.append(signature_table)

    elements.append(KeepTogether(final_page_elements))

    # Add Solar Appendix if applicable
    if project_details['solar']:
        solar_elements = _create_solar_appendix_elements_en_gr(project_details['solar_kw'], project_details['solar_price'], {'Heading': heading_style, 'NormalBilingual': styles['NormalBilingual'], 'PriceTotal': price_total_style})
        elements.extend(solar_elements)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_customer_proposal_pdf_tr(house_price, solar_price, total_price, project_details, notes, customer_info, logo_img):
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

    def _header_footer(canvas, doc):
        canvas.saveState()
        if logo_img:
            logo_img.drawOn(canvas, doc.width + doc.leftMargin - logo_img.drawWidth, doc.height + doc.topMargin - logo_img.drawHeight)
        canvas.restoreState()
        draw_footer(canvas, doc)

    doc.onFirstPage = _header_footer
    doc.onLaterPages = _header_footer

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='NormalTR', parent=styles['Normal'], fontSize=9, leading=12,
        spaceAfter=3, fontName=MAIN_FONT
    ))
    title_style = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER,
        spaceAfter=8, fontName=MAIN_FONT, textColor=colors.HexColor("#4a5568")
    )
    heading_style = ParagraphStyle(
        name='Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6, spaceBefore=12,
        fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    )
    price_total_style = ParagraphStyle(
        name='PriceTotal', parent=styles['Heading1'], fontSize=22, alignment=TA_CENTER,
        spaceAfter=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#c53030")
    )
    payment_heading_style = ParagraphStyle(
        name='PaymentHeading', parent=styles['Heading3'], fontSize=10, spaceAfter=4,
        spaceBefore=8, fontName=f"{MAIN_FONT}-Bold"
    )
    signature_style = ParagraphStyle(
        name='Signature', parent=styles['Normal'], fontSize=9, fontName=MAIN_FONT,
        alignment=TA_CENTER, leading=12
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
    elements.append(Paragraph("MÜŞTERİ VE PROJE BİLGİLERİ", heading_style))

    customer_project_data = [
        [Paragraph("<b>Adı Soyadı:</b>", styles['NormalTR']), Paragraph(f"{customer_info['name']}", styles['NormalTR'])],
        [Paragraph("<b>Firma:</b>", styles['NormalTR']), Paragraph(f"{customer_info['company'] or 'Yok'}", styles['NormalTR'])],
        [Paragraph("<b>Adres:</b>", styles['NormalTR']), Paragraph(f"{customer_info['address'] or 'Yok'}", styles['NormalTR'])],
        [Paragraph("<b>Telefon:</b>", styles['NormalTR']), Paragraph(f"{customer_info['phone'] or 'Yok'}", styles['NormalTR'])],
    ]
    info_table = Table(customer_project_data, colWidths=[50*mm, 120*mm])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # --- Technical Specifications Table ---
    elements.append(Paragraph("TEKNİK ÖZELLİKLER", heading_style))

    def get_var_yok(value):
        return 'Var' if value else 'Yok'

    spec_data = [
        [Paragraph('<b>Boyutlar</b>', styles['NormalTR']), Paragraph(f"{project_details['width']}m x {project_details['length']}m x {project_details['height']}m ({project_details['area']:.2f} m²)", styles['NormalTR'])],
        [Paragraph('<b>Yapı</b>', styles['NormalTR']), Paragraph(f"{project_details['structure_type']}, Sandviç Panel cephe & çatı.", styles['NormalTR'])],
        [Paragraph('<b>İç Mekan</b>', styles['NormalTR']), Paragraph(f"Plywood Zemin. Alçıpan: {get_var_yok(project_details['plasterboard'])}", styles['NormalTR'])],
        [Paragraph('<b>Doğramalar</b>', styles['NormalTR']), Paragraph(f"Pencereler: {project_details['window_count']} adet ({project_details['window_size']})<br/>Kapılar: {project_details['door_count']} adet ({project_details['door_size']})<br/>Sürme Kapılar: {project_details['sliding_door_count']} adet ({project_details['sliding_door_size']})", styles['NormalTR'])],
        [Paragraph('<b>Mutfak</b>', styles['NormalTR']), Paragraph(get_var_yok(project_details['kitchen']), styles['NormalTR'])],
        [Paragraph('<b>Duş/WC</b>', styles['NormalTR']), Paragraph(get_var_yok(project_details['shower']), styles['NormalTR'])],
    ]

    if project_details['electrical']:
        electrical_materials = "• Elektrik Kabloları (3x2.5, 3x1.5 mm²)<br/>• Spiral Borular ve Kanallar<br/>• Buatlar<br/>• Sigorta Kutusu<br/>• Sigortalar & Kaçak Akım Rölesi<br/>• Prizler ve Anahtarlar<br/>• LED Spot Aydınlatma<br/>• Topraklama Sistemi"
        spec_data.append([Paragraph('<b>Elektrik Tesisatı</b>', styles['NormalTR']), Paragraph(electrical_materials, styles['NormalTR'])])

    if project_details['plumbing']:
        plumbing_materials = "<b>Temiz Su:</b><br/>• PPRC Borular<br/>• Bataryalar, Duş Başlığı<br/><b>Atık Su:</b><br/>• PVC Gider Boruları (50/100mm)<br/>• Sifonlar & Süzgeçler"
        spec_data.append([Paragraph('<b>Sıhhi Tesisat</b>', styles['NormalTR']), Paragraph(plumbing_materials, styles['NormalTR'])])

    spec_data.extend([
        [Paragraph('<b>Yerden Isıtma</b>', styles['NormalTR']), Paragraph(get_var_yok(project_details['heating']), styles['NormalTR'])],
        [Paragraph('<b>Güneş Enerjisi</b>', styles['NormalTR']), Paragraph(f"{get_var_yok(project_details['solar'])} ({project_details['solar_kw']} kW)", styles['NormalTR'])],
    ])

    spec_table = Table(spec_data, colWidths=[50*mm, 120*mm])
    spec_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f4f4f4")),
    ]))
    elements.append(spec_table)

    if notes.strip():
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("MÜŞTERİ NOTLARI", heading_style))
        elements.append(Paragraph(notes, styles['NormalTR']))

    # --- Final Page Content ---
    final_page_elements = [Spacer(1, 12*mm)]

    if solar_price > 0:
        final_page_elements.append(Paragraph("FİYAT VE ÖDEME PLANI", heading_style))
        payment_data_h = [
            [Paragraph("<b>Ana Ev Bedeli</b>", payment_heading_style), Paragraph(f"<b>{format_currency(house_price)}</b>", payment_heading_style)],
            [Paragraph("<b>Güneş Enerji Sistemi Bedeli</b>", payment_heading_style), Paragraph(f"<b>{format_currency(solar_price)}</b>", payment_heading_style)],
            [Paragraph("<b>TOPLAM BEDEL</b>", payment_heading_style), Paragraph(f"<b>{format_currency(total_price)}</b>", payment_heading_style)],
        ]
        payment_table_h = Table(payment_data_h, colWidths=[120*mm, 50*mm])
        payment_table_h.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        final_page_elements.append(payment_table_h)
        final_page_elements.append(Spacer(1, 8*mm))
        final_page_elements.append(Paragraph("Ana Ev Ödeme Planı", payment_heading_style))
    else:
        final_page_elements.append(Paragraph("TOPLAM SATIŞ FİYATI (KDV Dahil)", heading_style))
        final_page_elements.append(Paragraph(format_currency(total_price), price_total_style))
        final_page_elements.append(Spacer(1, 8*mm))
        final_page_elements.append(Paragraph("ÖDEME PLANI", heading_style))

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
    final_page_elements.append(Spacer(1, 25*mm))

    signature_data = [
        [Paragraph("_____________________________<br/>Alıcı", signature_style),
         Paragraph("_____________________________<br/>Satıcı", signature_style)]
    ]
    signature_table = Table(signature_data, colWidths=[doc.width/2, doc.width/2], hAlign='CENTER')
    signature_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
    final_page_elements.append(signature_table)

    elements.append(KeepTogether(final_page_elements))

    # Add Solar Appendix if applicable
    if project_details['solar']:
        solar_elements = _create_solar_appendix_elements_tr(project_details['solar_kw'], project_details['solar_price'], {'Heading': heading_style, 'NormalTR': styles['NormalTR'], 'PriceTotal': price_total_style})
        elements.extend(solar_elements)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_internal_cost_report_pdf(cost_breakdown_df, financial_summary_df, profile_analysis_df, project_details, customer_info, logo_img):
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
    def _header_footer(canvas, doc):
        canvas.saveState()
        if logo_img:
            logo_img.drawOn(canvas, doc.width + doc.leftMargin - logo_img.drawWidth, doc.height + doc.topMargin - logo_img.drawHeight)
        canvas.restoreState()
        draw_footer(canvas, doc)

    doc.onFirstPage = _header_footer
    doc.onLaterPages = _header_footer

    styles = getSampleStyleSheet()

    # Custom styles for Turkish report
    header_style = ParagraphStyle(
        name='Header', parent=styles['Normal'], fontSize=18, alignment=TA_CENTER,
        spaceAfter=20, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce")
    )
    section_heading_style = ParagraphStyle(
        name='SectionHeading', parent=styles['Heading2'], fontSize=12, spaceBefore=12,
        spaceAfter=6, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_LEFT
    )
    normal_tr_style = ParagraphStyle(
        name='NormalTR', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=4, fontName=MAIN_FONT
    )
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

    financial_table = Table(financial_data, colWidths=[100*mm, 70*mm])
    financial_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey),('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor("#f7fafc"), colors.white])]))
    elements.append(financial_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def create_sales_contract_pdf(customer_info, project_details, company_info, logo_img):
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
    def _header_footer(canvas, doc):
        canvas.saveState()
        if logo_img:
            logo_img.drawOn(canvas, doc.width + doc.leftMargin - logo_img.drawWidth, doc.height + doc.topMargin - logo_img.drawHeight)
        canvas.restoreState()
        # Page number only in contract footer
        canvas.setFont(MAIN_FONT, 8)
        canvas.drawRightString(doc.width + doc.leftMargin, 10*mm, f"Page {canvas.getPageNumber()}")

    doc.onFirstPage = _header_footer
    doc.onLaterPages = _header_footer

    styles = getSampleStyleSheet()
    # Define contract specific styles
    contract_heading_style = ParagraphStyle(
        name='ContractHeading', parent=styles['Heading2'], fontSize=14, spaceAfter=10,
        spaceBefore=15, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#3182ce"), alignment=TA_CENTER
    )
    contract_subheading_style = ParagraphStyle(
        name='ContractSubheading', parent=styles['Heading3'], fontSize=11, spaceAfter=6,
        spaceBefore=10, fontName=f"{MAIN_FONT}-Bold", textColor=colors.HexColor("#4a5568")
    )
    contract_normal_style = ParagraphStyle(
        name='ContractNormal', parent=styles['Normal'], fontSize=9, leading=12,
        spaceAfter=5, fontName=MAIN_FONT, alignment=TA_LEFT
    )
    contract_list_style = ParagraphStyle(
        name='ContractList', parent=styles['Normal'], fontSize=9, leading=12,
        spaceAfter=3, leftIndent=10*mm, fontName=MAIN_FONT
    )
    contract_signature_style = ParagraphStyle(
        name='ContractSignature', parent=styles['Normal'], fontSize=9, leading=12,
        alignment=TA_CENTER
    )

    elements = []
    # Title
    elements.append(Paragraph("SALES CONTRACT", contract_heading_style))
    elements.append(Spacer(1, 8*mm))

    # Parties involved
    elements.append(Paragraph(f"This Agreement is entered into as of this {datetime.now().strftime('%d')} day of {datetime.now().strftime('%B')}, {datetime.now().year} by and between,", contract_normal_style))
    elements.append(Paragraph(f"<b>{customer_info['name'].upper()}</b> (I.D. No: ____________________), hereinafter referred to as the \"Buyer,\" and", contract_normal_style))
    elements.append(Paragraph(f"<b>{company_info['name'].upper()}</b>, with a registered address at {company_info['address']}, hereinafter referred to as the \"Seller.\"", contract_normal_style))
    elements.append(Spacer(1, 8*mm))

    # Subject
    elements.append(Paragraph("Subject of the Agreement:", contract_subheading_style))
    elements.append(Paragraph(f"The Seller agrees to complete and deliver to the Buyer the LIGHT STEEL STRUCTURE CONSTRUCTION (Tiny House) at the address specified by the Buyer, in accordance with the specifications detailed in Appendix A.", contract_normal_style))
    elements.append(Spacer(1, 8*mm))

    # Sales Price and Payment Terms
    total_sales_price_formatted = format_currency(project_details['sales_price'])
    house_price = project_details['sales_price'] - project_details['solar_price']
    down_payment = house_price * 0.40
    remaining_balance = house_price - down_payment
    installment_amount = remaining_balance / 3

    elements.append(Paragraph("Sales Price and Payment Terms:", contract_subheading_style))
    elements.append(Paragraph(f"2.1. The total sales price is <b>{total_sales_price_formatted}</b> (VAT Included).", contract_list_style))
    elements.append(Paragraph("2.2. The payment shall be made according to the following schedule:", contract_list_style))
    elements.append(Paragraph(f"- Main House (Total: {format_currency(house_price)})", contract_list_style, bulletText=''))
    elements.append(Paragraph(f"  - 40% Down Payment: {format_currency(down_payment)} upon contract signing.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f"  - 20% First Installment: {format_currency(installment_amount)} upon completion of structure.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f"  - 20% Second Installment: {format_currency(installment_amount)} upon completion of interior works.", contract_list_style, bulletText='-'))
    elements.append(Paragraph(f"  - 20% Final Payment: {format_currency(installment_amount)} upon final delivery.", contract_list_style, bulletText='-'))
    if project_details['solar_price'] > 0:
        elements.append(Paragraph(f"- Solar System: {format_currency(project_details['solar_price'])} due upon contract signing.", contract_list_style, bulletText=''))

    elements.append(Spacer(1, 8*mm))

    # Delivery
    elements.append(Paragraph("Delivery and Handover:", contract_subheading_style))
    elements.append(Paragraph(f"3.1. The estimated delivery time is approximately {int(project_details['area'] / 5) + 10} business days from the date of contract signing and reception of down payment.", contract_list_style))
    elements.append(Paragraph("3.2. Any delays caused by Force Majeure events or by the Buyer shall extend the delivery period accordingly.", contract_list_style))
    elements.append(Spacer(1, 8*mm))

    # Signatures
    elements.append(Spacer(1, 20*mm))
    signature_table_data = [
        [Paragraph("<b>THE SELLER</b><br/><br/><br/>_____________________________<br/>For and on behalf of<br/>PREMIUM HOME LTD", contract_signature_style),
         Paragraph("<b>THE BUYER</b><br/><br/><br/>_____________________________<br/>Signature", contract_signature_style)]
    ]
    signature_table = Table(signature_table_data, colWidths=[doc.width/2 - 10*mm, doc.width/2 - 10*mm], hAlign='CENTER')
    elements.append(signature_table)
    elements.append(PageBreak())

    # APPENDIX "A"
    elements.append(Paragraph("APPENDIX \"A\" - SCOPE OF WORK", contract_heading_style))
    elements.append(Paragraph("The Light Steel Structure House will include the following features:", contract_normal_style))
    elements.append(Spacer(1, 5*mm))

    # Using a table for Appendix A
    def get_yes_no_en(value):
        return 'Yes' if value else 'No'

    appendix_data = [
        [Paragraph("<b>Dimension</b>", contract_subheading_style), Paragraph(f"{project_details['width']}m x {project_details['length']}m x {project_details['height']}m ({project_details['area']:.2f} m²)", contract_normal_style)],
        [Paragraph("<b>Structure</b>", contract_subheading_style), Paragraph(f"{project_details['structure_type']}, Sandwich Panel Roof & Facade", contract_normal_style)],
        [Paragraph("<b>Interior</b>", contract_subheading_style), Paragraph(f"Plywood flooring. Interior Walls: Plasterboard {get_yes_no_en(project_details['plasterboard'])}", contract_normal_style)],
        [Paragraph("<b>Openings</b>", contract_subheading_style), Paragraph(f"{project_details['window_count']} Windows, {project_details['door_count']} Doors, {project_details['sliding_door_count']} Sliding Doors", contract_normal_style)],
        [Paragraph("<b>Installations</b>", contract_subheading_style), Paragraph(f"Kitchen: {get_yes_no_en(project_details['kitchen'])}, Shower/WC: {get_yes_no_en(project_details['shower'])}, Electrical: {get_yes_no_en(project_details['electrical'])}, Plumbing: {get_yes_no_en(project_details['plumbing'])}", contract_normal_style)],
        [Paragraph("<b>Options</b>", contract_subheading_style), Paragraph(f"Floor Heating: {get_yes_no_en(project_details['heating'])}, Solar: {get_yes_no_en(project_details['solar'])}", contract_normal_style)]
    ]
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

# === UI COMPONENTS ===
# Customer Section
customer_section = widgets.VBox([
    customer_title,
    customer_note,
    widgets.HBox([customer_name, customer_company]),
    widgets.HBox([customer_address, customer_city]),
    widgets.HBox([customer_phone, customer_email])
], layout=widgets.Layout(margin='0 0 20px 0'))

# Project Details Section
project_details_section = widgets.VBox([
    widgets.HTML("<div class='section-title'>PROJECT DETAILS</div>"),
    widgets.HBox([structure_type, plasterboard_option]),
    widgets.HBox([width_input, length_input, height_input]),
    room_config_input # Updated to dropdown
], layout=widgets.Layout(margin='0 0 20px 0'))

# Steel Profile Quantities Section
steel_profile_section = widgets.VBox([
    profile_count_label,
    widgets.HBox([profile_100x100_count, profile_100x50_count]),
    widgets.HBox([profile_40x60_count, profile_50x50_count]),
    widgets.HBox([profile_30x30_count, profile_HEA160_count])
], layout=widgets.Layout(margin='0 0 20px 0'))

# Windows and Doors Section
windows_doors_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>WINDOWS AND DOORS</div>"),
    widgets.HBox([window_input, window_size]),
    widgets.HBox([sliding_door_input, sliding_door_size]),
    widgets.HBox([wc_window_input, wc_window_size]),
    widgets.HBox([wc_sliding_door_input, wc_sliding_door_size]),
    widgets.HBox([door_input, door_size]),
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Additional Equipment Section
equipment_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>ADDITIONAL EQUIPMENT</div>"),
    widgets.HBox([kitchen_input, shower_input], layout=widgets.Layout(justify_content='flex-start')), # Adjusted layout
    widgets.HBox([wc_ceramic_input, wc_ceramic_area], layout=widgets.Layout(justify_content='flex-start')),
    widgets.HBox([electrical_installation_input, plumbing_installation_input], layout=widgets.Layout(justify_content='flex-start')),
    widgets.HBox([transportation_input, heating_option], layout=widgets.Layout(justify_content='flex-start')),
    widgets.HBox([solar_option, solar_capacity, solar_price], layout=widgets.Layout(justify_content='flex-start')),
    widgets.HBox([wheeled_trailer_option, wheeled_trailer_price_input], layout=widgets.Layout(justify_content='flex-start')),
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Financial Settings Section
financial_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>FINANCIAL SETTINGS</div>"),
    profit_rate_input,
    vat_rate_display, # Display fixed VAT rate
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Customer Notes Section
notes_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>CUSTOMER SPECIAL REQUESTS AND NOTES</div>"),
    customer_notes,
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Main UI
ui = widgets.VBox([
    dark_mode_button,
    customer_section,
    project_details_section,
    steel_profile_section,
    windows_doors_section,
    equipment_section,
    financial_section,
    notes_section,
    pdf_language_selector # Add the language selector here
])

# Output area for results and PDF download
output_area = widgets.Output()

def on_calculate_button_clicked(b):
    with output_area:
        clear_output(wait=True)
        try:
            results = calculate()
            cost_df = results['cost_breakdown']
            financial_df = results['financial_summary']
            profile_df = results['profile_analysis']
            customer_info = results['customer_info']
            project_details = results['project_details']
            notes = results['notes']
            total_sales_price = results['total_sales_price']
            house_sales_price = results['house_sales_price']
            solar_sales_price = results['solar_sales_price']

            display(HTML("<h3>Cost Breakdown (Internal Report)</h3>"))
            # For display, format the numeric columns in cost_df
            cost_df_display = cost_df.copy()
            cost_df_display['Unit Price (€)'] = cost_df_display['Unit Price (€)'].apply(format_currency)
            cost_df_display['Total (€)'] = cost_df_display['Total (€)'].apply(format_currency)
            display(cost_df_display.style.set_table_attributes("class='dataframe'"))

            if not profile_df.empty and project_details['structure_type'] == 'Light Steel':
                display(HTML("<h3>Steel Profile Detailed Analysis (Internal Report)</h3>"))
                # Format currency columns for display, keeping original df for PDF
                profile_df_display = profile_df.copy()
                profile_df_display['Unit Price (€)'] = profile_df_display['Unit Price (€)'].apply(format_currency)
                profile_df_display['Total (€)'] = profile_df_display['Total (€)'].apply(format_currency)
                display(profile_df_display.style.set_table_attributes("class='dataframe'"))

            display(HTML("<h3>Financial Summary (Internal Report)</h3>"))
            display(financial_df.style.set_table_attributes("class='price-table'"))

            # Generate PDFs
            logo_img = get_company_logo()

            # Internal Cost Report PDF (Always Turkish)
            internal_pdf_bytes = create_internal_cost_report_pdf(cost_df, financial_df, profile_df, project_details, results['customer_info'], logo_img)
            internal_pdf_filename = f"Internal_Cost_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            display(HTML(f"<div class='pdf-container'><h4>Internal Cost Report (Turkish)</h4>{create_pdf_download_link(internal_pdf_bytes, internal_pdf_filename)}</div>"))

            # Customer Proposal PDF (Based on selection)
            if pdf_language_selector.value == 'en_gr':
                customer_pdf_bytes = create_customer_proposal_pdf(house_sales_price, solar_sales_price, total_sales_price, project_details, notes, customer_info, logo_img)
                customer_pdf_filename = f"Customer_Proposal_EN_GR_{customer_info['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                display(HTML(f"<div class='pdf-container'><h4>Customer Proposal (English-Greek)</h4>{create_pdf_download_link(customer_pdf_bytes, customer_pdf_filename)}</div>"))
            else: # Turkish version
                customer_pdf_bytes = create_customer_proposal_pdf_tr(house_sales_price, solar_sales_price, total_sales_price, project_details, notes, customer_info, logo_img)
                customer_pdf_filename = f"Customer_Proposal_TR_{customer_info['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                display(HTML(f"<div class='pdf-container'><h4>Customer Proposal (Turkish)</h4>{create_pdf_download_link(customer_pdf_bytes, customer_pdf_filename)}</div>"))

            # Sales Contract PDF
            sales_contract_pdf_bytes = create_sales_contract_pdf(customer_info, project_details, COMPANY_INFO, logo_img)
            sales_contract_pdf_filename = f"Sales_Contract_{customer_info['name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            display(HTML(f"<div class='pdf-container'><h4>Sales Contract</h4>{create_pdf_download_link(sales_contract_pdf_bytes, sales_contract_pdf_filename)}</div>"))

        except Exception as e:
            import traceback
            display(HTML(f"<div class='warning'>An error occurred: {e}<br><pre>{traceback.format_exc()}</pre></div>"))

calculate_button = widgets.Button(
    description="Calculate & Generate Proposals",
    button_style='success',
    icon='calculator',
    layout=widgets.Layout(margin='20px 0 0 0', width='auto')
)
calculate_button.on_click(on_calculate_button_clicked)

display(ui, calculate_button, output_area)
