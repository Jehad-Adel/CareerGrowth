import streamlit as st
from frontend.pages.dashboard import show_dashboard

# إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="CareerFarm | AI Career Platform", page_icon="🌱", layout="wide"
)


# تحميل ملف الـ CSS الموحد
def load_css():
  try:
    with open("frontend/assets/styles.css") as f:
      st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
  except FileNotFoundError:
    pass


load_css()

# القائمة الجانبية الاحترافية (Sidebar)
with st.sidebar:
  # شعار المنصة بأسلوب هادئ وواضح
  st.markdown(
      """
        <div style="display: flex; align-items: center; gap: 12px; padding: 5px 0 25px 5px;">
            <div style="background: #e8f5e9; padding: 10px; border-radius: 14px; font-size: 1.5rem;">🌱</div>
            <div>
                <h2 style="color: #2E7D32; margin: 0; font-weight: 700; font-size: 1.25rem; letter-spacing: -0.5px;">CareerFarm</h2>
                <span style="font-size: 0.75rem; color: #546E7A; font-weight: 500;">AI Career Ecosystem</span>
            </div>
        </div>
    """,
      unsafe_allow_html=True,
  )

  st.markdown(
      """<p style="font-size: 0.75rem; text-transform: uppercase; color: #90A4AE; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px;">Workspace</p>""",
      unsafe_allow_html=True,
  )

  # قائمة التنقل بأسماء واضحة ومباشرة بدون رموز عشوائية
  selected_page = st.sidebar.radio(
      "خريطة المزرعة",
      [
          "🏡 بيت العمدة (Dashboard)",
          "🌾 حقل الشتلات والمهارات",
          "🐑 حظيرة الأغنام (CV & ATS)",
          "🚜 جراج الوظائف",
          "🐮 حظيرة المقابلات (Interview)",
          "⚙️ إعدادات المزرعة",
      ],
      label_visibility="collapsed",
  )

  st.markdown("---")

  # بطاقة معلومات المستخدم السريعة في أسفل الـ Sidebar
  st.markdown(
      """
    <div style="background: linear-gradient(135deg, #f4f9f0 0%, #e8f5e9 100%); padding: 16px; border-radius: 16px; border: 1px solid rgba(46, 125, 50, 0.15); text-align: center;">
        <div style="font-size: 0.9rem; font-weight: 700; color: #2E7D32;">Level 5 Farmer 🌳</div>
        <div style="font-size: 0.78rem; color: #546E7A; margin-top: 4px;">420 / 500 XP to Next Level</div>
        <div style="background: #c8e6c9; border-radius: 10px; height: 6px; width: 100%; margin-top: 10px; overflow: hidden;">
            <div style="background: #2E7D32; width: 84%; height: 100%;"></div>
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )

# التوجيه بناءً على الاختيار النظيف
if "Dashboard" in selected_page:
  show_dashboard()
elif "My Farm" in selected_page:
  st.markdown(
      '<div class="dashboard-title">🌱 My Farm (Skills & Crops)</div>',
      unsafe_allow_html=True,
  )
  st.info(
      "هنا تظهر شاشة مزرعة المهارات الخاصة بالمستخدم وتتبع نمو كل تقنية."
  )
elif "CV Studio" in selected_page:
  st.markdown(
      '<div class="dashboard-title">📄 CV Studio & ATS</div>',
      unsafe_allow_html=True,
  )
  st.info("هنا يتم فحص السيرة الذاتية وتحسين توافقها مع نظام الـ ATS.")
else:
  st.markdown(
      f'<div class="dashboard-title">{selected_page}</div>',
      unsafe_allow_html=True,
  )
  st.info("هذه وحدة من وحدات النظام قيد التشغيل...")