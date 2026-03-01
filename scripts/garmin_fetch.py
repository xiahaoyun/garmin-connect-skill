#!/usr/bin/env python3
"""
Garmin Connect 数据获取脚本
支持中国区账号

用法: python3 garmin_fetch.py <邮箱> <密码> [--limit N] [--output FILE]
"""
import sys
import json
import argparse
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 自动加载当前目录及父目录可见的 .env
load_dotenv()

def setup_path():
    """设置 Python 路径以找到 garth 库"""
    import os
    user_site = os.path.expanduser('~/.local/lib/python3.12/site-packages')
    if user_site not in sys.path:
        sys.path.insert(0, user_site)

def resolve_env_file() -> str | None:
    """解析可选的自定义 .env 文件路径（GARMIN_ENV_FILE）"""
    env_file = os.environ.get("GARMIN_ENV_FILE")
    if env_file:
        p = Path(env_file).expanduser()
        if p.exists():
            return str(p)
    return None


def parse_args():
    # 若设置 GARMIN_ENV_FILE，则额外加载指定 env 文件
    custom_env = resolve_env_file()
    if custom_env:
        load_dotenv(custom_env, override=True)

    parser = argparse.ArgumentParser(description='获取 Garmin Connect 训练数据')
    parser.add_argument('email', nargs='?', default=os.environ.get('GARMIN_EMAIL'), 
                        help='Garmin 账号邮箱 (默认从 .env 读取)')
    parser.add_argument('password', nargs='?', default=os.environ.get('GARMIN_PASSWORD'),
                        help='Garmin 账号密码 (默认从 .env 读取)')
    parser.add_argument('--limit', type=int, default=20, help='获取记录数量 (默认: 20)')
    parser.add_argument('--output', '-o', default='/tmp/garmin_activities.json', help='输出文件路径')
    parser.add_argument('--days', type=int, default=365, help='查询天数范围 (默认: 365)')
    parser.add_argument('--domain', choices=['garmin.cn', 'garmin.com'], default=os.environ.get('GARMIN_DOMAIN', 'garmin.cn'),
                        help='Garmin 域名: garmin.cn(中国区) 或 garmin.com(国际区)')
    return parser.parse_args()

def format_pace(pace_min_km):
    """格式化配速显示"""
    if pace_min_km <= 0 or pace_min_km == float('inf'):
        return "N/A"
    mins = int(pace_min_km)
    secs = int((pace_min_km - mins) * 60)
    return f"{mins}:{secs:02d}"

def format_duration(seconds):
    """格式化时长显示"""
    if seconds <= 0:
        return "0:00"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}:{mins:02d}"
    return f"{mins}:{int(seconds % 60):02d}"

def fetch_activities(email, password, limit=20, days=365, domain='garmin.cn'):
    """获取训练记录"""
    setup_path()
    import garth
    
    # 配置域名（中国区/国际区）
    garth.configure(domain=domain)
    
    # 登录
    garth.login(email, password)
    
    # 获取用户信息
    profile = garth.client.user_profile
    user_info = {
        'user_id': profile.get('displayName', 'Unknown'),
        'total_activities': profile.get('totalActivities', 0)
    }
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 调用 API 获取活动列表
    url = "activitylist-service/activities/search/activities"
    params = {
        "start": "0",
        "limit": str(limit),
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d")
    }
    
    activities = garth.client.connectapi(url, params=params)
    return user_info, activities

def format_activity(activity):
    """格式化单条活动记录"""
    name = activity.get('activityName', 'Unknown')
    sport_type = activity.get('activityType', {}).get('typeKey', 'unknown')
    start_time = activity.get('startTimeLocal', 'Unknown')
    distance = activity.get('distance', 0)
    duration = activity.get('duration', 0)
    calories = activity.get('calories', 0)
    avg_hr = activity.get('averageHR', 0)
    max_hr = activity.get('maxHR', 0)
    avg_cadence = activity.get('averageRunningCadenceInStepsPerMinute', 0)
    elevation_gain = activity.get('elevationGain', 0)
    
    # 转换单位
    distance_km = distance / 1000 if distance else 0
    pace = (duration / 60) / distance_km if distance_km > 0 else 0
    
    return {
        'name': name,
        'type': sport_type,
        'date': start_time,
        'distance_km': round(distance_km, 2),
        'duration': format_duration(duration),
        'duration_seconds': duration,
        'calories': calories,
        'pace': format_pace(pace),
        'avg_hr': avg_hr,
        'max_hr': max_hr,
        'cadence': int(avg_cadence) if avg_cadence else 0,
        'elevation_gain': elevation_gain
    }

