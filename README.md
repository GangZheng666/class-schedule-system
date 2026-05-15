# 课表管理系统 (Class Schedule System)

一个功能完整的课表管理系统，支持 Excel 课表解析、多课表管理、学期设置等功能。

## 功能特性

- 📋 **Excel 课表解析** - 支持导入 .xls/.xlsx 格式的课表文件
- 📚 **多课表管理** - 同时管理多个课表，灵活切换
- 📅 **学期设置** - 自定义学期开始日期，自动计算周次
- 🔄 **周次导航** - 快速跳转到指定周，支持回到当前周
- 🎨 **侧边栏展开/收起** - 灵活的界面布局
- 📱 **响应式设计** - 现代化的用户界面

## 技术栈

### 前端
- Vue 3 + TypeScript
- Element Plus (UI 组件库)
- Vite (构建工具)
- Day.js (日期处理)
- XLSX (Excel 解析)

### 桌面应用
- Tauri (跨平台桌面应用框架)
- Rust (后端语言)

### 原始版本
- Python + Streamlit

## 项目结构

```
kebiao/
├── class-schedule-tauri/   # Tauri + Vue3 桌面应用
├── class-schedule-vue/     # 纯 Vue3 Web 应用
├── parser.py               # Python 版本解析器
├── app.py                  # Streamlit 应用
└── README.md               # 项目说明
```

## 快速开始

### 环境要求

- Node.js 18+
- npm 或 pnpm
- Rust (用于 Tauri 开发)

### 运行 Web 版本 (Vue)

```bash
cd class-schedule-vue
npm install
npm run dev
```

### 运行桌面应用 (Tauri)

```bash
cd class-schedule-tauri
npm install
npm run tauri dev
```

### 构建生产版本

```bash
# Web 版本
cd class-schedule-vue
npm run build

# 桌面应用
cd class-schedule-tauri
npm run tauri build
```

## 使用说明

1. **上传课表** - 在侧边栏点击上传区域，选择 Excel 文件
2. **设置课表名称** - 为上传的课表设置一个友好的名称
3. **选择课表** - 在"已保存的课表"列表中点击切换不同课表
4. **设置学期** - 在"学期设置"中选择学期开始日期
5. **浏览课表** - 使用周次导航或日期跳转查看不同周的课程

## Excel 格式要求

课表 Excel 文件应遵循以下格式：
- 第一行：标题
- 第一列：节次（如：第1-2节、第3-4节等）
- 第一行（从第2列开始）：星期（周一到周日）
- 其他单元格：课程信息（格式：课程名\n教师[周次]教室）

## 许可证

MIT License
