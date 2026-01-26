import streamlit as st

# =========================
# Configuración básica
# =========================
st.set_page_config(
    page_title="Algoritmos clínicos EMD",
    page_icon="🧠",
    layout="wide"
)

# =========================
# Lógica del algoritmo EMD
# =========================
def algoritmo_emd(
    tipo_paciente: str,
    semana: int,
    intervalo_actual: str,
    gmc_basal: float,
    gmc_actual: float,
    avmc_basal: int,
    avmc_actual: int,
):
    """
    Se implementa el algoritmo para manejo de EMD con Anti-VEGF.
    Devuelve: (plan, justificación, cambio_gmc, cambio_av)
    """

    # Evitar división por cero
    if gmc_basal <= 0:
        cambio_gmc = None
    else:
        cambio_gmc = (gmc_actual - gmc_basal) / gmc_basal * 100

    cambio_av = avmc_actual - avmc_basal

    # -------------------------------
    # 1. PACIENTE NAÍVE
    # -------------------------------
    if tipo_paciente == "Naive":

        # Fase de carga antes de semana 12
        if semana < 12:
            plan = "Continuar fase de carga"
            justificacion = (
                "Paciente naïve antes de la semana 12. "
                "Completar 3 dosis de carga mensuales y reevaluar en la semana 12."
            )
            return plan, justificacion, cambio_gmc, cambio_av

        # A partir de semana 12 aplicamos la lógica de GMC
        # GMC ≤ 325 → SWITCH inmediato
        if gmc_actual <= 325:
            plan = "Switch de anti-VEGF + 3 dosis de carga"
            justificacion = (
                "Mala respuesta al fármaco inicial: GMC ≤ 325 µm en la reevaluación."
            )
            return plan, justificacion, cambio_gmc, cambio_av

        # GMC ≥ 400 → Ozurdex
        if gmc_actual >= 400:
            plan = "Cambiar a Ozurdex"
            justificacion = (
                "Edema macular severo (GMC ≥ 400 µm). Se recomienda corticoide intravítreo."
            )
            return plan, justificacion, cambio_gmc, cambio_av

        # 325 < GMC < 400 → EARLY SWITCH
        if 325 < gmc_actual < 400:

            if cambio_gmc is None:
                plan = "Revisar datos"
                justificacion = (
                    "No se pudo calcular el porcentaje de cambio de GMC (GMC basal inválido)."
                )
                return plan, justificacion, cambio_gmc, cambio_av

            # Disminución > 10%
            if cambio_gmc < -10:
                plan = "Mantener intervalo actual"
                justificacion = (
                    "Buena respuesta: reducción >10% del GMC en zona 325-400 µm."
                )
                return plan, justificacion, cambio_gmc, cambio_av

            # GMC estable (±10%)
            if -10 <= cambio_gmc <= 10:
                plan = "Mantener intervalo actual"
                justificacion = "GMC estable (±10%). No hay empeoramiento significativo."
                return plan, justificacion, cambio_gmc, cambio_av

            # Aumento < 10%
            if 0 < cambio_gmc < 10:
                plan = "Acortar intervalo 4 semanas (mínimo Q4W)"
                justificacion = (
                    "Aumento leve del GMC (<10%). Se recomienda intensificar el esquema."
                )
                return plan, justificacion, cambio_gmc, cambio_av

            # Aumento ≥ 20%
            if cambio_gmc >= 20:
                plan = "Acortar intervalo 8 semanas (mínimo Q4W)"
                justificacion = (
                    "Aumento significativo del GMC (≥20%) en zona de Early Switch."
                )
                return plan, justificacion, cambio_gmc, cambio_av

            # Caso intermedio raro
            plan = "Mantener y reevaluar"
            justificacion = "Evolución dentro de un rango no típico. Correlacionar clínicamente."
            return plan, justificacion, cambio_gmc, cambio_av

    # -------------------------------
    # 2. PACIENTE CON TRATAMIENTO PREVIO
    # -------------------------------
    if tipo_paciente == "Previo":

        if cambio_gmc is None:
            plan = "Revisar datos"
            justificacion = (
                "No se pudo calcular el porcentaje de cambio de GMC (GMC basal inválido)."
            )
            return plan, justificacion, cambio_gmc, cambio_av

        # Disminución > 10%
        if cambio_gmc < -10:
            plan = "Pasar o mantener en Q8W (si estaba en Q4W)"
            justificacion = (
                "Buena respuesta: reducción >10% del GMC. Puede espaciarse a Q8W si estaba en Q4W."
            )
            return plan, justificacion, cambio_gmc, cambio_av

        # GMC estable (±10%)
        if -10 <= cambio_gmc <= 10:
            plan = "Mantener intervalo Q4W"
            justificacion = "GMC estable (±10%). No hay mejoría clara, pero tampoco empeora."
            return plan, justificacion, cambio_gmc, cambio_av

        # Aumento < 20%
        if 0 < cambio_gmc < 20:
            plan = "Mantener intervalo Q4W"
            justificacion = "Leve aumento del GMC (<20%). Se mantiene frecuencia mensual."
            return plan, justificacion, cambio_gmc, cambio_av

        # Aumento ≥ 20%
        if cambio_gmc >= 20:
            plan = "Switch de anti-VEGF + 3 dosis de carga"
            justificacion = "Mala respuesta: aumento ≥20% del GMC con tratamiento previo."
            return plan, justificacion, cambio_gmc, cambio_av

    # Si nada aplica
    plan = "Sin decisión automática"
    justificacion = "Revisar datos ingresados y correlacionar con el contexto clínico."
    return plan, justificacion, cambio_gmc, cambio_av
