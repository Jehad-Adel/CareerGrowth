import streamlit as st

from components.sidebar import sidebar
from pages.dashboard import dashboard


st.set_page_config(

    page_title="CareerFarm",

    page_icon="🌱",

    layout="wide"

)
def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()
hide = """
<style>

#MainMenu{
visibility:hidden;
}

header{
visibility:hidden;
}

footer{
visibility:hidden;
}

</style>
"""

st.markdown(hide,unsafe_allow_html=True)

page = sidebar()

if page == "🏠 Dashboard":

    dashboard()
    st.markdown("""

<style>

.stApp{

background:#F5F7F2;

}

</style>

""",unsafe_allow_html=True)