import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date
import base64
from fpdf import FPDF

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

# --- FUNCIONES ESTÉTICAS Y PDF ---
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
        [data-testid="stMetricValue"] {{ font-size: 24px; color: #5D4037; }}
        </style>
        <img src="{logo_html}" class="logo-esquina">
    """, unsafe_allow_html=True)

def generar_pdf_egresos(df, f_ini, f_fin, total_bs):
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(190, 10, txt="Iglesia Cristiana Luz y Vida", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="Reporte de Egresos y Pagos", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 8, txt=f"Período consultado: {f_ini} al {f_fin}", ln=True, align='C')
    pdf.ln(5)

    # Encabezados de la tabla
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(22, 8, "Fecha", 1, 0, 'C')
    pdf.cell(60, 8, "Beneficiario", 1, 0, 'C')
    pdf.cell(20, 8, "USD", 1, 0, 'C')
    pdf.cell(20, 8, "Tasa", 1, 0, 'C')
    pdf.cell(30, 8, "Total Bs", 1, 0, 'C')
    pdf.cell(38, 8, "Nota", 1, 1, 'C')

    # Filas de la tabla
    pdf.set_font("Arial", '', 8)
    for i, row in df.iterrows():
        fecha_str = str(row.get('Fecha', ''))
        # Limitar caracteres para que no se deforme la tabla en el PDF
        ben_str = str(row.get('Empleado_Beneficiario', ''))[:30] 
        obs_str = str(row.get('Observaciones', ''))[:20]
        
        # Evitar errores con tildes en el PDF
        ben_str = ben_str.encode('latin-1', 'replace').decode('latin-1')
        obs_str = obs_str.encode('latin-1', 'replace').decode('latin-1')

        usd_str = f"{float(row.get('Sueldo_USD', 0)):.2f}"
        tasa_str = f"{float(row.get('Tasa', 0)):.2f}"
        bs_str = f"{float(row.get('Total_Bs', 0)):.2f}"

        pdf.cell(22, 8, fecha_str, 1, 0, 'C')
        pdf.cell(60, 8, ben_str, 1, 0, 'L')
        pdf.cell(20, 8, usd_str, 1, 0, 'R')
        pdf.cell(20, 8, tasa_str, 1, 0, 'R')
        pdf.cell(30, 8, bs_str, 1, 0, 'R')
        pdf.cell(38, 8, obs_str, 1, 1, 'L')

    pdf.ln(5)
    # Total Final
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=f"TOTAL PAGADO: {total_bs:,.2f} Bs", ln=True, align='R')

    return pdf.output(dest="S").encode("latin-1")

# --- EJECUCIÓN PRINCIPAL ---
if login():
    aplicar_estetica()
    conn = st.connection("my_database", type=GSheetsConnection)

    REDES = ["Red de Ruben", "Red de Simeon", "Red de Levi", "Red de Juda", "Red de Neftali", 
             "Red de Efrain", "Red de Gad", "Red de Aser", "Red de Isacar", "Red de Zabulom", 
             "Red de Jose", "Red de Benjamin", "Protemplo", "Suelto General", "Pastores", "Red de Niños"]
    
    METODOS = ["Bolivares en Efectivo", "USD en Efectivo", "Transferencia / PM", "Punto"]

    rol = st.session_state.usuario_actual
    
    titulos = ["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS", "📊 INFORMES", "👥 PERSONAL"] if rol in ["admin", "tesoreria"] else ["🏠 INICIO", "📊 INFORMES"]
    tabs = st.tabs(titulos)

    # --- PESTAÑA INICIO ---
    with tabs[0]:
        st.markdown(f"<h4 style='text-align: right; color: #8D6E63;'>Bienvenido, {rol.capitalize()}</h4>", unsafe_allow_html=True)
        c_i1, c_i2, c_i3 = st.columns([1, 2, 1])
        with c_i2:
            try: st.image("logo.png", use_container_width=True)
            except: st.info("Iglesia Cristiana Luz y Vida")
            st.markdown("<h1 style='text-align: center;'>Iglesia Cristiana Luz y Vida</h1>", unsafe_allow_html=True)
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

    if rol in ["admin", "tesoreria"]:
        # --- PESTAÑA INGRESOS ---
        with tabs[1]:
            st.subheader("📥 Cargar Nuevo Registro")
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    f_rec = st.date_input("Fecha Recaudación", date.today(), key="ing_fecha")
                    red_sel = st.selectbox("Red / Origen", REDES, key="ing_red")
                    tipo_sel = st.radio("Clasificación", ["Ofrenda", "Diezmo"], key="ing_tipo", horizontal=True)
                with col2:
                    met_sel = st.selectbox("Método de Pago", METODOS, key="ing_metodo")
                    monto_in = st.number_input("Monto Recibido", min_value=0.0, step=0.01, key="ing_monto")
                    tasa_v = 1.0; ref_v = "N/A"; banco_v = "N/A"; f_op_v = str(f_rec)
                    if met_sel == "USD en Efectivo":
                        tasa_v = st.number_input("Tasa BCV", min_value=1.0, value=36.0, key="ing_tasa")
                    elif met_sel in ["Transferencia / PM", "Punto"]:
                        banco_v = st.text_input("Banco Emisor", key="ing_banco") if met_sel == "Transferencia / PM" else "Punto"
                        ref_v = st.text_input("Referencia (4 dígitos)", max_chars=4, key="ing_ref")
                        f_op_v = str(st.date_input("Fecha Operación", date.today(), key="ing_f_op"))
                with col3:
                    total_bs = monto_in * tasa_v if met_sel == "USD en Efectivo" else monto_in
                    st.metric("Total en Bolívares", f"{total_bs:,.2f} Bs")
                    st.metric("10% Correspondiente", f"{(total_bs * 0.10):,.2f} Bs")
                    if st.button("💾 GUARDAR REGISTRO", use_container_width=True):
                        try:
                            columnas_orden = ["Fecha", "Red", "Clasificacion", "Metodo", "Banco", "Referencia", "Fecha_Op", "Monto_Orig", "Tasa", "Total_Bs", "Diezmo_10"]
                            nuevo = pd.DataFrame([{
                                "Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel,
                                "Metodo": met_sel, "Banco": banco_v, "Referencia": str(ref_v),
                                "Fecha_Op": str(f_op_v), "Monto_Orig": float(monto_in),
                                "Tasa": float(tasa_v), "Total_Bs": float(total_bs),
                                "Diezmo_10": float(total_bs * 0.10)
                            }])
                            try:
                                df_actual = conn.read(worksheet="INGRESOS", ttl="10m")
                                df_update = pd.concat([df_actual, nuevo], ignore_index=True) if df_actual is not None else nuevo
                            except: df_update = nuevo
                            
                            for col in columnas_orden:
                                if col not in df_update.columns: df_update[col] = ""
                            
                            conn.update(worksheet="INGRESOS", data=df_update[columnas_orden])
                            st.cache_data.clear()
                            st.success("¡Registro guardado exitosamente!")
                            st.rerun()
                        except Exception as e: st.error(f"Error al guardar: {e}")

            st.markdown("---")
            st.subheader("📋 Gestión de Registros (Editar / Borrar)")
            try:
                df_gestion = conn.read(worksheet="INGRESOS", ttl="10m")
                if df_gestion is not None and not df_gestion.empty:
                    df_editado = st.data_editor(df_gestion, num_rows="dynamic", use_container_width=True, key="gestor_ingresos")
                    if st.button("🔄 APLICAR CAMBIOS EN LA BASE DE DATOS", type="primary"):
                        conn.update(worksheet="INGRESOS", data=df_editado)
                        st.cache_data.clear()
                        st.success("¡Base de datos actualizada!")
                        st.rerun()
                else: st.write("No hay registros para mostrar.")
            except: st.warning("Conectando con la base de datos...")

        # --- PESTAÑA EGRESOS ---
        with tabs[2]:
            st.header("📤 Registro de Egresos / Pagos")
            
            try:
                df_emp = conn.read(worksheet="EMPLEADOS", ttl="10m")
                if df_emp is not None and not df_emp.empty:
                    lista_empleados = (df_emp['Nombre'].astype(str) + " " + df_emp['Apellido'].astype(str) + " - " + df_emp['Cargo'].astype(str)).tolist()
                else: lista_empleados = ["Sin empleados registrados"]
            except: lista_empleados = ["Debe crear la pestaña EMPLEADOS en su Excel"]

            with st.container(border=True):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    nom_e = st.selectbox("Beneficiario / Empleado", lista_empleados, key="eg_nom")
                    monto_usd_e = st.number_input("Monto en USD", min_value=0.0, step=0.01, key="eg_monto")
                with col_e2:
                    tasa_e = st.number_input("Tasa BCV del día", min_value=1.0, value=36.0, key="eg_tasa")
                    nota_e = st.text_area("Observaciones", placeholder="Ej: Pago de quincena...", key="eg_obs")
                    st.metric("Total a Pagar (Bs)", f"{(monto_usd_e * tasa_e):,.2f} Bs")
                
                if st.button("💸 REGISTRAR PAGO", use_container_width=True):
                    try:
                        nuevo_egreso = pd.DataFrame([{
                            "Fecha": str(date.today()), "Empleado_Beneficiario": nom_e,
                            "Sueldo_USD": float(monto_usd_e), "Tasa": float(tasa_e),
                            "Total_Bs": float(monto_usd_e * tasa_e), "Observaciones": nota_e
                        }])
                        try:
                            df_eg_actual = conn.read(worksheet="EGRESOS", ttl="10m")
                            df_eg_final = pd.concat([df_eg_actual, nuevo_egreso], ignore_index=True) if df_eg_actual is not None else nuevo_egreso
                        except: df_eg_final = nuevo_egreso
                        
                        conn.update(worksheet="EGRESOS", data=df_eg_final)
                        st.cache_data.clear()
                        st.success("Pago registrado correctamente")
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
            
            st.markdown("---")
            st.subheader("📋 Gestión de Egresos (Editar / Borrar)")
            try:
                df_egr_view = conn.read(worksheet="EGRESOS", ttl="10m")
                if df_egr_view is not None and not df_egr_view.empty:
                    df_egr_edit = st.data_editor(df_egr_view, num_rows="dynamic", use_container_width=True, key="gestor_egresos")
                    if st.button("🔄 APLICAR CAMBIOS EN EGRESOS", type="primary"):
                        conn.update(worksheet="EGRESOS", data=df_egr_edit)
                        st.cache_data.clear()
                        st.success("¡Egresos actualizados!")
                        st.rerun()
                else: st.write("Aún no hay egresos registrados.")
            except: st.info("Sincronizando...")

        idx_inf = 3
        idx_pers = 4
    else:
        idx_inf = 1

    # --- PESTAÑA INFORMES ---
    with tabs[idx_inf]:
        st.header("📊 Reportes y Auditoría")
        
        # Selector de tipo de reporte
        tipo_reporte = st.radio("Seleccione el módulo a consultar:", ["📥 Reporte de INGRESOS", "📤 Reporte de EGRESOS (PDF)"], horizontal=True)
        st.markdown("---")

        if tipo_reporte == "📥 Reporte de INGRESOS":
            try:
                df_inf = conn.read(worksheet="INGRESOS", ttl="10m")
                if df_inf is not None and not df_inf.empty:
                    df_inf['Fecha'] = pd.to_datetime(df_inf['Fecha']).dt.date
                    
                    with st.expander("🔍 Filtros de Reporte de Ingresos", expanded=True):
                        c_f1, c_f2, c_f3 = st.columns(3)
                        f_ini = c_f1.date_input("Desde", date.today().replace(day=1))
                        f_fin = c_f2.date_input("Hasta", date.today())
                        red_filtro = c_f3.multiselect("Filtrar Redes", ["TODAS"] + REDES, default="TODAS")

                    mask = (df_inf['Fecha'] >= f_ini) & (df_inf['Fecha'] <= f_fin)
                    df_fil = df_inf.loc[mask]
                    if "TODAS" not in red_filtro:
                        df_fil = df_fil[df_fil['Red'].isin(red_filtro)]

                    if not df_fil.empty:
                        total_general = df_fil['Total_Bs'].sum()
                        apostol = df_fil['Diezmo_10'].sum()
                        df_presb = df_fil[df_fil['Red'] != "Red de Zabulom"]
                        presbiterio = df_presb['Diezmo_10'].sum()

                        m1, m2, m3 = st.columns(3)
                        m1.metric("Ingreso Total (Filtro)", f"{total_general:,.2f} Bs")
                        m2.metric("APÓSTOL (10% Total)", f"{apostol:,.2f} Bs")
                        m3.metric("PRESBITERIO (Sin Zabulón)", f"{presbiterio:,.2f} Bs")

                        st.markdown("---")
                        st.subheader("📈 Resumen Detallado por las 16 Redes")
                        resumen_redes = df_fil.groupby('Red').agg({'Total_Bs': 'sum', 'Diezmo_10': 'sum'}).reset_index()
                        df_todas_redes = pd.DataFrame({'Red': REDES})
                        resumen_final = pd.merge(df_todas_redes, resumen_redes, on='Red', how='left').fillna(0)
                        
                        st.table(resumen_final.style.format({"Total_Bs": "{:,.2f} Bs", "Diezmo_10": "{:,.2f} Bs"}))
                    else:
                        st.warning("No hay datos para estos filtros.")
                else:
                    st.info("Base de datos sin registros.")
            except Exception as e: st.error(f"Error al procesar ingresos: {e}")

        else:
            # LÓGICA DE REPORTE DE EGRESOS CON PDF
            try:
                df_egr_inf = conn.read(worksheet="EGRESOS", ttl="10m")
                if df_egr_inf is not None and not df_egr_inf.empty:
                    df_egr_inf['Fecha'] = pd.to_datetime(df_egr_inf['Fecha']).dt.date
                    
                    with st.expander("🔍 Filtros de Reporte de Egresos", expanded=True):
                        col_ef1, col_ef2 = st.columns(2)
                        fe_ini = col_ef1.date_input("Desde", date.today().replace(day=1), key="fe_ini")
                        fe_fin = col_ef2.date_input("Hasta", date.today(), key="fe_fin")

                    mask_e = (df_egr_inf['Fecha'] >= fe_ini) & (df_egr_inf['Fecha'] <= fe_fin)
                    df_fil_egr = df_egr_inf.loc[mask_e]

                    if not df_fil_egr.empty:
                        total_egresos = df_fil_egr['Total_Bs'].sum()
                        st.metric("TOTAL PAGADO EN EL PERÍODO (Bs)", f"{total_egresos:,.2f} Bs")
                        st.dataframe(df_fil_egr, use_container_width=True)

                        # BOTÓN DE DESCARGA PDF
                        pdf_data = generar_pdf_egresos(df_fil_egr, fe_ini, fe_fin, total_egresos)
                        st.download_button(
                            label="📄 DESCARGAR REPORTE EN PDF",
                            data=pdf_data,
                            file_name=f"Reporte_Egresos_{fe_ini}_al_{fe_fin}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    else:
                        st.warning("No hay egresos registrados en este rango de fechas.")
                else:
                    st.info("Base de datos de Egresos vacía.")
            except Exception as e: st.error(f"Error al procesar egresos: {e}")

    # --- PESTAÑA PERSONAL ---
    if rol in ["admin", "tesoreria"]:
        with tabs[idx_pers]:
            st.header("👥 Gestión de Empleados y Beneficiarios")
            st.write("Agrega a las personas que recibirán pagos.")
            try:
                df_empleados = conn.read(worksheet="EMPLEADOS", ttl="10m")
                if df_empleados is None or df_empleados.empty:
                    df_empleados = pd.DataFrame(columns=["Nombre", "Apellido", "Cargo"])
            except:
                df_empleados = pd.DataFrame(columns=["Nombre", "Apellido", "Cargo"])
            
            df_emp_editado = st.data_editor(df_empleados, num_rows="dynamic", use_container_width=True, key="gestor_empleados")
            
            if st.button("💾 GUARDAR LISTA DE PERSONAL", type="primary"):
                df_limpio = df_emp_editado.fillna("")
                conn.update(worksheet="EMPLEADOS", data=df_limpio)
                st.cache_data.clear()
                st.success("¡Directorio de personal actualizado!")
                st.rerun()
