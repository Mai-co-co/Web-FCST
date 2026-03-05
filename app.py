import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Cấu hình giao diện rộng và chuyên nghiệp
st.set_page_config(page_title="Financial Health Dashboard", layout="wide")

# CSS để làm giao diện đẹp hơn
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1565C0;'>🏥 HỆ THỐNG GIÁM SÁT SỨC KHỎE TÀI CHÍNH</h1>", unsafe_allow_html=True)
st.write("---")

# ---- HÀM TRÍCH XUẤT DỮ LIỆU THÔNG MINH ----
def extract_metrics(file):
    try:
        df = pd.read_excel(file)
        # Hàm tìm giá trị dựa trên từ khóa ở cột đầu tiên, lấy giá trị ở cột số 3 (index 3)
        def get_v(keyword):
            mask = df.iloc[:, 0].str.contains(keyword, na=False, case=False)
            return abs(float(df[mask].iloc[0, 3])) if not df[mask].empty else 0

        data = {
            "Month": file.name.replace(".xlsx", "").replace("ZFIR8730V- ", ""),
            "Revenue": get_v("DOANH THU THUẦN VỀ BÁN HÀNG"),
            "COGS": get_v("Giá vốn hàng bán"),
            "Gross_Profit": get_v("Lợi nhuận gộp"),
            "Selling_Exp": get_v("CHI PHÍ BÁN HÀNG"),
            "Admin_Exp": get_v("CHI PHÍ QUẢN LÝ"),
            "Fin_Exp": get_v("CHI PHÍ TÀI CHÍNH"),
            "Net_Profit": get_v("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH")
        }
        # Xử lý dấu cho Net Profit (Lợi nhuận có thể âm)
        mask_net = df.iloc[:, 0].str.contains("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH", na=False, case=False)
        data["Net_Profit"] = float(df[mask_net].iloc[0, 3]) if not df[mask_net].empty else 0
        
        return data
    except Exception as e:
        st.error(f"Lỗi khi đọc file {file.name}: {e}")
        return None

# ---- SIDEBAR TẢI FILE ----
st.sidebar.header("📥 Nạp Báo Cáo")
uploaded_files = st.sidebar.file_uploader(
    "Tải một hoặc nhiều file P&L (Tháng 2, 3, 4...)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    # Xử lý tất cả file được tải lên
    results = []
    for f in uploaded_files:
        m = extract_metrics(f)
        if m: results.append(m)
    
    all_df = pd.DataFrame(results)

    # THỨ TỰ ƯU TIÊN 1: NẾU CHỈ CÓ 1 FILE
    if len(uploaded_files) == 1:
        st.subheader(f"📊 Phân tích chi tiết: {all_df.iloc[0]['Month']}")
        res = all_df.iloc[0]
        
        # 1. Thẻ KPI Sức khỏe
        c1, c2, c3, c4 = st.columns(4)
        gp_margin = (res['Gross_Profit'] / res['Revenue'] * 100) if res['Revenue'] != 0 else 0
        net_margin = (res['Net_Profit'] / res['Revenue'] * 100) if res['Revenue'] != 0 else 0
        
        c1.metric("Doanh Thu", f"{res['Revenue']:,.0f}")
        c2.metric("Biên LN Gộp", f"{gp_margin:.1f}%")
        c3.metric("Biên LN Thuần", f"{net_margin:.1f}%")
        c4.metric("Lợi Nhuận", f"{res['Net_Profit']:,.0f}")

        # 2. Biểu đồ Waterfall
        fig_wf = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
            x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "CP Tài chính", "LN Thuần"],
            y = [res['Revenue'], -res['COGS'], 0, -res['Selling_Exp'], -res['Admin_Exp'], -res['Fin_Exp'], 0],
            decreasing = {"marker":{"color":"#ef5350"}},
            increasing = {"marker":{"color":"#66bb6a"}},
            totals = {"marker":{"color":"#42a5f5"}}
        ))
        fig_wf.update_layout(title="Cấu trúc dòng tiền (Thác nước tài chính)", height=500)
        st.plotly_chart(fig_wf, use_container_width=True)

        # 3. Chẩn đoán sức khỏe
        st.markdown("### 🩺 Chẩn đoán của 'Bác sĩ IT'")
        if net_margin < 5:
            st.error("🚩 **Cảnh báo:** Biên lợi nhuận quá thấp. Công ty đang làm rất nhiều nhưng thu về chẳng bao nhiêu.")
        elif gp_margin < 15:
            st.warning("⚠️ **Vấn đề:** Giá vốn hàng bán quá cao. Cần kiểm tra lại nguồn cung ứng hoặc quy trình sản xuất.")
        else:
            st.success("✅ **Sức khỏe tốt:** Các chỉ số tài chính đang ở mức an toàn.")

    # THỨ TỰ ƯU TIÊN 2: NẾU CÓ NHIỀU FILE (SO SÁNH)
    else:
        st.subheader("📈 So sánh biến động giữa các tháng")
        
        # Biểu đồ so sánh Doanh thu và Lợi nhuận
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=all_df['Month'], y=all_df['Revenue'], name='Doanh Thu', line=dict(color='#1565C0', width=4)))
        fig_trend.add_trace(go.Bar(x=all_df['Month'], y=all_df['Net_Profit'], name='Lợi Nhuận Thuần', marker_color='#66bb6a'))
        
        fig_trend.update_layout(title="Xu hướng Doanh thu vs Lợi nhuận qua các kỳ", height=500)
        st.plotly_chart(fig_trend, use_container_width=True)

        # Biểu đồ cơ cấu chi phí theo tháng
        st.write("---")
        st.subheader("🥧 So sánh cơ cấu Chi phí (%)")
        all_df['Total_Exp'] = all_df['Selling_Exp'] + all_df['Admin_Exp'] + all_df['Fin_Exp']
        fig_exp = px.area(all_df, x="Month", y=["Selling_Exp", "Admin_Exp", "Fin_Exp"], 
                          title="Biến động các loại chi phí",
                          labels={"value": "Số tiền", "variable": "Loại chi phí"})
        st.plotly_chart(fig_exp, use_container_width=True)

        # Bảng tổng hợp số liệu
        with st.expander("Xem bảng tổng hợp dữ liệu đa kỳ"):
            st.table(all_df[['Month', 'Revenue', 'Gross_Profit', 'Net_Profit']])

else:
    st.info("👈 Hãy tải file báo cáo tài chính của bạn lên để bắt đầu!")
