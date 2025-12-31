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
.main { background:#f5f7fb; }

section[data-testid="stSidebar"] {
    background:#ffffff;
    border-right:1px solid #e5e7eb;
}

.hero {
    background: linear-gradient(135deg,#0f172a,#020617);
    color:white;
    padding:52px;
    border-radius:30px;
    margin-bottom:40px;
}

.hero h1 { font-size:44px; margin-bottom:8px; }
.hero p { font-size:17px; color:#c7d2fe; max-width:900px; }

.card {
    background:white;
    padding:30px;
    border-radius:22px;
    box-shadow:0 18px 45px rgba(0,0,0,0.08);
    margin-bottom:28px;
}

.soft {
    background:#eef2ff;
    padding:22px;
    border-radius:18px;
    margin-bottom:22px;
}

.metric { font-size:38px; font-weight:800; }
.label { color:#64748b; font-size:14px; }

.ok { color:#16a34a; font-weight:800; }
.warn { color:#ca8a04; font-weight:800; }
.bad { color:#dc2626; font-weight:800; }

.download {
    background: linear-gradient(135deg,#1e293b,#020617);
    color:white;
    padding:36px;
    border-radius:26px;
    margin-top:24px;
}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.image("brin_logo.png", width=150)   # LOGO BRIN HANYA DI SINI
    st.markdown("## M-EMS")
    st.caption("Marine Engine Monitoring System")

    menu = option_menu(
        None,
        ["Home","IoT Monitor","Chart","ReadMe","About"],
        icons=["house","speedometer2","bar-chart","journal-text","person"],
        default_index=0
    )

# ================= DATA SOURCE =================
SHEET_ID = "1BX9h3qVC0NA41bi0oMQK3GsvdOjxOBkThQRJobpmeD0"
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

df = pd.DataFrame(sheet.get_all_records())
df.columns = df.columns.str.lower().str.strip()
df["waktu"] = pd.to_datetime(df["waktu"], errors="coerce")
df["oli"] = df["oli"].replace({"NORMAL":1,"DROP":0})

for c in ["suhu","getaran","oli","health"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df.dropna()
last = df.iloc[-1]

# ================= STATUS =================
def status(v,l,h):
    if v<l: return "NORMAL","ok"
    elif v<h: return "WASPADA","warn"
    else: return "BAHAYA","bad"

s_stat,s_cls = status(last["suhu"],70,90)
g_stat,g_cls = status(last["getaran"],3,6)
o_stat,o_cls = ("NORMAL","ok") if last["oli"]==1 else ("DROP","bad")

# ================= HOME =================
if menu=="Home":
    st.markdown("""
    <div class="hero">
        <h1>M-EMS</h1>
        <h3>Marine Engine Monitoring System</h3>
        <p>
        M-EMS merupakan platform pemantauan kondisi mesin kapal berbasis
        Internet of Things (IoT) yang dikembangkan untuk mendukung
        keselamatan operasional, efisiensi energi, serta pemeliharaan
        prediktif pada sektor transportasi laut.
        </p>
    </div>
    """, unsafe_allow_html=True)

    a,b,c,d = st.columns(4)
    a.markdown(f"<div class='card'><div class='label'>Suhu Mesin</div><div class='metric'>{last['suhu']} °C</div><span class='{s_cls}'>{s_stat}</span></div>",unsafe_allow_html=True)
    b.markdown(f"<div class='card'><div class='label'>Getaran Mesin</div><div class='metric'>{last['getaran']}</div><span class='{g_cls}'>{g_stat}</span></div>",unsafe_allow_html=True)
    c.markdown(f"<div class='card'><div class='label'>Tekanan Oli</div><div class='metric'>{'NORMAL' if last['oli']==1 else 'DROP'}</div><span class='{o_cls}'>{o_stat}</span></div>",unsafe_allow_html=True)
    d.markdown(f"<div class='card'><div class='label'>Health Index</div><div class='metric'>{last['health']}</div></div>",unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
    <b>Ringkasan Kondisi Sistem</b><br><br>
    Kondisi mesin dievaluasi menggunakan pendekatan multi-parameter
    yang mencakup suhu, getaran, dan tekanan oli.
    Kombinasi parameter ini memberikan gambaran menyeluruh
    mengenai performa dan tingkat keandalan mesin kapal
    pada kondisi operasional terkini.
    </div>
    """, unsafe_allow_html=True)

# ================= IOT MONITOR =================
elif menu=="IoT Monitor":
    st.header("📡 Real-Time Engine Monitoring")

    x,y,z = st.columns(3)

    x.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number",
        value=last["suhu"],
        title={"text":"Suhu Mesin (°C)"},
        gauge={"axis":{"range":[0,120]}}
    )),use_container_width=True)
    x.markdown("""
    <div class="soft">
    Parameter suhu digunakan untuk memantau beban termal mesin.
    Peningkatan suhu yang tidak wajar dapat mengindikasikan
    kegagalan sistem pendinginan atau pembakaran yang tidak optimal.
    </div>
    """,unsafe_allow_html=True)

    y.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number",
        value=last["getaran"],
        title={"text":"Getaran Mesin"},
        gauge={"axis":{"range":[0,10]}}
    )),use_container_width=True)
    y.markdown("""
    <div class="soft">
    Getaran mencerminkan kondisi mekanis mesin.
    Nilai getaran tinggi berpotensi menandakan keausan komponen,
    misalignment, atau ketidakseimbangan mekanis.
    </div>
    """,unsafe_allow_html=True)

    z.plotly_chart(go.Figure(go.Indicator(
        mode="gauge+number",
        value=last["oli"],
        title={"text":"Tekanan Oli"},
        gauge={"axis":{"range":[0,1]}}
    )),use_container_width=True)
    z.markdown("""
    <div class="soft">
    Tekanan oli berfungsi memastikan pelumasan optimal.
    Kondisi DROP meningkatkan risiko gesekan berlebih
    dan kerusakan permanen pada komponen mesin.
    </div>
    """,unsafe_allow_html=True)

# ================= CHART =================
elif menu=="Chart":
    st.header("📈 Historical Performance Analysis")

    p = st.selectbox("Pilih Parameter Analisis",
                     ["suhu","getaran","oli","health"])

    fig = px.line(df, x="waktu", y=p, markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div class="card">
    Analisis historis digunakan untuk mengidentifikasi tren jangka panjang,
    fluktuasi abnormal, serta indikasi awal degradasi performa mesin.
    Data ini menjadi dasar pengambilan keputusan pemeliharaan
    dan pengembangan model machine learning.
    </div>
    """,unsafe_allow_html=True)

# ================= README =================
elif menu=="ReadMe":
    st.header("📘 System Documentation")

    st.markdown("""
    **Latar Belakang**  
    Sistem monitoring mesin kapal konvensional masih bersifat reaktif
    dan bergantung pada inspeksi manual, sehingga risiko kegagalan
    mesin sering terdeteksi terlambat.

    **Research Gap**  
    Diperlukan platform riset yang mampu mengintegrasikan
    akuisisi data sensor, visualisasi real-time, dan analisis historis
    dalam satu sistem terpadu.

    **Tujuan Sistem**  
    Mengembangkan sistem monitoring mesin kapal berbasis IoT
    yang mampu menyajikan informasi kondisi mesin secara real-time
    dan mendukung pemeliharaan prediktif berbasis data.

    **Arsitektur Sistem**  
    Sensor → ESP32 → MQTT / Node-RED → Cloud Storage →
    Dashboard Streamlit → Analisis Data → Keputusan Pemeliharaan.

    **Kontribusi Sistem**  
    M-EMS menyediakan basis data historis, visualisasi interaktif,
    dan indikator kesehatan mesin sebagai fondasi riset lanjutan.
    """)

    st.markdown("""
    <div class="download">
    <h3>📥 Akses Data & Output Sistem</h3>
    <p>
    Dataset historis yang dihasilkan oleh M-EMS dapat digunakan
    untuk analisis lanjutan, validasi model, dan pengembangan
    metode machine learning.
    </p>
    </div>
    """, unsafe_allow_html=True)

    st.download_button(
        "⬇️ Download Dataset Sensor (CSV)",
        df.to_csv(index=False),
        "m_ems_dataset.csv",
        "text/csv"
    )

# ================= ABOUT (TIDAK DIUBAH) =================
elif menu=="About":
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
