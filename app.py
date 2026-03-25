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

@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# ==========================================
# 2. HÀM ĐỌC VÀ XỬ LÝ DỮ LIỆU (TÌM THEO VỊ TRÍ CỘT)
# ==========================================
@st.cache_data
def process_multiple_production_data(files):
    all_data_7 = []   
    all_data_682 = [] 
    
    for file in files:
        try:
            # Đọc file, bỏ qua các lỗi định dạng nhẹ
            df = pd.read_csv(file, on_bad_lines='skip') if file.name.endswith('.csv') else pd.read_excel(file)
            
            # 🛡️ CHIÊU MỚI: Định vị lại tên cột dựa trên vị trí (Cột D là 3, Cột N là 13)
            # Điều này giúp vượt qua lỗi KeyError nếu SAP xuất sai tên cột
            col_vat_tu = df.columns[3]       # Cột D: Vật tư
            col_phan_loai = df.columns[13]   # Cột N: Phân loại
            col_nha_may = df.columns[2]      # Cột C: Nhà máy
            col_so_luong = df.columns[14]    # Cột O: Số lượng nhập kho
            col_nguyen_gia = df.columns[15]  # Cột P: Nguyên giá sản xuất
            
            # Chuẩn hóa tên cột để code bên dưới chạy mượt
            df.rename(columns={
                col_vat_tu: 'Vật tư',
                col_phan_loai: 'Phân loại',
                col_nha_may: 'Nhà máy',
                col_so_luong: 'Số lượng nhập kho',
                col_nguyen_gia: 'Nguyên giá sản xuất'
            }, inplace=True)
            
            # Làm sạch khoảng trắng và NaN
            df['Vật tư'] = df['Vật tư'].fillna('').astype(str).str.strip()
            df['Phân loại'] = df['Phân loại'].fillna('').astype(str).str.strip()
            
            ky_bao_cao = file.name.rsplit('.', 1)[0]
            
            # --- XỬ LÝ MÃ 7* VÀ LỌC 'PD' ---
            mask_7 = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7', na=False))
            df_7 = df[mask_7].copy()
            
            df_7['Số lượng nhập kho'] = pd.to_numeric(df_7['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_7['Nguyên giá sản xuất'] = pd.to_numeric(df_7['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_7['Đơn giá 1 Sp'] = df_7.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            
            # Lấy các cột chi phí (tìm theo từ khóa để tránh lỗi nếu SAP đổi tên)
            nvl_cols = [c for c in df.columns if 'nguyên vật liệu' in c.lower() or 'nguyên phụ liệu' in c.lower()]
            df_7['Tổng Chi phí NVL'] = df_7[nvl_cols].sum(axis=1) if nvl_cols else 0
            
            nc_cols = [c for c in df.columns if 'nhân công' in c.lower()]
            df_7['Tổng Nhân công'] = df_7[nc_cols].sum(axis=1) if nc_cols else 0
            
            cpc_cols = [c for c in df.columns if 'khấu hao' in c.lower() or 'sửa chữa' in c.lower() or 'kinh phí' in c.lower() or 'vendor' in c.lower()]
            df_7['Tổng CP Sản xuất chung'] = df_7[cpc_cols].sum(axis=1) if cpc_cols else 0
            
            df_7['Kỳ báo cáo'] = ky_bao_cao
            all_data_7.append(df_7)
            
            # --- XỬ LÝ MÃ 682* VÀ LỌC 'PD' ---
            mask_682 = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('682', na=False))
            df_682 = df[mask_682].copy()
            
            df_682['Số lượng nhập kho'] = pd.to_numeric(df_682['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_682['Nguyên giá sản xuất'] = pd.to_numeric(df_682['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_682['Kỳ báo cáo'] = ky_bao_cao
            all_data_682.append(df_682)
            
        except Exception as e:
            st.error(f"Lỗi khi đọc file '{file.name}': Lỗi chi tiết: {str(e)}")
            st.warning("Gợi ý: Hãy mở file CSV bằng Excel, lưu lại thành file .xlsx rồi thử tải lên lại xem sao nhé!")
            
    res_7 = pd.concat(all_data_7, ignore_index=True) if all_data_7 else None
    res_682 = pd.concat(all_data_682, ignore_index=True) if all_data_682 else None
    return res_7, res_682

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")

uploaded_files = st.sidebar.file_uploader("Tải các file ZCOR0110 (Nhiều tháng)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    df_all, df_682_all = process_multiple_production_data(uploaded_files)
    
    if df_all is not None and not df_all.empty:
        st.markdown("<h1 style='text-align: center; color: #0D47A1;'>🏭 HỆ THỐNG PHÂN TÍCH GIÁ THÀNH SẢN XUẤT CHUYÊN SÂU</h1>", unsafe_allow_html=True)
        
        ky_list = sorted(df_all['Kỳ báo cáo'].unique())
        selected_kys = st.multiselect("Bấm vào đây để chọn các kỳ muốn phân tích:", ky_list, default=ky_list)
        
        if not selected_kys:
            st.warning("⚠️ Vui lòng chọn ít nhất 1 kỳ để xem báo cáo!")
        else:
            df_compare = df_all[df_all['Kỳ báo cáo'].isin(selected_kys)]
            
            tab1, tab2, tab3, tab4 = st.tabs(["📊 TỔNG QUAN & XU HƯỚNG", "🚨 CẢNH BÁO CHI PHÍ", "📋 BÁO CÁO CHI TIẾT", "📦 THỐNG KÊ MÃ 682*"])
            
            with tab1:
                st.markdown("### 📈 TỔNG QUAN SẢN LƯỢNG VÀ CHI PHÍ (THANG ĐO LOGARIT)")
                st.info("💡 Trục dọc (Y) đang sử dụng thang đo Logarit để nhìn rõ được cả nhà máy có sản lượng nhỏ.")
                
                compare_df = df_compare.groupby(['Kỳ báo cáo', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                compare_df['Nhà máy'] = compare_df['Nhà máy'].astype(str)
                
                c1, c2 = st.columns(2)
                with c1:
                    fig_qty = px.bar(compare_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ báo cáo", barmode="group", title="Sản Lượng Theo Nhà Máy (PCS)")
                    fig_qty.update_layout(yaxis_type="log") 
                    st.plotly_chart(fig_qty, use_container_width=True)
                with c2:
                    fig_cost = px.bar(compare_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ báo cáo", barmode="group", title="Chi Phí Theo Nhà Máy (VNĐ)")
                    fig_cost.update_layout(yaxis_type="log")
                    st.plotly_chart(fig_cost, use_container_width=True)
                
                st.write("---")
                
                st.markdown("### 🏆 BẢNG PHONG THẦN: TOP 3 THÀNH PHẨM SẢN XUẤT NHIỀU NHẤT")
                if len(selected_kys) > 1:
                    ky_top3 = st.selectbox("📌 Chọn 1 kỳ báo cáo để xem Top 3:", selected_kys, index=len(selected_kys)-1)
                else:
                    ky_top3 = selected_kys[0]
                    st.success(f"📌 Đang hiển thị Top 3 của kỳ: **{ky_top3}**")
                    
                df_top3 = df_compare[df_compare['Kỳ báo cáo'] == ky_top3]
                plants = sorted(df_top3['Nhà máy'].unique())
                tabs_top3 = st.tabs([f"🏭 Nhà máy {p}" for p in plants])
                
                for idx, p in enumerate(plants):
                    with tabs_top3[idx]:
                        top3 = df_top3[df_top3['Nhà máy'] == p].nlargest(3, 'Số lượng nhập kho')
                        cols = st.columns(3)
                        for i in range(len(top3)):
                            row = top3.iloc[i]
                            with cols[i]:
                                st.markdown(f"""
                                <div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd; height: 100%;">
                                    <h4 style="color:#0D47A1; margin-bottom:5px;">Top {i+1}: {row['Vật tư']}</h4>
                                    <p style="margin:5px 0;">📦 Sản lượng: <b>{row['Số lượng nhập kho']:,.0f} pcs</b></p>
                                    <p style="margin:5px 0;">💸 Tổng CP: <b>{row['Nguyên giá sản xuất']:,.0f} VNĐ</b></p>
                                    <p style="margin:5px 0; color:#D32F2F;">🔥 <b>Đơn giá 1 sp: {row['Đơn giá 1 Sp']:,.0f} VNĐ</b></p>
                                </div>
                                """, unsafe_allow_html=True)

                st.write("---")
                
                st.markdown("### 📉 BẮT MẠCH XU HƯỚNG TỪNG SẢN PHẨM")
                list_sp = sorted(df_compare['Vật tư'].unique())
                chon_sp = st.selectbox("Gõ hoặc chọn Mã Vật Tư cần kiểm tra:", list_sp)
                
                df_sp = df_compare[df_compare['Vật tư'] == chon_sp].sort_values('Kỳ báo cáo')
                if not df_sp.empty:
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(x=df_sp['Kỳ báo cáo'], y=df_sp['Đơn giá 1 Sp'], mode='lines+markers', name='Đơn giá SX', line=dict(color='red', width=3), marker=dict(size=10)))
                    fig_trend.update_layout(title=f"Biến động Đơn giá Sản xuất của Mã: {chon_sp}", yaxis_title="Đơn giá (VNĐ/pcs)")
                    st.plotly_chart(fig_trend, use_container_width=True)

            with tab2:
                st.markdown("### 🔥 CẢNH BÁO: TOP 5 MÃ TĂNG GIÁ MẠNH NHẤT TỪNG NHÀ MÁY")
                if len(selected_kys) >= 2:
                    col_b1, col_b2 = st.columns(2)
                    ky_goc = col_b1.selectbox("1. Chọn Kỳ Gốc (Kỳ cũ làm mốc):", selected_kys, index=0)
                    ky_moi = col_b2.selectbox("2. Chọn Kỳ Cần Kiểm Tra (Kỳ mới):", selected_kys, index=len(selected_kys)-1)
                    
                    if ky_goc == ky_moi:
                        st.warning("⚠️ Vui lòng chọn 2 kỳ KHÁC NHAU để hệ thống có thể so sánh chênh lệch!")
                    else:
                        st.write(f"*(Hệ thống đang đối chiếu giá của kỳ **{ky_moi}** so với mốc **{ky_goc}**)*")
                        
                        df_moi = df_compare[df_compare['Kỳ báo cáo'] == ky_moi].groupby(['Nhà máy', 'Vật tư'], as_index=False)['Đơn giá 1 Sp'].mean()
                        df_cu = df_compare[df_compare['Kỳ báo cáo'] == ky_goc].groupby(['Nhà máy', 'Vật tư'], as_index=False)['Đơn giá 1 Sp'].mean()
                        
                        df_alert = pd.merge(df_moi, df_cu, on=['Nhà máy', 'Vật tư'], suffixes=('_HienTai', '_KyTruoc'))
                        
                        df_alert = df_alert[df_alert['Đơn giá 1 Sp_KyTruoc'] > 0]
                        df_alert['% Tăng'] = ((df_alert['Đơn giá 1 Sp_HienTai'] - df_alert['Đơn giá 1 Sp_KyTruoc']) / df_alert['Đơn giá 1 Sp_KyTruoc']) * 100
                        
                        plants_alert = sorted(df_alert['Nhà máy'].unique())
                        tabs_alert = st.tabs([f"🏭 Nhà máy {p}" for p in plants_alert])
                        
                        for idx, p in enumerate(plants_alert):
                            with tabs_alert[idx]:
                                top_tang = df_alert[(df_alert['Nhà máy'] == p) & (df_alert['% Tăng'] > 0)].sort_values('% Tăng', ascending=False).head(5)
                                
                                if not top_tang.empty:
                                    for _, row in top_tang.iterrows():
                                        st.markdown(f"""
                                        <div class="alert-card">
                                            <h4 style="margin:0; color:#E65100;">🚨 Mã SP: {row['Vật tư']} (Tăng {row['% Tăng']:,.1f}%)</h4>
                                            <p style="margin:5px 0 0 0;">Giá {ky_goc}: {row['Đơn giá 1 Sp_KyTruoc']:,.0f} VNĐ ➡️ <b>Giá {ky_moi}: {row['Đơn giá 1 Sp_HienTai']:,.0f} VNĐ</b></p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.success(f"🎉 Tuyệt vời! Nhà máy {p} không có mã nào bị tăng giá so với kỳ gốc.")
                else:
                    st.info("⚠️ Vui lòng tải lên và chọn ít nhất 2 kỳ báo cáo ở thanh bên trên để hệ thống làm phép so sánh.")

            with tab3:
                st.markdown("### 📋 SỐ LIỆU CHI TIẾT & TẢI VỀ")
                st.success("💡 Bạn có thể tải toàn bộ dữ liệu đã gộp xuống máy để gửi cho Sếp!")
                csv_data = convert_df(df_compare)
                st.download_button(label="📥 TẢI BÁO CÁO GỘP (File CSV)", data=csv_data, file_name='Bao_Cao_Gop_ZCOR0110.csv', mime='text/csv')
                
                st.write("---")
                selected_ky_detail = st.selectbox("Xem chi tiết số liệu riêng từng kỳ:", selected_kys)
                df_display = df_compare[df_compare['Kỳ báo cáo'] == selected_ky_detail]
                
                total_qty = df_display['Số lượng nhập kho'].sum()
                total_cost = df_display['Nguyên giá sản xuất'].sum()
                
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"""<div class="metric-card"><h4>📦 TỔNG SẢN LƯỢNG</h4><h2 style="color:#1565C0;">{total_qty:,.0f} PCS</h2></div>""", unsafe_allow_html=True)
                col2.markdown(f"""<div class="metric-card"><h4>💰 TỔNG CHI PHÍ</h4><h2 style="color:#D32F2F;">{total_cost/1e9:,.2f} TỶ VNĐ</h2></div>""", unsafe_allow_html=True)
                col3.markdown(f"""<div class="metric-card"><h4>⚙️ SỐ MÃ SP</h4><h2 style="color:#2E7D32;">{df_display['Vật tư'].nunique()} Mã</h2></div>""", unsafe_allow_html=True)
                
                st.write("---")
                display_cols = ['Kỳ báo cáo', 'Nhà máy', 'Vật tư', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp', 'Tổng Chi phí NVL', 'Tổng Nhân công']
                valid_display_cols = [c for c in display_cols if c in df_display.columns]
                st.dataframe(df_display[valid_display_cols].style.format({"Số lượng nhập kho": "{:,.0f}", "Nguyên giá sản xuất": "{:,.0f}", "Đơn giá 1 Sp": "{:,.0f}", "Tổng Chi phí NVL": "{:,.0f}", "Tổng Nhân công": "{:,.0f}"}), use_container_width=True)

            with tab4:
                st.markdown("### 📦 BẢNG THỐNG KÊ SỐ LƯỢNG VÀ CHI PHÍ MÃ 682* THEO NHÀ MÁY")
                if df_682_all is not None and not df_682_all.empty:
                    df_682_compare = df_682_all[df_682_all['Kỳ báo cáo'].isin(selected_kys)]
                    
                    if not df_682_compare.empty:
                        summary_682 = df_682_compare.groupby(['Kỳ báo cáo', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                        summary_682['Nhà máy'] = summary_682['Nhà máy'].astype(str)
                        
                        st.dataframe(summary_682.style.format({
                            "Số lượng nhập kho": "{:,.0f}", 
                            "Nguyên giá sản xuất": "{:,.0f}"
                        }), use_container_width=True)
                        
                        st.write("---")
                        st.markdown("#### 📊 BIỂU ĐỒ TRỰC QUAN MÃ 682*")
                        
                        c3, c4 = st.columns(2)
                        with c3:
                            fig_qty_682 = px.bar(summary_682, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ báo cáo", barmode="group", title="Sản Lượng Mã 682* Theo Nhà Máy")
                            st.plotly_chart(fig_qty_682, use_container_width=True)
                        with c4:
                            fig_cost_682 = px.bar(summary_682, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ báo cáo", barmode="group", title="Chi Phí Mã 682* Theo Nhà Máy")
                            st.plotly_chart(fig_cost_682, use_container_width=True)
                    else:
                        st.info("💡 Không có dữ liệu mã 682* trong kỳ bạn đã chọn.")
                else:
                    st.warning("⚠️ File Excel/CSV của bạn không chứa mã vật tư nào bắt đầu bằng '682' với phân loại 'PD'.")
    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7 hoặc 682.")
