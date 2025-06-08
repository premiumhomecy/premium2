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
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, SimpleDocTemplate, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import requests
from PIL import Image as PILImage

# === THEME AND FONT SETTINGS ===
DARK_MODE = False  # User can toggle dark mode

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
    description='🌙 Dark Mode' if DARK_MODE else '☀️ Light Mode',
    tooltip='Toggle dark/light mode',
    button_style='',
    icon='moon' if DARK_MODE else 'sun'
)
dark_mode_button.observe(lambda change: toggle_dark_mode(change), 'value')

# === COMPANY INFORMATION ===
LOGO_URL = "https://premiumpluscy.eu/wp-content/uploads/2024/05/pp-logo-2-1.png"
LINKTREE_URL = "https://linktr.ee/premiumplushome?utm_source=linktree_admin_share"
COMPANY_INFO = {
    "name": "PREMIUM PLUS CONSTRUCTION",
    "address": "Iasonos 1, 1082, Nicosia Cyprus",
    "email": "info@premiumpluscy.eu",
    "phone": "+35722584081, +35797550946",
    "website": "www.premiumpluscy.eu",
    "linktree": LINKTREE_URL
}

# === PRICE DEFINITIONS ===
FIYATLAR = {
    # Steel Profile Prices
    "steel_profile_100x100x3": 45.00,
    "steel_profile_100x50x3": 33.00,
    "steel_profile_40x60x2": 14.00,
    "steel_profile_50x50x2": 11.00,  # Changed from 40x40 to 50x50
    "steel_profile_30x30x2": 8.50,
    "steel_profile_HEA160": 155.00,

    # Material Prices
    "heavy_steel_m2": 400.00,
    "sandwich_panel_m2": 22.00,
    "plywood_piece": 44.44,
    "aluminum_window_piece": 250.00,
    "sliding_glass_door_piece": 300.00,  # Added sliding glass door
    "wc_window_piece": 120.00,
    "wc_sliding_door_piece": 150.00,  # Added WC sliding door
    "door_piece": 280.00,
    "kitchen_installation_piece": 1500.00,
    "shower_wc_installation_piece": 1000.00,
    "connection_element_m2": 1.50,
    "transportation": 500.00,
    "floor_heating_m2": 50.00,
    "wc_ceramic_m2": 20.00 + (650/45.5),  # WC ceramic (labor + material converted from TL to EUR)

    # Labor Prices
    "welding_labor_m2": 160.00,
    "panel_assembly_labor_m2": 5.00,
    "plasterboard_material_m2": 20.00,
    "plasterboard_labor_m2": 80.00,
    "plywood_flooring_labor_m2": 11.11,
    "door_window_assembly_labor_piece": 50.00,
    
    # Installation Prices
    "electrical_installation_price": 1200.00,
    "plumbing_installation_price": 1300.00,
    
    # Solar Price (1kW = 1250€)
    "solar_per_kw": 1250.00
}

FIRE_RATE = 0.05
VAT_RATE = 0.19

# === CUSTOMER INFORMATION WIDGETS ===
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

# === PROJECT INFORMATION WIDGETS ===
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

room_config_input = widgets.Text(
    value="1 room, 1 bathroom, 1 kitchen", 
    description="Room Configuration:",
    style={'description_width': '120px'},
    layout={'width': '400px'}
)

# Steel Profile Quantities
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

