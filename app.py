import streamlit as st
import requests
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
        url = "https://api.telegram.org/bot" + token + "/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=8)
    except Exception as e:
        print("Error Telegram: " + str(e))

def obtener_precio_binance(fiat, trade_type, pay_types, amount):
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
        print("Error P2P: " + str(e))
    return None, None

st.title("🚀 Panel de Control P2P & Multi-Bots de Telegram")
st.markdown("Monitoreo en tiempo real con visualización web y reportes automáticos a Telegram **cada 1 minuto**.")

tab1, tab2, tab3 = st.tabs([
    "📈 Oportunidades P2P (COP & PEN)",
    "📡 Radar P2P Ventas",
    "🔄 Triangulación Dinámica (COP➔PEN➔COP)"
])

if 't1_running' not in st.session_state: st.session_state.t1_running = False
if 't2_running' not in st.session_state: st.session_state.t2_running = False
if 't3_running' not in st.session_state: st.session_state.t3_running = False

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

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("🚀 Iniciar Monitoreo Automático COP/PEN", key="btn_t1_start"):
            st.session_state.t1_running = True
            enviar_telegram(token_t1, chat_id_t1, "🚀 <b>Módulo Oportunidades Activado</b> (Reportes cada 1 min)")
            st.rerun()
    with col_b2:
        if st.button("⏹ Detener Monitoreo COP/PEN", key="btn_t1_stop"):
            st.session_state.t1_running = False
            st.rerun()

    if st.session_state.t1_running or st.button("🔍 Escanear Ahora", key="btn_t1_manual"):
        hora = time.strftime("%H:%M:%S")
        with st.spinner("Consultando Binance P2P (COP y PEN)..."):
            p_c_cop, n_c_cop = obtener_precio_binance('COP', "SELL", ['BreB', 'Nequi', 'BANK'], "33600")
            p_v_cop, n_v_cop = obtener_precio_binance('COP', "BUY", ['BreB', 'Nequi', 'BANK'], "33600")

            p_c_pen, n_c_pen = obtener_precio_binance('PEN', "SELL", ['YAPE', 'PLIN'], "30")
            p_v_pen, n_v_pen = obtener_precio_binance('PEN', "BUY", ['YAPE', 'PLIN'], "30")

            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.subheader("🇨🇴 Colombia (COP)")
                if p_c_cop and p_v_cop:
                    usdt_cop = (cap_cop / p_c_cop) * (1 - FEE_MAKER)
                    bruto_cop = usdt_cop * p_v_cop * (1 - FEE_MAKER)
                    c_4x1000 = (cap_cop * IMPUESTO_4X1000) if aplica_4x1000 else 0.0
                    ganancia_cop = bruto_cop - cap_cop - c_4x1000
                    margen_cop = (ganancia_cop / cap_cop) * 100
                    st.metric(label="Margen Neto COP", value="{:.2f}%".format(margen_cop), delta="${:,.2f} COP".format(ganancia_cop))
                    st.write("• **Compra:** $" + "{:,.2f}".format(p_c_cop) + " (" + str(n_c_cop) + ")")
                    st.write("• **Venta:** $" + "{:,.2f}".format(p_v_cop) + " (" + str(n_v_cop) + ")")
                    
                    msg_cop = "🔄 <b>Estado COP [" + hora + "]</b>\n• Margen: " + "{:.2f}".format(margen_cop) + "% (+${:,.2f} COP)\n• Compra: ${:,.2f} \vert{} Venta:${:,.2f}".format(ganancia_cop, p_c_cop, p_v_cop)
                    enviar_telegram(token_t1, chat_id_t1, msg_cop)

                    if margen_cop >= margen_obj_t1:
                        alerta_cop = "🚀 <b>¡OPORTUNIDAD P2P EN COP!</b> [" + hora + "]\n• Ganancia: +${:,.2f} COP ({:.2f}%)".format(ganancia_cop, margen_cop)
                        enviar_telegram(token_t1, chat_id_t1, alerta_cop)
                else:
                    st.warning("Sin datos suficientes en COP.")

            with col_res2:
                st.subheader("🇵🇪 Perú (PEN)")
                if p_c_pen and p_v_pen:
                    usdt_pen = (cap_pen / p_c_pen) * (1 - FEE_MAKER)
                    bruto_pen = usdt_pen * p_v_pen * (1 - FEE_MAKER)
                    ganancia_pen = bruto_pen - cap_pen
                    margen_pen = (ganancia_pen / cap_pen) * 100
                    st.metric(label="Margen Neto PEN", value="{:.2f}%".format(margen_pen), delta="S/{:,.3f} PEN".format(ganancia_pen))
                    st.write("• **Compra:** S/" + "{:,.3f}".format(p_c_pen) + " (" + str(n_c_pen) + ")")
                    st.write("• **Venta:** S/" + "{:,.3f}".format(p_v_pen) + " (" + str(n_v_pen) + ")")

                    msg_pen = "🔄 <b>Estado PEN [" + hora + "]</b>\n• Margen: " + "{:.2f}".format(margen_pen) + "% (+S/{:,.3f})\n• Compra: S/{:,.3f} | Venta: S/{:,.3f}".format(ganancia_pen, p_c_pen, p_v_pen)
                    enviar_telegram(token_t1, chat_id_t1, msg_pen)

                    if margen_pen >= margen_obj_t1:
                        alerta_pen = "🚀 <b>¡OPORTUNIDAD P2P EN PEN!</b> [" + hora + "]\n• Ganancia: +S/{:,.3f} ({:.2f}%)".format(ganancia_pen, margen_pen)
                        enviar_telegram(token_t1, chat_id_t1, alerta_pen)
                else:
                    st.warning("Sin datos suficientes en PEN.")

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

    col_b3, col_b4 = st.columns(2)
    with col_b3:
        if st.button("⚡ Iniciar Radar Ventas Automático", key="btn_t2_start"):
            st.session_state.t2_running = True
            enviar_telegram(token_t2, chat_id_t2, "🔴 <b>Radar Ventas Activado</b> (Reportes cada 1 min)")
            st.rerun()
    with col_b4:
        if st.button("⏹ Detener Radar Ventas", key="btn_t2_stop"):
            st.session_state.t2_running = False
            st.rerun()

    if st.session_state.t2_running or st.button("⚡ Verificar Mercado Ventas Ahora", key="btn_t2_manual"):
        hora = time.strftime("%H:%M:%S")
        margen_pct = float(margen_obj_t2)
        factor_maker = 1.0 - FEE_MAKER
        factor_4x1000 = (1.0 - IMPUESTO_4X1000) if (aplica_4x1000_t2 and fiat_t2 == 'COP') else 1.0
        precio_meta = (precio_compra_t2 * (1.0 + (margen_pct / 100.0))) / (factor_maker * factor_4x1000)

        currency_symbol = "S/" if fiat_t2 == 'PEN' else "$"
        meta_str = ("{:,.3f}" if fiat_t2 == 'PEN' else "{:,.2f}").format(precio_meta)

        st.metric(label="Precio Meta de Venta (" + fiat_t2 + ")", value=currency_symbol + meta_str)

        param_amount = '33600' if fiat_t2 == 'COP' else '30'
        pay_types_list = ['BreB', 'Nequi', 'BANK'] if fiat_t2 == 'COP' else ['YAPE', 'PLIN']

        with st.spinner("Consultando precio actual en Binance..."):
            p_actual, nick_actual = obtener_precio_binance(fiat_t2, "BUY", pay_types_list, param_amount)
            if p_actual:
                p_act_str = ("{:,.3f}" if fiat_t2 == 'PEN' else "{:,.2f}").format(p_actual)
                st.info("📊 **Mejor precio de mercado actual (BUY):** " + currency_symbol + p_act_str + " " + fiat_t2 + " (" + str(nick_actual) + ")")
                
                msg_radar = "🔄 <b>Radar Ventas [" + hora + "]</b>\n• Mercado: " + currency_symbol + p_act_str + " (" + str(nick_actual) + ")\n• Tu Meta: " + currency_symbol + meta_str
                enviar_telegram(token_t2, chat_id_t2, msg_radar)

                if p_actual >= precio_meta:
                    st.success("🚨 ¡El precio de mercado superó tu precio meta!")
                    ganancia = (cant_usdt_t2 * precio_compra_t2) * (margen_pct / 100.0)
                    gan_str = ("{:,.3f}" if fiat_t2 == 'PEN' else "{:,.2f}").format(ganancia)
                    msg_alerta = "🚨 <b>¡ALERTA DE VENTA ALCANZADA!</b> [" + hora + "]\n• Meta: " + currency_symbol + meta_str + "\n• Mercado: " + currency_symbol + p_act_str + " (" + str(nick_actual) + ")\n• Ganancia Est: +" + currency_symbol + gan_str
                    enviar_telegram(token_t2, chat_id_t2, msg_alerta)
                else:
                    st.warning("⏳ El mercado actual está por debajo de tu meta.")
            else:
                st.error("No se pudo obtener datos de Binance P2P en este momento.")

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

    col_b5, col_b6 = st.columns(2)
    with col_b5:
        if st.button("🔄 Iniciar Triangulación Automática", key="btn_t3_start"):
            st.session_state.t3_running = True
            enviar_telegram(token_t3, chat_id_t3, "🚀 <b>Radar Triangulación Activado</b> (Reportes cada 1 min)")
            st.rerun()
    with col_b6:
        if st.button("⏹ Detener Triangulación", key="btn_t3_stop"):
            st.session_state.t3_running = False
            st.rerun()

    if st.session_state.t3_running or st.button("🔄 Ejecutar Triangulación Ahora", key="btn_t3_manual"):
        hora = time.strftime("%H:%M:%S")
        margen_pct = float(margen_obj_t3)
        with st.spinner("Calculando ruta COP -> PEN -> COP en Binance P2P..."):
            p_pen_venta, user_pen_v = obtener_precio_binance("PEN", "BUY", ["YAPE", "PLIN"], "30")
            p_pen_compra, user_pen_c = obtener_precio_binance("PEN", "SELL", ["YAPE", "PLIN"], "30")
            p_cop_venta, user_cop_v = obtener_precio_binance("COP", "BUY", ["BreB", "Nequi", "BANK"], "33600")

            if p_pen_venta and p_pen_compra and p_cop_venta:
                tax_4x1000 = IMPUESTO_4X1000 if aplica_4x1000_t3 else 0.0

                pen_recibidos = usdt_inicial_t3 * p_pen_venta * (1.0 - FEE_MAKER)
                usdt_recomprados = (pen_recibidos / p_pen_compra) * (1.0 - FEE_MAKER)
                cop_brutos = usdt_recomprados * p_cop_venta * (1.0 - FEE_MAKER)
                cop_netos = cop_brutos * (1.0 - tax_4x1000)

                cop_inversion = usdt_inicial_t3 * cap_cop_t3
                ganancia_cop = cop_netos - cop_inversion
                margen_real_pct = (ganancia_cop / cop_inversion) * 100.0

                st.metric(label="Margen Neto Triangulación", value="{:+.2f}%".format(margen_real_pct), delta="${:,.2f} COP".format(ganancia_cop))
                st.write("• **Vender USDT/PEN:** S/" + "{:,.3f}".format(p_pen_venta) + " (" + str(user_pen_v) + ")")
                st.write("• **Recomprar USDT/PEN:** S/" + "{:,.3f}".format(p_pen_compra) + " (" + str(user_pen_c) + ")")
                st.write("• **Vender USDT/COP:** $" + "{:,.2f}".format(p_cop_venta) + " (" + str(user_cop_v) + ")")
                st.write("• **Retorno Neto en COP:** $" + "{:,.2f}".format(cop_netos) + " COP")

                msg_trio = "🔄 <b>Triangulación [" + hora + "]</b>\n• Margen: " + "{:+.2f}% (+${:,.2f} COP)".format(margen_real_pct, ganancia_cop)
                enviar_telegram(token_t3, chat_id_t3, msg_trio)

                if margen_real_pct >= margen_pct:
                    st.success("¡Margen objetivo alcanzado!")
                    msg_alerta = (
                        "🚨 <b>¡OPORTUNIDAD DE TRIANGULACIÓN DETECTADA!</b> [" + hora + "]\n\n"
                        "📈 <b>Margen Neto Estimado:</b> +" + "{:.2f}%".format(margen_real_pct) + "\n"
                        "💰 <b>Ganancia Estimada:</b> +$" + "{:,.2f} COP".format(ganancia_cop) + "\n\n"
                        "📋 <b>PASOS EN BINANCE P2P:</b>\n"
                        "1. Vender " + "{:,.2f}".format(usdt_inicial_t3) + " USDT a S/" + "{:,.3f}".format(p_pen_venta) + " PEN\n"
                        "2. Recomprar USDT con PEN a S/" + "{:,.3f}".format(p_pen_compra) + " PEN\n"
                        "3. Vender USDT finales a $" + "{:,.2f}".format(p_cop_venta) + " COP"
                    )
                    enviar_telegram(token_t3, chat_id_t3, msg_alerta)
                else:
                    st.warning("El margen actual del circuito está por debajo del objetivo configurado.")
            else:
                st.error("No se pudieron consultar todos los libros de órdenes necesarios en Binance P2P.")

# --- AUTO-REFRESH CADA 60 SEGUNDOS CUANDO ESTÁ ACTIVO ---
if st.session_state.t1_running or st.session_state.t2_running or st.session_state.t3_running:
    time.sleep(60)
    st.rerun()
