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
  const coursesRaw: string[] = []
  let i = 0
  
  while (i < lines.length) {
    const line = lines[i].trim()
    if (!line) {
      i++
      continue
    }
    
    const hasBracket = /\[.*?\]/.test(line)
    
    if (hasBracket) {
      i++
      continue
    }
    
    const courseName = line
    i++
    
    while (i < lines.length) {
      const nextLine = lines[i].trim()
      if (!nextLine) {
        i++
        continue
      }
      
      if (!/\[.*?\]/.test(nextLine)) {
        break
      }
      
      const block = courseName + '\n' + nextLine
      coursesRaw.push(block)
      i++
    }
  }
  
  return coursesRaw
}

function parseSingleCourse(text: string): Course | null {
  text = text.trim()
  if (!text) return null
  
  const lines = text.split('\n')
  
  const courseName = lines[0]?.trim() || '未知课程'
  let teacher = ''
  let weeks: number[] = []
  let room = ''
  
  const teacherLine = lines[1]?.trim() || ''
  
  if (teacherLine && /\[.*?\]/.test(teacherLine)) {
    const teacherMatch = teacherLine.match(/^(.+?)(\[)/)
    if (teacherMatch) {
      teacher = teacherMatch[1].trim()
    }
    
    const allWeekNums = new Set<number>()
    const weekPattern = teacherLine.match(/(\[.+?\])/)
    if (weekPattern) {
      const weekStr = weekPattern[1]
      
      let suffix = ''
      if (teacherLine.includes('单周')) {
        suffix = '单'
      } else if (teacherLine.includes('双周')) {
        suffix = '双'
      }
      
      const parsedWeeks = parseWeeks(weekStr, suffix)
      parsedWeeks.forEach(w => allWeekNums.add(w))
    }
    
    let remaining = teacherLine
    while (true) {
      const nextBracket = remaining.match(/，(.+?)(\[.+?\])/)
      if (nextBracket) {
        const bracketContent = nextBracket[2]
        const moreWeeks = parseWeeks(bracketContent, '')
        moreWeeks.forEach(w => allWeekNums.add(w))
        remaining = remaining.slice(nextBracket.index + nextBracket[0].length)
      } else {
        break
      }
    }
    
    weeks = Array.from(allWeekNums).sort((a, b) => a - b)
    
    const roomMatch = teacherLine.match(/[\]\)）].*?([^\[\]\(\)）]+)$/)
    if (roomMatch) {
      room = roomMatch[1].trim()
      if (room.startsWith('周')) room = room.slice(1).trim()
      if (room.startsWith('单周')) room = room.slice(2).trim()
      if (room.startsWith('双周')) room = room.slice(2).trim()
    }
  }
  
  if (weeks.length === 0) {
    return null
  }
  
  return {
    name: courseName,
    teacher,
    room,
    weeks,
    weekday: 0,
    startSlot: 0,
    endSlot: 0
  }
}

function parseCourseCell(cellText: string): Course[] {
  if (!cellText || cellText.trim() === '') {
    return []
  }
  
  const lines = cellText.trim().split('\n')
  const courses: Course[] = []
  
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
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][]
        
        const courses: Course[] = []
        const weekSet = new Set<number>()
        
        for (let rowIdx = 2; rowIdx < jsonData.length; rowIdx++) {
          const row = jsonData[rowIdx]
          const slotIdx = rowIdx - 2
          
          if (slotIdx >= Object.keys(SLOT_TIMES).length) {
            break
          }
          
          for (let colIdx = 2; colIdx < row.length; colIdx++) {
            const dayIdx = colIdx - 2
            if (dayIdx >= 7) {
              break
            }
            
            const cellText = String(row[colIdx] || '').trim()
            if (cellText) {
              const cellCourses = parseCourseCell(cellText)
              for (const course of cellCourses) {
                course.weekday = dayIdx
                course.startSlot = slotIdx
                course.endSlot = slotIdx
                
                courses.push(course)
                
                course.weeks.forEach(w => weekSet.add(w))
              }
            }
          }
        }
        
        const maxWeek = weekSet.size > 0 ? Math.max(...weekSet) : 16
        const minWeek = weekSet.size > 0 ? Math.min(...weekSet) : 1
        
        resolve({ courses, maxWeek, minWeek })
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