profile_50x50_count = widgets.IntText(  # Changed from 40x40 to 50x50
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

# Additional Features
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
    value=5 * 1250,
    description="Solar Price (€):",
    disabled=True,
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

# Windows and Doors Section
window_input = widgets.IntText(
    value=4, 
    description="Window Count:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

window_size = widgets.Text(
    value="100x100 cm",  # Updated to 1x1m
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

sliding_door_input = widgets.IntText(  # Added sliding glass door
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
    value="100x50 cm", 
    description="Size:",
    style={'description_width': '120px'},
    layout={'width': '200px'}
)

wc_sliding_door_input = widgets.IntText(  # Added WC sliding door
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

# Additional Equipment
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

wc_ceramic_input = widgets.Checkbox(  # Added WC ceramic option
    value=False, 
    description="WC Ceramic Floor/Walls",
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
    description="Include Electrical Installation",
    indent=False,
    style={'description_width': '120px'}
)

plumbing_installation_input = widgets.Checkbox(
    value=False, 
    description="Include Plumbing Installation",
    indent=False,
    style={'description_width': '120px'}
)

transportation_input = widgets.Checkbox(
    value=False, 
    description="Include Transportation (500€)",
    indent=False,
    style={'description_width': '120px'}
)

# Financial Settings
profit_rate_input = widgets.FloatSlider(
    value=0.20, 
    min=0.0, 
    max=0.50, 
    step=0.01, 
    description="Profit Rate:", 
    readout_format='.0%',
    style={'description
    'description_width': '120px'},
    layout={'width': '400px'}
)

vat_rate_input = widgets.FloatSlider(
    value=VAT_RATE, 
    min=0.0, 
    max=0.25, 
    step=0.01, 
    description="VAT Rate:", 
    readout_format='.0%',
    style={'description_width': '120px'},
    layout={'width': '400px'}
)

# Customer Notes
customer_notes = widgets.Textarea(
    value='',
    description='Customer Notes:',
    style={'description_width': '120px'},
    layout={'width': '95%', 'height': '100px'}
)

# === CALCULATION FUNCTIONS ===
def calculate_area(width, length, height):
    floor_area = width * length
    wall_area = math.ceil(2 * (width + length) * height)
    roof_area = floor_area
    return {"floor": floor_area, "wall": wall_area, "roof": roof_area}

def format_currency(value):
    """Formats currency professionally: €32,500.00"""
    if value >= 1000:
        return f"€{value:,.2f}"
    return f"€{value:.2f}"

def calculate():
    width, length, height = width_input.value, length_input.value, height_input.value
    window_count, sliding_door_count = window_input.value, sliding_door_input.value
    wc_window_count, wc_sliding_door_count = wc_window_input.value, wc_sliding_door_input.value
    door_count = door_input.value
    
    manual_profile_counts = {
        "100x100x3": profile_100x100_count.value,
        "100x50x3": profile_100x50_count.value,
        "40x60x2": profile_40x60_count.value,
        "50x50x2": profile_50x50_count.value,  # Changed from 40x40 to 50x50
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
            'Unit Price (€)': format_currency(FIYATLAR["heavy_steel_m2"]),
            'Total (€)': format_currency(total_price)
        })
        
        total_price = floor_area * FIYATLAR["welding_labor_m2"]
        costs.append({
            'Item': 'Steel Welding Labor',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': format_currency(FIYATLAR["welding_labor_m2"]),
            'Total (€)': format_currency(total_price)
        })
    else:
        for profile_type, piece_count in manual_profile_counts.items():
            if piece_count > 0:
                profile_key_clean = profile_type.lower().replace('x', '').replace(' ', '')
                unit_price_6m_piece = FIYATLAR.get(f"steel_profile_{profile_key_clean}")
                if unit_price_6m_piece is None:
                    continue
                total_price = piece_count * unit_price_6m_piece
                report_length_meters = piece_count * default_piece_length
                profile_analysis_details.append({
                    'Profile Type': profile_type,
                    'Count': piece_count,
                    'Unit Price (€)': unit_price_6m_piece,
                    'Total (€)': total_price
                })
                costs.append({
                    'Item': f"Steel Profile ({profile_type})",
                    'Quantity': f"{piece_count} pieces ({report_length_meters:.1f}m)",
                    'Unit Price (€)': format_currency(unit_price_6m_piece),
                    'Total (€)': format_currency(total_price)
                })
        
        total_price = floor_area * FIYATLAR["welding_labor_m2"]
        costs.append({
            'Item': 'Steel Welding Labor',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': format_currency(FIYATLAR["welding_labor_m2"]),
            'Total (€)': format_currency(total_price)
        })

    # Cladding and Insulation
    total_price = roof_area * FIYATLAR["sandwich_panel_m2"]
    costs.append({
        'Item': 'Roof (Sandwich Panel)',
        'Quantity': f'{roof_area:.2f} m²',
        'Unit Price (€)': format_currency(FIYATLAR["sandwich_panel_m2"]),
        'Total (€)': format_currency(total_price)
    })
    
    total_price = wall_area * FIYATLAR["sandwich_panel_m2"]
    costs.append({
        'Item': 'Facade (Sandwich Panel)',
        'Quantity': f'{wall_area:.2f} m²',
        'Unit Price (€)': format_currency(FIYATLAR["sandwich_panel_m2"]),
        'Total (€)': format_currency(total_price)
    })
    
    total_price = (wall_area + roof_area) * FIYATLAR["panel_assembly_labor_m2"]
    costs.append({
        'Item': "Panel Assembly Labor",
        'Quantity': f"{(wall_area + roof_area):.2f} m²",
        'Unit Price (€)': format_currency(FIYATLAR["panel_assembly_labor_m2"]),
        'Total (€)': format_currency(total_price)
    })

    # Interior and Flooring
    if plasterboard_option.value:
        plasterboard_area = wall_area + roof_area
        total_price = plasterboard_area * FIYATLAR["plasterboard_material_m2"]
        costs.append({
            'Item': 'Plasterboard Material', 
            'Quantity': f'{plasterboard_area:.2f} m²',
            'Unit Price (€)': format_currency(FIYATLAR["plasterboard_material_m2"]),
            'Total (€)': format_currency(total_price)
        })
        
        total_price = plasterboard_area * FIYATLAR["plasterboard_labor_m2"]
        costs.append({
            'Item': 'Plasterboard Labor', 
            'Quantity': f'{plasterboard_area:.2f} m²',
            'Unit Price (€)': format_currency(FIYATLAR["plasterboard_labor_m2"]),
            'Total (€)': format_currency(total_price)
        })

    plywood_pieces_needed = math.ceil(floor_area / (1.22 * 2.44))
    total_price = plywood_pieces_needed * FIYATLAR["plywood_piece"]
    costs.append({
        'Item': 'Floor (Plywood Material)',
        'Quantity': plywood_pieces_needed,
        'Unit Price (€)': format_currency(FIYATLAR["plywood_piece"]),
        'Total (€)': format_currency(total_price)
    })
    
    total_price = floor_area * FIYATLAR["plywood_flooring_labor_m2"]
    costs.append({
        'Item': 'Floor (Plywood Labor)',
        'Quantity': f'{floor_area:.2f} m²',
        'Unit Price (€)': format_currency(FIYATLAR["plywood_flooring_labor_m2"]),
        'Total (€)': format_currency(total_price)
    })

    # Floor Heating
    if heating_option.value:
        total_price = floor_area * FIYATLAR["floor_heating_m2"]
        costs.append({
            'Item': 'Floor Heating System',
            'Quantity': f'{floor_area:.2f} m²',
            'Unit Price (€)': format_currency(FIYATLAR["floor_heating_m2"]),
            'Total (€)': format_currency(total_price)
        })

    # Solar Energy System
    if solar_option.value:
        solar_price_value = solar_capacity.value * FIYATLAR['solar_per_kw']
        costs.append({
            'Item': f'Solar Energy System ({solar_capacity.value} kW)',
            'Quantity': 1,
            'Unit Price (€)': format_currency(solar_price_value),
            'Total (€)': format_currency(solar_price_value)
        })

    # Windows and Doors
    if window_count > 0:
        total_price = window_count * FIYATLAR["aluminum_window_piece"]
        costs.append({
            'Item': f'Window ({window_size.value})',
            'Quantity': window_count,
            'Unit Price (€)': format_currency(FIYATLAR["aluminum_window_piece"]),
            'Total (€)': format_currency(total_price)
        })
    
    if sliding_door_count > 0:  # Sliding glass door
        total_price = sliding_door_count * FIYATLAR["sliding_glass_door_piece"]
        costs.append({
            'Item': f'Sliding Glass Door ({sliding_door_size.value})',
            'Quantity': sliding_door_count,
            'Unit Price (€)': format_currency(FIYATLAR["sliding_glass_door_piece"]),
            'Total (€)': format_currency(total_price)
        })
    
    if wc_window_count > 0:
        total_price = wc_window_count * FIYATLAR["wc_window_piece"]
        costs.append({
            'Item': f'WC Window ({wc_window_size.value})',
            'Quantity': wc_window_count,
            'Unit Price (€)': format_currency(FIYATLAR["wc_window_piece"]),
            'Total (€)': format_currency(total_price)
        })
    
    if wc_sliding_door_count > 0:  # WC sliding door
        total_price = wc_sliding_door_count * FIYATLAR["wc_sliding_door_piece"]
        costs.append({
            'Item': f'WC Sliding Door ({wc_sliding_door_size.value})',
            'Quantity': wc_sliding_door_count,
            'Unit Price (€)': format_currency(FIYATLAR["wc_sliding_door_piece"]),
            'Total (€)': format_currency(total_price)
        })
    
    if door_count > 0:
        total_price = door_count * FIYATLAR["door_piece"]
        costs.append({
            'Item': f'Door ({door_size.value})',
            'Quantity': door_count,
            'Unit Price (€)': format_currency(FIYATLAR["door_piece"]),
            'Total (€)': format_currency(total_price)
        })
    
    total_door_window_count = window_count + sliding_door_count + wc_window_count + wc_sliding_door_count + door_count
    if total_door_window_count > 0:
        total_price = total_door_window_count * FIYATLAR["door_window_assembly_labor_piece"]
        costs.append({
            'Item': 'Door/Window Assembly Labor',
            'Quantity': total_door_window_count,
            'Unit Price (€)': format_currency(FIYATLAR["door_window_assembly_labor_piece"]),
            'Total (€)': format_currency(total_price)
        })
    
    # Other Items
    total_price = floor_area * FIYATLAR["connection_element_m2"]
    costs.append({
        'Item': "Connection Elements",
        'Quantity': f"{floor_area:.2f} m²",
        'Unit Price (€)': format_currency(FIYATLAR["connection_element_m2"]),
        'Total (€)': format_currency(total_price)
    })

    if kitchen_input.value:
        costs.append({
            'Item': 'Kitchen Installation',
            'Quantity': 1,
            'Unit Price (€)': format_currency(FIYATLAR["kitchen_installation_piece"]),
            'Total (€)': format_currency(FIYATLAR["kitchen_installation_piece"])
        })
    
    if shower_input.value:
        costs.append({
            'Item': 'Shower/WC Installation',
            'Quantity': 1,
            'Unit Price (€)': format_currency(FIYATLAR["shower_wc_installation_piece"]),
            'Total (€)': format_currency(FIYATLAR["shower_wc_installation_piece"])
        })
    
    if wc_ceramic_input.value and wc_ceramic_area.value > 0:  # Added WC ceramic
        total_price = wc_ceramic_area.value * FIYATLAR["wc_ceramic_m2"]
        costs.append({
            'Item': 'WC Ceramic Floor/Walls',
            'Quantity': f"{wc_ceramic_area.value:.2f} m²",
            'Unit Price (€)': format_currency(FIYATLAR["wc_ceramic_m2"]),
            'Total (€)': format_currency(total_price)
        })
    
    if electrical_installation_input.value: 
        costs.append({
            'Item': 'Electrical Installation',
            'Quantity': 1,
            'Unit Price (€)': format_currency(FIYATLAR["electrical_installation_price"]),
            'Total (€)': format_currency(FIYATLAR["electrical_installation_price"])
        })
    
    if plumbing_installation_input.value: 
        costs.append({
            'Item': 'Plumbing Installation',
            'Quantity': 1,
            'Unit Price (€)': format_currency(FIYATLAR["plumbing_installation_price"]),
            'Total (€)': format_currency(FIYATLAR["plumbing_installation_price"])
        })
    
    if transportation_input.value:
        costs.append({
            'Item': 'Transportation',
            'Quantity': 1,
            'Unit Price (€)': format_currency(FIYATLAR["transportation"]),
            'Total (€)': format_currency(FIYATLAR["transportation"])
        })

    # Financial Calculations
    subtotal = sum([float(item['Total (€)'].replace('€', '').replace(',', '')) 
                     for item in costs if 'Total (€)' in item])
    
    waste_cost = subtotal * FIRE_RATE
    total_cost = subtotal + waste_cost
    profit = total_cost * profit_rate_input.value
    vat_base = total_cost + profit
    vat = vat_base * vat_rate_input.value
    sales_price = vat_base + vat
    
    financial_summary_data = [
        ["Subtotal", subtotal],
        [f"Waste Cost (%{FIRE_RATE*100:.0f})", waste_cost],
        ["Total Cost (Including Waste)", total_cost],
        [f"Profit (%{profit_rate_input.value*100:.0f})", profit],
        [f"VAT (%{vat_rate_input.value*100:.0f})", vat],
        ["Sales Price (VAT Included)", sales_price]
    ]
    
    # Formatted financial summary
    formatted_financial_summary = []
    for item, amount in financial_summary_data:
        formatted_financial_summary.append({
            'Item': item,
            'Amount (€)': format_currency(amount)
        })
    
    # Process customer information
    customer_name_value = customer_name.value.strip() or "GENERAL"
    
    return {
        'cost_breakdown': pd.DataFrame(costs),
        'financial_summary': pd.DataFrame(formatted_financial_summary),
        'profile_analysis': pd.DataFrame(profile_analysis_details),
        'notes': customer_notes.value,
        'sales_price': sales_price,
        'area': floor_area,
        'width': width,
        'length': length,
        'height': height,
        'customer_info': {
            'name': customer_name_value,
            'company': customer_company.value or "",
            'address': customer_address.value or "",
            'city': customer_city.value or "",
            'phone': customer_phone.value or "",
            'email': customer_email.value or ""
        },
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
            'solar_price': solar_capacity.value * FIYATLAR['solar_per_kw'],
            'vat_rate': vat_rate_input.value,
            'room_configuration': room_config_input.value
        }
    }

# === PDF CREATION FUNCTIONS ===
def create_pdf_download_link(pdf_bytes, filename):
    """Creates a download link for PDF files"""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a class="pdf-button" href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'

def get_company_logo(width=180):
    """Gets the company logo and returns it in base64 format"""
    try:
        response = requests.get(LOGO_URL)
        img = PILImage.open(io.BytesIO(response.content))
        
        # Resize the logo
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width, h_size), PILImage.LANCZOS)
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except:
        # Return None if logo cannot be loaded
        return None