def print_summary(activities):
    """打印训练摘要"""
    print(f"\n找到 {len(activities)} 条记录:\n")
    
    for i, activity in enumerate(activities, 1):
        a = format_activity(activity)
        print(f"--- 记录 {i} ---")
        print(f"🏃 活动: {a['name']}")
        print(f"📅 时间: {a['date']}")
        print(f"🎯 类型: {a['type']}")
        if a['distance_km'] > 0:
            print(f"📏 距离: {a['distance_km']:.2f} km")
        print(f"⏱️ 时长: {a['duration']}")
        if a['calories'] > 0:
            print(f"🔥 卡路里: {a['calories']} kcal")
        if a['pace'] != "N/A":
            print(f"⚡ 平均配速: {a['pace']} min/km")
        if a['avg_hr'] > 0:
            print(f"❤️ 平均心率: {a['avg_hr']} bpm")
        if a['max_hr'] > 0:
            print(f"💓 最大心率: {a['max_hr']} bpm")
        if a['cadence'] > 0:
            print(f"👟 步频: {a['cadence']} spm")
        if a['elevation_gain'] > 0:
            print(f"⛰️ 爬升: {a['elevation_gain']} m")
        print()

def calculate_stats(activities):
    """计算统计数据"""
    if not activities:
        return {}
    
    total_distance = sum(a.get('distance', 0) for a in activities) / 1000
    total_duration = sum(a.get('duration', 0) for a in activities)
    total_calories = sum(a.get('calories', 0) for a in activities)
    
    # 按类型分组
    by_type = {}
    for a in activities:
        t = a.get('activityType', {}).get('typeKey', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
    
    return {
        'total_activities': len(activities),
        'total_distance_km': round(total_distance, 2),
        'total_duration_hours': round(total_duration / 3600, 2),
        'total_calories': int(total_calories),
        'by_type': by_type
    }

def main():
    args = parse_args()
    
    # 检查账号信息
    if not args.email or not args.password:
        print("❌ 错误: 需要提供 Garmin 账号信息")
        print("   方式1: 设置环境变量 GARMIN_EMAIL 和 GARMIN_PASSWORD")
        print("   方式2: 在项目 .env 文件中添加:")
        print("       GARMIN_EMAIL=your@email.com")
        print("       GARMIN_PASSWORD=yourpassword")
        print("       GARMIN_DOMAIN=garmin.cn  # 或 garmin.com")
        print("   方式3: 直接作为参数传入: python3 garmin_fetch.py <邮箱> <密码> --domain garmin.cn")
        sys.exit(1)
    
    print(f"🦴 正在连接 Garmin Connect ({args.domain})...\n")
    
    try:
        user_info, activities = fetch_activities(
            args.email,
            args.password,
            limit=args.limit,
            days=args.days,
            domain=args.domain
        )
        
        print(f"✅ 登录成功!")
        print(f"👤 用户ID: {user_info['user_id']}")
        print(f"📊 历史总活动数: {user_info['total_activities']}\n")
        
        if activities:
            print_summary(activities)
            
            # 计算并显示统计
            stats = calculate_stats(activities)
            print("--- 统计摘要 ---")
            print(f"📈 本次查询记录数: {stats['total_activities']}")
            print(f"🏃 总距离: {stats['total_distance_km']} km")
            print(f"⏱️ 总时长: {stats['total_duration_hours']} 小时")
            print(f"🔥 总消耗: {stats['total_calories']} kcal")
            if stats['by_type']:
                print(f"📊 活动类型分布:")
                for t, count in stats['by_type'].items():
                    print(f"   - {t}: {count}次")
            print()
            
            # 保存数据
            output_data = {
                'user_info': user_info,
                'stats': stats,
                'activities': [format_activity(a) for a in activities]
            }
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"💾 完整数据已保存到: {args.output}")
        else:
            print("⚠️ 没有找到训练记录")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
