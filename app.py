import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import base64
from fpdf import FPDF

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Iglesia Luz y Vida", layout="wide", page_icon="⛪")

# --- SISTEMA DE LOGIN Y ROLES ---
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

# --- FUNCIONES ESTÉTICAS ---
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
        div.stButton > button:hover {{ background-color: #5D4037; color: white; border: 1px solid white; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #f4ece1; border-radius: 5px 5px 0px 0px; color: #5D4037; padding: 8px 16px;
        }}
        .stTabs [aria-selected="true"] {{ background-color: #8D6E63 !important; color: white !important; }}
        </style>
        <img src="{logo_html}" class="logo-esquina">
    """, unsafe_allow_html=True)

# --- INICIO DE LA APP ---
if login():
    aplicar_estetica()
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Variables Maestras
    REDES = ["Red de Ruben", "Red de Simeon", "Red de Levi", "Red de Juda", "Red de Neftali", 
             "Red de Efrain", "Red de Gad", "Red de Aser", "Red de Isacar", "Red de Zabulom", 
             "Red de Jose", "Red de Benjamin", "Protemplo", "Suelto General", "Pastores", "Red de Niños"]
    METODOS = ["Bolivares en Efectivo", "USD en Efectivo", "Transferencia / PM", "Punto"]

    # Definición de pestañas por Rol
    rol = st.session_state.usuario_actual
    if rol in ["admin", "tesoreria"]:
        titulos = ["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS", "📊 INFORMES"]
    else:
        titulos = ["🏠 INICIO", "📊 INFORMES"]

    tabs = st.tabs(titulos)

    # --- PESTAÑA INICIO ---
    with tabs[0]:
        st.markdown(f"<h4 style='text-align: right; color: #8D6E63;'>Bienvenido, {rol.capitalize()}</h4>", unsafe_allow_html=True)
        c_i1, c_i2, c_i3 = st.columns([1, 2, 1])
        with c_i2:
            try: st.image("logo.png", use_container_width=True)
            except: st.info("Logo Iglesia Luz y Vida")
            st.markdown("<h1 style='text-align: center;'>Iglesia Cristiana Luz y Vida</h1>", unsafe_allow_html=True)
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

    # --- PESTAÑAS EXCLUSIVAS (ADMIN/TESORERIA) ---
    if rol in ["admin", "tesoreria"]:
        # INGRESOS
        with tabs[1]:
            st.header("📥 Registro de Ingresos")
            with st.form("form_ingresos", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    f_rec = st.date_input("Fecha Recaudación", date.today())
                    red_sel = st.selectbox("Red", REDES)
                    tipo_sel = st.radio("Clasificación", ["Ofrenda", "Diezmo"])
                with col2:
                    met_sel = st.selectbox("Forma de Pago", METODOS)
                    monto_in = st.number_input("Monto Ingresado", min_value=0.0)
                    tasa_v = 1.0; ref_v = "N/A"; banco_v = "N/A"; f_op_v = str(f_rec)

                    if met_sel == "USD en Efectivo":
                        tasa_v = st.number_input("Tasa BCV", min_value=1.0, value=36.0)
                    elif met_sel == "Transferencia / PM":
                        banco_v = st.text_input("Banco de Origen")
                        ref_v = st.text_input("Referencia (4 d)", max_chars=4)
                        f_op_v = str(st.date_input("Fecha Op. Transferencia", date.today()))
                    elif met_sel == "Punto":
                        ref_v = st.text_input("Ref Punto (4 d)", max_chars=4)
                        f_op_v = str(st.date_input("Fecha Op. Punto", date.today()))
                with col3:
                    total_bs = monto_in * tasa_v if met_sel == "USD en Efectivo" else monto_in
                    st.metric("TOTAL Bs", f"{total_bs:,.2f}")
                    st.metric("10%", f"{(total_bs * 0.10):,.2f}")

                if st.form_submit_button("💾 GUARDAR"):
                    df_act = conn.read(worksheet="INGRESOS")
                    nuevo = pd.DataFrame([{"Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel, "Metodo": met_sel, "Banco": banco_v, "Referencia": ref_v, "Fecha_Op": f_op_v, "Monto_Orig": monto_in, "Tasa": tasa_v, "Total_Bs": total_bs, "Diezmo_10": total_bs*0.10}])
                    conn.update(worksheet="INGRESOS", data=pd.concat([df_act, nuevo], ignore_index=True))
                    st.cache_data.clear()
                    st.success("Registro Guardado")
            
            st.divider()
            st.subheader("📋 Vista Previa y Corrección")
            df_v = conn.read(worksheet="INGRESOS")
            if not df_v.empty:
                ed_ing = st.data_editor(df_v.tail(15), use_container_width=True)
                if st.button("🔄 Sincronizar Ediciones"):
                    conn.update(worksheet="INGRESOS", data=ed_ing)
                    st.cache_data.clear()
                    st.success("Base de Datos Actualizada")

        # EGRESOS
        with tabs[2]:
            st.header("📤 Pagos a Personal")
            with st.form("form_egresos", clear_on_submit=True):
                e1, e2 = st.columns(2)
                with e1:
                    nom = st.text_input("NOMBRE")
                    cargo = st.text_input("CARGO")
                    m_usd = st.number_input("SUELDO USD", min_value=0.0)
                with e2:
                    t_eg = st.number_input("TASA BCV EGRESO", min_value=1.0, value=36.0)
                    obs = st.text_area("OBSERVACIONES")
                    st.metric("TOTAL A PAGAR (Bs)", f"{(m_usd * t_eg):,.2f}")
                if st.form_submit_button("💸 REGISTRAR PAGO"):
                    df_e = conn.read(worksheet="EGRESOS")
                    n_e = pd.DataFrame([{"Fecha": str(date.today()), "Nombre": nom, "Cargo": cargo, "Sueldo_USD": m_usd, "Tasa": t_eg, "Total_Bs": m_usd*t_eg, "Observaciones": obs}])
                    conn.update(worksheet="EGRESOS", data=pd.concat([df_e, n_e], ignore_index=True))
                    st.cache_data.clear()
                    st.success("Pago registrado")
        idx_inf = 3
    else:
        idx_inf = 1

    # --- PESTAÑA INFORMES (COMPARTIDA) ---
    with tabs[idx_inf]:
        st.header("📊 Reportes y Cierres")
        try:
            df_rep = conn.read(worksheet="INGRESOS")
            if not df_rep.empty:
                df_rep['Fecha'] = pd.to_datetime(df_rep['Fecha']).dt.date
                df_rep['Total_Bs'] = pd.to_numeric(df_rep['Total_Bs'], errors='coerce').fillna(0)
                df_rep['Diezmo_10'] = pd.to_numeric(df_rep['Diezmo_10'], errors='coerce').fillna(0)

                with st.expander("🔍 Filtros de Fecha y Red", expanded=True):
                    f1, f2 = st.columns(2)
                    inicio = f1.date_input("Desde", date.today().replace(day=1))
                    fin = f2.date_input("Hasta", date.today())
                    redes_f = st.multiselect("Filtrar Redes", ["TODAS"] + REDES, default="TODAS")

                mask = (df_rep['Fecha'] >= inicio) & (df_rep['Fecha'] <= fin)
                df_f = df_rep.loc[mask]
                if "TODAS" not in redes_f:
                    df_f = df_f[df_f['Red'].isin(redes_f)]

                res = df_f.groupby('Red').agg({'Total_Bs': 'sum', 'Diezmo_10': 'sum'}).reset_index()
                t_10 = res['Diezmo_10'].sum()
                zabulon = res[res['Red'] == 'Red de Zabulom']['Diezmo_10'].sum()

                m_a, m_p = st.columns(2)
                m_a.metric("APÓSTOL", f"{t_10:,.2f} Bs")
                m_p.metric("PRESBITERIO", f"{(t_10 - zabulon):,.2f} Bs")
                st.table(res.style.format({"Total_Bs": "{:,.2f}", "Diezmo_10": "{:,.2f}"}))

                if st.button("📄 GENERAR PDF"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 14)
                    pdf.set_text_color(93, 64, 55)
                    pdf.cell(200, 10, "Iglesia Luz y Vida - Reporte Administrativo", ln=True, align='C')
                    pdf.set_font("Arial", size=10)
                    pdf.cell(200, 10, f"Periodo: {inicio} al {fin}", ln=True, align='C')
                    pdf.ln(5)
                    pdf.set_fill_color(141, 110, 99); pdf.set_text_color(255, 255, 255)
                    pdf.cell(90, 10, "Red", 1, 0, 'C', True)
                    pdf.cell(50, 10, "Total Bs", 1, 0, 'C', True)
                    pdf.cell(50, 10, "10% Bs", 1, 1, 'C', True)
                    pdf.set_text_color(0, 0, 0)
                    for _, r in res.iterrows():
                        pdf.cell(90, 10, str(r['Red']), 1)
                        pdf.cell(50, 10, f"{r['Total_Bs']:,.2f}", 1)
                        pdf.cell(50, 10, f"{r['Diezmo_10']:,.2f}", 1, 1)
                    
                    pdf_out = pdf.output(dest='S').encode('latin-1')
                    st.download_button("📥 Descargar Reporte PDF", data=pdf_out, file_name=f"Reporte_{inicio}.pdf")
            else: st.warning("Sin datos para informes.")
        except Exception as e: st.error(f"Error: {e}")
