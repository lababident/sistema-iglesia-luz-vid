import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import base64

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
        .stTabs [aria-selected="true"] {{ background-color: #8D6E63 !important; color: white !important; }}
        </style>
        <img src="{logo_html}" class="logo-esquina">
    """, unsafe_allow_html=True)

if login():
    aplicar_estetica()
    conn = st.connection("my_database", type=GSheetsConnection)

    # --- LISTAS DE REFERENCIA ---
    REDES = ["Red de Ruben", "Red de Simeon", "Red de Levi", "Red de Juda", "Red de Neftali", 
             "Red de Efrain", "Red de Gad", "Red de Aser", "Red de Isacar", "Red de Zabulom", 
             "Red de Jose", "Red de Benjamin", "Protemplo", "Suelto General", "Pastores", "Red de Niños"]
    METODOS = ["Bolivares en Efectivo", "USD en Efectivo", "Transferencia / PM", "Punto"]
    
    # Lista de empleados (Puedes agregar más aquí)
    EMPLEADOS = ["Pastor Principal", "Secretaria", "Mantenimiento", "Músico 1", "Músico 2", "Otro"]

    rol = st.session_state.usuario_actual
    titulos = ["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS", "📊 INFORMES"] if rol in ["admin", "tesoreria"] else ["🏠 INICIO", "📊 INFORMES"]
    tabs = st.tabs(titulos)

    # --- PESTAÑA INICIO ---
    with tabs[0]:
        st.markdown(f"<h4 style='text-align: right; color: #8D6E63;'>Bienvenido, {rol.capitalize()}</h4>", unsafe_allow_html=True)
        c_i1, c_i2, c_i3 = st.columns([1, 2, 1])
        with c_i2:
            try: st.image("logo.png", use_container_width=True)
            except: st.info("Iglesia Luz y Vida")
            st.markdown("<h1 style='text-align: center;'>Iglesia Cristiana Luz y Vida</h1>", unsafe_allow_html=True)
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

    if rol in ["admin", "tesoreria"]:
        # --- PESTAÑA INGRESOS ---
        with tabs[1]:
            st.header("📥 Registro de Ingresos")
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    f_rec = st.date_input("Fecha Recaudación", date.today(), key="f_ingreso")
                    red_sel = st.selectbox("Red", REDES, key="red_ingreso")
                    tipo_sel = st.radio("Clasificación", ["Ofrenda", "Diezmo"], key="tipo_ingreso")
                with col2:
                    met_sel = st.selectbox("Forma de Pago", METODOS, key="met_ingreso")
                    monto_in = st.number_input("Monto Ingresado", min_value=0.0, key="monto_ingreso")
                    tasa_v = 1.0; ref_v = "N/A"; banco_v = "N/A"; f_op_v = str(f_rec)
                    if met_sel == "USD en Efectivo":
                        tasa_v = st.number_input("Tasa BCV", min_value=1.0, value=36.0, key="tasa_ingreso")
                    elif met_sel in ["Transferencia / PM", "Punto"]:
                        banco_v = st.text_input("Banco", key="banco_ingreso") if met_sel == "Transferencia / PM" else "Punto"
                        ref_v = st.text_input("Referencia (4 d)", max_chars=4, key="ref_ingreso")
                        f_op_v = str(st.date_input("Fecha Operación", date.today(), key="f_op_ingreso"))
                with col3:
                    total_bs = monto_in * tasa_v if met_sel == "USD en Efectivo" else monto_in
                    st.metric("TOTAL Bs", f"{total_bs:,.2f}")
                    st.metric("10%", f"{(total_bs * 0.10):,.2f}")

                if st.button("💾 GUARDAR REGISTRO", use_container_width=True):
                    try:
                        nuevo_df = pd.DataFrame([{"Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel, "Metodo": met_sel, "Banco": banco_v, "Referencia": str(ref_v), "Fecha_Op": str(f_op_v), "Monto_Orig": float(monto_in), "Tasa": float(tasa_v), "Total_Bs": float(total_bs), "Diezmo_10": float(total_bs*0.10)}])
                        df_ex = conn.read(worksheet="INGRESOS", ttl=0)
                        df_final = pd.concat([df_ex, nuevo_df], ignore_index=True) if df_ex is not None else nuevo_df
                        conn.update(worksheet="INGRESOS", data=df_final)
                        st.cache_data.clear()
                        st.success("✅ ¡Guardado!")
                        st.rerun()
                    except Exception as e: st.exception(e)

            st.divider()
            st.subheader("📋 Gestión de Registros (Edición/Borrado)")
            try:
                df_ing = conn.read(worksheet="INGRESOS", ttl=0)
                if df_ing is not None and not df_ing.empty:
                    # Editor de datos para corregir o borrar
                    edited_df = st.data_editor(df_ing, num_rows="dynamic", use_container_width=True, key="editor_ingresos")
                    if st.button("💾 APLICAR CAMBIOS EN TABLA"):
                        conn.update(worksheet="INGRESOS", data=edited_df)
                        st.cache_data.clear()
                        st.success("Cambios aplicados correctamente")
                        st.rerun()
                else: st.info("No hay registros aún.")
            except: st.warning("Error al cargar la gestión.")

        # --- PESTAÑA EGRESOS ---
        with tabs[2]:
            st.header("📤 Pagos a Personal")
            with st.container(border=True):
                e1, e2 = st.columns(2)
                with e1:
                    nom = st.selectbox("Nombre del Beneficiario", EMPLEADOS, key="nom_egreso")
                    cargo = st.text_input("Cargo", key="cargo_egreso")
                    m_usd = st.number_input("Monto USD", min_value=0.0, key="monto_egreso")
                with e2:
                    t_eg = st.number_input("Tasa BCV", min_value=1.0, value=36.0, key="tasa_egreso")
                    obs = st.text_area("Observaciones", key="obs_egreso")
                    st.metric("Total en Bs", f"{(m_usd * t_eg):,.2f}")
                
                if st.button("💸 REGISTRAR PAGO", use_container_width=True):
                    try:
                        n_e = pd.DataFrame([{"Fecha": str(date.today()), "Nombre": nom, "Cargo": cargo, "Sueldo_USD": m_usd, "Tasa": t_eg, "Total_Bs": m_usd*t_eg, "Observaciones": obs}])
                        df_ex_e = conn.read(worksheet="EGRESOS", ttl=0)
                        df_f_e = pd.concat([df_ex_e, n_e], ignore_index=True) if df_ex_e is not None else n_e
                        conn.update(worksheet="EGRESOS", data=df_f_e)
                        st.cache_data.clear()
                        st.success("Pago registrado")
                        st.rerun()
                    except Exception as e: st.exception(e)
            
            st.divider()
            st.subheader("📋 Vista Previa de Egresos")
            try:
                df_egr = conn.read(worksheet="EGRESOS", ttl=0)
                if df_egr is not None and not df_egr.empty:
                    st.dataframe(df_egr, use_container_width=True)
                    st.metric("TOTAL GASTADO (Bs)", f"{df_egr['Total_Bs'].sum():,.2f}")
                else: st.info("No hay egresos registrados.")
            except: st.warning("Error al cargar egresos.")

        idx_inf = 3
    else:
        idx_inf = 1

    # --- PESTAÑA INFORMES ---
    with tabs[idx_inf]:
        st.header("📊 Reportes Administrativos")
        try:
            df_rep = conn.read(worksheet="INGRESOS", ttl=0)
            if df_rep is not None and not df_rep.empty:
                # Convertir fechas para filtrar
                df_rep['Fecha'] = pd.to_datetime(df_rep['Fecha']).dt.date
                
                # --- FILTROS ---
                with st.expander("🔍 Filtros de Búsqueda", expanded=True):
                    f1, f2 = st.columns(2)
                    inicio = f1.date_input("Fecha Inicio", date.today().replace(day=1))
                    fin = f2.date_input("Fecha Fin", date.today())
                    redes_f = st.multiselect("Filtrar por Red", ["TODAS"] + REDES, default="TODAS")

                # Aplicar filtros
                mask = (df_rep['Fecha'] >= inicio) & (df_rep['Fecha'] <= fin)
                df_filtrado = df_rep.loc[mask]
                if "TODAS" not in redes_f:
                    df_filtrado = df_filtrado[df_filtrado['Red'].isin(redes_f)]

                if not df_filtrado.empty:
                    # --- CÁLCULOS SOLICITADOS ---
                    # 1. Diezmo Apóstol (10% de TODO lo recaudado en el filtro)
                    diezmo_apostol = df_filtrado['Diezmo_10'].sum()
                    
                    # 2. Diezmo Presbiterio (10% de todo EXCEPTO Zabulon)
                    df_presbiterio = df_filtrado[df_filtrado['Red'] != "Red de Zabulom"]
                    diezmo_presbiterio = df_presbiterio['Diezmo_10'].sum()

                    # Mostrar Métricas
                    c1, c2, c3 = st.columns(3)
                    c1.metric("TOTAL FILTRADO (Bs)", f"{df_filtrado['Total_Bs'].sum():,.2f}")
                    c2.metric("APÓSTOL (10% Total)", f"{diezmo_apostol:,.2f} Bs")
                    c3.metric("PRESBITERIO (Excl. Zabulón)", f"{diezmo_presbiterio:,.2f} Bs")

                    st.markdown("### Detalles de Movimientos Filtrados")
                    st.dataframe(df_filtrado, use_container_width=True)
                else:
                    st.warning("No hay datos para los filtros seleccionados.")
            else:
                st.info("La base de datos está vacía.")
        except Exception as e:
            st.error(f"Error al generar informe: {e}")