def draw_header(canvas, doc, logo_data):
    """Draws the page header (logo and company information)"""
    # Logo
    if logo_data:
        logo = Image(io.BytesIO(base64.b64decode(logo_data)))
        logo.drawHeight = 40 * mm
        logo.drawWidth = 150 * mm
        logo.drawOn(canvas, doc.width + doc.leftMargin - 150*mm - 20, doc.height + doc.topMargin - 10*mm)

def draw_footer(canvas, doc):
    """Draws the page footer with company info and Linktree catalog link"""
    # Company contact information
    footer_text = f"{COMPANY_INFO['address']} | {COMPANY_INFO['email']} | {COMPANY_INFO['phone']} | {COMPANY_INFO['website']}"
    canvas.setFont(f"{MAIN_FONT}-Bold", 9)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 20*mm, footer_text)
    
    # Linktree catalog link
    catalog_text = f"Catalog: {COMPANY_INFO['linktree']}"
    canvas.setFont(f"{MAIN_FONT}", 8)
    canvas.drawCentredString(doc.width/2 + doc.leftMargin, 15*mm, catalog_text)
    
    # Page number
    page_num = canvas.getPageNumber()
    canvas.setFont(MAIN_FONT, 9)
    canvas.drawRightString(doc.width + doc.leftMargin, 10*mm, f"Page {page_num}")

