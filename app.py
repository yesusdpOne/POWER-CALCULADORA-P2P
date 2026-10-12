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
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=8)
    except Exception as e:
        st.error(f"Error Telegram: {e}")

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
st.markdown("Monitoreo en tiempo real de Oportunidades, Radar de Ventas y Triangulación Dinámica con alertas automáticas.")

tab1, tab2, tab3 = st.tabs([
    "📈 Oportunidades P2P (COP & PEN)",
    "📡 Radar P2P Ventas",
    "🔄 Triangulación Dinámica (COP➔PEN➔COP)"
])

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

    if st.button("🚀 Activar y Escanear Oportunidades", key="btn_t1"):
        # Alerta de activación inicial
        msg_inicio_t1 = (
            f"🚀 <b>¡MÓDULO OPORTUNIDADES P2P ACTIVADO!</b> 🚀\n\n"
            f"• <b>Capital COP:</b> ${cap_cop:,.2f}\n"
            f"• <b>Capital PEN:</b> S/{cap_pen:,.2f}\n"
            f"• <b>Margen Objetivo:</b> {margen_obj_t1}%\n"
            f"📡 <i>Escaneando mercados en Binance...</i>"
        )
        enviar_telegram(token_t1, chat_id_t1, msg_inicio_t1)
        st.success("¡Alerta de activación enviada a Telegram!")

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
                    st.metric(label="Margen Neto COP", value=f"{margen_cop:.2f}%", delta=f"${ganancia_cop:,.2f} COP")
                    st.write(f"• **Compra:** ${p_c_cop:,.2f} ({n_c_cop})")
                    st.write(f"• **Venta:** ${p_v_cop:,.2f} ({n_v_cop})")
                    if margen_cop >= margen_obj_t1:
                        msg = f"🚀 <b>¡OPORTUNIDAD P2P EN COP!</b>\n• Ganancia: +${ganancia_cop:,.2f} COP ({margen_cop:.2f}%)"
                        enviar_telegram(token_t1, chat_id_t1, msg)
                else:
                    st.warning("Sin datos suficientes en COP.")

            with col_res2:
                st.subheader("🇵🇪 Perú (PEN)")
                if p_c_pen and p_v_pen:
                    usdt_pen = (cap_pen / p_c_pen) * (1 - FEE_MAKER)
                    bruto_pen = usdt_pen * p_v_pen * (1 - FEE_MAKER)
                    ganancia_pen = bruto_pen - cap_pen
                    margen_pen = (ganancia_pen / cap_pen) * 100
                    st.metric(label="Margen Neto PEN", value=f"{margen_pen:.2f}%", delta=f"S/{ganancia_pen:,.3f} PEN")
                    st.write(f"• **Compra:** S/{p_c_pen:.3f} ({n_c_pen})")
                    st.write(f"• **Venta:** S/{p_v_pen:.3f} ({n_v_pen})")
                    if margen_pen >= margen_obj_t1:
                        msg = f"🚀 <b>¡OPORTUNIDAD P2P EN PEN!</b>\n• Ganancia: +S/{ganancia_pen:,.3f} ({margen_pen:.2f}%)"
                        enviar_telegram(token_t1, chat_id_t1, msg)
                else:
                    st.warning("Sin datos suficientes en PEN.")