# =========================
# Lógica del algoritmo DMRE (simplificado para intervalos)
# =========================
def algoritmo_dmre(
    intervalo_actual: str,
    lir: bool,
    lsr_micras: float,
    avmc_basal: int,
    avmc_mejor: int,
    avmc_actual: int,
    hemorragia_nueva: bool,
    gmc_sem16: float,
    gmc_min_hist: float,
    gmc_actual: float,
):
    """
    DMRE Anti-VEGF (Aflibercept 8 / Faricimab 6) - lógica de actividad y ajuste de intervalo.
    Devuelve:
      - plan (Extender / Mantener / Acortar / Considerar switch)
      - justificación
      - detalle (dict)
    """

    # Intervalo en semanas
    map_int = {"Q4W": 4, "Q8W": 8, "Q12W": 12, "Q16W": 16}
    int_sem = map_int.get(intervalo_actual, 8)

    # Cambios visuales
    delta_vs_basal = avmc_actual - avmc_basal      # negativo = empeora
    delta_vs_mejor = avmc_actual - avmc_mejor      # negativo = peor que su mejor

    # Criterios de actividad por OCT/visión/hemorragia (según umbrales del diagrama)
    actividad_liquido = lir or (lsr_micras >= 50)
    actividad_vision = (delta_vs_basal <= -5) or (delta_vs_mejor <= -10)
    actividad_hemorragia = hemorragia_nueva

    # Criterios GMC del diagrama
    delta_gmc_vs_sem16 = None if gmc_sem16 <= 0 else (gmc_actual - gmc_sem16)
    delta_gmc_vs_min = None if gmc_min_hist <= 0 else (gmc_actual - gmc_min_hist)

    actividad_gmc = False
    motivos_gmc = []
    if delta_gmc_vs_sem16 is not None and delta_gmc_vs_sem16 >= 50:
        actividad_gmc = True
        motivos_gmc.append(f"ΔGMC vs semana 16 = +{delta_gmc_vs_sem16:.0f} µm (≥ 50)")
    if delta_gmc_vs_min is not None and delta_gmc_vs_min >= 75:
        actividad_gmc = True
        motivos_gmc.append(f"ΔGMC vs mínimo histórico = +{delta_gmc_vs_min:.0f} µm (≥ 75)")

    # Actividad global
    actividad = actividad_liquido or actividad_vision or actividad_hemorragia or actividad_gmc

    # Reglas de ajuste de intervalo (enfoque práctico)
    # - Si NO hay actividad: extender +4 semanas hasta Q16W
    # - Si hay actividad: acortar -4 semanas hasta mínimo Q8W
    # - Si hay actividad pese a Q8W: sugerir considerar switch / reevaluación
    if not actividad:
        if int_sem < 16:
            nuevo = min(16, int_sem + 4)
            plan = f"Extender intervalo a Q{nuevo}W"
            just = "Sin criterios de actividad (líquido/visión/hemorragia/GMC). Se puede extender en +4 semanas (máx Q16W)."
        else:
            plan = "Mantener intervalo (Q16W)"
            just = "Sin criterios de actividad y ya está en el intervalo máximo (Q16W)."
    else:
        if int_sem > 8:
            nuevo = max(8, int_sem - 4)
            plan = f"Acortar intervalo a Q{nuevo}W"
            just = "Hay criterios de actividad. Se recomienda acortar 4 semanas (mínimo Q8W)."
        else:
            plan = "Mantener Q8W y considerar switch"
            just = "Hay actividad a pesar de estar en intervalo corto (Q8W). Considerar evaluación para switch o causas de respuesta subóptima."

    # Construir justificación detallada
    motivos = []
    if actividad_liquido:
        motivos.append("Actividad por OCT: LIR presente o LSR ≥ 50 µm.")
    if actividad_vision:
        motivos.append("Actividad funcional: caída de AVMC (≤ -5 vs basal o ≤ -10 vs mejor).")
    if actividad_hemorragia:
        motivos.append("Actividad clínica: hemorragia macular nueva.")
    if actividad_gmc:
        motivos.append("Actividad por GMC: " + "; ".join(motivos_gmc))

    detalle = {
        "actividad": actividad,
        "delta_vs_basal_letras": delta_vs_basal,
        "delta_vs_mejor_letras": delta_vs_mejor,
        "delta_gmc_vs_sem16": delta_gmc_vs_sem16,
        "delta_gmc_vs_min": delta_gmc_vs_min,
        "motivos": motivos
    }
    return plan, just, detalle


