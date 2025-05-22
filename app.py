import streamlit as st

st.set_page_config(page_title="Operatsion Tizimlar", layout="wide")

st.title("📚 Operatsion Tizimlar Fani")

st.write("""
**Operatsion tizimlar** — bu kompyuterning apparat va dasturiy ta’minot resurslarini boshqaruvchi dasturiy vosita.  
U foydalanuvchi va kompyuter apparati o‘rtasida vositachi sifatida ishlaydi.  
Bugungi kunda eng mashhur operatsion tizimlarga Windows, Linux, macOS va Unix kiradi.
""")

st.header("Sayt haqida")
st.write("""
Ushbu sayt yordamida siz:
- Operatsion tizimlar asoslari bilan tanishasiz
- Kernel, fayl tizimi kabi asosiy komponentlarni o‘rganasiz
- Operatsion tizimlarning turlari va vazifalari haqida ma’lumot olasiz
- Oddiy Linux buyruqlari va tushunchalar bilan tanishasiz
""")

st.header("Navigatsiya")
st.write("""
Yon menyudan kerakli bo‘limni tanlab, o‘rganishni boshlang.  
Har bir bo‘limda mavzu bo‘yicha qisqacha tushuntirish va kod namunalar mavjud.  
Shuningdek, har bir bo‘lim oxirida amaliy kod bloklari yoki buyruqlar ko‘rsatilgan.
""")

st.header("Qanday foydalanish mumkin?")
st.write("""
1. Yon menyudan mavzuni tanlang  
2. Matnni diqqat bilan o‘qing  
3. Kerak bo‘lsa, ko‘rsatilgan buyruqlarni o‘z Linux terminalingizda sinab ko‘ring  
4. Savollaringiz bo‘lsa, keyingi bo‘limlarda qidirib ko‘ring yoki admin bilan bog‘laning  
""")

st.markdown("---")

st.info("🔔 Bu sayt ta’lim maqsadida tuzilgan va real tizimlarda sinab ko‘rish uchun mos keladi.")

st.write("Yana qo‘shimcha savollar yoki takliflar bo‘lsa, bemalol so‘rashingiz mumkin!")
