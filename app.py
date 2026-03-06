import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Cấu hình trang
st.set_page_config(page_title="Production Cost Dashboard", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-family: 'Arial', sans-serif; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #0D47A1; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM ĐỌC VÀ XỬ LÝ DỮ LIỆU CHUẨN XÁC ----
@st.cache_data
def process_production_data(file):
    try:
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        
        # Đảm bảo mã vật tư là chuỗi văn bản
        df['Vật tư'] = df['Vật tư'].astype(str)
        
        # 1. BỘ LỌC THẦN THÁNH CỦA BẠN: Phân loại = PD và Vật tư bắt đầu bằng "7"
        df = df[(df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7'))]
        
        # 2. TÍNH ĐƠN GIÁ SẢN XUẤT 1 CON (Cột P / Cột O)
        # Đề phòng lỗi chia cho 0, dùng hàm an toàn
        df['Số lượng nhập kho'] = pd.to_numeric(df['Số lượng nhập kho'], errors='coerce').fillna(0)
        df['Nguyên giá sản xuất'] = pd.to_numeric(df['Nguyên giá sản xuất'], errors='coerce').fillna(0)
        
        df['Đơn giá 1 Sp'] = df.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
        
        # 3. Gom nhóm chi phí để làm báo cáo
        df['Tổng Chi phí NVL'] = df[['nguyên vật liệu(WAFER)', 'nguyên vật liệu(METAL)', 'nguyên vật liệu((GAS)', 'nguyên vật liệu(CHEM)', 'nguyên vật liệu(MOSC)', 'nguyên vật liệu(CHIP)', 'nguyên vật liệu(FILM)', 'nguyên vật liệu(FRAM)', 'nguyên vật liệu(LENS)', 'nguyên vật liệu(PCBM)', 'nguyên vật liệu(PCBS)', 'nguyên vật liệu(RFLT)', 'Nguyên phụ liệu']].sum(axis=1)
        df['Tổng Nhân công'] = df['Phí nhân công- trực'] + df['Phí nhân công- gián']
        df['Tổng CP Sản xuất chung'] = df['Chi phí khấu hao'] + df['Phí vật tư/ sửa chữa'] + df['Kinh phí-trực tiếp'] + df['Kinh phí-gián tiếp'] + df['Phí gia công vendor']
        
        return df
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return None

# ---- GIAO DIỆN CHÍNH ----
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")
uploaded_file = st.sidebar.file_uploader("Tải file ZCOR0110", type=["csv", "xlsx"])

if uploaded_file:
    df = process_production_data(uploaded_file)
    
    if df is not None and not df.empty:
        # =========================================================
        # PHẦN 1: TỔNG QUAN HIỆU SUẤT NHÀ MÁY
        # =========================================================
        st.markdown(f"## 🏭 BÁO CÁO GIÁ THÀNH SẢN XUẤT | KỲ {df['Kỳ g.sổ'].iloc[0]}/{df['Năm tài chính'].iloc[0]}")
        st.write("*Dữ liệu đã tự động lọc: Hàng sản xuất (PD) - Mã thành phẩm (Đầu 7)*")
        
        total_qty = df['Số lượng nhập kho'].sum()
        total_cost = df['Nguyên giá sản xuất'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""<div class="metric-card"><h4>📦 TỔNG SẢN LƯỢNG</h4><h2 style="color:#1565C0;">{total_qty:,.0f} PCS</h2></div>""", unsafe_allow_html=True)
        col2.markdown(f"""<div class="metric-card"><h4>💰 TỔNG CHI PHÍ SẢN XUẤT</h4><h2 style="color:#D32F2F;">{total_cost/1e9:,.2f} TỶ VNĐ</h2></div>""", unsafe_allow_html=True)
        col3.markdown(f"""<div class="metric-card"><h4>⚙️ TỔNG SỐ MÃ SP (MODEL)</h4><h2 style="color:#2E7D32;">{df['Vật tư'].nunique()} Mã</h2></div>""", unsafe_allow_html=True)
        
        st.write("---")
        
        # =========================================================
        # PHẦN 2: SO SÁNH GIỮA CÁC NHÀ MÁY & CƠ CẤU CHI PHÍ
        # =========================================================
        st.markdown("### 📊 PHÂN TÍCH THEO NHÀ MÁY VÀ CẤU TRÚC GIÁ THÀNH")
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            # Nhóm dữ liệu theo nhà máy
            plant_df = df.groupby('Nhà máy', as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
            plant_df['Nhà máy'] = plant_df['Nhà máy'].astype(str)
            
            fig_plant = go.Figure()
            fig_plant.add_trace(go.Bar(x=plant_df['Nhà máy'], y=plant_df['Số lượng nhập kho'], name="Sản lượng (PCS)", marker_color='#42A5F5', text=[f"{v:,.0f}" for v in plant_df['Số lượng nhập kho']], textposition='auto'))
            # Dùng trục y phụ (secondary y-axis) cho chi phí vì số tiền rất lớn so với sản lượng
            fig_plant.add_trace(go.Scatter(x=plant_df['Nhà máy'], y=plant_df['Nguyên giá sản xuất'], name="Chi phí (VNĐ)", marker_color='#E53935', mode='lines+markers', yaxis='y2', line=dict(width=4)))
            
            fig_plant.update_layout(
                title="Tương quan Sản lượng và Chi phí giữa các Nhà máy",
                yaxis=dict(title="Sản lượng (PCS)"),
                yaxis2=dict(title="Chi phí (VNĐ)", overlaying='y', side='right'),
                height=450, legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_plant, use_container_width=True)
            
        with c2:
            # Biểu đồ Donut xem tiền dồn vào đâu
            cost_structure = [df['Tổng Chi phí NVL'].sum(), df['Tổng Nhân công'].sum(), df['Tổng CP Sản xuất chung'].sum()]
            cost_labels = ["Nguyên vật liệu", "Nhân công", "CP Sản xuất chung (Khấu hao, Vendor...)"]
            
            fig_pie = px.pie(values=cost_structure, names=cost_labels, hole=0.5, color_discrete_sequence=['#1565C0', '#43A047', '#FFB300'])
            fig_pie.update_layout(title="Cơ cấu 1 đồng Giá thành Sản xuất", height=450)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.write("---")

        # =========================================================
        # PHẦN 3: BẢNG XẾP HẠNG TOP 3 MODEL MỖI NHÀ MÁY
        # =========================================================
        st.markdown("### 🏆 BẢNG PHONG THẦN: TOP 3 THÀNH PHẨM SẢN XUẤT NHIỀU NHẤT")
        
        # Tạo các tab cho mỗi nhà máy
        plants = sorted(df['Nhà máy'].unique())
        tabs = st.tabs([f"Nhà máy {p}" for p in plants])
        
        for idx, p in enumerate(plants):
            with tabs[idx]:
                # Lấy dữ liệu của nhà máy đó, xếp hạng giảm dần theo Số lượng
                top3 = df[df['Nhà máy'] == p].nlargest(3, 'Số lượng nhập kho')
                
                # Hiển thị các chỉ số của top 3
                cols = st.columns(3)
                for i in range(len(top3)):
                    row = top3.iloc[i]
                    with cols[i]:
                        st.markdown(f"""
                        <div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd;">
                            <h4 style="color:#0D47A1; margin-bottom:5px;">Top {i+1}: {row['Vật tư']}</h4>
                            <p style="font-size:14px; font-weight:bold; color:#555;">{row['Mô tả vật tư']}</p>
                            <hr style="margin:10px 0;">
                            <p style="margin:5px 0;">📦 Sản lượng: <b>{row['Số lượng nhập kho']:,.0f} pcs</b></p>
                            <p style="margin:5px 0;">💸 Tổng CP: <b>{row['Nguyên giá sản xuất']:,.0f} VNĐ</b></p>
                            <p style="margin:5px 0; color:#D32F2F;">🔥 <b>Đơn giá 1 sp: {row['Đơn giá 1 Sp']:,.0f} VNĐ/pcs</b></p>
                        </div>
                        """, unsafe_allow_html=True)

        # =========================================================
        # PHẦN 4: BẢNG DỮ LIỆU ĐÃ LỌC CHO KẾ TOÁN
        # =========================================================
        st.write("---")
        with st.expander("📂 XEM CHI TIẾT BẢNG TÍNH ĐƠN GIÁ (Đã lọc thành phẩm)"):
            display_cols = ['Nhà máy', 'Vật tư', 'Mô tả vật tư', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp', 'Tổng Chi phí NVL', 'Tổng Nhân công']
            st.dataframe(df[display_cols].style.format({"Số lượng nhập kho": "{:,.0f}", "Nguyên giá sản xuất": "{:,.0f}", "Đơn giá 1 Sp": "{:,.0f}", "Tổng Chi phí NVL": "{:,.0f}", "Tổng Nhân công": "{:,.0f}"}), use_container_width=True)

    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7.")
