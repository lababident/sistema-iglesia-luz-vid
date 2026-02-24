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

def numero_a_letras(n):
    unidades = ["cero", "un", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve"]
    decenas = ["", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa"]
    especiales = {10:"diez", 11:"once", 12:"doce", 13:"trece", 14:"catorce", 15:"quince", 16:"dieciseis", 17:"diecisiete", 18:"dieciocho", 19:"diecinueve", 20:"veinte", 21:"veintiun", 22:"veintidos", 23:"veintitres", 24:"veinticuatro", 25:"veinticinco", 26:"veintiseis", 27:"veintisiete", 28:"veintiocho", 29:"veintinueve"}
    centenas = ["", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos", "seiscientos", "setecientos", "ochocientos", "novecientos"]

    def convertir(numero):
        if numero < 10: return unidades[numero]
        if numero < 30: return especiales[numero]
        if numero < 100:
            resto = numero % 10
            return decenas[numero // 10] + (" y " + unidades[resto] if resto > 0 else "")
        if numero == 100: return "cien"
        if numero < 1000:
            resto = numero % 100
            return centenas[numero // 100] + (" " + convertir(resto) if resto > 0 else "")
        if numero < 1000000:
            miles = numero // 1000
            resto = numero % 1000
            prefijo = "mil" if miles == 1 else convertir(miles) + " mil"
            return prefijo + (" " + convertir(resto) if resto > 0 else "")
        if numero < 1000000000:
            millones = numero // 1000000
            resto = numero % 1000000
            prefijo = "un millon" if millones == 1 else convertir(millones) + " millones"
            return prefijo + (" " + convertir(resto) if resto > 0 else "")
        return str(numero)

    entero = int(n)
    decimal = int(round((n - entero) * 100))
    letras_ent = convertir(entero)
    letras_dec = convertir(decimal) if decimal > 0 else "cero"
    return f"{letras_ent} bolivares con {letras_dec} centimos"

def obtener_proximo_recibo(conn):
    max_rec = 20000
    for hoja in ["EGRESOS", "OTROS_EGRESOS"]:
        try:
            df = conn.read(worksheet=hoja, ttl="10m")
            if df is not None and not df.empty and "Nro_Recibo" in df.columns:
                max_val = pd.to_numeric(df["Nro_Recibo"], errors='coerce').max()
                if pd.notna(max_val) and max_val > max_rec:
                    max_rec = max_val
        except: pass
    return int(max_rec + 1)

# --- FUNCIONES DE PDF ---
def generar_recibo_pdf(nro_recibo, monto, fecha, concepto):
    pdf = FPDF(orientation='P', unit='mm', format='Letter')
    pdf.add_page()
    pdf.rect(5, 5, 205, 135) 
    try: pdf.image('logo.png', 12, 12, 30)
    except: pass
    pdf.set_font("Arial", 'B', 20)
    pdf.set_xy(0, 15)
    pdf.cell(216, 10, txt="RECIBO DE EGRESO", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_xy(160, 12)
    pdf.cell(40, 12, txt=f"Nro: {nro_recibo}", border=1, ln=True, align='C')
    pdf.set_xy(10, 45)
    pdf.set_font("Arial", '', 12)
    pdf.cell(195, 10, txt=f"Fecha: {fecha}", ln=True, align='R')
    pdf.set_xy(15, 60)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(45, 10, txt="Beneficiario: ", ln=False)
    pdf.line(45, 68, 195, 68)
    pdf.ln(15)
    pdf.set_x(15)
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(185, 15, txt=f"Monto: {monto:,.2f} Bs", ln=True, align='C')
    pdf.ln(5)
    pdf.set_x(15)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(35, 8, txt="La cantidad de: ", ln=False)
    pdf.set_font("Arial", 'I', 11)
    monto_letras = numero_a_letras(monto).upper()
    monto_letras = monto_letras.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(150, 8, txt=monto_letras, align='L')
    pdf.line(50, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)
    pdf.set_x(15)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(25, 8, txt="Concepto: ", ln=False)
    pdf.set_font("Arial", 'I', 11)
    concepto_limpio = str(concepto)[:150].encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(160, 8, txt=concepto_limpio, align='L')
    pdf.line(40, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(15)
    pdf.set_x(15)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 8, txt="Forma de pago:  [  ] Efectivo     [  ] Banco", ln=False)
    pdf.cell(20, 8, txt="Firma: ", ln=False)
    pdf.line(145, pdf.get_y()+6, 195, pdf.get_y()+6)
    return pdf.output(dest="S").encode("latin-1")

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
    pdf.cell(22, 8, "Recibo", 1, 0, 'C')
    pdf.cell(22, 8, "Fecha", 1, 0, 'C')
    pdf.cell(50, 8, "Beneficiario", 1, 0, 'C')
    pdf.cell(28, 8, "Total Bs", 1, 0, 'C')
    pdf.cell(68, 8, "Nota", 1, 1, 'C')
    pdf.set_font("Arial", '', 8)
    for i, row in df.iterrows():
        rec_str = str(row.get('Nro_Recibo', 'N/A'))
        fecha_str = str(row.get('Fecha', ''))
        ben_str = str(row.get('Empleado_Beneficiario', ''))[:25].encode('latin-1', 'replace').decode('latin-1')
        obs_str = str(row.get('Observaciones', ''))[:40].encode('latin-1', 'replace').decode('latin-1')
        bs_str = f"{float(row.get('Total_Bs', 0)):.2f}"
        pdf.cell(22, 8, rec_str, 1, 0, 'C')
        pdf.cell(22, 8, fecha_str, 1, 0, 'C')
        pdf.cell(50, 8, ben_str, 1, 0, 'L')
        pdf.cell(28, 8, bs_str, 1, 0, 'R')
        pdf.cell(68, 8, obs_str, 1, 1, 'L')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, txt=f"TOTAL PAGADO: {total_bs:,.2f} Bs", ln=True, align='R')
    return pdf.output(dest="S").encode("latin-1")

def generar_pdf_caja(df, f_ini, f_fin, t_ing, t_egr, saldo_n):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, txt="Iglesia Cristiana Luz y Vida", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 8, txt="ESTADO DE CUENTA - LIBRO MAYOR", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 7, txt=f"Desde: {f_ini} hasta: {f_fin}", ln=True, align='C')
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(63, 8, f"INGRESOS: {t_ing:,.2f} Bs", 1, 0, 'C', True)
    pdf.cell(63, 8, f"EGRESOS: {t_egr:,.2f} Bs", 1, 0, 'C', True)
    pdf.cell(64, 8, f"SALDO NETO: {saldo_n:,.2f} Bs", 1, 1, 'C', True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(25, 8, "Fecha", 1, 0, 'C')
    pdf.cell(85, 8, "Descripción", 1, 0, 'C')
    pdf.cell(25, 8, "Entrada", 1, 0, 'C')
    pdf.cell(25, 8, "Salida", 1, 0, 'C')
    pdf.cell(30, 8, "Saldo Acum.", 1, 1, 'C')
    pdf.set_font("Arial", '', 8)
    for i, row in df.iterrows():
        desc = str(row['Descripción'])[:50].encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(25, 7, str(row['Fecha']), 1, 0, 'C')
        pdf.cell(85, 7, desc, 1, 0, 'L')
        pdf.cell(25, 7, f"{row['Entrada']:,.2f}", 1, 0, 'R')
        pdf.cell(25, 7, f"{row['Salida']:,.2f}", 1, 0, 'R')
        pdf.cell(30, 7, f"{row['Saldo']:,.2f}", 1, 1, 'R')
    return pdf.output(dest="S").encode("latin-1")

# --- EJECUCIÓN PRINCIPAL ---
if login():
    aplicar_estetica()
    conn = st.connection("my_database", type=GSheetsConnection)

    REDES = ["Red de Ruben", "Red de Simeon", "Red de Levi", "Red de Juda", "Red de Neftali", 
             "Red de Efrain", "Red de Gad", "Red de Aser", "Red de Isacar", "Red de Zabulom", 
             "Red de Jose", "Red de Benjamin", "Protemplo", "Suelto General", "Pastores", 
             "Red de Niños", "Primicias", "Pacto", "Venta de Divisas", "Escuela de Formacion", "Encuentro"]
    
    REDES_EXENTAS = ["Primicias", "Pacto", "Venta de Divisas", "Escuela de Formacion", "Encuentro"]
    METODOS = ["Bolivares en Efectivo", "USD en Efectivo", "Transferencia / PM", "Punto"]

    rol = st.session_state.usuario_actual
    
    if rol in ["admin", "tesoreria"]:
        titulos = ["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS FIJOS", "🛠️ OTROS EGRESOS", "📊 INFORMES", "🏧 CAJA", "💵 CAJA DIVISAS", "⚙️ CONFIG"]
        idx_inicio, idx_ingresos, idx_egresos, idx_otros, idx_informes, idx_caja, idx_divisas, idx_config = 0, 1, 2, 3, 4, 5, 6, 7
    else:
        titulos = ["🏠 INICIO", "📊 INFORMES", "🏧 CAJA", "💵 CAJA DIVISAS"]
        idx_inicio, idx_informes, idx_caja, idx_divisas = 0, 1, 2, 3
        
    tabs = st.tabs(titulos)

    # --- INICIO ---
    with tabs[idx_inicio]:
        st.markdown(f"<h4 style='text-align: right; color: #8D6E63;'>Bienvenido, {rol.capitalize()}</h4>", unsafe_allow_html=True)
        c_i1, c_i2, c_i3 = st.columns([1, 2, 1])
        with c_i2:
            try: st.image("logo.png", use_container_width=True)
            except: st.info("Iglesia Cristiana Luz y Vida")
            st.markdown("<h1 style='text-align: center;'>Iglesia Cristiana Luz y Vida</h1>", unsafe_allow_html=True)
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()

    # --- MÓDULOS DE CARGA Y EDICIÓN (SOLO ADMIN/TESORERÍA) ---
    if rol in ["admin", "tesoreria"]:
        
        # --- PESTAÑA INGRESOS ---
        with tabs[idx_ingresos]:
            st.subheader("📥 Cargar Nuevo Registro")
            if "key_ing" not in st.session_state: st.session_state.key_ing = 0
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    f_rec = st.date_input("Fecha Recaudación", date.today(), key="ing_fecha")
                    red_sel = st.selectbox("Red / Origen", REDES, key="ing_red")
                    tipo_sel = st.radio("Clasificación", ["Ofrenda", "Diezmo"], key="ing_tipo", horizontal=True)
                with col2:
                    met_sel = st.selectbox("Método de Pago", METODOS, key="ing_metodo")
                    monto_in = st.number_input("Monto Recibido", min_value=0.0, step=0.01, key=f"ing_monto_{st.session_state.key_ing}")
                    tasa_v = 1.0; ref_v = ""; banco_v = ""
                    if met_sel == "USD en Efectivo":
                        tasa_v = st.number_input("Tasa BCV", min_value=1.0, value=36.0, key="ing_tasa")
                        f_op_v = str(f_rec)
                    elif met_sel in ["Transferencia / PM", "Punto"]:
                        banco_v = st.text_input("Banco", key=f"ing_banco_{st.session_state.key_ing}") if met_sel == "Transferencia / PM" else "Punto"
                        ref_v = st.text_input("Referencia (4 dígitos)", max_chars=4, key=f"ing_ref_{st.session_state.key_ing}")
                        f_op_v = str(st.date_input("Fecha Operación", date.today(), key="ing_f_op"))
                    else: f_op_v = str(f_rec)
                with col3:
                    total_bs = monto_in * tasa_v if met_sel == "USD en Efectivo" else monto_in
                    diezmo_calculado = 0.0 if red_sel in REDES_EXENTAS else float(total_bs * 0.10)
                    st.metric("Total en Bolívares", f"{total_bs:,.2f} Bs")
                    st.metric("10% Correspondiente", f"{diezmo_calculado:,.2f} Bs")
                    
                    if st.button("💾 GUARDAR REGISTRO", use_container_width=True):
                        try:
                            df_actual = conn.read(worksheet="INGRESOS", ttl="10m")
                            nuevo = pd.DataFrame([{
                                "Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel,
                                "Metodo": met_sel, "Banco": banco_v, "Referencia": str(ref_v),
                                "Fecha_Op": str(f_op_v), "Monto_Orig": float(monto_in),
                                "Tasa": float(tasa_v), "Total_Bs": float(total_bs),
                                "Diezmo_10": diezmo_calculado
                            }])
                            df_update = pd.concat([df_actual, nuevo], ignore_index=True) if df_actual is not None else nuevo
                            conn.update(worksheet="INGRESOS", data=df_update)
                            st.cache_data.clear()
                            st.session_state.key_ing += 1
                            st.success("¡Guardado!")
                            st.rerun()
                        except Exception as e: st.error(f"Error: {e}")

            # Módulo de Edición de Ingresos
            st.markdown("---")
            with st.expander("✏️ Editar o Borrar Registros de Ingresos", expanded=False):
                try:
                    df_edit_i = conn.read(worksheet="INGRESOS", ttl="10m")
                    if not df_edit_i.empty:
                        df_edited_i = st.data_editor(df_edit_i, num_rows="dynamic", key="edit_ing_table")
                        if st.button("💾 Guardar Cambios en Ingresos", key="btn_ed_ing"):
                            conn.update(worksheet="INGRESOS", data=df_edited_i)
                            st.cache_data.clear()
                            st.success("Cambios guardados correctamente.")
                            st.rerun()
                    else:
                        st.info("No hay datos para editar.")
                except Exception as e: st.warning("Aún no hay registros de ingresos creados.")

        # --- PESTAÑA EGRESOS FIJOS ---
        with tabs[idx_egresos]:
            st.header("📤 Registro de Egresos Fijos")
            if "pdf_eg" in st.session_state:
                st.success(f"✅ Recibo Nro: {st.session_state.nro_eg}")
                st.download_button("🖨️ DESCARGAR PDF", data=st.session_state.pdf_eg, file_name=f"Recibo_{st.session_state.nro_eg}.pdf", key=f"dl_eg_{st.session_state.nro_eg}")
            try:
                df_emp = conn.read(worksheet="EMPLEADOS", ttl="10m")
                lista_empleados = (df_emp['Nombre'] + " " + df_emp['Apellido']).tolist() if df_emp is not None else ["Sin personal"]
            except: lista_empleados = ["Cree la pestaña EMPLEADOS"]
            with st.container(border=True):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    nom_e = st.selectbox("Empleado", lista_empleados, key="eg_nom")
                    monto_usd_e = st.number_input("Monto USD", min_value=0.0, key=f"eg_monto_{st.session_state.key_ing}")
                with col_e2:
                    tasa_e = st.number_input("Tasa", value=36.0, key="eg_tasa")
                    total_p = monto_usd_e * tasa_e
                    st.metric("Total Bs", f"{total_p:,.2f}")
                if st.button("💸 REGISTRAR PAGO"):
                    nro = obtener_proximo_recibo(conn)
                    nuevo_eg = pd.DataFrame([{"Nro_Recibo": nro, "Fecha": str(date.today()), "Empleado_Beneficiario": nom_e, "Total_Bs": total_p, "Observaciones": "Pago Nómina"}])
                    df_eg_act = conn.read(worksheet="EGRESOS", ttl="10m")
                    conn.update(worksheet="EGRESOS", data=pd.concat([df_eg_act, nuevo_eg]))
                    st.session_state.pdf_eg = generar_recibo_pdf(nro, total_p, str(date.today()), f"Nomina: {nom_e}")
                    st.session_state.nro_eg = nro
                    st.cache_data.clear()
                    st.rerun()

            # Módulo de Edición de Egresos
            st.markdown("---")
            with st.expander("✏️ Editar o Borrar Egresos Fijos", expanded=False):
                try:
                    df_edit_ef = conn.read(worksheet="EGRESOS", ttl="10m")
                    if not df_edit_ef.empty:
                        df_edited_ef = st.data_editor(df_edit_ef, num_rows="dynamic", key="edit_eg_table")
                        if st.button("💾 Guardar Cambios en Egresos", key="btn_ed_eg"):
                            conn.update(worksheet="EGRESOS", data=df_edited_ef)
                            st.cache_data.clear()
                            st.success("Cambios guardados correctamente.")
                            st.rerun()
                    else:
                        st.info("No hay datos para editar.")
                except Exception as e: st.warning("Aún no hay registros creados.")

        # --- PESTAÑA OTROS EGRESOS ---
        with tabs[idx_otros]:
            st.header("🛠️ Otros Egresos")
            try:
                df_cat = conn.read(worksheet="CAT_GASTOS", ttl="10m")
                lista_gastos = df_cat["Tipo_Gasto"].tolist() if df_cat is not None else ["General"]
            except: lista_gastos = ["General"]
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    desc_oe = st.selectbox("Tipo de Gasto", lista_gastos)
                    fecha_oe = st.date_input("Fecha", date.today(), key="oe_f")
                with col2:
                    monto_oe = st.number_input("Monto Bs", min_value=0.0, key="oe_m")
                    obs_oe = st.text_area("Observaciones", key="oe_o")
                if st.button("🔧 REGISTRAR GASTO"):
                    nro_oe = obtener_proximo_recibo(conn)
                    nuevo_oe = pd.DataFrame([{"Nro_Recibo": nro_oe, "Descripcion": desc_oe, "Fecha": str(fecha_oe), "Monto": monto_oe, "Observaciones": obs_oe}])
                    df_oe_act = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
                    conn.update(worksheet="OTROS_EGRESOS", data=pd.concat([df_oe_act, nuevo_oe]))
                    st.success("Gasto registrado")
                    st.cache_data.clear()
                    st.rerun()

            # Módulo de Edición de Otros Egresos
            st.markdown("---")
            with st.expander("✏️ Editar o Borrar Otros Egresos", expanded=False):
                try:
                    df_edit_oe = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
                    if not df_edit_oe.empty:
                        df_edited_oe = st.data_editor(df_edit_oe, num_rows="dynamic", key="edit_oe_table")
                        if st.button("💾 Guardar Cambios en Otros Egresos", key="btn_ed_oe"):
                            conn.update(worksheet="OTROS_EGRESOS", data=df_edited_oe)
                            st.cache_data.clear()
                            st.success("Cambios guardados correctamente.")
                            st.rerun()
                    else:
                        st.info("No hay datos para editar.")
                except Exception as e: st.warning("Aún no hay registros creados.")

    # --- INFORMES (TODOS LOS ROLES) ---
    with tabs[idx_informes]:
        st.header("📊 Reportes")
        f_ini = st.date_input("Desde", date.today().replace(day=1), key="inf_desde")
        f_fin = st.date_input("Hasta", date.today(), key="inf_hasta")
        try:
            df_f = conn.read(worksheet="EGRESOS", ttl="10m")
            df_o = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
            df_f['Fecha'] = pd.to_datetime(df_f['Fecha']).dt.date
            df_o['Fecha'] = pd.to_datetime(df_o['Fecha']).dt.date
            tf = df_f[(df_f['Fecha'] >= f_ini) & (df_f['Fecha'] <= f_fin)]['Total_Bs'].sum()
            to = df_o[(df_o['Fecha'] >= f_ini) & (df_o['Fecha'] <= f_fin)]['Monto'].sum()
            if (tf+to) > 0:
                fig_e = px.pie(values=[tf, to], names=["Fijos (Nómina)", "Otros (Gastos)"], hole=0.4, title="Comparativa de Egresos")
                st.plotly_chart(fig_e)
        except: st.info("No hay datos para graficar.")

    # --- CAJA EN BOLÍVARES (TODOS LOS ROLES) ---
    with tabs[idx_caja]:
        st.header("🏧 Estado de Caja (Bs)")
        try:
            df_i = conn.read(worksheet="INGRESOS", ttl="10m")
            df_ef = conn.read(worksheet="EGRESOS", ttl="10m")
            df_eo = conn.read(worksheet="OTROS_EGRESOS", ttl="10m")
            
            df_i_std = df_i[['Fecha', 'Red', 'Total_Bs']].rename(columns={'Red':'Descripción', 'Total_Bs':'Entrada'})
            df_i_std['Salida'] = 0.0
            df_ef_std = df_ef[['Fecha', 'Empleado_Beneficiario', 'Total_Bs']].rename(columns={'Empleado_Beneficiario':'Descripción', 'Total_Bs':'Salida'})
            df_ef_std['Entrada'] = 0.0
            df_eo_std = df_eo[['Fecha', 'Descripcion', 'Monto']].rename(columns={'Descripcion':'Descripción', 'Monto':'Salida'})
            df_eo_std['Entrada'] = 0.0
            
            libro = pd.concat([df_i_std, df_ef_std, df_eo_std]).sort_values('Fecha')
            libro['Fecha'] = pd.to_datetime(libro['Fecha']).dt.date
            libro['Saldo'] = libro['Entrada'].cumsum() - libro['Salida'].cumsum()
            
            col_c1, col_c2 = st.columns(2)
            fd = col_c1.date_input("Desde", date.today().replace(day=1), key="caja_fd")
            fh = col_c2.date_input("Hasta", date.today(), key="caja_fh")
            df_caja_f = libro[(libro['Fecha'] >= fd) & (libro['Fecha'] <= fh)]
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Ingresos", f"{df_caja_f['Entrada'].sum():,.2f}")
            m2.metric("Egresos", f"{df_caja_f['Salida'].sum():,.2f}")
            m3.metric("Saldo Final", f"{libro['Saldo'].iloc[-1] if not libro.empty else 0:,.2f}")
            
            st.dataframe(df_caja_f, use_container_width=True)
            if st.button("📄 GENERAR PDF DE CAJA"):
                pdf_c = generar_pdf_caja(df_caja_f, fd, fh, df_caja_f['Entrada'].sum(), df_caja_f['Salida'].sum(), libro['Saldo'].iloc[-1])
                st.download_button("🖨️ Descargar Reporte de Caja", data=pdf_c, file_name="Caja.pdf")
        except Exception as e: st.error(f"Error en Caja: {e}")

    # --- CAJA DIVISAS ---
    with tabs[idx_divisas]:
        st.header("💵 Control de Caja en Divisas")
        st.write("Vista de saldos y movimientos en moneda extranjera.")
        
        try:
            df_div = conn.read(worksheet="CAJA_DIVISAS", ttl="10m")
            if df_div is None or df_div.empty:
                df_div = pd.DataFrame(columns=["Fecha", "Moneda", "Descripcion", "Ingreso", "Egreso"])
        except:
            df_div = pd.DataFrame(columns=["Fecha", "Moneda", "Descripcion", "Ingreso", "Egreso"])

        monedas = ["Efectivo USD", "USDT", "Zelle"]
        tabs_divisas = st.tabs(["💵 Efectivo USD", "🪙 USDT", "🏦 Zelle"])
        
        for i, moneda in enumerate(monedas):
            with tabs_divisas[i]:
                st.subheader(f"Movimientos - {moneda}")
                
                df_m = df_div[df_div["Moneda"] == moneda].copy() if not df_div.empty else pd.DataFrame(columns=["Fecha", "Moneda", "Descripcion", "Ingreso", "Egreso"])
                df_m['Ingreso'] = pd.to_numeric(df_m['Ingreso'], errors='coerce').fillna(0)
                df_m['Egreso'] = pd.to_numeric(df_m['Egreso'], errors='coerce').fillna(0)
                saldo_actual = df_m['Ingreso'].sum() - df_m['Egreso'].sum()
                
                st.metric(f"SALDO NETO ({moneda})", f"{saldo_actual:,.2f}")
                
                if rol in ["admin", "tesoreria"]:
                    with st.expander(f"➕ Registrar nuevo movimiento en {moneda}", expanded=False):
                        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                        with c1:
                            f_div = st.date_input("Fecha", date.today(), key=f"f_div_{i}")
                        with c2:
                            desc_div = st.text_input("Descripción", placeholder="Motivo de la operación...", key=f"desc_div_{i}")
                        with c3:
                            tipo_div = st.selectbox("Tipo de Operación", ["Ingreso", "Egreso"], key=f"tipo_div_{i}")
                        with c4:
                            monto_div = st.number_input("Monto", min_value=0.01, step=0.01, key=f"monto_div_{i}")
                            
                        if st.button(f"💾 Guardar Movimiento en {moneda}", type="primary", key=f"btn_div_{i}"):
                            if desc_div:
                                ingreso_val = monto_div if tipo_div == "Ingreso" else 0.0
                                egreso_val = monto_div if tipo_div == "Egreso" else 0.0
                                nuevo_div = pd.DataFrame([{
                                    "Fecha": str(f_div), "Moneda": moneda, "Descripcion": desc_div,
                                    "Ingreso": float(ingreso_val), "Egreso": float(egreso_val)
                                }])
                                df_div_update = pd.concat([df_div, nuevo_div], ignore_index=True)
                                try:
                                    conn.update(worksheet="CAJA_DIVISAS", data=df_div_update)
                                    st.cache_data.clear()
                                    st.success(f"¡Movimiento de {moneda} registrado!")
                                    st.rerun()
                                except Exception as e: 
                                    # MOSTRAR EL ERROR REAL AQUÍ
                                    st.error(f"Error técnico al guardar: {e}")
                            else:
                                st.error("Por favor, ingresa una descripción.")
                
                if not df_m.empty:
                    df_m_show = df_m[['Fecha', 'Descripcion', 'Ingreso', 'Egreso']].copy()
                    df_m_show['Saldo_Acumulado'] = df_m_show['Ingreso'].cumsum() - df_m_show['Egreso'].cumsum()
                    st.dataframe(df_m_show, use_container_width=True)
                else:
                    st.info(f"No hay movimientos registrados en {moneda}.")

        # Módulo de Edición General de Divisas (Solo Admin/Tesorería)
        if rol in ["admin", "tesoreria"]:
            st.markdown("---")
            with st.expander("✏️ Editar o Borrar Cualquier Registro de Divisas", expanded=False):
                if not df_div.empty:
                    df_edited_div = st.data_editor(df_div, num_rows="dynamic", key="edit_div_table", use_container_width=True)
                    if st.button("💾 Guardar Cambios en Divisas", key="btn_ed_div"):
                        conn.update(worksheet="CAJA_DIVISAS", data=df_edited_div)
                        st.cache_data.clear()
                        st.success("Cambios guardados correctamente.")
                        st.rerun()
                else:
                    st.info("No hay datos de divisas para editar aún.")

    # --- CONFIGURACIÓN (SOLO ADMIN/TESORERÍA) ---
    if rol in ["admin", "tesoreria"]:
        with tabs[idx_config]:
            st.header("⚙️ Configuración")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Personal")
                try:
                    df_p = conn.read(worksheet="EMPLEADOS", ttl="10m")
                    df_pe = st.data_editor(df_p, num_rows="dynamic", key="ed_pers")
                    if st.button("Guardar Personal"):
                        conn.update(worksheet="EMPLEADOS", data=df_pe.fillna(""))
                        st.cache_data.clear()
                        st.success("Guardado")
                        st.rerun()
                except Exception as e:
                    st.error("Error al leer 'EMPLEADOS'. Verifica tu conexión.")

            with c2:
                st.subheader("Catálogo de Gastos")
                try: 
                    df_g = conn.read(worksheet="CAT_GASTOS", ttl="10m")
                    if df_g is None or df_g.empty:
                        df_g = pd.DataFrame(columns=["Tipo_Gasto"])
                    df_g["Tipo_Gasto"] = df_g["Tipo_Gasto"].astype(str).replace("nan", "")
                except: 
                    df_g = pd.DataFrame(columns=["Tipo_Gasto"])
                
                df_ge = st.data_editor(df_g, num_rows="dynamic", key="ed_gast", use_container_width=True)
                
                if st.button("Guardar Catálogo"):
                    df_guardar = df_ge[df_ge["Tipo_Gasto"].astype(str).str.strip() != ""]
                    conn.update(worksheet="CAT_GASTOS", data=df_guardar)
                    st.cache_data.clear()
                    st.success("¡Catálogo actualizado!")
                    st.rerun()
