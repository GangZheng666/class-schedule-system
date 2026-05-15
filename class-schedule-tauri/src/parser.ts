import * as XLSX from 'xlsx'
import type { Course, ScheduleData } from './types'

const SLOT_TIMES: Record<number, string> = {
  0: '08:00-09:40',
  1: '09:55-11:35',
  2: '14:00-15:40',
  3: '15:55-17:35',
  4: '18:00-19:40',
  5: '19:50-21:30'
}

const WEEKDAYS = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

function parseWeeks(weekStr: string, suffix: string = ''): number[] {
  weekStr = weekStr.trim()
  if (!weekStr.startsWith('[') || !weekStr.endsWith(']')) {
    return []
  }
  let inner = weekStr.slice(1, -1)
  inner = inner.replace('，', ',')
  
  const isOdd = inner.includes('单') || suffix.includes('单')
  const isEven = inner.includes('双') || suffix.includes('双')
  
  for (const ch of ['单', '双', '周']) {
    inner = inner.replace(ch, '')
  }
  
  const weeks: number[] = []
  
  if (inner.includes(',')) {
    for (const part of inner.split(',')) {
      const p = part.trim()
      if (p.includes('-')) {
        const [a, b] = p.split('-')
        for (let i = parseInt(a); i <= parseInt(b); i++) {
          weeks.push(i)
        }
      } else {
        try {
          weeks.push(parseInt(p))
        } catch {
          // ignore
        }
      }
    }
  } else if (inner.includes('-')) {
    const [a, b] = inner.split('-')
    for (let i = parseInt(a); i <= parseInt(b); i++) {
      weeks.push(i)
    }
  } else {
    try {
      weeks.push(parseInt(inner))
    } catch {
      return []
    }
  }
  
  let result = weeks
  if (isOdd) {
    result = result.filter(w => w % 2 === 1)
  }
  if (isEven) {
    result = result.filter(w => w % 2 === 0)
  }
  
  return result.sort((a, b) => a - b)
}

function splitMultiCourse(lines: string[]): string[] {
  console.log('splitMultiCourse 输入行:', lines)
  const coursesRaw: string[] = []
  let i = 0
  
  while (i < lines.length) {
    const line = lines[i].trim()
    if (!line) {
      i++
      continue
    }
    
    const hasBracket = /\[[^\]]+\]/.test(line)
    
    if (hasBracket) {
      console.log(`跳过行 ${i} (包含方括号):`, line)
      i++
      continue
    }
    
    const courseName = line
    console.log(`找到课程名:`, courseName)
    i++
    
    while (i < lines.length) {
      const nextLine = lines[i].trim()
      if (!nextLine) {
        i++
        continue
      }
      
      if (!/\[[^\]]+\]/.test(nextLine)) {
        console.log(`下一行不包含方括号，停止:`, nextLine)
        break
      }
      
      const block = courseName + '\n' + nextLine
      console.log('添加课程块:', block)
      coursesRaw.push(block)
      i++
    }
  }
  
  console.log('splitMultiCourse 输出:', coursesRaw)
  return coursesRaw
}

