import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
import pickle
import os

# Konfigurasi halaman
st.set_page_config(page_title="Dashboard PLTU ANGGREK", layout="wide")

# Fungsi untuk menyimpan data
def save_data(sheet_dict):
    with open("uploaded_data.pkl", "wb") as f:
        pickle.dump(sheet_dict, f)

# Fungsi untuk memuat data
def load_data():
    if os.path.exists("uploaded_data.pkl"):
        with open("uploaded_data.pkl", "rb") as f:
            return pickle.load(f)
    return None

# Hapus data tersimpan
def clear_saved_data():
    if os.path.exists("uploaded_data.pkl"):
        os.remove("uploaded_data.pkl")
    for key in ["df", "sheet_names", "sheet_dict"]:
        st.session_state.pop(key, None)

# Load data saat aplikasi pertama kali dijalankan
if "df" not in st.session_state:
    loaded_data = load_data()
    if loaded_data:
        st.session_state.sheet_dict = loaded_data
        st.session_state.sheet_names = list(loaded_data.keys())
        st.session_state.df = list(loaded_data.values())[0]

# Sidebar menu
with st.sidebar:
    selected = option_menu(
        menu_title="Menu Utama",
        options=["Home", "Performance Indikator", "Kesiapan Peralatan"],
        icons=["house", "bar-chart", "gear"],
        menu_icon="cast",
        default_index=0,
    )
    if st.button("🗑️ Hapus Semua Data"):
        clear_saved_data()
        st.success("Data berhasil dihapus. Silakan unggah ulang di menu Performance Indikator.")

# Halaman Home
if selected == "Home":
    st.title("📈 Dashboard Parameter PLTU ANGGREK")
    st.markdown("Tampilan ringkas dari semua parameter dalam bentuk grafik tren.")

    if "df" not in st.session_state:
        st.warning("Silakan upload data terlebih dahulu di menu Performance Indikator.")
        st.stop()

    df = st.session_state.df
    selected_sheet = st.selectbox("📑 Pilih Sheet:", st.session_state.sheet_names)
    df = st.session_state.sheet_dict[selected_sheet]
    st.session_state.df = df

    date_column = None
    for col in df.columns:
        if pd.to_datetime(df[col], errors='coerce').notna().all():
            date_column = col
            df[date_column] = pd.to_datetime(df[date_column])
            df['Month'] = df[date_column].dt.strftime('%b %Y')
            break

    numerical_columns = df.select_dtypes(include='number').columns.tolist()
    chart_type = st.selectbox("Pilih Jenis Grafik:", ["Line Chart", "Bar Chart", "Scatter Plot"], index=0)

    for i in range(0, len(numerical_columns), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(numerical_columns):
                colname = numerical_columns[i + j]
                with cols[j]:
                    st.markdown(f"**{colname}**")
                    if date_column:
                        df_sorted = df.sort_values(by=date_column)
                        if chart_type == "Line Chart":
                            fig = px.line(df_sorted, x="Month", y=colname, markers=True)
                        elif chart_type == "Bar Chart":
                            fig = px.bar(df_sorted, x="Month", y=colname)
                        elif chart_type == "Scatter Plot":
                            fig = px.scatter(df_sorted, x="Month", y=colname)
                    else:
                        if chart_type == "Line Chart":
                            fig = px.line(df, x=df.index, y=colname, markers=True)
                        elif chart_type == "Bar Chart":
                            fig = px.bar(df, x=df.index, y=colname)
                        elif chart_type == "Scatter Plot":
                            fig = px.scatter(df, x=df.index, y=colname)

                    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300)
                    st.plotly_chart(fig, use_container_width=True)

