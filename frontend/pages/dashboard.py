import base64
import streamlit as st


def get_img_as_base64(file_path):
  try:
    with open(file_path, "rb") as f:
      data = f.read()
    return base64.b64encode(data).decode()
  except Exception:
    return ""


def show_dashboard(user_data=None):
  if user_data is None:
    user_data = {
        "name": "Jehad Adel",
        "level": 5,
        "xp_current": 420,
        "xp_max": 500,
        "metrics": {
            "profile_match": 72,
            "skills_mastered": 38,
            "courses_completed": 12,
            "interview_score": 85,
        },
        "crops": [
            {
                "name": "Python & ML",
                "level": "Level 3",
                "status": "شجرة مثمرة وجاهزة للحصاد 🌳",
                "progress": 0.90,
                "color": "#2E7D32",
            },
            {
                "name": "Advanced RAG & LLMs",
                "level": "Level 2",
                "status": "شتلة تنمو بسرعة 🌿",
                "progress": 0.60,
                "color": "#43A047",
            },
            {
                "name": "System Design",
                "level": "Level 4",
                "status": "بذرة جديدة تحت التربة 🌱",
                "progress": 0.30,
                "color": "#81C784",
            },
        ],
    }

  # تحميل الصورة لتحويلها لـ Base64 واستخدامها كخلفية متحركة للبانر
  img_base64 = get_img_as_base64("frontend/assets/farm_poss.png")
  bg_url = (
      f"data:image/png;base64,{img_base64}"
      if img_base64
      else "https://images.unsplash.com/photo-1534528741775-53994a69daeb"
  )

  # حقن كود الـ CSS للأنيميشن (حركة الزوم الخلفي + الظهور المتتابع للنصوص)
  st.markdown(
      f"""
    <style>
        @keyframes zoomEffect {{
            0% {{
                background-size: 100% auto;
            }}
            100% {{
                background-size: 120% auto;
            }}
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .animated-banner {{
            position: relative;
            background-image: linear-gradient(rgba(10, 40, 10, 0.75), rgba(20, 50, 20, 0.75)), url('{bg_url}');
            background-position: center;
            background-repeat: no-repeat;
            animation: zoomEffect 10s ease-out infinite alternate;
            color: white;
            padding: 50px 40px;
            border-radius: 24px;
            box-shadow: 0 15px 35px rgba(27, 94, 32, 0.3);
            margin-bottom: 25px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .fade-in-tag {{
            animation: fadeInUp 1s ease-out 0.2s both;
        }}

        .fade-in-title {{
            animation: fadeInUp 1s ease-out 0.5s both;
        }}

        .fade-in-desc {{
            animation: fadeInUp 1s ease-out 0.8s both;
        }}

        .saas-card {{
            background: #ffffff;
            padding: 22px;
            border-radius: 18px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
            border: 1px solid #e0e0e0;
            transition: all 0.3s ease;
        }}
        .saas-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 30px rgba(46, 125, 50, 0.12);
            border-color: #81C784;
        }}
    </style>
    """,
      unsafe_allow_html=True,
  )

  # 1. البانر الترحيبي المتحرك (سينمائي بالكامل)
  st.markdown(
      """
    <div class="animated-banner">
        <div style="max-width: 700px;">
            <div class="fade-in-tag">
                <span style="background: rgba(255, 193, 7, 0.9); color: #3E2723; padding: 6px 16px; border-radius: 20px; font-size: 0.82rem; font-weight: 800; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">🚜 مقصورة عمدة المزرعة: Jehad Adel</span>
            </div>
            <div class="fade-in-title">
                <h1 style="margin: 18px 0 12px 0; font-size: 2.3rem; font-weight: 800; text-shadow: 0 3px 6px rgba(0,0,0,0.5);">أهلاً بكِ في حظيرة الكارير الذكية!</h1>
            </div>
            <div class="fade-in-desc">
                <p style="margin: 0; font-size: 1.05rem; opacity: 0.95; font-weight: 500; text-shadow: 0 2px 4px rgba(0,0,0,0.5);">المحاصيل البرمجية تنمو بتناغم، وحيوانات المزرعة في انتظار إنجاز المهام لترتوي وتنتج.</p>
            </div>
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # 2. حوار الحيوانات التفاعلي
  st.markdown(
      """
    <div style="background: linear-gradient(135deg, #FFFDE7 0%, #FFF9C4 100%); border: 2px dashed #FBC02D; padding: 18px 24px; border-radius: 18px; display: flex; align-items: center; gap: 20px; margin-bottom: 25px; box-shadow: 0 6px 20px rgba(251, 192, 45, 0.12);">
        <div style="font-size: 3rem; background: white; padding: 10px; border-radius: 50%; box-shadow: 0 4px 10px rgba(0,0,0,0.08);">🐮</div>
        <div style="flex-grow: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <span style="font-weight: 800; color: #F57F17; font-size: 0.95rem;">💬 حظيرة الجوع (مستوى طاقة الحيوانات):</span>
                <span style="background: #E65100; color: white; padding: 2px 10px; border-radius: 10px; font-size: 0.72rem; font-weight: 700;">جائعة جداً 🚨</span>
            </div>
            <div style="color: #37474f; font-size: 1.02rem; font-weight: 700; margin-bottom: 8px;">"يا عمدة بطننا بتصوت من الجوع! 🐄 مفيش أسئلة مقابلة أو تحديث للسي في عشان نتغذى وننتج؟"</div>
        </div>
    </div>
    """,
      unsafe_allow_html=True,
  )

  # 3. بطاقات مؤشرات الأداء الاحترافية (KPI Cards)
  m = user_data["metrics"]
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    st.markdown(
        f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 1.8rem; margin-bottom: 5px;">🎯</div>
            <div style="font-size: 0.75rem; color: #546E7A; font-weight: 700;">Profile Match</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #2E7D32; margin: 6px 0;">{m['profile_match']}%</div>
            <div style="background: #E8F5E9; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px;">
                <div style="background: #2E7D32; width: {m['profile_match']}%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.7rem; color: #43A047; font-weight: 600; margin-top: 6px;">جاهزة للحصاد</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with c2:
    st.markdown(
        f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 1.8rem; margin-bottom: 5px;">🌿</div>
            <div style="font-size: 0.75rem; color: #546E7A; font-weight: 700;">Skills Mastered</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #1976D2; margin: 6px 0;">{m['skills_mastered']}</div>
            <div style="background: #E3F2FD; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px;">
                <div style="background: #1976D2; width: 75%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.7rem; color: #1976D2; font-weight: 600; margin-top: 6px;">مهارات منبتة</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with c3:
    st.markdown(
        f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 1.8rem; margin-bottom: 5px;">📚</div>
            <div style="font-size: 0.75rem; color: #546E7A; font-weight: 700;">Courses Done</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #F57C00; margin: 6px 0;">{m['courses_completed']}</div>
            <div style="background: #FFF3E0; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px;">
                <div style="background: #F57C00; width: 65%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.7rem; color: #F57C00; font-weight: 600; margin-top: 6px;">محاصيل مسقية</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with c4:
    st.markdown(
        f"""
        <div class="saas-card" style="text-align: center;">
            <div style="font-size: 1.8rem; margin-bottom: 5px;">🏆</div>
            <div style="font-size: 0.75rem; color: #546E7A; font-weight: 700;">Interview Score</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #7B1FA2; margin: 6px 0;">{m['interview_score']}%</div>
            <div style="background: #F3E5F5; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px;">
                <div style="background: #7B1FA2; width: {m['interview_score']}%; height: 100%;"></div>
            </div>
            <div style="font-size: 0.7rem; color: #7B1FA2; font-weight: 600; margin-top: 6px;">ممتاز يا عمدة</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.write("")

  # 4. جدول المحاصيل النشطة
  st.markdown(
      """
    <div class="saas-card">
        <h3 style="color: #2E7D32; margin-top: 0; font-size: 1.2rem; margin-bottom: 20px; font-weight: 800;">🌾 حقل المحاصيل النشطة (Active Crops Ecosystem)</h3>
    """,
      unsafe_allow_html=True,
  )

  for crop in user_data["crops"]:
    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 700; margin-bottom: 6px; color: #263238;">
                <span>{crop['name']} <span style="color: #78909C; font-weight: 500; font-size: 0.8rem;">({crop['status']})</span></span>
                <span style="color: {crop['color']}; font-weight: 800;">{int(crop['progress']*100)}%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(crop["progress"])

  st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
  show_dashboard()