#!/usr/bin/env python3
"""
Garmin Connect Skill 使用示例

展示如何获取各种健康与训练数据
"""

from datetime import date, timedelta
from garmin_skill import GarminSkill

def main():
    print("=" * 60)
    print("Garmin Connect Skill - 使用示例")
    print("=" * 60)
    
    # 初始化 Skill
    skill = GarminSkill()
    print("\n✅ 连接成功\n")
    
    # ========== 1. 跑步数据 ==========
    print("-" * 60)
    print("🏃 最近跑步记录")
    print("-" * 60)
    
    runs = skill.get_recent_runs(limit=5)
    for i, run in enumerate(runs, 1):
        print(f"{i}. {run.start_time}")
        print(f"   距离: {run.distance_km}km | 配速: {run.avg_pace}/km")
        print(f"   心率: {run.avg_hr}/{run.max_hr} bpm | 消耗: {run.calories}kcal")
        print()
    
    # ========== 2. 身体电量 ==========
    print("-" * 60)
    print("🔋 身体电量")
    print("-" * 60)
    
    bb = skill.get_body_battery()
    if bb:
        print(f"当前电量: {bb.current_level}/100")
        print(f"今日最高: {bb.max_level} | 最低: {bb.min_level}")
        if bb.current_level and bb.current_level < 25:
            print("⚠️ 电量偏低，建议休息")
    else:
        print("未获取到身体电量数据（需要支持该功能的手表）")
    print()
    
    # ========== 3. 训练准备程度 ==========
    print("-" * 60)
    print("🎯 训练准备程度")
    print("-" * 60)
    
    readiness = skill.get_training_readiness()
    if readiness and readiness.score:
        print(f"评分: {readiness.score}/100 ({readiness.qualifier})")
        print(f"静息心率: {readiness.resting_hr} bpm")
        print(f"睡眠评分: {readiness.sleep_score}")
        
        if readiness.score >= 80:
            print("✅ 状态极佳，适合高强度训练")
        elif readiness.score >= 60:
            print("⚠️ 状态良好，可进行中等强度训练")
        else:
            print("🔴 建议休息或轻度活动")
    else:
        print("未获取到训练准备程度数据")
    print()
    
    # ========== 4. 训练负荷 ==========
    print("-" * 60)
    print("🏋️ 训练负荷")
    print("-" * 60)
    
    load = skill.get_training_load()
    if load and load.acute_load:
        print(f"急性负荷(7天): {load.acute_load:.0f}")
        print(f"慢性负荷(28天): {load.chronic_load:.0f}")
        print(f"ACWR比值: {load.acwr_ratio}%")
        
        if load.acwr_ratio:
            if 80 <= load.acwr_ratio <= 130:
                print("✅ 负荷在最佳范围")
            elif load.acwr_ratio > 130:
                print("⚠️ 负荷过高，注意受伤风险")
            else:
                print("ℹ️ 负荷较低，可以适当增加")
    else:
        print("未获取到训练负荷数据")
    print()
    
    # ========== 5. 训练状态 ==========
    print("-" * 60)
    print("📊 训练状态")
    print("-" * 60)
    
    status = skill.get_training_status()
    if status:
        print(f"状态: {status.status}")
        if status.status_feedback:
            print(f"反馈: {status.status_feedback}")
        if status.fitness_trend:
            print(f"体能趋势: {status.fitness_trend}")
    else:
        print("未获取到训练状态")
    print()
    
    # ========== 6. 每日综合摘要 ==========
    print("-" * 60)
    print("📈 今日综合健康")
    print("-" * 60)
    
    summary = skill.get_daily_summary()
    if summary:
        print(f"静息心率: {summary.resting_hr} bpm")
        print(f"血氧: {summary.avg_spo2}% (最低 {summary.lowest_spo2}%)")
        print(f"呼吸: {summary.avg_respiration} bpm")
        print(f"步数: {summary.total_steps}")
        print(f"中强度运动: {summary.moderate_intensity_minutes} 分钟")
        print(f"高强度运动: {summary.vigorous_intensity_minutes} 分钟")
        print(f"久坐时间: {summary.sedentary_seconds // 60} 分钟")
    else:
        print("未获取到每日摘要")
    print()
    
    # ========== 7. 睡眠数据 ==========
    print("-" * 60)
    print("😴 昨晚睡眠")
    print("-" * 60)
    
    yesterday = date.today() - timedelta(days=1)
    sleep = skill.get_daily_sleep(yesterday)
    if sleep and 'daily_sleep_dto' in sleep:
        dto = sleep['daily_sleep_dto']
        sleep_seconds = getattr(dto, 'sleep_time_seconds', 0)
        if sleep_seconds:
            hours = sleep_seconds // 3600
            mins = (sleep_seconds % 3600) // 60
            deep = getattr(dto, 'deep_sleep_seconds', 0)
            deep_pct = deep / sleep_seconds * 100 if sleep_seconds > 0 else 0
            
            print(f"总时长: {hours}小时{mins}分钟")
            print(f"深睡: {deep//60}分钟 ({deep_pct:.0f}%)")
            
            if hours >= 7:
                print("✅ 睡眠充足")
            elif hours >= 6:
                print("⚠️ 睡眠偏少")
            else:
                print("🔴 睡眠不足")
    else:
        print("未获取到睡眠数据")
    print()
    
    # ========== 8. HRV 趋势 ==========
    print("-" * 60)
    print("💓 HRV 趋势（最近7天）")
    print("-" * 60)
    
    hrv_list = skill.get_hrv_status(days=7)
    for hrv in hrv_list[:3]:  # 显示最近3天
        status_emoji = {
            'BALANCED': '✅',
            'UNBALANCED': '⚠️',
            'LOW': '🔴',
            'POOR': '🔴'
        }.get(hrv.status or '', 'ℹ️')
        
        print(f"{hrv.date}: {status_emoji} {hrv.status} | HRV {hrv.avg_hrv or 'N/A'}")
    print()
    
    print("=" * 60)
    print("示例结束")
    print("=" * 60)

if __name__ == "__main__":
    main()
