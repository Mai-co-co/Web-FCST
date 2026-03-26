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
    html, body, [class*="st-"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 16px !important; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #0D47A1; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .alert-card { background-color: #FFF3E0; padding: 18px; border-radius: 10px; border-left: 6px solid #E65100; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); margin-bottom: 12px; }
    
    .wow-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 25px;
        border-radius: 12px;
        border-left: 8px solid #1565C0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        transition: transform 0.2s ease-in-out;
        text-align: center;
        margin-bottom: 20px;
    }
    .wow-card:hover { transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.15); }
    .wow-title { color: #546E7A; font-size: 18px; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }
    .wow-value { color: #0D47A1; font-size: 32px; font-weight: 900; }
    .wow-value-red { color: #D32F2F; font-size: 32px; font-weight: 900; }
    .wow-value-green { color: #2E7D32; font-size: 32px; font-weight: 900; }
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
            
            col_nam = df.columns[0]          
            col_thang = df.columns[1]        
            col_nha_may = df.columns[2]      
            col_vat_tu = df.columns[3]       
            col_phien_ban = df.columns[12]   
            col_phan_loai = df.columns[13]   
            col_so_luong = df.columns[14]    
            col_nguyen_gia = df.columns[15]  
            
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
            
            df['Năm'] = pd.to_numeric(df['Năm'], errors='coerce').fillna(0).astype(int).astype(str)
            df['Tháng'] = pd.to_numeric(df['Tháng'], errors='coerce').fillna(0).astype(int).astype(str).str.zfill(2)
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
    df_compare, df_682_compare = process_multiple_production_data(uploaded_files)
    
    if df_compare is not None and not df_compare.empty:
        st.markdown("<h1 style='text-align: center; color: #0D47A1; font-weight: 900;'>🏭 HỆ THỐNG PHÂN TÍCH GIÁ THÀNH SẢN XUẤT (BẢN VIP)</h1>", unsafe_allow_html=True)
        st.write("")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 TỔNG QUAN & XU HƯỚNG", 
            "🚨 CẢNH BÁO CHI PHÍ", 
            "📋 BÁO CÁO CHI TIẾT", 
            "📦 THỐNG KÊ MÃ 682*", 
            "📈 TREND BIẾN ĐỘNG ĐƠN GIÁ"
        ])
        
        # ----------------------------------------------------
        # TAB 1: TỔNG QUAN
        # ----------------------------------------------------
        with tab1:
            st.markdown("### 📈 TỔNG QUAN SẢN LƯỢNG VÀ CHI PHÍ (MÃ 7*)")
            
            chart_df = df_compare.groupby(['Kỳ_Tháng', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
            chart_df['Nhà máy'] = chart_df['Nhà máy'].astype(str)
            
            c1, c2 = st.columns(2)
            with c1:
                fig_qty = px.bar(chart_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ_Tháng", barmode="group", title="Sản Lượng Theo Nhà Máy (EA)")
                fig_qty.update_layout(yaxis_type="log", font=dict(size=14)) 
                st.plotly_chart(fig_qty, use_container_width=True)
            with c2:
                fig_cost = px.bar(chart_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ_Tháng", barmode="group", title="Chi Phí Theo Nhà Máy (VND)")
                fig_cost.update_layout(yaxis_type="log", font=dict(size=14))
                st.plotly_chart(fig_cost, use_container_width=True)
            
            st.markdown("#### 📦 BẢNG SỐ LIỆU TỔNG HỢP MÃ 7* THEO NHÀ MÁY")
            st.markdown("*(Đơn vị tính: Sản lượng = **EA** | Chi phí = **VND**)*")
            pivot_tonghop = df_compare.pivot_table(
                index='Nhà máy', 
                columns=['Năm', 'Tháng'], 
                values=['Số lượng nhập kho', 'Nguyên giá sản xuất'], 
                aggfunc='sum'
            )
            styled_tonghop = pivot_tonghop.style.format("{:,.0f}", na_rep="-").set_properties(**{'font-size': '15px'})
            st.dataframe(styled_tonghop, use_container_width=True)

            st.write("---")
            
            st.markdown("### 🎯 THEO DÕI BIẾN ĐỘNG ĐƠN GIÁ 1 SẢN PHẨM CỤ THỂ")
            list_sp = sorted(df_compare['Vật tư'].unique())
            chon_sp = st.selectbox("🔍 Gõ hoặc chọn Mã Vật Tư cần soi trend:", list_sp)
            
            df_sp = df_compare[df_compare['Vật tư'] == chon_sp].sort_values(['Năm', 'Tháng'])
            if not df_sp.empty:
                min_val = df_sp['Đơn giá 1 Sp'].min()
                max_val = df_sp['Đơn giá 1 Sp'].max()
                padding = (max_val - min_val) * 0.15 if max_val != min_val else max_val * 0.1
                
                fig_trend_1 = go.Figure()
                fig_trend_1.add_trace(go.Scatter(
                    x=df_sp['Kỳ_Tháng'], 
                    y=df_sp['Đơn giá 1 Sp'], 
                    mode='lines+markers+text', 
                    name='Đơn giá SX', 
                    line=dict(color='#D32F2F', width=4, shape='spline'), 
                    marker=dict(size=16, color='#1565C0', symbol='circle', line=dict(width=2, color='white')), 
                    fill='tozeroy', 
                    fillcolor='rgba(211, 47, 47, 0.1)',
                    text=df_sp['Đơn giá 1 Sp'].apply(lambda x: f"{x:,.0f}"),
                    textposition="top center"
                ))
                
                fig_trend_1.update_yaxes(range=[max(0, min_val - padding), max_val + padding * 1.5])
                fig_trend_1.update_layout(title=f"Biến động Đơn giá Sản xuất của Mã: <b>{chon_sp}</b>", yaxis_title="Đơn giá (VND/EA)", font=dict(size=15), plot_bgcolor='white')
                fig_trend_1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                fig_trend_1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                st.plotly_chart(fig_trend_1, use_container_width=True)

        # ----------------------------------------------------
        # TAB 2: CẢNH BÁO
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
                    st.write(f"*(Hệ thống đang đối chiếu giá của tháng **{ky_moi}** so với mốc **{ky_goc}**)*")
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
                                        <p style="margin:5px 0 0 0; font-size:16px;">Giá {ky_goc}: {row['Đơn giá 1 Sp_KyTruoc']:,.0f} VND ➡️ <b>Giá {ky_moi}: {row['Đơn giá 1 Sp_HienTai']:,.0f} VND</b></p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.success(f"🎉 Nhà máy {p} không có mã nào tăng giá so với tháng gốc.")
            else:
                st.info("⚠️ Cần ít nhất dữ liệu của 2 tháng để so sánh cảnh báo.")

        # ----------------------------------------------------
        # TAB 3: BÁO CÁO CHI TIẾT
        # ----------------------------------------------------
        with tab3:
            st.markdown("### 📋 BÁO CÁO CHI TIẾT")
            
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1: loc_nam = st.multiselect("🗓️ Năm:", sorted(df_compare['Năm'].unique()))
            with col_f2: loc_thang = st.multiselect("📆 Tháng:", sorted(df_compare['Tháng'].unique()))
            with col_f3: loc_nhamay = st.multiselect("🏭 Nhà máy:", sorted(df_compare['Nhà máy'].unique()))
            with col_f4: loc_vattu = st.multiselect("📦 Vật tư:", sorted(df_compare['Vật tư'].unique()))
                
            df_display = df_compare.copy()
            if loc_nam: df_display = df_display[df_display['Năm'].isin(loc_nam)]
            if loc_thang: df_display = df_display[df_display['Tháng'].isin(loc_thang)]
            if loc_nhamay: df_display = df_display[df_display['Nhà máy'].isin(loc_nhamay)]
            if loc_vattu: df_display = df_display[df_display['Vật tư'].isin(loc_vattu)]

            total_qty = df_display['Số lượng nhập kho'].sum()
            total_cost = df_display['Nguyên giá sản xuất'].sum()
            
            st.write("")
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"""<div class="wow-card"><div class="wow-title">📦 TỔNG SẢN LƯỢNG</div><div class="wow-value">{total_qty:,.0f} EA</div></div>""", unsafe_allow_html=True)
            col2.markdown(f"""<div class="wow-card" style="border-left-color: #D32F2F;"><div class="wow-title">💰 TỔNG CHI PHÍ</div><div class="wow-value-red">{total_cost/1e9:,.2f} TỶ VND</div></div>""", unsafe_allow_html=True)
            col3.markdown(f"""<div class="wow-card" style="border-left-color: #2E7D32;"><div class="wow-title">⚙️ SỐ MÃ SẢN PHẨM</div><div class="wow-value-green">{df_display['Vật tư'].nunique()} MÃ</div></div>""", unsafe_allow_html=True)
            
            st.write("---")
            
            display_cols = ['Năm', 'Tháng', 'Nhà máy', 'Vật tư', 'Phiên bản sản xuất', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp', 'Tổng Chi phí NVL', 'Tổng Nhân công']
            valid_display_cols = [c for c in display_cols if c in df_display.columns]
            df_display_tab3 = df_display[valid_display_cols].copy()
            
            df_display_tab3.rename(columns={
                'Số lượng nhập kho': 'Số lượng (EA)',
                'Nguyên giá sản xuất': 'Chi phí SX (VND)',
                'Đơn giá 1 Sp': 'Đơn giá (VND/EA)',
                'Tổng Chi phí NVL': 'Chi phí NVL (VND)',
                'Tổng Nhân công': 'Chi phí NC (VND)'
            }, inplace=True)
            
            styled_tab3 = df_display_tab3.style.format({
                "Số lượng (EA)": "{:,.0f}", 
                "Chi phí SX (VND)": "{:,.0f}", 
                "Đơn giá (VND/EA)": "{:,.0f}", 
                "Chi phí NVL (VND)": "{:,.0f}", 
                "Chi phí NC (VND)": "{:,.0f}"
            }).set_properties(**{'font-size': '15px'})
            
            col_config_tab3 = {
                "Năm": st.column_config.TextColumn(width="small"),
                "Tháng": st.column_config.TextColumn(width="small"),
                "Nhà máy": st.column_config.TextColumn(width="small"),
                "Phiên bản sản xuất": st.column_config.TextColumn(width="small"),
                "Vật tư": st.column_config.TextColumn(width="medium"),
            }
            
            st.dataframe(styled_tab3, use_container_width=True, height=800, column_config=col_config_tab3)

        # ----------------------------------------------------
        # TAB 4: MÃ 682
        # ----------------------------------------------------
        with tab4:
            st.markdown("### 📦 BẢNG THỐNG KÊ SỐ LƯỢNG VÀ CHI PHÍ MÃ 682* THEO NHÀ MÁY")
            if df_682_compare is not None and not df_682_compare.empty:
                st.markdown("*(Đơn vị tính: Sản lượng = **EA** | Chi phí = **VND**)*")
                pivot_682 = df_682_compare.pivot_table(
                    index='Nhà máy', 
                    columns=['Năm', 'Tháng'], 
                    values=['Số lượng nhập kho', 'Nguyên giá sản xuất'], 
                    aggfunc='sum'
                )
                styled_682 = pivot_682.style.format("{:,.0f}", na_rep="-").set_properties(**{'font-size': '15px'})
                st.dataframe(styled_682, use_container_width=True)
                
                st.write("---")
                st.markdown("#### 📊 BIỂU ĐỒ TRỰC QUAN MÃ 682*")
                chart_682_df = df_682_compare.groupby(['Kỳ_Tháng', 'Nhà máy'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                c3, c4 = st.columns(2)
                with c3:
                    fig_qty_682 = px.bar(chart_682_df, x="Nhà máy", y="Số lượng nhập kho", color="Kỳ_Tháng", barmode="group", title="Sản Lượng Mã 682* (EA)")
                    st.plotly_chart(fig_qty_682, use_container_width=True)
                with c4:
                    fig_cost_682 = px.bar(chart_682_df, x="Nhà máy", y="Nguyên giá sản xuất", color="Kỳ_Tháng", barmode="group", title="Chi Phí Mã 682* (VND)")
                    st.plotly_chart(fig_cost_682, use_container_width=True)
            else:
                st.info("💡 Không có dữ liệu mã 682*.")

        # ----------------------------------------------------
        # TAB 5: TREND BẢNG KÈM BIỂU ĐỒ CỘT TRỰC TIẾP TRONG HÀNG
        # ----------------------------------------------------
        with tab5:
            st.markdown("### 📈 BẢNG PHÂN TÍCH XU HƯỚNG VÀ BIỂU ĐỒ TỔNG HỢP")
            st.info("💡 Bảng bao gồm Dữ liệu các tháng, Cột Cảnh báo và **Biểu đồ Cột** được gắn trực tiếp vào từng dòng mã vật tư. Chắc chắn không bao giờ bị lệch hàng!")
            
            df_trend_all = pd.concat([df_compare, df_682_compare], ignore_index=True) if df_682_compare is not None else df_compare
            
            if not df_trend_all.empty:
                st.markdown("#### ⚙️ BỘ LỌC ĐIỀU KIỆN TÌM KIẾM")
                col_t1, col_t2, col_t3, col_t4, col_t5 = st.columns(5)
                with col_t1: loc_nam_t5 = st.multiselect("Năm:", sorted(df_trend_all['Năm'].unique()))
                with col_t2: loc_thang_t5 = st.multiselect("Tháng:", sorted(df_trend_all['Tháng'].unique()))
                with col_t3: loc_nha_may_t5 = st.multiselect("Nhà máy:", sorted(df_trend_all['Nhà máy'].unique()))
                with col_t4: loc_vat_tu_t5 = st.multiselect("Vật tư:", sorted(df_trend_all['Vật tư'].unique()))
                with col_t5: loc_phien_ban_t5 = st.multiselect("Phiên bản SX:", sorted(df_trend_all['Phiên bản sản xuất'].unique()))
                
                if loc_nam_t5: df_trend_all = df_trend_all[df_trend_all['Năm'].isin(loc_nam_t5)]
                if loc_thang_t5: df_trend_all = df_trend_all[df_trend_all['Tháng'].isin(loc_thang_t5)]
                if loc_nha_may_t5: df_trend_all = df_trend_all[df_trend_all['Nhà máy'].isin(loc_nha_may_t5)]
                if loc_vat_tu_t5: df_trend_all = df_trend_all[df_trend_all['Vật tư'].isin(loc_vat_tu_t5)]
                if loc_phien_ban_t5: df_trend_all = df_trend_all[df_trend_all['Phiên bản sản xuất'].isin(loc_phien_ban_t5)]
                
                st.write("")
                alert_level = st.selectbox("🎯 LỌC KHOẢNG BIẾN ĐỘNG ĐƠN GIÁ (Tháng cuối cùng so với tháng kề trước):", [
                    "Hiển thị tất cả các mã", 
                    "🔴 Tăng cực sốc (70% đến 100% trở lên)",
                    "🔴 Tăng mạnh (50% đến 70%)",
                    "🔴 Tăng (20% đến 50%)", 
                    "🟢 Giảm (-50% đến -20%)", 
                    "🟢 Giảm mạnh (-70% đến -50%)", 
                    "🟢 Giảm cực sốc (-100% đến -70%)"
                ])

                trend_grp = df_trend_all.groupby(['Nhà máy', 'Vật tư', 'Phiên bản sản xuất', 'Kỳ_Tháng'], as_index=False)[['Số lượng nhập kho', 'Nguyên giá sản xuất']].sum()
                trend_grp['Đơn giá'] = trend_grp.apply(lambda r: r['Nguyên giá sản xuất'] / r['Số lượng nhập kho'] if r['Số lượng nhập kho'] > 0 else 0, axis=1)
                
                pivot_trend = trend_grp.pivot_table(
                    index=['Nhà máy', 'Vật tư', 'Phiên bản sản xuất'], 
                    columns='Kỳ_Tháng', 
                    values='Đơn giá'
                ).reset_index()
                
                all_months = sorted(trend_grp['Kỳ_Tháng'].unique())
                rename_months = {m: f"Tháng {m[-2:]} (VND/EA)" for m in all_months}
                pivot_trend.rename(columns=rename_months, inplace=True)
                all_months_display = list(rename_months.values())
                
                warning_labels = []

                for idx, row in pivot_trend.iterrows():
                    valid_vals = [(m, val) for m, val in zip(all_months_display, row[all_months_display].values) if pd.notna(val)]
                    if len(valid_vals) >= 2:
                        prev_val = valid_vals[-2][1]
                        curr_val = valid_vals[-1][1]
                        pct = ((curr_val - prev_val) / prev_val) * 100 if prev_val > 0 else 0
                    else:
                        pct = 0
                        
                    if pct >= 70: label = "🔴 Tăng cực sốc (>70%)"
                    elif 50 <= pct < 70: label = "🔴 Tăng mạnh (50% - 70%)"
                    elif 20 <= pct < 50: label = "🔴 Tăng (20% - 50%)"
                    elif -50 < pct <= -20: label = "🟢 Giảm (-50% đến -20%)"
                    elif -70 < pct <= -50: label = "🟢 Giảm mạnh (-70% đến -50%)"
                    elif pct <= -70: label = "🟢 Giảm cực sốc (<-70%)"
                    else: label = "⚪ Ít biến động (±20%)"
                    
                    if len(valid_vals) < 2: label = "➖ Không đủ dữ liệu"
                    warning_labels.append(label)

                pivot_trend['🎯 Cảnh báo Mức độ'] = warning_labels
                
                # 🛡️ TUYỆT CHIÊU: CHUẨN HÓA DATA CHO BIỂU ĐỒ CỘT MINI ĐỂ THẤY RÕ BIẾN ĐỘNG
                def normalize_for_bar(row, m_cols):
                    vals = []
                    for c in m_cols:
                        val = row.get(c, pd.NA)
                        if pd.notna(val): vals.append(val)
                    if not vals: return []
                    min_v, max_v = min(vals), max(vals)
                    if max_v == min_v: return [50] * len(vals) # Bằng nhau thì cột cao vừa
                    # Cột thấp nhất là 10 (để không bị tàng hình), cao nhất là 100
                    return [10 + ((v - min_v) / (max_v - min_v)) * 90 for v in vals]

                pivot_trend['📊 Biểu đồ Cột Xu hướng'] = pivot_trend.apply(lambda r: normalize_for_bar(r, all_months_display), axis=1)

                rows_to_keep = []
                for idx, row in pivot_trend.iterrows():
                    keep = False
                    if alert_level == "Hiển thị tất cả các mã":
                        keep = True
                    else:
                        label = row['🎯 Cảnh báo Mức độ']
                        if "Giảm cực sốc" in alert_level and "Giảm cực sốc" in label: keep = True
                        elif "Giảm mạnh" in alert_level and "Giảm mạnh" in label: keep = True
                        elif "Giảm (-50% đến -20%)" in alert_level and "Giảm (-50% đến -20%)" in label: keep = True
                        elif "Tăng (20% đến 50%)" in alert_level and "Tăng (20% - 50%)" in label: keep = True
                        elif "Tăng mạnh" in alert_level and "Tăng mạnh" in label: keep = True
                        elif "Tăng cực sốc" in alert_level and "Tăng cực sốc" in label: keep = True
                    if keep:
                        rows_to_keep.append(idx)
                
                pivot_filtered = pivot_trend.loc[rows_to_keep].copy()
                
                if pivot_filtered.empty:
                    st.success(f"🎉 Không có mã vật tư nào thỏa mãn điều kiện: {alert_level}.")
                else:
                    st.markdown(f"*(Đang hiển thị **{len(pivot_filtered)}** mã vật tư thỏa mãn điều kiện)*")
                    
                    def style_table(row):
                        styles = [''] * len(row)
                        for i in range(1, len(all_months_display)):
                            prev_col = all_months_display[i-1]
                            curr_col = all_months_display[i]
                            try:
                                curr_idx = pivot_filtered.columns.get_loc(curr_col)
                                prev_val = row[prev_col]
                                curr_val = row[curr_col]
                                
                                if pd.notna(prev_val) and pd.notna(curr_val) and prev_val > 0:
                                    change = (curr_val - prev_val) / prev_val
                                    pct = change * 100
                                    
                                    if pct >= 70: styles[curr_idx] = 'color: #D32F2F; font-weight: bold;'
                                    elif 50 <= pct < 70: styles[curr_idx] = 'color: #D32F2F; font-weight: bold;'
                                    elif 20 <= pct < 50: styles[curr_idx] = 'color: #E65100; font-weight: bold;'
                                    elif -100 <= pct < -70: styles[curr_idx] = 'color: #2E7D32; font-weight: bold;'
                                    elif -70 <= pct < -50: styles[curr_idx] = 'color: #2E7D32; font-weight: bold;'
                                    elif -50 <= pct <= -20: styles[curr_idx] = 'color: #1565C0; font-weight: bold;'
                            except:
                                pass
                                
                        try:
                            label_idx = pivot_filtered.columns.get_loc('🎯 Cảnh báo Mức độ')
                            label_val = row['🎯 Cảnh báo Mức độ']
                            if "Tăng" in label_val: styles[label_idx] = 'color: #D32F2F; font-weight: bold;'
                            elif "Giảm" in label_val: styles[label_idx] = 'color: #2E7D32; font-weight: bold;'
                        except:
                            pass
                        return styles
                    
                    format_dict = {col: "{:,.0f}" for col in all_months_display}
                    styled_pivot = pivot_filtered.style.apply(style_table, axis=1).format(format_dict, na_rep="-").set_properties(**{'font-size': '15px'})
                    
                    col_config_tab5 = {
                        "Nhà máy": st.column_config.TextColumn(width="small"),
                        "Vật tư": st.column_config.TextColumn(width="medium"),
                        "Phiên bản sản xuất": st.column_config.TextColumn(width="small"),
                        "🎯 Cảnh báo Mức độ": st.column_config.TextColumn(width="medium"),
                        # ĐÂY LÀ BIỂU ĐỒ CỘT ĐƯỢC NHÉT THẲNG VÀO TRONG BẢNG:
                        "📊 Biểu đồ Cột Xu hướng": st.column_config.BarChartColumn(
                            "📊 Biểu đồ Cột (Giá trị)", y_min=0, y_max=100, width="large"
                        )
                    }
                    st.dataframe(styled_pivot, use_container_width=True, height=800, column_config=col_config_tab5)
            else:
                st.warning("⚠️ Chưa có đủ dữ liệu để vẽ bảng.")
    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7 hoặc 682.")
