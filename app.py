import streamlit as st
from PIL import Image
import base64
from fpdf import FPDF

# Твоя таблица размеров страз (в мм)
strass_sizes = {
    "SS3 (ок. 1.3 мм)": 1.3,
    "SS5 (1.7-1.9 мм)": 1.8,
    "SS6 (ок. 2.0 мм)": 2.0,
    "SS7 (2.1-2.3 мм)": 2.2,
    "SS8 (ок. 2.4 мм)": 2.4,
    "SS9 (2.5-2.7 мм)": 2.6,
    "SS10 (2.7-2.9 мм)": 2.8,
    "SS12 (ок. 3.1 мм)": 3.1,
    "SS14 (3.4-3.6 мм)": 3.5,
    "SS16 (ок. 4.0 мм)": 4.0,
    "SS17 (4.0-4.2 мм)": 4.1,
    "SS18 (4.2-4.4 мм)": 4.3,
    "SS19 (4.4-4.6 мм)": 4.5,
    "SS20 (ок. 4.8 мм)": 4.8,
    "SS30 (6.3-6.5 мм)": 6.4,
    "SS34 (7.2-7.5 мм)": 7.4,
    "SS40 (ок. 8.5 мм)": 8.5,
    "SS48 (до 11.3 мм)": 11.3,
}

st.set_page_config(page_title="Схема для страз", layout="centered")
st.title("🎨 Генератор схем для страз")
st.markdown("""
Загрузите фотографию, выберите размер страз и количество цветов.
Программа создаст **PDF-схему**, каждую стразинку покажет кружочком, а в конце добавит список нужных цветов.
""")

# Загрузка фото
uploaded_file = st.file_uploader("1. Загрузите изображение", type=["jpg", "jpeg", "png"])

col1, col2, col3 = st.columns(3)
with col1:
    selected_strass = st.selectbox("2. Размер страз", list(strass_sizes.keys()), index=7)
    bead_size_mm = strass_sizes[selected_strass]
with col2:
    num_colors = st.slider("3. Количество цветов", min_value=5, max_value=50, value=25)
with col3:
    desired_width_cm = st.number_input("4. Ширина изделия (см)", min_value=5.0, value=40.0, step=1.0)

if uploaded_file:
    original_image = Image.open(uploaded_file).convert("RGB")
    st.image(original_image, caption="Исходное фото", use_column_width=True)

    # Пересчитываем пиксели под стразы
    beads_per_cm = 10 / bead_size_mm
    target_width_pixels = int(desired_width_cm * beads_per_cm)

    w_percent = target_width_pixels / float(original_image.size[0])
    target_height_pixels = int(float(original_image.size[1]) * w_percent)

    resized_image = original_image.resize((target_width_pixels, target_height_pixels), Image.Resampling.LANCZOS)
    quantized_image = resized_image.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT).convert("RGB")

    st.image(quantized_image, caption=f"Схема: {target_width_pixels} x {target_height_pixels} страз", use_column_width=True)

    # Генерация PDF
    if st.button("📄 Скачать PDF-схему"):
        pdf = FPDF(orientation='L', unit='mm', format='A3')
        pdf.add_page()

        cell_size = min(380 / target_width_pixels, 250 / target_height_pixels)

        for y in range(target_height_pixels):
            for x in range(target_width_pixels):
                r, g, b = quantized_image.getpixel((x, y))
                pdf.set_fill_color(r, g, b)
                cx = x * cell_size + 10 + cell_size/2
                cy = y * cell_size + 10 + cell_size/2
                radius = cell_size / 2 - 0.1
                pdf.circle(cx, cy, radius, 'F')

        # Легенда
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        palette = quantized_image.getcolors()
        if palette:
            y_legend = 15
            for count, color in sorted(palette, reverse=True):
                r, g, b = color
                pdf.set_fill_color(r, g, b)
                pdf.circle(20, y_legend + 3, 3, 'F')
                pdf.text(28, y_legend + 5, f"RGB({r},{g},{b}) — {count} шт.")
                y_legend += 8
                if y_legend > 180:
                    pdf.add_page()
                    y_legend = 15

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="strass_scheme.pdf">💾 Нажмите здесь, чтобы скачать PDF</a>'
        st.markdown(href, unsafe_allow_html=True)
