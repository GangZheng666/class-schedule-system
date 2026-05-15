"""课表展示系统 - Streamlit App"""

import glob
import os
import sys
import streamlit as st
from datetime import datetime, timedelta

from parser import (
    parse_schedule,
    get_courses_for_week,
    get_semester_week,
    get_week_date_range,
    SLOT_TIMES,
    WEEKDAYS,
)

# 获取程序运行的基础目录
def get_base_dir():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

st.set_page_config(
    page_title="我的课表",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"  # 强制侧边栏展开
)

st.markdown("""<style>
    /* 强制显示侧边栏切换按钮 */
    [data-testid="collapsedControl"] {
        display: flex !important;
    }
    
    /* 确保侧边栏容器不被隐藏 */
    [data-testid="stSidebar"] {
        display: block !important;
    }

    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
    
    * { font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* 侧边栏样式 - 黑色背景 */
    section[data-testid="stSidebar"] {
        background: #0a0a0a !important;
        border-right: 1px solid #333 !important;
    }
    section[data-testid="stSidebar"] > div {
        background: #0a0a0a !important;
    }
    [data-testid="stSidebarContent"] {
        background: #0a0a0a !important;
        color: #f0f0f0 !important;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] span {
        color: #f0f0f0 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #333 !important;
    }
    
    /* ====== 隐藏 Streamlit 顶部工具栏，但保留侧边栏切换按钮 ====== */
    [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 让 header 变透明且紧凑，只保留侧边栏切换按钮 */
    [data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }
    
    /* 确保侧边栏切换按钮正常显示 */
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 999999 !important;
        display: flex !important;
        background: white !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
        padding: 8px !important;
    }
    
    /* 主体内容容器 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0 !important;
        max-width: 100% !important;
    }
    
    /* 确保内容完整显示，不溢出隐藏 */
    [data-testid="stVerticalBlock"] > div {
        overflow: visible !important;
    }
    
    table.sched { 
        width:100%; 
        border-collapse:separate; 
        border-spacing: 0;
        font-size:0.72rem; 
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    table.sched th { 
        padding:6px 3px; 
        text-align:center; 
        font-weight:600; 
    }
    table.sched td { 
        vertical-align:top; 
        padding:2px; 
        width:12%;
        background: #fafbfc;
    }
    table.sched .th-time { 
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
        color:#fff; 
        width:60px;
        font-size: 0.7rem;
    }
    table.sched .th-day { 
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        color:#495057;
        border-bottom: 2px solid #dee2e6;
    }
    table.sched .th-today { 
        background: linear-gradient(180deg, #e74c3c 0%, #c0392b 100%);
        color:#fff;
        border-bottom: 2px solid #e74c3c;
    }
    table.sched .th-day .d, table.sched .th-today .d { 
        font-size:0.65rem; 
        opacity:.85;
        font-weight: 400;
    }
    .td-slot { 
        background: linear-gradient(180deg, #f8f9fa 0%, #f1f3f5 100%);
        text-align:center; 
        font-size:0.7rem;
        padding:4px 1px;
        border-right: 1px solid #e9ecef;
    }
    .td-slot .st { 
        font-size:0.6rem; 
        color:#868e96;
        display: block;
        margin-top: 1px;
    }
    
    .card { 
        border-radius:4px; 
        padding:3px 5px; 
        margin:1px 0; 
        font-size:0.7rem;
        line-height:1.25; 
        border-left:2px solid #4a90d9; 
        background: linear-gradient(135deg, #e8f4fd 0%, #d4ecfc 100%);
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .card:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .card.multi { 
        border-left-color:#e67e22; 
        background: linear-gradient(135deg, #fef9e7 0%, #fdf3d7 100%);
    }
    .card .cn { font-weight:600; color: #2c3e50; font-size: 0.7rem; }
    .card .cd { font-size:0.6rem; color:#6c757d; margin-top: 1px; }
    .card .cd .teacher { margin-right: 3px; }
    .card .cd .room { color: #868e96; }
    
    .empty { 
        color:#ced4da; 
        text-align:center; 
        font-size:0.65rem; 
        padding:5px 0;
        font-style: italic;
    }
    
    /* 减少组件间距 */
    [data-testid="stVerticalBlock"] > div {
        gap: 0.4rem !important;
    }
    [data-testid="stButton"] > div {
        gap: 0.3rem !important;
    }
    
    .course-count {
        text-align: center;
        padding: 5px 10px;
        background: linear-gradient(135deg, #e8f4fd 0%, #d4ecfc 100%);
        border-radius: 6px;
        margin: 6px 0;
        font-weight: 500;
        color: #495057;
        font-size: 0.8rem;
    }
    
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        padding: 0.5rem 0.8rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
    }
    
    [data-testid="stExpanderToggle"] {
        font-size: 0.85rem;
    }
</style>""", unsafe_allow_html=True)

