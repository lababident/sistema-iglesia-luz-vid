import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Iglesia Luz y Vida", layout="wide", page_icon="⛪")

# --- SISTEMA DE LOGIN ---
# Define aquí tus 3 usuarios y contraseñas
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
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def aplicar_estetica():
    try:
        bin_str = get_base64_of_bin_file('logo.png')
        logo_html = f"data:image/png;base64,{bin_str}"
    except:
        logo_html = ""

    st.markdown(f"""
        <style>
        h1, h2, h3 {{ color: #5D4037 !important; }}
        .logo-esquina {{ position: absolute; top: -50px; right: 0px; width: 70px; }}
        div.stButton > button {{ background-color: #8D6E63; color: white; border-radius: 8px; border: none; }}
        div.stButton > button:hover {{ background-color: #5D4037; color: white; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 10px; }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #f4ece1; border-radius: 5px 5px 0px 0px; color: #5D4037; padding: 10px 20px;
        }}
        .stTabs [aria-selected="true"] {{ background-color: #8D6E63 !important; color: white !important; }}
        </style>
        <img src="{logo_html}" class="logo-esquina">
    """, unsafe_allow_html=True)

# --- INICIO DE LA APLICACIÓN ---
if login():
    aplicar_estetica()
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Listas maestras
    REDES = ["Red de Ruben", "Red de Simeon", "Red de Levi", "Red de Juda", "Red de Neftali", 
             "Red de Efrain", "Red de Gad", "Red de Aser", "Red de Isacar", "Red de Zabulom", 
             "Red de Jose", "Red de Benjamin", "Protemplo", "Suelto General", "Pastores", "Red de Niños"]
    METODOS = ["Bolivares en Efectivo", "USD en Efectivo", "Transferencia / PM", "Punto"]

    tabs = st.tabs(["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS", "📊 INFORMES"])

    # --- PESTAÑA INICIO ---
    with tabs[0]:
        st.markdown(f"<h4 style='text-align: right;'>Bienvenido, {st.session_state.usuario_actual.capitalize()}</h4>", unsafe_allow_html=True)
        col_c1, col_c2, col_c3 = st.columns([1, 2, 1])
        with col_c2:
            try: st.image("logo.png", use_container_width=True)
            except: st.info("Sube 'logo.png' para visualizarlo aquí.")
            st.markdown("<h1 style='text-align: center;'>Iglesia Cristiana Luz y Vida</h1>", unsafe_allow_html=True)
            st.divider()
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

    # --- PESTAÑA INGRESOS ---
    with tabs[1]:
        st.header("📥 Registro de Ofrendas y Diezmos")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                f_rec = st.date_input("Fecha Recaudación", date.today())
                red_sel = st.selectbox("Red", REDES)
                tipo_sel = st.radio("Clasificación", ["Ofrenda", "Diezmo"])
            with c2:
                metodo_sel = st.selectbox("Forma de Pago", METODOS)
                monto_in = st.number_input("Monto Ingresado", min_value=0.0)
                tasa_v = 1.0; ref_v = "N/A"; banco_v = "N/A"; f_op_v = str(f_rec)

                if metodo_sel == "USD en Efectivo":
                    tasa_v = st.number_input("Tasa BCV", min_value=1.0, value=36.0)
                elif metodo_sel == "Transferencia / PM":
                    banco_v = st.text_input("Banco")
                    ref_v = st.text_input("Referencia (4 d)", max_chars=4)
                    f_op_v = str(st.date_input("Fecha Op.", date.today()))
                elif metodo_sel == "Punto":
                    ref_v = st.text_input("Ref Punto (4 d)", max_chars=4)
                    f_op_v = str(st.date_input("Fecha Op. Punto", date.today()))
            with c3:
                total_bs = monto_in * tasa_v if metodo_sel == "USD en Efectivo" else monto_in
                st.metric("TOTAL Bs", f"{total_bs:,.2f}")
                st.metric("10%", f"{(total_bs * 0.10):,.2f}")

            if st.button("💾 GUARDAR", use_container_width=True):
                df_act = conn.read(worksheet="INGRESOS")
                nuevo = pd.DataFrame([{"Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel, "Metodo": metodo_sel, "Banco": banco_v, "Referencia": ref_v, "Fecha_Op": f_op_v, "Monto_Orig": monto_in, "Tasa": tasa_v, "Total_Bs": total_bs, "Diezmo_10": total_bs*0.10}])
                conn.update(worksheet="INGRESOS", data=pd.concat([df_act, nuevo], ignore_index=True))
                st.cache_data.clear()
                st.success("Guardado exitoso")
                st.rerun()

    # --- PESTAÑA EGRESOS ---
    with tabs[2]:
        st.header("📤 Pagos a Personal")
        with st.container(border=True):
            e1, e2 = st.columns(2)
            with e1:
                nom = st.text_input("NOMBRE")
                cargo = st.text_input("CARGO")
                m_usd = st.number_input("SUELDO USD", min_value=0.0)
            with e2:
                t_eg = st.number_input("TASA BCV", min_value=1.0, value=36.0)
                obs = st.text_area("OBS")
                st.metric("TOTAL A PAGAR (Bs)", f"{(m_usd * t_eg):,.2f}")
            if st.button("💸 REGISTRAR PAGO", use_container_width=True):
                df_e = conn.read(worksheet="EGRESOS")
                n_e = pd.DataFrame([{"Fecha": str(date.today()), "Nombre": nom, "Cargo": cargo, "Sueldo_USD": m_usd, "Tasa": t_eg, "Total_Bs": m_usd*t_eg, "Observaciones": obs}])
                conn.update(worksheet="EGRESOS", data=pd.concat([df_e, n_e], ignore_index=True))
                st.cache_data.clear()
                st.success("Pago registrado")
                st.rerun()

    # --- PESTAÑA INFORMES ---
    with tabs[3]:
        st.header("📊 Resumen de Cierre")
        try:
            df_rep = conn.read(worksheet="INGRESOS")
            if not df_rep.empty:
                df_rep['Total_Bs'] = pd.to_numeric(df_rep['Total_Bs'], errors='coerce').fillna(0)
                df_rep['Diezmo_10'] = pd.to_numeric(df_rep['Diezmo_10'], errors='coerce').fillna(0)
                res = df_rep.groupby('Red').agg({'Total_Bs': 'sum', 'Diezmo_10': 'sum'}).reset_index()
                t_10 = res['Diezmo_10'].sum()
                zabulon = res[res['Red'] == 'Red de Zabulom']['Diezmo_10'].sum()
                m1, m2 = st.columns(2)
                m1.metric("APÓSTOL", f"{t_10:,.2f} Bs")
                m2.metric("PRESBITERIO", f"{(t_10 - zabulon):,.2f} Bs")
                st.table(res.style.format({"Total_Bs": "{:,.2f}", "Diezmo_10": "{:,.2f}"}))
        except: st.warning("Sin datos para informes.")
