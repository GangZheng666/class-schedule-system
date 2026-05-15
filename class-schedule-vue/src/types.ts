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
  courses: Course[]
  maxWeek: number
  minWeek: number
}