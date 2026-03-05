import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình trang mở rộng toàn màn hình
st.set_page_config(page_title="FCST Dashboard Pro", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E88E5;'>📊 HỆ THỐNG BÁO CÁO SALE FCST 2026</h1>", unsafe_allow_html=True)
st.write("---")

# 2. ---- KHU VỰC TẢI FILE (Nằm ở thanh công cụ bên trái) ----
st.sidebar.header("⚙️ BẢNG ĐIỀU KHIỂN")
st.sidebar.info("Tải file Báo cáo Excel của bạn vào đây (VD: ModuleFCST...)")
uploaded_file = st.sidebar.file_uploader("Kéo thả file Excel", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Đọc tên các Sheet có trong file
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        
        # Cho người dùng chọn Sheet
        selected_sheet = st.sidebar.selectbox("📂 Chọn Tháng / Sheet cần xem:", sheet_names)
        
        st.sidebar.markdown("---")
        st.sidebar.warning("⚠️ **Xử lý tiêu đề rác:**\nFile báo cáo thường có các dòng tiêu đề chung ở trên cùng. Hãy tăng số dưới đây cho đến khi bảng dữ liệu hiện ra chuẩn xác tên cột (VD: Qty, Sales, VC...).")
        # Tính năng "Ăn tiền": Bỏ qua các dòng rác ở trên cùng
        skip_rows = st.sidebar.number_input("Số dòng tiêu đề cần bỏ qua:", min_value=0, max_value=20, value=0, step=1)
        
        # Đọc dữ liệu từ Sheet đã chọn với tùy chọn bỏ qua dòng
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet, skiprows=skip_rows)
        
        # Làm sạch cơ bản: Xóa các dòng/cột trống trơn
        df.dropna(how='all', axis=1, inplace=True)
        df.dropna(how='all', axis=0, inplace=True)

        st.success(f"✅ Đã tải thành công dữ liệu từ Sheet: **{selected_sheet}**")

        # 3. ---- HIỂN THỊ DỮ LIỆU & BIỂU ĐỒ ----
        # Chia làm 2 Tab cho gọn gàng
        tab1, tab2 = st.tabs(["📈 Báo Cáo Trực Quan (Dashboard)", "🗄️ Bảng Số Liệu Chi Tiết"])
        
        with tab1:
            st.markdown("### Phân Tích Biểu Đồ Tự Động")
            st.write("Hãy tự chọn Trục ngang và Trục dọc để hệ thống vẽ biểu đồ cho bạn:")
            
            # Khung chọn dữ liệu để vẽ
            col1, col2 = st.columns(2)
            with col1:
                x_axis = st.selectbox("Chọn cột làm Trục ngang (X):", df.columns)
            with col2:
                # Chỉ lấy các cột chứa số để làm trục Y
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if len(numeric_cols) > 0:
                    y_axis = st.selectbox("Chọn cột làm Trục dọc (Y - Giá trị):", numeric_cols)
                else:
                    st.error("Chưa tìm thấy cột số nào. Hãy tăng 'Số dòng tiêu đề cần bỏ qua' ở bên trái để máy tính tìm đúng dòng dữ liệu nhé!")
                    y_axis = None

            # Vẽ biểu đồ Plotly
            if y_axis:
                fig = px.bar(df, x=x_axis, y=y_axis, color=x_axis, text_auto=True,
                             title=f"Biểu đồ {y_axis} phân bổ theo {x_axis}")
                fig.update_layout(xaxis_tickangle=-45) # Nghiêng chữ cho dễ đọc
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 Mẹo: Trỏ chuột vào các cột để xem số chi tiết. Bạn có thể kéo thả để phóng to, hoặc bấm biểu tượng Camera ở góc biểu đồ để tải ảnh về máy.")

        with tab2:
            st.markdown("### Bảng tính chi tiết")
            st.write("Bạn có thể xem toàn bộ dữ liệu gốc đã được làm sạch tại đây:")
            st.dataframe(df, use_container_width=True, height=500)

    except Exception as e:
        st.error(f"❌ Có lỗi xảy ra khi xử lý file: {e}")

else:
    # Màn hình chờ khi chưa có file
    st.info("👈 Hãy tải file Excel của bạn lên từ thanh công cụ bên trái để bắt đầu!")
