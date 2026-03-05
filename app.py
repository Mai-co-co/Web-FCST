import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ... (Giữ phần set_page_config và tiêu đề)

# ---- SIDEBAR: TẢI NHIỀU FILE ----
st.sidebar.header("📥 Kho Dữ Liệu")
# THÊM THAM SỐ: accept_multiple_files=True
uploaded_files = st.sidebar.file_uploader(
    "Tải các file P&L (Tháng 2, 3, 4, 5...)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    # Tạo một danh sách tên file để người dùng chọn file muốn "khám bệnh"
    file_mapping = {f.name: f for f in uploaded_files}
    selected_file_name = st.sidebar.selectbox("🎯 Chọn file để phân tích chi tiết:", list(file_mapping.keys()))
    
    # Lấy file cụ thể mà người dùng chọn
    current_file = file_mapping[selected_file_name]
    
    # --- ĐOẠN CODE XỬ LÝ DỮ LIỆU ---
    # (Sử dụng current_file thay cho uploaded_file như code cũ)
    df = pd.read_excel(current_file)
    
    st.success(f"📌 Đang hiển thị phân tích cho: **{selected_file_name}**")
    
    # ... (Các bước trích xuất Doanh thu, Lợi nhuận và vẽ Waterfall Chart như cũ)
    
    # 💡 Ý TƯỞNG NÂNG CAO: SO SÁNH CÁC THÁNG
    if len(uploaded_files) > 1:
        st.write("---")
        st.subheader("📈 So sánh hiệu quả giữa các tháng")
        
        comparison_data = []
        for f in uploaded_files:
            temp_df = pd.read_excel(f)
            # Giả sử hàm get_val đã được định nghĩa như bài trước
            rev = get_val(temp_df, "DOANH THU THUẦN")
            net_profit = get_val(temp_df, "LỢI NHUẬN THUẦN")
            comparison_data.append({"Month": f.name, "Revenue": rev, "Profit": net_profit})
        
        comp_df = pd.DataFrame(comparison_data)
        
        # Vẽ biểu đồ cột chồng so sánh Doanh thu và Lợi nhuận
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(x=comp_df['Month'], y=comp_df['Revenue'], name='Doanh Thu'))
        fig_comp.add_trace(go.Bar(x=comp_df['Month'], y=comp_df['Profit'], name='Lợi Nhuận'))
        st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.info("👈 Hãy kéo thả cùng lúc nhiều file Excel vào thanh bên trái!")