# =========================
# Sidebar (menú lateral)
# =========================
st.sidebar.title("Menú")
pagina = st.sidebar.selectbox(
    "Selecciona una sección:",
    ["Inicio", "Algoritmo EMD (Anti-VEGF)", "Algoritmo DMRE (Anti-VEGF)", "Bibliografia"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Herramienta de apoyo a la decisión. No reemplaza el juicio clínico.")

# =========================
# Página: INICIO
# =========================
if pagina == "Inicio":
    st.title("Algoritmos clínicos (EMD y DMRE) 👁️‍🧠")

    st.write(
        """
        Esta app implementa una **herramienta de apoyo a la decisión** para el manejo del
        **Edema Macular Diabético (EMD)** con Anti-VEGF, basada en cambios del **GMC** y la **AVMC**.

        En el menú de la izquierda puedes:
        - Ir al **algoritmo EMD (Anti-VEGF)**

        >  *Esta herramienta no reemplaza el juicio clínico del oftalmólogo ni las guías formales.*
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Versión del prototipo", "0.1.0")
    with col2:
        st.metric("Algoritmos activos", 1)

    st.subheader("Resumen del flujo de decisión")
    st.markdown(
        """
        - Clasificar al paciente como **Naïve** o **con tratamiento previo**.
        - Basarse en el **cambio porcentual del GMC** (y el valor absoluto en micras).
        - A la semana 12 en Naïve:
          - **GMC ≤ 325 µm** → Switch + 3 dosis de carga
          - **325–400 µm** → Esquema de *Early Switch*
          - **≥ 400 µm** → Considerar **Ozurdex**
        - En tratamiento previo:
          - ↓ >10% → espaciar (Q8W)
          - Estable ±10% → mantener Q4W
          - ↑ ≥20% → Switch + 3 dosis de carga
        """
    )

# =========================
# Página: ALGORTIMO EMD
# =========================
elif pagina == "Algoritmo EMD (Anti-VEGF)":
    st.title("Algoritmo EMD – Anti-VEGF 💉")

    st.markdown(
        """
        Ingresa los datos clave del paciente para que la herramienta sugiera:
        - Si continuar, acortar o extender el intervalo.
        - Si realizar **switch** de Anti-VEGF.
        - Si considerar **corticoide intravítreo (Ozurdex)**.
        """
    )

    col_izq, col_der = st.columns([1.1, 1])

    # -------------------------
    # Columna izquierda: inputs
    # -------------------------
    with col_izq:
        st.subheader("Datos del paciente")

        tipo_paciente = st.radio(
            "Tipo de paciente",
            ["Naive", "Previo"],
            help="Naive: nunca ha recibido Anti-VEGF. Previo: ya venía en tratamiento."
        )

        semana = st.number_input(
            "Semana de tratamiento (desde inicio de esquema actual)",
            min_value=0,
            max_value=200,
            value=12,
            step=1
        )

        intervalo_actual = st.selectbox(
            "Intervalo actual entre aplicaciones",
            ["Q4W", "Q8W", "Q12W", "Q16W"]
        )

        st.markdown("---")
        st.subheader("OCT – Grosor Macular Central (GMC)")

        gmc_basal = st.number_input(
            "GMC basal (µm)",
            min_value=0.0,
            max_value=1200.0,
            value=400.0,
            step=1.0
        )

        gmc_actual = st.number_input(
            "GMC actual (µm)",
            min_value=0.0,
            max_value=1200.0,
            value=350.0,
            step=1.0
        )

        st.markdown("---")
        st.subheader("Agudeza Visual (AVMC)")

        avmc_basal = st.number_input(
            "AVMC basal (letras)",
            min_value=0,
            max_value=100,
            value=60,
            step=1
        )

        avmc_actual = st.number_input(
            "AVMC actual (letras)",
            min_value=0,
            max_value=100,
            value=65,
            step=1
        )

        calcular = st.button("Calcular recomendación 🧮")

    # -------------------------
    # Columna derecha: outputs
    # -------------------------
    with col_der:
        st.subheader("Resultado")

        if calcular:
            plan, justificacion, cambio_gmc, cambio_av = algoritmo_emd(
                tipo_paciente,
                semana,
                intervalo_actual,
                gmc_basal,
                gmc_actual,
                avmc_basal,
                avmc_actual
            )

            # Mostrar plan
            st.success(f"**Plan sugerido:** {plan}")

            # Mostrar justificación
            st.write(f"**Justificación clínica:** {justificacion}")

            st.markdown("---")
            st.subheader("Detalles de la evolución")

            if cambio_gmc is not None:
                st.write(
                    f"- Cambio porcentual de GMC: "
                    f"**{cambio_gmc:.1f}%** (de {gmc_basal:.0f} µm a {gmc_actual:.0f} µm)"
                )
            else:
                st.warning("No se pudo calcular el % de cambio de GMC (GMC basal no válido).")

            st.write(
                f"- Cambio de AVMC: **{cambio_av} letras** "
                f"(de {avmc_basal} a {avmc_actual})"
            )

            st.info(
                "Esta herramienta es solo de apoyo a la decisión y **no reemplaza** el juicio clínico "
                "ni las guías institucionales."
            )
        else:
            st.info("Ingresa los datos a la izquierda y pulsa **Calcular recomendación**.")
# =========================
# Página: Bibliografia
# =========================
elif pagina == "Bibliografia":
    st.title ("BIBLIOGRAFIA")
    st.subheader("Edema macular diabético")
    st.markdown(    """
                        <ol>
                        
                        <li><b>Zhang J, Zhang J, Zhang C, et al.</b>
                        Diabetic Macular Edema: Current Understanding, Molecular Mechanisms and Therapeutic Implications.
                        <i>Cells</i>. 2022;11(21):3362.</li>
                        
                        <li><b>Rodríguez FJ, Wu L, Bordon AF, et al.</b>
                        Intravitreal aflibercept for the treatment of patients with diabetic macular edema in routine clinical practice in Latin America: the AQUILA study.
                        <i>Int J Retina Vitreous</i>. 2022;8(1):52.</li>
                        
                        <li><b>Liberski S, Wichrowska M, Kocięcki J.</b>
                        Aflibercept versus Faricimab in the Treatment of Neovascular Age-Related Macular Degeneration and Diabetic Macular Edema: A Review.
                        <i>Int J Mol Sci</i>. 2022;23(16):9424.</li>
                        
                        <li><b>Penha FM, Masud M, Khanani ZA, et al.</b>
                        Review of real-world evidence of dual inhibition of VEGF-A and ANG-2 with faricimab in nAMD and DME.
                        <i>Int J Retina Vitreous</i>. 2024;10(1):5.</li>
                        
                        <li><b>Wykoff CC, Abreu F, Adamis AP, et al.</b>
                        Efficacy, durability, and safety of intravitreal faricimab with extended dosing up to every 16 weeks in patients with diabetic macular oedema (YOSEMITE and RHINE): two randomised, double-masked, phase 3 trials.
                        <i>Lancet</i>. 2022;399(10326):741–755.</li>
                        
                        <li><b>Brown DM, Boyer DS, Do DV, et al.</b>
                        Intravitreal aflibercept 8 mg in diabetic macular oedema (PHOTON): 48-week results from a randomised, double-masked, non-inferiority, phase 2/3 trial.
                        <i>Lancet</i>. 2024;403(10432):1153–1163.</li>
                        
                        <li><b>Friedman SM, Xu Y, Sherman S, et al.</b>
                        Aflibercept 8 mg versus Faricimab Treat-and-Extend for Diabetic Macular Edema or Neovascular Age-Related Macular Degeneration: A Bayesian Fixed-Effect Network Meta-analysis of Clinical Trials.
                        <i>Ophthalmol Ther</i>. 2025;14(11):2919–2936.</li>
                        
                        <li><b>Maccauro C, Jimenez Perez Y, Neri P, et al.</b>
                        Short-term outcomes of faricimab and aflibercept 8 mg in diabetic macular edema.
                        <i>AJO International</i>. 2025;2:100132.</li>
                        
                        <li><b>Asociación Mexicana de Retina.</b>
                        Primer consenso nacional de edema macular diabético.
                        <i>Rev Mex Oftalmol</i>. 2021;95(Suppl 2):1–144.</li>
                        
                        </ol>
                        """,
                            unsafe_allow_html=True)
    
# =========================
# Página: ALGORTIMO DMRE
# =========================
elif pagina == "Algoritmo DMRE (Anti-VEGF)":
    st.title("Algoritmo DMRE – Anti-VEGF 💉👁️")
    st.caption("Incluye criterios de actividad por OCT (LIR/LSR), AVMC, hemorragia y GMC (Δ≥50 vs sem16 o Δ≥75 vs mínimo).")

    col_izq, col_der = st.columns([1.15, 1])

    with col_izq:
        st.subheader("Esquema actual")
        intervalo_actual = st.selectbox("Intervalo actual", ["Q8W", "Q12W", "Q16W"], index=0)

        st.markdown("---")
        st.subheader("OCT – Líquido")
        lir = st.radio("¿LIR (líquido intrarretiniano) presente?", ["No", "Sí"], index=0) == "Sí"
        lsr_micras = st.number_input("LSR (micras)", min_value=0.0, max_value=500.0, value=30.0, step=1.0)

        st.markdown("---")
        st.subheader("Agudeza Visual (AVMC)")
        avmc_basal = st.number_input("AVMC basal (letras)", min_value=0, max_value=100, value=60, step=1)
        avmc_mejor = st.number_input("Mejor AVMC registrada (letras)", min_value=0, max_value=100, value=70, step=1)
        avmc_actual = st.number_input("AVMC actual (letras)", min_value=0, max_value=100, value=68, step=1)

        st.markdown("---")
        st.subheader("Evento clínico")
        hemorragia_nueva = st.radio("¿Hemorragia macular nueva?", ["No", "Sí"], index=0) == "Sí"

        st.markdown("---")
        st.subheader("GMC – Grosor Macular Central")
        gmc_sem16 = st.number_input("GMC semana 16 (µm)", min_value=0.0, max_value=1200.0, value=280.0, step=1.0)
        gmc_min_hist = st.number_input("GMC mínimo histórico (µm)", min_value=0.0, max_value=1200.0, value=260.0, step=1.0)
        gmc_actual = st.number_input("GMC actual (µm)", min_value=0.0, max_value=1200.0, value=300.0, step=1.0)

        calcular_dmre = st.button("Calcular recomendación (DMRE) 🧮")

    with col_der:
        st.subheader("Resultado")
        if calcular_dmre:
            plan, just, detalle = algoritmo_dmre(
                intervalo_actual,
                lir,
                lsr_micras,
                avmc_basal,
                avmc_mejor,
                avmc_actual,
                hemorragia_nueva,
                gmc_sem16,
                gmc_min_hist,
                gmc_actual
            )

            if "Acortar" in plan or "considerar switch" in plan.lower():
                st.warning(f"**Plan sugerido:** {plan}")
            else:
                st.success(f"**Plan sugerido:** {plan}")

            st.write(f"**Justificación clínica:** {just}")

            st.markdown("---")
            st.subheader("Detalles de actividad")

            st.write(f"- Actividad global: **{'Sí' if detalle['actividad'] else 'No'}**")
            st.write(f"- ΔAVMC vs basal: **{detalle['delta_vs_basal_letras']} letras**")
            st.write(f"- ΔAVMC vs mejor: **{detalle['delta_vs_mejor_letras']} letras**")

            if detalle["delta_gmc_vs_sem16"] is not None:
                st.write(f"- ΔGMC vs semana 16: **+{detalle['delta_gmc_vs_sem16']:.0f} µm** (umbral ≥ 50)")
            else:
                st.write("- ΔGMC vs semana 16: **N/A**")

            if detalle["delta_gmc_vs_min"] is not None:
                st.write(f"- ΔGMC vs mínimo histórico: **+{detalle['delta_gmc_vs_min']:.0f} µm** (umbral ≥ 75)")
            else:
                st.write("- ΔGMC vs mínimo histórico: **N/A**")

            if detalle["motivos"]:
                st.markdown("**Motivos detectados:**")
                for m in detalle["motivos"]:
                    st.write(f"- {m}")
            else:
                st.write("No se detectaron criterios de actividad.")

            st.info("Soporte a la decisión. No reemplaza juicio clínico.")
        else:
            st.info("Ingresa los datos a la izquierda y pulsa **Calcular recomendación (DMRE)**.")
   
