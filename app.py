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
# Sidebar (menú lateral)
# =========================
st.sidebar.title("Menú")
pagina = st.sidebar.selectbox(
    "Selecciona una sección:",
    ["Inicio", "Algoritmo EMD (Anti-VEGF)","Bibliografia"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Herramienta de apoyo a la decisión. No reemplaza el juicio clínico.")

# =========================
# Página: INICIO
# =========================
if pagina == "Inicio":
    st.title("Algoritmos clínicos para EMD 👁️‍🧠")
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
    col_izq, col_der = st.columns([1.1, 1])

    # -------------------------
    # Columna izquierda: Edema macular diabético
    # -------------------------
    with col_izq:
        st.subheader("Edema macular diabético")

        st.markdown("""
                        1. **Zhang J, Zhang J, Zhang C, et al.**
                           Diabetic Macular Edema: Current Understanding, Molecular Mechanisms and Therapeutic Implications.
                           *Cells*. 2022;11(21):3362.
                        
                        2. **Rodríguez FJ, Wu L, Bordon AF, et al.**
                           Intravitreal aflibercept for the treatment of patients with diabetic macular edema in routine clinical practice in Latin America (AQUILA study).
                           *Int J Retina Vitreous*. 2022;8(1):52.
                        
                        3. **Liberski S, Wichrowska M, Kocięcki J.**
                           Aflibercept versus Faricimab in the treatment of nAMD and DME: Review.
                           *Int J Mol Sci*. 2022;23(16):9424.
                        
                        4. **Penha FM, Masud M, Khanani ZA, et al.**
                           Real-world evidence of dual inhibition of VEGF-A and ANG-2 in nAMD and DME.
                           *Int J Retina Vitreous*. 2024;10(1):5.
                        
                        5. **Wykoff CC, Abreu F, Adamis AP, et al.**
                           YOSEMITE & RHINE — Faricimab with extended dosing up to Q16W in DME.
                           *Lancet*. 2022;399(10326):741–755.
                        
                        6. **Brown DM, Boyer DS, Do DV, et al.**
                           Aflibercept 8 mg in diabetic macular edema (PHOTON): 48-week results.
                           *Lancet*. 2024;403(10432):1153–1163.
                        
                        7. **Friedman SM, Xu Y, Sherman S, et al.**
                           Aflibercept 8 mg vs Faricimab — Bayesian network meta-analysis.
                           *Ophthalmol Ther*. 2025;14(11):2919–2936.
                        
                        8. **Maccauro C, Jimenez Perez Y, Neri P, et al.**
                           Short-term outcomes of Faricimab and Aflibercept 8 mg in DME.
                           *AJO International*. 2025;2:100132.
                        
                        9. **Asociación Mexicana de Retina.**
                           Primer consenso nacional de edema macular diabético.
                           *Rev Mex Oftalmol*. 2021;95(Suppl 2):1–144.
                        """)

    with col_der:
       st.subheader("Degeneración macular relacionada con la edad")

        st.markdown(
            """
        <ol>
        <li><b>Zhang S</b>, Ren J, Chai R, Yuan S, Hao Y. Global burden of AMD 1990–2050.
        <i>BMC Public Health</i>. 2024;24(1):3510.</li>
        
        <li><b>Pugazhendhi A</b>, Hubbell M, Jairam P, Ambati B.
        Neovascular macular degeneration — etiology & therapy review.
        <i>Int J Mol Sci</i>. 2021;22(3):1170.</li>
        
        <li><b>Schneider M</b>, Bjerager J, Hodzic-Hadzibegovic D, et al.
        Switch to Faricimab in aflibercept-resistant nAMD.
        <i>Graefes Arch Clin Exp Ophthalmol</i>. 2024;262(7):2153-2162.</li>
        
        <li><b>Wong DT</b>, Aboobaker S, Maberley D, Sharma S, Yoganathan P.
        Expert recommendations for switching to Faricimab.
        <i>BMJ Open Ophthalmol</i>. 2025;10(1):e001967.</li>
        
        <li><b>Sharma A</b>, Kumar N, Kuppermann BD, Bandello F, Loewenstein A.
        Faricimab — expanding horizon beyond VEGF.
        <i>Eye</i>. 2020;34(5):802-804.</li>
        
        <li><b>Khanani AM</b>, Kotecha A, Chang A, et al.
        TENAYA & LUCERNE — Year-2 Faricimab treat-and-extend.
        <i>Ophthalmology</i>. 2024;131(8):914-926.</li>
        
        <li><b>Friedman SM</b>, Xu Y, Sherman S, et al.
        Aflibercept 8 mg vs Faricimab — network meta-analysis.
        <i>Ophthalmol Ther</i>. 2025;14(11):2919-2936.</li>
        
        <li><b>Wykoff CC</b>, Brown DM, Reed K, et al.
        High-dose Aflibercept 8 mg — CANDELA trial.
        <i>JAMA Ophthalmol</i>. 2023;141(9):834-842.</li>
        
        <li><b>Lanzetta P</b>, Korobelnik JF, Heier JS, et al.
        PULSAR — Aflibercept 8 mg in nAMD (48-week results).
        <i>Lancet</i>. 2024;403(10432):1141-1152.</li>
        
        <li><b>Korobelnik JF</b>, Dugel PU, Wykoff CC, et al.
        PULSAR — Long-term phase-3 outcomes.
        <i>Ophthalmology</i>. 2025.</li>
        </ol>
        """,
            unsafe_allow_html=True
        )