# ====== 状态初始化 ======
if "sched_week" not in st.session_state:
    st.session_state.sched_week = None
if "semester_start" not in st.session_state:
    st.session_state.semester_start = datetime(2026, 3, 9)
if "sel_file" not in st.session_state:
    st.session_state.sel_file = ""
if "show_course_list" not in st.session_state:
    st.session_state.show_course_list = True

# ====== 侧边栏 ======
with st.sidebar:
    st.markdown("### 📁 课表文件")
    
    # 查找目录列表：程序目录、_internal 目录
    search_dirs = [BASE_DIR]
    internal_dir = os.path.join(BASE_DIR, "_internal")
    if os.path.exists(internal_dir):
        search_dirs.append(internal_dir)
    
    # 在所有目录查找课表文件
    xls_files_set = set()
    for dir_path in search_dirs:
        for pattern in ["*.xls", "*.xlsx"]:
            xls_files_set.update(glob.glob(os.path.join(dir_path, pattern)))
    # 只保留文件名（不含路径）
    xls_files = sorted(set([os.path.basename(f) for f in xls_files_set]))
    
    uploaded = st.file_uploader("上传课表文件", type=["xls", "xlsx"], key="uploader", label_visibility="collapsed")
    if uploaded is not None:
        filename = uploaded.name
        save_path = os.path.join(BASE_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"✓ 已导入: {filename}")
        st.session_state.sel_file = filename
        st.rerun()
    
    if xls_files:
        if st.session_state.sel_file and st.session_state.sel_file in xls_files:
            sel = st.selectbox("选择文件", xls_files, index=xls_files.index(st.session_state.sel_file), key="file_select")
        else:
            sel = st.selectbox("选择文件", xls_files, key="file_select", index=0)
        st.session_state.sel_file = sel
    else:
        st.warning("⚠️ 请上传 .xls 或 .xlsx 课表文件")
        st.stop()
    
    # 查找文件的完整路径
    full_path = None
    for dir_path in search_dirs:
        test_path = os.path.join(dir_path, st.session_state.sel_file)
        if os.path.exists(test_path):
            full_path = test_path
            break
    
    if full_path is None:
        st.error(f"找不到文件: {st.session_state.sel_file}")
        st.stop()
    
    data = parse_schedule(full_path)
    today = datetime.now()
    cur_week = get_semester_week(st.session_state.semester_start, today)
    cur_week = max(data["min_week"], min(cur_week, data["max_week"]))
    
    if st.session_state.sched_week is None or st.session_state.sched_week < data["min_week"] or st.session_state.sched_week > data["max_week"]:
        st.session_state.sched_week = cur_week
    
    week = st.session_state.sched_week
    w_data = get_courses_for_week(data, week)
    
    # 课程统计
    st.markdown("---")
    st.markdown("### 📊 课程统计")
    week_course_count = sum(len(slot) for day in w_data.values() for slot in day)
    if week_course_count > 0:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 10px 12px; border-radius: 8px; color: white; text-align: center;">
            <strong>本周共有 {week_course_count} 节课</strong>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("本周无课程安排 🎉")
    
    st.markdown("---")
    st.markdown("### ⚙️ 学期设置")
    sd = st.date_input("第一周周一", value=st.session_state.semester_start, key="sem_start_picker")
    st.session_state.semester_start = datetime.combine(sd, datetime.min.time())
    
    st.markdown("---")
    st.markdown("### 🔍 快速跳转")
    
    jd = st.date_input("按日期跳转", value=today, key="jump_date")
    if st.button("跳转", use_container_width=True, width='stretch'):
        jw = get_semester_week(st.session_state.semester_start, datetime.combine(jd, datetime.min.time()))
        st.session_state.sched_week = max(data["min_week"], min(jw, data["max_week"]))
        st.rerun()
    
    st.markdown("---")
    st.markdown(f"**当前文件:** `{st.session_state.sel_file}`")
    st.markdown(f"**学期周次:** 第 {data['min_week']}–{data['max_week']} 周")
    
    st.markdown("---")
    st.markdown("### 📋 显示设置")
    show_list = st.checkbox("显示课程列表", value=st.session_state.show_course_list, key="show_list_toggle")
    st.session_state.show_course_list = show_list

# ====== 主界面 ======
week = st.session_state.sched_week
w_data = get_courses_for_week(data, week)
monday, sunday = get_week_date_range(st.session_state.semester_start, week)

