import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN GOOGLE SHEETS ---
SHEET_NAME = "Torneo CPU"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["google_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(creds_dict), scope)
client = gspread.authorize(creds)

# --- CACHÉ EN SESIÓN ---
if "sheet_cache" not in st.session_state:
    st.session_state.sheet_cache = {}

# --- HOJAS DISPONIBLES ---
SHEETS = {
    "Fase de grupos": ("resultados", "goleadores"),
    "Zona Campeonato": ("segunda_campeonato", "goleadores_campeonato"),
    "Zona Promoción": ("promocion_resultados", "promocion_goleadores")
}

# --- DATOS TORNEO ---
grupos = {
    "Grupo A": ["España", "México", "Australia", "Noruega", "Polonia", "Venezuela", "Ghana", "Albania"],
    "Grupo B": ["Francia", "Marruecos", "Austria", "Canadá", "Paraguay", "Nigeria", "Eslovenia", "Bosnia"],
    "Grupo C": ["Argentina", "Alemania", "Corea", "Suecia", "Escocia", "Costa de Marfil", "Islandia", "Angola"],
    "Grupo D": ["Inglaterra", "Uruguay", "Dinamarca", "Surinam", "Checa", "Cabo Verde", "Jamaica", "Finlandia"],
    "Grupo E": ["Portugal", "Colombia", "Senegal", "Serbia", "Grecia", "Rumania", "Chile", "Burkina Faso"],
    "Grupo F": ["Brasil", "Croacia", "Japón", "Ucrania", "Hungría", "Camerún", "Irlanda", "Guinea"],
    "Grupo G": ["Holanda", "Italia", "Ecuador", "Turquía", "Eslovaquia", "Mali", "Congo", "Haití"],
    "Grupo H": ["Bélgica", "Estados Unidos", "Suiza", "Gales", "Argelia", "Arabia", "Georgia", "Kosovo"]
}

zona_promocion = {
    "Zona A": ["España", "Surinam", "Senegal", "Eslovaquia"],
    "Zona B": ["México", "Cabo Verde", "Chile", "Bélgica"],
    "Zona C": ["Venezuela", "Angola", "Croacia", "Kosovo"],
    "Zona D": ["Austria", "Alemania", "Burkina Faso", "Ecuador"],
    "Zona E": ["Bosnia", "Jamaica", "Camerún", "Arabia"],
    "Zona F": ["Paraguay", "Islandia", "Guinea", "Haití"]
}

zona_campeonato = {
    "Zona A": ["Polonia", "Escocia", "Eslovenia", "Estados Unidos", "Congo"],
    "Zona B": ["Argelia", "Corea", "Irlanda", "Serbia", "Dinamarca"],
    "Zona C": ["Francia", "Países Bajos", "Australia", "Checa", "Grecia"],
    "Zona D": ["Costa de Marfil", "Inglaterra", "Gales", "Brasil", "Rumania"],
    "Zona E": ["Argentina", "Marruecos", "Georgia", "Ghana", "Japón"],
    "Zona F": ["Colombia", "Finlandia", "Nigeria", "Suiza", "Turquía"],
    "Zona G": ["Portugal", "Albania", "Hungría", "Italia", "Uruguay"],
    "Zona H": ["Noruega", "Canadá", "Ucrania", "Suecia", "Mali"]
}

fechas = [f"Fecha {i+1}" for i in range(7)]
fechas_promocion = [f"Fecha {i+1}" for i in range(4)]
fechas_campeonato = [f"Fecha {i+1}" for i in range(5)]


cpu = "CPU"



# --- BANDERAS ---
def bandera_html(nombre):
    especiales = {
        "Escocia": "https://flagcdn.com/w20/gb-sct.png",
        "Gales": "https://flagcdn.com/w20/gb-wls.png",
        "Inglaterra": "https://flagcdn.com/w20/gb-eng.png",
        "Kosovo": "https://flagcdn.com/w20/xk.png"
    }
    if nombre in especiales:
        return f"<img src='{especiales[nombre]}' width='20'> {nombre}"
    codigos = {
        "España":"es","México":"mx","Australia":"au","Noruega":"no","Polonia":"pl","Venezuela":"ve","Ghana":"gh","Albania":"al",
        "Francia":"fr","Marruecos":"ma","Austria":"at","Canadá":"ca","Paraguay":"py","Nigeria":"ng","Eslovenia":"si","Bosnia":"ba",
        "Argentina":"ar","Alemania":"de","Corea":"kr","Suecia":"se","Costa de Marfil":"ci","Islandia":"is","Angola":"ao",
        "Uruguay":"uy","Dinamarca":"dk","Surinam":"sr","Checa":"cz","Cabo Verde":"cv","Jamaica":"jm","Finlandia":"fi",
        "Portugal":"pt","Colombia":"co","Senegal":"sn","Serbia":"rs","Grecia":"gr","Rumania":"ro","Chile":"cl","Burkina Faso":"bf",
        "Brasil":"br","Croacia":"hr","Japón":"jp","Ucrania":"ua","Hungría":"hu","Camerún":"cm","Irlanda":"ie","Guinea":"gn",
        "Holanda":"nl","Italia":"it","Ecuador":"ec","Turquía":"tr","Eslovaquia":"sk","Mali":"ml","Congo":"cd","Haití":"ht",
        "Bélgica":"be","Estados Unidos":"us","Suiza":"ch","Argelia":"dz","Arabia":"sa","Georgia":"ge",
    }
    code = codigos.get(nombre)
    if code:
        return f"<img src='https://flagcdn.com/w20/{code}.png' width='20'> {nombre}"
    elif nombre == "CPU":
        return f"🤖 {nombre}"
    return nombre

# --- FUNCIONES ---
def load_sheet(res_name, gol_name):
    """Carga datos de Google Sheets con validación automática de columnas"""
    cache_key = f"{res_name}_{gol_name}"
    if cache_key in st.session_state.sheet_cache:
        return st.session_state.sheet_cache[cache_key]

    sh = client.open(SHEET_NAME)

    # --- RESULTADOS ---
    try:
        ws_r = sh.worksheet(res_name)
    except:
        ws_r = sh.add_worksheet(title=res_name, rows="1000", cols="10")

    # Verificar encabezados correctos
    expected_cols_r = ["Grupo", "Fecha", "Equipo", "GolesEquipo", "GolesCPU"]
    first_row_r = ws_r.row_values(1)
    if first_row_r != expected_cols_r:
        ws_r.clear()
        ws_r.append_row(expected_cols_r)

    # --- GOLEADORES ---
    try:
        ws_g = sh.worksheet(gol_name)
    except:
        ws_g = sh.add_worksheet(title=gol_name, rows="1000", cols="10")

    expected_cols_g = ["Equipo", "Jugador", "Goles", "Grupo", "Fecha"]
    first_row_g = ws_g.row_values(1)
    if first_row_g != expected_cols_g:
        ws_g.clear()
        ws_g.append_row(expected_cols_g)

    # --- Cargar DataFrames ---
    df_r = pd.DataFrame(ws_r.get_all_records())
    df_g = pd.DataFrame(ws_g.get_all_records())

    st.session_state.sheet_cache[cache_key] = (df_r, df_g, ws_r, ws_g)
    return df_r, df_g, ws_r, ws_g



def guardar_resultado(ws_results, grupo, fecha, equipo, goles_eq, goles_cpu):
    ws_results.append_row([grupo, fecha, equipo, goles_eq, goles_cpu])


def guardar_goleadores(ws_scorers, grupo, fecha, equipo, jugadores):
    for j in jugadores:
        ws_scorers.append_row([equipo, j, 1, grupo, fecha])


# --- APP ---
st.set_page_config(page_title="Torneo vs CPU", layout="centered")
st.title("🏆 Torneo vs CPU")

fase_sel = st.selectbox("Elegí la fase", list(SHEETS.keys()))
res_name, gol_name = SHEETS[fase_sel]

# Botón para refrescar manualmente
if st.button("🔄 Actualizar datos"):
    st.session_state.sheet_cache = {}
    st.rerun()

df_res, df_gol, ws_results, ws_scorers = load_sheet(res_name, gol_name)

tab1, tab2, tab3 = st.tabs(["📅 Fixture / Resultados", "📊 Tablas", "⚽ Goleadores"])

# --- TAB 1: FIXTURE / RESULTADOS ---
with tab1:
    # Detectar si es Zona Promoción
    if fase_sel == "Zona Promoción":
        grupos_activos = zona_promocion
        fechas_activas = fechas_promocion
    elif fase_sel == "Zona Campeonato":
        grupos_activos = zona_campeonato
        fechas_activas = fechas_campeonato
    else:
        grupos_activos = grupos
        fechas_activas = fechas


    grupo_sel = st.selectbox("Elegí un grupo", list(grupos_activos.keys()), key="grupo_fixture")
    fecha_sel = st.selectbox("Elegí una fecha", fechas_activas, key="fecha_fixture")

    st.markdown("---")

    for equipo in grupos_activos[grupo_sel]:
        titulo = f"{bandera_html(equipo)} vs {bandera_html(cpu)}"

    # Buscar si ya tiene resultado cargado
        match = df_res[
            (df_res["Grupo"].astype(str).str.strip().str.lower() == grupo_sel.lower())
            & (df_res["Fecha"].astype(str).str.strip().str.lower() == fecha_sel.lower())
            & (df_res["Equipo"].astype(str).str.strip().str.lower() == equipo.lower())
        ]


        if match.empty:
            goles_eq, goles_cpu, ya_cargado = 0, 0, False
        else:
            goles_eq = int(match.iloc[0].get("GolesEquipo", 0))
            goles_cpu = int(match.iloc[0].get("GolesCPU", 0))
            ya_cargado = True

    # Mostrar la fila (gris si ya cargado)
        st.markdown(
            f"<div style='background-color:{'#f0f0f0' if ya_cargado else 'transparent'};"
            f"padding:5px;border-radius:6px'><b>{titulo}</b></div>",
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([2, 1, 1])
        g_eq = col1.number_input(
            "Goles equipo", 0, 50, goles_eq,
            key=f"{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}_eq"
        )
        g_cpu = col2.number_input(
            "Goles CPU", 0, 50, goles_cpu,
            key=f"{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}_cpu"
        )

        if col3.button("💾", key=f"save_{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}"):
            if not ya_cargado:
                guardar_resultado(ws_results, grupo_sel, fecha_sel, equipo, g_eq, g_cpu)
                st.success(f"✅ Guardado: {equipo} {g_eq}-{g_cpu} CPU")
            else:
                st.warning("⚠️ Ya cargaste este partido.")

        with st.expander("Goleadores"):
    # Si el df_gol no tiene columnas (hoja vacía), evitar error
            if not all(c in df_gol.columns for c in ["Equipo", "Jugador", "Goles", "Grupo", "Fecha"]):
                 jugadores_guardados = ""
            else:
                gol_match = df_gol[
                    (df_gol["Equipo"] == equipo)
                    & (df_gol["Grupo"] == grupo_sel)
                    & (df_gol["Fecha"] == fecha_sel)
                ]
                jugadores_guardados = ", ".join(gol_match["Jugador"].tolist()) if not gol_match.empty else ""

            goles_txt = st.text_input(
                "Jugadores (separar por coma)",
                jugadores_guardados,
                key=f"gols_{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}",
            )

            if st.button("⚽ Guardar goleadores", key=f"save_gol_{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}"):
                jugadores = [j.strip() for j in goles_txt.split(",") if j.strip()]
                if jugadores:
                    guardar_goleadores(ws_scorers, grupo_sel, fecha_sel, equipo, jugadores)
                    st.success("✅ Goleadores guardados")



# --- TAB 2: TABLAS ---
# --- TAB 2: TABLAS ---
with tab2:
    st.subheader(f"📊 Tablas - {fase_sel}")

    # Detectar zona activa según la fase
    if fase_sel == "Zona Promoción":
        grupos_activos = zona_promocion
    elif fase_sel == "Zona Campeonato":
        grupos_activos = zona_campeonato
    else:
        grupos_activos = grupos

    grupo_tabla = st.selectbox("Elegí un grupo", list(grupos_activos.keys()), key="grupo_tabla")

    if not df_res.empty:
        # Crear estructura de estadísticas vacía
        stats = {eq: {"PJ": 0, "PG": 0, "PE": 0, "PP": 0, "GF": 0, "GC": 0, "Pts": 0}
                 for eq in grupos_activos[grupo_tabla]}

        # Filtrar por grupo actual (asegurando coincidencia de texto)
        for _, r in df_res[df_res["Grupo"].astype(str).str.strip().str.lower() == grupo_tabla.lower()].iterrows():
            eq, gf, gc = r["Equipo"], int(r["GolesEquipo"]), int(r["GolesCPU"])
            s = stats.get(eq)
            if s is not None:
                s["PJ"] += 1
                s["GF"] += gf
                s["GC"] += gc
                if gf > gc:
                    s["PG"] += 1
                    s["Pts"] += 3
                elif gf == gc:
                    s["PE"] += 1
                    s["Pts"] += 1
                else:
                    s["PP"] += 1

        # Crear DataFrame de tabla
        df = pd.DataFrame.from_dict(stats, orient="index")
        df["DG"] = df["GF"] - df["GC"]
        df = df.sort_values(by=["Pts", "DG", "GF"], ascending=[False, False, False]).reset_index().rename(columns={"index": "Equipo"})
        df.insert(0, "Pos", range(1, len(df) + 1))
        df["Equipo"] = df["Equipo"].apply(bandera_html)

        # Definir color según fase
        if fase_sel == "Zona Promoción":
            color = df["Pos"].apply(lambda p: "#2ecc71" if p <= 2 else "#e74c3c")
        elif fase_sel == "Zona Campeonato":
            color = df["Pos"].apply(lambda p: "#2ecc71" if p <= 3 else ("#e74c3c" if p in [4, 5] else "transparent"))
        else:
            color = df["Pos"].apply(lambda p: "#2ecc71" if p <= 5 else "#e74c3c")

        # Agregar barra de color lateral
        df.insert(0, " ", color.apply(lambda c: f"<div style='width:4px;height:20px;background-color:{c}'></div>"))

        tabla_html = df[[" ", "Pos", "Equipo", "Pts", "PJ", "PG", "PE", "PP", "GF", "GC", "DG"]].to_html(escape=False, index=False)
        st.markdown(tabla_html, unsafe_allow_html=True)

    else:
        st.info("Todavía no hay resultados cargados en esta fase.")


# --- TAB 3: GOLEADORES ---
with tab3:
    st.subheader(f"⚽ Goleadores - {fase_sel}")

    vista_sel = st.radio(
        "Ver:",
        ["Esta fase", "General"],
        horizontal=True,
        key="vista_goleadores"
    )

    if vista_sel == "General":
        # Unir los goleadores de todas las fases
        hojas = [
            ("resultados", "goleadores"),
            ("segunda_campeonato", "goleadores_campeonato"),
            ("segunda_promocion", "goleadores_promocion")
        ]
        frames = []
        for r, g in hojas:
            try:
                _, df_g, _, _ = load_sheet(r, g)  # acá está el cambio importante
                if not df_g.empty:
                    frames.append(df_g)
            except Exception as e:
                print("Error al leer hoja", g, e)
                continue

        if frames:
            df_all = pd.concat(frames, ignore_index=True)
            df_rank = (
                df_all.groupby(["Jugador", "Equipo"])["Goles"]
                .sum()
                .reset_index()
                .sort_values("Goles", ascending=False)
            )
            df_rank["Equipo"] = df_rank["Equipo"].apply(bandera_html)
            goleadores_html = df_rank.to_html(escape=False, index=False)
            st.markdown(goleadores_html, unsafe_allow_html=True)
        else:
            st.info("Todavía no hay goleadores cargados en ninguna fase.")
    else:
        # Solo los goleadores de la fase actual
        if not df_gol.empty:
            df_rank = (
                df_gol.groupby(["Jugador", "Equipo"])["Goles"]
                .sum()
                .reset_index()
                .sort_values("Goles", ascending=False)
            )
            df_rank["Equipo"] = df_rank["Equipo"].apply(bandera_html)
            goleadores_html = df_rank.to_html(escape=False, index=False)
            st.markdown(goleadores_html, unsafe_allow_html=True)
        else:
            st.info("Todavía no hay goleadores cargados en esta fase.")
