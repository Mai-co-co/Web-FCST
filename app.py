import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Cấu hình trang mở rộng toàn màn hình
st.set_page_config(page_title="FCST Dashboard Pro", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E88E5;'>📊 HỆ THỐNG BÁO CÁO SALE FCST 2026</h1>", unsafe_allow_html=True)
st.write("---")

# ---- KHU VỰC TẢI FILE ----
st.sidebar.header("⚙️ Bảng Điều Khiển")
st.sidebar.info("Tải file Báo cáo tổng hợp Excel của bạn vào đây (Ví dụ: file ModuleFCST...)")
uploaded_file = st.sidebar.file_uploader("Kéo thả file Excel", type=["xlsx"])

if uploaded_file is not None:
    # 1. Đọc tên các Sheet trong file Excel
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    
    # 2. Cho người dùng chọn Sheet và chọn Dòng bắt đầu
    selected_sheet = st.sidebar.selectbox("📂 Chọn tháng / Sheet cần xem:", sheet_names)
    
    st.sidebar.markdown("---")
    st.sidebar.write("⚠️ *Vì file công ty thường có tiêu đề thừa ở trên cùng, hãy chỉnh số dòng bỏ qua cho đến khi bảng dữ liệu hiện ra chuẩn xác:*")
    skip_rows = st.sidebar.number_input("Số dòng tiêu đề cần bỏ qua:", min_value=0, max_value=20, value=0, step=1)
    
    try:
        # 3. Đọc dữ liệu từ Sheet đã chọn
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, skiprows=skip_rows)
        
        # Xóa các cột/dòng rỗng hoàn toàn để làm sạch
        df.dropna(how='all', axis=1, inplace=True)
        df.dropna(how='all', axis=0, inplace=True)

        st.success(f"✅ Đã tải thành công dữ liệu từ Sheet: **{selected_sheet}**")

        # ---- HIỂN THỊ DỮ LIỆU ----
        tab1, tab2 = st.tabs(["📈 Báo Cáo Trực Quan (Dashboard)", "🗄️ Bảng Số Liệu Chi Tiết"])
        
        with tab1:
            st.markdown("### 1. Tổng Quan Hiệu Quả (KPI)")
            # Tạo 3 thẻ số liệu (Giả lập việc tính tổng từ các cột có chứa số)
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            
            if len(numeric_cols) >= 2:
                col1, col2, col3 = st.columns(3)
                col1.metric("📌 Số lượng cột dữ liệu số", f"{len(numeric_cols)} cột")
                col2.metric("📌 Tổng số dòng dữ liệu", f"{len(df)} dòng")
                col3.metric("📌 Trạng thái", "Sẵn sàng phân tích", delta="Mượt mà")
                
                st.write("---")
                st.markdown("### 2. Phân Tích Biểu Đồ Tự Động")
                
                # Cho người dùng tự chọn cột để vẽ biểu đồ
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    x_axis = st.selectbox("Chọn cột làm Trục ngang (X):", df.columns)
                with chart_col2:
                    y_axis = st.selectbox("Chọn cột làm Trục dọc (Y - Giá trị):", numeric_cols)

                # Vẽ biểu đồ bằng Plotly
                fig = px.bar(df, x=x_axis, y=y_axis, color=x_axis, title=f"Biểu đồ thể hiện {y_axis} theo {x_axis}")
                fig.update_layout(xaxis_tickangle=-45) # Nghiêng chữ cho dễ đọc
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("Hệ thống chưa tìm thấy cột dữ liệu dạng số nào. Hãy tăng 'Số dòng tiêu đề cần bỏ qua' ở bên thanh công cụ trái!")

        with tab2:
            st.markdown("### Bảng tính chi tiết (Có thể chỉnh sửa)")
            st.write("Dữ liệu gốc từ file Excel. Bạn có thể xem và đối chiếu tại đây:")
            st.dataframe(df, use_container_width=True, height=500)

    except Exception as e:
        st.error(f"❌ Có lỗi xảy ra khi đọc file: {e}")

else:
    # Màn hình chờ khi chưa có file
    st.info("👈 Hãy tải file Excel của bạn lên từ thanh công cụ bên trái để bắt đầu!")
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=2070&auto=format&fit=crop", caption="Giao diện sẽ hiển thị Dashboard khi có dữ liệu", use_container_width=True)
