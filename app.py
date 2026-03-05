import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard FCST Pro", layout="wide")
st.title("Hệ Thống Báo Cáo Sale FCST Tự Động 🚀")

# ---- PHẦN 1: TẢI FILE LÊN ----
st.markdown("### 1. Tải file Excel của bạn lên (Tùy chọn)")
st.info("💡 Mẹo: Bạn có thể kéo thả file báo cáo Excel cũ vào đây, hệ thống sẽ tự đọc!")
uploaded_file = st.file_uploader("Kéo thả file Excel vào đây...", type=["xlsx", "xls"])

# Khởi tạo dữ liệu mặc định nếu chưa ai up file
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Tên nhân viên": ["Ms Phương", "Ms Tươi", "Mr Bình"],
        "Tháng 2": [100, 150, 80],
        "Tháng 3": [120, 160, 90]
    })

# Nếu có file up lên thì đọc luôn file đó
if uploaded_file is not None:
    try:
        st.session_state.df = pd.read_excel(uploaded_file)
        st.success("✅ Đã đọc file Excel thành công! Số liệu đã được cập nhật xuống bảng dưới.")
    except Exception as e:
        st.error("❌ Lỗi đọc file. Vui lòng đảm bảo đó là file Excel chuẩn.")

# ---- PHẦN 2: BẢNG NHẬP LIỆU ----
st.markdown("### 2. Bảng nhập liệu & Chỉnh sửa")
st.write("Bạn có thể sửa số trực tiếp ở bảng này, biểu đồ sẽ nhảy theo ngay lập tức!")

# Hiển thị bảng và cho phép sửa (gán lại vào biến edited_df)
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

# Nút Lưu 
if st.button("Lưu dữ liệu báo cáo"):
    st.session_state.df = edited_df
    st.success("🎉 TUYỆT VỜI! Dữ liệu đã được lưu thành công trên hệ thống!")
    st.balloons() # Thả bóng bay ăn mừng

# ---- PHẦN 3: BIỂU ĐỒ TỰ ĐỘNG ----
st.markdown("### 3. Biểu đồ Báo Cáo Tự Động 📊")

# Xử lý dữ liệu một chút để biểu đồ hiểu được (Lấy cột Tên nhân viên làm mốc)
try:
    chart_data = edited_df.set_index("Tên nhân viên")
    # Vẽ thẳng biểu đồ cột
    st.bar_chart(chart_data)
except Exception as e:
    st.warning("⚠️ Đang chờ dữ liệu hợp lệ để vẽ biểu đồ... Hãy đảm bảo file của bạn có cột 'Tên nhân viên'")
