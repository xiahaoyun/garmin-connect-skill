# Garmin Connect Skill for OpenClaw

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

为 OpenClaw AI 助手提供完整的 Garmin Connect 数据获取能力，包括跑步训练分析、健康监测、身体电量、训练负荷等。

> 项目说明：本项目主要由 **Haoyun** 进行需求定义与开发指挥，AI 负责实现与迭代。

## ✨ 功能特性

### 🏃 跑步训练数据
- 跑步/越野跑活动列表与详情
- **每公里配速分析**（splits）
- 心率、步频、爬升高度
- 周/月跑量统计

### 💓 健康监测
- 静息心率与全天心率曲线
- 睡眠质量分析（深睡/浅睡/REM）
- 压力水平监测
- 每日步数统计

### 🔋 身体电量与恢复 ⭐NEW
- 全天身体电量曲线
- 晨起训练准备程度
- HRV（心率变异性）状态
- 恢复时间建议

### 🏋️ 训练负荷与状态 ⭐NEW
- 急性/慢性训练负荷比 (ACWR)
- 训练状态评估（巅峰/维持/恢复/过度训练）
- 每日/每周训练负荷值
- 有氧训练效果

### 📊 每日综合摘要 ⭐NEW
- 血氧饱和度 (SpO2)
- 呼吸频率统计
- 上下楼层数
- 久坐时间统计
- 中高强度运动时间

## 🚀 快速开始

### 安装依赖

```bash
pip3 install garth python-dotenv requests --user --break-system-packages
```

### 配置账号

在 `.env` 文件中添加你的 Garmin 账号：

```bash
# .env (推荐放在项目根目录；也可通过 GARMIN_ENV_FILE 指定路径)
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
```

**支持中国区账号 (garmin.cn) 和国际区账号 (garmin.com)**

### 基本使用

```python
from garmin_skill import GarminSkill

# 初始化（中国区账号）
skill = GarminSkill(domain="garmin.cn")

# 获取最近跑步
runs = skill.get_recent_runs(limit=5)
for run in runs:
    print(f"{run.start_time}: {run.distance_km}km @ {run.avg_pace}/km")

# 获取身体电量
body_battery = skill.get_body_battery()
print(f"当前电量: {body_battery.current_level}")

# 获取训练状态
status = skill.get_training_status()
print(f"训练状态: {status.status}")
```

## ⚡ OpenClaw 最小接入（One-Click 模板）

可直接使用模板：

- `templates/OPENCLAW_SETUP_TEMPLATE.md`

模板已包含：依赖安装、`.env` 配置、CN/国际域名选择、连通性验证、可复制的引导文案。

## 📖 API 文档

### 跑步相关

#### `get_recent_runs(limit=10, days=None)`
获取最近跑步列表

**参数:**
- `limit`: 最多返回多少条记录
- `days`: 只返回最近 N 天的记录

**返回:** `List[RunSummary]`

#### `get_run_detail(activity_id)`
获取跑步详情，包括每公里配速

**返回:** `RunDetail`

```python
detail = skill.get_run_detail("12345678")
for split in detail.splits:
    print(f"第{split.km}公里: {split.pace_per_km}/km")
```

### 身体电量与恢复

#### `get_body_battery()`
获取全天身体电量数据

**返回:** `BodyBatteryData`

```python
bb = skill.get_body_battery()
print(f"最高: {bb.max_level}, 最低: {bb.min_level}, 当前: {bb.current_level}")
```

#### `get_training_readiness()`
获取晨起训练准备程度

**返回:** `TrainingReadinessData`

```python
readiness = skill.get_training_readiness()
# 评分 0-100，>80 优秀，60-80 良好，<60 建议休息
print(f"准备程度: {readiness.score}/100")
```

#### `get_hrv_status(days=7)`
获取 HRV 状态趋势

**返回:** `List[HRVData]`

### 训练负荷与状态

#### `get_training_status()`
获取当前训练状态评估

**返回:** `TrainingStatusData`

```python
status = skill.get_training_status()
# 可能值: PEAKING, PRODUCTIVE, MAINTAINING, DETRAINING, OVERREACHING
print(f"状态: {status.status}")
print(f"建议: {status.feedback}")
```

#### `get_training_load()`
获取训练负荷数据

**返回:** `TrainingLoadData`

```python
load = skill.get_training_load()
print(f"今日负荷: {load.acute_load}")
print(f"7天平均: {load.chronic_load}")
print(f"ACWR: {load.acwr_ratio}% (安全范围 80-130%)")
```

### 每日综合摘要

#### `get_daily_summary()`
获取今日综合健康数据

**返回:** `DailySummaryData`

```python
summary = skill.get_daily_summary()
print(f"静息心率: {summary.resting_hr}")
print(f"血氧: {summary.avg_spo2}%")
print(f"呼吸: {summary.avg_respiration} bpm")
print(f"中高强度: {summary.moderate_intensity_minutes} 分钟")
```

### 健康数据

#### `get_daily_sleep(day)`
获取指定日期睡眠数据

#### `get_daily_heart_rate(day)`
获取指定日期心率数据

#### `get_daily_stress(day)`
获取指定日期压力数据

#### `get_daily_steps(day)`
获取指定日期步数

## 🔒 隐私与安全

- 账号信息存储在本地 `.env` 文件，不上传到任何服务器
- 使用 Garmin 官方 API，数据直接从 Garmin Connect 获取
- 支持会话缓存，避免频繁登录

## 🛠️ 故障排除

### 登录失败
```python
# 检查账号配置
import os
print(os.getenv("GARMIN_EMAIL"))
print(os.getenv("GARMIN_PASSWORD"))
```

### 某些数据获取不到
- 确保手表已同步到 Garmin Connect
- 某些数据（如血氧、身体电量）需要特定型号手表支持
- 检查隐私设置是否允许访问健康数据

### 国际区账号
```python
# 使用国际区账号
skill = GarminSkill(domain="garmin.com")
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 🙏 致谢

- [garth](https://github.com/matin/garth) - 优秀的 Garmin Connect 非官方 Python 库
- OpenClaw 社区
