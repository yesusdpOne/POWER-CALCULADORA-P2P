import streamlit as st
import requests
import threading
import time

st.set_page_config(
    page_title="Panel P2P Multi-Bot",
    page_icon="🚀",
    layout="wide"
)

# Constantes globales
FEE_MAKER = 0.0025
IMPUESTO_4X1000 = 0.004
URL_P2P = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
CHAT_ID_DEFAULT = "1116350726"

def enviar_telegram(token, chat_id, msg):
    if not token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=8)
    except Exception as e:
        print(f"Error Telegram: {e}")

def obtener_precio_binance(fiat, trade_type, pay_types, amount):
    """Consulta la API P2P de Binance y obtiene el mejor precio válido filtrando comercios seguros."""
    payload = {
        "asset": "USDT", "fiat": fiat, "merchantCheck": False, "publisherType": None,
        "payLimitTime": None, "countries": [], "page": 1, "rows": 20,
        "tradeType": trade_type, "payTypes": pay_types, "transAmount": str(amount)
    }
    headers = {"Accept": "*/*", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        res = requests.post(URL_P2P, json=payload, headers=headers, timeout=10).json()
        if res.get("code") == "000000" and res.get("data"):
            for item in res["data"]:
                adv, adv_user = item["adv"], item["advertiser"]
                if item.get("isPromoted") or adv.get("isPromoted") or adv.get("classify") == "promoted":
                    continue
                rate = float(adv_user.get("monthFinishRate", 0))
                rate_pct = rate * 100 if rate <= 1.0 else rate
                if rate_pct < 90.0:
                    continue
                return float(adv["price"]), adv_user.get("nickName", "Comerciante")
    except Exception as e:
        print(f"Error P2P: {e}")
    return None, None

st.title("🚀 Panel de Control P2P & Multi-Bots de Telegram")
st.markdown("Monitoreo continuo con alertas automáticas enviadas a Telegram **cada 1 minuto**.")

tab1, tab2, tab3 = st.tabs([
    "📈 Oportunidades P2P (COP & PEN)",
    "📡 Radar P2P Ventas",
    "🔄 Triangulación Dinámica (COP➔PEN➔COP)"
])

# Inicializar estados en sesión
if 't1_running' not in st.session_state: st.session_state.t1_running = False
if 't2_running' not in st.session_state: st.session_state.t2_running = False
if 't3_running' not in st.session_state: st.session_state.t3_running = False

# --- HILO BUCLE PESTAÑA 1 ---
def loop_oportunidades(cap_cop, cap_pen, aplica_4k, margen_obj, token, chat_id):
    enviar_telegram(token, chat_id, f"🚀 <b>¡MÓDULO OPORTUNIDADES ACTIVADO!</b> (Monitoreo cada 1 min)\n• Margen Obj: {margen_obj}%")
    while st.session_state.t1_running:
        try:
            hora = time.strftime("%H:%M:%S")
            p_c_cop, n_c_cop = obtener_precio_binance('COP', "SELL", ['BreB', 'Nequi', 'BANK'], "33600")
            p_v_cop, n_v_cop = obtener_precio_binance('COP', "BUY", ['BreB', 'Nequi', 'BANK'], "33600")
            p_c_pen, n_c_pen = obtener_precio_binance('PEN', "SELL", ['YAPE', 'PLIN'], "30")
            p_v_pen, n_v_pen = obtener_precio_binance('PEN', "BUY", ['YAPE', 'PLIN'], "30")

            if p_c_cop and p_v_cop:
                usdt_cop = (cap_cop / p_c_cop) * (1 - FEE_MAKER)
                bruto_cop = usdt_cop * p_v_cop * (1 - FEE_MAKER)
                c_4x1000 = (cap_cop * IMPUESTO_4X1000) if aplica_4k else 0.0
                ganancia_cop = bruto_cop - cap_cop - c_4x1000
                margen_cop = (ganancia_cop / cap_cop) * 100
                if margen_cop >= margen_obj:
                    enviar_telegram(token, chat_id, f"🚀 <b>[OPORTUNIDAD COP]</b> [{hora}]\n• Ganancia: +${ganancia_cop:,.2f} COP ({margen_cop:.2f}%)\n• Compra: ${p_c_cop:,.2f} \vert{} Venta:${p_v_cop:,.2f}")

            if p_c_pen and p_v_pen:
                usdt_pen = (cap_pen / p_c_pen) * (1 - FEE_MAKER)
                bruto_pen = usdt_pen * p_v_pen * (1 - FEE_MAKER)
                ganancia_pen = bruto_pen - cap_pen
                margen_pen = (ganancia_pen / cap_pen) * 100
                if margen_pen >= margen_obj:
                    enviar_telegram(token, chat_id, f"🚀 <b>[OPORTUNIDAD PEN]</b> [{hora}]\n• Ganancia: +S/{ganancia_pen:,.3f} ({margen_pen:.2f}%)\n• Compra: S/{p_c_pen:.3f} | Venta: S/{p_v_pen:.3f}")
        except Exception as e:
            print(f"Error T1: {e}")
        time.sleep(60)

# --- HILO BUCLE PESTAÑA 2 ---
def loop_radar_ventas(fiat, precio_compra, cant_usdt, aplica_4k, margen_pct, token, chat_id):
    factor_maker = 1.0 - FEE_MAKER
    factor_4x1000 = (1.0 - IMPUESTO_4X1000) if (aplica_4k and fiat == 'COP') else 1.0
    precio_meta = (precio_compra * (1.0 + (margen_pct / 100.0))) / (factor_maker * factor_4x1000)
    decimals_fmt = ",.3f" if fiat == 'PEN' else ",.2f"
    curr_sym = "S/" if fiat == 'PEN' else "$"

    enviar_telegram(token, chat_id, f"🔴 <b>Radar Ventas Activado</b> (Monitoreo cada 1 min)\n• Meta: {curr_sym}{precio_meta:{decimals_fmt}} {fiat}")
    param_amount = '33600' if fiat == 'COP' else '30'
    pay_types_list = ['BreB', 'Nequi', 'BANK'] if fiat == 'COP' else ['YAPE', 'PLIN']

    while st.session_state.t2_running:
        try:
            hora = time.strftime("%H:%M:%S")
            p_actual, nick_actual = obtener_precio_binance(fiat, "BUY", pay_types_list, param_amount)
            if p_actual:
                if p_actual >= precio_meta:
                    ganancia = (cant_usdt * precio_compra) * (margen_pct / 100.0)
                    enviar_telegram(token, chat_id, f"🚨 <b>¡ALERTA DE VENTA ALCANZADA!</b> 🚨 [{hora}]\n• Mercado: {curr_sym}{p_actual:{decimals_fmt}} ({nick_actual})\n• Meta: {curr_sym}{precio_meta:{decimals_fmt}}\n• Ganancia Est: +{curr_sym}{ganancia:{decimals_fmt}}")
        except Exception as e:
            print(f"Error T2: {e}")
        time.sleep(60)

# --- HILO BUCLE PESTAÑA 3 ---
def loop_triangulacion(cap_pcompra, usdt_inicial, aplica_4k, margen_pct, token, chat_id):
    enviar_telegram(token, chat_id, f"🚀 <b>Radar Triangulación Activado</b> (Monitoreo cada 1 min)\n• Margen Obj: {margen_pct}%")
    while st.session_state.t3_running:
        try:
            hora = time.strftime("%H:%M:%S")
            p_pen_venta, user_pen_v = obtener_precio_binance("PEN", "BUY", ["YAPE", "PLIN"], "30")
            p_pen_compra, user_pen_c = obtener_precio_binance("PEN", "SELL", ["YAPE", "PLIN"], "30")
            p_cop_venta, user_cop_v = obtener_precio_binance("COP", "BUY", ["BreB", "Nequi", "BANK"], "33600")

            if p_pen_venta and p_pen_compra and p_cop_venta:
                tax_4x1000 = IMPUESTO_4X1000 if aplica_4k else 0.0
                pen_recibidos = usdt_inicial * p_pen_venta * (1.0 - FEE_MAKER)
                usdt_recomprados = (pen_recibidos / p_pen_compra) * (1.0 - FEE_MAKER)
                cop_brutos = usdt_recomprados * p_cop_venta * (1.0 - FEE_MAKER)
                cop_netos = cop_brutos * (1.0 - tax_4x1000)

                cop_inversion = usdt_inicial * cap_pcompra
                ganancia_cop = cop_netos - cop_inversion
                margen_real_pct = (ganancia_cop / cop_inversion) * 100.0

                if margen_real_pct >= margen_pct:
                    enviar_telegram(token, chat_id, f"🚨 <b>¡OPORTUNIDAD DE TRIANGULACIÓN DETECTADA!</b> [{hora}]\n• Margen: +{margen_real_pct:.2f}%\n• Ganancia: +${ganancia_cop:,.2f} COP")
        except Exception as e:
            print(f"Error T3: {e}")
        time.sleep(60)


# --- PESTAÑA 1: OPORTUNIDADES P2P ---
with tab1:
    st.header("Oportunidades P2P (Compra / Venta Simultánea)")
    st.markdown("Bot Token por defecto: `8879706084:AAGVdtn5wvpYNyRKOvYjaus97XSLet9H_FY`")
    
    col1, col2 = st.columns(2)
    with col1:
        cap_cop = st.number_input("Capital COP", value=500000.0, step=50000.0, key="t1_cop")
        aplica_4x1000 = st.checkbox("Descontar 4x1000 (COP)", value=True, key="t1_4x1000")
    with col2:
        cap_pen = st.number_input("Capital PEN", value=1000.0, step=100.0, key="t1_pen")
        margen_obj_t1 = st.selectbox("Margen Objetivo (%)", [0.4, 0.5, 0.8, 1.0], index=1, key="t1_margen")

    token_t1 = st.text_input("Token Bot Telegram", value="8879706084:AAGVdtn5wvpYNyRKOvYjaus97XSLet9H_FY", key="t1_token")
    chat_id_t1 = st.text_input("Chat ID Telegram", value=CHAT_ID_DEFAULT, key="t1_chat")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 INICIAR MONITOREO AUTOMÁTICO", key="btn_t1_start"):
            if not st.session_state.t1_running:
                st.session_state.t1_running = True
                threading.Thread(target=loop_oportunidades, args=(cap_cop, cap_pen, aplica_4x1000, margen_obj_t1, token_t1, chat_id_t1), daemon=True).start()
                st.success("Monitoreo automático iniciado (envía alerta a Telegram cada 1 min si hay oportunidad).")
    with c2:
        if st.button("⏹ DETENER MONITOREO", key="btn_t1_stop"):
            st.session_state.t1_running = False
            st.warning("Monitoreo detenido.")

# --- PESTAÑA 2: RADAR P2P VENTAS ---
with tab2:
    st.header("Radar P2P Ventas (Precio Meta)")
    st.markdown("Bot Token por defecto: `8673349898:AAEeBsWnJA4YRgNtEyoJ4fVcPifKSR1pqjg`")

    fiat_t2 = st.selectbox("Moneda", ["COP", "PEN"], key="t2_fiat")
    if fiat_t2 == "PEN":
        precio_compra_t2 = st.number_input("Precio de Compra USDT", value=3.750, step=0.001, format="%.3f", key="t2_pcompra")
    else:
        precio_compra_t2 = st.number_input("Precio de Compra USDT", value=3900.0, step=10.0, format="%.2f", key="t2_pcompra")

    cant_usdt_t2 = st.number_input("Cantidad de USDT a vender", value=100.0, step=10.0, key="t2_cant")
    aplica_4x1000_t2 = st.checkbox("Descontar 4x1000 (COP)", value=True, key="t2_4x1000")
    margen_obj_t2 = st.selectbox("Margen Objetivo (%)", [0.4, 0.5, 0.6, 0.8, 1.0], index=1, key="t2_margen")

    token_t2 = st.text_input("Token Bot Telegram", value="8673349898:AAEeBsWnJA4YRgNtEyoJ4fVcPifKSR1pqjg", key="t2_token")
    chat_id_t2 = st.text_input("Chat ID Telegram", value=CHAT_ID_DEFAULT, key="t2_chat")

    c3, c4 = st.columns(2)
    with c3:
        if st.button("⚡ INICIAR RADAR VENTAS AUTOMÁTICO", key="btn_t2_start"):
            if not st.session_state.t2_running:
                st.session_state.t2_running = True
                threading.Thread(target=loop_radar_ventas, args=(fiat_t2, precio_compra_t2, cant_usdt_t2, aplica_4x1000_t2, float(margen_obj_t2), token_t2, chat_id_t2), daemon=True).start()
                st.success("Radar de ventas iniciado (alerta cada 1 min si alcanza la meta).")
    with c4:
        if st.button("⏹ DETENER RADAR", key="btn_t2_stop"):
            st.session_state.t2_running = False
            st.warning("Radar detenido.")

# --- PESTAÑA 3: TRIANGULACIÓN DINÁMICA ---
with tab3:
    st.header("Triangulación Dinámica (COP ➔ PEN ➔ COP)")
    st.markdown("Bot Token por defecto: `8991219988:AAGFcr0F40QRjUUBDHGXnnmioeOkTRrBT5o`")

    cap_cop_t3 = st.number_input("Precio Compra Inicial (COP por USDT)", value=3750.0, step=10.0, key="t3_pcompra")
    usdt_inicial_t3 = st.number_input("Cantidad de USDT comprados", value=500.0, step=10.0, key="t3_usdt")
    aplica_4x1000_t3 = st.checkbox("Descontar 4x1000 (Sin cupo COP)", value=False, key="t3_4x1000")
    margen_obj_t3 = st.selectbox("Margen Objetivo Deseado (%)", [0.2, 0.3, 0.4, 0.5, 0.8, 1.0], index=2, key="t3_margen")

    token_t3 = st.text_input("Token Bot Telegram", value="8991219988:AAGFcr0F40QRjUUBDHGXnnmioeOkTRrBT5o", key="t3_token")
    chat_id_t3 = st.text_input("Chat ID Telegram", value=CHAT_ID_DEFAULT, key="t3_chat")

    c5, c6 = st.columns(2)
    with c5:
        if st.button("🔄 INICIAR TRIANGULACIÓN AUTOMÁTICA", key="btn_t3_start"):
            if not st.session_state.t3_running:
                st.session_state.t3_running = True
                threading.Thread(target=loop_triangulacion, args=(cap_cop_t3, usdt_inicial_t3, aplica_4x1000_t3, float(margen_obj_t3), token_t3, chat_id_t3), daemon=True).start()
                st.success("Triangulación automática iniciada (alerta cada 1 min si hay oportunidad).")
    with c6:
        if st.button("⏹ DETENER TRIANGULACIÓN", key="btn_t3_stop"):
            st.session_state.t3_running = False
            st.warning("Triangulación detenida.")
