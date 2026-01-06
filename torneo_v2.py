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
    "Segunda fase - Campeonato": ("segunda_campeonato", "goleadores_campeonato"),
    "Segunda fase - Promoción": ("segunda_promocion", "goleadores_promocion")
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
fechas = [f"Fecha {i+1}" for i in range(7)]
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
    """Carga datos de Google Sheets con caché"""
    cache_key = f"{res_name}_{gol_name}"
    if cache_key in st.session_state.sheet_cache:
        return st.session_state.sheet_cache[cache_key]

    sh = client.open(SHEET_NAME)
    # cargar resultados
    try:
        ws_r = sh.worksheet(res_name)
    except:
        ws_r = sh.add_worksheet(title=res_name, rows="1000", cols="10")
        ws_r.append_row(["Grupo", "Fecha", "Equipo", "GolesEquipo", "GolesCPU"])
    # cargar goleadores
    try:
        ws_g = sh.worksheet(gol_name)
    except:
        ws_g = sh.add_worksheet(title=gol_name, rows="1000", cols="10")
        ws_g.append_row(["Equipo", "Jugador", "Goles", "Grupo", "Fecha"])

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
    grupo_sel = st.selectbox("Elegí un grupo", list(grupos.keys()), key="grupo_fixture")
    fecha_sel = st.selectbox("Elegí una fecha", fechas, key="fecha_fixture")
    st.markdown("---")

    for equipo in grupos[grupo_sel]:
        titulo = f"{bandera_html(equipo)} vs {bandera_html(cpu)}"
        match = df_res[(df_res["Grupo"]==grupo_sel) & (df_res["Fecha"]==fecha_sel) & (df_res["Equipo"]==equipo)]
        ya_cargado = not match.empty
        goles_eq = int(match.iloc[0]["GolesEquipo"]) if ya_cargado else 0
        goles_cpu = int(match.iloc[0]["GolesCPU"]) if ya_cargado else 0

        st.markdown(f"<div style='background-color:{'#f0f0f0' if ya_cargado else 'transparent'};"
                    f"padding:5px;border-radius:6px'><b>{titulo}</b></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2,1,1])
        g_eq = col1.number_input("Goles equipo", 0, 50, goles_eq, key=f"{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}_eq")
        g_cpu = col2.number_input("Goles CPU", 0, 50, goles_cpu, key=f"{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}_cpu")
        if col3.button("💾", key=f"save_{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}"):
            if not ya_cargado:
                guardar_resultado(ws_results, grupo_sel, fecha_sel, equipo, g_eq, g_cpu)
                st.success(f"✅ Guardado: {equipo} {g_eq}-{g_cpu} CPU")
            else:
                st.warning("⚠️ Ya cargaste este partido.")
        with st.expander("Goleadores"):
            gol_match = df_gol[(df_gol["Equipo"]==equipo) & (df_gol["Grupo"]==grupo_sel) & (df_gol["Fecha"]==fecha_sel)]
            jugadores_guardados = ", ".join(gol_match["Jugador"].tolist()) if not gol_match.empty else ""
            goles_txt = st.text_input("Jugadores (separar por coma)", jugadores_guardados,
                                      key=f"gols_{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}")
            if st.button("⚽ Guardar goleadores", key=f"save_gol_{fase_sel}_{grupo_sel}_{fecha_sel}_{equipo}"):
                jugadores = [j.strip() for j in goles_txt.split(",") if j.strip()]
                if jugadores:
                    guardar_goleadores(ws_scorers, grupo_sel, fecha_sel, equipo, jugadores)
                    st.success("✅ Goleadores guardados")

# --- TAB 2: TABLAS ---
with tab2:
    st.subheader(f"📊 Tablas - {fase_sel}")
    grupo_tabla = st.selectbox("Elegí un grupo", list(grupos.keys()), key="grupo_tabla")
    if not df_res.empty:
        stats = {eq: {"PJ":0,"PG":0,"PE":0,"PP":0,"GF":0,"GC":0,"Pts":0} for eq in grupos[grupo_tabla]}
        for _,r in df_res[df_res["Grupo"]==grupo_tabla].iterrows():
            eq, gf, gc = r["Equipo"], r["GolesEquipo"], r["GolesCPU"]
            s = stats[eq]
            s["PJ"]+=1; s["GF"]+=gf; s["GC"]+=gc
            if gf>gc: s["PG"]+=1; s["Pts"]+=3
            elif gf==gc: s["PE"]+=1; s["Pts"]+=1
            else: s["PP"]+=1
        df = pd.DataFrame.from_dict(stats, orient="index")
        df["DG"]=df["GF"]-df["GC"]
        df = df.sort_values(by=["Pts","DG","GF"],ascending=[False,False,False]).reset_index().rename(columns={"index":"Equipo"})
        df.insert(0,"Pos",range(1,len(df)+1))
        df["Equipo"] = df["Equipo"].apply(bandera_html)

        # barra lateral de color
        df.insert(0," ", df["Pos"].apply(lambda p: f"<div style='width:4px;height:20px;background-color:{'#2ecc71' if p<=5 else '#e74c3c'}'></div>"))
        tabla_html = df[[" ","Pos","Equipo","Pts","PJ","PG","PE","PP","GF","GC","DG"]].to_html(escape=False,index=False)
        st.markdown(tabla_html, unsafe_allow_html=True)
    else:
        st.info("Todavía no hay resultados cargados en esta fase.")

# --- TAB 3: GOLEADORES ---
with tab3:
    st.subheader(f"⚽ Goleadores - {fase_sel}")
    if not df_gol.empty:
        df_rank = df_gol.groupby(["Jugador","Equipo"])["Goles"].sum().reset_index().sort_values("Goles",ascending=False)
        df_rank["Equipo"] = df_rank["Equipo"].apply(bandera_html)
        goleadores_html = df_rank.to_html(escape=False,index=False)
        st.markdown(goleadores_html, unsafe_allow_html=True)
    else:
        st.info("Todavía no hay goleadores cargados en esta fase.")