def create_customer_pdf(sales_price, project_details, notes, customer_info, logo_data):
    """Creates a proposal PDF for the customer (English and Greek)"""
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
    
    # Custom styles with Greek font support
    bilingual_style = ParagraphStyle(
        name='Bilingual',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6,
        fontName=MAIN_FONT
    )
    
    bilingual_bold_style = ParagraphStyle(
        name='BilingualBold',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6,
        fontName=f"{MAIN_FONT}-Bold"
    )
    
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName=f"{MAIN_FONT}-Bold"
    )
    
    heading_style = ParagraphStyle(
        name='Heading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6,
        fontName=f"{MAIN_FONT}-Bold"
    )
    
    price_style = ParagraphStyle(
        name='Price',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName=f"{MAIN_FONT}-Bold"
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("PREFABRICATED HOUSE PROPOSAL / ΠΡΟΤΑΣΗ ΠΡΟΠΤΥΧΑΚΙΣΜΕΝΟΥ ΣΠΙΤΙΟΥ", title_style))
    elements.append(Paragraph(f"Date / Ημερομηνία: {datetime.now().strftime('%d/%m/%Y')}", bilingual_style))
    elements.append(Spacer(1, 12))
    
    # Customer Information
    elements.append(Paragraph("CUSTOMER INFORMATION / ΠΛΗΡΟΦΟΡΙΕΣ ΠΕΛΑΤΗ", heading_style))
    
    customer_data = [
        [f"Name / Όνομα: {customer_info['name']}"],
        [f"Company / Εταιρεία: {customer_info['company']}" if customer_info['company'] else ""],
        [f"Address / Διεύθυνση: {customer_info['address']}" if customer_info['address'] else ""],
        [f"City / Πόλη: {customer_info['city']}" if customer_info['city'] else ""],
        [f"Phone / Τηλέφωνο: {customer_info['phone']}" if customer_info['phone'] else ""],
        [f"Email / Ηλεκτρονικό Ταχυδρομείο: {customer_info['email']}" if customer_info['email'] else ""]
    ]
    
    for line in customer_data:
        if line[0]:  # Only add non-empty lines
            elements.append(Paragraph(line[0], bilingual_style))
    
    elements.append(Spacer(1, 12))
    
    # Project Details
    elements.append(Paragraph("PROJECT DETAILS / ΣΤΟΙΧΕΙΑ ΠΡΟΤΎΠΟΥ", heading_style))
    
    project_data = [
        [f"Dimensions / Διαστάσεις: {project_details['width']}m x {project_details['length']}m x {project_details['height']}m"],
        [f"Total Area / Συνολική Έκταση: {project_details['area']:.2f} m²"],
        [f"Room Configuration / Διαμόρφωση Δωματίων: {project_details['room_configuration']}"],
        [f"Estimated Delivery Time / Εκτιμώμενος Χρόνος Παράδοσης: {int(project_details['area'] / 5) + 10} days / ημέρες"]
    ]
    
    for line in project_data:
        elements.append(Paragraph(line[0], bilingual_style))
    
    elements.append(Spacer(1, 12))
    
    # Technical Specifications
    elements.append(Paragraph("TECHNICAL SPECIFICATIONS / ΤΕΧΝΙΚΑ ΧΑΡΑΚΤΗΡΙΣΤΙΚΑ", heading_style))
    
    specs_data = [
        [f"Structure Type / Τύπος Κατασκευής: {project_details['structure_type']}"],
        [f"Interior Plasterboard / Εσωτερικό Τσιμεντόβαμβακα: {'Included / Συμπεριλαμβάνεται' if project_details['plasterboard'] else 'Not included / Δεν συμπεριλαμβάνεται'}"],
        [f"Windows / Παράθυρα: {project_details['window_count']} units / τεμάχια ({project_details['window_size']})"],
        [f"Sliding Glass Doors / Ολισθαίνουσες Γυάλινες Πόρτες: {project_details['sliding_door_count']} units / τεμάχια ({project_details['sliding_door_size']})"],
        [f"WC Windows / Παράθυρα WC: {project_details['wc_window_count']} units / τεμάχια ({project_details['wc_window_size']})"],
        [f"WC Sliding Doors / Ολισθαίνουσες Πόρτες WC: {project_details['wc_sliding_door_count']} units / τεμάχια ({project_details['wc_sliding_door_size']})"],
        [f"Doors / Πόρτες: {project_details['door_count']} units / τεμάχια ({project_details['door_size']})"],
        [f"Kitchen / Κουζίνα: {'Included / Συμπεριλαμβάνεται' if project_details['kitchen'] else 'Not included / Δεν συμπεριλαμβάνεται'}"],
        [f"Shower/WC / Ντους/WC: {'Included / Συμπεριλαμβάνεται' if project_details['shower'] else 'Not included / Δεν συμπεριλαμβάνεται'}"],
        [f"WC Ceramic Floor/Walls / Κεραμικά WC: {'Included / Συμπεριλαμβάνεται' if project_details['wc_ceramic'] else 'Not included / Δεν συμπεριλαμβάνεται'}" + 
         (f" ({project_details['wc_ceramic_area']:.2f} m²)" if project_details['wc_ceramic'] else "")],
        [f"Electrical Installation / Ηλεκτρολογικές Εγκαταστάσεις: {'Included / Συμπεριλαμβάνεται' if project_details['electrical'] else 'Not included / Δεν συμπεριλαμβάνεται'}"],
        [f"Plumbing / Υδραυλικές Εγκαταστάσεις: {'Included / Συμπεριλαμβάνεται' if project_details['plumbing'] else 'Not included / Δεν συμπεριλαμβάνεται'}"],
        [f"Floor Heating / Υπόγεια Θέρμανση: {'Included / Συμπεριλαμβάνεται' if project_details['heating'] else 'Not included / Δεν συμπεριλαμβάνεται'}"],
        [f"Solar Energy System / Ηλιακό Σύστημα: {'Included / Συμπεριλαμβάνεται' if project_details['solar'] else 'Not included / Δεν συμπεριλαμβάνεται'} ({project_details['solar_kw']} kW)"],
        [f"Transportation / Μεταφορά: {'Included / Συμπεριλαμβάνεται' if project_details['transportation'] else 'Not included / Δεν συμπεριλαμβάνεται'}"]
    ]
    
    for line in specs_data:
        elements.append(Paragraph(line[0], bilingual_style))
    
    elements.append(Spacer(1, 15))
    
    # Total Sales Price
    elements.append(Paragraph("TOTAL SALES PRICE (VAT INCLUDED) / ΣΥΝΟΛΙΚΗ ΤΙΜΗ ΠΩΛΗΣΗΣ (ΜΕ ΦΠΑ", heading_style))
    elements.append(Paragraph(format_currency(sales_price), price_style))
    elements.append(Paragraph(f"(VAT %{project_details['vat_rate']*100:.0f} included) / (ΦΠΑ %{project_details['vat_rate']*100:.0f} συμπεριλαμβάνεται)", bilingual_style))
    elements.append(Spacer(1, 15))
    
    # Special Notes
    if notes:
        elements.append(Paragraph("SPECIAL NOTES / ΕΙΔΙΚΕΣ ΣΗΜΕΙΩΣΕΙΣ", heading_style))
        elements.append(Paragraph(notes, bilingual_style))
    
    # Catalog Link
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("For more models and options, please visit our catalog:", bilingual_style))
    elements.append(Paragraph(COMPANY_INFO['linktree'], bilingual_bold_style))
    
    # PDF creation function
    def on_first_page(canvas, doc):
        draw_header(canvas, doc, logo_data)
        draw_footer(canvas, doc)
        
    def on_later_pages(canvas, doc):
        draw_footer(canvas, doc)
    
    doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    buffer.seek(0)
    return buffer.getvalue()

