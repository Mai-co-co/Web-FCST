import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# 1. Cấu hình giao diện và phông chữ
st.set_page_config(page_title="Hệ thống Kiểm toán Tài chính SSC", layout="wide")

st.markdown("""
    <style>
    /* Ép phông chữ Arial toàn trang để không lỗi tiếng Việt */
    html, body, [class*="st-"] {
        font-family: 'Arial', sans-serif !important;
    }
    .report-container {
        padding: 40px;
        background-color: white;
        border: 1px solid #cccccc;
        border-radius: 8px;
        color: #212121;
        line-height: 1.8;
    }
    .main-title { color: #0D47A1; text-align: center; font-weight: bold; }
    .header-audit { color: #1565C0; border-bottom: 2px solid #1565C0; margin-top: 30px; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM TRÍCH XUẤT DỮ LIỆU ----
def get_audit_data(file):
    try:
        df = pd.read_excel(file)
        def find(name):
            row = df[df.iloc[:, 0].str.contains(name, na=False, case=False)]
            return float(row.iloc[0, 3]) if not row.empty else 0
        
        data = {
            "Month": file.name.split(".")[0],
            "Rev": find("DOANH THU THUẦN VỀ BÁN HÀNG"),
            "COGS": abs(find("Giá vốn hàng bán")),
            "GP": find("Lợi nhuận gộp"),
            "Sell_Exp": abs(find("CHI PHÍ BÁN HÀNG")),
            "Admin_Exp": abs(find("CHI PHÍ QUẢN LÝ")),
            "Int_Exp": abs(find("CHI PHÍ LÃI VAY")),
            "Fin_Exp": abs(find("CHI PHÍ TÀI CHÍNH")),
            "FX_Loss": abs(find("LỖ CHÊNH LỆCH TỶ GIÁ")),
            "Net_Profit": find("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH")
        }
        return data
    except: return None

# ---- SIDEBAR ----
st.sidebar.header("📂 NẠP BÁO CÁO")
uploaded_files = st.sidebar.file_uploader("Tải các file P&L (ZFIR8730V)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    results = [get_audit_data(f) for f in uploaded_files if get_audit_data(f)]
    all_df = pd.DataFrame(results)

    # =========================================================
    # PHẦN 1: BIỂU ĐỒ TRỰC QUAN (ƯU TIÊN LÊN ĐẦU)
    # =========================================================
    st.markdown("<h2 class='main-title'>📈 PHÂN TÍCH BIẾN ĐỘNG & CƠ CẤU TÀI CHÍNH</h2>", unsafe_allow_html=True)
    
    if len(uploaded_files) == 1:
        d = results[0]
        # Vẽ biểu đồ Thác nước (Waterfall) có hiện con số
        fig = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
            x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "CP Tài chính", "LN Thuần"],
            y = [d['Rev'], -d['COGS'], 0, -d['Sell_Exp'], -d['Admin_Exp'], -d['Fin_Exp'], 0],
            text = [f"{v/1e6:,.1f}M" for v in [d['Rev'], -d['COGS'], d['GP'], -d['Sell_Exp'], -d['Admin_Exp'], -d['Fin_Exp'], d['Net_Profit']]],
            textposition = "outside",
            decreasing = {"marker":{"color":"#E53935"}},
            increasing = {"marker":{"color":"#43A047"}},
            totals = {"marker":{"color":"#1E88E5"}}
        ))
        fig.update_layout(title=f"Dòng chảy Lợi nhuận kỳ {d['Month']} (Đv: Triệu đồng)", height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Biểu đồ xu hướng đa tháng
        fig_trend = px.line(all_df, x="Month", y=["Rev", "Net_Profit"], markers=True, 
                            title="Xu hướng Doanh thu và Lợi nhuận thuần qua các kỳ")
        fig_trend.update_traces(textposition="top center")
        st.plotly_chart(fig_trend, use_container_width=True)

    # =========================================================
    # PHẦN 2: BẢNG SỐ LIỆU EXCEL (DƯỚI BIỂU ĐỒ)
    # =========================================================
    st.write("---")
    with st.expander("📂 CHI TIẾT SỐ LIỆU TỪ HỆ THỐNG SAP (DÀNH CHO ĐỐI SOÁT)"):
        st.dataframe(all_df.style.format(precision=0), use_container_width=True)

    # =========================================================
    # PHẦN 3: BẢN PHÂN TÍCH CHUYÊN SÂU (TỜ A4 CUỐI TRANG)
    # =========================================================
    st.write("---")
    d = results[0]
    
    # Tính toán các chỉ số kinh tế chuyên sâu
    gp_margin = (d['GP'] / d['Rev'] * 100) if d['Rev'] > 0 else 0
    net_margin = (d['Net_Profit'] / d['Rev'] * 100) if d['Rev'] > 0 else 0
    operating_ratio = ((d['Sell_Exp'] + d['Admin_Exp']) / d['Rev'] * 100) if d['Rev'] > 0 else 0
    ebit = d['Net_Profit'] + d['Fin_Exp']
    icr = ebit / d['Int_Exp'] if d['Int_Exp'] > 0 else 999

    # Toàn bộ nội dung báo cáo A4 gói gọn trong 1 lệnh markdown
    report_html = f"""
    <div class="report-container">
        <h1 style="text-align: center; color: #0D47A1;">BÁO CÁO PHÂN TÍCH TÌNH TRẠNG SỨC KHỎE TÀI CHÍNH</h1>
        <p style="text-align: center; font-style: italic;">Đơn vị thực hiện: Hệ thống Kiểm toán AI | Kỳ báo cáo: {d['Month']}</p>
        
        <div class="header-audit">I. ĐÁNH GIÁ HIỆU SUẤT DOANH THU & SẢN XUẤT</div>
        <p>Với mức doanh thu ghi nhận <b>{d['Rev']:,.0f} VNĐ</b> và Biên lợi nhuận gộp đạt <b>{gp_margin:.2f}%</b>, doanh nghiệp đang thể hiện khả năng kiểm soát giá vốn tương đối ổn định. Tuy nhiên, dưới góc nhìn kiểm toán, cần đặc biệt lưu ý đến các biến động của chi phí nguyên vật liệu trực tiếp. Một sự sụt giảm nhẹ trong biên lợi nhuận gộp cũng có thể kéo theo sự sụt giảm nghiêm trọng của lợi nhuận ròng do quy mô doanh thu nghìn tỷ.</p>

        <div class="header-audit">II. PHÂN TÍCH CHI PHÍ VẬN HÀNH & QUẢN TRỊ (SGA)</div>
        <p>Tỷ lệ chi phí vận hành trên doanh thu đang ở mức <b>{operating_ratio:.2f}%</b>. Trong đó, chi phí quản lý doanh nghiệp ghi nhận <b>{d['Admin_Exp']:,.0f} VNĐ</b>. Đây là khu vực cần được rà soát kỹ lưỡng (Deep-dive) để bóc tách các khoản chi phí không tạo ra giá trị gia tăng (Non-value added costs). Hiệu suất quản trị đang là bài toán then chốt để tối ưu hóa lợi nhuận trong bối cảnh cạnh tranh gay gắt.</p>

        <div class="header-audit">III. RỦI RO ĐÒN BẨY TÀI CHÍNH & NGOẠI HỐI</div>
        <p>Chỉ số khả năng trả lãi (ICR) đạt <b>{icr:.2f}</b>. Đây là con số biết nói về năng lực tài chính của công ty. Với ngưỡng an toàn trên 3.0, doanh nghiệp hiện tại <b>{"có nền tảng tài chính rất vững chắc" if icr > 3 else "đang nằm trong vùng rủi ro về nợ vay"}</b>. Tuy nhiên, khoản lỗ chênh lệch tỷ giá <b>{d['FX_Loss']:,.0f} VNĐ</b> cho thấy sự phơi nhiễm rủi ro ngoại hối rất lớn. Điều này đặc biệt quan trọng đối với một tập đoàn đa quốc gia như Seoul Semiconductor, yêu cầu phải có chiến lược phòng vệ tỷ giá quyết liệt hơn.</p>

        <div class="header-audit">IV. KẾT LUẬN VÀ KIẾN NGHỊ CHIẾN LƯỢC</div>
        <p><b>Tổng kết sức khỏe:</b> Doanh nghiệp đang vận hành <b>{"TRONG TRẠNG THÁI KHỎE MẠNH" if net_margin > 5 else "CẦN TÁI CẤU TRÚC CHI PHÍ KHẨN CẤP"}</b> với biên lợi nhuận ròng đạt <b>{net_margin:.2f}%</b>.</p>
        <p><b>Kiến nghị:</b> <br>
        1. Thực hiện kiểm soát chi phí cố định (Fixed Costs) một cách nghiêm ngặt. <br>
        2. Tối ưu hóa chuỗi cung ứng để giảm giá vốn hàng bán, nhằm nâng biên lợi nhuận gộp lên mục tiêu cao hơn. <br>
        3. Theo dõi sát sao dòng tiền hoạt động (CFO) để đảm bảo khả năng thanh toán ngắn hạn luôn ở mức cao.</p>
        
        <br>
        <p style="text-align: right;"><b>TRƯỞNG BAN PHÂN TÍCH TÀI CHÍNH</b><br><i>(Đã ký bằng hệ thống)</i></p>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)

else:
    st.info("👈 Hãy nạp các file báo cáo ZFIR8730V của bạn để bắt đầu chẩn đoán!")
