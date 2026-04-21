import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIG ---
SHEET_NAME = "Torneo CPU"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    dict(st.secrets["google_service_account"]), scope
)
client = gspread.authorize(creds)

# --- EQUIPOS ---
equipos = [
    "Argentina","Brasil","España","Francia","Italia","Alemania",
    "Portugal","Inglaterra","Holanda","Bélgica",
    "Uruguay","Colombia","México","Chile","Perú",
    "Estados Unidos","Canadá","Japón","Corea","Australia",
    "Marruecos","Nigeria","Senegal","Camerún","Ghana",
    "Croacia","Suiza","Dinamarca","Suecia","Noruega"
]

fechas = [f"Fecha {i+1}" for i in range(20)]
cpu = "CPU"

# --- BANDERAS ---
def bandera_html(nombre):
    codigos = {
        "Argentina":"ar","Brasil":"br","España":"es","Francia":"fr","Italia":"it","Alemania":"de",
        "Portugal":"pt","Inglaterra":"gb-eng","Holanda":"nl","Bélgica":"be",
        "Uruguay":"uy","Colombia":"co","México":"mx","Chile":"cl","Perú":"pe",
        "Estados Unidos":"us","Canadá":"ca","Japón":"jp","Corea":"kr","Australia":"au",
        "Marruecos":"ma","Nigeria":"ng","Senegal":"sn","Camerún":"cm","Ghana":"gh",
        "Croacia":"hr","Suiza":"ch","Dinamarca":"dk","Suecia":"se","Noruega":"no"
    }
    code = codigos.get(nombre)
    if code:
        return f"<img src='https://flagcdn.com/w20/{code}.png'> {nombre}"
    return nombre

# --- LOAD SHEET ---
def load_sheet():
    sh = client.open(SHEET_NAME)

    try:
        ws_r = sh.worksheet("liga_resultados")
    except:
        ws_r = sh.add_worksheet("liga_resultados", 1000, 10)
        ws_r.append_row(["Equipo","Fecha","GolesEquipo","GolesCPU"])

    try:
        ws_g = sh.worksheet("liga_goleadores")
    except:
        ws_g = sh.add_worksheet("liga_goleadores", 1000, 10)
        ws_g.append_row(["Equipo","Jugador","Goles","Fecha"])

    records_r = ws_r.get_all_records()
    records_g = ws_g.get_all_records()

    df_r = pd.DataFrame(records_r) if records_r else pd.DataFrame(columns=["Equipo","Fecha","GolesEquipo","GolesCPU"])
    df_g = pd.DataFrame(records_g) if records_g else pd.DataFrame(columns=["Equipo","Jugador","Goles","Fecha"])

    return df_r, df_g, ws_r, ws_g

# --- APP ---
st.set_page_config(layout="centered")
st.title("🏆 Liga vs CPU")

if st.button("🔄 Actualizar"):
    st.rerun()

df_res, df_gol, ws_r, ws_g = load_sheet()

tab1, tab2, tab3 = st.tabs(["📅 Partidos", "📊 Tabla", "⚽ Goleadores"])

# --- TAB 1 ---
with tab1:
    fecha_sel = st.selectbox("Fecha", fechas)

    faltan = len(equipos) - len(df_res[df_res["Fecha"] == fecha_sel])
    st.markdown(f"### 📊 {fecha_sel} — {faltan} sin cargar")

    total = len(equipos)
    cargados = len(df_res[df_res["Fecha"] == fecha_sel])
    st.progress(int((cargados/total)*100))

    for eq in equipos:
        match = df_res[(df_res["Equipo"] == eq) & (df_res["Fecha"] == fecha_sel)]
        ya = not match.empty

        g1 = int(match.iloc[0]["GolesEquipo"]) if ya else 0
        g2 = int(match.iloc[0]["GolesCPU"]) if ya else 0

        color = "#d4edda" if ya else "#ffe6e6"
        borde = "#28a745" if ya else "#dc3545"

        st.markdown(f"""
        <div style='background:{color};border-left:6px solid {borde};padding:8px;border-radius:8px;margin-bottom:5px'>
        <b>{bandera_html(eq)} vs 🤖 CPU</b>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1,1,1])
        g_eq = c1.number_input("",0,20,g1,key=f"{eq}_{fecha_sel}_1")
        g_cpu = c2.number_input("",0,20,g2,key=f"{eq}_{fecha_sel}_2")

        if c3.button("💾", key=f"{eq}_{fecha_sel}_save"):
            if not ya:
                ws_r.append_row([eq, fecha_sel, g_eq, g_cpu])
                st.success("Guardado")

        # --- GOLEADORES ---
        with st.expander("⚽ Goleadores"):

            jugadores_existentes = df_gol[df_gol["Equipo"]==eq]["Jugador"].dropna().unique().tolist()

            busqueda = st.text_input("Buscar jugador", key=f"bus_{eq}_{fecha_sel}")

            sugerencias = [j for j in jugadores_existentes if busqueda.lower() in j.lower()] if busqueda else jugadores_existentes
            sugerencias = sugerencias[:5]

            col1, col2, col3 = st.columns([2,1,1])

            jugador_sel = col1.selectbox("Sugerencias", [""]+sugerencias, key=f"sug_{eq}_{fecha_sel}")
            jugador_final = jugador_sel if jugador_sel else busqueda

            goles = col2.number_input("Goles",1,10,1,key=f"gol_{eq}_{fecha_sel}")

            if col3.button("⚽", key=f"golbtn_{eq}_{fecha_sel}"):
                if jugador_final:
                    jugador_final = jugador_final.strip().title()
                    for _ in range(goles):
                        ws_g.append_row([eq, jugador_final, 1, fecha_sel])
                    st.success(f"{jugador_final} x{goles}")

# --- TAB 2 ---
with tab2:
    stats = {e:{"PJ":0,"Pts":0,"GF":0,"GC":0} for e in equipos}

    for _,r in df_res.iterrows():
        eq = r["Equipo"]
        gf = int(r["GolesEquipo"])
        gc = int(r["GolesCPU"])

        s = stats[eq]
        s["PJ"]+=1
        s["GF"]+=gf
        s["GC"]+=gc

        if gf>gc: s["Pts"]+=3
        elif gf==gc: s["Pts"]+=1

    df = pd.DataFrame.from_dict(stats,orient="index")
    df["DG"]=df["GF"]-df["GC"]

    df = df.sort_values(["Pts","DG","GF"],ascending=False)
    df = df.reset_index().rename(columns={"index":"Equipo"})
    df.insert(0,"Pos",range(1,len(df)+1))

    # Colores
    def color_bar(pos):
        if pos == 1:
            return "#2ecc71"
        elif pos >= len(df)-2:
            return "#e74c3c"
        return "transparent"

    df.insert(0," ", df["Pos"].apply(lambda p: f"<div style='width:4px;height:20px;background:{color_bar(p)}'></div>"))

    st.markdown(df.to_html(escape=False,index=False), unsafe_allow_html=True)

# --- TAB 3 ---
with tab3:
    if not df_gol.empty:
        df_rank = df_gol.groupby(["Jugador","Equipo"])["Goles"].sum().reset_index()
        df_rank = df_rank.sort_values("Goles",ascending=False)

        st.markdown("## 🔥 Top 10")
        top10 = df_rank.head(10)
        st.dataframe(top10, use_container_width=True)

        st.markdown("## 📋 Todos")
        st.dataframe(df_rank, use_container_width=True)
    else:
        st.info("Sin goleadores aún")
