import streamlit as st

st.title("Fayl tizimi")

st.write("""
Fayl tizimi – bu fayllarni saqlash, tartiblash va boshqarish uchun operatsion tizim komponenti.
""")

st.write("""
Mashhur fayl tizimlari:
- NTFS (Windows uchun)  
- ext4 (Linux uchun)  
- APFS (macOS uchun)  
- FAT32 (universalligi bilan mashhur)
""")

st.write("""
Fayl tizimi vazifalari:
- Fayllarni nomlash va kataloglash  
- Fayllarga o‘qish va yozish  
- Fayl xavfsizligini ta’minlash
""")

st.code("""
# Linuxda fayl tizimini ko'rish uchun buyruq:
df -T
""", language='bash')
