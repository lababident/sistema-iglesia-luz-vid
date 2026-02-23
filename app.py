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
    
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(190, 10, txt="Iglesia Cristiana Luz y Vida", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="Reporte de Egresos Fijos", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 8, txt=f"Período consultado: {f_ini} al {f_fin}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(22, 8, "Fecha", 1, 0, 'C')
    pdf.cell(60, 8, "Beneficiario", 1, 0, 'C')
    pdf.cell(20, 8, "USD", 1, 0, 'C')
    pdf.cell(20, 8, "Tasa", 1, 0, 'C')
    pdf.cell(30, 8, "Total Bs", 1, 0, 'C')
    pdf.cell(38, 8, "Nota", 1, 1, 'C')

    pdf.set_font("Arial", '', 8)
    for i, row in df.iterrows():
        fecha_str = str(row.get('Fecha', ''))
        ben_str = str(row.get('Empleado_Beneficiario', ''))[:30] 
        obs_str = str(row.get('Observaciones', ''))[:20]
        
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
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=f"TOTAL PAGADO: {total_bs:,.2f} Bs", ln=True, align='R')

    return pdf.output(dest="S").encode("latin-1")


def generar_pdf_otros_egresos(df, f_ini, f_fin, total_monto):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(190, 10, txt="Iglesia Cristiana Luz y Vida", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="Reporte de Otros Egresos (Gastos Operativos)", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 8, txt=f"Período consultado: {f_ini} al {f_fin}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(30, 8, "Fecha", 1, 0, 'C')
    pdf.cell(60, 8, "Descripción", 1, 0, 'C')
    pdf.cell(40, 8, "Monto", 1, 0, 'C')
    pdf.cell(60, 8, "Observaciones", 1, 1, 'C')

    pdf.set_font("Arial", '', 8)
    for i, row in df.iterrows():
        fecha_str = str(row.get('Fecha', ''))
        desc_str = str(row.get('Descripcion', ''))[:35] 
        obs_str = str(row.get('Observaciones', ''))[:35]
        
        desc_str = desc_str.encode('latin-1', 'replace').decode('latin-1')
        obs_str = obs_str.encode('latin-1', 'replace').decode('latin-1')
        
        try:
            monto_val = float(row.get('Monto', 0))
            monto_str = f"{monto_val:,.2f}"
        except:
            monto_str = str(row.get('Monto', '0'))

        pdf.cell(30, 8, fecha_str, 1, 0, 'C')
        pdf.cell(60, 8, desc_str, 1, 0, 'L')
        pdf.cell(40, 8, monto_str, 1, 0, 'R')
        pdf.cell(60, 8, obs_str, 1, 1, 'L')

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=f"TOTAL OTROS EGRESOS: {total_monto:,.2f}", ln=True, align='R')

    return pdf.output(dest="S").encode("latin-1")


