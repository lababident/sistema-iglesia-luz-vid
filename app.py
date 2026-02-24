import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import base64
from fpdf import FPDF
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Iglesia Luz y Vida", layout="wide", page_icon="⛪")

# --- SISTEMA DE LOGIN ---
USUARIOS_VALIDOS = {
    "admin": "luzvida2026",
    "tesoreria": "iglesia123",
    "pastoral": "barinas2026"
}

def login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if not st.session_state.autenticado:
        col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
        with col_l2:
            st.markdown("<h2 style='text-align: center; color: #5D4037;'>Acceso Administrativo</h2>", unsafe_allow_html=True)
            with st.container(border=True):
                usuario = st.text_input("Usuario")
                clave = st.text_input("Contraseña", type="password")
                if st.button("Ingresar", use_container_width=True):
                    if usuario in USUARIOS_VALIDOS and USUARIOS_VALIDOS[usuario] == clave:
                        st.session_state.autenticado = True
                        st.session_state.usuario_actual = usuario
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
        return False
    return True

# --- FUNCIONES AUXILIARES ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

def aplicar_estetica():
    logo_b64 = get_base64_of_bin_file('logo.png')
    logo_html = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
    st.markdown(f"""
        <style>
        h1, h2, h3 {{ color: #5D4037 !important; font-family: 'Segoe UI'; }}
        .logo-esquina {{ position: absolute; top: -50px; right: 0px; width: 70px; }}
        div.stButton > button {{ background-color: #8D6E63; color: white; border-radius: 8px; border: none; font-weight: bold; }}
        div.stButton > button:hover {{ background-color: #5D4
