import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Fiskal Aceh", page_icon="📊", layout="wide")

DATA_URL = "https://raw.githubusercontent.com/Alam-A99/DATAAKSI/main/dataset_fiskal_97_hipoFull.csv"

st.markdown("""
<style>
.stApp { background-color: #f4f7fb; }
[data-testid="stMetric"] {
    background: white; padding: 16px; border-radius: 12px;
    border: 1px solid #e1e8f0;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL)

st.sidebar.title("📊 Dashboard Fiskal Aceh")
uploaded = st.sidebar.file_uploader("Unggah CSV jika diperlukan", type=["csv"])

try:
    data = pd.read_csv(uploaded) if uploaded is not None else load_data()
except Exception as error:
    st.title("Dashboard Fiskal Aceh")
    st.error("Data tidak berhasil dimuat. Periksa koneksi internet atau unggah file CSV melalui sidebar.")
    st.caption(f"Detail: {error}")
    st.stop()

data.columns = [str(c).strip() for c in data.columns]

st.title("Dashboard Data Fiskal Aceh")
st.write("Dashboard interaktif untuk melihat data, ringkasan statistik, dan perkembangan indikator fiskal.")
st.caption("Sumber data: dataset CSV dari GitHub")
st.divider()

# Deteksi kolom tahun dan wilayah secara otomatis.
year_col = next((c for c in data.columns if "tahun" in c.lower() or c.lower() == "year"), None)
region_col = next((c for c in data.columns if any(k in c.lower() for k in
                  ["provinsi", "kabupaten", "kota", "daerah", "wilayah", "region"])), None)

if region_col:
    options = sorted(data[region_col].dropna().astype(str).unique())
    aceh_options = [x for x in options if "aceh" in x.lower()]
    default_options = aceh_options if aceh_options else options
    selected = st.sidebar.multiselect("Pilih wilayah", options, default=default_options)
    if selected:
        data = data[data[region_col].astype(str).isin(selected)]

if year_col:
    year_values = pd.to_numeric(data[year_col], errors="coerce")
    years = sorted(year_values.dropna().unique())
    if len(years) > 0:
        chosen_years = st.sidebar.slider("Rentang tahun", int(min(years)), int(max(years)),
                                         (int(min(years)), int(max(years))))
        data = data[pd.to_numeric(data[year_col], errors="coerce").between(*chosen_years)]

# Konversi kolom yang tampak numerik agar grafik dan statistik dapat digunakan.
numeric_cols = data.select_dtypes(include="number").columns.tolist()
for col in data.columns:
    if col not in numeric_cols:
        converted = pd.to_numeric(data[col], errors="coerce")
        if converted.notna().mean() >= 0.75 and converted.notna().sum() > 0:
            data[col] = converted
            numeric_cols.append(col)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Jumlah baris", f"{len(data):,}")
m2.metric("Jumlah kolom", f"{len(data.columns):,}")
m3.metric("Variabel numerik", f"{len(numeric_cols):,}")
m4.metric("Tahun tersedia", f"{data[year_col].nunique():,}" if year_col else "Tidak terdeteksi")

tab1, tab2, tab3 = st.tabs(["🏠 Ringkasan", "📈 Grafik", "📋 Tabel Data"])

with tab1:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Pratinjau Data")
        st.dataframe(data.head(15), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Statistik Deskriptif")
        if numeric_cols:
            st.dataframe(data[numeric_cols].describe().T.round(2), use_container_width=True)
        else:
            st.info("Tidak ada kolom numerik yang terdeteksi.")

with tab2:
    st.subheader("Visualisasi Indikator Fiskal")
    if numeric_cols:
        x_default = year_col if year_col else data.columns[0]
        x_col = st.selectbox("Pilih sumbu X", list(data.columns),
                             index=list(data.columns).index(x_default))
        y_col = st.selectbox("Pilih indikator", numeric_cols)
        kind = st.radio("Jenis grafik", ["Garis", "Batang", "Area"], horizontal=True)
        chart_data = data[[x_col, y_col]].dropna()
        if chart_data[x_col].duplicated().any():
            chart_data = chart_data.groupby(x_col, as_index=False)[y_col].mean()
        if not chart_data.empty:
            if kind == "Garis":
                fig = px.line(chart_data, x=x_col, y=y_col, markers=True, title=f"Perkembangan {y_col}")
            elif kind == "Batang":
                fig = px.bar(chart_data, x=x_col, y=y_col, title=f"Perbandingan {y_col}")
            else:
                fig = px.area(chart_data, x=x_col, y=y_col, title=f"Perkembangan {y_col}")
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Kolom numerik tidak tersedia untuk dibuat grafik.")

with tab3:
    st.subheader("Data Lengkap")
    search = st.text_input("Cari dalam data")
    display_data = data
    if search:
        mask = data.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        display_data = data[mask]
    st.write(f"{len(display_data):,} baris data")
    st.dataframe(display_data, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Unduh CSV", display_data.to_csv(index=False).encode("utf-8-sig"),
                       file_name="data_fiskal_aceh.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.caption("Dibuat dengan Streamlit, Pandas, dan Plotly.")
