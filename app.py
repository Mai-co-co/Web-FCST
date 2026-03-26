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
# 2. HÀM ĐỌC VÀ XỬ LÝ DỮ LIỆU
# ==========================================
@st.cache_data
def process_multiple_production_data(files):
    all_data_7 = []   
    all_data_682 = [] 
    
    for file in files:
        try:
            df = pd.read_csv(file, on_bad_lines='skip') if file.name.endswith('.csv') else pd.read_excel(file)
            
            col_nam = df.columns[0]          # Cột A: Năm
            col_thang = df.columns[1]        # Cột B: Tháng
            col_nha_may = df.columns[2]      # Cột C: Nhà máy
            col_vat_tu = df.columns[3]       # Cột D: Vật tư
            col_phien_ban = df.columns[12]   # Cột M: Phiên bản sản xuất
            col_phan_loai = df.columns[13]   # Cột N: Phân loại
            col_so_luong = df.columns[14]    # Cột O: Số lượng nhập kho
            col_nguyen_gia = df.columns[15]  # Cột P: Nguyên giá sản xuất
            
            df.rename(columns={
                col_nam: 'Năm',
                col_thang: 'Tháng',
                col_vat_tu: 'Vật tư',
                col_phien_ban: 'Phiên bản sản xuất',
                col_phan_loai: 'Phân loại',
                col_nha_may: 'Nhà máy',
                col_so_luong: 'Số lượng nhập kho',
                col_nguyen_gia: 'Nguyên giá sản xuất'
            }, inplace=True)
            
            df['Vật tư'] = df['Vật tư'].fillna('').astype(str).str.strip()
            df['Phân loại'] = df['Phân loại'].fillna('').astype(str).str.strip()
            df['Phiên bản sản xuất'] = df['Phiên bản sản xuất'].fillna('').astype(str).str.strip()
            
            # Tách riêng Năm và Tháng chuẩn chỉ
            df['Năm'] = pd.to_numeric(df['Năm'], errors='coerce').fillna(0).astype(int).astype(str)
            df['Tháng'] = pd.to_numeric(df['Tháng'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
            
            # Cột Kỳ_Tháng chỉ giữ lại để vẽ Biểu đồ (Plotly cần 1 trục X duy nhất)
            df['Kỳ_Tháng'] = df['Năm'] + "-" + df['Tháng'] 
            
            # --- XỬ LÝ MÃ 7* ---
            mask_7 = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7', na=False))
            df_7 = df[mask_7].copy()
            
            df_7['Số lượng nhập kho'] = pd.to_numeric(df_7['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_7['Nguyên giá sản xuất'] = pd.to_numeric(df_7['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_7['Đơn giá 1 Sp'] = df_7.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            
            nvl_cols = [c for c in df.columns if 'nguyên vật liệu' in c.lower() or 'nguyên phụ liệu' in c.lower()]
            df_7['Tổng Chi phí NVL'] = df_7[nvl_cols].sum(axis=1) if nvl_cols else 0
            
            nc_cols = [c for c in df.columns if 'nhân công' in c.lower()]
            df_7['Tổng Nhân công'] = df_7[nc_cols].sum(axis=1) if nc_cols else 0
            
            cpc_cols = [c for c in df.columns if 'khấu hao' in c.lower() or 'sửa chữa' in c.lower() or 'kinh phí' in c.lower() or 'vendor' in c.lower()]
            df_7['Tổng CP Sản xuất chung'] = df_7[cpc_cols].sum(axis=1) if cpc_cols else 0
            
            all_data_7.append(df_7)
            
            # --- XỬ LÝ MÃ 682* ---
            mask_682 = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('682', na=False))
            df_682 = df[mask_682].copy()
            
            df_682['Số lượng nhập kho'] = pd.to_numeric(df_682['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_682['Nguyên giá sản xuất'] = pd.to_numeric(df_682['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_682['Đơn giá 1 Sp'] = df_682.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            
            all_data_682.append(df_682)
            
        except Exception as e:
            st.error(f"Lỗi khi đọc file '{file.name}': Lỗi chi tiết: {str(e)}")
            
    res_7 = pd.concat(all_data_7, ignore_index=True) if all_data_7 else None
    res_682 = pd.concat(all_data_682, ignore_index=True) if all_data_682 else None
    return res_7, res_682

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")

uploaded_files = st.sidebar.file_uploader("Tải file ZCOR0110 (Chứa số liệu Năm/Tháng)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    df_all, df_682_all = process_multiple_production_data(uploaded_files)
    
    if df_all is not None and not df_all.empty:
        st.markdown("<h1 style='text-align: center; color: #0D47A1;'>🏭 HỆ THỐNG PHÂN TÍCH GIÁ THÀNH SẢN XUẤT CHUYÊN SÂU</h1>", unsafe_allow_html=True)
        
        # Lấy toàn bộ dữ liệu (Không dùng bộ lọc dài ngoằng ở trên cùng nữa)
        df_compare = df_all.copy()
        df_682_compare = df_682_all.copy() if df_682_all is not None else pd.DataFrame()
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 TỔNG QUAN & XU HƯỚNG", 
            "🚨 CẢNH BÁO CHI PHÍ", 
            "📋 BÁO CÁO CHI TIẾT", 
            "📦 THỐNG KÊ MÃ 682*", 
            "📈 TREND BIẾN ĐỘNG ĐƠN GIÁ (PRO)"
        ])
        
        # ----------------------------------------------------
        # TAB 1: BẢNG CHÉO MULTI-INDEX (NĂM NẰM TRÊN, THÁNG NẰM DƯỚI)
        # ----------------------------------------------------
        with tab1:
            st.markdown("### 📈 TỔNG QUAN SẢN LƯỢNG VÀ CHI PHÍ (MÃ 7*)")
            
            # Biểu đồ vẫn dùng Kỳ_Tháng để có 1 trục X duy nhất
            chart_df = df_compare.groupby(['Kỳ_Tháng', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
            chart_df['Nhà máy'] = chart_df['Nhà máy'].astype(str)
            
            c1, c2 = st.columns(2)
            with c1:
                fig_qty = px.bar(chart_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ_Tháng", barmode="group", title="Sản Lượng Theo Nhà Máy (PCS)")
                fig_qty.update_layout(yaxis_type="log") 
                st.plotly_chart(fig_qty, use_container_width=True)
            with c2:
                fig_cost = px.bar(chart_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ_Tháng", barmode="group", title="Chi Phí Theo Nhà Máy (VNĐ)")
                fig_cost.update_layout(yaxis_type="log")
                st.plotly_chart(fig_cost, use_container_width=True)
            
            st.markdown("#### 📦 BẢNG SỐ LIỆU TỔNG HỢP MÃ 7* THEO NHÀ MÁY (NĂM & THÁNG)")
            
            # 🛡️ TUYỆT CHIÊU 1: MultiIndex Pivot Table
            # Cột ['Năm', 'Tháng'] sẽ tạo ra cấu trúc Năm ở trên, Tháng ở dưới
            pivot_tonghop = df_compare.pivot_table(
                index='Nhà máy', 
                columns=['Năm', 'Tháng'], 
                values=['Số lượng nhập kho', 'Nguyên giá sản xuất'], 
                aggfunc='sum'
            )
            st.dataframe(pivot_tonghop.style.format("{:,.0f}", na_rep="-"), use_container_width=True)
            
            st.write("---")
            st.markdown("### 📉 BẮT MẠCH XU HƯỚNG TỪNG SẢN PHẨM THEO THÁNG")
            list_sp = sorted(df_compare['Vật tư'].unique())
            chon_sp = st.selectbox("Gõ hoặc chọn Mã Vật Tư cần kiểm tra:", list_sp)
            df_sp = df_compare[df_compare['Vật tư'] == chon_sp].sort_values(['Năm', 'Tháng'])
            if not df_sp.empty:
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=df_sp['Kỳ_Tháng'], y=df_sp['Đơn giá 1 Sp'], mode='lines+markers', name='Đơn giá SX', line=dict(color='red', width=3), marker=dict(size=10)))
                fig_trend.update_layout(title=f"Biến động Đơn giá Sản xuất của Mã: {chon_sp}", yaxis_title="Đơn giá (VNĐ/pcs)")
                st.plotly_chart(fig_trend, use_container_width=True)

        # ----------------------------------------------------
        # TAB 2: CẢNH BÁO CHI PHÍ (Vẫn giữ bộ chọn tháng vì đây là so sánh đối chiếu)
        # ----------------------------------------------------
        with tab2:
            st.markdown("### 🔥 CẢNH BÁO: TOP 5 MÃ TĂNG GIÁ MẠNH NHẤT TỪNG NHÀ MÁY")
            ky_list_tab2 = sorted(df_compare['Kỳ_Tháng'].unique())
            if len(ky_list_tab2) >= 2:
                col_b1, col_b2 = st.columns(2)
                ky_goc = col_b1.selectbox("1. Chọn Tháng Gốc (Làm mốc):", ky_list_tab2, index=0)
                ky_moi = col_b2.selectbox("2. Chọn Tháng Cần Kiểm Tra:", ky_list_tab2, index=len(ky_list_tab2)-1)
                
                if ky_goc == ky_moi:
                    st.warning("⚠️ Vui lòng chọn 2 Tháng KHÁC NHAU để so sánh!")
                else:
                    df_moi = df_compare[df_compare['Kỳ_Tháng'] == ky_moi].groupby(['Nhà máy', 'Vật tư'], as_index=False)['Đơn giá 1 Sp'].mean()
                    df_cu = df_compare[df_compare['Kỳ_Tháng'] == ky_goc].groupby(['Nhà máy', 'Vật tư'], as_index=False)['Đơn giá 1 Sp'].mean()
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
                                st.success(f"🎉 Nhà máy {p} không có mã nào tăng giá so với tháng gốc.")
            else:
                st.info("⚠️ Cần ít nhất dữ liệu của 2 tháng để so sánh cảnh báo.")

        # ----------------------------------------------------
        # TAB 3: BỘ LỌC ĐỘC LẬP TỪNG CỘT (NHƯ EXCEL)
        # ----------------------------------------------------
        with tab3:
            st.markdown("### 📋 BÁO CÁO CHI TIẾT (LỌC THEO CỘT)")
            st.info("💡 Hãy sử dụng bộ lọc bên dưới để tìm kiếm chính xác dữ liệu bạn cần (Có thể chọn nhiều mục cùng lúc).")
            
            # 🛡️ TUYỆT CHIÊU 2: BỘ LỌC EXCEL TRỰC TIẾP TRÊN BẢNG
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                loc_nam = st.multiselect("Lọc Năm:", sorted(df_compare['Năm'].unique()))
            with col_f2:
                loc_thang = st.multiselect("Lọc Tháng:", sorted(df_compare['Tháng'].unique()))
            with col_f3:
                loc_nhamay = st.multiselect("Lọc Nhà máy:", sorted(df_compare['Nhà máy'].unique()))
            with col_f4:
                loc_vattu = st.multiselect("Lọc Vật tư (Mã 7*):", sorted(df_compare['Vật tư'].unique()))
                
            # Áp dụng bộ lọc vào DataFrame
            df_display = df_compare.copy()
            if loc_nam: df_display = df_display[df_display['Năm'].isin(loc_nam)]
            if loc_thang: df_display = df_display[df_display['Tháng'].isin(loc_thang)]
            if loc_nhamay: df_display = df_display[df_display['Nhà máy'].isin(loc_nhamay)]
            if loc_vattu: df_display = df_display[df_display['Vật tư'].isin(loc_vattu)]

            # Hiện các chỉ số tổng quan của phần dữ liệu ĐÃ LỌC
            total_qty = df_display['Số lượng nhập kho'].sum()
            total_cost = df_display['Nguyên giá sản xuất'].sum()
            
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"""<div class="metric-card"><h4>📦 SẢN LƯỢNG (ĐÃ LỌC)</h4><h2 style="color:#1565C0;">{total_qty:,.0f} PCS</h2></div>""", unsafe_allow_html=True)
            col2.markdown(f"""<div class="metric-card"><h4>💰 CHI PHÍ (ĐÃ LỌC)</h4><h2 style="color:#D32F2F;">{total_cost/1e9:,.2f} TỶ VNĐ</h2></div>""", unsafe_allow_html=True)
            col3.markdown(f"""<div class="metric-card"><h4>⚙️ SỐ MÃ SP (ĐÃ LỌC)</h4><h2 style="color:#2E7D32;">{df_display['Vật tư'].nunique()} Mã</h2></div>""", unsafe_allow_html=True)
            
            st.write("---")
            
            # Chỉ hiển thị các cột Năm, Tháng độc lập (Không có Kỳ_Tháng)
            display_cols = ['Năm', 'Tháng', 'Nhà máy', 'Vật tư', 'Phiên bản sản xuất', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp', 'Tổng Chi phí NVL', 'Tổng Nhân công']
            valid_display_cols = [c for c in display_cols if c in df_display.columns]
            
            st.dataframe(df_display[valid_display_cols].style.format({
                "Số lượng nhập kho": "{:,.0f}", 
                "Nguyên giá sản xuất": "{:,.0f}", 
                "Đơn giá 1 Sp": "{:,.0f}", 
                "Tổng Chi phí NVL": "{:,.0f}", 
                "Tổng Nhân công": "{:,.0f}"
            }), use_container_width=True, height=500)
            
            csv_data = convert_df(df_display)
            st.download_button(label="📥 TẢI BÁO CÁO ĐÃ LỌC (File CSV)", data=csv_data, file_name='Bao_Cao_Chi_Tiet.csv', mime='text/csv')

        # ----------------------------------------------------
        # TAB 4: MÃ 682 CŨNG ÁP DỤNG MULTI-INDEX (NĂM TRÊN, THÁNG DƯỚI)
        # ----------------------------------------------------
        with tab4:
            st.markdown("### 📦 BẢNG THỐNG KÊ SỐ LƯỢNG VÀ CHI PHÍ MÃ 682* THEO NHÀ MÁY")
            if not df_682_compare.empty:
                pivot_682 = df_682_compare.pivot_table(
                    index='Nhà máy', 
                    columns=['Năm', 'Tháng'], 
                    values=['Số lượng nhập kho', 'Nguyên giá sản xuất'], 
                    aggfunc='sum'
                )
                st.dataframe(pivot_682.style.format("{:,.0f}", na_rep="-"), use_container_width=True)
                
                st.write("---")
                st.markdown("#### 📊 BIỂU ĐỒ TRỰC QUAN MÃ 682*")
                
                chart_682_df = df_682_compare.groupby(['Kỳ_Tháng', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                c3, c4 = st.columns(2)
                with c3:
                    fig_qty_682 = px.bar(chart_682_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ_Tháng", barmode="group", title="Sản Lượng Mã 682* Theo Nhà Máy")
                    st.plotly_chart(fig_qty_682, use_container_width=True)
                with c4:
                    fig_cost_682 = px.bar(chart_682_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ_Tháng", barmode="group", title="Chi Phí Mã 682* Theo Nhà Máy")
                    st.plotly_chart(fig_cost_682, use_container_width=True)
            else:
                st.info("💡 Không có dữ liệu mã 682*.")

        # ----------------------------------------------------
        # TAB 5: TREND BIẾN ĐỘNG ĐƠN GIÁ (PRO) - GIỮ NGUYÊN
        # ----------------------------------------------------
        with tab5:
            st.markdown("### 📈 BẢNG THEO DÕI XU HƯỚNG ĐƠN GIÁ (NHÓM THEO NĂM/THÁNG)")
            
            df_trend_all = pd.concat([df_all, df_682_all], ignore_index=True) if df_682_all is not None else df_all
            
            if not df_trend_all.empty:
                st.markdown("#### ⚙️ BỘ ĐIỀU KHIỂN BÁO CÁO")
                ctrl1, ctrl2 = st.columns([2, 1])
                
                with ctrl1:
                    all_ky_thang = sorted(df_trend_all['Kỳ_Tháng'].unique())
                    selected_trend_months = st.multiselect("🗓️ 1. Chọn các Tháng/Năm muốn đưa vào bảng so sánh:", all_ky_thang, default=all_ky_thang)
                
                with ctrl2:
                    alert_level = st.selectbox("🎯 2. Lọc nhanh các mã Tăng/Giảm mạnh:", 
                                               ["Hiện tất cả", "Biến động > 20%", "Biến động > 50%", "Biến động > 70%", "Biến động > 100%"])
                    
                threshold_map = {"Hiện tất cả": 0.0, "Biến động > 20%": 0.2, "Biến động > 50%": 0.5, "Biến động > 70%": 0.7, "Biến động > 100%": 1.0}
                thresh = threshold_map[alert_level]

                df_trend_filtered = df_trend_all[df_trend_all['Kỳ_Tháng'].isin(selected_trend_months)]
                
                if not df_trend_filtered.empty:
                    trend_grp = df_trend_filtered.groupby(['Nhà máy', 'Vật tư', 'Phiên bản sản xuất', 'Năm', 'Tháng'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                    trend_grp['Đơn giá'] = trend_grp.apply(lambda r: r['Nguyên giá sản xuất'] / r['Số lượng nhập kho'] if r['Số lượng nhập kho'] > 0 else 0, axis=1)
                    
                    pivot_trend = trend_grp.pivot_table(
                        index=['Nhà máy', 'Vật tư', 'Phiên bản sản xuất'], 
                        columns=['Năm', 'Tháng'], 
                        values='Đơn giá'
                    )
                    
                    rows_to_keep = []
                    for idx, row in pivot_trend.iterrows():
                        keep = False
                        if thresh == 0:
                            keep = True
                        else:
                            valid_vals = [(i, val) for i, val in enumerate(row.values) if pd.notna(val)]
                            for i in range(1, len(valid_vals)):
                                prev_val = valid_vals[i-1][1]
                                curr_val = valid_vals[i][1]
                                if prev_val > 0:
                                    change = abs((curr_val - prev_val) / prev_val)
                                    if change >= thresh:
                                        keep = True
                                        break
                        if keep:
                            rows_to_keep.append(idx)
                    
                    pivot_filtered = pivot_trend.loc[rows_to_keep]
                    
                    if pivot_filtered.empty:
                        st.success(f"🎉 Rất tốt! Không có mã vật tư nào bị biến động {alert_level} trong các tháng bạn vừa chọn.")
                    else:
                        st.markdown(f"*(Đang hiển thị **{len(pivot_filtered)}** mã vật tư thỏa mãn điều kiện lọc)*")
                        
                        def style_variance(row):
                            styles = [''] * len(row)
                            vals = row.values
                            valid_vals = [(i, val) for i, val in enumerate(vals) if pd.notna(val)]
                            
                            for i in range(1, len(valid_vals)):
                                curr_idx = valid_vals[i][0]
                                prev_val = valid_vals[i-1][1]
                                curr_val = valid_vals[i][1]
                                
                                if prev_val > 0:
                                    change = (curr_val - prev_val) / prev_val
                                    if change >= 1.0:
                                        styles[curr_idx] = 'background-color: #8b0000; color: white; font-weight: bold;'
                                    elif change >= 0.7:
                                        styles[curr_idx] = 'background-color: #e60000; color: white; font-weight: bold;'
                                    elif change >= 0.5:
                                        styles[curr_idx] = 'background-color: #ff6666; color: black; font-weight: bold;'
                                    elif change >= 0.2:
                                        styles[curr_idx] = 'background-color: #ffcccc; color: black;'
                                    elif change <= -1.0 or change <= -0.7:
                                        styles[curr_idx] = 'background-color: #008000; color: white; font-weight: bold;'
                                    elif change <= -0.5:
                                        styles[curr_idx] = 'background-color: #33cc33; color: black; font-weight: bold;'
                                    elif change <= -0.2:
                                        styles[curr_idx] = 'background-color: #ccffcc; color: black;'
                            return styles
                        
                        styled_pivot = pivot_filtered.style.apply(style_variance, axis=1).format("{:,.0f}", na_rep="-")
                        st.dataframe(styled_pivot, use_container_width=True, height=650)
                else:
                    st.info("💡 Không có dữ liệu trong các tháng bạn vừa chọn.")
            else:
                st.warning("⚠️ Chưa có đủ dữ liệu để vẽ bảng.")
    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7 hoặc 682.")
