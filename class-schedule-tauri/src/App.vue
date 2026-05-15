<template>
  <el-container class="app-container">
    <el-aside :width="sidebarCollapsed ? '50px' : '300px'" class="sidebar">
      <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon v-if="sidebarCollapsed"><Right /></el-icon>
        <el-icon v-else><Left /></el-icon>
      </div>
      
      <div class="sidebar-content" v-if="!sidebarCollapsed">
        <h2 class="sidebar-title">📚 课表管理</h2>
        
        <el-divider />
        
        <div class="file-section">
          <el-upload
            class="upload-demo"
            drag
            accept=".xls,.xlsx"
            :auto-upload="false"
            :on-change="handleFileChange"
            :show-file-list="false"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖放或点击上传课表
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xls 和 .xlsx 格式
              </div>
            </template>
          </el-upload>
          
          <el-input
            v-if="showNameInput"
            v-model="newScheduleName"
            placeholder="输入课表名称"
            size="small"
            style="margin-top: 10px"
            @keyup.enter="confirmAddSchedule"
          >
            <template #append>
              <el-button @click="confirmAddSchedule">确定</el-button>
            </template>
          </el-input>
        </div>
        
        <el-divider />
        
        <div class="schedule-list-section" v-if="savedSchedules.length > 0">
          <h3 class="section-title">已保存的课表</h3>
          <div class="schedule-list">
            <div 
              v-for="schedule in savedSchedules" 
              :key="schedule.id"
              class="schedule-item"
              :class="{ active: currentScheduleId === schedule.id }"
              @click="switchSchedule(schedule.id)"
            >
              <div class="schedule-info">
                <div class="schedule-name">{{ schedule.name }}</div>
                <div class="schedule-file">{{ schedule.fileName }}</div>
              </div>
              <el-button 
                type="danger" 
                size="small" 
                circle
                @click.stop="deleteSchedule(schedule.id)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
        
        <el-divider v-if="savedSchedules.length > 0" />
        
        <div class="semester-section">
          <h3 class="section-title">学期设置</h3>
          <el-date-picker
            v-model="semesterStart"
            type="date"
            placeholder="选择开学日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="full-width"
            @change="onSemesterChange"
          />
          
          <el-button 
            type="primary" 
            size="small" 
            class="full-width refresh-btn"
            @click="refreshSchedule"
          >
            <el-icon><Refresh /></el-icon>
            刷新课表
          </el-button>
        </div>
        
        <el-divider />
        
        <div class="week-section">
          <h3 class="section-title">周次导航</h3>
          <div class="week-nav">
            <el-button size="small" @click="prevWeek" :disabled="currentWeek <= 1">
              <el-icon><arrow-left /></el-icon>
              上一周
            </el-button>
            <div class="week-display">
              <span class="week-num">第 {{ currentWeek }} 周</span>
            </div>
            <el-button size="small" @click="nextWeek">
              下一周
              <el-icon><arrow-right /></el-icon>
            </el-button>
          </div>
          
          <el-button 
            type="primary" 
            size="small" 
            class="full-width" 
            style="margin-top: 10px"
            @click="goToCurrentWeek"
          >
            <el-icon><calendar /></el-icon>
            回到本周
          </el-button>
          
          <el-date-picker
            v-model="jumpDate"
            type="date"
            placeholder="跳转到指定日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="full-width"
            style="margin-top: 10px"
            @change="jumpToDate"
          />
        </div>
        
        <el-divider />
        
        <div class="stats-section">
          <div class="stat-card">
            <div class="stat-num">{{ weekCourses.length }}</div>
            <div class="stat-label">本周课程</div>
          </div>
        </div>
      </div>
    </el-aside>
    
    <el-main class="main-content">
      <div v-if="!currentSchedule" class="empty-state">
        <el-empty description="请上传课表文件或选择已有课表">
          <el-button type="primary" @click="triggerUpload">
            上传课表
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="schedule-container">
        <div class="schedule-header">
          <h1 class="title">
            {{ currentSchedule.name }}
            <span class="week-info">第 {{ currentWeek }} 周</span>
            <span class="date-range">{{ weekDateRange }}</span>
          </h1>
        </div>
        
        <table class="schedule-table">
          <thead>
            <tr>
              <th class="time-col">时间</th>
              <th 
                v-for="dayIdx in 7" 
                :key="dayIdx"
                :class="{ 'today-col': isToday(dayIdx - 1) }"
              >
                <div class="day-name">{{ WEEKDAYS[dayIdx - 1] }}</div>
                <div class="day-date">{{ getWeekDate(dayIdx - 1) }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="slot in 6" :key="slot">
              <td class="time-col">
                <div class="slot-time">{{ SLOT_TIMES[slot - 1] }}</div>
                <div class="slot-num">第{{ slot * 2 - 1 }},{{ slot * 2 }}节</div>
              </td>
              <td 
                v-for="dayIdx in 7" 
                :key="dayIdx"
                :class="{ 'today-col': isToday(dayIdx - 1) }"
              >
                <div class="slot-content">
                  <div 
                    v-for="(course, courseIdx) in getCoursesAt(dayIdx - 1, slot - 1)" 
                    :key="courseIdx"
                    class="course-card"
                  >
                    <div class="course-name" :title="course.name">{{ truncateText(course.name, 10) }}</div>
                    <div class="course-detail">
                      <span class="teacher" v-if="course.teacher" :title="course.teacher">👨‍🏫 {{ truncateText(course.teacher, 6) }}</span>
                      <span class="room" v-if="course.room" :title="course.room">📍 {{ truncateText(course.room, 6) }}</span>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        
        <el-collapse class="course-list-collapse">
          <el-collapse-item title="📋 本周课程详情">
            <div class="course-list">
              <div 
                v-for="(course, idx) in sortedWeekCourses" 
                :key="idx"
                class="course-item"
              >
                <div class="course-item-left">
                  <div class="course-item-name">{{ course.name }}</div>
                  <div class="course-item-info">
                    {{ WEEKDAYS[course.weekday] }} 
                    第{{ course.startSlot * 2 + 1 }},{{ course.startSlot * 2 + 2 }}节 · 
                    {{ course.teacher }} · {{ course.room }}
                  </div>
                </div>
                <div class="course-item-right">
                  <el-tag size="small" type="info">
                    第{{ Math.min(...course.weeks) }}-{{ Math.max(...course.weeks) }}周
                  </el-tag>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import type { Course, ScheduleData, SavedSchedule } from './types'
import { parseExcel, getCoursesForWeek, SLOT_TIMES, WEEKDAYS } from './parser'

const SCHEDULES_KEY = 'class_schedule_schedules'
const SETTINGS_KEY = 'class_schedule_settings'
const CURRENT_SCHEDULE_KEY = 'class_schedule_current'

const savedSchedules = ref<SavedSchedule[]>([])
const currentScheduleId = ref<string>('')
const semesterStart = ref<string>('2026-03-09')
const currentWeek = ref<number>(1)
const jumpDate = ref<string>('')
const showNameInput = ref(false)
const newScheduleName = ref('')
const pendingFile = ref<File | null>(null)
const sidebarCollapsed = ref(false)

function truncateText(text: string, maxLength: number): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

const currentSchedule = computed(() => {
  return savedSchedules.value.find(s => s.id === currentScheduleId.value) || null
})

const weekCourses = computed(() => {
  if (!currentSchedule.value) return []
  return getCoursesForWeek(currentSchedule.value.data.courses, currentWeek.value)
})

const sortedWeekCourses = computed(() => {
  return [...weekCourses.value].sort((a, b) => {
    if (a.weekday !== b.weekday) return a.weekday - b.weekday
    return a.startSlot - b.startSlot
  })
})

const weekDateRange = computed(() => {
  const start = dayjs(semesterStart.value).add((currentWeek.value - 1) * 7, 'day')
  const end = start.add(6, 'day')
  return `(${start.format('MM-DD')} ~ ${end.format('MM-DD')})`
})

onMounted(() => {
  loadFromStorage()
  updateCurrentWeek()
})

function loadFromStorage() {
  try {
    const savedData = localStorage.getItem(SCHEDULES_KEY)
    const savedSettings = localStorage.getItem(SETTINGS_KEY)
    const currentId = localStorage.getItem(CURRENT_SCHEDULE_KEY)
    
    if (savedData) {
      savedSchedules.value = JSON.parse(savedData)
    }
    
    if (savedSettings) {
      const settings = JSON.parse(savedSettings)
      if (settings.semesterStart) {
        semesterStart.value = settings.semesterStart
      }
    }
    
    if (currentId && savedSchedules.value.find(s => s.id === currentId)) {
      currentScheduleId.value = currentId
    } else if (savedSchedules.value.length > 0) {
      currentScheduleId.value = savedSchedules.value[0].id
    }
  } catch (e) {
    console.error('Failed to load from storage:', e)
  }
}

function saveToStorage() {
  try {
    localStorage.setItem(SCHEDULES_KEY, JSON.stringify(savedSchedules.value))
    localStorage.setItem(CURRENT_SCHEDULE_KEY, currentScheduleId.value)
  } catch (e) {
    console.error('Failed to save to storage:', e)
  }
}

function saveSettings() {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify({ semesterStart: semesterStart.value }))
  } catch (e) {
    console.error('Failed to save settings:', e)
  }
}

function triggerUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.xls,.xlsx'
  input.onchange = (e: any) => {
    if (e.target.files[0]) {
      handleFileChange({ raw: e.target.files[0] })
    }
  }
  input.click()
}

function handleFileChange(file: any) {
  pendingFile.value = file.raw
  showNameInput.value = true
  newScheduleName.value = file.name?.replace(/\.(xls|xlsx)$/i, '') || '新课表'
}

function confirmAddSchedule() {
  if (!pendingFile.value) return
  
  const name = newScheduleName.value.trim() || '新课表'
  
  parseExcel(pendingFile.value)
    .then(data => {
      // 调试日志
      console.log('解析到的课程数据:', data)
      
      const newSchedule: SavedSchedule = {
        id: data.id,
        name,
        fileName: data.fileName || pendingFile.value?.name || '未知文件',
        data
      }
      
      savedSchedules.value.push(newSchedule)
      currentScheduleId.value = newSchedule.id
      saveToStorage()
      
      showNameInput.value = false
      newScheduleName.value = ''
      pendingFile.value = null
      
      ElMessage.success(`${name} 加载成功！共解析到 ${data.courses.length} 门课程`)
    })
    .catch(err => {
      ElMessage.error('课表解析失败，请检查文件格式')
      console.error('解析错误:', err)
    })
}

function switchSchedule(id: string) {
  currentScheduleId.value = id
  saveToStorage()
  refreshSchedule()
}

async function deleteSchedule(id: string) {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个课表吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = savedSchedules.value.findIndex(s => s.id === id)
    if (index > -1) {
      savedSchedules.value.splice(index, 1)
      
      if (currentScheduleId.value === id) {
        currentScheduleId.value = savedSchedules.value[0]?.id || ''
      }
      
      saveToStorage()
      ElMessage.success('课表已删除')
    }
  } catch {
    // 用户取消
  }
}

function refreshSchedule() {
  if (!currentSchedule.value) return
  updateCurrentWeek()
  ElMessage.success('课表已刷新')
}

function onSemesterChange() {
  saveSettings()
  updateCurrentWeek()
}

function updateCurrentWeek() {
  const now = dayjs()
  const start = dayjs(semesterStart.value)
  const diffDays = now.diff(start, 'day')
  const week = Math.floor(diffDays / 7) + 1
  currentWeek.value = Math.max(1, week)
}

function getWeekDate(weekday: number): string {
  const start = dayjs(semesterStart.value).add((currentWeek.value - 1) * 7, 'day')
  return start.add(weekday, 'day').format('MM-DD')
}

function isToday(weekday: number): boolean {
  const today = dayjs()
  const start = dayjs(semesterStart.value).add((currentWeek.value - 1) * 7, 'day')
  const target = start.add(weekday, 'day')
  return today.isSame(target, 'day')
}

function getCoursesAt(weekday: number, slot: number): Course[] {
  return weekCourses.value.filter(c => 
    c.weekday === weekday && 
    c.startSlot === slot
  )
}

function prevWeek() {
  if (currentWeek.value > 1) currentWeek.value--
}

function nextWeek() {
  currentWeek.value++
}

function goToCurrentWeek() {
  updateCurrentWeek()
}

function jumpToDate(date: string) {
  if (!date) return
  const target = dayjs(date)
  const start = dayjs(semesterStart.value)
  const diffDays = target.diff(start, 'day')
  const week = Math.floor(diffDays / 7) + 1
  if (week > 0) {
    currentWeek.value = week
    ElMessage.success(`已跳转到第 ${week} 周`)
  }
}
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
  display: flex;
}

.sidebar {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: white;
  overflow-y: auto;
  position: relative;
  transition: width 0.3s ease;
}

.sidebar-toggle {
  position: absolute;
  top: 50%;
  right: -12px;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  color: white;
  transition: all 0.3s;
}

.sidebar-toggle:hover {
  background: linear-gradient(180deg, #2a2a4e 0%, #26315e 100%);
}

.sidebar-content {
  padding: 20px;
}

.sidebar-title {
  font-size: 20px;
  margin-bottom: 10px;
}

.section-title {
  font-size: 14px;
  margin-bottom: 10px;
  color: #a0a0a0;
}

.full-width {
  width: 100%;
}

.file-section,
.schedule-list-section,
.semester-section,
.week-section,
.stats-section {
  margin-bottom: 20px;
}

.schedule-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.schedule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.schedule-item:hover {
  background: rgba(255, 255, 255, 0.15);
}

.schedule-item.active {
  background: rgba(64, 158, 255, 0.3);
  border: 1px solid #409eff;
}

.schedule-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.schedule-file {
  font-size: 12px;
  opacity: 0.7;
}

.refresh-btn {
  margin-top: 10px;
}

.week-nav {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.week-display {
  text-align: center;
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.week-num {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 15px;
  border-radius: 12px;
  text-align: center;
}

.stat-num {
  font-size: 32px;
  font-weight: bold;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.main-content {
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
  flex: 1;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.schedule-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.schedule-header {
  margin-bottom: 20px;
}

.title {
  font-size: 24px;
  color: #303133;
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.week-info {
  font-size: 16px;
  color: #409eff;
  font-weight: normal;
}

.date-range {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}

.schedule-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 4px;
}

.schedule-table th,
.schedule-table td {
  padding: 8px;
  text-align: center;
  border-radius: 8px;
  width: calc((100% - 120px) / 7);
}

.schedule-table th {
  background: linear-gradient(180deg, #f5f7fa 0%, #e8ecf1 100%);
  font-weight: 600;
  color: #303133;
}

.schedule-table .time-col {
  background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
  color: white;
  width: 120px;
  min-width: 120px;
}

.slot-time {
  font-size: 12px;
  font-weight: 500;
}

.slot-num {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 2px;
}

.day-name {
  font-size: 14px;
}

.day-date {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.today-col {
  background: linear-gradient(180deg, #fef0f0 0%, #fde2e2 100%) !important;
}

.today-col .day-name {
  color: #f56c6c;
  font-weight: bold;
}

.schedule-table td {
  background: #fafbfc;
  vertical-align: top;
  height: 100px;
  min-height: 100px;
}

.slot-content {
  min-height: 90px;
  height: 100%;
}

.course-card {
  background: linear-gradient(135deg, #e8f4fd 0%, #d4ecfc 100%);
  border-left: 3px solid #409eff;
  padding: 6px 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  text-align: left;
  overflow: hidden;
}

.course-name {
  font-size: 12px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-detail {
  font-size: 10px;
  color: #6c757d;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-detail .teacher {
  margin-right: 6px;
}

.course-list-collapse {
  margin-top: 24px;
}

.course-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.course-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.course-item-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.course-item-info {
  font-size: 12px;
  color: #909399;
}
</style>