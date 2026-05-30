import streamlit as st
import sqlite3
import pandas as pd
import secrets
from datetime import date

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect(
    "task_manager.db",
    check_same_thread=False
)

cursor = conn.cursor()

# USERS TABLE

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT,
phone TEXT,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
user_email TEXT,
user_phone TEXT,
task TEXT,
description TEXT,
user_type TEXT,
category TEXT,
priority TEXT,
due_date TEXT,
reminder_days INTEGER,
notes TEXT,
status TEXT,
FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("PRAGMA table_info(tasks)")
task_columns = [column[1] for column in cursor.fetchall()]

if "important" not in task_columns:
    cursor.execute(
        """
        ALTER TABLE tasks
        ADD COLUMN important INTEGER DEFAULT 0
        """
    )

cursor.execute("""
CREATE TABLE IF NOT EXISTS login_sessions(
token TEXT PRIMARY KEY,
user_id INTEGER,
created_at TEXT DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique
ON users(email)
WHERE email IS NOT NULL AND email != ''
""")

cursor.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_unique
ON users(phone)
WHERE phone IS NOT NULL AND phone != ''
""")

conn.commit()

# ---------------- HELPERS ---------------- #

def load_user_tasks(user_id):
    cursor.execute(
        """
        SELECT
        id, task, description, user_type, category, priority,
        due_date, reminder_days, notes, status, important
        FROM tasks
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    user_tasks = []

    for row in cursor.fetchall():
        user_tasks.append({
            "id": row[0],
            "task": row[1],
            "description": row[2],
            "user_type": row[3],
            "category": row[4],
            "priority": row[5],
            "due_date": date.fromisoformat(row[6]),
            "reminder_days": row[7],
            "notes": row[8],
            "status": row[9],
            "important": bool(row[10]),
        })

    return user_tasks

def get_display_status(task, today):
    if (
        task["status"] != "Completed"
        and task["due_date"] < today
    ):
        return "Overdue"

    return task["status"]

def set_logged_in_user(user):
    st.session_state.logged_in = True
    st.session_state.current_user_id = user[0]
    st.session_state.current_user = user[1]
    st.session_state.current_user_email = user[2]
    st.session_state.current_user_phone = user[3]
    st.session_state.nav_page = "Dashboard"
    st.session_state.tasks = load_user_tasks(user[0])

def create_login_session(user_id):
    token = secrets.token_urlsafe(32)

    cursor.execute(
        """
        INSERT INTO login_sessions(token,user_id)
        VALUES(?,?)
        """,
        (token, user_id)
    )

    conn.commit()
    st.query_params["session_token"] = token

def restore_login_session():
    token = st.query_params.get("session_token")

    if not token:
        return

    cursor.execute(
        """
        SELECT users.*
        FROM login_sessions
        JOIN users ON users.id = login_sessions.user_id
        WHERE login_sessions.token=?
        """,
        (token,)
    )

    user = cursor.fetchone()

    if user:
        set_logged_in_user(user)
    else:
        st.query_params.clear()

def clear_login_session():
    token = st.query_params.get("session_token")

    if token:
        cursor.execute(
            """
            DELETE FROM login_sessions
            WHERE token=?
            """,
            (token,)
        )
        conn.commit()

    st.query_params.clear()

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Personal Task Manager",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CUSTOM CSS ---------------- #

