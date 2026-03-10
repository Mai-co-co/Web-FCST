import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# ==========================================
# 1. CẤU HÌNH TRANG VÀ GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Production Cost Dashboard PRO", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-family: 'Arial', sans-serif; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #0D47A1; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .alert-card { background-color: #FFF3E0; padding: 15px; border-radius: 8px; border-left: 5px solid #E65100; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

# Hàm hỗ trợ tải file CSV (Mở được bằng Excel không bị lỗi font)
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# ==========================================
# 2. HÀM ĐỌC VÀ XỬ LÝ NHIỀU FILE (CHỐNG LỖI SAP)
# ==========================================
@st.cache_data
def process_multiple_production_data(files):
    all_data = []
    for file in files:
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            # --- BỘ LỌC CHỐNG LỖI FONT SAP ---
            df.columns = df.columns.str.strip()
            col_mapping = {
                'Vật tư': 'Vật tư', 'Nhà máy': 'Nhà máy', 'Kỳ g.sổ': 'Kỳ g.sổ',
                'Năm tài chính': 'Năm tài chính', 'Mô tả vật tư': 'Mô tả vật tư',
                'Phân loại': 'Phân loại', 'Số lượng nhập kho': 'Số lượng nhập kho',
                'Nguyên giá sản xuất': 'Nguyên giá sản xuất'
            }
            df.rename(columns=col_mapping, inplace=True)
            # ---------------------------------
            
            if 'Vật tư' in df.columns:
                df['Vật tư'] = df['Vật tư'].astype(str)
            
            # Lọc dữ liệu: Hàng PD và Mã bắt đầu bằng 7
            df = df[(df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7'))]
            
            # Xử lý số liệu
            df['Số lượng nhập kho'] = pd.to_numeric(df['Số lượng nhập kho'], errors='coerce').fillna(0)
            df['Nguyên giá sản xuất'] = pd.to_numeric(df['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df['Đơn giá 1 Sp'] = df.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            
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
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")

uploaded_files = st.sidebar.file_uploader("Tải các file ZCOR0110 (Nhiều tháng)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    df_all = process_multiple_production_data(uploaded_files)
    
    if df_all is not None and not df_all.empty:
        st.markdown("<h1 style='text-align: center; color: #0D47A1;'>🏭 HỆ THỐNG PHÂN TÍCH GIÁ THÀNH SẢN XUẤT CHUYÊN SÂU</h1>", unsafe_allow_html=True)
        
        ky_list = sorted(df_all['Kỳ báo cáo'].unique())
        selected_kys = st.multiselect("Bấm vào đây để chọn các kỳ muốn phân tích:", ky_list, default=ky_list)
        
        if not selected_kys:
            st.warning("⚠️ Vui lòng chọn ít nhất 1 kỳ để xem báo cáo!")
        else:
            df_compare = df_all[df_all['Kỳ báo cáo'].isin(selected_kys)]
            
            # CHIA LÀM 3 TAB CHUYÊN NGHIỆP
            tab1, tab2, tab3 = st.tabs(["📊 TỔNG QUAN & XU HƯỚNG", "🚨 CẢNH BÁO CHI PHÍ", "📋 BÁO CÁO CHI TIẾT"])
            
            # -----------------------------------------
            # TAB 1: TỔNG QUAN & XU HƯỚNG (TRENDLINE)
            # -----------------------------------------
            with tab1:
                if len(selected_kys) > 1:
                    st.markdown("### 📈 SO SÁNH TỔNG QUAN")
                    compare_df = df_compare.groupby(['Kỳ báo cáo', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                    compare_df['Nhà máy'] = compare_df['Nhà máy'].astype(str)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        fig_qty = px.bar(compare_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ báo cáo", barmode="group", title="So Sánh Sản Lượng (PCS)")
                        st.plotly_chart(fig_qty, use_container_width=True)
                    with c2:
                        fig_cost = px.bar(compare_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ báo cáo", barmode="group", title="So Sánh Chi Phí (VNĐ)")
                        st.plotly_chart(fig_cost, use_container_width=True)
                
                st.write("---")
                # Ý TƯỞNG 1: TRENDLINE THEO MÃ SẢN PHẨM
                st.markdown("### 📉 BẮT MẠCH XU HƯỚNG TỪNG SẢN PHẨM")
                list_sp = sorted(df_compare['Vật tư'].unique())
                chon_sp = st.selectbox("Gõ hoặc chọn Mã Vật Tư cần kiểm tra:", list_sp)
                
                df_sp = df_compare[df_compare['Vật tư'] == chon_sp].sort_values('Kỳ báo cáo')
                if not df_sp.empty:
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(x=df_sp['Kỳ báo cáo'], y=df_sp['Đơn giá 1 Sp'], mode='lines+markers', name='Đơn giá SX', line=dict(color='red', width=3), marker=dict(size=10)))
                    fig_trend.update_layout(title=f"Biến động Đơn giá Sản xuất của Mã: {chon_sp}", yaxis_title="Đơn giá (VNĐ/pcs)")
                    st.plotly_chart(fig_trend, use_container_width=True)

            # -----------------------------------------
            # TAB 2: CẢNH BÁO CHI PHÍ ĐỘT BIẾN
            # -----------------------------------------
            with tab2:
                st.markdown("### 🔥 CẢNH BÁO: TOP 5 MÃ SẢN PHẨM TĂNG GIÁ MẠNH NHẤT")
                if len(selected_kys) >= 2:
                    ky_moi_nhat = selected_kys[-1]
                    ky_truoc_do = selected_kys[-2]
                    
                    st.write(f"*(Đang so sánh kỳ **{ky_moi_nhat}** so với kỳ **{ky_truoc_do}**)*")
                    
                    # Tính toán đơn giá bình quân của 2 kỳ
                    df_moi = df_compare[df_compare['Kỳ báo cáo'] == ky_moi_nhat].groupby('Vật tư', as_index=False)['Đơn giá 1 Sp'].mean()
                    df_cu = df_compare[df_compare['Kỳ báo cáo'] == ky_truoc_do].groupby('Vật tư', as_index=False)['Đơn giá 1 Sp'].mean()
                    
                    # Nối dữ liệu để so sánh
                    df_alert = pd.merge(df_moi, df_cu, on='Vật tư', suffixes=('_HiệnTải', '_KỳTrước'))
                    
                    # Chỉ lấy những mã kỳ trước có đơn giá > 0 để tránh lỗi chia cho 0
                    df_alert = df_alert[df_alert['Đơn giá 1 Sp_KỳTrước'] > 0]
                    df_alert['% Tăng Giảm'] = ((df_alert['Đơn giá 1 Sp_HiệnTải'] - df_alert['Đơn giá 1 Sp_KỳTrước']) / df_alert['Đơn giá 1 Sp_KỳTrước']) * 100
                    
                    # Lọc ra Top 5 mã tăng giá mạnh nhất (tăng trên 0%)
                    top_tang = df_alert[df_alert['% Tăng Giảm'] > 0].sort_values('% Tăng Giảm', ascending=False).head(5)
                    
                    if not top_tang.empty:
                        for idx, row in top_tang.iterrows():
                            st.markdown(f"""
                            <div class="alert-card">
                                <h4 style="margin:0; color:#E65100;">🚨 Mã SP: {row['Vật tư']} (Tăng {row['% Tăng Giảm']:,.1f}%)</h4>
                                <p style="margin:5px 0 0 0;">Giá kỳ trước: {row['Đơn giá 1 Sp_KỳTrước']:,.0f} VNĐ ➡️ <b>Giá hiện tại: {row['Đơn giá 1 Sp_HiệnTải']:,.0f} VNĐ</b></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("🎉 Tuyệt vời! Không có mã sản phẩm nào bị tăng giá so với kỳ trước.")
                else:
                    st.info("⚠️ Vui lòng chọn ít nhất 2 kỳ báo cáo ở trên để hệ thống làm phép so sánh.")

            # -----------------------------------------
            # TAB 3: BÁO CÁO CHI TIẾT & XUẤT EXCEL
            # -----------------------------------------
            with tab3:
                st.markdown("### 📋 SỐ LIỆU CHI TIẾT & TẢI VỀ")
                
                # Ý TƯỞNG 3: NÚT TẢI EXCEL (CSV Format để không lỗi)
                st.success("💡 Bạn có thể tải toàn bộ dữ liệu đã gộp và làm sạch xuống máy để gửi cho Sếp!")
                csv_data = convert_df(df_compare)
                st.download_button(
                    label="📥 TẢI BÁO CÁO GỘP (File CSV - Mở bằng Excel)",
                    data=csv_data,
                    file_name='Bao_Cao_Gop_ZCOR0110.csv',
                    mime='text/csv',
                )
                
                st.write("---")
                
                selected_ky_detail = st.selectbox("Xem chi tiết riêng từng kỳ:", selected_kys)
                df_display = df_compare[df_compare['Kỳ báo cáo'] == selected_ky_detail]
                
                total_qty = df_display['Số lượng nhập kho'].sum()
                total_cost = df_display['Nguyên giá sản xuất'].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"""<div class="metric-card"><h4>📦 TỔNG SẢN LƯỢNG</h4><h2 style="color:#1565C0;">{total_qty:,.0f} PCS</h2></div>""", unsafe_allow_html=True)
                col2.markdown(f"""<div class="metric-card"><h4>💰 TỔNG CHI PHÍ</h4><h2 style="color:#D32F2F;">{total_cost/1e9:,.2f} TỶ VNĐ</h2></div>""", unsafe_allow_html=True)
                col3.markdown(f"""<div class="metric-card"><h4>⚙️ SỐ MÃ SP</h4><h2 style="color:#2E7D32;">{df_display['Vật tư'].nunique()} Mã</h2></div>""", unsafe_allow_html=True)
                
                st.write("---")
                display_cols = ['Kỳ báo cáo', 'Nhà máy', 'Vật tư', 'Mô tả vật tư', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp', 'Tổng Chi phí NVL', 'Tổng Nhân công']
                valid_display_cols = [c for c in display_cols if c in df_display.columns]
                st.dataframe(df_display[valid_display_cols].style.format({"Số lượng nhập kho": "{:,.0f}", "Nguyên giá sản xuất": "{:,.0f}", "Đơn giá 1 Sp": "{:,.0f}", "Tổng Chi phí NVL": "{:,.0f}", "Tổng Nhân công": "{:,.0f}"}), use_container_width=True)

    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7.")
