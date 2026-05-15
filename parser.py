"""课表XLS文件解析器"""

import re
import xlrd
from datetime import datetime, timedelta

# 节次对应时间
SLOT_TIMES = {
    0: ("第1,2节", "08:00-09:40"),
    1: ("第3,4节", "09:55-11:35"),
    2: ("第5,6节", "14:00-15:40"),
    3: ("第7,8节", "15:55-17:35"),
    4: ("9,10节", "18:00-19:40"),
    5: ("第11,12节", "19:50-21:30"),
}

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def parse_weeks(week_str: str, suffix: str = "") -> list[int]:
    """解析周次字符串，如 '[1-16]' -> [1,2,...,16], '[1-14双]' -> [2,4,...,14]

    suffix: '单'表示单周, '双'表示双周（括号外的情况）。
    """
    week_str = week_str.strip()
    if not week_str.startswith("[") or not week_str.endswith("]"):
        return []
    inner = week_str[1:-1]
    inner = inner.replace("，", ",")
    is_odd = "单" in inner or "单" in suffix
    is_even = "双" in inner or "双" in suffix
    for ch in ["单", "双", "周"]:
        inner = inner.replace(ch, "")
    weeks = []
    if "," in inner:
        for part in inner.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-")
                weeks.extend(range(int(a), int(b) + 1))
            else:
                try:
                    weeks.append(int(part))
                except ValueError:
                    pass
    elif "-" in inner:
        a, b = inner.split("-")
        weeks = list(range(int(a), int(b) + 1))
    else:
        try:
            weeks = [int(inner)]
        except ValueError:
            return []
    if is_odd:
        weeks = [w for w in weeks if w % 2 == 1]
    if is_even:
        weeks = [w for w in weeks if w % 2 == 0]
    return weeks


def _parse_teacher_line(week_str: str, rest: str) -> tuple:
    """解析教师行的周次和教室信息。

    处理各种格式的后缀:
    - "单周正心23" → odd weeks, room="正心23"
    - "周正心31" → room="正心31" (周为分隔符)
    - "教学楼722" → room="教学楼722"
    """
    suffix = ""
    # 先检测单周/双周（必须在剥离"周"之前）
    if rest.startswith("单周"):
        suffix = "单"
        rest = rest[2:]
    elif rest.startswith("双周"):
        suffix = "双"
        rest = rest[2:]
    # 剥离分隔符"周"
    if rest.startswith("周"):
        rest = rest[1:]
    weeks = parse_weeks(week_str, suffix)
    return weeks, rest.strip()


def _split_multi_course(lines: list) -> list:
    """将多门课程的文本分割成独立的课程块
    
    格式规则：
    - 课程名行：不含 [周次] 
    - 教师行：含 [周次]
    - 每门课 = 课程名行 + 教师行(+可选教室)
    """
    courses_raw = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        
        has_bracket = bool(re.search(r'\[[^\]]+\]', line))
        
        if has_bracket:
            i += 1
            continue
        
        course_name = line
        i += 1
        
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                i += 1
                continue
            
            if not re.search(r'\[[^\]]+\]', next_line):
                break
            
            block = course_name + '\n' + next_line
            courses_raw.append(block)
            i += 1
    
    return courses_raw


