---
name: garmin-connect
description: 从 Garmin Connect 获取完整的健康与训练数据，包括跑步分析、身体电量、训练负荷、睡眠监测等。支持中国区账号。
version: 1.0.0
author: haoyun
github: https://github.com/haoyun/garmin-connect-skill
license: MIT
---

# Garmin Connect Skill for OpenClaw

为 OpenClaw AI 助手提供完整的 Garmin Connect 数据获取能力。

## ✨ 功能特性

### 🏃 跑步训练分析
- 跑步/越野跑活动列表与详情
- **每公里配速分析**（splits）- 精确到每公里的配速、心率、爬升
- 周/月跑量统计与趋势分析
- 支持多种活动类型：跑步、越野跑、骑行、游泳等

### 🔋 身体电量与恢复 ⭐
- **全天身体电量曲线** - 了解能量储备变化
- **晨起训练准备程度** - 0-100分评估今天是否适合训练
- **HRV 心率变异性** - 长期疲劳与恢复状态监测
- **恢复时间建议** - 基于 Garmin 算法的恢复指导

### 🏋️ 训练负荷与状态 ⭐
- **急性/慢性训练负荷比 (ACWR)** - 科学的受伤风险评估
- **训练状态评估** - 巅峰/维持/恢复/过度训练判断
- **有氧训练效果** - 每次训练对体能的实际提升
- **负荷趋势分析** - 避免突然增加训练量导致受伤

### 📊 每日综合健康摘要 ⭐
- **血氧饱和度 (SpO2)** - 睡眠期间血氧监测
- **呼吸频率统计** - 全天呼吸数据分析
- **上下楼层数** - 日常活动量统计
- **中高强度运动时间** - WHO 推荐运动量追踪
- **久坐时间** - 健康风险提醒

### 💓 基础健康监测
- 静息心率与全天心率曲线
- 睡眠质量分析（深睡/浅睡/REM/清醒次数）
- 压力水平监测
- 每日步数与卡路里消耗

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

或单独安装：
```bash
pip3 install garth python-dotenv requests --user --break-system-packages
```

### 2. 配置 Garmin 账号

在 OpenClaw workspace 的 `.env` 文件中添加：

```bash
# ~/.openclaw/workspace/.env
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
```

**支持中国区账号 (garmin.cn) 和国际区账号 (garmin.com)**

### 3. 验证配置

```bash
python3 scripts/garmin_skill.py
```

如果显示你的最近跑步记录，说明配置成功。

## 📖 使用示例

### 分析最近跑步

```python
from garmin_skill import GarminSkill

skill = GarminSkill()

# 获取最近跑步
runs = skill.get_recent_runs(limit=5)
for run in runs:
    print(f"{run.start_time}: {run.distance_km}km @ {run.avg_pace}/km")

# 获取详细配速分析
detail = skill.get_run_detail(runs[0].activity_id)
for split in detail.splits:
    print(f"第{split.km}公里: {split.pace_per_km}/km, 心率{split.avg_hr}")
```

### 检查身体状态

```python
# 身体电量 - 当前能量储备
bb = skill.get_body_battery()
print(f"当前电量: {bb.current_level}/100")

# 训练准备程度 - 今天是否适合训练
readiness = skill.get_training_readiness()
print(f"准备程度: {readiness.score}/100")
if readiness.score and readiness.score < 60:
    print("建议今天休息")

# HRV 状态 - 长期疲劳指标
hrv = skill.get_hrv_status(days=7)
print(f"HRV状态: {hrv[0].status}")
```

### 评估训练负荷

```python
# 训练负荷与 ACWR 比值
load = skill.get_training_load()
print(f"ACWR: {load.acwr_ratio}%")

if load.acwr_ratio:
    if load.acwr_ratio > 130:
        print("⚠️ 负荷过高，受伤风险增加")
    elif load.acwr_ratio < 80:
        print("负荷较低，可以适当增加")
    else:
        print("✅ 负荷在最佳范围")

# 训练状态
tstatus = skill.get_training_status()
print(f"当前状态: {tstatus.status}")
```

### 每日健康快照

```python
# 今日综合数据
summary = skill.get_daily_summary()
print(f"静息心率: {summary.resting_hr}")
print(f"血氧: {summary.avg_spo2}%")
print(f"呼吸: {summary.avg_respiration} bpm")
print(f"中高强度: {summary.moderate_intensity_minutes} 分钟")

# 睡眠数据
sleep = skill.get_daily_sleep(date.today())
if sleep and 'daily_sleep_dto' in sleep:
    dto = sleep['daily_sleep_dto']
    hours = dto.sleep_time_seconds // 3600
    print(f"昨晚睡眠: {hours} 小时")
```

## 🔧 高级配置

### 使用国际区账号

```python
# 默认是中国区 (garmin.cn)
skill = GarminSkill(domain="garmin.com")
```

### 数据导出

```python
# 导出跑步数据为 JSON
runs = skill.get_recent_runs(limit=30)
skill.save_to_json(runs, "/path/to/runs.json")
```

## ⚠️ 注意事项

1. **首次使用需要登录** - 会自动保存 session，后续无需重复登录
2. **部分数据需要特定手表** - 身体电量、血氧、训练准备程度需要较新型号（如 Fenix、Forerunner 245/745/945 等）
3. **数据同步延迟** - 手表数据同步到 Connect 可能有延迟，极端情况下几分钟到几小时
4. **中国区与国际区** - 账号数据不互通，确保使用正确的 domain

## 🐛 故障排除

### 登录失败

```python
import os
print(os.getenv("GARMIN_EMAIL"))  # 检查是否读取到配置
```

### 某些数据为空

- 确认手表型号支持该功能
- 检查 Garmin Connect App 中是否有数据
- 确认隐私设置允许访问健康数据

### 国际区账号

```python
skill = GarminSkill(domain="garmin.com")
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

GitHub: https://github.com/haoyun/garmin-connect-skill

## 🙏 致谢

- [garth](https://github.com/matin/garth) - 优秀的 Garmin Connect 非官方 Python 库
- OpenClaw 社区
