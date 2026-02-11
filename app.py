import streamlit as st
import simpy
import random
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Simulasi Piket IT Del", 
    page_icon="🍱",                        
    layout="wide"                          
)

# ==========================================
# 2. CSS CUSTOM PREMIUM (BAHASA INDONESIA)
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Animasi Gradient Bergerak untuk Header */
    .hero-container {
        background: linear-gradient(-45deg, #00b4db, #0083b0, #0575e6, #021b79);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        padding: 50px 20px;
        border-radius: 25px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Kartu Informasi */
    .info-card {
        background: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 20px;
    }

    /* Styling Metrik agar lebih menonjol */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 20px !important;
        border: 1px solid rgba(128, 128, 128, 0.1);
        transition: 0.3s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #00b4db;
    }

    /* Tombol Kustom */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        background: linear-gradient(90deg, #00b4db 0%, #0083b0 100%);
        color: white;
        font-weight: 700;
        border: none;
        padding: 12px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 8px 20px rgba(0, 180, 219, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. ENGINE SIMULASI (DES)
# ==========================================
class SimulasiPiket:
    def __init__(self, env, p_lauk, p_angkat, p_nasi):
        self.env = env
        self.lauk = simpy.Resource(env, capacity=p_lauk)
        self.angkat = simpy.Resource(env, capacity=p_angkat)
        self.nasi = simpy.Resource(env, capacity=p_nasi)
        self.data = []
        self.waktu_mulai = datetime.now().replace(hour=12, minute=0, second=0)

    def alur_makan(self, id_ompreng):
        datang = self.env.now
        
        # 1. Antre Lauk
        with self.lauk.request() as req:
            yield req
            mulai_lauk = self.env.now
            yield self.env.timeout(random.uniform(25, 55))
        
        # 2. Antre Angkat
        with self.angkat.request() as req:
            yield req
            mulai_angkat = self.env.now
            yield self.env.timeout(random.uniform(15, 45))
            
        # 3. Antre Nasi
        with self.nasi.request() as req:
            yield req
            mulai_nasi = self.env.now
            yield self.env.timeout(random.uniform(30, 60))

        selesai = self.env.now
        durasi_total = selesai - datang
        waktu_murni = (selesai - mulai_nasi) + (mulai_nasi - mulai_angkat) + (mulai_angkat - mulai_lauk)
        tunggu = max(0, durasi_total - waktu_murni)

        self.data.append({
            "Ompreng": f"Unit-{id_ompreng+1:03d}",
            "Waktu Pelayanan (s)": round(durasi_total, 1),
            "Waktu Antre (s)": round(tunggu, 1),
            "Jam Selesai": (self.waktu_mulai + timedelta(seconds=selesai)).strftime("%H:%M:%S")
        })

    def jalankan(self, jumlah_ompreng):
        for i in range(jumlah_ompreng):
            self.env.process(self.alur_makan(i))
            yield self.env.timeout(1.5)

# ==========================================
# 4. ANTARMUKA PENGGUNA (UI)
# ==========================================
def main():
    # --- HEADER ---
    st.markdown("""
        <div class="hero-container">
            <h1 style="font-size: 3.5rem; margin-bottom: 5px;">🍱 Analisis Piket IT Del</h1>
            <p style="font-size: 1.3rem; opacity: 0.9; font-weight: 400;">
                Optimasi Sistem Antrean Makan Siang Mahasiswa secara Cerdas
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR KONFIGURASI ---
    with st.sidebar:
        st.markdown("### 🛠️ Pengaturan Staf")
        st.caption("Total staf tersedia: 7 orang")
        
        with st.container(border=True):
            st.markdown("**Alokasi Pos:**")
            st_lauk = st.slider("🍗 Petugas Lauk", 1, 5, 2)
            st_angkat = st.slider("🧺 Petugas Angkat", 1, 5, 2)
            
            sisa = 7 - st_lauk - st_angkat
            st_nasi = max(1, sisa)
            
            if sisa < 1:
                st.error("Kapasitas Penuh! (Maks 7)")
                siap = False
            else:
                st.success(f"🍚 Petugas Nasi: {st_nasi}")
                siap = True
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_simulasi = st.button("🚀 Jalankan Simulasi")
        st.divider()
        st.markdown("🔍 *Sistem ini memprediksi titik kemacetan (bottleneck) secara real-time.*")

    # --- KONTEN UTAMA ---
    if btn_simulasi and siap:
        env = simpy.Environment()
        sim = SimulasiPiket(env, st_lauk, st_angkat, st_nasi)
        env.process(sim.jalankan(180)) # Total 180 mahasiswa (60 meja x 3)
        
        with st.status("🔮 Menghitung probabilitas antrean...", expanded=False) as status:
            env.run()
            status.update(label="Analisis Selesai!", state="complete")
            
        df = pd.DataFrame(sim.data)

        # --- PANEL METRIK ---
        st.markdown("### 📊 Statistik Performa")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        avg_wait = df['Waktu Antre (s)'].mean()
        kpi1.metric("Rerata Layanan", f"{df['Waktu Pelayanan (s)'].mean():.1f}s")
        kpi2.metric("Waktu Tunggu", f"{avg_wait:.1f}s", delta=f"{avg_wait-20:.1f}s", delta_color="inverse")
        kpi3.metric("Selesai Pukul", df["Jam Selesai"].iloc[-1])
        kpi4.metric("Efisiensi Pos", f"{max(0, 100-(avg_wait/2)):.0f}%")

        st.divider()

        # --- VISUALISASI ---
        tab_grafik, tab_data = st.tabs(["🎯 Visualisasi Tren", "📋 Tabel Detail"])
        
        with tab_grafik:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### ⏳ Grafik Penumpukan Antrean")
                fig_area = px.area(df, x="Ompreng", y="Waktu Antre (s)", 
                                   color_discrete_sequence=['#00b4db'])
                fig_area.update_layout(template="none", hovermode="x unified")
                st.plotly_chart(fig_area, use_container_width=True)
                
            with c2:
                st.markdown("#### 📉 Distribusi Kecepatan")
                fig_hist = px.histogram(df, x="Waktu Pelayanan (s)", 
                                        color_discrete_sequence=['#0575e6'], nbins=20)
                fig_hist.update_layout(template="none")
                st.plotly_chart(fig_hist, use_container_width=True)

        with tab_data:
            st.markdown("#### Log Aktivitas Simulasi")
            st.dataframe(df.style.background_gradient(subset=['Waktu Antre (s)'], cmap='OrRd'), use_container_width=True)
            
            # Tombol Unduh
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Laporan (CSV)", data=csv, file_name="laporan_piket_del.csv", mime="text/csv")

    else:
        # --- TAMPILAN AWAL ---
        col_text, col_img = st.columns([1, 1])
        with col_text:
            st.markdown("""
            <div class="info-card">
                <h3>Selamat Datang! 👋</h3>
                <p>Dashboard ini membantu regu piket IT Del untuk menentukan jumlah staf terbaik di setiap pos pelayanan makanan.</p>
                <ul>
                    <li><b>Pos Lauk:</b> Mengambil porsi lauk utama.</li>
                    <li><b>Pos Angkat:</b> Mengambil piring/ompreng.</li>
                    <li><b>Pos Nasi:</b> Pengisian nasi hangat.</li>
                </ul>
                <p><i>Coba pindahkan satu petugas dari Lauk ke Nasi dan lihat perbedaannya pada waktu tunggu!</i></p>
            </div>
            """, unsafe_allow_html=True)
        with col_img:
            st.image("https://images.unsplash.com/photo-1547573854-74d2a71d0826?q=80&w=1200", use_container_width=True)

if __name__ == "__main__":
    main()
