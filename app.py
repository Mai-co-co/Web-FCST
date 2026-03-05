import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Hệ thống Kiểm toán & Phân tích Tài chính", layout="wide")

# CSS tạo giao diện báo cáo chuyên nghiệp
st.markdown("""
    <style>
    .report-box { padding: 30px; background-color: white; border: 1px solid #d3d3d3; border-radius: 5px; font-family: 'Times New Roman', Times, serif; color: #333; line-height: 1.6; }
    .report-title { text-align: center; text-transform: uppercase; font-weight: bold; font-size: 24px; margin-bottom: 20px; }
    .section-title { font-weight: bold; font-size: 18px; border-bottom: 2px solid #1565C0; margin-top: 20px; color: #1565C0; }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM TRÍCH XUẤT DỮ LIỆU CHUYÊN SÂU ----
def get_metrics_advanced(file):
    try:
        df = pd.read_excel(file)
        def find(kw):
            row = df[df.iloc[:, 0].str.contains(kw, na=False, case=False)]
            return float(row.iloc[0, 3]) if not row.empty else 0

        # Lấy đầy đủ các chỉ số để phân tích
        data = {
            "Month": file.name,
            "Rev_Gross": find("DOANH THU BÁN HÀNG VÀ CUNG CẤP DỊCH VỤ"),
            "Discounts": find("CÁC KHOẢN GIẢM TRỪ DOANH THU"),
            "Rev_Net": find("DOANH THU THUẦN VỀ BÁN HÀNG"),
            "COGS": find("Giá vốn hàng bán"),
            "GP": find("Lợi nhuận gộp"),
            "Fin_Rev": find("DOANH THU HOẠT ĐỘNG TÀI CHÍNH"),
            "Fin_Exp": find("CHI PHÍ TÀI CHÍNH"),
            "Interest": find("CHI PHÍ LÃI VAY"),
            "Exchange_Loss": find("LỖ CHÊNH LỆCH TỶ GIÁ"),
            "Sell_Exp": find("CHI PHÍ BÁN HÀNG"),
            "Admin_Exp": find("CHI PHÍ QUẢN LÝ"),
            "Net_Profit": find("LỢI NHUẬN THUẦN TỪ HOẠT ĐỘNG KINH DOANH")
        }
        return data
    except: return None

# ---- SIDEBAR ----
st.sidebar.header("📂 NẠP BÁO CÁO TÀI CHÍNH")
uploaded_files = st.sidebar.file_uploader("Tải file ZFIR8730V (Tháng 2, 3, 4...)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    results = [get_metrics_advanced(f) for f in uploaded_files if get_metrics_advanced(f)]
    all_df = pd.DataFrame(results)

    # TRƯỜNG HỢP 1: PHÂN TÍCH CHUYÊN SÂU 1 FILE (VIẾT BÁO CÁO A4)
    if len(uploaded_files) == 1:
        d = results[0]
        # Tính toán các chỉ số kinh tế
        gp_margin = (d['GP'] / d['Rev_Net'] * 100) if d['Rev_Net'] != 0 else 0
        sga_ratio = ((d['Sell_Exp'] + d['Admin_Exp']) / d['Rev_Net'] * 100) if d['Rev_Net'] != 0 else 0
        interest_coverage = (d['GP'] - d['Sell_Exp'] - d['Admin_Exp']) / d['Interest'] if d['Interest'] != 0 else 999
        net_margin = (d['Net_Profit'] / d['Rev_Net'] * 100) if d['Rev_Net'] != 0 else 0

        st.subheader("📝 BÁO CÁO PHÂN TÍCH SỨC KHỎE TÀI CHÍNH CHI TIẾT")
        
        # Giao diện báo cáo tờ A4
        report_html = f"""
        <div class="report-box">
            <div class="report-title">BÁO CÁO PHÂN TÍCH TÌNH HÌNH TÀI CHÍNH</div>
            <p style="text-align: right;"><i>Ngày báo cáo: {d['Month']}</i></p>
            
            <div class="section-title">I. ĐÁNH GIÁ QUY MÔ VÀ DOANH THU</div>
            <p>Doanh thu thuần ghi nhận <b>{d['Rev_Net']:,.0f} VNĐ</b>. Các khoản giảm trừ doanh thu chiếm <b>{(d['Discounts']/d['Rev_Gross']*100):.2f}%</b> trên tổng doanh thu thô. 
            Dưới góc độ kiểm toán, tỷ lệ giảm trừ này cần được đối chiếu với chính sách trả hàng và chiết khấu thương mại để đảm bảo không có sự bất thường trong ghi nhận doanh thu cuối kỳ.</p>
            
            <div class="section-title">II. HIỆU QUẢ SẢN XUẤT VÀ BIÊN LỢI NHUẬN GỘP</div>
            <p>Giá vốn hàng bán (COGS) ở mức <b>{d['COGS']:,.0f} VNĐ</b>, dẫn đến Biên lợi nhuận gộp đạt <b>{gp_margin:.2f}%</b>. 
            {"Mức biên này được đánh giá là khỏe mạnh đối với ngành sản xuất." if gp_margin > 20 else "Cảnh báo: Biên lợi nhuận gộp đang ở mức thấp, phản ánh áp lực từ giá nguyên vật liệu đầu vào hoặc hiệu suất máy móc đang sụt giảm."}</p>
            
            <div class="section-title III. QUẢN TRỊ CHI PHÍ VẬN HÀNH (SGA)</div>
            <p>Tổng chi phí bán hàng và quản lý doanh nghiệp chiếm <b>{sga_ratio:.2f}%</b> trên doanh thu thuần. 
            Theo tiêu chuẩn quản trị tài chính, tỷ lệ này nếu vượt quá 15% sẽ bào mòn lợi nhuận mục tiêu. Cần rà soát các khoản 'Chi phí bằng tiền khác' chiếm <b>{d['Admin_Exp']:,.0f} VNĐ</b> để tìm dư địa cắt giảm.</p>
            
            <div class="section-title">IV. RỦI RO TÀI CHÍNH VÀ CHI PHÍ LÃI VAY</div>
            <p>Chi phí lãi vay ghi nhận <b>{d['Interest']:,.0f} VNĐ</b>. Chỉ số khả năng trả lãi (Interest Coverage Ratio) là <b>{interest_coverage:.2f}</b>. 
            {"Doanh nghiệp đang chịu áp lực nợ vay lớn, rủi ro mất cân đối dòng tiền nếu lãi suất tiếp tục biến động." if interest_coverage < 2 else "Khả năng thanh toán lãi vay tốt, đòn bẩy tài chính đang ở mức an toàn."}</p>
            <p>Lỗ chênh lệch tỷ giá: <b>{d['Exchange_Loss']:,.0f} VNĐ</b>. Đây là yếu tố cần lưu ý đối với doanh nghiệp có hoạt động xuất nhập khẩu lớn như Seoul Semiconductor.</p>

            <div class="section-title">V. KẾT LUẬN VÀ KIẾN NGHỊ</div>
            <p>Lợi nhuận thuần sau cùng đạt <b>{d['Net_Profit']:,.0f} VNĐ</b> (Biên LN thuần: <b>{net_margin:.2f}%</b>). 
            <b>Kết luận:</b> {"Sức khỏe tài chính ỔN ĐỊNH nhưng cần tối ưu chi phí vận hành." if net_margin > 5 else "Sức khỏe tài chính đang ở mức báo động, cần tái cấu trúc danh mục chi phí ngay lập tức."}</p>
        </div>
        """
        st.markdown(report_html, unsafe_allow_html=True)
        
        # Thêm biểu đồ Waterfall bổ trợ bên dưới
        fig_wf = go.Figure(go.Waterfall(
            orientation = "v",
            measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
            x = ["Doanh thu", "Giá vốn", "LN Gộp", "CP Bán hàng", "CP Quản lý", "CP Tài chính", "LN Thuần"],
            y = [d['Rev_Net'], -d['COGS'], 0, -d['Sell_Exp'], -d['Admin_Exp'], -d['Fin_Exp'], 0],
            decreasing = {"marker":{"color":"#ef5350"}}, increasing = {"marker":{"color":"#66bb6a"}}, totals = {"marker":{"color":"#42a5f5"}}
        ))
        st.plotly_chart(fig_wf, use_container_width=True)

    # TRƯỜNG HỢP 2: NHIỀU FILE (SO SÁNH BIẾN ĐỘNG)
    else:
        st.subheader("📈 BÁO CÁO SO SÁNH BIẾN ĐỘNG ĐA KỲ")
        
        # Biểu đồ xu hướng Doanh thu vs LN thuần
        fig_trend = px.line(all_df, x="Month", y=["Rev_Net", "Net_Profit"], title="Xu hướng Tăng trưởng Doanh thu vs Lợi nhuận", markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Biểu đồ so sánh cơ cấu chi phí theo tháng
        st.write("---")
        st.subheader("📊 Phân tích Cơ cấu Chi phí qua các tháng")
        fig_bar = px.bar(all_df, x="Month", y=["COGS", "Sell_Exp", "Admin_Exp", "Fin_Exp"], title="Cấu trúc Chi phí biến động")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Bảng so sánh các chỉ số Margin
        all_df['GP_Margin'] = all_df['GP'] / all_df['Rev_Net'] * 100
        all_df['Net_Margin'] = all_df['Net_Profit'] / all_df['Rev_Net'] * 100
        st.write("### Bảng đối soát các chỉ số Biên lợi nhuận (%)")
        st.table(all_df[['Month', 'Rev_Net', 'GP_Margin', 'Net_Margin']])

else:
    st.info("👈 Hãy tải file báo cáo tài chính của bạn lên để hệ thống bắt đầu phân tích chuyên sâu!")
