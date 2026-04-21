import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Set konfigurasi halaman streamlit
st.set_page_config(page_title="Air Quality Dashboard", page_icon="☁️", layout="wide")

# Set style seaborn untuk visualisasi
sns.set_theme(style='darkgrid')

# Definisikan bins dan labels DI LUAR fungsi agar bisa diakses secara global
aqi_bins = [0, 12, 35.4, 55.4, 150.4, 250.4, float('inf')]
aqi_labels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous']

# Menyiapkan dan Membersihkan Data
@st.cache_data
def load_data():
    data = pd.read_csv("main_data.csv")
    # Pastikan format datetime
    data['datetime'] = pd.to_datetime(data['datetime'])
    
    # Menerapkan Binning untuk Analisis Lanjutan (AQI)
    data['AQI_Category'] = pd.cut(data['PM2.5'], bins=aqi_bins, labels=aqi_labels, include_lowest=True)
    
    return data

df = load_data()

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("☁️ Air Quality Tracker")
st.sidebar.markdown("Silakan filter data di bawah ini:")

# Filter Rentang Waktu
min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()

# Tangkap hasilnya dalam satu variabel (date_range)
date_range = st.sidebar.date_input(
    label='Rentang Waktu',
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Cek apakah user sudah memilih 2 tanggal atau baru 1
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = date_range[0]
    end_date = date_range[0] # Gunakan tanggal yang sama jika baru satu yang diklik

# Filter Stasiun
stations = df['station'].unique()
selected_stations = st.sidebar.multiselect(
    "Pilih Stasiun Pemantau:",
    options=stations,
    default=stations
)

# Menerapkan filter pada DataFrame
filtered_df = df[
    (df["datetime"].dt.date >= start_date) & 
    (df["datetime"].dt.date <= end_date) & 
    (df['station'].isin(selected_stations))
]

# ==============================
# MAIN DASHBOARD
# ==============================
st.title("☁️ Air Quality Data Dashboard (Beijing)")
st.markdown("Dashboard ini menyajikan hasil analisis data kualitas udara di berbagai stasiun pemantau di Beijing. Berfokus pada parameter **PM2.5** yang menjadi indikator utama polusi udara.")

# --- Row 1: KPI Metrics ---
st.subheader("Ringkasan Data")
col1, col2, col3 = st.columns(3)

with col1:
    avg_pm25 = filtered_df['PM2.5'].mean()
    st.metric("Rata-rata Konsentrasi PM2.5", value=f"{avg_pm25:.2f} µg/m³")

with col2:
    max_pm25 = filtered_df['PM2.5'].max()
    st.metric("Nilai PM2.5 Tertinggi", value=f"{max_pm25:.2f} µg/m³")

with col3:
    # Mengambil kategori AQI yang paling sering muncul
    if not filtered_df.empty:
        common_aqi = filtered_df['AQI_Category'].mode()[0]
    else:
        common_aqi = "N/A"
    st.metric("Kategori AQI Terbanyak", value=common_aqi)

st.markdown("---")

# --- Row 2: Visualisasi Tren & Perbandingan ---
st.subheader("Tren dan Perbandingan Kualitas Udara")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### Tren Konsentrasi PM2.5 Bulanan")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    # Ekstrak Tahun-Bulan untuk agregasi
    filtered_df['year_month'] = filtered_df['datetime'].dt.to_period('M').astype(str)
    monthly_pm25 = filtered_df.groupby('year_month')['PM2.5'].mean().reset_index()
    
    sns.lineplot(data=monthly_pm25, x='year_month', y='PM2.5', marker='o', color='#d32f2f', linewidth=2, ax=ax1)
    
    ax1.set_xlabel('Tahun - Bulan', fontsize=12)
    ax1.set_ylabel('Rata-rata PM2.5 (µg/m³)', fontsize=12)
    plt.xticks(rotation=45)
    st.pyplot(fig1)

with col_chart2:
    st.markdown("#### Perbandingan PM2.5 Antar Stasiun")
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    station_pm25 = filtered_df.groupby('station')['PM2.5'].mean().sort_values(ascending=False).reset_index()
    sns.barplot(data=station_pm25, x='PM2.5', y='station', palette='viridis', ax=ax2)
    
    ax2.set_xlabel('Rata-rata PM2.5 (µg/m³)', fontsize=12)
    ax2.set_ylabel('Stasiun Pemantau', fontsize=12)
    st.pyplot(fig2)

st.markdown("---")

# --- Row 3: Visualisasi Analisis Lanjutan (Binning) ---
st.subheader("Distribusi Kategori Kualitas Udara (AQI)")
fig3, ax3 = plt.subplots(figsize=(14, 5))

sns.countplot(data=filtered_df, x='AQI_Category', palette='magma', ax=ax3, order=aqi_labels)

ax3.set_xlabel('Kategori Indeks Kualitas Udara (AQI)', fontsize=12)
ax3.set_ylabel('Jumlah Observasi (Jam)', fontsize=12)
plt.xticks(rotation=0)
st.pyplot(fig3)

with st.expander("Lihat Penjelasan Kategori AQI"):
    st.write("""
    - **Good (0 - 12.0):** Kualitas udara sangat baik dan tidak menimbulkan risiko kesehatan.
    - **Moderate (12.1 - 35.4):** Kualitas udara dapat diterima; namun, ada potensi risiko sedang bagi sebagian kecil orang yang sangat sensitif.
    - **Unhealthy for Sensitive Groups (35.5 - 55.4):** Kelompok rentan (anak-anak, lansia, penderita asma) mungkin mengalami efek kesehatan.
    - **Unhealthy (55.5 - 150.4):** Setiap orang mungkin mulai mengalami efek kesehatan; kelompok sensitif dapat mengalami efek yang lebih serius.
    - **Very Unhealthy (150.5 - 250.4):** Peringatan kesehatan: setiap orang mungkin mengalami efek kesehatan yang lebih serius.
    - **Hazardous (> 250.4):** Peringatan darurat kesehatan: seluruh populasi kemungkinan besar akan terkena dampaknya.
    """)

st.caption("Data source: PRSA Data (2013-2017) - Dicoding Academy")