st.markdown("""
<style>

:root{
color-scheme:light;
}

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div{
background:#ffffff !important;
color:#0f172a !important;
}

.main-title{
align-items:center;
background:#ffffff;
border-bottom:1px solid #e2e8f0;
box-shadow:0 2px 8px rgba(15,23,42,0.08);
box-sizing:border-box;
display:flex;
min-height:72px;
justify-content:center;
left:0;
margin:0 !important;
position:fixed;
right:0;
text-align:center;
font-family:"Segoe UI", Arial, sans-serif;
font-size:clamp(28px, 3vw, 38px) !important;
font-weight:600;
color:#0f172a;
letter-spacing:0;
line-height:1.15;
top:0;
width:100%;
z-index:999;
}

div[data-testid="stHeading"] h2{
font-size:20px !important;
font-weight:600;
line-height:1.25;
}

section.main > div{
padding-top:1rem;
}

section[data-testid="stSidebar"] > div{
padding-top:5rem;
}

span[data-testid="stHeaderActionElements"]{
display:none !important;
}

.task-card{
background:white;
padding:20px;
border-radius:15px;
margin-bottom:15px;
box-shadow:0px 2px 10px rgba(0,0,0,0.1);
}

.overdue-task-card{
background:#fff1f2;
}

.important-task-card{
box-shadow:0px 2px 14px rgba(245,158,11,0.22);
}

.important-star{
color:#f59e0b;
font-size:22px;
margin-right:8px;
}

.muted-star{
color:#cbd5e1;
font-size:22px;
margin-right:8px;
}

.high{
border-left:8px solid red;
}

.medium{
border-left:8px solid orange;
}

.low{
border-left:8px solid green;
}

.completed{
color:green;
font-weight:bold;
}

.pending{
color:red;
font-weight:bold;
}

.updated{
color:orange;
font-weight:bold;
}

.overdue{
color:#b91c1c;
font-weight:bold;
}

.stButton > button{
width:100%;
border-radius:10px;
height:40px;
font-size:15px;
}

section[data-testid="stSidebar"] .stButton > button{
align-items:center;
background:transparent;
border:0;
border-left:4px solid transparent;
border-radius:0;
box-sizing:border-box;
color:#334155;
display:flex;
font-weight:600;
height:42px;
justify-content:flex-start !important;
min-width:100%;
padding:8px 12px;
text-align:left;
width:100%;
}

section[data-testid="stSidebar"] .stButton > button > div{
align-items:center;
display:flex;
justify-content:flex-start;
width:100%;
}

section[data-testid="stSidebar"] .stButton > button:hover{
background:#eef2ff;
border-left-color:#6366f1;
color:#1e293b;
}

section[data-testid="stSidebar"] div[data-testid="stButton"]{
width:100% !important;
display:block !important;
}

section[data-testid="stSidebar"] div[data-testid="stButton"] > button{
width:100% !important;
}

section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(div[data-testid="stButton"]),
section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(.nav-item-active),
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stButton"]),
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:has(.nav-item-active){
width:100% !important;
max-width:100% !important;
align-self:stretch !important;
}

section[data-testid="stSidebar"] .stButton > button p{
display:block;
margin:0;
padding:0;
text-align:left;
width:100%;
}

.sidebar-title{
color:#64748b;
font-size:13px;
font-weight:700;
letter-spacing:0.04em;
margin:18px 0 8px 0;
text-transform:uppercase;
}

.nav-item-active{
align-items:center;
background:#e0e7ff;
border-left:4px solid #4f46e5;
box-sizing:border-box;
color:#1e293b;
display:flex;
font-size:15px;
font-weight:700;
height:42px;
line-height:1.4;
margin:4px 0;
padding:8px 12px;
text-align:left;
width:100%;
}

[class*="st-key-complete"] div[data-testid="stButton"] > button{
background:#90e2ae !important;
border:1px solid #16a34a !important;
color:#147638 !important;
}

[class*="st-key-complete"] div[data-testid="stButton"] > button:hover{
background:#16a34a !important;
border-color:#15803d !important;
color:#147638 !important;
}

[class*="st-key-update"] div[data-testid="stButton"] > button{
background:#e0e7ff !important;
border:1px solid #4f46e5 !important;
color:#1e293b !important;
}

[class*="st-key-update"] div[data-testid="stButton"] > button:hover{
background:#c7d2fe !important;
border-color:#4338ca !important;
color:#1e293b !important;
}

[class*="st-key-delete"] div[data-testid="stButton"] > button{
background:#fee2e2 !important;
border:1px solid #ef4444 !important;
color:#991b1b !important;
}

[class*="st-key-delete"] div[data-testid="stButton"] > button:hover{
background:#fecaca !important;
border-color:#dc2626 !important;
color:#7f1d1d !important;
}

[class*="st-key-complete"] div[data-testid="stButton"] > button:disabled,
[class*="st-key-update"] div[data-testid="stButton"] > button:disabled,
[class*="st-key-delete"] div[data-testid="stButton"] > button:disabled{
opacity:0.65;
cursor:not-allowed;
}

#MainMenu,
header,
footer,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="manage-app-button"],
[data-testid="stBaseButton-headerNoPadding"],
[data-testid="stBaseButton-header"],
[data-testid="stMainMenu"],
.stDeployButton{
display:none !important;
visibility:hidden !important;
height:0 !important;
}

[data-testid="stAppViewContainer"]{
margin-top:0 !important;
}

[class*="st-key-nav_toggle"]{
align-items:center !important;
background:#ffffff !important;
box-sizing:border-box !important;
display:flex !important;
height:44px !important;
justify-content:center !important;
left:14px !important;
margin:0 !important;
pointer-events:auto !important;
position:fixed !important;
top:14px !important;
width:44px !important;
z-index:5000 !important;
}

[class*="st-key-nav_toggle"] div[data-testid="stButton"] > button{
align-items:center !important;
background:transparent !important;
border:0 !important;
border-radius:8px !important;
box-sizing:border-box !important;
box-shadow:none !important;
color:#0f172a !important;
display:flex !important;
font-size:26px !important;
font-weight:800 !important;
height:44px !important;
justify-content:center !important;
left:14px !important;
line-height:1 !important;
margin:0 !important;
min-height:44px !important;
padding:0 !important;
pointer-events:auto !important;
position:fixed !important;
top:14px !important;
width:44px !important;
z-index:5100 !important;
}

[class*="st-key-nav_toggle"] div[data-testid="stButton"] > button:hover{
background:#f1f5f9 !important;
}

[class*="st-key-nav_close"]{
left:172px !important;
position:fixed !important;
top:14px !important;
width:38px !important;
z-index:5200 !important;
}

[class*="st-key-nav_close"] div[data-testid="stButton"] > button{
background:#334155 !important;
border:0 !important;
border-radius:8px !important;
box-shadow:none !important;
color:#f8fafc !important;
font-size:20px !important;
font-weight:800 !important;
height:38px !important;
min-height:38px !important;
padding:0 !important;
width:38px !important;
}

.app-nav-panel{
background:#1f2937;
border-right:1px solid #111827;
bottom:0;
box-shadow:8px 0 24px rgba(15,23,42,0.24);
left:0;
padding:62px 10px 16px 10px;
position:fixed;
top:0;
width:220px;
z-index:4900;
}

.app-nav-panel-title{
color:#93c5fd;
font-size:12px;
font-weight:700;
letter-spacing:0.04em;
margin:0 0 10px 0;
text-transform:uppercase;
}

[class*="st-key-panel_auth_"],
[class*="st-key-panel_nav_"]{
left:10px !important;
position:fixed !important;
width:200px !important;
z-index:5300 !important;
}

[class*="st-key-panel_auth_"] div[data-testid="stButton"] > button,
[class*="st-key-panel_nav_"] div[data-testid="stButton"] > button{
align-items:center !important;
background:transparent !important;
border:0 !important;
border-radius:8px !important;
box-shadow:none !important;
color:#f8fafc !important;
display:flex !important;
font-size:15px !important;
font-weight:600 !important;
height:42px !important;
justify-content:flex-start !important;
padding:8px 12px !important;
text-align:left !important;
width:200px !important;
}

[class*="st-key-panel_auth_"] div[data-testid="stButton"] > button:hover,
[class*="st-key-panel_nav_"] div[data-testid="stButton"] > button:hover{
background:#334155 !important;
color:#ffffff !important;
}

[class*="st-key-panel_auth_login"],
[class*="st-key-panel_nav_dashboard"]{
top:132px !important;
}

[class*="st-key-panel_auth_register"],
[class*="st-key-panel_nav_add_task"]{
top:178px !important;
}

[class*="st-key-panel_nav_manage_tasks"]{
top:224px !important;
}

[class*="st-key-panel_nav_about"]{
top:270px !important;
}

[class*="st-key-panel_nav_logout"]{
top:316px !important;
}

div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"],
div[data-testid="column"],
.task-card,
.nav-item-active{
max-width:100%;
}

.task-card{
overflow-wrap:anywhere;
word-break:break-word;
}

div[data-testid="stDataFrame"],
div[data-testid="stTable"],
div[data-testid="stJson"]{
overflow-x:auto;
}

@media (max-width: 768px){

.main-title{
font-size:clamp(22px, 6vw, 30px) !important;
line-height:1.12;
min-height:64px;
padding:8px 16px 8px 64px;
position:relative;
text-wrap:balance;
top:auto;
z-index:1;
white-space:normal;
}

.block-container{
padding-left:0.9rem !important;
padding-right:0.9rem !important;
padding-top:1rem !important;
max-width:100% !important;
}

section.main > div{
padding-left:0 !important;
padding-right:0 !important;
padding-top:0 !important;
}

section[data-testid="stSidebar"] > div{
padding-top:1rem;
}

section[data-testid="stSidebar"]{
max-width:82vw !important;
}

.task-card{
border-left-width:6px;
border-radius:12px;
margin-bottom:10px;
padding:14px;
}

.task-card h3{
font-size:20px;
line-height:1.25;
margin-bottom:10px;
}

.task-card p{
font-size:14px;
line-height:1.4;
margin-bottom:8px;
}

.important-star,
.muted-star{
font-size:20px;
margin-right:6px;
}

.stButton > button{
font-size:14px;
height:42px;
min-height:42px;
padding-left:8px;
padding-right:8px;
white-space:normal;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"],
div[data-testid="stDateInput"]{
max-width:100% !important;
}

div[data-testid="stMetric"]{
background:#f8fafc;
border:1px solid #e2e8f0;
border-radius:12px;
padding:10px;
}

}

@media (max-width: 480px){

.main-title{
font-size:clamp(20px, 6vw, 24px) !important;
height:auto;
min-height:58px;
padding-left:64px;
padding-right:12px;
text-align:left;
justify-content:flex-start;
}

[class*="st-key-nav_toggle"]{
top:14px !important;
}

[class*="st-key-nav_toggle"] div[data-testid="stButton"] > button{
top:14px !important;
}

.block-container{
padding-top:1rem !important;
}

div[data-testid="column"]{
min-width:0 !important;
}

}

@media print{
body{
display:none !important;
}
}

</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "show_logout_confirm" not in st.session_state:
    st.session_state.show_logout_confirm = False

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "Login"

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Dashboard"

if "edit_task_id" not in st.session_state:
    st.session_state.edit_task_id = None

if "delete_task_id" not in st.session_state:
    st.session_state.delete_task_id = None

if "show_delete_completed_confirm" not in st.session_state:
    st.session_state.show_delete_completed_confirm = False

if "show_add_task_form" not in st.session_state:
    st.session_state.show_add_task_form = False

if "show_due_today_tasks" not in st.session_state:
    st.session_state.show_due_today_tasks = False

if "show_nav_panel" not in st.session_state:
    st.session_state.show_nav_panel = False

if not st.session_state.logged_in:
    restore_login_session()

if (
    st.session_state.logged_in
    and "current_user_id" not in st.session_state
):
    st.session_state.logged_in = False
    st.session_state.tasks = []

if (
    st.session_state.logged_in
    and "current_user_id" in st.session_state
):
    st.session_state.tasks = load_user_tasks(
        st.session_state.current_user_id
    )

# ---------------- TITLE ---------------- #

st.markdown(
'<p class="main-title">📝 Personal Task Manager</p>',
unsafe_allow_html=True
)

if st.button("☰", key="nav_toggle"):
    st.session_state.show_nav_panel = (
        not st.session_state.show_nav_panel
    )
    st.rerun()

def render_nav_panel():
    st.markdown(
        """
        <div class="app-nav-panel">
        <div class="app-nav-panel-title">Navigation</div>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.logged_in:
        for item, key_name in [
            ("☁ Login", "login"),
            ("👤 Register", "register")
        ]:
            if st.button(item, key=f"panel_auth_{key_name}"):
                auth_page = item.split(" ", 1)[1]
                st.session_state.auth_page = auth_page
                st.session_state.show_nav_panel = False
                st.rerun()
    else:
        for item, key_name, target_page in [
            ("📊 Dashboard", "dashboard", "Dashboard"),
            ("➕ Add Task", "add_task", "Add Task"),
            ("📋 Manage Tasks", "manage_tasks", "Manage Tasks"),
            ("ℹ About", "about", "About"),
            ("⏻ Logout", "logout", "Logout")
        ]:
            if st.button(item, key=f"panel_nav_{key_name}"):
                if target_page == "Logout":
                    st.session_state.show_logout_confirm = True
                else:
                    st.session_state.nav_page = target_page
                    if target_page != "Manage Tasks":
                        st.session_state.edit_task_id = None

                st.session_state.show_nav_panel = False
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.show_nav_panel:
    if st.button("×", key="nav_close"):
        st.session_state.show_nav_panel = False
        st.rerun()

    render_nav_panel()

# ---------------- LOGIN / REGISTER ---------------- #

if not st.session_state.logged_in:

    st.sidebar.markdown(
        '<div class="sidebar-title">Authentication</div>',
        unsafe_allow_html=True
    )

    for auth_item in ["Login", "Register"]:
        if st.session_state.auth_page == auth_item:
            st.sidebar.markdown(
                f'<div class="nav-item-active">{auth_item}</div>',
                unsafe_allow_html=True
            )
        elif st.sidebar.button(auth_item, key=f"auth_{auth_item}"):
            st.session_state.auth_page = auth_item
            st.rerun()

    auth = st.session_state.auth_page

    # ---------------- REGISTER ---------------- #

    if auth == "Register":

        st.header("📝 Register")

        name = st.text_input("Full Name")

        email = st.text_input("Email")

        phone = st.text_input("Phone Number")

        password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        if st.button("Register"):

            email_value = email.strip()
            phone_value = phone.strip()

            if (
                name.strip() != ""
                and password != ""
                and (
                    email_value != ""
                    or phone_value != ""
                )
            ):

                # CHECK EXISTING USER

                existing = None

                if email_value != "":
                    cursor.execute(
                        """
                        SELECT * FROM users
                        WHERE email=?
                        """,
                        (email_value,)
                    )
                    existing = cursor.fetchone()

                if existing is None and phone_value != "":
                    cursor.execute(
                        """
                        SELECT * FROM users
                        WHERE phone=?
                        """,
                        (phone_value,)
                    )
                    existing = cursor.fetchone()

                if existing:

                    st.error(
                        "Email or phone number already exists"
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO users
                    (name,email,phone,password)
                    VALUES(?,?,?,?)
                    """,
                        (
                            name.strip(),
                            email_value,
                            phone_value,
                            password
                        )
                    )

                    conn.commit()

                    st.success(
                        "✅ Registration Successful!"
                    )

            else:

                st.warning(
                    "⚠ Fill Required Fields"
                )

    # ---------------- LOGIN ---------------- #

    elif auth == "Login":

        st.header("🔐 Login")

        login_input = st.text_input(
            "Email or Phone"
        ).strip()

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login"):

            cursor.execute(
                """
                SELECT * FROM users
                WHERE
                (
                    email=?
                    OR phone=?
                )
                AND password=?
                """,
                (
                            login_input.strip(),
                            login_input.strip(),
                            password
                )
            )

            user = cursor.fetchone()

            if user:

                set_logged_in_user(user)

                create_login_session(user[0])

                st.success(
                    "✅ Login Successful!"
                )

                st.rerun()

            else:

                st.error(
                    "❌ Invalid Credentials"
                )

# ---------------- MAIN APP ---------------- #

else:

    @st.dialog("Confirm Logout")
    def confirm_logout():
        st.write("Are you sure you want to logout?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Yes, Logout"):
                clear_login_session()
                st.session_state.logged_in = False
                st.session_state.tasks = []
                st.session_state.show_logout_confirm = False
                st.success(
                    "Logged Out Successfully!"
                )
                st.rerun()

        with col2:
            if st.button("Cancel"):
                st.session_state.show_logout_confirm = False
                st.rerun()

    @st.dialog("Confirm Delete")
    def confirm_delete_task():
        task_to_delete = next(
            (
                task for task in st.session_state.tasks
                if task["id"] == st.session_state.delete_task_id
            ),
            None
        )

        task_name = (
            task_to_delete["task"]
            if task_to_delete else "this task"
        )

        st.warning(f"Are you sure you want to delete '{task_name}'?")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Delete Task"):
                cursor.execute(
                    """
                    DELETE FROM tasks
                    WHERE id=? AND user_id=?
                    """,
                    (
                        st.session_state.delete_task_id,
                        st.session_state.current_user_id
                    )
                )

                conn.commit()

                st.session_state.tasks = load_user_tasks(
                    st.session_state.current_user_id
                )

                st.session_state.delete_task_id = None
                st.session_state.edit_task_id = None

                st.success(
                    "Task deleted successfully!"
                )

                st.rerun()

        with col2:
            if st.button("Cancel"):
                st.session_state.delete_task_id = None
                st.rerun()

    @st.dialog("Remove Completed Tasks")
    def confirm_delete_completed_tasks():
        completed_count = len([
            task for task in st.session_state.tasks
            if task["status"] == "Completed"
        ])

        st.warning(
            f"Are you sure you want to delete all {completed_count} completed task(s)?"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Remove Completed"):
                cursor.execute(
                    """
                    DELETE FROM tasks
                    WHERE user_id=? AND status=?
                    """,
                    (
                        st.session_state.current_user_id,
                        "Completed"
                    )
                )

                conn.commit()

                st.session_state.tasks = load_user_tasks(
                    st.session_state.current_user_id
                )

                st.session_state.show_delete_completed_confirm = False
                st.session_state.edit_task_id = None
                st.session_state.delete_task_id = None

                st.success(
                    "Completed tasks removed successfully!"
                )

                st.rerun()

        with col2:
            if st.button("Cancel"):
                st.session_state.show_delete_completed_confirm = False
                st.rerun()

    st.sidebar.success(
        f"Welcome {st.session_state.current_user}"
    )

    st.sidebar.markdown(
        '<div class="sidebar-title">Navigation</div>',
        unsafe_allow_html=True
    )

    for nav_item in ["Dashboard", "Add Task", "Manage Tasks", "About", "Logout"]:
        if nav_item != "Logout" and st.session_state.nav_page == nav_item:
            st.sidebar.markdown(
                f'<div class="nav-item-active">{nav_item}</div>',
                unsafe_allow_html=True
            )
        elif st.sidebar.button(nav_item, key=f"nav_{nav_item}"):
            if nav_item == "Logout":
                st.session_state.show_logout_confirm = True
            else:
                st.session_state.nav_page = nav_item
                if nav_item != "Manage Tasks":
                    st.session_state.edit_task_id = None
            st.rerun()

    menu = st.session_state.nav_page

    # ---------------- HOME ---------------- #

    if menu == "Add Task":

        st.session_state.show_add_task_form = True

        if (
            st.session_state.edit_task_id is None
            and st.session_state.show_add_task_form
        ):
            st.header("➕ Add New Task")

            task_name = st.text_input(
                "Task Name"
            )

            description = st.text_area(
                "Description"
            )

            user_type = st.selectbox(
                "User Type",
                [
                    "Student",
                    "Teacher",
                    "Employee",
                    "Personal User"
                ]
            )

            category = st.selectbox(
                "Category",
                [
                    "Study",
                    "Assignment",
                    "Teaching",
                    "Meeting",
                    "Office Work",
                    "Health",
                    "Personal"
                ]
            )

            priority = st.selectbox(
                "Priority",
                [
                    "High",
                    "Medium",
                    "Low"
                ]
            )

            due_date = st.date_input(
                "Due Date",
                min_value=date.today()
            )

            reminder_days = st.selectbox(
                "Reminder Before Due Date",
                [1,2,3]
            )

            important = st.checkbox(
                "Mark as Important"
            )

            notes = st.text_area("Notes")

            # ADD TASK

            if st.button("Add Task"):

                if task_name != "":

                    cursor.execute(
                        """
                        INSERT INTO tasks
                        (
                            user_id,user_email,user_phone,task,description,
                            user_type,category,priority,due_date,
                            reminder_days,notes,status,important
                        )
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """,
                        (
                            st.session_state.current_user_id,
                            st.session_state.current_user_email,
                            st.session_state.current_user_phone,
                            task_name,
                            description,
                            user_type,
                            category,
                            priority,
                            str(due_date),
                            reminder_days,
                            notes,
                            "Pending",
                            int(important)
                        )
                    )

                    conn.commit()

                    st.session_state.tasks = load_user_tasks(
                        st.session_state.current_user_id
                    )

                    st.session_state.show_add_task_form = True

                    st.success(
                        "✅ Task Added Successfully!"
                    )

                else:

                    st.warning(
                        "⚠ Enter Task Name"
                    )

            st.write("---")

    elif menu == "Manage Tasks":

        if st.session_state.edit_task_id is not None:
            edit_task = next(
                (
                    task
                    for task in st.session_state.tasks
                    if task["id"] == st.session_state.edit_task_id
                ),
                None
            )

            if edit_task:
                st.header("Edit Task")

                user_type_options = [
                    "Student",
                    "Teacher",
                    "Employee",
                    "Personal User"
                ]

                category_options = [
                    "Study",
                    "Assignment",
                    "Teaching",
                    "Meeting",
                    "Office Work",
                    "Health",
                    "Personal"
                ]

                priority_options = [
                    "High",
                    "Medium",
                    "Low"
                ]

                status_options = [
                    "Pending",
                    "Completed",
                    "Updated"
                ]

                with st.form(
                    key=f"edit_task_form_{edit_task['id']}"
                ):
                    edit_task_name = st.text_input(
                        "Task Name",
                        value=edit_task["task"]
                    )

                    edit_description = st.text_area(
                        "Description",
                        value=edit_task["description"]
                    )

                    edit_user_type = st.selectbox(
                        "User Type",
                        user_type_options,
                        index=user_type_options.index(
                            edit_task["user_type"]
                        )
                    )

                    edit_category = st.selectbox(
                        "Category",
                        category_options,
                        index=category_options.index(
                            edit_task["category"]
                        )
                    )

                    edit_priority = st.selectbox(
                        "Priority",
                        priority_options,
                        index=priority_options.index(
                            edit_task["priority"]
                        )
                    )

                    edit_due_date = st.date_input(
                        "Due Date",
                        value=max(edit_task["due_date"], date.today()),
                        min_value=date.today()
                    )

                    edit_reminder_days = st.selectbox(
                        "Reminder Before Due Date",
                        [1, 2, 3],
                        index=[1, 2, 3].index(
                            edit_task["reminder_days"]
                        )
                    )

                    edit_important = st.checkbox(
                        "Mark as Important",
                        value=edit_task["important"]
                    )

                    edit_notes = st.text_area(
                        "Notes",
                        value=edit_task["notes"]
                    )

                    edit_status = st.selectbox(
                        "Status",
                        status_options,
                        index=status_options.index(
                            edit_task["status"]
                        )
                    )

                    save_col, cancel_col = st.columns(2)

                    with save_col:
                        save_changes = st.form_submit_button(
                            "Save Changes"
                        )

                    with cancel_col:
                        cancel_edit = st.form_submit_button(
                            "Cancel"
                        )

                if save_changes:
                    if edit_task_name.strip() != "":
                        cursor.execute(
                            """
                            UPDATE tasks
                            SET
                            task=?,
                            description=?,
                            user_type=?,
                            category=?,
                            priority=?,
                            due_date=?,
                            reminder_days=?,
                            notes=?,
                            status=?,
                            important=?
                            WHERE id=? AND user_id=?
                            """,
                            (
                                edit_task_name,
                                edit_description,
                                edit_user_type,
                                edit_category,
                                edit_priority,
                                str(edit_due_date),
                                edit_reminder_days,
                                edit_notes,
                                edit_status,
                                int(edit_important),
                                edit_task["id"],
                                st.session_state.current_user_id
                            )
                        )

                        conn.commit()

                        st.session_state.tasks = load_user_tasks(
                            st.session_state.current_user_id
                        )

                        st.session_state.edit_task_id = None

                        st.success(
                            "Task updated successfully!"
                        )

                        st.rerun()

                    else:
                        st.warning(
                            "Enter Task Name"
                        )

                if cancel_edit:
                    st.session_state.edit_task_id = None
                    st.rerun()

                st.write("---")

        # SEARCH

        search = st.text_input(
            "🔍 Search Task"
        )

        st.header("📋 Task List")

        completed_task_count = len([
            task for task in st.session_state.tasks
            if task["status"] == "Completed"
        ])

        if st.button(
            "Remove All Completed Tasks",
            disabled=completed_task_count == 0
        ):
            st.session_state.show_delete_completed_confirm = True
            st.rerun()

        today = date.today()

        if st.button(
            (
                "Show Regular Tasks"
                if st.session_state.show_due_today_tasks
                else "Show Due & Today's Tasks"
            )
        ):
            st.session_state.show_due_today_tasks = (
                not st.session_state.show_due_today_tasks
            )
            st.rerun()

        display_tasks = [
            task for task in st.session_state.tasks
            if search.lower() in task["task"].lower()
        ]

        if st.session_state.show_due_today_tasks:
            display_tasks = sorted(
                [
                    task for task in display_tasks
                    if (
                        task["status"] != "Completed"
                        and task["due_date"] <= today
                    )
                ],
                key=lambda task: task["due_date"]
            )
            st.subheader("Due & Today's Tasks")

            if not display_tasks:
                st.info("No due or today's tasks found.")
        else:
            display_tasks = sorted(
                display_tasks,
                key=lambda task: (
                    not task["important"],
                    task["due_date"]
                )
            )

            if not display_tasks:
                st.info("No tasks found.")
            elif not any(task["important"] for task in display_tasks):
                st.subheader("⭐ Important Tasks")
                st.info("No important tasks marked yet.")

        important_header_shown = False
        regular_header_shown = False

        for i, task in enumerate(
            display_tasks
        ):

            if (
                search.lower()
                not in task["task"].lower()
            ):
                continue

            if not st.session_state.show_due_today_tasks:
                if task["important"] and not important_header_shown:
                    st.subheader("⭐ Important Tasks")
                    important_header_shown = True

                if not task["important"] and not regular_header_shown:
                    st.subheader("Regular Tasks")
                    regular_header_shown = True

            priority_class = task[
                "priority"
            ].lower()

            display_status = get_display_status(task, today)

            due_days = (
                task["due_date"] - today
            ).days

            # REMINDER ALERT

            if (
                0 <= due_days <= task["reminder_days"]
                and
                task["status"] != "Completed"
            ):

                st.warning(
                    f"""
🔔 Reminder Alert

Task:
{task['task']}

Due in {due_days} day(s)
                    """
                )

            card_col = st.container()

            with card_col:

                status_class = (
                    display_status.lower()
                )

                card_class = f"task-card {priority_class}"

                if display_status == "Overdue":
                    card_class = f"{card_class} overdue-task-card"

                if task["important"]:
                    card_class = f"{card_class} important-task-card"

                star_class = (
                    "important-star"
                    if task["important"]
                    else "muted-star"
                )

                star_symbol = (
                    "&#9733;"
                    if task["important"]
                    else "&#9734;"
                )

                st.markdown(f"""
                <div class="{card_class}">

                <h3><span class="{star_class}">{star_symbol}</span>{task['task']}</h3>

                <p><b>Description:</b>
                {task['description']}</p>

                <p><b>User Type:</b>
                {task['user_type']}</p>

                <p><b>Category:</b>
                {task['category']}</p>

                <p><b>Priority:</b>
                {task['priority']}</p>

                <p><b>Due Date:</b>
                {task['due_date']}</p>

                <p><b>Status:</b>
                <span class="{status_class}">
                {display_status}
                </span></p>

                <p><b>Notes:</b>
                {task['notes']}</p>

                </div>
                """, unsafe_allow_html=True)

            action_col1, action_col2 = st.columns(2)
            action_col3, action_col4 = st.columns(2)

            # IMPORTANT

            with action_col1:
                important_label = (
                    "⭐ Important"
                    if task["important"]
                    else "☆ Important"
                )

                if st.button(
                    important_label,
                    key=f"important{i}_{task['id']}"
                ):

                    cursor.execute(
                        """
                        UPDATE tasks
                        SET important=?
                        WHERE id=? AND user_id=?
                        """,
                        (
                            int(not task["important"]),
                            task["id"],
                            st.session_state.current_user_id
                        )
                    )

                    conn.commit()

                    st.session_state.tasks = load_user_tasks(
                        st.session_state.current_user_id
                    )

                    st.rerun()

            # COMPLETE

            with action_col2:
                st.markdown(
                    '<div class="complete-action"></div>',
                    unsafe_allow_html=True
                )

                if st.button(
                    "Complete",
                    key=f"complete{i}_{task['id']}",
                    disabled=task["status"] == "Completed"
                ):

                    cursor.execute(
                        """
                        UPDATE tasks
                        SET status=?
                        WHERE id=? AND user_id=?
                        """,
                        (
                            "Completed",
                            task["id"],
                            st.session_state.current_user_id
                        )
                    )

                    conn.commit()

                    st.session_state.tasks = load_user_tasks(
                        st.session_state.current_user_id
                    )

                    st.rerun()

            # UPDATE

            with action_col3:
                st.markdown(
                    '<div class="edit-action"></div>',
                    unsafe_allow_html=True
                )

                if st.button(
                    "Edit",
                    key=f"update{i}_{task['id']}",
                    disabled=task["status"] == "Completed"
                ):

                    st.session_state.edit_task_id = task["id"]

                    st.rerun()

            # DELETE

            with action_col4:
                st.markdown(
                    '<div class="delete-action"></div>',
                    unsafe_allow_html=True
                )

                if st.button(
                    "Delete",
                    key=f"delete{i}_{task['id']}"
                ):

                    st.session_state.delete_task_id = task["id"]

                    st.rerun()

    # ---------------- DASHBOARD ---------------- #

    elif menu == "Dashboard":

        st.header("📊 Dashboard")

        total = len(st.session_state.tasks)

        completed = len([
            t for t in st.session_state.tasks
            if t["status"] == "Completed"
        ])

        pending = len([
            t for t in st.session_state.tasks
            if t["status"] == "Pending"
        ])

        updated = len([
            t for t in st.session_state.tasks
            if t["status"] == "Updated"
        ])

        progress = (
            completed / total
            if total > 0 else 0
        )

        completion_percentage = progress * 100

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("📋 Total", total)

        c2.metric("✅ Completed", completed)

        c3.metric("⏳ Pending", pending)

        c4.metric("✏️ Updated", updated)

        c5.metric("📈 Progress", f"{completion_percentage:.0f}%")

        st.progress(progress)

        from streamlit_calendar import calendar

        st.subheader("📅 Task Calendar")

        calendar_events = []

        for task in st.session_state.tasks:

            color = "#22c55e"

            if task["priority"] == "High":
                color = "#ef4444"

            elif task["priority"] == "Medium":
                color = "#f59e0b"

            calendar_events.append({
                "title": task["task"],
                "start": str(task["due_date"]),
                "end": str(task["due_date"]),
                "color": color,
            })

        calendar_options = {
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay",
            },
        }

        calendar(
            events=calendar_events,
            options=calendar_options,
        )

        if total > 0:

            df = pd.DataFrame(
                st.session_state.tasks
            )

            st.dataframe(df)

    # ---------------- ABOUT ---------------- #

    elif menu == "About":

        st.header("📖 About")

        st.write("""

## Personal Task Manager

Personal Task Manager helps you organize your day in a simple and clear way.
You can keep important work in one place, follow upcoming deadlines, and stay
updated on what still needs attention.

This app is useful for students planning study time, teachers keeping track
of class work, employees managing daily responsibilities, and anyone handling
personal tasks in everyday life.

### What You Can Do

- Add tasks for study, work, or personal life
- Set priorities so important tasks stand out
- Choose due dates and stay ready for upcoming deadlines
- Update task details whenever plans change
- Mark tasks as completed and track your progress
- Use the dashboard for a quick view of your task status

### Why It Helps

With everything in one place, it becomes easier to plan your day, finish work
on time, and avoid forgetting important tasks.

        """)

    # ---------------- LOGOUT ---------------- #

    elif menu == "Logout":

        st.session_state.show_logout_confirm = True

    if st.session_state.show_logout_confirm:
        confirm_logout()

    if st.session_state.delete_task_id is not None:
        confirm_delete_task()

    if st.session_state.show_delete_completed_confirm:
        confirm_delete_completed_tasks()
