import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Multi-Month Financial Doctor", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1565C0;'>🏥 HỆ THỐNG PHÂN TÍCH TÀI CHÍNH ĐA KỲ</h1>", unsafe_allow_html=True)
st.write("---")

# ---- TRÌNH TRÍCH XUẤT DỮ LIỆU THÔNG MINH ----
def get_val(df, keyword):
    try:
        # Tìm dòng chứa từ khóa (không phân biệt hoa thường)
        row = df[df.iloc[:, 0].str.contains(keyword, na=False, case=False)]
        # Lấy giá trị ở cột số 4 (chỉ số thực tế)
        return float(row.iloc[0, 3])
    except:
        return 0

# ---- SIDEBAR: TẢI NHIỀU FILE ----
st.sidebar.header("📥 Kho Báo Cáo")
uploaded_files = st.sidebar.file_uploader(
    "Chọn tất cả các file P&L của bạn:", 
    type=["xlsx"], 
    accept_multiple_files=True # <--- CHÌA KHÓA Ở ĐÂY
)

if uploaded_files:
    # 1. XỬ LÝ TỔNG HỢP (Gom tất cả các file lại)
    all_data = []
    for file in uploaded_files:
        temp_df = pd.read_excel(file)
        # Trích xuất các chỉ số chính
        rev = get_val(temp_df, "DOANH THU THUẦN")
        profit = get_val(temp_df, "LỢI NHUẬN THUẦN")
        # Lưu vào danh sách để so sánh
        all_data.append({
            "FileName": file.name,
            "Revenue": rev,
            "Profit": profit
        })
    
    summary_df = pd.DataFrame(all_data)

    # 2. GIAO DIỆN SO SÁNH TỔNG QUAN
    st.subheader("📈 Biểu đồ Tăng trưởng & Xu hướng")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Biểu đồ đường so sánh Doanh thu qua các file
        fig_rev = px.line(summary_df, x="FileName", y="Revenue", title="Biến động Doanh thu", markers=True)
        st.plotly_chart(fig_rev, use_container_width=True)
        
    with col_chart2:
        # Biểu đồ cột so sánh Lợi nhuận
        fig_profit = px.bar(summary_df, x="FileName", y="Profit", title="So sánh Lợi nhuận thuần", color="Profit", color_continuous_scale="RdYlGn")
        st.plotly_chart(fig_profit, use_container_width=True)

    st.write("---")

    # 3. CHI TIẾT TỪNG THÁNG (Chọn 1 file để xem Waterfall)
    st.subheader("🔍 Phân tích chi tiết từng kỳ")
    selected_file_name = st.selectbox("Chọn một báo cáo cụ thể để xem 'Thác nước tài chính':", [f.name for f in uploaded_files])
    
    # Lấy đúng file đã chọn
    selected_file = next(f for f in uploaded_files if f.name == selected_file_name)
    df_detail = pd.read_excel(selected_file)
    
    # Lấy số liệu chi tiết cho Waterfall
    rev = get_val(df_detail, "DOANH THU THUẦN")
    cogs = get_val(df_detail, "Giá vốn hàng bán")
    gross = get_val(df_detail, "Lợi nhuận gộp")
    sell_exp = get_val(df_detail, "CHI PHÍ BÁN HÀNG")
    adm_exp = get_val(df_detail, "CHI PHÍ QUẢN LÝ")
    net = get_val(df_detail, "LỢI NHUẬN THUẦN")

    # Vẽ biểu đồ Thác nước (Waterfall)
    fig_wf = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "total", "relative", "relative", "total"],
        x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "LN Thuần"],
        y = [rev, -cogs, 0, -sell_exp, -adm_exp, 0],
        increasing = {"marker":{"color":"#2E7D32"}},
        decreasing = {"marker":{"color":"#C62828"}},
        totals = {"marker":{"color":"#1565C0"}}
    ))
    st.plotly_chart(fig_wf, use_container_width=True)
    

else:
    st.info("👈 Hãy chọn và tải lên cùng lúc nhiều file P&L (Tháng 2, 3, 4...) để bắt đầu phân tích xu hướng!")
