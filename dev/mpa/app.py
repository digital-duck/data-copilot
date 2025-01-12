# import streamlit as st
from utils import *

# st.set_page_config(
#     page_title=f'{STR_APP_NAME}',
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

st.logo(
    "https://raw.githubusercontent.com/gongwork/data-copilot/refs/heads/main/docs/st_app_logo.png", 
    icon_image="https://docs.streamlit.io/logo.svg",
    # icon_image="images/icon_blue.png",
)

header_html = f"""
<table style="border: none; border-collapse: collapse; width: 100%; max-width: 1200px;">
    <tr style="border: none;">
        <td style="width: 100px; vertical-align: top; padding: 1rem; border: none;">
            <!-- Icon -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" style="width: 80px; height: 80px;">
                <circle cx="50" cy="50" r="45" fill="#E3F2FD"/>
                <rect x="25" y="60" width="10" height="20" fill="#2196F3"/>
                <rect x="45" y="40" width="10" height="40" fill="#1976D2"/>
                <rect x="65" y="30" width="10" height="50" fill="#0D47A1"/>
                <path d="M25 45 L45 35 L65 25" fill="none" stroke="#4CAF50" stroke-width="3" stroke-linecap="round"/>
                <circle cx="25" cy="45" r="3" fill="#4CAF50"/>
                <circle cx="45" cy="35" r="3" fill="#4CAF50"/>
                <circle cx="65" cy="25" r="3" fill="#4CAF50"/>
                <circle cx="60" cy="40" r="12" fill="none" stroke="#FF5722" stroke-width="3"/>
                <line x1="68" y1="48" x2="75" y2="55" stroke="#FF5722" stroke-width="3" stroke-linecap="round"/>
            </svg>
        </td>
        <td style="vertical-align: top; padding: 1rem; line-height: 1.5; border: none;">
            <!-- Text -->
            <span style="color: red;"><strong>Data-Copilot</strong></span>
is an AI Assistant, speaks both natural language (like English) and machine languages (such as SQL and Python), acts like an interpreter between Analysts and Data, Analysts can now talk to data and derive insight faster than ever. With gained productivity, they can spend more time on deep analysis and strategic decision-making.
        </td>
    </tr>
</table>
"""

msg_features = """
#### <span style="color: black;">Features</span>
- **<span style="color: red;">RAG</span>**: ask dataset-specific question via Retrieval Augmented Generation
    - <span style="color: blue;">Semantic Search</span>: discover data schema
    - <span style="color: blue;">Text-to-SQL</span>: generate SQL from plain text
    - <span style="color: blue;">Data-to-Plot</span>: generate Python code to visualize data 
- **<span style="color: red;">ChatGPT</span>**: ask general question on <span style="color: blue;">Large-Language-Model </span> (LLM) of choice 
- **<span style="color: red;">Data Privacy</span>** (_optional_) : leverage  <span style="color: blue;">Ollama</span> and open-source LLM models locally 
- **<span style="color: red;">Note-Taking</span>**:
- **<span style="color: red;">Knowledge-Sharing</span>**:
- **<span style="color: red;">Chat-History</span>**:
"""

def render_header():
    st.markdown(header_html, unsafe_allow_html=True)

def do_welcome():
    ## Welcome page
    st.markdown(f"""
    ### <span style="color: black;">Self-Service Analytics</span>
    """, unsafe_allow_html=True)

    render_header()

    st.markdown(f"""
    #### <span style="color: black;">Architecture </span>
    """, unsafe_allow_html=True)

    st.image("https://raw.githubusercontent.com/gongwork/data-copilot/refs/heads/main/docs/00-data-copilot-arch-design.png")

    st.markdown(msg_features, unsafe_allow_html=True)



NO_ROLE = ""
if "role" not in st.session_state:
    st.session_state.role = NO_ROLE

role_list = [NO_ROLE, "User_001", "Admin"]


