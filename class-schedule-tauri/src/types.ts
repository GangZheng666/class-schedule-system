export interface Course {
  name: string
  teacher: string
  room: string
  weeks: number[]
  weekday: number
  startSlot: number
  endSlot: number
}

export interface ScheduleData {
  id: string
  name: string
  courses: Course[]
  maxWeek: number
  minWeek: number
  fileName?: string
}

export interface SavedSchedule {
  id: string
  name: string
  fileName: string
  data: ScheduleData
}