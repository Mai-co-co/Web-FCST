import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Cấu hình phông chữ và trang
st.set_page_config(page_title="Hệ thống Kiểm toán SSC Vina", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-family: 'Arial', sans-serif; }
    .audit-report { 
        padding: 30px; 
        background-color: #f8f9fa; 
        border-left: 5px solid #1565C0; 
        border-radius: 5px;
        line-height: 1.8;
    }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM TRÍCH XUẤT DỮ LIỆU ----
def get_data(file):
    try:
        df = pd.read_excel(file)
        def find(kw):
            row = df[df.iloc[:, 0].str.contains(kw, na=False, case=False)]
            return float(row.iloc[0, 3]) if not row.empty else 0
        
        return {
            "Month": file.name.split(".")[0],
            "Revenue": find("DOANH THU THUẦN VỀ BÁN HÀNG"),
            "COGS": abs(find("Giá vốn hàng bán")),
            "GP": find("Lợi nhuận gộp"),
            "Sell_Exp": abs(find("CHI PHÍ BÁN HÀNG")),
            "Admin_Exp": abs(find("CHI PHÍ QUẢN LÝ")),
            "Fin_Exp": abs(find("CHI PHÍ TÀI CHÍNH")),
            "Net_Profit": find("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH")
        }
    except: return None

# ---- SIDEBAR ----
st.sidebar.header("📂 NẠP BÁO CÁO")
uploaded_files = st.sidebar.file_uploader("Tải các file P&L (Tháng 2, 3, 4...)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    results = [get_data(f) for f in uploaded_files if get_data(f)]
    all_df = pd.DataFrame(results)

    # =========================================================
    # BƯỚC 1: BIỂU ĐỒ TRỰC QUAN (ƯU TIÊN ĐẦU TRANG)
    # =========================================================
    st.markdown("### 📈 BIỂU ĐỒ PHÂN TÍCH TÀI CHÍNH")
    
    if len(uploaded_files) == 1:
        d = results[0]
        # Biểu đồ Waterfall (Thác nước) hiện số trực tiếp
        fig = go.Figure(go.Waterfall(
            orientation = "v",
            x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "CP Tài chính", "LN Thuần"],
            y = [d['Revenue'], -d['COGS'], 0, -d['Sell_Exp'], -d['Admin_Exp'], -d['Fin_Exp'], 0],
            measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
            text = [f"{v/1e6:,.1f}M" for v in [d['Revenue'], -d['COGS'], d['GP'], -d['Sell_Exp'], -d['Admin_Exp'], -d['Fin_Exp'], d['Net_Profit']]],
            textposition = "outside",
            decreasing = {"marker":{"color":"#D32F2F"}}, increasing = {"marker":{"color":"#388E3C"}}, totals = {"marker":{"color":"#1976D2"}}
        ))
        fig.update_layout(title=f"Cấu trúc lợi nhuận kỳ {d['Month']} (Đv: Triệu đồng)", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        fig_trend = px.bar(all_df, x="Month", y=["Revenue", "Net_Profit"], barmode="group", text_auto='.2s', title="So sánh biến động qua các kỳ")
        st.plotly_chart(fig_trend, use_container_width=True)

    # =========================================================
    # BƯỚC 2: BẢNG DỮ LIỆU CHI TIẾT
    # =========================================================
    st.write("---")
    with st.expander("📂 CHI TIẾT SỐ LIỆU EXCEL"):
        st.dataframe(all_df.style.format(precision=0), use_container_width=True)

    # =========================================================
    # BƯỚC 3: BÁO CÁO PHÂN TÍCH CHUYÊN SÂU (KHÔNG LỖI HTML)
    # =========================================================
    st.write("---")
    st.header("🩺 CHẨN ĐOÁN SỨC KHỎE TÀI CHÍNH")
    
    d = results[0]
    gp_margin = (d['GP'] / d['Revenue'] * 100) if d['Revenue'] > 0 else 0
    net_margin = (d['Net_Profit'] / d['Revenue'] * 100) if d['Revenue'] > 0 else 0
    sga_ratio = ((d['Sell_Exp'] + d['Admin_Exp']) / d['Revenue'] * 100) if d['Revenue'] > 0 else 0

    # Dùng st.container để bao bọc báo cáo
    with st.container():
        st.markdown(f"""
        ### 1. Đánh giá Hiệu suất và Lợi nhuận
        Với mức doanh thu **{d['Revenue']:,.0f} VNĐ**, biên lợi nhuận gộp đạt **{gp_margin:.2f}%**. 
        Dưới góc độ tài chính, tỷ lệ này cho thấy khả năng sinh lời trực tiếp từ hoạt động sản xuất đang gặp áp lực rất lớn. 
        Nếu biên lợi nhuận gộp thấp hơn 10%, doanh nghiệp nghìn tỷ sẽ rất khó bù đắp được các chi phí cố định (Fixed Costs) khổng lồ của bộ máy vận hành.

        ### 2. Quản trị Chi phí và Rủi ro Vận hành
        Tổng chi phí SGA (Bán hàng & Quản lý) chiếm **{sga_ratio:.2f}%** trên doanh thu. 
        Trong kiểm toán nội bộ, việc chi phí quản lý chiếm tới **{d['Admin_Exp']:,.0f} VNĐ** là một dấu hiệu cần "soi" kỹ các khoản chi phí không tên. 
        Khi biên lợi nhuận ròng rơi xuống mức **{net_margin:.2f}%**, công ty đang ở trạng thái **{"BÁO ĐỘNG" if net_margin < 0 else "CẦN TỐI ƯU"}**.

        ### 3. Kết luận và Kiến nghị
        **Tình trạng:** {"Doanh nghiệp đang 'thua lỗ' về mặt kỹ thuật, cần tái cấu trúc ngay lập tức." if net_margin < 0 else "Doanh nghiệp có lãi nhưng cực kỳ mỏng, rủi ro cao."}
        
        **Kiến nghị:**
        * Rà soát lại định mức tiêu hao nguyên vật liệu để cải thiện biên lợi nhuận gộp.
        * Cắt giảm các khoản chi phí quản lý không trực tiếp tạo ra doanh thu.
        * Theo dõi sát sao dòng tiền để tránh mất thanh khoản trong ngắn hạn.
        """)
        
    st.info("Báo cáo được lập bởi Trưởng ban Phân tích Tài chính AI - SSC Vina")

else:
    st.info("👈 Hãy tải file báo cáo tài chính lên để bắt đầu phân tích.")