def generar_pdf_ingresos(df_resumen, f_ini, f_fin, total_bs, apostol, presbiterio):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 15)
    pdf.cell(190, 10, txt="Iglesia Cristiana Luz y Vida", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="Reporte de Ingresos (Diezmos y Ofrendas)", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 8, txt=f"Período consultado: {f_ini} al {f_fin}", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(63, 8, txt=f"INGRESO TOTAL: {total_bs:,.2f} Bs", border=1, align='C')
    pdf.cell(63, 8, txt=f"APOSTOL (10%): {apostol:,.2f} Bs", border=1, align='C')
    pdf.cell(64, 8, txt=f"PRESBITERIO: {presbiterio:,.2f} Bs", border=1, ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(90, 8, "Red", 1, 0, 'C')
    pdf.cell(50, 8, "Total Ingresado (Bs)", 1, 0, 'C')
    pdf.cell(50, 8, "Diezmo 10% (Bs)", 1, 1, 'C')

    pdf.set_font("Arial", '', 9)
    for i, row in df_resumen.iterrows():
        red_str = str(row.get('Red', ''))
        red_str = red_str.encode('latin-1', 'replace').decode('latin-1')
        
        bs_str = f"{float(row.get('Total_Bs', 0)):,.2f}"
        diezmo_str = f"{float(row.get('Diezmo_10', 0)):,.2f}"

        pdf.cell(90, 8, red_str, 1, 0, 'L')
        pdf.cell(50, 8, bs_str, 1, 0, 'R')
        pdf.cell(50, 8, diezmo_str, 1, 1, 'R')

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
    
    titulos = ["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS FIJOS", "🛠️ OTROS EGRESOS", "📊 INFORMES", "👥 PERSONAL"] if rol in ["admin", "tesoreria"] else ["🏠 INICIO", "📊 INFORMES"]
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
                    tasa_v = 1.0; ref_v = ""; banco_v = ""
                    
                    if met_sel == "USD en Efectivo":
                        tasa_v = st.number_input("Tasa BCV", min_value=1.0, value=36.0, key="ing_tasa")
                        f_op_v = str(f_rec)
                    elif met_sel in ["Transferencia / PM", "Punto"]:
                        banco_v = st.text_input("Banco", key="ing_banco") if met_sel == "Transferencia / PM" else "Punto"
                        ref_v = st.text_input("Referencia (4 dígitos)", max_chars=4, key="ing_ref")
                        f_op_v = str(st.date_input("Fecha Operación", date.today(), key="ing_f_op"))
                    else:
                        f_op_v = str(f_rec)
                        
                with col3:
                    total_bs = monto_in * tasa_v if met_sel == "USD en Efectivo" else monto_in
                    st.metric("Total en Bolívares", f"{total_bs:,.2f} Bs")
                    st.metric("10% Correspondiente", f"{(total_bs * 0.10):,.2f} Bs")
                    
                    if st.button("💾 GUARDAR REGISTRO", use_container_width=True):
                        try:
                            # 1. Leer la base de datos actual para validar
                            try:
                                df_actual = conn.read(worksheet="INGRESOS", ttl="10m")
                            except:
                                df_actual = None

                            es_duplicado = False
                            
                            ref_str = str(ref_v).strip()
                            f_op_str = str(f_op_v).strip()

                            # 2. Validar duplicados
                            if df_actual is not None and not df_actual.empty and met_sel in ["Transferencia / PM", "Punto"] and ref_str != "":
                                refs_limpias = df_actual['Referencia'].astype(str).str.replace('.0', '', regex=False).str.strip()
                                fechas_limpias = df_actual['Fecha_Op'].astype(str).str.strip()
                                
                                duplicados = df_actual[
                                    (df_actual['Metodo'].isin(["Transferencia / PM", "Punto"])) & 
                                    (fechas_limpias == f_op_str) & 
                                    (refs_limpias == ref_str)
                                ]
                                
                                if not duplicados.empty:
                                    es_duplicado = True

                            # 3. Tomar acción
                            if es_duplicado:
                                st.error(f"⚠️ ¡ALERTA! Ya existe un pago registrado el {f_op_str} con la referencia '{ref_str}'.")
                            elif monto_in <= 0:
                                st.error("⚠️ El monto debe ser mayor a 0 para poder guardarlo.")
                            else:
                                columnas_orden = ["Fecha", "Red", "Clasificacion", "Metodo", "Banco", "Referencia", "Fecha_Op", "Monto_Orig", "Tasa", "Total_Bs", "Diezmo_10"]
                                nuevo = pd.DataFrame([{
                                    "Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel,
                                    "Metodo": met_sel, "Banco": banco_v, "Referencia": ref_str,
                                    "Fecha_Op": f_op_str, "Monto_Orig": float(monto_in),
                                    "Tasa": float(tasa_v), "Total_Bs": float(total_bs),
                                    "Diezmo_10": float(total_bs * 0.10)
                                }])
                                
                                df_update = pd.concat([df_actual, nuevo], ignore_index=True) if df_actual is not None else nuevo
                                
                                for col in columnas_orden:
                                    if col not in df_update.columns: df_update[col] = ""
                                
                                conn.update(worksheet="INGRESOS", data=df_update[columnas_orden])
                                st.cache_data.clear()
                                
                                # 4. VACIAR LOS CAMPOS (Forzando los valores en el session_state)
                                st.session_state.ing_monto = 0.0
                                if "ing_banco" in st.session_state:
                                    st.session_state.ing_banco = ""
                                if "ing_ref" in st.session_state:
                                    st.session_state.ing_ref = ""
                                
                                st.success("¡Registro guardado exitosamente!")
                                st.rerun()
                                
                        except Exception as e: 
                            st.error(f"Error al procesar: {e}")

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
            st.header("📤 Registro de Egresos Fijos / Nómina")
            
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
                
                if st.button("💸 REGISTRAR PAGO FIJO", use_container_width=True):
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
            st.subheader("📋 Gestión de Egresos Fijos (Editar / Borrar)")
            try:
                df_egr_view = conn.read(worksheet="EGRESOS", ttl="10m")
                if df_egr_view is not None and not df_egr_view.empty:
                    df_egr_edit = st.data_editor(df_egr_view, num_rows="dynamic", use_container_width=True, key="gestor_egresos")
                    if st.button("🔄 APLICAR CAMBIOS EN EGRESOS FIJOS", type="primary"):
                        conn.update(worksheet="EGRESOS", data=df_egr_edit)
                        st.cache_data.clear()
                        st.success("¡Egresos actualizados!")
                        st.rerun()
                else: st.write("Aún no hay egresos registrados.")
            except: st.info("Sincronizando...")

        # --- PESTAÑA OTROS EGRESOS ---
        with tabs[3]:
            st.header("🛠️ Registro de Otros Egresos")
            st.write("Aquí puedes registrar gastos operativos, compras de insumos, reparaciones, etc.")
            
            with st.container(border=True):
                col_oe1, col_oe2 = st.columns(2)
                with col_oe1:
                    desc_oe = st.text_input("Descripción del gasto", placeholder="Ej: Compra de artículos de limpieza", key="oe_desc")
                    fecha_oe = st.date_input("Fecha", date.today(), key="oe_fecha")
                with col_oe2:
                    monto_oe = st.number_input("Monto", min_value=0.0, step=0.01, key="oe_monto")
                    obs_oe = st.text_area("Observaciones", placeholder="Ej: Factura #1234", key="oe_obs")
                
                if st.button("🔧 REGISTRAR GASTO", use_container_width=True):
                    if desc_oe and monto_oe > 0:
                        try:
                            nuevo_otro_egreso = pd.DataFrame([{
                                "Descripcion": desc_oe, "Fecha": str(fecha_oe),
                                "Monto": float(monto_oe), "Observaciones": obs_oe
                            }])
                            try:
                                df_oe_actual = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
                                df_oe_final = pd.concat([df_oe_actual, nuevo_otro_egreso], ignore_index=True) if df_oe_actual is not None else nuevo_otro_egreso
                            except: df_oe_final = nuevo_otro_egreso
                            
                            conn.update(worksheet="OTROS_EGRESOS", data=df_oe_final)
                            st.cache_data.clear()
                            st.success("Gasto registrado correctamente")
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}. Crea la pestaña OTROS_EGRESOS en Sheets.")
                    else:
                        st.error("Por favor ingresa una descripción y un monto mayor a cero.")

            st.markdown("---")
            st.subheader("📋 Gestión de Otros Egresos (Editar / Borrar)")
            try:
                df_oe_view = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
                if df_oe_view is not None and not df_oe_view.empty:
                    df_oe_edit = st.data_editor(df_oe_view, num_rows="dynamic", use_container_width=True, key="gestor_otros_egresos")
                    if st.button("🔄 APLICAR CAMBIOS EN OTROS EGRESOS", type="primary"):
                        conn.update(worksheet="OTROS_EGRESOS", data=df_oe_edit)
                        st.cache_data.clear()
                        st.success("¡Otros egresos actualizados!")
                        st.rerun()
                else: 
                    st.write("Aún no hay otros egresos registrados.")
            except: 
                st.info("Sincronizando o buscando pestaña OTROS_EGRESOS...")

        idx_inf = 4
        idx_pers = 5
    else:
        idx_inf = 1

    # --- PESTAÑA INFORMES ---
    with tabs[idx_inf]:
        st.header("📊 Reportes y Auditoría")
        
        tipo_reporte = st.radio("Seleccione el módulo a consultar:", 
                                ["📥 Reporte de INGRESOS (PDF)", "📤 Reporte de EGRESOS Fijos (PDF)", "🛠️ Reporte de OTROS EGRESOS (PDF)"], 
                                horizontal=True)
        st.markdown("---")

        if tipo_reporte == "📥 Reporte de INGRESOS (PDF)":
            try:
                df_inf = conn.read(worksheet="INGRESOS", ttl="10m")
                if df_inf is not None and not df_inf.empty:
                    df_inf['Fecha'] = pd.to_datetime(df_inf['Fecha']).dt.date
                    
                    with st.expander("🔍 Filtros de Reporte de Ingresos", expanded=True):
                        c_f1, c_f2, c_f3 = st.columns(3)
                        f_ini = c_f1.date_input("Desde", date.today().replace(day=1), key="fi_ing")
                        f_fin = c_f2.date_input("Hasta", date.today(), key="ff_ing")
                        red_filtro = c_f3.multiselect("Filtrar Redes", ["TODAS"] + REDES, default="TODAS")

                    mask = (df_inf['Fecha'] >= f_ini) & (df_inf['Fecha'] <= f_fin)
                    df_fil = df_inf.loc[mask]
                    if "TODAS" not in red_filtro:
                        df_fil = df_fil[df_fil['Red'].isin(red_filtro)]

                    if not df_fil.empty:
                        efectivo_bs = df_fil[df_fil['Metodo'] == 'Bolivares en Efectivo']['Total_Bs'].sum()
                        efectivo_usd_monto = df_fil[df_fil['Metodo'] == 'USD en Efectivo']['Monto_Orig'].sum() 
                        efectivo_usd_bs = df_fil[df_fil['Metodo'] == 'USD en Efectivo']['Total_Bs'].sum() 
                        transf_pm = df_fil[df_fil['Metodo'] == 'Transferencia / PM']['Total_Bs'].sum()
                        punto = df_fil[df_fil['Metodo'] == 'Punto']['Total_Bs'].sum()

                        st.subheader("💰 Resumen por Método de Pago")
                        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                        col_m1.metric("Efectivo Bs", f"{efectivo_bs:,.2f} Bs")
                        col_m2.metric("Efectivo Divisas", f"${efectivo_usd_monto:,.2f} USD")
                        col_m3.metric("Transferencias / PM", f"{transf_pm:,.2f} Bs")
                        col_m4.metric("Punto", f"{punto:,.2f} Bs")

                        datos_torta = pd.DataFrame({
                            "Método": ["Efectivo Bs", "Efectivo Divisas (en Bs)", "Transferencia / PM", "Punto"],
                            "Monto": [efectivo_bs, efectivo_usd_bs, transf_pm, punto]
                        })
                        datos_torta = datos_torta[datos_torta["Monto"] > 0] 
                        
                        if not datos_torta.empty:
                            fig = px.pie(datos_torta, values="Monto", names="Método", title="Distribución de Ingresos (Proporción en Bolívares)", hole=0.3)
                            st.plotly_chart(fig, use_container_width=True)

                        st.markdown("---")

                        total_general = df_fil['Total_Bs'].sum()
                        apostol = df_fil['Diezmo_10'].sum()
                        df_presb = df_fil[df_fil['Red'] != "Red de Zabulom"]
                        presbiterio = df_presb['Diezmo_10'].sum()

                        st.subheader("🏛️ Resumen Institucional")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("INGRESO TOTAL", f"{total_general:,.2f} Bs")
                        m2.metric("APÓSTOL (10% Total)", f"{apostol:,.2f} Bs")
                        m3.metric("PRESBITERIO", f"{presbiterio:,.2f} Bs")

                        st.markdown("---")
                        st.subheader("📈 Resumen Detallado por las 16 Redes")
                        resumen_redes = df_fil.groupby('Red').agg({'Total_Bs': 'sum', 'Diezmo_10': 'sum'}).reset_index()
                        df_todas_redes = pd.DataFrame({'Red': REDES})
                        resumen_final = pd.merge(df_todas_redes, resumen_redes, on='Red', how='left').fillna(0)
                        
                        st.table(resumen_final.style.format({"Total_Bs": "{:,.2f} Bs", "Diezmo_10": "{:,.2f} Bs"}))
                        
                        pdf_data_ingresos = generar_pdf_ingresos(resumen_final, f_ini, f_fin, total_general, apostol, presbiterio)
                        st.download_button(
                            label="📄 DESCARGAR REPORTE DE INGRESOS EN PDF",
                            data=pdf_data_ingresos,
                            file_name=f"Reporte_Ingresos_{f_ini}_al_{f_fin}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    else:
                        st.warning("No hay datos para estos filtros.")
                else:
                    st.info("Base de datos sin registros.")
            except Exception as e: st.error(f"Error al procesar ingresos: {e}")

        elif tipo_reporte == "📤 Reporte de EGRESOS Fijos (PDF)":
            try:
                df_egr_inf = conn.read(worksheet="EGRESOS", ttl="10m")
                if df_egr_inf is not None and not df_egr_inf.empty:
                    df_egr_inf['Fecha'] = pd.to_datetime(df_egr_inf['Fecha']).dt.date
                    
                    with st.expander("🔍 Filtros de Reporte de Egresos Fijos", expanded=True):
                        col_ef1, col_ef2 = st.columns(2)
                        fe_ini = col_ef1.date_input("Desde", date.today().replace(day=1), key="fe_ini_eg")
                        fe_fin = col_ef2.date_input("Hasta", date.today(), key="fe_fin_eg")

                    mask_e = (df_egr_inf['Fecha'] >= fe_ini) & (df_egr_inf['Fecha'] <= fe_fin)
                    df_fil_egr = df_egr_inf.loc[mask_e]

                    if not df_fil_egr.empty:
                        total_egresos = df_fil_egr['Total_Bs'].sum()
                        st.metric("TOTAL PAGADO EN EL PERÍODO (Bs)", f"{total_egresos:,.2f} Bs")
                        st.dataframe(df_fil_egr, use_container_width=True)

                        pdf_data = generar_pdf_egresos(df_fil_egr, fe_ini, fe_fin, total_egresos)
                        st.download_button(
                            label="📄 DESCARGAR REPORTE DE EGRESOS EN PDF",
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
            
        elif tipo_reporte == "🛠️ Reporte de OTROS EGRESOS (PDF)":
            try:
                df_oe_inf = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
                if df_oe_inf is not None and not df_oe_inf.empty:
                    df_oe_inf['Fecha'] = pd.to_datetime(df_oe_inf['Fecha']).dt.date
                    
                    with st.expander("🔍 Filtros de Reporte de Otros Egresos", expanded=True):
                        col_oef1, col_oef2 = st.columns(2)
                        foe_ini = col_oef1.date_input("Desde", date.today().replace(day=1), key="foe_ini")
                        foe_fin = col_oef2.date_input("Hasta", date.today(), key="foe_fin")

                    mask_oe = (df_oe_inf['Fecha'] >= foe_ini) & (df_oe_inf['Fecha'] <= foe_fin)
                    df_fil_oe = df_oe_inf.loc[mask_oe]

                    if not df_fil_oe.empty:
                        df_fil_oe['Monto'] = pd.to_numeric(df_fil_oe['Monto'], errors='coerce').fillna(0)
                        total_otros_egresos = df_fil_oe['Monto'].sum()
                        
                        st.metric("TOTAL GASTOS OPERATIVOS EN EL PERÍODO", f"{total_otros_egresos:,.2f}")
                        st.dataframe(df_fil_oe, use_container_width=True)

                        pdf_data_oe = generar_pdf_otros_egresos(df_fil_oe, foe_ini, foe_fin, total_otros_egresos)
                        st.download_button(
                            label="📄 DESCARGAR REPORTE DE OTROS EGRESOS EN PDF",
                            data=pdf_data_oe,
                            file_name=f"Reporte_OtrosEgresos_{foe_ini}_al_{foe_fin}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    else:
                        st.warning("No hay otros egresos registrados en este rango de fechas.")
                else:
                    st.info("Base de datos de Otros Egresos vacía.")
            except Exception as e: st.error(f"Error al procesar otros egresos: {e}")

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



