import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Financial Health Doctor", layout="wide")

st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🏥 BÁC SĨ TÀI CHÍNH: PHÂN TÍCH LÃI LỖ</h1>", unsafe_allow_html=True)
st.write("---")

# ---- SIDEBAR ----
st.sidebar.header("📥 Nạp Dữ Liệu")
uploaded_file = st.sidebar.file_uploader("Tải file P&L (ZFIR8730V...)", type=["xlsx"])

def get_val(df, keyword):
    """Hàm tìm giá trị dựa trên từ khóa trong cột tên chỉ tiêu"""
    try:
        row = df[df.iloc[:, 0].str.contains(keyword, na=False, case=False)]
        return float(row.iloc[0, 3]) # Lấy giá trị ở cột số 4 (chỉ số hiện tại)
    except:
        return 0

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # 1. TRÍCH XUẤT CÁC CHỈ SỐ "SINH TỒN" (Dựa trên cấu trúc file của bạn)
    rev = get_val(df, "DOANH THU THUẦN")
    cogs = get_val(df, "Giá vốn hàng bán")
    gross_profit = get_val(df, "Lợi nhuận gộp")
    selling_exp = get_val(df, "CHI PHÍ BÁN HÀNG")
    admin_exp = get_val(df, "CHI PHÍ QUẢN LÝ")
    fin_exp = get_val(df, "CHI PHÍ TÀI CHÍNH")
    net_profit = get_val(df, "LỢI NHUẬN THUẦN")

    # 2. HIỂN THỊ CÁC THẺ SỨC KHỎE (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Doanh Thu Thuần", f"{rev:,.0f}")
    with col2:
        gp_margin = (gross_profit / rev * 100) if rev != 0 else 0
        st.metric("Biên Lợi Nhuận Gộp", f"{gp_margin:.1f}%", delta="Khỏe" if gp_margin > 20 else "Yếu")
    with col3:
        exp_ratio = ((selling_exp + admin_exp) / rev * 100) if rev != 0 else 0
        st.metric("Tỷ lệ Chi phí/Doanh thu", f"{exp_ratio:.1f}%", delta=f"{exp_ratio:.1f}%", delta_color="inverse")
    with col4:
        st.metric("Lợi Nhuận Cuối Cùng", f"{net_profit:,.0f}", delta="CÓ LÃI" if net_profit > 0 else "LỖ", delta_color="normal" if net_profit > 0 else "inverse")

    st.write("---")

    # 3. BIỂU ĐỒ THÁC NƯỚC (WATERFALL) - PHÂN TÍCH DÒNG TIỀN
    st.subheader("📊 Biểu đồ Thác nước: Từ Doanh thu đến Lợi nhuận thuần")
    
    fig = go.Figure(go.Waterfall(
        name = "P&L", orientation = "v",
        measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
        x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "CP Tài chính", "LN Thuần"],
        textposition = "outside",
        text = [f"{rev:,.0f}", f"{-cogs:,.0f}", f"{gross_profit:,.0f}", f"{-selling_exp:,.0f}", f"{-admin_exp:,.0f}", f"{-fin_exp:,.0f}", f"{net_profit:,.0f}"],
        y = [rev, -cogs, 0, -selling_exp, -admin_exp, -fin_exp, 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        increasing = {"marker":{"color":"#2E7D32"}},
        decreasing = {"marker":{"color":"#C62828"}},
        totals = {"marker":{"color":"#1565C0"}}
    ))
    
    fig.update_layout(title="Phân tích cấu trúc chi phí", showlegend=False, height=600)
    st.plotly_chart(fig, use_container_width=True)

    # 4. PHẦN ĐỌC "BỆNH" TỰ ĐỘNG
    st.subheader("🩺 Chẩn đoán của Bác sĩ IT")
    col_a, col_b = st.columns(2)
    with col_a:
        if net_profit > 0:
            st.success(f"✅ Công ty đang hoạt động CÓ LÃI. Mức sinh lời thuần đạt {net_profit/rev*100:.1f}% trên doanh thu.")
        else:
            st.error("🚨 CẢNH BÁO: Công ty đang LỖ THUẦN. Cần rà soát ngay các khoản chi phí.")
            
    with col_b:
        if fin_exp > (gross_profit * 0.3):
            st.warning("⚠️ Rủi ro: Chi phí tài chính (lãi vay) đang chiếm quá 30% lợi nhuận gộp. Sức khỏe tài chính đang bị đe dọa bởi nợ nần.")
        else:
            st.info("ℹ️ Chi phí vận hành đang ở mức kiểm soát được.")

    # 5. CHI TIẾT BẢNG SỐ
    with st.expander("Xem bảng dữ liệu gốc"):
        st.dataframe(df, use_container_width=True)

else:
    st.info("Hãy tải file báo cáo lãi lỗ ZFIR8730V của bạn lên để bắt đầu khám sức khỏe doanh nghiệp!")