# Halaman Performance Indikator
elif selected == "Performance Indikator":
    st.title("📊 Performance Indikator")
    uploaded_file = st.file_uploader("📄 Upload file data (CSV atau Excel)", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            st.session_state.sheet_dict = {"Sheet1": df}
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_dict = {name: pd.read_excel(xls, sheet_name=name) for name in xls.sheet_names}
            st.session_state.sheet_dict = sheet_dict

        st.session_state.sheet_names = list(st.session_state.sheet_dict.keys())
        st.session_state.df = list(st.session_state.sheet_dict.values())[0]
        save_data(st.session_state.sheet_dict)
        st.success("✅ Data berhasil diunggah!")

    if "sheet_dict" not in st.session_state:
        st.info("Silakan upload file terlebih dahulu.")
        st.stop()

    selected_sheet = st.radio("📄 Pilih Sheet:", st.session_state.sheet_names, horizontal=True)
    df = st.session_state.sheet_dict[selected_sheet]
    st.session_state.df = df

    columns = df.select_dtypes(include=['number']).columns.tolist()

    selected_param = st.selectbox(
        "Pilih Parameter:",
        options=columns,
        index=0,
        key="param_selectbox",
        help="Pilih parameter yang ingin dianalisis dari daftar"
    )

    st.markdown(f"**Parameter yang dipilih**: {selected_param}")

    date_column = None
    for col in df.columns:
        if pd.to_datetime(df[col], errors='coerce').notna().all():
            date_column = col
            df[date_column] = pd.to_datetime(df[date_column])
            df['Month'] = df[date_column].dt.strftime('%b %Y')
            break

    st.subheader(f"📈 Statistik: {selected_param}")
    mean = df[selected_param].mean()
    median = df[selected_param].median()
    std = df[selected_param].std()
    min_val = df[selected_param].min()
    max_val = df[selected_param].max()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Mean", f"{mean:.2f}")
    col2.metric("Median", f"{median:.2f}")
    col3.metric("Std Dev", f"{std:.2f}")
    col4.metric("Min", f"{min_val:.2f}")
    col5.metric("Max", f"{max_val:.2f}")

    st.markdown("### 📉 Grafik Tren")

    # Color picker dan slider transparansi sejajar
    with st.container():
        col1, col2, col3 = st.columns([1.5, 1.5, 3])
        with col1:
            line_color = st.color_picker("Warna Garis", value="#1f77b4")
        with col2:
            fill_color = st.color_picker("Warna Bayangan", value="#add8e6")
        with col3:
            opacity = st.slider("Transparansi Bayangan (%)", 0, 100, 50)

    opacity = opacity / 100
    fig_line = px.line(df, x='Month' if date_column else df.index, y=selected_param)
    fig_line.update_traces(
        line=dict(color=line_color, shape="spline"),
        fill='tozeroy',
        fillcolor=f'rgba{tuple([int(fill_color[1:3], 16), int(fill_color[3:5], 16), int(fill_color[5:7], 16), opacity])}'
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("### 📊 Histogram")
    st.plotly_chart(px.histogram(df, x=selected_param), use_container_width=True)

    st.markdown("### 📦 Box Plot")
    st.plotly_chart(px.box(df, y=selected_param), use_container_width=True)

    st.markdown("### 🧠 Ringkasan Otomatis")
    recent = df.sort_values(by=date_column).iloc[-5:] if date_column else df.iloc[-5:]
    if recent[selected_param].is_monotonic_increasing:
        trend = "Nilai parameter menunjukkan **tren meningkat**."
    elif recent[selected_param].is_monotonic_decreasing:
        trend = "Nilai parameter menunjukkan **tren menurun**."
    else:
        trend = "Nilai parameter menunjukkan **fluktuasi**."

    st.markdown(f"Rata-rata: **{mean:.2f}**, Median: **{median:.2f}**, Std Dev: **{std:.2f}**, Min: **{min_val:.2f}**, Max: **{max_val:.2f}**. {trend}")

# Halaman Kesiapan Peralatan
elif selected == "Kesiapan Peralatan":
    st.title("🔧 Kesiapan Peralatan PLTU ANGGREK")
    sheet_id = "1vh_3k_6uacjs96Bpr9ap_gQ-6T3CF-xQfFYt2AuSNvo"
    st.markdown(
        f'<iframe src="https://docs.google.com/spreadsheets/d/{sheet_id}/embed" width="100%" height="600"></iframe>',
        unsafe_allow_html=True
    )
    st.markdown(f"[📄 Buka Google Sheet di tab baru](https://docs.google.com/spreadsheets/d/{sheet_id}/edit)")
