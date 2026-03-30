import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re  

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
    all_data_6_all = [] 
    
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
            df['Kỳ_Tháng'] = df['Năm'] + "/" + df['Tháng'] 
            
            mask_7 = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7', na=False))
            df_7 = df[mask_7].copy()
            df_7['Số lượng nhập kho'] = pd.to_numeric(df_7['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_7['Nguyên giá sản xuất'] = pd.to_numeric(df_7['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_7['Đơn giá 1 Sp'] = df_7.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            all_data_7.append(df_7)
            
            mask_682 = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('682', na=False))
            df_682 = df[mask_682].copy()
            df_682['Số lượng nhập kho'] = pd.to_numeric(df_682['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_682['Nguyên giá sản xuất'] = pd.to_numeric(df_682['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_682['Đơn giá 1 Sp'] = df_682.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            all_data_682.append(df_682)

            mask_6_all = (df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('6', na=False))
            df_6_all = df[mask_6_all].copy()
            df_6_all['Số lượng nhập kho'] = pd.to_numeric(df_6_all['Số lượng nhập kho'], errors='coerce').fillna(0)
            df_6_all['Nguyên giá sản xuất'] = pd.to_numeric(df_6_all['Nguyên giá sản xuất'], errors='coerce').fillna(0)
            df_6_all['Đơn giá 1 Sp'] = df_6_all.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
            all_data_6_all.append(df_6_all)
            
        except Exception as e:
            st.error(f"Lỗi khi đọc file '{file.name}': Lỗi chi tiết: {str(e)}")
            
    res_7 = pd.concat(all_data_7, ignore_index=True) if all_data_7 else None
    res_682 = pd.concat(all_data_682, ignore_index=True) if all_data_682 else None
    res_6_all = pd.concat(all_data_6_all, ignore_index=True) if all_data_6_all else None
    
    return res_7, res_682, res_6_all

# ==========================================
# 3. GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
st.sidebar.header("🏭 NẠP DỮ LIỆU SẢN XUẤT")

uploaded_files = st.sidebar.file_uploader("Tải file ZCOR0110 (Chứa số liệu Năm/Tháng)", type=["csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    df_compare, df_682_compare, df_6_all_compare = process_multiple_production_data(uploaded_files)
    
    if df_compare is not None and not df_compare.empty:
        st.markdown("<h1 style='text-align: center; color: #0D47A1; font-weight: 900;'>🏭 HỆ THỐNG PHÂN TÍCH GIÁ THÀNH SẢN XUẤT (BẢN VIP)</h1>", unsafe_allow_html=True)
        st.write("")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 TỔNG QUAN & XU HƯỚNG", 
            "🚨 CẢNH BÁO CHI PHÍ", 
            "📋 BÁO CÁO CHI TIẾT", 
            "📦 THỐNG KÊ MÃ 682*", 
            "📈 TREND BIẾN ĐỘNG ĐƠN GIÁ (VIP)"
        ])
        
        # ----------------------------------------------------
        # TAB 1: TỔNG QUAN VÀ BIỂU ĐỒ VIP
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
                index='Nhà máy', columns='Kỳ_Tháng', values=['Số lượng nhập kho', 'Nguyên giá sản xuất'], aggfunc='sum'
            )
            styled_tonghop = pivot_tonghop.style.format("{:,.0f}", na_rep="-").set_properties(**{'font-size': '15px'})
            st.dataframe(styled_tonghop, use_container_width=True)

            st.write("---")
            
            st.markdown("### 🎯 THEO DÕI BIẾN ĐỘNG ĐƠN GIÁ CỦA CÁC SẢN PHẨM")
            st.info("💡 Bạn có thể chọn nhiều Mã Vật Tư cùng lúc để so sánh xu hướng giá.")
            list_sp = sorted(df_compare['Vật tư'].unique())
            
            chon_sp = st.multiselect("🔍 Gõ hoặc chọn các Mã Vật Tư cần soi trend:", list_sp, default=[list_sp[0]] if list_sp else [])
            
            if chon_sp:
                df_sp = df_compare[df_compare['Vật tư'].isin(chon_sp)].sort_values('Kỳ_Tháng')
                if not df_sp.empty:
                    min_val = df_sp['Đơn giá 1 Sp'].min()
                    max_val = df_sp['Đơn giá 1 Sp'].max()
                    padding = (max_val - min_val) * 0.15 if max_val != min_val else max_val * 0.1
                    
                    fig_trend_1 = go.Figure()
                    
                    color_palette = px.colors.qualitative.Plotly
                    
                    for i, sp in enumerate(chon_sp):
                        df_sp_single = df_sp[df_sp['Vật tư'] == sp]
                        
                        if len(chon_sp) == 1:
                            line_color = '#D32F2F'
                            marker_color = '#1565C0'
                            fill_opt = 'tozeroy'
                            fill_clr = 'rgba(211, 47, 47, 0.1)'
                            marker_size = 16
                        else:
                            line_color = color_palette[i % len(color_palette)]
                            marker_color = line_color
                            fill_opt = 'none'
                            fill_clr = 'rgba(0,0,0,0)'
                            marker_size = 12
                        
                        fig_trend_1.add_trace(go.Scatter(
                            x=df_sp_single['Kỳ_Tháng'], 
                            y=df_sp_single['Đơn giá 1 Sp'], 
                            mode='lines+markers+text', 
                            name=sp, 
                            line=dict(color=line_color, width=4, shape='spline'), 
                            marker=dict(size=marker_size, color=marker_color, symbol='circle', line=dict(width=2, color='white')), 
                            fill=fill_opt, 
                            fillcolor=fill_clr,
                            text=df_sp_single['Đơn giá 1 Sp'].apply(lambda x: f"{x:,.0f}"), 
                            textposition="top center"
                        ))
                    
                    fig_trend_1.update_yaxes(range=[max(0, min_val - padding), max_val + padding * 1.5])
                    
                    title_text = f"Biến động Đơn giá của: <b>{', '.join(chon_sp)}</b>" if len(chon_sp) <= 3 else f"So sánh Xu hướng Đơn giá của <b>{len(chon_sp)} mã vật tư</b>"
                    
                    fig_trend_1.update_layout(title=title_text, yaxis_title="Đơn giá (VND/EA)", font=dict(size=15), plot_bgcolor='white', hovermode="x unified")
                    
                    fig_trend_1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', categoryorder='category ascending')
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
                ky_goc = col_b1.selectbox("1. Chọn Năm/Tháng Gốc (Làm mốc):", ky_list_tab2, index=0)
                ky_moi = col_b2.selectbox("2. Chọn Năm/Tháng Cần Kiểm Tra:", ky_list_tab2, index=len(ky_list_tab2)-1)
                
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
            col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
            with col_f1: loc_kythang = st.multiselect("🗓️ Năm/Tháng:", sorted(df_compare['Kỳ_Tháng'].unique()))
            with col_f2: loc_nhamay = st.multiselect("🏭 Nhà máy:", sorted(df_compare['Nhà máy'].unique()))
            with col_f3: loc_vattu = st.multiselect("📦 Vật tư:", sorted(df_compare['Vật tư'].unique()))
                
            df_display = df_compare.copy()
            if loc_kythang: df_display = df_display[df_display['Kỳ_Tháng'].isin(loc_kythang)]
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
            display_cols = ['Kỳ_Tháng', 'Nhà máy', 'Vật tư', 'Phiên bản sản xuất', 'Số lượng nhập kho', 'Nguyên giá sản xuất', 'Đơn giá 1 Sp']
            valid_display_cols = [c for c in display_cols if c in df_display.columns]
            df_display_tab3 = df_display[valid_display_cols].copy()
            
            df_display_tab3.rename(columns={'Kỳ_Tháng': 'Năm/Tháng', 'Số lượng nhập kho': 'Số lượng (EA)', 'Nguyên giá sản xuất': 'Chi phí SX (VND)', 'Đơn giá 1 Sp': 'Đơn giá (VND/EA)'}, inplace=True)
            
            if len(df_display_tab3) > 1000:
                st.warning("⚠️ Bảng dữ liệu có hơn 1000 dòng. Hãy dùng bộ lọc để tăng tốc độ xem!")
            
            styled_tab3 = df_display_tab3.style.format({"Số lượng (EA)": "{:,.0f}", "Chi phí SX (VND)": "{:,.0f}", "Đơn giá (VND/EA)": "{:,.0f}"}).set_properties(**{'font-size': '15px'})
            col_config_tab3 = {"Năm/Tháng": st.column_config.TextColumn(width="small"), "Nhà máy": st.column_config.TextColumn(width="small"), "Phiên bản sản xuất": st.column_config.TextColumn(width="small"), "Vật tư": st.column_config.TextColumn(width="medium")}
            st.dataframe(styled_tab3, use_container_width=True, height=800, column_config=col_config_tab3)

        # ----------------------------------------------------
        # TAB 4: MÃ 682
        # ----------------------------------------------------
        with tab4:
            st.markdown("### 📦 BẢNG THỐNG KÊ SỐ LƯỢNG VÀ CHI PHÍ MÃ 682* THEO NHÀ MÁY")
            if df_682_compare is not None and not df_682_compare.empty:
                st.markdown("*(Đơn vị tính: Sản lượng = **EA** | Chi phí = **VND**)*")
                pivot_682 = df_682_compare.pivot_table(index='Nhà máy', columns='Kỳ_Tháng', values=['Số lượng nhập kho', 'Nguyên giá sản xuất'], aggfunc='sum')
                styled_682 = pivot_682.style.format("{:,.0f}", na_rep="-").set_properties(**{'font-size': '15px'})
                st.dataframe(styled_682, use_container_width=True)

        # ----------------------------------------------------
        # TAB 5: ĐỈNH CAO THIẾT KẾ ĐA TẦNG (BỘ LỌC ĐA LỰA CHỌN)
        # ----------------------------------------------------
        with tab5:
            st.markdown("### 📈 BẢNG PHÂN TÍCH XU HƯỚNG ĐƠN GIÁ CHUYÊN SÂU")
            st.info("💡 **BỘ LỌC THÔNG MINH:** Hỗ trợ lọc nhiều điều kiện cùng lúc (cách nhau bằng dấu phẩy). Ví dụ gõ: `6*, 725*, *14D`")
            
            frames_tab5 = []
            if df_compare is not None and not df_compare.empty:
                frames_tab5.append(df_compare)
            if df_6_all_compare is not None and not df_6_all_compare.empty:
                frames_tab5.append(df_6_all_compare)
                
            if frames_tab5:
                df_trend_all = pd.concat(frames_tab5, ignore_index=True)
            else:
                df_trend_all = pd.DataFrame()
            
            if not df_trend_all.empty:
                st.markdown("#### ⚙️ BỘ LỌC ĐIỀU KIỆN TÌM KIẾM")
                
                col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                with col_t1: loc_kythang_t5 = st.multiselect("Năm/Tháng:", sorted(df_trend_all['Kỳ_Tháng'].unique()))
                with col_t2: loc_nha_may_t5 = st.multiselect("Nhà máy:", sorted(df_trend_all['Nhà máy'].unique()))
                with col_t3: 
                    # BỔ SUNG: Thanh lọc đa điều kiện
                    loc_vat_tu_text = st.text_input("🔍 Lọc Ký tự (Hỗ trợ nhập nhiều đ/k, ví dụ: 6*, *14D):", placeholder="Gõ 6*, 7* rồi Enter...")
                    loc_vat_tu_t5 = st.multiselect("Hoặc chọn thủ công:", sorted(df_trend_all['Vật tư'].unique()))
                with col_t4: loc_phien_ban_t5 = st.multiselect("Phiên bản SX:", sorted(df_trend_all['Phiên bản sản xuất'].unique()))
                
                if loc_kythang_t5: df_trend_all = df_trend_all[df_trend_all['Kỳ_Tháng'].isin(loc_kythang_t5)]
                if loc_nha_may_t5: df_trend_all = df_trend_all[df_trend_all['Nhà máy'].isin(loc_nha_may_t5)]
                
                # BỔ SUNG: Xử lý logic lọc nhiều điều kiện cách nhau bằng dấu phẩy hoặc chấm phẩy
                if loc_vat_tu_text:
                    # Tách các điều kiện bằng dấu phẩy hoặc chấm phẩy
                    conditions = [c.strip() for c in re.split(r'[,;]', loc_vat_tu_text) if c.strip()]
                    
                    patterns = []
                    for cond in conditions:
                        if '*' in cond:
                            # Nếu có dấu *, chuyển nó thành regex .* và thêm ^ $ để khớp đầu/đuôi
                            escaped_cond = re.escape(cond).replace(r'\*', '.*')
                            patterns.append(f"^{escaped_cond}$")
                        else:
                            # Nếu không có dấu *, chỉ cần dùng contains bình thường
                            patterns.append(re.escape(cond))
                    
                    # Ghép các điều kiện bằng toán tử OR (|)
                    combined_pattern = "|".join(patterns)
                    
                    # Thực hiện lọc
                    df_trend_all = df_trend_all[df_trend_all['Vật tư'].str.contains(combined_pattern, flags=re.IGNORECASE, regex=True, na=False)]
                        
                if loc_vat_tu_t5: df_trend_all = df_trend_all[df_trend_all['Vật tư'].isin(loc_vat_tu_t5)]
                if loc_phien_ban_t5: df_trend_all = df_trend_all[df_trend_all['Phiên bản sản xuất'].isin(loc_phien_ban_t5)]
                
                st.write("")
                alert_levels = st.multiselect("🎯 LỌC KHOẢNG BIẾN ĐỘNG ĐƠN GIÁ (So với cột tháng liền trước trong bảng - Để trống nếu muốn xem tất cả):", [
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
                    index=['Nhà máy', 'Vật tư', 'Phiên bản sản xuất'], columns='Kỳ_Tháng', values='Đơn giá'
                ).reset_index()
                
                all_months = sorted(trend_grp['Kỳ_Tháng'].unique())
                rename_months = {m: f"{m} (VND/EA)" for m in all_months}
                pivot_trend.rename(columns=rename_months, inplace=True)
                all_months_display = list(rename_months.values())
                
                num_months = len(all_months_display)
                
                latest_variance_vnd = []
                latest_variance_pct = []
                warning_labels = []

                for idx, row in pivot_trend.iterrows():
                    valid_vals = [(m, val) for m, val in zip(all_months_display, row[all_months_display].values) if pd.notna(val)]
                    if len(valid_vals) >= 2:
                        prev_val = valid_vals[-2][1]
                        curr_val = valid_vals[-1][1]
                        diff = curr_val - prev_val
                        pct = (diff / prev_val) * 100 if prev_val > 0 else 0
                    else:
                        diff = 0; pct = 0
                        
                    latest_variance_vnd.append(diff)
                    latest_variance_pct.append(pct)
                    
                    if pct >= 70: label = "🔴 Tăng cực sốc (>70%)"
                    elif 50 <= pct < 70: label = "🔴 Tăng mạnh (50% - 70%)"
                    elif 20 <= pct < 50: label = "🔴 Tăng (20% - 50%)"
                    elif -50 < pct <= -20: label = "🟢 Giảm (-50% đến -20%)"
                    elif -70 < pct <= -50: label = "🟢 Giảm mạnh (-70% đến -50%)"
                    elif pct <= -70: label = "🟢 Giảm cực sốc (<-70%)"
                    else: label = "⚪ Ít biến động (±20%)"
                    
                    if len(valid_vals) < 2: label = "➖ Không đủ dữ liệu"
                    warning_labels.append(label)

                pivot_trend['💸 Chênh lệch (VND)'] = latest_variance_vnd
                pivot_trend['📈 Tỷ lệ (%)'] = latest_variance_pct
                pivot_trend['🎯 Cảnh báo Mức độ'] = warning_labels
                
                rows_to_keep = []
                for idx, row in pivot_trend.iterrows():
                    keep = False
                    if not alert_levels: keep = True
                    else:
                        pct = row['📈 Tỷ lệ (%)']
                        for level in alert_levels:
                            if level == "🟢 Giảm cực sốc (-100% đến -70%)" and pct < -70: keep = True
                            elif level == "🟢 Giảm mạnh (-70% đến -50%)" and -70 <= pct < -50: keep = True
                            elif level == "🟢 Giảm (-50% đến -20%)" and -50 <= pct <= -20: keep = True
                            elif level == "🔴 Tăng (20% đến 50%)" and 20 <= pct <= 50: keep = True
                            elif level == "🔴 Tăng mạnh (50% đến 70%)" and 50 < pct <= 70: keep = True
                            elif level == "🔴 Tăng cực sốc (70% đến 100% trở lên)" and pct >= 70: keep = True
                            if keep: break
                            
                    if keep: rows_to_keep.append(idx)
                
                pivot_filtered = pivot_trend.loc[rows_to_keep].copy()
                
                if pivot_filtered.empty:
                    st.success(f"🎉 Không có mã vật tư nào thỏa mãn các điều kiện bạn vừa chọn.")
                else:
                    cols_to_drop = []
                    if num_months >= 5: cols_to_drop = ['💸 Chênh lệch (VND)', '📈 Tỷ lệ (%)', '🎯 Cảnh báo Mức độ']
                    elif num_months == 4: cols_to_drop = ['🎯 Cảnh báo Mức độ']
                        
                    for c in cols_to_drop:
                        if c in pivot_filtered.columns: pivot_filtered.drop(columns=[c], inplace=True)
                            
                    col_config_tab5 = {
                        "Nhà máy": st.column_config.TextColumn(width="small"),
                        "Vật tư": st.column_config.TextColumn(width="medium"),
                        "Phiên bản sản xuất": st.column_config.TextColumn(width="small"),
                    }
                    if '💸 Chênh lệch (VND)' in pivot_filtered.columns: col_config_tab5["💸 Chênh lệch (VND)"] = st.column_config.TextColumn(width="medium")
                    if '📈 Tỷ lệ (%)' in pivot_filtered.columns: col_config_tab5["📈 Tỷ lệ (%)"] = st.column_config.NumberColumn(width="small")
                    if '🎯 Cảnh báo Mức độ' in pivot_filtered.columns: col_config_tab5["🎯 Cảnh báo Mức độ"] = st.column_config.TextColumn(width="medium")
                    
                    if len(pivot_filtered) > 1000:
                        st.warning(f"⚠️ Dữ liệu lớn (>1000 dòng). Hệ thống tạm TẮT chế độ tô màu để chống đơ máy! Hãy dùng bộ lọc để thu hẹp và bật lại màu.")
                        
                        format_dict_fallback = {col: "{:,.0f}" for col in all_months_display}
                        if '💸 Chênh lệch (VND)' in pivot_filtered.columns: format_dict_fallback['💸 Chênh lệch (VND)'] = "{:+,.0f}"
                        if '📈 Tỷ lệ (%)' in pivot_filtered.columns: format_dict_fallback['📈 Tỷ lệ (%)'] = "{:+,.1f}%"
                        
                        styled_no_color = pivot_filtered.style.format(format_dict_fallback, na_rep="-").set_properties(**{'font-size': '15px'})
                        st.dataframe(styled_no_color, use_container_width=True, height=800, column_config=col_config_tab5)
                    else:
                        st.markdown(f"*(Đang hiển thị **{len(pivot_filtered)}** mã vật tư thỏa mãn điều kiện)*")
                        
                        def style_bg_color(row):
                            styles = pd.Series([''] * len(row), index=row.index)
                            for i in range(1, len(all_months_display)):
                                prev_col = all_months_display[i-1]
                                curr_col = all_months_display[i]
                                if prev_col in row.index and curr_col in row.index:
                                    prev_val = row[prev_col]
                                    curr_val = row[curr_col]
                                    if pd.notna(prev_val) and pd.notna(curr_val) and prev_val > 0:
                                        change = (curr_val - prev_val) / prev_val
                                        pct = change * 100
                                        if pct >= 70: styles[curr_col] = 'background-color: #8b0000; color: white; font-weight: bold;'
                                        elif 50 <= pct < 70: styles[curr_col] = 'background-color: #e60000; color: white; font-weight: bold;'
                                        elif 20 <= pct < 50: styles[curr_col] = 'background-color: #ffcccc; color: black; font-weight: bold;'
                                        elif -100 <= pct < -70: styles[curr_col] = 'background-color: #006400; color: white; font-weight: bold;'
                                        elif -70 <= pct < -50: styles[curr_col] = 'background-color: #008000; color: white; font-weight: bold;'
                                        elif -50 <= pct <= -20: styles[curr_col] = 'background-color: #ccffcc; color: black; font-weight: bold;'
                                    return styles
                            
                        def style_txt_color(row):
                            styles = pd.Series([''] * len(row), index=row.index)
                            for i in range(1, len(all_months_display)):
                                prev_col = all_months_display[i-1]
                                curr_col = all_months_display[i]
                                if prev_col in row.index and curr_col in row.index:
                                    prev_val = row[prev_col]
                                    curr_val = row[curr_col]
                                    if pd.notna(prev_val) and pd.notna(curr_val) and prev_val > 0:
                                        change = (curr_val - prev_val) / prev_val
                                        pct = change * 100
                                        if pct >= 70: styles[curr_col] = 'color: #8b0000; font-weight: bold;'
                                        elif 50 <= pct < 70: styles[curr_col] = 'color: #e60000; font-weight: bold;'
                                        elif 20 <= pct < 50: styles[curr_col] = 'color: #D32F2F; font-weight: bold;'
                                        elif -100 <= pct < -70: styles[curr_col] = 'color: #006400; font-weight: bold;'
                                        elif -70 <= pct < -50: styles[curr_col] = 'color: #008000; font-weight: bold;'
                                        elif -50 <= pct <= -20: styles[curr_col] = 'color: #2E7D32; font-weight: bold;'
                            return styles

                        format_dict = {col: "{:,.0f}" for col in all_months_display}
                        if '💸 Chênh lệch (VND)' in pivot_filtered.columns: format_dict['💸 Chênh lệch (VND)'] = "{:+,.0f}"
                        if '📈 Tỷ lệ (%)' in pivot_filtered.columns: format_dict['📈 Tỷ lệ (%)'] = "{:+,.1f}%"
                        
                        style_func = style_bg_color if num_months >= 5 else style_txt_color
                        styled_pivot = pivot_filtered.style.apply(style_func, axis=1).format(format_dict, na_rep="-").set_properties(**{'font-size': '15px'})
                        
                        st.dataframe(styled_pivot, use_container_width=True, height=800, column_config=col_config_tab5)
            else:
                st.warning("⚠️ Chưa có đủ dữ liệu để vẽ bảng.")
    else:
        st.warning("⚠️ Không tìm thấy dữ liệu hợp lệ. Đảm bảo file có chứa hàng PD và mã vật tư bắt đầu bằng 7 hoặc 6.")
