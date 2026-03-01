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
# 2. CSS CUSTOM PREMIUM
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .hero-container {
        background: linear-gradient(-45deg, #00b4db, #0083b0, #0575e6, #021b79);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        padding: 40px 20px;
        border-radius: 25px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .info-card {
        background: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 20px;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px !important;
        border: 1px solid rgba(128, 128, 128, 0.1);
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
        # PERBAIKAN: Set waktu mulai ke pukul 07:00:00
        self.waktu_mulai = datetime.now().replace(hour=7, minute=0, second=0, microsecond=0)

    def alur_makan(self, id_ompreng):
        datang = self.env.now
        
        # 1. Proses di Pos Lauk
        with self.lauk.request() as req:
            yield req
            mulai_layanan_lauk = self.env.now
            yield self.env.timeout(random.uniform(25, 55))
        
        # 2. Proses di Pos Angkat
        with self.angkat.request() as req:
            yield req
            mulai_layanan_angkat = self.env.now
            yield self.env.timeout(random.uniform(15, 45))
            
        # 3. Proses di Pos Nasi
        with self.nasi.request() as req:
            yield req
            mulai_layanan_nasi = self.env.now
            yield self.env.timeout(random.uniform(30, 60))

        selesai = self.env.now
        durasi_total = selesai - datang
        
        # Logika perhitungan waktu antre (Total waktu dikurangi waktu pengerjaan murni)
        waktu_proses_murni = (selesai - mulai_layanan_nasi) + \
                             (mulai_layanan_nasi - mulai_layanan_angkat) + \
                             (mulai_layanan_angkat - mulai_layanan_lauk)
        
        tunggu = max(0, durasi_total - waktu_proses_murni)

        self.data.append({
            "Ompreng": f"Unit-{id_ompreng+1:03d}",
            "Waktu Pelayanan (s)": round(durasi_total, 1),
            "Waktu Antre (s)": round(tunggu, 1),
            "Jam Selesai": (self.waktu_mulai + timedelta(seconds=selesai)).strftime("%H:%M:%S")
        })

    def jalankan(self, jumlah_ompreng):
        for i in range(jumlah_ompreng):
            self.env.process(self.alur_makan(i))
            # Interval antar unit/mahasiswa datang ke barisan (misal tiap 3 detik)
            yield self.env.timeout(3)

# ==========================================
# 4. ANTARMUKA PENGGUNA (UI)
# ==========================================
def main():
    st.markdown("""
        <div class="hero-container">
            <h1 style="font-size: 3rem; margin-bottom: 5px;">🍱 Analisis Piket IT Del</h1>
            <p style="font-size: 1.2rem; opacity: 0.9;">Optimasi Sistem Antrean Makan Mahasiswa (Mulai 07:00 WIB)</p>
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("🛠️ Konfigurasi Staf")
        st.info("Total staf tersedia: 7 orang")
        
        st_lauk = st.slider("🍗 Petugas Lauk", 1, 5, 2)
        st_angkat = st.slider("🧺 Petugas Angkat", 1, 5, 2)
        
        # Hitung sisa otomatis
        sisa = 7 - st_lauk - st_angkat
        
        if sisa < 1:
            st.error("⚠️ Alokasi melebihi 7 staf! Kurangi petugas lain.")
            siap = False
            st_nasi = 0
        else:
            st_nasi = sisa
            st.success(f"🍚 Petugas Nasi: {st_nasi}")
            siap = True
        
        st.divider()
        st.write("**Parameter Simulasi:**")
        jumlah_mhs = st.number_input("Jumlah Ompreng", min_value=10, max_value=500, value=180)
        btn_simulasi = st.button("🚀 Jalankan Simulasi", disabled=not siap, use_container_width=True)

    if btn_simulasi:
        env = simpy.Environment()
        sim = SimulasiPiket(env, st_lauk, st_angkat, st_nasi)
        env.process(sim.jalankan(jumlah_mhs)) 
        
        with st.spinner("Mengkalkulasi dinamika antrean..."):
            env.run()
            
        df = pd.DataFrame(sim.data)

        # --- PANEL METRIK ---
        st.subheader("📊 Statistik Performa")
        m1, m2, m3, m4 = st.columns(4)
        
        avg_wait = df['Waktu Antre (s)'].mean()
        m1.metric("Rerata Total Layanan", f"{df['Waktu Pelayanan (s)'].mean():.1f}s")
        m2.metric("Rerata Waktu Tunggu", f"{avg_wait:.1f}s", delta=f"{avg_wait/60:.1f} m", delta_color="inverse")
        m3.metric("Piket Selesai Pukul", df["Jam Selesai"].iloc[-1])
        m4.metric("Total Unit Dilayani", len(df))

        # --- VISUALISASI ---
        t1, t2 = st.tabs(["🎯 Visualisasi Tren", "📋 Detail Data"])
        
        with t1:
            c1, c2 = st.columns(2)
            with c1:
                fig_line = px.line(df, x="Ompreng", y="Waktu Antre (s)", 
                                 title="Akumulasi Waktu Antre per Unit",
                                 color_discrete_sequence=['#ff4b4b'])
                st.plotly_chart(fig_line, use_container_width=True)
            with c2:
                fig_hist = px.histogram(df, x="Waktu Pelayanan (s)", 
                                      title="Distribusi Kecepatan Layanan",
                                      color_discrete_sequence=['#00b4db'],
                                      nbins=20)
                st.plotly_chart(fig_hist, use_container_width=True)

        with t2:
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Laporan (CSV)", csv, "laporan_simulasi_piket.csv", "text/csv")
    else:
        # Tampilan Landing
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("""
            <div class="info-card">
                <h3>Panduan Simulasi:</h3>
                1. Atur komposisi petugas di sidebar (Total harus 7).<br>
                2. Tentukan berapa banyak unit (ompreng) yang akan diproses.<br>
                3. Klik <b>Jalankan Simulasi</b> untuk melihat visualisasi.<br><br>
                <b>Logika Waktu:</b> Simulasi dimulai pukul <b>07:00</b> untuk memantau durasi piket pagi.
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.image("https://images.unsplash.com/photo-1547573854-74d2a71d0826?q=80&w=1200", caption="Optimasi Kantin IT Del")

if __name__ == "__main__":
    main()
