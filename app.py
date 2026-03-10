import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CẤU HÌNH TRANG VÀ GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Production Cost Dashboard", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-family: 'Arial', sans-serif; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #0D47A1; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. HÀM ĐỌC VÀ XỬ LÝ NHIỀU FILE (CHỐNG LỖI SAP)
# ==========================================
@st.cache_data
def process_multiple_production_data(files):
    all_data = []
    
    for file in files:
        try:
            # Đọc file CSV hoặc Excel
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            # --- BỘ LỌC CHỐNG LỖI FONT SAP ---
            # Xóa khoảng trắng thừa ở tên cột
            df.columns = df.columns.str.strip()
            
            # Ép các tên cột hay bị lỗi Unicode của SAP về chuẩn tiếng Việt
            col_mapping = {
                'Vật tư': 'Vật tư',
                'Nhà máy': 'Nhà máy',
                'Kỳ g.sổ': 'Kỳ g.sổ',
                'Năm tài chính': 'Năm tài chính',
                'Mô tả vật tư': 'Mô tả vật tư',
                'Phân loại': 'Phân loại',
                'Số lượng nhập kho': 'Số lượng nhập kho',
                'Nguyên giá sản xuất': 'Nguyên giá sản xuất'
            }
            df.rename(columns=col_mapping, inplace=True)
            # ---------------------------------
            
            # Đảm bảo mã vật tư là chuỗi
            if 'Vật tư' in df.columns:
                df['Vật tư'] = df['Vật tư'].astype(str)
            
            # Lọc dữ liệu: Hàng PD và Mã bắt đầu bằng 7
            df = df[(df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7'))]
            
            # Xử lý số liệu trống hoặc lỗi
            df['Số lượng nhập kho'] = pd.to_numeric(df['Số lượng nhập kho'], errors='coerce').fillna(0)
            df['Nguyên giá sản xuất'] = pd.to_numeric(df['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df['Đơn giá 1 Sp'] = df.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            
            # Tính tổng chi phí (Dùng kiểm tra xem cột có tồn tại không để tránh lỗi)
            nvl_cols = ['nguyên vật liệu(WAFER)', 'nguyên vật liệu(METAL)', 'nguyên vật liệu((GAS)', 'nguyên vật liệu(CHEM)', 'nguyên vật liệu(MOSC)', 'nguyên vật liệu(CHIP)', 'nguyên vật liệu(FILM)', 'nguyên vật liệu(FRAM)', 'nguyên vật liệu(LENS)', 'nguyên vật liệu(PCBM)', 'nguyên vật liệu(PCBS)', 'nguyên vật liệu(RFLT)', 'Nguyên phụ liệu']
            valid_nvl = [c for c in nvl_cols if c in df.columns]
            df['Tổng Chi phí NVL'] = df[valid_nvl].sum(axis=1) if valid_nvl else 0
            
            nc_cols = ['Phí nhân công- trực', 'Phí nhân công- gián']
            valid_nc = [c for c in nc_cols if c in df.columns]
            df['Tổng Nhân công'] = df[valid_nc].sum(axis=1) if valid_nc else 0
            
            cpc_cols = ['Chi phí khấu hao', 'Phí vật tư/ sửa chữa', 'Kinh phí-trực tiếp', 'Kinh phí-gián tiếp', 'Phí gia công vendor']
            valid_cpc = [c for c in cpc_cols if c in df.columns]
            df['Tổng CP Sản xuất chung'] = df[valid_cpc].sum(axis=1) if valid_cpc else 0
            
            # Lấy tên file để làm Kỳ báo cáo
            ky_bao_cao = file.name.rsplit('.', 1)[0]
            df['Kỳ báo cáo'] = ky_bao_cao
            
            all_data.append(df)
            
        except Exception as e:
            st.error(f"Lỗi khi đọc file '{file.name}': {e}")
            
    # Gộp tất cả dataframe lại
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")

uploaded_files = st.sidebar.file_uploader("Tải các file ZCOR0110 (Có thể chọn nhiều file)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    df_all = process_multiple_production_data(uploaded_files)
    
    if df_all is not None and not df_all.empty:
        st.markdown("## 🏭 BÁO CÁO SO SÁNH GIÁ THÀNH SẢN XUẤT")
        
        ky_list = sorted(df_all['Kỳ báo cáo'].unique())
        
        # --- NẾU CÓ TỪ 2 FILE TRỞ LÊN: BẬT TÍNH NĂNG SO SÁNH ---
        if len(ky_list) > 1:
            st.markdown("### 🔍 Chọn Kỳ Để So Sánh")
            col_k1, col_k2 = st.columns(2)
            ky_1 = col_k1.selectbox("Kỳ báo cáo 1", ky_list, index=0)
            ky_2 = col_k2.selectbox("Kỳ báo cáo 2", ky_list, index=len(ky_list)-1)
            
            df_compare = df_all[df_all['Kỳ báo cáo'].isin([ky_1, ky_2])]
            
            st.write("---")
            st.markdown("### 📈 SO SÁNH TỔNG QUAN GIỮA 2 KỲ")
            
            compare_df = df_compare.groupby(['Kỳ báo cáo', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
            compare_df['Nhà máy'] = compare_df['Nhà máy'].astype(str)
            
            c1, c2 = st.columns(2)
            with c1:
                fig_qty = px.bar(compare_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ báo cáo", barmode="group",
                                title="So Sánh Sản Lượng (PCS) Theo Nhà Máy", color_discrete_sequence=['#42A5F5', '#1565C0'])
                st.plotly_chart(fig_qty, use_container_width=True)
                
            with c2:
                fig_cost = px.bar(compare_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ báo cáo", barmode="group",
                                title="So Sánh Chi Phí (VNĐ) Theo Nhà Máy", color_discrete_sequence=['#E53935', '#B71C1C'])
                st.plotly_chart(fig_cost, use_container_width=True)
                
            st.write("---")
            
        else:
            st.info("💡 Bạn có thể kéo thả thêm file ZCOR0110 của tháng khác vào để kích hoạt tính năng So Sánh!")
            df_compare = df_all
            
        # --- PHẦN CHI TIẾT TỪNG KỲ ---
        st.markdown("### 📋 DỮ LIỆU CHI TIẾT TỪNG KỲ")
        selected_ky = st.selectbox("Chọn kỳ để xem chi tiết", ky_list)
        df_display = df_compare[df_compare['Kỳ báo cáo'] == selected_ky]
        
        total_qty = df_display['Số lượng nhập kho'].sum()
        total_cost = df_display['Nguyên giá sản xuất'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""<div class="metric-card"><h4>📦 TỔNG SẢN LƯỢNG</h4><h2 style="color:#1565C0;">{total_qty:,.0f} PCS</h2></div>""", unsafe_allow_html=True)
        col2.markdown(f"""<div class="metric-card"><h4>💰 TỔNG CHI PHÍ SẢN XUẤT</h4><h2 style="color:#D32F2F;">{total_cost/1e9:,.2f} TỶ VNĐ</h2></div>""", unsafe_allow_html=True)
        col3.markdown(f"""<div class="metric-card"><h4>⚙️ TỔNG SỐ MÃ SP (MODEL)</h4><h2 style="color:#2E7D32;">{df_display['Vật tư'].nunique()} Mã</h2></div>""", unsafe_allow_html=True)
        
        st.write("---")
        
        # TOP 3 SẢN PHẨM
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
            valid_display_cols = [c for c in display_cols if c in df_display.columns]
            st.dataframe(df_display[valid_display_cols].style.format({"Số lượng nhập kho": "{:,.0f}", "Nguyên giá sản xuất": "{:,.0f}", "Đơn giá 1 Sp": "{:,.0f}", "Tổng Chi phí NVL": "{:,.0f}", "Tổng Nhân công": "{:,.0f}"}), use_container_width=True)

    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7.")
