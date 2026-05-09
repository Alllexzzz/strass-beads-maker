import streamlit as st
from PIL import Image
import numpy as np
import cv2
from fpdf import FPDF
import io
import base64
from rembg import remove
import os

st.set_page_config(page_title="Схема для страз", layout="centered")
st.title("🎨 Генератор схем для страз")
st.markdown("Загрузите фото, выберите параметры и получите схему с адаптивным размером страз.")

# Твоя таблица размеров
strass_sizes = {
    "SS6 (2.0 мм)": 2.0,
    "SS10 (2.8 мм)": 2.8,
    "SS12 (3.1 мм)": 3.1,
    "SS16 (4.0 мм)": 4.0,
    "SS20 (4.8 мм)": 4.8,
    "SS30 (6.4 мм)": 6.4,
    "SS34 (7.4 мм)": 7.4,
    "SS40 (8.5 мм)": 8.5
}

uploaded_file = st.file_uploader("1. Загрузите изображение", type=["jpg", "jpeg", "png"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    remove_bg = st.checkbox("Вырезать объект", value=False)
with col2:
    selected_size = st.selectbox("Размер страз", list(strass_sizes.keys()))
    bead_size_mm = strass_sizes[selected_size]
with col3:
    num_colors = st.slider("Количество цветов", 5, 50, 25)
with col4:
    desired_width_cm = st.number_input("Ширина (см)", 5.0, 100.0, 40.0, 1.0)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    
    # Удаление фона
    if remove_bg:
        with st.spinner("Удаляю фон..."):
            image = remove(image.convert("RGBA")).convert("RGB")
    
    st.image(image, caption="Обработанное фото", use_column_width=True)
    
    # Анализ сложности и создание схемы
    with st.spinner("Создаю схему..."):
        img_array = np.array(image)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Определяем размеры для адаптивной сетки
        block_size = max(10, min(img_array.shape[0], img_array.shape[1]) // 50)
        blocks_h = img_array.shape[0] // block_size
        blocks_w = img_array.shape[1] // block_size
        
        beads_per_cm = 10 / bead_size_mm
        target_width_pixels = int(desired_width_cm * beads_per_cm)
        w_percent = target_width_pixels / float(img_array.shape[1])
        target_height_pixels = int(float(img_array.shape[0]) * w_percent)
        
        # Создаем PDF
        pdf = FPDF(orientation='L', unit='mm', format='A3')
        pdf.add_page()
        
        cell_size = min(380 / target_width_pixels, 250 / target_height_pixels)
        
        for y in range(target_height_pixels):
            for x in range(target_width_pixels):
                # Находим, к какому блоку относится пиксель
                block_y = min(y * blocks_h // target_height_pixels, blocks_h - 1)
                block_x = min(x * blocks_w // target_width_pixels, blocks_w - 1)
                
                # Сложность блока
                block = edges[block_y*block_size:(block_y+1)*block_size,
                             block_x*block_size:(block_x+1)*block_size]
                complexity = np.count_nonzero(block) / (block_size * block_size)
                
                # Размер круга зависит от сложности
                # Сложные участки - мельче, простые - крупнее
                base_radius = cell_size / 2 - 0.1
                if complexity > 0.3:  # Высокая сложность
                    radius = base_radius * 0.6
                elif complexity > 0.1:  # Средняя
                    radius = base_radius * 0.8
                else:  # Низкая
                    radius = base_radius
                
                # Цвет пикселя
                r, g, b = img_array[block_y*block_size + (y * block_size // target_height_pixels) % block_size,
                                    block_x*block_size + (x * block_size // target_width_pixels) % block_size]
                
                pdf.set_fill_color(r, g, b)
                cx = x * cell_size + 10 + cell_size/2
                cy = y * cell_size + 10 + cell_size/2
                pdf.circle(cx, cy, radius, 'F')
        
        # Легенда
        pdf.add_page()
        pdf.set_font("Arial", size=8)
        # Простая легенда без подсчета
        pdf.text(10, 10, "Схема создана с адаптивным размером страз.")
        pdf.text(10, 18, "Мелкие кружки на сложных участках, крупные - на простых.")
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="strass_scheme.pdf">📥 Скачать PDF-схему</a>'
        st.markdown(href, unsafe_allow_html=True)
