import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Cấu hình trang
st.set_page_config(page_title="Production Cost Dashboard", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="st-"] { font-family: 'Arial', sans-serif; }
    .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 5px solid #0D47A1; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ---- HÀM ĐỌC VÀ XỬ LÝ DỮ LIỆU ----
@st.cache_data(ttl=600) # Lưu cache 10 phút để web chạy nhanh
def process_production_data(file_input, is_url=False):
    try:
        # Nếu là link Google Drive/Google Sheets
        if is_url:
            df = pd.read_excel(file_input) 
        # Nếu là file người dùng upload
        else:
            df = pd.read_csv(file_input) if file_input.name.endswith('.csv') else pd.read_excel(file_input)
        
        df['Vật tư'] = df['Vật tư'].astype(str)
        df = df[(df['Phân loại'] == 'PD') & (df['Vật tư'].str.startswith('7'))]
        
        df['Số lượng nhập kho'] = pd.to_numeric(df['Số lượng nhập kho'], errors='coerce').fillna(0)
        df['Nguyên giá sản xuất'] = pd.to_numeric(df['Nguyên giá sản xuất'], errors='coerce').fillna(0)
        df['Đơn giá 1 Sp'] = df.apply(lambda row: row['Nguyên giá sản xuất'] / row['Số lượng nhập kho'] if row['Số lượng nhập kho'] > 0 else 0, axis=1)
        
        # Gom nhóm chi phí
        nvl_cols = [c for c in df.columns if 'nguyên vật liệu' in c.lower()] + ['Nguyên phụ liệu']
        # Đề phòng trường hợp file không đủ cột
        nvl_cols = [c for c in nvl_cols if c in df.columns] 
        df['Tổng Chi phí NVL'] = df[nvl_cols].sum(axis=1) if nvl_cols else 0
        
        df['Tổng Nhân công'] = df.get('Phí nhân công- trực', 0) + df.get('Phí nhân công- gián', 0)
        df['Tổng CP Sản xuất chung'] = df.get('Chi phí khấu hao', 0) + df.get('Phí vật tư/ sửa chữa', 0) + df.get('Kinh phí-trực tiếp', 0) + df.get('Kinh phí-gián tiếp', 0) + df.get('Phí gia công vendor', 0)
        
        return df
    except Exception as e:
        return None

# =========================================================
# GIAO DIỆN SIDEBAR - Y HỆT SẾP
# =========================================================
st.sidebar.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)

st.sidebar.markdown("### 📁 Personal Data View")
st.sidebar.caption("Only you can see this data; it will be cleared when you close the browser.")
uploaded_file = st.sidebar.file_uploader("Upload your own Excel file", type=["csv", "xlsx"])

# =========================================================
# LOGIC CHỌN DỮ LIỆU THÔNG MINH
# =========================================================
df = None

if uploaded_file is not None:
    # 1. NẾU CÓ NGƯỜI TẢI FILE LÊN -> Ưu tiên dùng file tải lên (chế độ xem tạm thời)
    df = process_production_data(uploaded_file, is_url=False)
    st.info("👀 Đang hiển thị dữ liệu tạm thời từ file của bạn. Dữ liệu này không lưu lại trên hệ thống.")
else:
    # 2. NẾU KHÔNG CÓ FILE TẢI LÊN -> Đọc dữ liệu mặc định từ Google Drive/Google Sheets
    # BẠN HÃY THAY ĐƯỜNG LINK NÀY BẰNG LINK DIRECT GOOGLE DRIVE CỦA BẠN
    # (Đọc hướng dẫn bên dưới để lấy link direct)
    DEFAULT_DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ.../pub?output=xlsx" # <-- Sửa chỗ này
    
    with st.spinner("Đang tải dữ liệu mặc định của hệ thống..."):
        df = process_production_data(DEFAULT_DATA_URL, is_url=True)

# =========================================================
# HIỂN THỊ BIỂU ĐỒ (Giữ nguyên code của bạn)
# =========================================================
if df is not None and not df.empty:
    st.markdown(f"## 🏭 BÁO CÁO GIÁ THÀNH SẢN XUẤT | KỲ {df.get('Kỳ g.sổ', pd.Series(['N/A'])).iloc[0]}/{df.get('Năm tài chính', pd.Series(['N/A'])).iloc[0]}")
    # ... (Copy toàn bộ code vẽ biểu đồ cũ của bạn paste vào đây) ...
else:
    st.warning("⚠️ Không tìm thấy dữ liệu hoặc file lỗi.")