def login():

    do_welcome()

    st.sidebar.subheader("Log in")
    role = st.sidebar.selectbox("Choose a role", role_list)
    if st.sidebar.button("Log in"):
        st.session_state.role = role
        st.rerun()

def logout():
    st.session_state.role = NO_ROLE
    st.rerun()

role = st.session_state.role

login_page = st.Page(
    login,
)

logout_page = st.Page(
    logout, 
    title="Log out", 
    icon=":material/logout:"
)

# grouping pages
account_pages = [logout_page]

configure_page = st.Page(
    "01-🛠Configure.py", 
    title="Configure", 
    icon="🛠",  # ":material/settings:"
)

database_page = st.Page(
    "02-💻DataBase.py", 
    title="Database", 
    icon="💻",  # ":material/settings:"
)

knowledgebase_page = st.Page(
    "03-📚KnowledgeBase.py", 
    title="KnowledgeBase", 
    icon="📚",  # ":material/settings:"
)

# grouping pages
configure_pages = [
    configure_page, database_page, knowledgebase_page,
]

ask_rag_page = st.Page(
    "04-❓Ask-RAG.py", 
    title="Ask-RAG", 
    icon="❓",  # ":material/settings:"
)

# grouping pages
ask_ai_pages = [
    ask_rag_page, 
]

review_qa_page = st.Page(
    "05-🚀QA-Results.py", 
    title="Review-QA", 
    icon="🚀",  # ":material/settings:"
)

# grouping pages
review_pages = [
    review_qa_page, 
]

take_note_page = st.Page(
    "80-📝Notes.py", 
    title="Notes", 
    icon="📝",  # ":material/settings:"
)

# grouping pages
note_pages = [
    take_note_page, 
]

task_dashboard_page = st.Page(
    "90-Task-Dashboard.py", 
    title="Task-Dashboard", 
    icon="📝",  # ":material/settings:"
)

tasks_page = st.Page(
    "91-Tasks.py", 
    title="Tasks", 
    icon="📝",  # ":material/settings:"
)

# grouping pages
manage_task_pages = [
    task_dashboard_page, tasks_page
]

import_csv_page = st.Page(
    "21- 📥Import-DB-from-CSV.py", 
    title="CSV", 
    icon="📥",  # ":material/settings:"
)

import_xlsx_page = st.Page(
    "22- 📥Import-DB-from-XLSX.py", 
    title="XLSX", 
    icon="📥",  # ":material/settings:"
)

import_sqlite_page = st.Page(
    "23- 📥Import-DB-from-SQLite.py", 
    title="SQLite", 
    icon="📥",  # ":material/settings:"
)

# grouping pages
import_db_pages = [
    import_csv_page, import_xlsx_page, import_sqlite_page,
]

evaluate_llm_page = st.Page(
    "70-💯Evaluations.py", 
    title="Evaluate", 
    icon="💯",  # ":material/settings:"
)

thank_you_page = st.Page(
    "99-💜Acknowledge.py", 
    title="Acknowledge", 
    icon="💜",  # ":material/settings:"
)

# grouping pages
misc_pages = [
    evaluate_llm_page, thank_you_page, 
]

page_dict = {}
# if role and (role.startswith("User_") or role in ["Admin"]):
page_dict["Configure"] = configure_pages
page_dict["Ask-AI"] = ask_ai_pages
page_dict["Review"] = review_pages
page_dict["Note"] = note_pages
page_dict["Task"] = manage_task_pages
page_dict["Import"] = import_db_pages
page_dict["Misc"] = misc_pages
# print(f"role = {role}")
# print(f"page_dict = {page_dict}")

page_layout = ({"Account": account_pages} | page_dict) if len(page_dict) > 0 else [login_page]
# if len(page_dict) > 0:
#     pg = st.navigation(page_dict)
# else:
#     pg = st.navigation([login_page])

pg = st.navigation(page_layout)
pg.run()