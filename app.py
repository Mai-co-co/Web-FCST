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

# ---- HÀM ĐỌC VÀ XỬ LÝ DỮ LIỆU NHIỀU FILE ----
@st.cache_data
def process_multiple_production_data(files):
    all_data = []
    
    for file in files:
        try:
            # Đọc file
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            # Đảm bảo mã vật tư là chuỗi
            df['Vật tư'] = df['Vật tư'].astype(str)
            
            # Lọc dữ liệu
            df = df[(df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7'))]
            
            # Tính toán
            df['Số lượng nhập kho'] = pd.to_numeric(df['Số lượng nhập kho'], errors='coerce').fillna(0)
            df['Nguyên giá sản xuất'] = pd.to_numeric(df['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df['Đơn giá 1 Sp'] = df.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            
            df['Tổng Chi phí NVL'] = df[['nguyên vật liệu(WAFER)', 'nguyên vật liệu(METAL)', 'nguyên vật liệu((GAS)', 'nguyên vật liệu(CHEM)', 'nguyên vật liệu(MOSC)', 'nguyên vật liệu(CHIP)', 'nguyên vật liệu(FILM)', 'nguyên vật liệu(FRAM)', 'nguyên vật liệu(LENS)', 'nguyên vật liệu(PCBM)', 'nguyên vật liệu(PCBS)', 'nguyên vật liệu(RFLT)', 'Nguyên phụ liệu']].sum(axis=1)
            df['Tổng Nhân công'] = df['Phí nhân công- trực'] + df['Phí nhân công- gián']
            df['Tổng CP Sản xuất chung'] = df['Chi phí khấu hao'] + df['Phí vật tư/ sửa chữa'] + df['Kinh phí-trực tiếp'] + df['Kinh phí-gián tiếp'] + df['Phí gia công vendor']
            
            # THÊM CỘT TÊN FILE ĐỂ PHÂN BIỆT KỲ BÁO CÁO
            # Lấy tên file bỏ đuôi mở rộng để làm tên kỳ
            ky_bao_cao = file.name.rsplit('.', 1)[0]
            df['Kỳ báo cáo'] = ky_bao_cao
            
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Lỗi đọc file {file.name}: {e}")
            
    # Gộp tất cả dataframe lại
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

# ---- GIAO DIỆN CHÍNH ----
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")

# CHO PHÉP TẢI LÊN NHIỀU FILE
uploaded_files = st.sidebar.file_uploader("Tải các file ZCOR0110 (Có thể chọn nhiều file)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    # Gọi hàm xử lý nhiều file
    df_all = process_multiple_production_data(uploaded_files)
    
    if df_all is not None and not df_all.empty:
        st.markdown("## 🏭 BÁO CÁO SO SÁNH GIÁ THÀNH SẢN XUẤT")
        
        # Tạo danh sách các kỳ để làm bộ lọc
        ky_list = sorted(df_all['Kỳ báo cáo'].unique())
        
        # Nếu tải lên nhiều hơn 1 file, thêm tính năng chọn 2 kỳ để so sánh
        if len(ky_list) > 1:
            st.markdown("### 🔍 Chọn Kỳ Để So Sánh")
            col_k1, col_k2 = st.columns(2)
            ky_1 = col_k1.selectbox("Kỳ báo cáo 1", ky_list, index=0)
            ky_2 = col_k2.selectbox("Kỳ báo cáo 2", ky_list, index=len(ky_list)-1)
            
            # Lọc dữ liệu theo 2 kỳ đã chọn
            df_compare = df_all[df_all['Kỳ báo cáo'].isin([ky_1, ky_2])]
            
            st.write("---")
            
            # =========================================================
            # BIỂU ĐỒ SO SÁNH SẢN LƯỢNG VÀ CHI PHÍ GIỮA 2 KỲ
            # =========================================================
            st.markdown("### 📈 SO SÁNH TỔNG QUAN GIỮA 2 KỲ")
            
            # Nhóm theo Kỳ và Nhà máy
            compare_df = df_compare.groupby(['Kỳ báo cáo', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
            compare_df['Nhà máy'] = compare_df['Nhà máy'].astype(str)
            
            c1, c2 = st.columns(2)
            
            with c1:
                # Biểu đồ cột ghép (Grouped Bar Chart) so sánh Sản lượng
                fig_qty = px.bar(compare_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ báo cáo", barmode="group",
                                title="So Sánh Sản Lượng (PCS) Theo Nhà Máy", color_discrete_sequence=['#42A5F5', '#1565C0'])
                st.plotly_chart(fig_qty, use_container_width=True)
                
            with c2:
                # Biểu đồ cột ghép (Grouped Bar Chart) so sánh Chi phí
                fig_cost = px.bar(compare_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ báo cáo", barmode="group",
                                title="So Sánh Chi Phí (VNĐ) Theo Nhà Máy", color_discrete_sequence=['#E53935', '#B71C1C'])
                st.plotly_chart(fig_cost, use_container_width=True)
                
            st.write("---")
            
        else:
            st.info("💡 Tải lên thêm file ZCOR0110 của tháng khác để kích hoạt tính năng So Sánh!")
            df_compare = df_all # Nếu chỉ có 1 file thì hiển thị dữ liệu của file đó
            
        # =========================================================
        # HIỂN THỊ DỮ LIỆU TỔNG HỢP (Hoặc của 1 kỳ nếu chỉ có 1 file)
        # =========================================================
        st.markdown("### 📋 DỮ LIỆU CHI TIẾT")
        
        # Thêm nút lọc theo kỳ cho phần bảng dữ liệu
        selected_ky = st.selectbox("Chọn kỳ để xem chi tiết", ky_list)
        df_display = df_compare[df_compare['Kỳ báo cáo'] == selected_ky]
        
        # Phần hiển thị tổng quan (giữ nguyên logic cũ, chỉ áp dụng cho kỳ đang chọn)
        total_qty = df_display['Số lượng nhập kho'].sum()
        total_cost = df_display['Nguyên giá sản xuất'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""<div class="metric-card"><h4>📦 TỔNG SẢN LƯỢNG</h4><h2 style="color:#1565C0;">{total_qty:,.0f} PCS</h2></div>""", unsafe_allow_html=True)
        col2.markdown(f"""<div class="metric-card"><h4>💰 TỔNG CHI PHÍ SẢN XUẤT</h4><h2 style="color:#D32F2F;">{total_cost/1e9:,.2f} TỶ VNĐ</h2></div>""", unsafe_allow_html=True)
        col3.markdown(f"""<div class="metric-card"><h4>⚙️ TỔNG SỐ MÃ SP (MODEL)</h4><h2 style="color:#2E7D32;">{df_display['Vật tư'].nunique()} Mã</h2></div>""", unsafe_allow_html=True)
        
        st.write("---")
        
        # Phần Top 3 giữ nguyên, áp dụng cho kỳ đang chọn
        st.markdown(f"### 🏆 TOP 3 THÀNH PHẨM SẢN XUẤT NHIỀU NHẤT (Kỳ: {selected_ky})")
        plants = sorted(df_display['Nhà máy'].unique())
        tabs = st.tabs([f"Nhà máy {p}" for p in plants])
        
        for idx, p in enumerate(plants):
            with tabs[idx]:
                top3 = df_display[df_display['Nhà máy'] == p].nlargest(3, 'Số lượng nhập kho')
                cols = st.columns(3)
                for i in range(len(top3)):
                    row = top3.iloc[i]
                    with cols[i]:
                        st.markdown(f"""
                        <div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd;">
                            <h4 style="color:#0D47A1; margin-bottom:5px;">Top {i+1}: {row['Vật tư']}</h4>
                            <p style="font-size:14px; font-weight:bold; color:#555;">{row['Mô tả vật tư']}</p>
                            <hr style="margin:10px 0;">
                            <p style="margin:5px 0;">📦 Sản lượng: <b>{row['Số lượng nhập kho']:,.0f} pcs</b></p>
                            <p style="margin:5px 0;">💸 Tổng CP: <b>{row['Nguyên giá sản xuất']:,.0f} VNĐ</b></p>
                            <p style="margin:5px 0; color:#D32F2F;">🔥 <b>Đơn giá 1 sp: {row['Đơn giá 1 Sp']:,.0f} VNĐ/pcs</b></p>
                        </div>
                        """, unsafe_allow_html=True)

        st.write("---")
        with st.expander("📂 XEM CHI TIẾT BẢNG TÍNH"):
            display_cols = ['Kỳ báo cáo', 'Nhà máy', 'Vật tư', 'Mô tả vật tư', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp', 'Tổng Chi phí NVL', 'Tổng Nhân công']
            st.dataframe(df_display[display_cols].style.format({"Số lượng nhập kho": "{:,.0f}", "Nguyên giá sản xuất": "{:,.0f}", "Đơn giá 1 Sp": "{:,.0f}", "Tổng Chi phí NVL": "{:,.0f}", "Tổng Nhân công": "{:,.0f}"}), use_container_width=True)

    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7.")