# 顶部标题（独立一行）
st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 12px 20px; border-radius: 10px; color: white; margin-bottom: 8px;">
    <span style="font-size: 1.2rem; font-weight: 700;">📚 第 {week} 周课表</span>
    <span style="opacity: 0.9; font-size: 0.85rem; margin-left: 20px;">
        {monday.strftime('%Y年%m月%d日')} — {sunday.strftime('%m月%d日')}
    </span>
</div>
""", unsafe_allow_html=True)

# 导航按钮（独立一行）
col_prev, col_next, col_today = st.columns([1, 1, 1])
with col_prev:
    if st.button("◀ 上一周", width='stretch', disabled=(week <= data["min_week"])):
        st.session_state.sched_week = max(data["min_week"], week - 1)
        st.rerun()
with col_next:
    if st.button("下一周 ▶", width='stretch', disabled=(week >= data["max_week"])):
        st.session_state.sched_week = min(data["max_week"], week + 1)
        st.rerun()
with col_today:
    if st.button("📍 回到本周", width='stretch'):
        st.session_state.sched_week = cur_week
        st.rerun()

# ====== 构建HTML课表 ======
# 颜色分配：同一课程名使用相同颜色
COLS = [
    ("#e8f4fd", "#4a90d9"), ("#fef9e7", "#e67e22"), ("#e8f8f5", "#27ae60"),
    ("#f4ecf7", "#8e44ad"), ("#fdedec", "#e74c3c"), ("#ebf5fb", "#2980b9"),
    ("#fef5e7", "#d35400"), ("#eafaf1", "#1e8449"),
]
color_map = {}

def get_color(name):
    if name not in color_map:
        color_map[name] = COLS[len(color_map) % len(COLS)]
    return color_map[name]

def render_cell(courses):
    if not courses:
        return '<div class="empty">—</div>'
    parts = []
    multi = len(courses) > 1
    for c in courses:
        bg, bc = get_color(c["name"])
        if multi:
            bg, bc = "#fef9e7", "#e67e22"
        teacher = c["teacher"]
        room = c["room"]
        teacher_html = f'<span class="teacher">👤 {teacher}</span>' if teacher else ''
        room_html = f'<span class="room">📍 {room}</span>' if room else ''
        parts.append(
            f'<div class="card{" multi" if multi else ""}" '
            f'style="background:{bg};border-left-color:{bc};">'
            f'<div class="cn">{c["name"]}</div>'
            f'<div class="cd">{teacher_html} {room_html}</div>'
            f'</div>'
        )
    return "".join(parts)

# 表头
rows_html = ["<tr>"]
rows_html.append('<th class="th-time">时段</th>')
for i in range(7):
    d = monday + timedelta(days=i)
    is_today = d.date() == today.date()
    cls = "th-today" if is_today else "th-day"
    rows_html.append(
        f'<th class="{cls}">{WEEKDAYS[i]}'
        f'<div class="d">{d.strftime("%m/%d")}</div></th>'
    )
rows_html.append("</tr>")

# 每行一个时段
for si, (sn, stm) in SLOT_TIMES.items():
    rows_html.append("<tr>")
    rows_html.append(f'<td class="td-slot">{sn}<br><span class="st">{stm}</span></td>')
    for di in range(7):
        courses = w_data.get(di, [[]])[si] if si < len(w_data.get(di, [])) else []
        rows_html.append(f'<td>{render_cell(courses)}</td>')
    rows_html.append("</tr>")

table_html = f'<table class="sched">{"".join(rows_html)}</table>'
st.markdown(table_html, unsafe_allow_html=True)

# ====== 课程列表（可折叠）======
if st.session_state.show_course_list:
    with st.expander("📋 本周课程列表", expanded=True):
        all_courses = []
        for di in range(7):
            d = monday + timedelta(days=di)
            for si in range(len(SLOT_TIMES)):
                courses = w_data.get(di, [[]])[si] if si < len(w_data.get(di, [])) else []
                for c in courses:
                    all_courses.append({
                        "日期": f"{WEEKDAYS[di]} {d.strftime('%m/%d')}",
                        "节次": c["slot_name"],
                        "课程": c["name"],
                        "教师": c["teacher"],
                        "教室": c["room"],
                    })
        
        if all_courses:
            import pandas as pd
            df = pd.DataFrame(all_courses)
            st.dataframe(df, use_container_width=True, hide_index=True, 
                        column_config={
                            "日期": st.column_config.TextColumn("日期", width=120),
                            "节次": st.column_config.TextColumn("节次", width=100),
                            "课程": st.column_config.TextColumn("课程", width=200),
                            "教师": st.column_config.TextColumn("教师", width=100),
                            "教室": st.column_config.TextColumn("教室", width=100),
                        })
        else:
            st.info("本周无课程安排 🎉")
