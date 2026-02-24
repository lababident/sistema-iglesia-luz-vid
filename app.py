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

# --- FUNCIONES ESTÉTICAS, NÚMEROS A LETRAS Y PDF ---
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
            df = conn.read(worksheet=hoja, ttl="0m")
            if df is not None and not df.empty and "Nro_Recibo" in df.columns:
                max_val = pd.to_numeric(df["Nro_Recibo"], errors='coerce').max()
                if pd.notna(max_val) and max_val > max_rec:
                    max_rec = max_val
        except: pass
    return int(max_rec + 1)

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
    pdf.cell(20, 8, "Recibo", 1, 0, 'C')
    pdf.cell(22, 8, "Fecha", 1, 0, 'C')
    pdf.cell(50, 8, "Descripción", 1, 0, 'C')
    pdf.cell(30, 8, "Monto Bs", 1, 0, 'C')
    pdf.cell(68, 8, "Observaciones", 1, 1, 'C')
    pdf.set_font("Arial", '', 8)
    for i, row in df.iterrows():
        rec_str = str(row.get('Nro_Recibo', 'N/A'))
        fecha_str = str(row.get('Fecha', ''))
        desc_str = str(row.get('Descripcion', ''))[:25].encode('latin-1', 'replace').decode('latin-1')
        obs_str = str(row.get('Observaciones', ''))[:40].encode('latin-1', 'replace').decode('latin-1')
        try: monto_str = f"{float(row.get('Monto', 0)):,.2f}"
        except: monto_str = str(row.get('Monto', '0'))
        pdf.cell(20, 8, rec_str, 1, 0, 'C')
        pdf.cell(22, 8, fecha_str, 1, 0, 'C')
        pdf.cell(50, 8, desc_str, 1, 0, 'L')
        pdf.cell(30, 8, monto_str, 1, 0, 'R')
        pdf.cell(68, 8, obs_str, 1, 1, 'L')
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
        red_str = str(row.get('Red', '')).encode('latin-1', 'replace').decode('latin-1')
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

    # ACTUALIZACIÓN DE REDES (PASO 1)
    REDES = ["Red de Ruben", "Red de Simeon", "Red de Levi", "Red de Juda", "Red de Neftali", 
             "Red de Efrain", "Red de Gad", "Red de Aser", "Red de Isacar", "Red de Zabulom", 
             "Red de Jose", "Red de Benjamin", "Protemplo", "Suelto General", "Pastores", 
             "Red de Niños", "Primicias", "Pacto"]
    
    # REDES QUE NO PAGAN DIEZMO
    REDES_EXENTAS = ["Primicias", "Pacto"]
    
    METODOS = ["Bolivares en Efectivo", "USD en Efectivo", "Transferencia / PM", "Punto"]

    rol = st.session_state.usuario_actual
    titulos = ["🏠 INICIO", "📥 INGRESOS", "📤 EGRESOS FIJOS", "🛠️ OTROS EGRESOS", "📊 INFORMES", "👥 CONFIG"] if rol in ["admin", "tesoreria"] else ["🏠 INICIO", "📊 INFORMES"]
    tabs = st.tabs(titulos)

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
        # --- PESTAÑA INGRESOS (Lógica de Diezmo condicional) ---
        with tabs[1]:
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
                    # Cálculo de diezmo condicional (PASO 4)
                    diezmo_calculado = 0.0 if red_sel in REDES_EXENTAS else float(total_bs * 0.10)
                    st.metric("Total en Bolívares", f"{total_bs:,.2f} Bs")
                    st.metric("10% Correspondiente", f"{diezmo_calculado:,.2f} Bs")
                    
                    if st.button("💾 GUARDAR REGISTRO", use_container_width=True):
                        try:
                            df_actual = conn.read(worksheet="INGRESOS", ttl="10m")
                            ref_str = str(ref_v).strip()
                            f_op_str = str(f_op_v).strip()
                            es_duplicado = False
                            if df_actual is not None and not df_actual.empty and met_sel in ["Transferencia / PM", "Punto"] and ref_str != "":
                                duplicados = df_actual[(df_actual['Metodo'] == met_sel) & (df_actual['Referencia'].astype(str) == ref_str) & (df_actual['Fecha_Op'].astype(str) == f_op_str)]
                                if not duplicados.empty: es_duplicado = True
                            if es_duplicado: st.error("⚠️ ¡ALERTA! Registro duplicado detectado.")
                            elif monto_in <= 0: st.error("⚠️ Monto inválido.")
                            else:
                                nuevo = pd.DataFrame([{
                                    "Fecha": str(f_rec), "Red": red_sel, "Clasificacion": tipo_sel,
                                    "Metodo": met_sel, "Banco": banco_v, "Referencia": ref_str,
                                    "Fecha_Op": f_op_str, "Monto_Orig": float(monto_in),
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

        # --- PESTAÑA EGRESOS FIJOS ---
        with tabs[2]:
            st.header("📤 Registro de Egresos Fijos")
            if "pdf_eg" in st.session_state:
                st.success(f"✅ Recibo Nro: {st.session_state.nro_eg}")
                st.download_button("🖨️ DESCARGAR PDF", data=st.session_state.pdf_eg, file_name=f"Recibo_{st.session_state.nro_eg}.pdf", key=f"dl_eg_{st.session_state.nro_eg}")
            
            try:
                df_emp = conn.read(worksheet="EMPLEADOS", ttl="5m")
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
                    df_eg_act = conn.read(worksheet="EGRESOS")
                    conn.update(worksheet="EGRESOS", data=pd.concat([df_eg_act, nuevo_eg]))
                    st.session_state.pdf_eg = generar_recibo_pdf(nro, total_p, str(date.today()), f"Nomina: {nom_e}")
                    st.session_state.nro_eg = nro
                    st.cache_data.clear()
                    st.rerun()

        # --- PESTAÑA OTROS EGRESOS (Con Desplegable de Gastos) ---
        with tabs[3]:
            st.header("🛠️ Otros Egresos")
            try:
                df_cat = conn.read(worksheet="CAT_GASTOS", ttl="5m")
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
                    df_oe_act = conn.read(worksheet="OTROS_EGRESOS")
                    conn.update(worksheet="OTROS_EGRESOS", data=pd.concat([df_oe_act, nuevo_oe]))
                    st.success("Gasto registrado")
                    st.cache_data.clear()
                    st.rerun()

    # --- PESTAÑA INFORMES (Con Gráfico de Egresos) ---
    idx_inf = 4 if rol in ["admin", "tesoreria"] else 1
    with tabs[idx_inf]:
        st.header("📊 Reportes")
        f_ini = st.date_input("Desde", date.today().replace(day=1))
        f_fin = st.date_input("Hasta", date.today())
        
        # Gráfico de Egresos (PASO 3)
        st.subheader("📉 Distribución de Gastos (Fijos vs Operativos)")
        try:
            df_f = conn.read(worksheet="EGRESOS")
            df_o = conn.read(worksheet="OTROS_EGRESOS")
            df_f['Fecha'] = pd.to_datetime(df_f['Fecha']).dt.date
            df_o['Fecha'] = pd.to_datetime(df_o['Fecha']).dt.date
            tf = df_f[(df_f['Fecha'] >= f_ini) & (df_f['Fecha'] <= f_fin)]['Total_Bs'].sum()
            to = df_o[(df_o['Fecha'] >= f_ini) & (df_o['Fecha'] <= f_fin)]['Monto'].sum()
            if (tf+to) > 0:
                fig_e = px.pie(values=[tf, to], names=["Fijos (Nómina)", "Otros (Gastos)"], hole=0.4, title="Comparativa de Egresos")
                st.plotly_chart(fig_e)
        except: st.info("No hay datos de egresos para el gráfico.")

    # --- PESTAÑA CONFIG (Personal + Catálogo de Gastos) (PASO 2) ---
    if rol in ["admin", "tesoreria"]:
        with tabs[5]:
            st.header("⚙️ Configuración del Sistema")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("👥 Personal")
                df_pers = conn.read(worksheet="EMPLEADOS")
                df_p_edit = st.data_editor(df_pers, num_rows="dynamic", key="ed_p")
                if st.button("💾 Guardar Personal"):
                    conn.update(worksheet="EMPLEADOS", data=df_p_edit.fillna(""))
                    st.success("Actualizado")
            with c2:
                st.subheader("🛠️ Catálogo de Gastos")
                try: df_gastos = conn.read(worksheet="CAT_GASTOS")
                except: df_gastos = pd.DataFrame(columns=["Tipo_Gasto"])
                df_g_edit = st.data_editor(df_gastos, num_rows="dynamic", key="ed_g")
                if st.button("💾 Guardar Catálogo"):
                    conn.update(worksheet="CAT_GASTOS", data=df_g_edit.fillna(""))
                    st.success("Actualizado")
