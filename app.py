import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Cấu hình trang và Giao diện
st.set_page_config(page_title="SSC Finance Dashboard", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM TRÍCH XUẤT DỮ LIỆU CHUẨN ----
def extract_finance_data(file):
    try:
        df = pd.read_excel(file)
        def get_v(kw):
            mask = df.iloc[:, 0].str.contains(kw, na=False, case=False)
            return float(df[mask].iloc[0, 3]) if not df[mask].empty else 0
        
        # Lấy tên tháng từ tên file để làm trục X
        name = file.name.replace(".xlsx", "").replace("ZFIR8730V ", "").replace("Data", "").strip()
        
        return {
            "Kỳ": name,
            "Doanh Thu Thuần": get_v("DOANH THU THUẦN"),
            "Giá Vốn": abs(get_v("Giá vốn hàng bán")),
            "LN Gộp": get_v("Lợi nhuận gộp"),
            "CP Bán Hàng": abs(get_v("CHI PHÍ BÁN HÀNG")),
            "CP Quản Lý": abs(get_v("CHI PHÍ QUẢN LÝ")),
            "CP Tài Chính": abs(get_v("CHI PHÍ TÀI CHÍNH")),
            "LN Thuần": get_v("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH")
        }
    except: return None

# ---- SIDEBAR ----
st.sidebar.image("https://www.streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
st.sidebar.header("📂 TRUNG TÂM DỮ LIỆU")
uploaded_files = st.sidebar.file_uploader("Nạp các file P&L (Chọn nhiều file cùng lúc)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    # Xử lý gom dữ liệu
    data_list = []
    for f in uploaded_files:
        res = extract_finance_data(f)
        if res: data_list.append(res)
    
    # Sắp xếp theo tên file (giả định tên file có thứ tự tháng)
    all_df = pd.DataFrame(data_list).sort_values(by="Kỳ")

    # =========================================================
    # PHẦN 1: CÁC CHỈ SỐ SỐNG CÒN (TOP METRICS)
    # =========================================================
    latest = all_df.iloc[-1]
    st.markdown(f"## 📊 Tổng quan tài chính kỳ: {latest['Kỳ']}")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Doanh Thu Thuần", f"{latest['Doanh Thu Thuần']:,.0f}")
    m2.metric("Lợi Nhuận Gộp", f"{latest['LN Gộp']:,.0f}", f"{(latest['LN Gộp']/latest['Doanh Thu Thuần']*100):.1f}%")
    m3.metric("Chi Phí Vận Hành", f"{(latest['CP Bán Hàng'] + latest['CP Quản Lý']):,.0f}")
    m4.metric("Lợi Nhuận Thuần", f"{latest['LN Thuần']:,.0f}", f"{(latest['LN Thuần']/latest['Doanh Thu Thuần']*100):.1f}%")

    st.write("---")

    # =========================================================
    # PHẦN 2: BIỂU ĐỒ TRỰC QUAN HÓA (CHART FIRST)
    # =========================================================
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Xu hướng Doanh thu & Lợi nhuận")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=all_df['Kỳ'], y=all_df['Doanh Thu Thuần'], name='Doanh Thu', line=dict(color='#1E88E5', width=4), mode='lines+markers+text', text=[f"{v/1e6:,.0f}M" for v in all_df['Doanh Thu Thuần']], textposition="top center"))
        fig_trend.add_trace(go.Bar(x=all_df['Kỳ'], y=all_df['LN Thuần'], name='LN Thuần', marker_color='#43A047', text=[f"{v/1e6:,.1f}M" for v in all_df['LN Thuần']], textposition="auto"))
        fig_trend.update_layout(height=450, margin=dict(l=20, r=20, t=50, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("🥧 Cơ cấu Chi phí (Kỳ mới nhất)")
        exp_data = {
            "Hạng mục": ["Giá Vốn", "CP Bán Hàng", "CP Quản Lý", "CP Tài Chính"],
            "Giá trị": [latest['Giá Vốn'], latest['CP Bán Hàng'], latest['CP Quản Lý'], latest['CP Tài Chính']]
        }
        fig_pie = px.pie(exp_data, values='Giá trị', names='Hạng mục', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
        fig_pie.update_layout(height=450, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    # =========================================================
    # PHẦN 3: BẢNG EXCEL SO SÁNH (DATA TABLES)
    # =========================================================
    st.write("---")
    st.subheader("📋 Bảng đối soát và So sánh đa kỳ")
    
    # Tạo bảng xoay trục để so sánh các tháng cạnh nhau
    compare_df = all_df.set_index("Kỳ").T
    
    # Định dạng bảng đẹp mắt
    st.dataframe(compare_df.style.format("{:,.0f}").highlight_max(axis=1, color='#e3f2fd').highlight_min(axis=1, color='#ffebee'), use_container_width=True)

    # Phân tích biến động % (Growth Rate)
    if len(all_df) > 1:
        st.write("### 🚀 Tốc độ tăng trưởng so với kỳ trước (%)")
        growth_df = all_df.set_index("Kỳ").pct_change() * 100
        st.dataframe(growth_df.style.format("{:.2f}%").applymap(lambda x: 'color: red' if x < 0 else 'color: green'), use_container_width=True)

else:
    # Giao diện chào mừng khi chưa nạp file
    st.markdown("""
        <div style="text-align: center; padding: 100px;">
            <h1 style="color: #1E88E5;">CHÀO MỪNG ĐẾN VỚI FINANCE HUB</h1>
            <p style="font-size: 20px;">Vui lòng tải các file <b>ZFIR8730V</b> từ thanh bên trái để bắt đầu phân tích!</p>
            <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop" width="600" style="border-radius: 20px; margin-top: 30px;">
        </div>
    """, unsafe_allow_html=True)