def create_cost_report_pdf(project_details, cost_breakdown_df, financial_summary_df, profile_analysis_df, customer_info, logo_data):
    """Creates a cost report PDF in Turkish"""
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
    
    # Custom styles
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName=f"{MAIN_FONT}-Bold"
    )
    
    heading_style = ParagraphStyle(
        name='Heading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=6,
        fontName=f"{MAIN_FONT}-Bold"
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("MALİYET VE MALZEME RAPORU", title_style))
    elements.append(Paragraph(f"Oluşturulma Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Customer Information
    elements.append(Paragraph("MÜŞTERİ BİLGİLERİ", heading_style))
    
    customer_data = [
        [f"Adı Soyadı: {customer_info['name']}"],
        [f"Şirket: {customer_info['company']}" if customer_info['company'] else ""],
        [f"Adres: {customer_info['address']}" if customer_info['address'] else ""],
        [f"Şehir: {customer_info['city']}" if customer_info['city'] else ""],
        [f"Telefon: {customer_info['phone']}" if customer_info['phone'] else ""],
        [f"E-posta: {customer_info['email']}" if customer_info['email'] else ""]
    ]
    
    for line in customer_data:
        if line[0]:  # Only add non-empty lines
            elements.append(Paragraph(line[0], styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    # Project Details
    elements.append(Paragraph("PROJE BİLGİLERİ", heading_style))
    
    project_data = [
        [f"Boyutlar: {project_details['width']}m x {project_details['length']}m x {project_details['height']}m"],
        [f"Toplam Alan: {project_details['area']:.2f} m²"],
        [f"Yapı Tipi: {project_details['structure_type']}"],
        [f"Oda Konfigürasyonu: {project_details['room_configuration']}"]
    ]
    
    for line in project_data:
        elements.append(Paragraph(line[0], styles['Normal']))
    
    elements.append(Spacer(1, 12))
    
    # Steel Profile Analysis Table (For Light Steel)
    if not profile_analysis_df.empty:
        elements.append(Paragraph("ÇELİK PROFİL ANALİZİ", heading_style))
        
        data = [profile_analysis_df.columns.tolist()]
        for row in profile_analysis_df.values.tolist():
            formatted_row = list(row)
            formatted_row[2] = format_currency(row[2])
            formatted_row[3] = format_currency(row[3])
            data.append(formatted_row)
        
        table = Table(data, repeatRows=1, colWidths=[5*cm, 3*cm, 4*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), f"{MAIN_FONT}-Bold"),
            ('FONTNAME', (0,1), (-1,-1), MAIN_FONT),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#ddd')),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    # Cost Breakdown
    elements.append(Paragraph("MALİYET DÖKÜMÜ", heading_style))
    
    data = [cost_breakdown_df.columns.tolist()]
    for _, row in cost_breakdown_df.iterrows():
        formatted_row = [
            row['Item'],
            row['Quantity'],
            row['Unit Price (€)'],
            row['Total (€)']
        ]
        data.append(formatted_row)
    
    table = Table(data, repeatRows=1, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), f"{MAIN_FONT}-Bold"),
        ('FONTNAME', (0,1), (-1,-1), MAIN_FONT),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#ddd')),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Financial Summary
    elements.append(Paragraph("FİNANSAL ÖZET", heading_style))
    
    data = [financial_summary_df.columns.tolist()]
    for _, row in financial_summary_df.iterrows():
        formatted_row = [row['Item'], row['Amount (€)']]
        data.append(formatted_row)
    
    table = Table(data, repeatRows=1, colWidths=[12*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), f"{MAIN_FONT}-Bold"),
        ('FONTNAME', (0,1), (-1,-1), MAIN_FONT),
        ('FONTNAME', (0,-1), (-1,-1), f"{MAIN_FONT}-Bold"),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#ddd')),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LINEBELOW', (0,-2), (-1,-2), 1, colors.black),
    ]))
    elements.append(table)
    
    # PDF creation function
    def on_first_page(canvas, doc):
        draw_header(canvas, doc, logo_data)
        draw_footer(canvas, doc)
        
    def on_later_pages(canvas, doc):
        draw_footer(canvas, doc)
    
    doc.build(elements, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    buffer.seek(0)
    return buffer.getvalue()

# === MAIN CALCULATION BUTTON ===
calculate_button = widgets.Button(
    description="Calculate and Create PDFs", 
    button_style='success', 
    icon='calculator',
    layout=widgets.Layout(width='350px', height='45px')
)
output_area = widgets.Output()

def on_calculate_clicked(b):
    with output_area:
        clear_output(wait=True)
        try:
            result = calculate()
            
            # Show results
            display(HTML(f"<h3>Project Report: {result['width']}m x {result['length']}m = {result['area']:.2f} m²</h3>"))
            
            if not result['profile_analysis'].empty:
                display(HTML("<h4>Steel Profile Analysis</h4>"))
                display(result['profile_analysis'])
            
            display(HTML("<h4>Cost Breakdown</h4>"))
            display(result['cost_breakdown'])
            
            display(HTML("<h4>Financial Summary</h4>"))
            display(result['financial_summary'])
            
            if result['notes']:
                display(HTML(f"<h4>Special Notes</h4><p><i>{result['notes']}</i></p>"))
            
            # Get logo data
                        logo_data = get_company_logo()
            
            # Create PDFs
            proposal_pdf = create_customer_pdf(
                result['sales_price'], 
                result['project_details'], 
                result['notes'],
                result['customer_info'],
                logo_data
            )
            
            cost_pdf = create_cost_report_pdf(
                result['project_details'],
                result['cost_breakdown'],
                result['financial_summary'],
                result['profile_analysis'],
                result['customer_info'],
                logo_data
            )
            # PDF download links
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            proposal_filename = f"Proposal_Form_{timestamp}.pdf"
            cost_filename = f"Cost_Report_{timestamp}.pdf"
            
            display(HTML(f"""
            <div class="pdf-container">
                <h4>DOWNLOAD PDF FILES</h4>
                {create_pdf_download_link(proposal_pdf, proposal_filename)}
                {create_pdf_download_link(cost_pdf, cost_filename)}
                <p style="margin-top: 20px; font-size: 14px; color: #555;">
                    Use the buttons above to download PDF files.<br>
                    Your browser may prefer to open PDFs directly.
                </p>
            </div>
            """))
            
        except Exception as e:
            import traceback
            display(HTML(f"<div style='color:red; background-color:#ffe8e8; padding:15px; border-radius:8px; margin-top:20px;'><b>Error:</b> {str(e)}<br>{traceback.format_exc()}</div>"))

calculate_button.on_click(on_calculate_clicked)

# === UI LAYOUT ===
# Customer Information Section
customer_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    customer_title,
    customer_note,
    customer_name,
    customer_company,
    customer_address,
    customer_city,
    customer_phone,
    customer_email,
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Project Details Section
project_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>PROJECT DETAILS</div>"),
    widgets.HBox([structure_type, plasterboard_option]),
    widgets.HBox([width_input, length_input, height_input]),
    room_config_input,
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Windows and Doors Section
door_window_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>WINDOWS & DOORS</div>"),
    widgets.HBox([window_input, window_size]),
    widgets.HBox([sliding_door_input, sliding_door_size]),
    widgets.HBox([wc_window_input, wc_window_size]),
    widgets.HBox([wc_sliding_door_input, wc_sliding_door_size]),
    widgets.HBox([door_input, door_size]),
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Steel Profile Section
steel_profile_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>STEEL PROFILE QUANTITIES</div>"),
    profile_count_label,
    widgets.HBox([profile_100x100_count, profile_100x50_count]),
    widgets.HBox([profile_40x60_count, profile_50x50_count]),
    widgets.HBox([profile_30x30_count, profile_HEA160_count]),
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Additional Equipment Section
equipment_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>ADDITIONAL EQUIPMENT</div>"),
    widgets.HBox([kitchen_input, shower_input]),
    widgets.HBox([wc_ceramic_input, wc_ceramic_area]),
    widgets.HBox([electrical_installation_input, plumbing_installation_input]),
    transportation_input,
    heating_option,
    widgets.HBox([solar_option, solar_capacity, solar_price]),
    widgets.HTML("</div>")
], layout=widgets.Layout(margin='0 0 20px 0'))

# Financial Settings Section
financial_section = widgets.VBox([
    widgets.HTML("<div class='card'>"),
    widgets.HTML("<div class='section-title'>FINANCIAL SETTINGS</div>"),
    profit_rate_input,
    vat_rate_input,
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
    project_section,
    door_window_section,
    steel_profile_section,
    equipment_section,
    financial_section,
    notes_section,
    calculate_button,
    output_area
], layout=widgets.Layout(width='95%', margin='0 auto'))

display(ui)
