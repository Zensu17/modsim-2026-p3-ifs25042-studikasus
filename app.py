import streamlit as st
import simpy
import random
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# =========================
# KONFIGURASI SISTEM
# =========================
TOTAL_MEJA = 60
MHS_PER_MEJA = 3
TOTAL_OMPRENG = TOTAL_MEJA * MHS_PER_MEJA
TOTAL_PETUGAS = 7

# Custom CSS agar adaptif terhadap Dark/Light Mode
st.markdown("""
    <style>
    .stMetric {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    /* Memastikan gambar responsif */
    .header-img {
        width: 100%;
        border-radius: 15px;
        margin-bottom: 20px;
        object-fit: cover;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# ENGINE SIMULASI
# =========================
class SistemPiketDES:
    def __init__(self, env, p_lauk, p_angkat, p_nasi):
        self.env = env
        self.lauk = simpy.Resource(env, capacity=p_lauk)
        self.angkat = simpy.Resource(env, capacity=p_angkat)
        self.nasi = simpy.Resource(env, capacity=p_nasi)
        self.data = []
        self.start_time = datetime.now().replace(hour=7, minute=0, second=0)

    def proses_ompreng(self, oid):
        t_datang = self.env.now
        
        # Logika antrean untuk setiap tahap
        # 1. Tahap Lauk
        with self.lauk.request() as req:
            yield req
            t_mulai_lauk = self.env.now
            yield self.env.timeout(random.uniform(30, 60))
        
        # 2. Tahap Angkat
        with self.angkat.request() as req:
            yield req
            t_mulai_angkat = self.env.now
            yield self.env.timeout(random.uniform(20, 60))
            
        # 3. Tahap Nasi
        with self.nasi.request() as req:
            yield req
            t_mulai_nasi = self.env.now
            yield self.env.timeout(random.uniform(30, 60))

        t_selesai = self.env.now
        
        self.data.append({
            "Ompreng ID": oid + 1,
            "Total Durasi": round(t_selesai - t_datang, 2),
            "Waktu Antre": round((t_selesai - t_datang) - ((t_selesai - t_mulai_nasi) + (t_mulai_nasi - t_mulai_angkat) + (t_mulai_angkat - t_mulai_lauk)), 2),
            "Selesai": self.start_time + timedelta(seconds=t_selesai)
        })

    def run(self):
        for i in range(TOTAL_OMPRENG):
            self.env.process(self.proses_ompreng(i))
            yield self.env.timeout(1.5) # Interval pengumpulan ompreng dari meja

# =========================
# UI STREAMLIT
# =========================
def main():
    # Render gambar header menggunakan Unsplash (Adaptive & High Quality)
    st.image("https://images.unsplash.com/photo-1547573854-74d2a71d0826?q=80&w=1200", use_container_width=True)
    
    st.title("🍱 Smart Simulation: IT Del")
    st.subheader("Optimasi Sistem Antrean Piket Makan")
    
    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Konfigurasi Petugas")
    st.sidebar.info(f"Total SDM Tersedia: **{TOTAL_PETUGAS} Orang**")
    
    p_lauk = st.sidebar.slider("Petugas Lauk", 1, 5, 2)
    p_angkat = st.sidebar.slider("Petugas Angkat", 1, 5, 2)
    
    sisa = TOTAL_PETUGAS - p_lauk - p_angkat
    
    if sisa < 1:
        st.sidebar.error("⚠️ Alokasi melebihi batas 7 petugas! Kurangi porsi pos lain.")
        p_nasi = 0
        ready = False
    else:
        p_nasi = sisa
        st.sidebar.success(f"✅ Petugas Nasi otomatis: **{p_nasi}**")
        ready = True

    btn_run = st.sidebar.button("🚀 Jalankan Simulasi", use_container_width=True)

    # --- MAIN UI ---
    if btn_run and ready:
        env = simpy.Environment()
        model = SistemPiketDES(env, p_lauk, p_angkat, p_nasi)
        env.process(model.run())
        
        with st.status("Mensimulasikan antrean...", expanded=True) as status:
            env.run()
            status.update(label="Simulasi Selesai!", state="complete", expanded=False)
            
        df = pd.DataFrame(model.data)

        # Dashboard Metrik
        m1, m2, m3 = st.columns(3)
        m1.metric("Rata-rata Waktu", f"{df['Total Durasi'].mean():.1f}s")
        m2.metric("Waktu Selesai", df["Selesai"].max().strftime("%H:%M:%S"))
        m3.metric("Bottleneck Index", f"{df['Waktu Antre'].mean():.1f}s")

        # Tabs untuk visualisasi
        tab_dist, tab_trend, tab_data = st.tabs(["📊 Distribusi", "📈 Tren Waktu", "📋 Data Lengkap"])

        with tab_dist:
            # Histogram dengan warna tema yang adaptif
            fig1 = px.histogram(
                df, x="Total Durasi", 
                title="Penyebaran Durasi Penyelesaian",
                color_discrete_sequence=['#00CC96'],
                template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
            )
            st.plotly_chart(fig1, use_container_width=True)

        with tab_trend:
            # Scatter plot untuk melihat lonjakan antrean
            fig2 = px.area(
                df, x="Ompreng ID", y="Waktu Antre",
                title="Analisis Penumpukan Antrean (Waktu Tunggu)",
                template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white"
            )
            st.plotly_chart(fig2, use_container_width=True)

        with tab_data:
            st.dataframe(df, use_container_width=True)
            
    else:
        # Tampilan Awal (Welcome Screen)
        st.info("Atur pembagian tugas pada sidebar di sebelah kiri, lalu tekan tombol **Jalankan Simulasi**.")
        
        with st.expander("📌 Informasi Parameter"):
            st.write(f"""
            - **Total Ompreng:** {TOTAL_OMPRENG} buah (60 meja × 3 mhs)
            - **Target SDM:** 7 Petugas
            - **Variabel Waktu:** Random Uniform (Sesuai standar operasional pelayanan makanan)
            """)

if __name__ == "__main__":
    main()