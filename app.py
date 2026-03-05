import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Cấu hình trang và Phông chữ hệ thống để tránh lỗi tiếng Việt
st.set_page_config(page_title="Hệ thống Phân tích Tài chính Cao cấp", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Arial', 'Segoe UI', sans-serif;
    }
    .report-box { 
        padding: 40px; 
        background-color: #ffffff; 
        border: 2px solid #e0e0e0; 
        border-radius: 10px; 
        color: #1a1a1a; 
        line-height: 1.8;
        font-size: 16px;
    }
    .section-header {
        color: #0d47a1;
        border-bottom: 2px solid #0d47a1;
        padding-bottom: 5px;
        margin-top: 25px;
        font-weight: bold;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM TRÍCH XUẤT DỮ LIỆU TÀI CHÍNH ----
def get_advanced_data(file):
    try:
        df = pd.read_excel(file)
        def find_val(name):
            row = df[df.iloc[:, 0].str.contains(name, na=False, case=False)]
            return float(row.iloc[0, 3]) if not row.empty else 0
        
        # Lấy dữ liệu theo mẫu ZFIR8730V
        data = {
            "Month": file.name.split(".")[0],
            "DoanhThuThuan": find_val("DOANH THU THUẦN VỀ BÁN HÀNG"),
            "GiaVon": abs(find_val("Giá vốn hàng bán")),
            "LoiNhuanGop": find_val("Lợi nhuận gộp"),
            "CP_BanHang": abs(find_val("CHI PHÍ BÁN HÀNG")),
            "CP_QuanLy": abs(find_val("CHI PHÍ QUẢN LÝ")),
            "CP_TaiChinh": abs(find_val("CHI PHÍ TÀI CHÍNH")),
            "LaiVay": abs(find_val("CHI PHÍ LÃI VAY")),
            "TyGia": abs(find_val("LỖ CHÊNH LỆCH TỶ GIÁ")),
            "LoiNhuanThuan": find_val("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH")
        }
        return data
    except: return None

# ---- SIDEBAR ----
st.sidebar.header("📥 HỆ THỐNG NẠP DỮ LIỆU")
uploaded_files = st.sidebar.file_uploader("Tải các file Báo cáo P&L", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    results = [get_advanced_data(f) for f in uploaded_files if get_advanced_data(f)]
    all_df = pd.DataFrame(results)

    # =========================================================
    # PHẦN 1: BIỂU ĐỒ TỔNG QUAN (ƯU TIÊN LÊN ĐẦU THEO Ý BẠN)
    # =========================================================
    st.markdown("<h2 style='text-align: center;'>📈 BIỂU ĐỒ PHÂN TÍCH THỊ TRƯỜNG & TÀI CHÍNH</h2>", unsafe_allow_html=True)
    
    if len(uploaded_files) == 1:
        # BIỂU ĐỒ THÁC NƯỚC CHO 1 THÁNG
        d = results[0]
        fig_wf = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
            x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "CP Tài chính", "LN Thuần"],
            y = [d['DoanhThuThuan'], -d['GiaVon'], 0, -d['CP_BanHang'], -d['CP_QuanLy'], -d['CP_TaiChinh'], 0],
            text = [f"{v:,.0f}" for v in [d['DoanhThuThuan'], -d['GiaVon'], d['LoiNhuanGop'], -d['CP_BanHang'], -d['CP_QuanLy'], -d['CP_TaiChinh'], d['LoiNhuanThuan']]],
            textposition = "outside",
            decreasing = {"marker":{"color":"#ef5350"}}, 
            increasing = {"marker":{"color":"#66bb6a"}}, 
            totals = {"marker":{"color":"#1565C0"}}
        ))
        fig_wf.update_layout(title="Cấu trúc dòng tiền bị bào mòn bởi chi phí", height=600)
        st.plotly_chart(fig_wf, use_container_width=True)
    else:
        # BIỂU ĐỒ SO SÁNH ĐA THÁNG
        fig_multi = px.bar(all_df, x="Month", y=["DoanhThuThuan", "LoiNhuanThuan"], 
                           barmode="group", text_auto='.2s', title="So sánh Doanh thu và Lợi nhuận qua các kỳ")
        st.plotly_chart(fig_multi, use_container_width=True)

    # =========================================================
    # PHẦN 2: BẢNG DỮ LIỆU EXCEL
    # =========================================================
    st.write("---")
    with st.expander("📂 XEM CHI TIẾT BẢNG SỐ LIỆU EXCEL (DÀNH CHO KẾ TOÁN)"):
        st.dataframe(all_df, use_container_width=True)

    # =========================================================
    # PHẦN 3: BẢN PHÂN TÍCH CHI TIẾT (TỜ A4)
    # =========================================================
    st.write("---")
    st.markdown("### 🩺 KẾT LUẬN & CHẨN ĐOÁN TÌNH HÌNH TÀI CHÍNH")
    
    # Chỉ phân tích chi tiết khi có ít nhất 1 file
    d = results[0]
    # Tính toán các chỉ số kinh tế học
    gp_margin = (d['LoiNhuanGop'] / d['DoanhThuThuan'] * 100)
    net_margin = (d['LoiNhuanThuan'] / d['DoanhThuThuan'] * 100)
    op_exp_ratio = ((d['CP_BanHang'] + d['CP_QuanLy']) / d['DoanhThuThuan'] * 100)
    # Khả năng trả lãi (EBIT / Interest)
    ebit = d['LoiNhuanThuan'] + d['CP_TaiChinh']
    icr = ebit / d['LaiVay'] if d['LaiVay'] > 0 else 999

    report_content = f"""
    <div class="report-box">
        <h2 style="text-align: center; color: #0d47a1;">BÁO CÁO GIÁM SÁT SỨC KHỎE TÀI CHÍNH DOANH NGHIỆP</h2>
        <p style="text-align: center;"><b>Đơn vị: Seoul Semiconductor Vina | Kỳ báo cáo: {d['Month']}</b></p>
        
        <div class="section-header">1. Phân tích Hiệu suất Kinh doanh & Doanh thu</div>
        <p>Ghi nhận doanh thu thuần đạt <b>{d['DoanhThuThuan']:,.0f} VNĐ</b>. Biên lợi nhuận gộp (Gross Margin) đạt <b>{gp_margin:.2f}%</b>. 
        Dưới góc độ kinh tế học, mức biên này cho thấy doanh nghiệp đang giữ được lợi thế cạnh tranh về giá hoặc đang kiểm soát tốt chi phí nguyên vật liệu đầu vào. 
        Tuy nhiên, cần đối soát lại với giá thị trường toàn cầu để đảm bảo không bị ảnh hưởng bởi lạm phát chi phí sản xuất.</p>

        <div class="section-header">2. Kiểm soát Chi phí Vận hành & Hiệu quả Quản trị</div>
        <p>Tổng chi phí bán hàng và quản lý (SGA) chiếm <b>{op_exp_ratio:.2f}%</b> trên doanh thu. 
        Trong kiểm toán, nếu con số này vượt ngưỡng 15% đối với doanh nghiệp sản xuất quy mô lớn, đây là dấu hiệu của sự cồng kềnh trong bộ máy. 
        Đặc biệt, chi phí quản lý doanh nghiệp đang ở mức <b>{d['CP_QuanLy']:,.0f} VNĐ</b>, cần thực hiện rà soát định kỳ các khoản chi bằng tiền khác để tối ưu hóa dòng tiền thuần.</p>

        <div class="section-header">3. Rủi ro Tài chính & Áp lực Đòn bẩy</div>
        <p>Chỉ số khả năng trả lãi (Interest Coverage Ratio - ICR) đạt <b>{icr:.2f}</b>. 
        {"Mức ICR dưới 2.0 là tín hiệu cảnh báo nguy hiểm về khả năng thanh khoản." if icr < 2 else "Mức ICR an toàn, cho thấy doanh nghiệp hoàn toàn đủ khả năng chi trả các khoản lãi vay từ lợi nhuận hoạt động."} 
        Bên cạnh đó, khoản lỗ tỷ giá <b>{d['TyGia']:,.0f} VNĐ</b> cho thấy sự nhạy cảm của doanh nghiệp trước các biến động tiền tệ. Kiến nghị sử dụng các công cụ phái sinh tài chính (Hedging) để bảo vệ lợi nhuận.</p>

        <div class="section-header">4. Kết luận của Ban Kiểm toán</div>
        <p>Dựa trên các chỉ số trên, sức khỏe tài chính của công ty được đánh giá ở mức: 
        <b><span style="color: {'green' if net_margin > 5 else 'red'};">{'ỔN ĐỊNH & PHÁT TRIỂN' if net_margin > 5 else 'CẦN TÁI CẤU TRÚC CHI PHÍ'}</span></b>. 
        Biên lợi nhuận thuần cuối cùng dừng ở <b>{net_margin:.2f}%</b>. Đây là mức sinh lời {"khá" if net_margin > 5 else "thấp"} so với quy mô vốn đầu tư nghìn tỷ.</p>
        
        <p><i><b>Kiến nghị:</b> Tập trung giảm tỷ lệ chi phí cố định (Fixed Costs) và đàm phán lại các điều khoản tín dụng để giảm gánh nặng lãi vay trong các kỳ tiếp theo.</i></p>
    </div>
    """
    st.markdown(report_content, unsafe_allow_html=True)

else:
    st.info("👈 Vui lòng tải file báo cáo tài chính lên để hệ thống phân tích chuyên sâu.")
