import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="M-EMS | Marine Engine Monitoring System",
    layout="wide"
)
st_autorefresh(interval=60_000, key="refresh")

# ================= STYLE =================
st.markdown("""
<style>
.main { background-color: #f5f6fa; }

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e5e7eb;
}

.card {
    background-color: white;
    padding: 26px;
    border-radius: 18px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.08);
    margin-bottom: 22px;
    border-left: 6px solid #991b1b;
}

.title-big {
    font-size: 42px;
    font-weight: 900;
    color: #991b1b;
    letter-spacing: 0.5px;
}

.subtitle {
    color: #6b7280;
    font-size: 17px;
}

.metric {
    font-size: 34px;
    font-weight: 800;
}

.label {
    color: #9ca3af;
    font-size: 14px;
}

.watermark {
    text-align:center;
    margin-top:60px;
    margin-bottom:25px;
    color:#9ca3af;
    font-size:13px;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.image("brin_logo.png", use_container_width=True)
    st.markdown("## M-EMS")
    st.caption("Marine Engine Monitoring System")

    menu = option_menu(
        None,
        ["Home", "IoT Monitor", "Chart", "ReadMe", "About"],
        icons=["house", "speedometer2", "bar-chart", "journal-text", "person"],
        default_index=0,
        styles={
            "nav-link": {"font-size": "15px", "padding": "12px"},
            "nav-link-selected": {
                "background-color": "#991b1b",
                "color": "white",
                "font-weight": "700",
            },
        },
    )

# ================= HEADER =================
st.markdown("""
<div>
  <h1 class="title-big">🚢 M-EMS</h1>
  <p class="subtitle">Marine Engine Monitoring System</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ================= DATA SOURCE =================
SHEET_ID = "1BX9h3qVC0NA41bi0oMQK3GsvdOjxOBkThQRJobpmeD0"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())
except Exception:
    df = pd.read_csv("backup_data.csv")
    st.warning("⚠️ Mode offline: menggunakan data cadangan")

# ================= PREPROCESS =================
df.columns = df.columns.str.lower().str.strip()
df["waktu"] = pd.to_datetime(df["waktu"], errors="coerce")

