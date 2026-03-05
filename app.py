import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sale FCST Nội Bộ", layout="wide")
st.title("Bảng nhập liệu Sale FCST 🚀")

st.write("Giao diện nhập liệu giống Excel. Có thể click đúp để sửa, thêm dòng mới ở dưới cùng!")

# Tạo dữ liệu mẫu tạm thời
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Tên nhân viên": ["Ms Phương", "Ms Tươi", "Mr Bình"],
        "Tháng 2": [100, 150, 0],
        "Tháng 3": [120, 160, 0]
    })

# Hiển thị bảng tính cho phép chỉnh sửa (Quyền năng của Streamlit)
edited_df = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)

if st.button("Lưu số liệu"):
    st.session_state.df = edited_df
    st.success("✅ Đã lưu tạm thời trên Web! (Bước tiếp theo Anh IT sẽ hướng dẫn nối dữ liệu này cắm thẳng vào file Google Sheets thật để lưu vĩnh viễn)")
