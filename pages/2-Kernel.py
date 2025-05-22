import streamlit as st

st.title("Yadro (Kernel)")

st.write("""
Yadro operatsion tizimning markaziy qismidir va tizim resurslarini boshqaradi.
""")

st.write("""
Yadro turlari:
- Monolitik yadro
- Mikroyadro
- Gibrid yadro
""")

st.write("Kernelning vazifalari:")
st.markdown("""
- Protsesslarni boshqarish  
- Xotira boshqaruvi  
- Qurilmalar bilan aloqalar  
- Fayl tizimi bilan ishlash
""")

st.code("""
# Kernel haqida Linux tizimida ko'rish uchun buyruq:
uname -r
""", language='bash')