for c in ["suhu", "getaran", "oli", "health"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna()
last = df.iloc[-1]

# ================= STATUS LOGIC =================
def overall_status(row):
    if row["suhu"] < 60 and row["getaran"] < 1.2 and row["oli"] == 1:
        return "AMAN", "#15803d"
    elif row["suhu"] < 80 and row["getaran"] < 2.0:
        return "WASPADA", "#f59e0b"
    else:
        return "BAHAYA", "#dc2626"

status_text, status_color = overall_status(last)

# ================= HOME =================
if menu == "Home":
    st.markdown("<div class='title-big'>System Overview</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.image("alat_mems.jpg", use_container_width=True)

    with c2:
        st.markdown("""
        <div class="card">
        M-EMS merupakan platform pemantauan kondisi mesin kapal berbasis
        Internet of Things (IoT) yang dirancang untuk mendukung keselamatan
        operasional, efisiensi energi, serta pengembangan pemeliharaan
        prediktif berbasis data melalui integrasi sensor, sistem komunikasi,
        dan analisis data terpusat.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📊 Status Operasional Terkini")

    a,b,c,d = st.columns(4)
    a.markdown(f"<div class='card'><div class='label'>Suhu Mesin</div><div class='metric'>{last['suhu']:.1f} °C</div></div>", unsafe_allow_html=True)
    b.markdown(f"<div class='card'><div class='label'>Getaran Mesin</div><div class='metric'>{last['getaran']:.2f}</div></div>", unsafe_allow_html=True)
    c.markdown(f"<div class='card'><div class='label'>Tekanan Oli</div><div class='metric'>{'ON' if last['oli']==1 else 'OFF'}</div></div>", unsafe_allow_html=True)
    d.markdown(f"<div class='card'><div class='label'>Health Index</div><div class='metric'>{int(last['health'])}</div></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card" style="text-align:center;border-left:10px solid {status_color};">
        <div class="label">Status Operasional Mesin</div>
        <div style="font-size:46px;font-weight:900;color:{status_color};">
            {status_text}
        </div>
        <p style="color:#6b7280;">
            Status ditentukan berdasarkan evaluasi suhu mesin,
            tingkat getaran, dan kondisi sistem pelumasan.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ================= IOT MONITOR =================
elif menu == "IoT Monitor":
    st.markdown("<div class='title-big'>Real-Time IoT Monitoring</div>", unsafe_allow_html=True)

    a,b,c = st.columns(3)

    a.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number",
        value=last["suhu"],
        title={"text":"Suhu Mesin (°C)"},
        gauge={"axis":{"range":[0,120]},
               "steps":[
                   {"range":[0,60],"color":"#15803d"},
                   {"range":[60,80],"color":"#f59e0b"},
                   {"range":[80,120],"color":"#dc2626"}
               ]}
    )), use_container_width=True)

    b.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number",
        value=last["getaran"],
        title={"text":"Getaran Mesin"},
        gauge={"axis":{"range":[0,3]},
               "steps":[
                   {"range":[0,1.2],"color":"#15803d"},
                   {"range":[1.2,2.0],"color":"#f59e0b"},
                   {"range":[2.0,3.0],"color":"#dc2626"}
               ]}
    )), use_container_width=True)

    c.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number",
        value=last["oli"],
        title={"text":"Tekanan Oli"},
        gauge={"axis":{"range":[0,1]},
               "steps":[
                   {"range":[0,0.5],"color":"#dc2626"},
                   {"range":[0.5,1],"color":"#15803d"}
               ]}
    )), use_container_width=True)

# ================= CHART =================
elif menu == "Chart":
    st.markdown("<div class='title-big'>Historical Data Analysis</div>", unsafe_allow_html=True)

    param = st.selectbox(
        "Pilih Parameter",
        ["suhu","getaran","oli","health"]
    )

    fig = px.line(
        df,
        x="waktu",
        y=param,
        markers=True,
        title=f"Tren Historis {param.upper()}"
    )
    st.plotly_chart(fig, use_container_width=True)

# ================= README =================
elif menu == "ReadMe":
    st.markdown("<div class='title-big'>System Documentation</div>", unsafe_allow_html=True)

    t1,t2,t3,t4 = st.tabs(["Overview","Architecture","IoT Pipeline","Parameter & Status"])

    with t1:
        st.markdown("""
        <div class="card">
        M-EMS dikembangkan sebagai sistem pemantauan mesin kapal
        berbasis IoT yang mendukung pemantauan real-time, analisis
        historis, dan pengambilan keputusan pemeliharaan berbasis data.
        </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown("""
        <div class="card">
        Arsitektur sistem terdiri dari sensor mesin, ESP32 sebagai
        node akuisisi data, protokol MQTT, Node-RED untuk routing data,
        penyimpanan cloud, dan dashboard Streamlit.
        </div>
        """, unsafe_allow_html=True)

    with t3:
        st.markdown("""
        <div class="card">
        Data sensor dikirim secara periodik, diproses, divalidasi,
        dan divisualisasikan. Data historis menjadi dasar analisis
        tren dan pengembangan model machine learning.
        </div>
        """, unsafe_allow_html=True)

    with t4:
        st.markdown("""
        <div class="card">
        <b>KONDISI AMAN</b><br>
        Suhu &lt; 60°C, Getaran &lt; 1.2, Oil = ON, Drop_ratio &lt; 0.05<br><br>

        <b>KONDISI WASPADA</b><br>
        Suhu 60–80°C atau Getaran 1.2–2.0 atau Drop_ratio 0.05–0.2<br><br>

        <b>KONDISI BAHAYA</b><br>
        Suhu ≥ 80°C, Getaran ≥ 2.0, Oil OFF terlalu lama, Drop_ratio ≥ 0.2
        </div>
        """, unsafe_allow_html=True)

    st.download_button(
        "⬇️ Download Dataset (CSV)",
        df.to_csv(index=False),
        "m_ems_dataset.csv",
        "text/csv"
    )

# ================= ABOUT (JANGAN DIUBAH) =================
elif menu == "About":
    st.subheader("👤 About")
    st.markdown("""
Nama Alat  
M-EMS (Marine Engine Monitoring System)

**Pengembang**  
Arin Nur Damayanti  
Mahasiswa Teknik Telekomunikasi  
Institut Teknologi Sumatera

**Pembimbing**  
Fauzi Dwi Setiawan, S.Si., M.Sc  
Aji Pamungkas Tri Nurcahyo, S.T., M.Sc

**Afiliasi Riset**  
Kelompok Riset Pemodelan Sarana Transportasi Berkelanjutan  
Pusat Riset Teknologi Transportasi  
Badan Riset dan Inovasi Nasional (BRIN)
""")

# ================= WATERMARK =================
st.markdown("""
<div class="watermark">
© 2025 Marine Engine Monitoring System (M-EMS) —  
Pusat Riset Teknologi Transportasi, Badan Riset dan Inovasi Nasional (BRIN)
</div>
""", unsafe_allow_html=True)
