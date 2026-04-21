import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit.components.v1 as components

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

df_res, df_gol, ws_r, ws_g = load_sheet()

tab1, tab2, tab3 = st.tabs(["📅 Partidos", "📊 Tabla", "⚽ Goleadores"])

# =========================
# 📊 TABLA (FIX REAL)
# =========================
with tab2:
    if df_res.empty:
        st.info("Sin datos")
    else:
        stats = {e:{"PJ":0,"Pts":0,"GF":0,"GC":0} for e in equipos}

        for _, r in df_res.iterrows():
            eq = str(r["Equipo"]).strip()
            if eq not in stats:
                continue

            gf = int(r["GolesEquipo"])
            gc = int(r["GolesCPU"])

            stats[eq]["PJ"] += 1
            stats[eq]["GF"] += gf
            stats[eq]["GC"] += gc

            if gf > gc:
                stats[eq]["Pts"] += 3
            elif gf == gc:
                stats[eq]["Pts"] += 1

        df = pd.DataFrame.from_dict(stats, orient="index")
        df["DG"] = df["GF"] - df["GC"]
        df = df.sort_values(["Pts","DG","GF"], ascending=False)
        df = df.reset_index().rename(columns={"index":"Equipo"})
        df.insert(0,"Pos", range(1,len(df)+1))

        filas = ""
        for _, r in df.iterrows():
            pos = r["Pos"]

            if pos == 1:
                bg = "#d4edda"
            elif pos >= len(df)-2:
                bg = "#f8d7da"
            else:
                bg = "white"

            filas += f"""
            <tr style='background:{bg}'>
                <td>{pos}</td>
                <td>{bandera_html(r['Equipo'])}</td>
                <td>{r['Pts']}</td>
                <td>{r['PJ']}</td>
                <td>{r['GF']}</td>
                <td>{r['GC']}</td>
                <td>{r['DG']}</td>
            </tr>
            """

        html = f"""
        <html>
        <body style="color:black;">
        <table style="width:100%;border-collapse:collapse;">
        <tr>
        <th>#</th><th>Equipo</th><th>Pts</th><th>PJ</th><th>GF</th><th>GC</th><th>DG</th>
        </tr>
        {filas}
        </table>
        </body>
        </html>
        """

        components.html(html, height=800)

# =========================
# ⚽ GOLEADORES (CON BANDERAS)
# =========================
with tab3:
    if df_gol.empty:
        st.info("Sin goleadores")
    else:
        df_rank = df_gol.groupby(["Jugador","Equipo"])["Goles"].sum().reset_index()
        df_rank = df_rank.sort_values("Goles", ascending=False)

        filas = ""
        for _, r in df_rank.iterrows():
            filas += f"""
            <tr>
                <td>{r['Jugador']}</td>
                <td>{bandera_html(r['Equipo'])}</td>
                <td>⚽ {r['Goles']}</td>
            </tr>
            """

        html = f"""
        <html>
        <body style="color:black;">
        <table style="width:100%;">
        <tr><th>Jugador</th><th>Equipo</th><th>Goles</th></tr>
        {filas}
        </table>
        </body>
        </html>
        """

        components.html(html, height=600)
