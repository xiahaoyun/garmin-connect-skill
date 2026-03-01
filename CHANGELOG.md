# 更新日志

所有 notable changes to this project will be documented in this file.

## [1.0.0] - 2026-03-01

### ✨ 新增功能

#### 🏃 跑步训练分析
- `get_recent_runs()` - 获取最近跑步列表
- `get_run_detail()` - 获取跑步详情，包含每公里配速分析
- `get_running_stats()` - 周/月跑量统计
- 支持跑步、越野跑、骑行、游泳等多种活动类型

#### 🔋 身体电量与恢复
- `get_body_battery()` - 全天身体电量曲线与当前电量
- `get_training_readiness()` - 晨起训练准备程度评分
- `get_hrv_status()` - 心率变异性趋势分析

#### 🏋️ 训练负荷与状态
- `get_training_status()` - 训练状态评估（巅峰/维持/恢复/过度训练）
- `get_training_load()` - 急性/慢性训练负荷与 ACWR 比值
- `get_aerobic_training_effects()` - 有氧训练效果分析

#### 📊 每日综合摘要
- `get_daily_summary()` - 每日健康快照
  - 静息心率、血氧、呼吸频率
  - 上下楼层数、久坐时间
  - 中高强度运动时间

#### 💓 健康监测
- `get_daily_sleep()` - 睡眠数据分析
- `get_daily_heart_rate()` - 心率数据
- `get_daily_stress()` - 压力水平
- `get_daily_steps()` - 步数统计

### 📖 文档
- 完整的 API 文档
- 使用示例脚本
- README 快速开始指南
- OpenClaw SKILL.md 规范文档

### 🔧 技术
- 基于 garth 库构建
- 支持中国区 (garmin.cn) 和国际区 (garmin.com)
- 自动会话管理，避免重复登录
- 类型提示支持

## [0.1.0] - 2026-02-04

### 🎉 初始版本
- 基础跑步数据获取
- 简单健康数据查询
