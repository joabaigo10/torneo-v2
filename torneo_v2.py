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
"Polonia","Irlanda","Checa","Rumania","Georgia","Turquía","Albania","Corea",
"Mali","Portugal","Escocia","Brasil","Japón","Marruecos","Noruega","Dinamarca",
"Suiza","Argentina","Francia","Inglaterra","Suecia","Costa de Marfil","Finlandia","Colombia",
"Canadá","Bosnia","Croacia","Gales","México","Países Bajos","Austria","Italia",
"Australia","Argelia","Arabia Saudita","Ucrania","Nigeria","Uruguay","Grecia","Congo",
"Serbia","Estados Unidos","Bélgica","Surinam","Ecuador","Hungría","Kosovo","Eslovaquia"
]

fechas = [f"Fecha {i+1}" for i in range(20)]

# --- BANDERAS ---
def bandera_html(nombre):
    codigos = {
        "Argentina":"ar","Brasil":"br","Francia":"fr","Italia":"it",
        "Portugal":"pt","Inglaterra":"gb-eng","Países Bajos":"nl","Bélgica":"be",
        "Colombia":"co","México":"mx","Estados Unidos":"us","Canadá":"ca",
        "Japón":"jp","Corea":"kr","Australia":"au","Marruecos":"ma",
        "Nigeria":"ng","Costa de Marfil":"ci","Croacia":"hr","Suiza":"ch",
        "Dinamarca":"dk","Suecia":"se","Noruega":"no","Polonia":"pl",
        "Irlanda":"ie","Checa":"cz","Rumania":"ro","Georgia":"ge",
        "Turquía":"tr","Albania":"al","Mali":"ml","Escocia":"gb-sct",
        "Gales":"gb-wls","Bosnia":"ba","Grecia":"gr","Congo":"cd",
        "Serbia":"rs","Ecuador":"ec","Hungría":"hu","Kosovo":"xk",
        "Eslovaquia":"sk","Austria":"at","Argelia":"dz","Arabia Saudita":"sa",
        "Ucrania":"ua","Uruguay":"uy","Surinam":"sr","Finlandia":"fi"
    }
    code = codigos.get(nombre)
    if code:
        return f"<img src='https://flagcdn.com/w20/{code}.png'> {nombre}"
    return nombre

# --- LOAD ---
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

    df_r = pd.DataFrame(ws_r.get_all_records())
    df_g = pd.DataFrame(ws_g.get_all_records())

    return df_r, df_g, ws_r, ws_g

# --- APP ---
st.set_page_config(layout="centered")
st.title("🏆 Liga vs CPU")

if st.button("🔄 Actualizar"):
    st.rerun()

df_res, df_gol, ws_r, ws_g = load_sheet()

tab1, tab2, tab3 = st.tabs(["📅 Partidos", "📊 Tabla", "⚽ Goleadores"])

# =========================
# 📅 PARTIDOS
# =========================
with tab1:
    fecha_sel = st.selectbox("Fecha", fechas)

    cargados = len(df_res[df_res["Fecha"] == fecha_sel]) if not df_res.empty else 0
    total = len(equipos)
    progreso = int((cargados/total)*100)

    st.markdown(f"### 📅 {fecha_sel}")
    st.progress(progreso)
    st.caption(f"{cargados}/{total} partidos cargados")

    for eq in equipos:
        match = df_res[(df_res["Equipo"] == eq) & (df_res["Fecha"] == fecha_sel)] if not df_res.empty else pd.DataFrame()
        ya = not match.empty

        g1 = int(match.iloc[0]["GolesEquipo"]) if ya else 0
        g2 = int(match.iloc[0]["GolesCPU"]) if ya else 0

        color = "#e8f5e9" if ya else "#ffebee"

        st.markdown(f"""
        <div style='background:{color};border-radius:12px;padding:10px;margin-bottom:8px;color:black;'>
        <b>{bandera_html(eq)} vs 🤖 CPU</b>
        <div style='font-size:18px;'><b>{g1} - {g2}</b></div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1,1,1])
        g_eq = c1.number_input("⚽",0,20,g1,key=f"{eq}_{fecha_sel}_1")
        g_cpu = c2.number_input("🤖",0,20,g2,key=f"{eq}_{fecha_sel}_2")

        if c3.button("Guardar", key=f"{eq}_{fecha_sel}"):
            if not ya:
                ws_r.append_row([eq, fecha_sel, g_eq, g_cpu])
                st.success("Guardado")

# =========================
# 📊 TABLA (FIX)
# =========================
with tab2:
    st.subheader("📊 Tabla de posiciones")

    columnas_ok = ["Equipo","Fecha","GolesEquipo","GolesCPU"]

    if df_res.empty or not all(col in df_res.columns for col in columnas_ok):
        st.info("Todavía no hay resultados cargados.")
    else:
        stats = {e:{"PJ":0,"Pts":0,"GF":0,"GC":0} for e in equipos}

        for _, r in df_res.iterrows():
            eq = str(r["Equipo"]).strip()

            if eq not in stats:
                continue

            gf = int(r["GolesEquipo"])
            gc = int(r["GolesCPU"])

            s = stats[eq]
            s["PJ"] += 1
            s["GF"] += gf
            s["GC"] += gc

            if gf > gc:
                s["Pts"] += 3
            elif gf == gc:
                s["Pts"] += 1

        df = pd.DataFrame.from_dict(stats, orient="index")
        df["DG"] = df["GF"] - df["GC"]

        df = df.sort_values(["Pts","DG","GF"], ascending=False)
        df = df.reset_index().rename(columns={"index":"Equipo"})
        df.insert(0,"Pos", range(1,len(df)+1))

        df["Equipo"] = df["Equipo"].apply(bandera_html)

        filas = []
        for _, row in df.iterrows():
            pos = row["Pos"]

            if pos == 1:
                fondo = "#d4edda"
            elif pos >= len(df)-2:
                fondo = "#f8d7da"
            else:
                fondo = "white"

            filas.append(f"""
            <tr style='background:{fondo}'>
                <td>{pos}</td>
                <td>{row['Equipo']}</td>
                <td>{row['Pts']}</td>
                <td>{row['PJ']}</td>
                <td>{row['GF']}</td>
                <td>{row['GC']}</td>
                <td>{row['DG']}</td>
            </tr>
            """)

        tabla_html = f"""
        <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;color:black;">
        <thead>
        <tr>
        <th>#</th><th>Equipo</th><th>Pts</th><th>PJ</th><th>GF</th><th>GC</th><th>DG</th>
        </tr>
        </thead>
        <tbody>
        {''.join(filas)}
        </tbody>
        </table>
        </div>
        """

        st.markdown(tabla_html, unsafe_allow_html=True)

# =========================
# ⚽ GOLEADORES
# =========================
with tab3:
    if not df_gol.empty:
        df_rank = df_gol.groupby(["Jugador","Equipo"])["Goles"].sum().reset_index()
        df_rank = df_rank.sort_values("Goles",ascending=False)

        st.markdown("## 🔥 Top 10")
        st.dataframe(df_rank.head(10), use_container_width=True)

        st.markdown("## 📋 Todos")
        st.dataframe(df_rank, use_container_width=True)
    else:
        st.info("Sin goleadores aún")