# --- PESTAÑA 2: RADAR P2P VENTAS ---
with tab2:
    st.header("Radar P2P Ventas (Precio Meta)")
    st.markdown("Bot Token por defecto: `8673349898:AAEeBsWnJA4YRgNtEyoJ4fVcPifKSR1pqjg`")

    fiat_t2 = st.selectbox("Moneda", ["COP", "PEN"], key="t2_fiat")
    precio_compra_t2 = st.number_input("Precio de Compra USDT", value=3900.0, step=10.0, key="t2_pcompra")
    cant_usdt_t2 = st.number_input("Cantidad de USDT a vender", value=100.0, step=10.0, key="t2_cant")
    aplica_4x1000_t2 = st.checkbox("Descontar 4x1000 (COP)", value=True, key="t2_4x1000")
    margen_obj_t2 = st.selectbox("Margen Objetivo (%)", [0.4, 0.5, 0.6, 0.8, 1.0], index=1, key="t2_margen")

    token_t2 = st.text_input("Token Bot Telegram", value="8673349898:AAEeBsWnJA4YRgNtEyoJ4fVcPifKSR1pqjg", key="t2_token")
    chat_id_t2 = st.text_input("Chat ID Telegram", value=CHAT_ID_DEFAULT, key="t2_chat")

    if st.button("⚡ Activar Radar de Ventas", key="btn_t2"):
        margen_pct = float(margen_obj_t2)
        factor_maker = 1.0 - FEE_MAKER
        factor_4x1000 = (1.0 - IMPUESTO_4X1000) if (aplica_4x1000_t2 and fiat_t2 == 'COP') else 1.0
        precio_meta = (precio_compra_t2 * (1.0 + (margen_pct / 100.0))) / (factor_maker * factor_4x1000)

        # Alerta de activación inicial
        msg_inicio_t2 = (
            f"🔴 <b>Radar P2P Activado (Ventas)</b>\n"
            f"• <b>Moneda:</b> {fiat_t2}\n"
            f"• <b>Precio Compra:</b> ${precio_compra_t2:,.2f}\n"
            f"• <b>Margen Neto:</b> {margen_pct}%\n"
            f"🎯 <b>Precio Meta de Venta:</b> <b>${precio_meta:,.2f} {fiat_t2}</b>\n\n"
            f"📢 <i>¡Monitoreando mercado en Binance P2P!</i>"
        )
        enviar_telegram(token_t2, chat_id_t2, msg_inicio_t2)
        st.success("¡Alerta de activación enviada a Telegram!")

        st.metric(label=f"Precio Meta de Venta ({fiat_t2})", value=f"${precio_meta:,.2f}")

        param_amount = '33600' if fiat_t2 == 'COP' else '30'
        pay_types_list = ['BreB', 'Nequi', 'BANK'] if fiat_t2 == 'COP' else ['YAPE', 'PLIN']

        with st.spinner("Consultando precio actual en Binance..."):
            p_actual, nick_actual = obtener_precio_binance(fiat_t2, "BUY", pay_types_list, param_amount)
            if p_actual:
                st.info(f"📊 **Mejor precio de mercado actual (BUY):** ${p_actual:,.2f} {fiat_t2} ({nick_actual})")
                if p_actual >= precio_meta:
                    st.success(f"🚨 ¡El precio de mercado (${p_actual:,.2f}) superó tu precio meta (${precio_meta:,.2f})!")
                    msg = f"🚨 <b>¡ALERTA DE VENTA ALCANZADA!</b>\n• Meta: ${precio_meta:,.2f}\n• Mercado: ${p_actual:,.2f} ({nick_actual})"
                    enviar_telegram(token_t2, chat_id_t2, msg)
                else:
                    st.warning(f"⏳ El mercado actual está por debajo de tu meta. Faltan ${precio_meta - p_actual:,.2f} para alcanzar el objetivo.")
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

    if st.button("🔄 Activar Triangulación Dinámica", key="btn_t3"):
        margen_pct = float(margen_obj_t3)
        
        # Alerta de activación inicial para la triangulación
        msg_inicio_t3 = (
            f"🚀 <b>¡RADAR DE TRIANGULACIÓN INTERNA ACTIVADO!</b> 🚀\n\n"
            f"💵 <b>Precio Compra Inicial:</b> ${cap_cop_t3:,.2f} COP\n"
            f"📊 <b>USDT en Operación:</b> {usdt_inicial_t3:,.2f} USDT\n"
            f"🎯 <b>Margen Objetivo:</b> {margen_pct}%\n"
            f"🏦 <b>Descontar 4x1000:</b> {'Sí' if aplica_4x1000_t3 else 'No'}\n\n"
            f"📡 <i>Escaneando circuito Binance P2P (COP ➔ PEN ➔ USDT ➔ COP)...</i>"
        )
        enviar_telegram(token_t3, chat_id_t3, msg_inicio_t3)
        st.success("¡Alerta de activación enviada a Telegram!")

        with st.spinner("Calculando ruta COP -> PEN -> COP en Binance P2P..."):
            # Paso A: Vender USDT por PEN (BUY)
            p_pen_venta, user_pen_v = obtener_precio_binance("PEN", "BUY", ["YAPE", "PLIN"], "30")
            # Paso B: Recomprar USDT con PEN (SELL)
            p_pen_compra, user_pen_c = obtener_precio_binance("PEN", "SELL", ["YAPE", "PLIN"], "30")
            # Paso C: Vender USDT por COP (BUY)
            p_cop_venta, user_cop_v = obtener_precio_binance("COP", "BUY", ["BreB", "Nequi", "BANK"], "33600")

            if p_pen_venta and p_pen_compra and p_cop_venta:
                tax_4x1000 = IMPUESTO_4X1000 if aplica_4x1000_t3 else 0.0

                # 1. Vender USDT por PEN
                pen_recibidos = usdt_inicial_t3 * p_pen_venta * (1.0 - FEE_MAKER)
                # 2. Recomprar USDT con PEN
                usdt_recomprados = (pen_recibidos / p_pen_compra) * (1.0 - FEE_MAKER)
                # 3. Vender USDT por COP
                cop_brutos = usdt_recomprados * p_cop_venta * (1.0 - FEE_MAKER)
                cop_netos = cop_brutos * (1.0 - tax_4x1000)

                cop_inversion = usdt_inicial_t3 * cap_cop_t3
                ganancia_cop = cop_netos - cop_inversion
                margen_real_pct = (ganancia_cop / cop_inversion) * 100.0

                st.metric(label="Margen Neto Triangulación", value=f"{margen_real_pct:+.2f}%", delta=f"${ganancia_cop:,.2f} COP")
                st.write(f"• **Vender USDT/PEN:** S/{p_pen_venta:,.3f} ({user_pen_v})")
                st.write(f"• **Recomprar USDT/PEN:** S/{p_pen_compra:,.3f} ({user_pen_c})")
                st.write(f"• **Vender USDT/COP:** ${p_cop_venta:,.2f} ({user_cop_v})")
                st.write(f"• **Retorno Neto en COP:** ${cop_netos:,.2f} COP")

                if margen_real_pct >= margen_pct:
                    st.success("¡Margen objetivo alcanzado y alerta enviada a Telegram!")
                    msg_alerta = (
                        f"🚨 <b>¡OPORTUNIDAD DE TRIANGULACIÓN DETECTADA!</b> 🚨\n\n"
                        f"📈 <b>Margen Neto Estimado:</b> +{margen_real_pct:.2f}%\n"
                        f"💰 <b>Ganancia Estimada:</b> +${ganancia_cop:,.2f} COP\n\n"
                        f"📋 <b>PASOS EN BINANCE P2P:</b>\n"
                        f"1. Vender {usdt_inicial_t3:,.2f} USDT a S/{p_pen_venta:,.3f} PEN\n"
                        f"2. Recomprar USDT con PEN a S/{p_pen_compra:,.3f} PEN\n"
                        f"3. Vender USDT finales a ${p_cop_venta:,.2f} COP"
                    )
                    enviar_telegram(token_t3, chat_id_t3, msg_alerta)
                else:
                    st.warning("El margen actual del circuito está por debajo del objetivo configurado.")
            else:
                st.error("No se pudieron consultar todos los libros de órdenes necesarios en Binance P2P.")