function parseSingleCourse(text: string): { name: string, teacher: string, weeks: number[], room: string } | null {
  console.log('parseSingleCourse 输入:', text)
  text = text.trim()
  if (!text) {
    return null
  }
  
  const lines = text.split('\n')
  console.log('分割后的行:', lines)
  
  const courseName = lines[0]?.trim() || '未知课程'
  let teacher = ''
  let weeks: number[] = []
  let room = ''
  
  const teacherLine = lines[1]?.trim() || ''
  console.log('教师行:', teacherLine)
  
  if (teacherLine && /\[[^\]]+\]/.test(teacherLine)) {
    console.log('教师行包含方括号')
    const teacherMatch = teacherLine.match(/^(.+?)(\[)/)
    if (teacherMatch) {
      teacher = teacherMatch[1].trim()
      console.log('提取教师:', teacher)
    }
    
    const allWeekNums = new Set<number>()
    const weekPattern = teacherLine.match(/(\[.+?\])/)
    if (weekPattern) {
      const weekStr = weekPattern[1]
      console.log('周次字符串:', weekStr)
      
      let suffix = ''
      if (teacherLine.includes('单周')) {
        suffix = '单'
      } else if (teacherLine.includes('双周')) {
        suffix = '双'
      }
      console.log('周次后缀:', suffix)
      
      const parsed = parseWeeks(weekStr, suffix)
      console.log('解析到的周次:', parsed)
      parsed.forEach(w => allWeekNums.add(w))
    }
    
    let remaining = teacherLine
    while (true) {
      const nextBracket = remaining.match(/，(.+?)(\[.+?\])/)
      if (nextBracket && nextBracket.index !== undefined) {
        const bracketContent = nextBracket[2]
        const moreWeeks = parseWeeks(bracketContent, '')
        moreWeeks.forEach(w => allWeekNums.add(w))
        remaining = remaining.slice(nextBracket.index + nextBracket[0].length)
      } else {
        break
      }
    }
    
    weeks = [...allWeekNums].sort((a, b) => a - b)
    console.log('最终周次:', weeks)
    
    const roomMatch = teacherLine.match(/[\]\)）].*?([^\[\]\(\)）]+)$/)
    if (roomMatch) {
      room = roomMatch[1].trim()
      console.log('教室匹配结果:', room)
      if (room.startsWith('周')) {
        room = room.slice(1).trim()
      }
      if (room.startsWith('单周')) {
        room = room.slice(2).trim()
      }
      if (room.startsWith('双周')) {
        room = room.slice(2).trim()
      }
    }
    console.log('最终教室:', room)
  }
  
  const result = {
    name: courseName,
    teacher,
    weeks,
    room
  }
  console.log('parseSingleCourse 输出:', result)
  return result
}

function parseCourseCell(cellText: string): Array<{ name: string, teacher: string, weeks: number[], room: string }> {
  if (!cellText || cellText.trim() === '') {
    return []
  }
  
  const lines = cellText.trim().split('\n')
  const courses: Array<{ name: string, teacher: string, weeks: number[], room: string }> = []
  
  const courseBlocks = splitMultiCourse(lines)
  
  for (const block of courseBlocks) {
    const course = parseSingleCourse(block)
    if (course && course.name && course.weeks.length > 0) {
      courses.push(course)
    }
  }
  
  return courses
}

export function parseExcel(file: File): Promise<ScheduleData> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer)
        const workbook = XLSX.read(data, { type: 'array' })
        const sheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[sheetName]
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, raw: false }) as any[][]
        
        console.log('读取到的完整数据:', jsonData)
        
        const courses: Course[] = []
        
        for (let rowIdx = 2; rowIdx < jsonData.length; rowIdx++) {
          const row = jsonData[rowIdx]
          const slotIdx = rowIdx - 2
          
          if (slotIdx >= Object.keys(SLOT_TIMES).length) {
            break
          }
          
          console.log(`处理第 ${rowIdx} 行 (节次 ${slotIdx}):`, row)
          
          for (let colIdx = 2; colIdx < row.length; colIdx++) {
            const dayIdx = colIdx - 2
            if (dayIdx >= 7) {
              break
            }
            
            const cellText = String(row[colIdx] || '').trim()
            if (cellText) {
              console.log(`解析单元格 (${rowIdx}, ${colIdx}):`, cellText)
              const parsedCourses = parseCourseCell(cellText)
              console.log('解析结果:', parsedCourses)
              for (const parsedCourse of parsedCourses) {
                if (parsedCourse.weeks.length > 0) {
                  courses.push({
                    name: parsedCourse.name,
                    teacher: parsedCourse.teacher,
                    room: parsedCourse.room,
                    weeks: parsedCourse.weeks,
                    weekday: dayIdx,
                    startSlot: slotIdx,
                    endSlot: slotIdx
                  })
                }
              }
            }
          }
        }
        
        const weekSet = new Set<number>()
        courses.forEach(c => c.weeks.forEach(w => weekSet.add(w)))
        const maxWeek = weekSet.size > 0 ? Math.max(...weekSet) : 16
        const minWeek = weekSet.size > 0 ? Math.min(...weekSet) : 1
        
        resolve({
          id: Date.now().toString(),
          name: file.name.replace(/\.(xls|xlsx)$/i, ''),
          courses,
          maxWeek,
          minWeek,
          fileName: file.name
        })
      } catch (err) {
        reject(err)
      }
    }
    reader.onerror = reject
    reader.readAsArrayBuffer(file)
  })
}

export function getCoursesForWeek(courses: Course[], week: number): Course[] {
  return courses.filter(c => c.weeks.includes(week))
}

export { SLOT_TIMES, WEEKDAYS }