def _parse_single_course(text: str) -> dict:
    """解析单门课程文本，返回课程信息"""
    text = text.strip()
    if not text:
        return None
    
    lines = text.split('\n')
    
    course_name = lines[0].strip() if lines else "未知课程"
    teacher = ""
    weeks = []
    room = ""
    
    teacher_line = lines[1].strip() if len(lines) > 1 else ""
    
    if teacher_line and re.search(r'\[[^\]]+\]', teacher_line):
        teacher_match = re.search(r'^(.+?)(\[)', teacher_line)
        if teacher_match:
            teacher = teacher_match.group(1).strip()
        
        all_week_nums = set()
        week_pattern = re.search(r'(\[.+?\])', teacher_line)
        if week_pattern:
            week_str = week_pattern.group(1)
            
            suffix = ""
            if "单周" in teacher_line:
                suffix = "单"
            elif "双周" in teacher_line:
                suffix = "双"
            
            all_week_nums = set(parse_weeks(week_str, suffix))
        
        remaining = teacher_line
        while True:
            next_bracket = re.search(r'，(.+?)(\[.+?\])', remaining)
            if next_bracket:
                bracket_content = next_bracket.group(2)
                all_week_nums |= set(parse_weeks(bracket_content, ""))
                remaining = remaining[next_bracket.end():]
            else:
                break
        
        weeks = sorted(list(all_week_nums))
        
        room_match = re.search(r'[\]\)）].*?([^\[\]\(\)）]+)$', teacher_line)
        if room_match:
            room = room_match.group(1).strip()
            if room.startswith("周"):
                room = room[1:].strip()
            if room.startswith("单周"):
                room = room[2:].strip()
            if room.startswith("双周"):
                room = room[2:].strip()
    
    return {
        "name": course_name,
        "teacher": teacher,
        "weeks": weeks,
        "room": room,
    }


def parse_course_cell(cell_text: str) -> list[dict]:
    """解析一个单元格中的课程信息，返回课程列表"""
    if not cell_text or cell_text.strip() == "":
        return []
    
    lines = cell_text.strip().split("\n")
    courses = []
    
    # 首先尝试按课程分割
    course_blocks = _split_multi_course(lines)
    
    for block in course_blocks:
        course = _parse_single_course(block)
        if course and course["name"]:
            courses.append(course)
    
    return courses


def parse_schedule(filepath: str) -> dict:
    """解析课表XLS文件，返回结构化数据"""
    wb = xlrd.open_workbook(filepath)
    ws = wb.sheet_by_index(0)

    # 解析标题
    title = str(ws.cell_value(0, 0)).strip()

    # 解析课表数据
    schedule = {}
    for row_idx in range(2, ws.nrows):
        slot_text = str(ws.cell_value(row_idx, 1)).strip()
        slot_idx = row_idx - 2
        if slot_idx >= len(SLOT_TIMES):
            break
        slot_name, slot_time = SLOT_TIMES[slot_idx]
        for col_idx in range(2, ws.ncols):
            day_idx = col_idx - 2
            if day_idx >= 7:
                break
            cell_text = str(ws.cell_value(row_idx, col_idx)).strip()
            if cell_text:
                courses = parse_course_cell(cell_text)
                for course in courses:
                    if course["weeks"]:
                        for w in course["weeks"]:
                            key = (w, day_idx)
                            schedule.setdefault(key, []).append({
                                **course,
                                "slot_idx": slot_idx,
                                "slot_name": slot_name,
                                "slot_time": slot_time,
                                "day": WEEKDAYS[day_idx],
                            })

    return {
        "title": title,
        "schedule": schedule,
        "max_week": max((k[0] for k in schedule.keys()), default=16),
        "min_week": min((k[0] for k in schedule.keys()), default=1),
    }


def get_courses_for_week(schedule_data: dict, week: int) -> dict:
    """获取指定周的课表"""
    schedule = schedule_data["schedule"]
    week_schedule = {day: [[] for _ in range(len(SLOT_TIMES))] for day in range(7)}
    for (w, day), courses in schedule.items():
        if w == week:
            for course in courses:
                slot = course["slot_idx"]
                if slot < len(week_schedule[day]):
                    week_schedule[day][slot].append(course)
    return week_schedule


def get_semester_week(start_date: datetime, target_date: datetime = None) -> int:
    """根据学期开始日期计算当前是第几周"""
    if target_date is None:
        target_date = datetime.now()
    delta = target_date - start_date
    weeks = delta.days // 7 + 1
    return max(1, weeks)


def get_week_date_range(start_date: datetime, week: int) -> tuple:
    """获取指定周的日期范围"""
    monday = start_date + timedelta(weeks=week - 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday
