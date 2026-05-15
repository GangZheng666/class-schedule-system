<template>
  <el-container class="app-container">
    <el-aside width="280px" class="sidebar">
      <div class="sidebar-content">
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
          
          <div v-if="scheduleData" class="file-info">
            <el-tag type="success" size="small">已加载课表</el-tag>
          </div>
        </div>
        
        <el-divider />
        
        <div class="semester-section">
          <h3 class="section-title">学期设置</h3>
          <el-date-picker
            v-model="semesterStart"
            type="date"
            placeholder="选择开学日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="full-width"
          />
        </div>
        
        <el-divider />
        
        <div class="week-section">
          <h3 class="section-title">周次导航</h3>
          <div class="week-nav">
            <el-button size="small" @click="prevWeek">
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
      <div v-if="!scheduleData" class="empty-state">
        <el-empty description="请先上传课表文件"></el-empty>
      </div>
      
      <div v-else class="schedule-container">
        <div class="schedule-header">
          <h1 class="title">
            第 {{ currentWeek }} 周课表
            <span class="date-range">{{ weekDateRange }}</span>
          </h1>
        </div>
        
        <table class="schedule-table">
          <thead>
            <tr>
              <th class="time-col">时间</th>
              <th 
                v-for="(day, idx) in WEEKDAYS" 
                :key="idx"
                :class="{ 'today-col': isToday(idx) }"
              >
                <div class="day-name">{{ day }}</div>
                <div class="day-date">{{ getWeekDate(idx) }}</div>
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
                v-for="(day, dayIdx) in 7" 
                :key="dayIdx"
                :class="{ 'today-col': isToday(dayIdx) }"
              >
                <div class="slot-content">
                  <div 
                    v-for="(course, courseIdx) in getCoursesAt(dayIdx, slot - 1)" 
                    :key="courseIdx"
                    class="course-card"
                  >
                    <div class="course-name">{{ course.name }}</div>
                    <div class="course-detail">
                      <span class="teacher" v-if="course.teacher">👨‍🏫 {{ course.teacher }}</span>
                      <span class="room" v-if="course.room">📍 {{ course.room }}</span>
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import type { Course, ScheduleData } from './types'
import { parseExcel, getCoursesForWeek, SLOT_TIMES, WEEKDAYS } from './parser'

const scheduleData = ref<ScheduleData | null>(null)
const semesterStart = ref<string>('2026-03-09')
const currentWeek = ref<number>(1)
const jumpDate = ref<string>('')

const weekCourses = computed(() => {
  if (!scheduleData.value) return []
  return getCoursesForWeek(scheduleData.value.courses, currentWeek.value)
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
  updateCurrentWeek()
})

function handleFileChange(file: any) {
  parseExcel(file.raw)
    .then(data => {
      scheduleData.value = data
      ElMessage.success('课表加载成功！')
    })
    .catch(err => {
      ElMessage.error('课表解析失败，请检查文件格式')
      console.error(err)
    })
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
.semester-section,
.week-section,
.stats-section {
  margin-bottom: 20px;
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

.file-info {
  margin-top: 10px;
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
}

.date-range {
  font-size: 14px;
  color: #909399;
  margin-left: 10px;
  font-weight: normal;
}

.schedule-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 4px;
}

.schedule-table th,
.schedule-table td {
  padding: 8px;
  text-align: center;
  border-radius: 8px;
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
  min-height: 80px;
}

.slot-content {
  min-height: 70px;
}

.course-card {
  background: linear-gradient(135deg, #e8f4fd 0%, #d4ecfc 100%);
  border-left: 3px solid #409eff;
  padding: 6px 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  text-align: left;
}

.course-name {
  font-size: 12px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
}

.course-detail {
  font-size: 10px;
  color: #6c757d;
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