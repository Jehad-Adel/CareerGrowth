import streamlit as st


def sidebar():

    with st.sidebar:

        st.title("🌱 CareerFarm")

        st.markdown("---")

        page = st.radio(

            "Navigation",

            [

                "🏠 Dashboard",

                "🌱 My Farm",

                "📄 CV Studio",

                "💼 Job Match",

                "🎤 Interview",

                "📚 Learning",

                "📈 Progress",

                "⚙ Settings"

            ]

        )

    return page