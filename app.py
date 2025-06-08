import streamlit as st
import pandas as pd
import math
import base64
import io
from datetime import datetime
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

# === FONT AYARLARI === (Türkçe karakter desteği için)
# Try to register Arial fonts for PDF generation.
# If Arial.ttf and Arial Bold.ttf are in the same directory as app.py, they will be used.
# Otherwise, it will fall back to Helvetica.
try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arial Bold.ttf'))
    MAIN_FONT = 'Arial'
except Exception:
    MAIN_FONT = 'Helvetica'

# === LOGO VE ŞİRKET BİLGİLERİ ===
LOGO_URL = "https://premiumpluscy.eu/wp-content/uploads/2024/05/pp-logo-2-1.png" # Lütfen bu URL'yi kontrol edin
LINKTREE_URL = "https://linktr.ee/premiumplushome?utm_source=linktree_admin_share"
COMPANY_INFO = {
    "name": "PREMIUM PLUS CONSTRUCTION",
    "address": "Iasonos 1, 1082, Nicosia Cyprus",
    "email": "info@premiumpluscy.eu",
    "phone": "+35722584081, +35797550946",
    "website": "www.premiumpluscy.eu",
    "linktree": LINKTREE_URL
}

# === Fiyat Tanımlamaları ===
FIYATLAR = {} # Initialize global FIYATLAR

def update_prices():
    """Defines and updates the global FIYATLAR dictionary with current prices."""
    global FIYATLAR
    FIYATLAR = {
        # Çelik Profil Fiyatları (per 6m piece for light steel)
        "celik_profil_100x100x3": 45.00,
        "celik_profil_100x50x3": 33.00,
        "celik_profil_40x60x2": 14.00,
        "celik_profil_40x40x2": 11.00,
        "celik_profil_30x30x2": 8.50,
        "celik_profil_HEA160": 155.00,

        # Malzeme Fiyatları
        "celik_agir_m2": 400.00,       # Heavy steel per m²
        "sandvic_panel_m2": 22.00,     # Sandwich panel per m²
        "plywood_adet": 44.44,         # Plywood per piece (approx 1.22x2.44m)
        "aluminyum_pencere_adet": 250.00, # Aluminum window per piece
        "wc_pencere_adet": 120.00,      # WC window per piece
        "kapi_adet": 280.00,            # Door per piece
        "mutfak_kurulum_adet": 1500.00, # Kitchen installation
        "dus_wc_kurulum_adet": 1000.00, # Shower/WC installation
        "baglanti_elemani_m2": 1.50,   # Connection elements per m²
        "tasinma": 500.00,              # Transportation/Shipping
        "yerden_isitma_m2": 50.00,      # Underfloor heating per m²

        # İşçilik Fiyatları
        "kaynak_iscilik_m2": 160.00,        # Welding labor per m²
        "panel_montaj_iscilik_m2": 5.00,    # Panel assembly labor per m²
        "alcipan_malzeme_m2": 20.00,        # Drywall material per m²
        "alcipan_iscilik_m2": 80.00,        # Drywall labor per m²
        "plywood_doseme_iscilik_m2": 11.11, # Plywood flooring labor per m²
        "kapi_pencere_montaj_iscilik_adet": 50.00, # Door/window installation labor per piece
        
        # Tesisat Fiyatları
        "elektrik_tesisat_fiyat": 1200.00,  # Electrical installation
        "su_tesisat_fiyat": 1300.00,        # Water installation
       
        # Solar Fiyatı (1kW = 1250€)
        "solar_per_kw": 1250.00             # Solar energy per kW
    }

# Load initial prices when the app starts
update_prices()

# Sabit Oranlar
FIRE_ORANI = 0.05 # Waste/Contingency rate
KDV_ORANI = 0.19  # VAT rate (default)

# === Hesaplama Fonksiyonları ===
def alan_hesapla(genislik, uzunluk, yukseklik):
    """Calculates ground, wall, and roof areas."""
    zemin_alani = genislik * uzunluk
    duvar_alani = math.ceil(2 * (genislik + uzunluk) * yukseklik)
    cati_alani = zemin_alani
    return {"zemin": zemin_alani, "duvar": duvar_alani, "cati": cati_alani}

def format_currency(value):
    """Formats a numeric value as a Euro currency string (e.g., €32.500,00)."""
    if value is None:
        return "N/A"
    # Convert to string with 2 decimal places, replace decimal point with comma
    # and use dot for thousands separator.
    s = f"{value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"€{s}"

def calculate_costs(
    yapi_tipi_val, alcipan_secenek_val, en, boy, yukseklik, oda_konfigurasyonu,
    profil_100x100_adet, profil_100x50_adet, profil_40x60_adet, profil_40x40_adet, profil_30x30_adet, profil_HEA160_adet,
    isitma_secenek_val, solar_secenek_val, solar_kapasite_val,
    pencere_ad, pencere_olcu, wc_pencere_ad, wc_pencere_olcu, kapi_ad, kapi_olcu,
    mutfak_input_val, dus_input_val, elektrik_tesisat_input_val, su_tesisat_input_val, tasinma_input_val,
    kar_orani, kdv_orani, musteri_notlari,
    customer_name_val, customer_company_val, customer_address_val, customer_city_val, customer_phone_val, customer_email_val
):
    """
    Performs detailed cost calculations for the construction project.
    Returns a dictionary containing cost breakdown, financial summary, and project details.
    """
    
    manuel_profil_adetleri = {
        "100x100x3": profil_100x100_adet,
        "100x50x3": profil_100x50_adet,
        "40x60x2": profil_40x60_adet,
        "40x40x2": profil_40x40_adet,
        "30x30x2": profil_30x30_adet,
        "HEA160": profil_HEA160_adet,
    }
    
    varsayilan_parca_boyutu = 6.0 # Default length of a steel profile piece in meters
    alanlar = alan_hesapla(en, boy, yukseklik)
    zemin_alani = alanlar["zemin"]
    duvar_alani = math.ceil(2 * (en + boy) * yukseklik) # Corrected to use en and boy
    cati_alani = zemin_alani
    
    maliyetler = [] # List to store detailed cost items
    profil_analizi_detaylari = [] # List to store steel profile breakdown

    # Çelik İskelet (Steel Frame) Costs
    if yapi_tipi_val == 'Ağır Çelik': # Heavy Steel
        toplam_fiyat = zemin_alani * FIYATLAR["celik_agir_m2"]
        maliyetler.append({
            'Kalem': 'Ağır Çelik Konstrüksiyon',
            'Miktar': f'{zemin_alani:.2f} m²',
            'Birim Fiyat (€)': format_currency(FIYATLAR["celik_agir_m2"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
        
        toplam_fiyat = zemin_alani * FIYATLAR["kaynak_iscilik_m2"]
        maliyetler.append({
            'Kalem': 'Çelik Kaynak İşçiliği',
            'Miktar': f'{zemin_alani:.2f} m²',
            'Birim Fiyat (€)': format_currency(FIYATLAR["kaynak_iscilik_m2"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
    else: # Hafif Çelik (Light Steel)
        for profil_tipi, adet_parca in manuel_profil_adetleri.items():
            if adet_parca > 0:
                # Get the base price per 6m piece for the steel profile type
                birim_fiyat_6m_parca = FIYATLAR.get(f"celik_profil_{profil_tipi.replace('x', '_').lower()}")
                if birim_fiyat_6m_parca is None:
                    # Fallback if specific key is not found, though it should be
                    birim_fiyat_6m_parca = 0.0
                
                toplam_fiyat = adet_parca * birim_fiyat_6m_parca
                rapor_miktari_metre = adet_parca * varsayilan_parca_boyutu
                profil_analizi_detaylari.append({
                    'Profil Tipi': profil_tipi,
                    'Adet': adet_parca,
                    'Birim Fiyat (€)': birim_fiyat_6m_parca,
                    'Toplam (€)': toplam_fiyat
                })
                maliyetler.append({
                    'Kalem': f"Çelik Profil ({profil_tipi})",
                    'Miktar': f"{adet_parca} adet ({rapor_miktari_metre:.1f}m)",
                    'Birim Fiyat (€)': format_currency(birim_fiyat_6m_parca),
                    'Toplam (€)': format_currency(toplam_fiyat)
                })
        
        toplam_fiyat = zemin_alani * FIYATLAR["kaynak_iscilik_m2"]
        maliyetler.append({
            'Kalem': 'Çelik Kaynak İşçiliği',
            'Miktar': f'{zemin_alani:.2f} m²',
            'Birim Fiyat (€)': format_currency(FIYATLAR["kaynak_iscilik_m2"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })

    # Kaplama ve Yalıtım (Cladding and Insulation)
    toplam_fiyat = cati_alani * FIYATLAR["sandvic_panel_m2"]
    maliyetler.append({
        'Kalem': 'Çatı (Sandviç Panel)',
        'Miktar': f'{cati_alani:.2f} m²',
        'Birim Fiyat (€)': format_currency(FIYATLAR["sandvic_panel_m2"]),
        'Toplam (€)': format_currency(toplam_fiyat)
    })
    
    toplam_fiyat = duvar_alani * FIYATLAR["sandvic_panel_m2"]
    maliyetler.append({
        'Kalem': 'Cephe (Sandviç Panel)',
        'Miktar': f'{duvar_alani:.2f} m²',
        'Birim Fiyat (€)': format_currency(FIYATLAR["sandvic_panel_m2"]),
        'Toplam (€)': format_currency(toplam_fiyat)
    })
    
    toplam_fiyat = (duvar_alani + cati_alani) * FIYATLAR["panel_montaj_iscilik_m2"]
    maliyetler.append({
        'Kalem': "Panel Montaj İşçiliği",
        'Miktar': f"{(duvar_alani + cati_alani):.2f} m²",
        'Birim Fiyat (€)': format_currency(FIYATLAR["panel_montaj_iscilik_m2"]),
        'Toplam (€)': format_currency(toplam_fiyat)
    })

    # İç Mekan ve Zemin (Interior and Flooring)
    if alcipan_secenek_val: # Drywall option selected
        alcipan_alani = duvar_alani + cati_alani # Drywall applies to walls and ceiling
        toplam_fiyat = alcipan_alani * FIYATLAR["alcipan_malzeme_m2"]
        maliyetler.append({
            'Kalem': 'Alçıpan Malzeme',
            'Miktar': f'{alcipan_alani:.2f} m²',
            'Birim Fiyat (€)': format_currency(FIYATLAR["alcipan_malzeme_m2"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
        
        toplam_fiyat = alcipan_alani * FIYATLAR["alcipan_iscilik_m2"]
        maliyetler.append({
            'Kalem': 'Alçıpan İşçilik',
            'Miktar': f'{alcipan_alani:.2f} m²',
            'Birim Fiyat (€)': format_currency(FIYATLAR["alcipan_iscilik_m2"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })

    plywood_adet_gerekli = math.ceil(zemin_alani / (1.22 * 2.44)) # Calculate plywood pieces needed (assuming 1.22x2.44m sheets)
    toplam_fiyat = plywood_adet_gerekli * FIYATLAR["plywood_adet"]
    maliyetler.append({
        'Kalem': 'Zemin (Plywood Malzeme)',
        'Miktar': plywood_adet_gerekli,
        'Birim Fiyat (€)': format_currency(FIYATLAR["plywood_adet"]),
        'Toplam (€)': format_currency(toplam_fiyat)
    })
    
    toplam_fiyat = zemin_alani * FIYATLAR["plywood_doseme_iscilik_m2"]
    maliyetler.append({
        'Kalem': 'Zemin (Plywood İşçilik)',
        'Miktar': f'{zemin_alani:.2f} m²',
        'Birim Fiyat (€)': format_currency(FIYATLAR["plywood_doseme_iscilik_m2"]),
        'Toplam (€)': format_currency(toplam_fiyat)
    })

    # Yerden Isıtma (Underfloor Heating)
    if isitma_secenek_val:
        toplam_fiyat = zemin_alani * FIYATLAR["yerden_isitma_m2"]
        maliyetler.append({
            'Kalem': 'Yerden Isıtma Sistemi',
            'Miktar': f'{zemin_alani:.2f} m²',
            'Birim Fiyat (€)': format_currency(FIYATLAR["yerden_isitma_m2"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })

    # Solar Energy System
    if solar_secenek_val and solar_kapasite_val > 0:
        solar_fiyat_deger = solar_kapasite_val * FIYATLAR['solar_per_kw']
        maliyetler.append({
            'Kalem': f'Solar Energy System ({solar_kapasite_val} kW)',
            'Miktar': 1,
            'Birim Fiyat (€)': format_currency(solar_fiyat_deger),
            'Toplam (€)': format_currency(solar_fiyat_deger)
        })

    # Kapı ve Pencereler (Doors and Windows)
    if pencere_ad > 0:
        toplam_fiyat = pencere_ad * FIYATLAR["aluminyum_pencere_adet"]
        maliyetler.append({
            'Kalem': f'Pencere ({pencere_olcu})',
            'Miktar': pencere_ad,
            'Birim Fiyat (€)': format_currency(FIYATLAR["aluminyum_pencere_adet"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
    if wc_pencere_ad > 0:
        toplam_fiyat = wc_pencere_ad * FIYATLAR["wc_pencere_adet"]
        maliyetler.append({
            'Kalem': f'WC Pencere ({wc_pencere_olcu})',
            'Miktar': wc_pencere_ad,
            'Birim Fiyat (€)': format_currency(FIYATLAR["wc_pencere_adet"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
    if kapi_ad > 0:
        toplam_fiyat = kapi_ad * FIYATLAR["kapi_adet"]
        maliyetler.append({
            'Kalem': f'Kapı ({kapi_olcu})',
            'Miktar': kapi_ad,
            'Birim Fiyat (€)': format_currency(FIYATLAR["kapi_adet"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
    
    toplam_kapi_pencere_adet = pencere_ad + wc_pencere_ad + kapi_ad
    if toplam_kapi_pencere_adet > 0:
        toplam_fiyat = toplam_kapi_pencere_adet * FIYATLAR["kapi_pencere_montaj_iscilik_adet"]
        maliyetler.append({
            'Kalem': 'Kapı/Pencere Montaj İşçiliği',
            'Miktar': toplam_kapi_pencere_adet,
            'Birim Fiyat (€)': format_currency(FIYATLAR["kapi_pencere_montaj_iscilik_adet"]),
            'Toplam (€)': format_currency(toplam_fiyat)
        })
    
    # Diğer Kalemler (Other Items)
    toplam_fiyat = zemin_alani * FIYATLAR["baglanti_elemani_m2"]
    maliyetler.append({
        'Kalem': "Bağlantı Elemanları",
        'Miktar': f"{zemin_alani:.2f} m²",
        'Birim Fiyat (€)': format_currency(FIYATLAR["baglanti_elemani_m2"]),
        'Toplam (€)': format_currency(toplam_fiyat)
    })

    if mutfak_input_val:
        maliyetler.append({
            'Kalem': 'Mutfak Kurulumu',
            'Miktar': 1,
            'Birim Fiyat (€)': format_currency(FIYATLAR["mutfak_kurulum_adet"]),
            'Toplam (€)': format_currency(FIYATLAR["mutfak_kurulum_adet"])
        })
    if dus_input_val:
        maliyetler.append({
            'Kalem': 'Duş/WC Kurulumu',
            'Miktar': 1,
            'Birim Fiyat (€)': format_currency(FIYATLAR["dus_wc_kurulum_adet"]),
            'Toplam (€)': format_currency(FIYATLAR["dus_wc_kurulum_adet"])
        })
    if elektrik_tesisat_input_val:
        maliyetler.append({
            'Kalem': 'Elektrik Tesisatı',
            'Miktar': 1,
            'Birim Fiyat (€)': format_currency(FIYATLAR["elektrik_tesisat_fiyat"]),
            'Toplam (€)': format_currency(FIYATLAR["elektrik_tesisat_fiyat"])
        })
    if su_tesisat_input_val:
        maliyetler.append({
            'Kalem': 'Su Tesisatı',
            'Miktar': 1,
            'Birim Fiyat (€)': format_currency(FIYATLAR["su_tesisat_fiyat"]),
            'Toplam (€)': format_currency(FIYATLAR["su_tesisat_fiyat"])
        })
    if tasinma_input_val:
        maliyetler.append({
            'Kalem': 'Taşıma (Nakliye)',
            'Miktar': 1,
            'Birim Fiyat (€)': format_currency(FIYATLAR["tasinma"]),
            'Toplam (€)': format_currency(FIYATLAR["tasinma"])
        })

    # Finansal Hesaplamalar (Financial Calculations)
    # Convert formatted currency strings back to floats for calculation
    ara_toplam = sum([float(item['Toplam (€)'].replace('€', '').replace('.', '').replace(',', '.'))
                     for item in maliyetler if 'Toplam (€)' in item])
    
    fire_maliyeti = ara_toplam * FIRE_ORANI
    toplam_maliyet = ara_toplam + fire_maliyeti
    kar = toplam_maliyet * kar_orani
    kdv_matrahi = toplam_maliyet + kar
    kdv = kdv_matrahi * kdv_orani
    satis_fiyati = kdv_matrahi + kdv
    
    finansal_ozet_data = [
        ["Ara Toplam", ara_toplam],
        [f"Fire Payı (%{FIRE_ORANI*100:.0f})", fire_maliyeti],
        ["Toplam Maliyet (Fire Dahil)", toplam_maliyet],
        [f"Kar (%{kar_orani*100:.0f})", kar],
        [f"KDV (%{kdv_orani*100:.0f})", kdv],
        ["Satış Fiyatı (KDV Dahil)", satis_fiyati]
    ]
    
    # Create formatted financial summary for display
    formatted_finansal_ozet = []
    for kalem, tutar in finansal_ozet_data:
        formatted_finansal_ozet.append({
            'Kalem': kalem,
            'Tutar (€)': format_currency(tutar)
        })
    
    # Process customer info, default to "GENERAL" if name is empty
    customer_name_processed = customer_name_val.strip() or "GENERAL"

    customer_info = {
        'name': customer_name_processed,
        'company': customer_company_val or "",
        'address': customer_address_val or "",
        'city': customer_city_val or "",
        'phone': customer_phone_val or "",
        'email': customer_email_val or ""
    }

    proje_bilgileri = {
        'en': en,
        'boy': boy,
        'yukseklik': yukseklik,
        'alan': zemin_alani,
        'yapi_tipi': yapi_tipi_val,
        'alcipan': alcipan_secenek_val,
        'pencere_adet': pencere_ad,
        'pencere_olcu': pencere_olcu,
        'wc_pencere_adet': wc_pencere_ad,
        'wc_pencere_olcu': wc_pencere_olcu,
        'kapi_adet': kapi_ad,
        'kapi_olcu': kapi_olcu,
        'mutfak': mutfak_input_val,
        'dus': dus_input_val,
        'elektrik': elektrik_tesisat_input_val,
        'su': su_tesisat_input_val,
        'tasinma': tasinma_input_val,
        'isitma': isitma_secenek_val,
        'solar': solar_secenek_val,
        'solar_kw': solar_kapasite_val,
        'solar_fiyat': solar_kapasite_val * FIYATLAR['solar_per_kw'],
        'kdv_orani': kdv_orani,
        'oda_konfigurasyonu': oda_konfigurasyonu
    }

    return {
        'maliyet_dokum': pd.DataFrame(maliyetler),
        'finansal_ozet': pd.DataFrame(formatted_finansal_ozet),
        'profil_analizi': pd.DataFrame(profil_analizi_detaylari),
        'notlar': musteri_notlari,
        'satis_fiyati': satis_fiyati,
        'alan': zemin_alani,
        'en': en,
        'boy': boy,
        'yukseklik': yukseklik,
        'customer_info': customer_info,
        'proje_bilgileri': proje_bilgileri
    }

# === PDF OLUŞTURMA FONKSİYONLARI ===
def get_company_logo(width=180):
    """Fetches the company logo from URL and returns it as base64 encoded string."""
    try:
        response = requests.get(LOGO_URL)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        img = PILImage.open(io.BytesIO(response.content))
        w_percent = (width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((width, h_size), PILImage.LANCZOS)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except requests.exceptions.RequestException as e:
        st.warning(f"Logo URL'den alınırken hata oluştu: {e}")
        return None
    except Exception as e:
        st.warning(f"Logo işlenirken hata oluştu: {e}")
        return None

def draw_header(canvas, doc, logo_data):
    """Draws the page header with logo and company info."""
    if logo_data:
        logo = Image(io.BytesIO(base64.b64decode(logo_data)))
        # Adjust drawHeight and drawWidth as needed to fit.
        # Keep aspect ratio.
        logo.drawHeight = 25 * mm
        logo.drawWidth = 80 * mm 
        # Position logo: 15mm from left, 15mm from top margin (approx)
        logo.drawOn(canvas, doc.leftMargin, A4[1] - doc.topMargin + 5*mm)

    # Company Contact Info at the top right
    canvas.setFont(MAIN_FONT, 8)
    canvas.setFillColor(colors.HexColor('#2C3E50')) # Dark blue
    canvas.drawString(A4[0] - doc.rightMargin - 60*mm, A4[1] - doc.topMargin + 20*mm, COMPANY_INFO['phone'])
    canvas.drawString(A4[0] - doc.rightMargin - 60*mm, A4[1] - doc.topMargin + 15*mm, COMPANY_INFO['email'])
    canvas.drawString(A4[0] - doc.rightMargin - 60*mm, A4[1] - doc.topMargin + 10*mm, COMPANY_INFO['website'])

def draw_footer(canvas, doc):
    """Draws the page footer with company info and page number."""
    footer_text = f"{COMPANY_INFO['address']} | {COMPANY_INFO['email']} | {COMPANY_INFO['phone']} | {COMPANY_INFO['website']} | Linktree: {COMPANY_INFO['linktree']}"
    canvas.setFont(f"{MAIN_FONT}-Bold", 8)
    # Position: Centered horizontally, 15mm from bottom
    canvas.drawCentredString(A4[0] / 2, 15*mm, footer_text)
    
    page_num = canvas.getPageNumber()
    canvas.setFont(MAIN_FONT, 8)
    # Position page number: 10mm from bottom, 15mm from right margin
    canvas.drawString(A4[0] - doc.rightMargin, 10*mm, f"Page {page_num}")


def musteri_pdf_olustur(satis_fiyati, proje_bilgileri, notlar, customer_info, logo_data):
    """Creates a customer-facing proposal PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=40*mm, # Increased top margin to make space for header
        bottomMargin=25*mm # Increased bottom margin for footer
    )
    styles = getSampleStyleSheet()
    custom_styles = {}
    custom_styles['Bilingual'] = ParagraphStyle(
        name='Bilingual', parent=styles['Normal'], fontSize=10, leading=14, fontName=MAIN_FONT
    )
    custom_styles['BilingualBold'] = ParagraphStyle(
        name='BilingualBold', parent=styles['Normal'], fontSize=10, leading=14, fontName=f"{MAIN_FONT}-Bold"
    )
    custom_styles['Title'] = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=12, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.HexColor('#2C3E50')
    )
    custom_styles['Heading'] = ParagraphStyle(
        name='Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.HexColor('#34495E')
    )
    custom_styles['Price'] = ParagraphStyle(
        name='Price', parent=styles['Heading1'], fontSize=20, alignment=TA_CENTER, spaceAfter=6, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.HexColor('#2C3E50')
    )

    elements = []

    # Müşteri ve Şirket Bilgileri (Side-by-side)
    customer_data = [
        [Paragraph("<b>MÜŞTERİ BİLGİLERİ</b>", custom_styles['BilingualBold'])],
        [Paragraph(f"Adı Soyadı: {customer_info['name']}", custom_styles['Bilingual'])],
        [Paragraph(f"Şirket: {customer_info['company']}", custom_styles['Bilingual'])],
        [Paragraph(f"Adres: {customer_info['address']}", custom_styles['Bilingual'])],
        [Paragraph(f"Şehir: {customer_info['city']}", custom_styles['Bilingual'])],
        [Paragraph(f"Telefon: {customer_info['phone']}", custom_styles['Bilingual'])],
        [Paragraph(f"E-posta: {customer_info['email']}", custom_styles['Bilingual'])]
    ]
    company_data = [
        [Paragraph("<b>ŞİRKET BİLGİLERİ</b>", custom_styles['BilingualBold'])],
        [Paragraph(f"Şirket: {COMPANY_INFO['name']}", custom_styles['Bilingual'])],
        [Paragraph(f"Adres: {COMPANY_INFO['address']}", custom_styles['Bilingual'])],
        [Paragraph(f"Telefon: {COMPANY_INFO['phone']}", custom_styles['Bilingual'])],
        [Paragraph(f"E-posta: {COMPANY_INFO['email']}", custom_styles['Bilingual'])],
        [Paragraph(f"Website: {COMPANY_INFO['website']}", custom_styles['Bilingual'])],
        [Paragraph(f"Linktree: {COMPANY_INFO['linktree']}", custom_styles['Bilingual'])]
    ]

    # Use a Table to layout customer and company info side-by-side
    info_table_data = [
        [
            Table(customer_data, colWidths=[doc.width/2], style=[
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]),
            Table(company_data, colWidths=[doc.width/2], style=[
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ])
        ]
    ]
    info_table = Table(info_table_data, colWidths=[doc.width/2, doc.width/2])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))

    elements.append(Paragraph("TEKLİF FORMU", custom_styles['Title']))
    elements.append(Paragraph(f"PROJE ALANI: {proje_bilgileri['alan']:.2f} m²", custom_styles['Heading']))
    elements.append(Paragraph(f"YAPI TİPİ: {proje_bilgileri['yapi_tipi']}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"ODA KONFİGÜRASYONU: {proje_bilgileri['oda_konfigurasyonu']}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"İç Mekan Alçıpan Dahil: {'Evet' if proje_bilgileri['alcipan'] else 'Hayır'}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"Yerden Isıtma Dahil: {'Evet' if proje_bilgileri['isitma'] else 'Hayır'}", custom_styles['Bilingual']))
    if proje_bilgileri['solar']:
        elements.append(Paragraph(f"Solar Enerji Sistemi ({proje_bilgileri['solar_kw']} kW) Dahil: Evet", custom_styles['Bilingual']))

    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("KAPI & PENCERE", custom_styles['Heading']))
    elements.append(Paragraph(f"Pencere Adedi: {proje_bilgileri['pencere_adet']} ({proje_bilgileri['pencere_olcu']})", custom_styles['Bilingual']))
    elements.append(Paragraph(f"WC Pencere Adedi: {proje_bilgileri['wc_pencere_adet']} ({proje_bilgileri['wc_pencere_olcu']})", custom_styles['Bilingual']))
    elements.append(Paragraph(f"Kapı Adedi: {proje_bilgileri['kapi_adet']} ({proje_bilgileri['kapi_olcu']})", custom_styles['Bilingual']))

    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("EK DONANIMLAR VE TESİSATLAR", custom_styles['Heading']))
    elements.append(Paragraph(f"Mutfak Kurulumu: {'Dahil' if proje_bilgileri['mutfak'] else 'Değil'}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"Duş/WC Kurulumu: {'Dahil' if proje_bilgileri['dus'] else 'Değil'}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"Elektrik Tesisatı: {'Dahil' if proje_bilgileri['elektrik'] else 'Değil'}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"Su Tesisatı: {'Dahil' if proje_bilgileri['su'] else 'Değil'}", custom_styles['Bilingual']))
    elements.append(Paragraph(f"Taşıma (Nakliye): {'Dahil' if proje_bilgileri['tasinma'] else 'Değil'}", custom_styles['Bilingual']))

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph("MÜŞTERİ NOTLARI:", custom_styles['Heading']))
    elements.append(Paragraph(notlar if notlar else "Belirtilen özel not bulunmamaktadır.", custom_styles['Bilingual']))

    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph("TOPLAM FİYAT", custom_styles['Heading']))
    elements.append(Paragraph(format_currency(satis_fiyati), custom_styles['Price']))

    doc.build(buffer, onLaterPages=lambda canvas, doc: draw_header(canvas, doc, logo_data),
              onFirstPage=lambda canvas, doc: draw_footer(canvas, doc)) 
    return buffer.getvalue()

def maliyet_raporu_pdf_olustur(proje_bilgileri, maliyet_dokum, finansal_ozet, profil_analizi, customer_info, logo_data):
    """Creates a detailed cost report PDF (for internal use)."""
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
    custom_styles = {}
    custom_styles['Normal'] = ParagraphStyle(
        name='Normal', parent=styles['Normal'], fontSize=9, leading=12, fontName=MAIN_FONT
    )
    custom_styles['Bold'] = ParagraphStyle(
        name='Bold', parent=styles['Normal'], fontSize=9, leading=12, fontName=f"{MAIN_FONT}-Bold"
    )
    custom_styles['Heading'] = ParagraphStyle(
        name='Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.HexColor('#34495E')
    )
    custom_styles['SubHeading'] = ParagraphStyle(
        name='SubHeading', parent=styles['Heading3'], fontSize=10, spaceAfter=4, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.HexColor('#2C3E50')
    )
    custom_styles['Title'] = ParagraphStyle(
        name='Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=12, fontName=f"{MAIN_FONT}-Bold",
        textColor=colors.HexColor('#2C3E50')
    )

    elements = []

    # Title
    elements.append(Paragraph("MALİYET RAPORU", custom_styles['Title']))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(f"Müşteri: {customer_info['name']} ({customer_info['company']})", custom_styles['Normal']))
    elements.append(Paragraph(f"Proje Alanı: {proje_bilgileri['alan']:.2f} m²", custom_styles['Normal']))
    elements.append(Paragraph(f"Yapı Tipi: {proje_bilgileri['yapi_tipi']}", custom_styles['Normal']))
    elements.append(Spacer(1, 10*mm))

    # Maliyet Dökümü
    elements.append(Paragraph("Maliyet Dökümü", custom_styles['Heading']))
    if not maliyet_dokum.empty:
        # Convert DataFrame to list of lists for ReportLab Table
        data = [maliyet_dokum.columns.tolist()] + maliyet_dokum.values.tolist()
        table = Table(data, colWidths=[40*mm, 30*mm, 40*mm, 40*mm]) # Adjust colWidths as needed
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), f"{MAIN_FONT}-Bold"),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Maliyet dökümü bulunmamaktadır.", custom_styles['Normal']))
    elements.append(Spacer(1, 10*mm))

    # Finansal Özet
    elements.append(Paragraph("Finansal Özet", custom_styles['Heading']))
    if not finansal_ozet.empty:
        data = [finansal_ozet.columns.tolist()] + finansal_ozet.values.tolist()
        table = Table(data, colWidths=[80*mm, 60*mm]) # Adjust colWidths as needed
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), f"{MAIN_FONT}-Bold"),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Finansal özet bulunmamaktadır.", custom_styles['Normal']))
    elements.append(Spacer(1, 10*mm))

    # Profil Analizi (If Light Steel)
    if proje_bilgileri['yapi_tipi'] == 'Hafif Çelik' and not profil_analizi.empty:
        elements.append(Paragraph("Çelik Profil Analizi", custom_styles['Heading']))
        data = [profil_analizi.columns.tolist()] + profil_analizi.values.tolist()
        table = Table(data, colWidths=[40*mm, 20*mm, 30*mm, 30*mm]) # Adjust colWidths as needed
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), f"{MAIN_FONT}-Bold"),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), MAIN_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10*mm))

    doc.build(buffer, onLaterPages=lambda canvas, doc: draw_header(canvas, doc, logo_data),
              onFirstPage=lambda canvas, doc: draw_footer(canvas, doc)) 
    return buffer.getvalue()


# === Streamlit UI ===
st.set_page_config(layout="centered", page_title="Premium Plus Proje Hesaplayıcı", initial_sidebar_state="expanded")

# Custom CSS for a better look (adapted from your original HTML styles)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Open Sans', sans-serif !important;
    }
    .st-emotion-cache-nahz7x { /* Main content padding - adjust as needed for newer Streamlit versions */
        padding-top: 1rem;
        padding-right: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
    }
    h1 { /* Main Title */
        color: #2C3E50; 
        border-bottom: 2px solid #3498DB;
        padding-bottom: 5px; 
        margin-top: 20px;
        font-weight: 700 !important;
    }
    h2 { /* Section Headers */
        color: #34495E;
        margin-top: 15px;
        font-weight: 700 !important;
    }
    h3 { /* Sub-Section Headers / Streamlit's default headers */
        background-color: #2C3E50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: 700 !important;
        margin-top: 20px;
    }
    .stButton > button {
        background-color: #2C3E50;
        border: none;
        color: white;
        padding: 12px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 10px 0;
        cursor: pointer;
        border-radius: 5px;
        transition: all 0.3s;
        font-weight: 700 !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        background-color: #3498DB;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .stAlert { /* Styles for st.warning/info */
        background-color: #e9f7fe; /* Lighter blue */
        border: 1px solid #3498DB;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 20px;
    }
    /* Table styling for st.dataframe if needed, although Streamlit applies its own styles */
    .st-dataframe th, .st-dataframe td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }
    .st-dataframe th {
        background-color: #f2f2f2;
    }
    .st-dataframe tr:nth-child(even) {
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# Application Title
st.title("Premium Plus Proje Hesaplayıcı")

# --- Sidebar for General Settings and Company Info ---
st.sidebar.header("Şirket Bilgileri")
st.sidebar.info(
    f"**{COMPANY_INFO['name']}**\n\n"
    f"{COMPANY_INFO['address']}\n"
    f"Email: {COMPANY_INFO['email']}\n"
    f"Telefon: {COMPANY_INFO['phone']}\n"
    f"Website: {COMPANY_INFO['website']}\n"
    f"Linktree: {COMPANY_INFO['linktree']}"
)

st.sidebar.header("Fiyat Güncelleme")
if st.sidebar.button("Fiyatları Güncelle"):
    update_prices()
    st.sidebar.success("Fiyatlar başarıyla güncellendi!")
    # Optionally, display some updated prices
    st.sidebar.write(f"- Panel montaj işçiliği: {FIYATLAR['panel_montaj_iscilik_m2']} €/m²")
    st.sidebar.write(f"- Solar enerji: {FIYATLAR['solar_per_kw']} €/kW")

st.sidebar.header("Güncel Fiyat Listesi (Örnek)")
price_data = {
    "Malzeme / Hizmet": [
        "Çelik Profil (100x100x3)", "Sandviç Panel", "Plywood",
        "Alüminyum Pencere", "Panel Montaj İşçiliği", "Alçıpan İşçilik",
        "Mutfak Kurulumu", "Duş/WC Kurulumu", "Yerden Isıtma",
        "Solar Energy (1 kW)", "Taşıma"
    ],
    "Fiyat (€)": [
        f"{FIYATLAR['celik_profil_100x100x3']} / adet",
        f"{FIYATLAR['sandvic_panel_m2']} / m²",
        f"{FIYATLAR['plywood_adet']} / adet",
        f"{FIYATLAR['aluminyum_pencere_adet']} / adet",
        f"{FIYATLAR['panel_montaj_iscilik_m2']} / m²",
        f"{FIYATLAR['alcipan_iscilik_m2']} / m²",
        f"{FIYATLAR['mutfak_kurulum_adet']} / adet",
        f"{FIYATLAR['dus_wc_kurulum_adet']} / adet",
        f"{FIYATLAR['yerden_isitma_m2']} / m²",
        f"{FIYATLAR['solar_per_kw']} / kW",
        f"{FIYATLAR['tasinma']} / sefer"
    ]
}
st.sidebar.table(pd.DataFrame(price_data))


# --- Main Content Area ---
st.header("MÜŞTERİ BİLGİLERİ (Opsiyonel)")
st.warning("Not: Müşteri bilgileri zorunlu değildir. Boş bırakılırsa 'GENERAL' olarak işaretlenecektir.")
col1, col2 = st.columns(2)
customer_name = col1.text_input("Adı Soyadı:", value="GENERAL")
customer_company = col2.text_input("Şirket:")
col3, col4 = st.columns(2)
customer_address = col3.text_input("Adres:")
customer_city = col4.text_input("Şehir:")
col5, col6 = st.columns(2)
customer_phone = col5.text_input("Telefon:")
customer_email = col6.text_input("E-posta:")


st.header("PROJE DETAYLARI")
yapi_tipi = st.radio("Yapı Tipi:", ['Hafif Çelik', 'Ağır Çelik'], horizontal=True)
alcipan_secenek = st.checkbox("İç Mekan Alçıpan Dahil", value=True)
col_dims1, col_dims2, col_dims3 = st.columns(3)
en_input = col_dims1.number_input("En (m):", value=10.0, min_value=1.0)
boy_input = col_dims2.number_input("Boy (m):", value=8.0, min_value=1.0)
yukseklik_input = col_dims3.number_input("Yükseklik (m):", value=2.6, min_value=0.1)
oda_konfigurasyonu_input = st.text_input("Oda Konfigürasyonu:", value="1 oda, 1 banyo, 1 mutfak")

st.header("ÇELİK PROFİL ADETLERİ (Hafif Çelik İçin)")
st.info("**(6m parça başına adet)**")
col_profil1, col_profil2 = st.columns(2)
profil_100x100_adet = col_profil1.number_input("100x100x3 Adet:", value=0, min_value=0, help="6m'lik 100x100x3 profil adedi")
profil_100x50_adet = col_profil2.number_input("100x50x3 Adet:", value=0, min_value=0, help="6m'lik 100x50x3 profil adedi")
col_profil3, col_profil4 = st.columns(2)
profil_40x60_adet = col_profil3.number_input("40x60x2 Adet:", value=0, min_value=0, help="6m'lik 40x60x2 profil adedi")
profil_40x40_adet = col_profil4.number_input("40x40x2 Adet:", value=0, min_value=0, help="6m'lik 40x40x2 profil adedi")
col_profil5, col_profil6 = st.columns(2)
profil_30x30_adet = col_profil5.number_input("30x30x2 Adet:", value=0, min_value=0, help="6m'lik 30x30x2 profil adedi")
profil_HEA160_adet = col_profil6.number_input("HEA160 Adet:", value=0, min_value=0, help="6m'lik HEA160 profil adedi")


st.header("KAPI & PENCERE DETAYLARI")
col_pencere1, col_pencere2 = st.columns(2)
pencere_input = col_pencere1.number_input("Pencere Adedi:", value=4, min_value=0)
pencere_olcu = col_pencere2.text_input("Pencere Ölçüsü:", value="150x120 cm")
col_wc_pencere1, col_wc_pencere2 = st.columns(2)
wc_pencere_input = col_wc_pencere1.number_input("WC Pencere Adedi:", value=1, min_value=0)
wc_pencere_olcu = col_wc_pencere2.text_input("WC Pencere Ölçüsü:", value="60x50 cm")
col_kapi1, col_kapi2 = st.columns(2)
kapi_input = col_kapi1.number_input("Kapı Adedi:", value=2, min_value=0)
kapi_olcu = col_kapi2.text_input("Kapı Ölçüsü:", value="90x210 cm")

st.header("EK DONANIM VE TESİSATLAR")
col_ek1, col_ek2 = st.columns(2)
mutfak_input = col_ek1.checkbox("Mutfak Dahil", value=True)
dus_input = col_ek2.checkbox("Duş/WC Dahil", value=True)
col_tesisat1, col_tesisat2 = st.columns(2)
elektrik_tesisat_input = col_tesisat1.checkbox("Elektrik Tesisatı Dahil", value=False)
su_tesisat_input = col_tesisat2.checkbox("Su Tesisatı Dahil", value=False)
tasinma_input = st.checkbox("Taşıma Dahil (500€)", value=False)

isitma_secenek = st.checkbox("Yerden Isıtma Dahil (50€/m²)", value=False)

solar_secenek = st.checkbox("Solar Energy System", value=False)
if solar_secenek:
    col_solar1, col_solar2 = st.columns(2)
    solar_kapasite = col_solar1.selectbox(
        "Kapasite:", options=[5, 7.2, 11], format_func=lambda x: f"{x} kW"
    )
    solar_fiyat_display = solar_kapasite * FIYATLAR['solar_per_kw']
    col_solar2.metric(label="Solar Fiyat (€):", value=format_currency(solar_fiyat_display))
else:
    solar_kapasite = 0 # Default to 0 if not selected

st.header("FİNANSAL AYARLAR")
# Düzeltildi: format_func kaldırıldı
kar_orani_input = st.slider(
    "Kar Oranı:",
    min_value=0.0,
    max_value=0.50,
    value=0.20,
    step=0.01
)
kdv_input = st.slider(
    "KDV Oranı:",
    min_value=0.0,
    max_value=0.25,
    value=KDV_ORANI,
    step=0.01
)

st.header("MÜŞTERİ ÖZEL İSTEKLERİ VE NOTLAR")
musteri_notlari = st.text_area("Müşteri Notları:", value='')

# --- Calculation and PDF Generation Button ---
if st.button("Hesapla ve PDF Oluştur"):
    with st.spinner('Hesaplanıyor ve PDF oluşturuluyor...'):
        try:
            result = calculate_costs(
                yapi_tipi, alcipan_secenek, en_input, boy_input, yukseklik_input, oda_konfigurasyonu_input,
                profil_100x100_adet, profil_100x50_adet, profil_40x60_adet, profil_40x40_adet, profil_30x30_adet, profil_HEA160_adet,
                isitma_secenek, solar_secenek, solar_kapasite,
                pencere_input, pencere_olcu, wc_pencere_input, wc_pencere_olcu, kapi_input, kapi_olcu,
                mutfak_input, dus_input, elektrik_tesisat_input, su_tesisat_input, tasinma_input,
                kar_orani_input, kdv_input, musteri_notlari,
                customer_name, customer_company, customer_address, customer_city, customer_phone, customer_email
            )

            st.subheader("Hesaplama Sonuçları")
            col_res1, col_res2 = st.columns(2)
            col_res1.metric(label="Tahmini Satış Fiyatı (KDV Dahil)", value=format_currency(result['satis_fiyati']))
            col_res2.metric(label="Proje Alanı", value=f"{result['alan']:.2f} m²")

            st.subheader("Maliyet Dökümü")
            st.dataframe(result['maliyet_dokum'], use_container_width=True)

            st.subheader("Finansal Özet")
            st.dataframe(result['finansal_ozet'], use_container_width=True)

            if yapi_tipi == 'Hafif Çelik':
                st.subheader("Çelik Profil Analizi")
                st.dataframe(result['profil_analizi'], use_container_width=True)

            # --- PDF Generation ---
            logo_data = get_company_logo()

            teklif_pdf = musteri_pdf_olustur(
                result['satis_fiyati'],
                result['proje_bilgileri'],
                result['notlar'],
                result['customer_info'],
                logo_data
            )

            maliyet_pdf = maliyet_raporu_pdf_olustur(
                result['proje_bilgileri'],
                result['maliyet_dokum'],
                result['finansal_ozet'],
                result['profil_analizi'],
                result['customer_info'],
                logo_data
            )
            
            # PDF download links
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            teklif_filename = f"Teklif_Formu_{timestamp}.pdf"
            maliyet_filename = f"Maliyet_Raporu_{timestamp}.pdf"

            st.markdown("---")
            st.subheader("PDF Dosyalarını İndir")
            
            col_pdf1, col_pdf2 = st.columns(2)
            col_pdf1.download_button(
                label=f"⬇️ {teklif_filename} İndir",
                data=teklif_pdf,
                file_name=teklif_filename,
                mime="application/pdf"
            )
            col_pdf2.download_button(
                label=f"⬇️ {maliyet_filename} İndir",
                data=maliyet_pdf,
                file_name=maliyet_filename,
                mime="application/pdf"
            )
            st.info("PDF'leri indirmek için yukarıdaki butonları kullanın. Tarayıcınız PDF'leri doğrudan açmayı tercih edebilir.")

        except Exception as e:
            st.error(f"Hata oluştu: {e}")
            st.exception(e) # Display full traceback for debugging
