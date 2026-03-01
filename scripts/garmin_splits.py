#!/usr/bin/env python3
"""
获取 Garmin 单条活动的每公里分段数据
"""
import sys
import json
import os
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 自动加载当前目录及父目录可见的 .env
load_dotenv()

def setup_path():
    """设置 Python 路径"""
    user_site = os.path.expanduser('~/.local/lib/python3.12/site-packages')
    if user_site not in sys.path:
        sys.path.insert(0, user_site)

def parse_args():
    parser = argparse.ArgumentParser(description='获取 Garmin 活动分段数据')
    parser.add_argument('--activity-id', help='指定活动 ID')
    parser.add_argument('--date', help='按日期匹配活动 (YYYY-MM-DD)')
    parser.add_argument('--domain', choices=['garmin.cn', 'garmin.com'], default=os.environ.get('GARMIN_DOMAIN', 'garmin.cn'),
                        help='Garmin 域名: garmin.cn(中国区) 或 garmin.com(国际区)')
    return parser.parse_args()


def get_activity_splits(activity_id=None, date_str=None, domain='garmin.cn'):
    """获取活动分段数据"""
    setup_path()
    import garth
    
    # 配置域名（中国区/国际区）
    garth.configure(domain=domain)
    
    # 登录
    email = os.environ.get('GARMIN_EMAIL')
    password = os.environ.get('GARMIN_PASSWORD')
    garth.login(email, password)
    
    # 如果没有指定 activity_id，先获取最近的活动列表
    if not activity_id:
        url = "activitylist-service/activities/search/activities"
        params = {"start": "0", "limit": "5"}
        activities = garth.client.connectapi(url, params=params)
        
        if not activities:
            print("没有找到活动")
            return
        
        # 如果指定了日期，找匹配的活动
        if date_str:
            for a in activities:
                if date_str in a.get('startTimeLocal', ''):
                    activity_id = a.get('activityId')
                    print(f"找到活动: {a.get('activityName')} ({a.get('startTimeLocal')})")
                    break
        
        # 如果没指定日期或没找到，用最新的跑步活动
        if not activity_id:
            for a in activities:
                if a.get('activityType', {}).get('typeKey') == 'running':
                    activity_id = a.get('activityId')
                    print(f"使用最新跑步: {a.get('activityName')} ({a.get('startTimeLocal')})")
                    break
    
    if not activity_id:
        print("未找到指定活动")
        return
    
    # 获取活动详情（包含 splits）
    detail_url = f"activity-service/activity/{activity_id}"
    details = garth.client.connectapi(detail_url)
    
    # 尝试获取详细分段数据
    # 方式1: activitySplits
    splits = details.get('activitySplits', [])
    
    # 方式2: 通过 splits-service API 获取
    if not splits:
        try:
            splits_url = f"activity-service/activity/{activity_id}/splits"
            splits_data = garth.client.connectapi(splits_url)
            if splits_data:
                # 可能有不同的结构
                if isinstance(splits_data, list):
                    splits = splits_data
                elif isinstance(splits_data, dict):
                    splits = splits_data.get('splits', [])
        except Exception as e:
            print(f"获取 splits API 失败: {e}")
    
    # 方式3: 从 splitSummaries 推断分段数，但数据可能在 metrics 里
    if not splits:
        # 尝试从统计信息计算
        summary = details.get('summaryDTO', {})
        distance = summary.get('distance', 0)
        
        # 尝试获取原始数据点来计算每公里
        try:
            # 获取详细指标数据
            metrics_url = f"activity-service/activity/{activity_id}/details"
            metrics = garth.client.connectapi(metrics_url)
            if metrics:
                print("找到 metrics 数据，尝试提取每公里信息...")
                # 这里可能需要更复杂的处理
        except Exception as e:
            pass
    
    if not splits:
        print("没有找到分段数据 - 可能需要在 Garmin Connect 网页端导出")
        return details
    
    print(f"\n📊 共 {len(splits)} 个分段:\n")
    
    for split in splits:
        split_num = split.get('split', 0)
        distance = split.get('distance', 0) / 1000  # 转 km
        duration = split.get('duration', 0)
        avg_hr = split.get('averageHR', 0)
        max_hr = split.get('maxHR', 0)
        
        # 计算配速
        pace_min_km = (duration / 60) / distance if distance > 0 else 0
        mins = int(pace_min_km)
        secs = int((pace_min_km - mins) * 60)
        pace_str = f"{mins}:{secs:02d}"
        
        # 计算用时
        dur_mins = int(duration // 60)
        dur_secs = int(duration % 60)
        dur_str = f"{dur_mins}:{dur_secs:02d}"
        
        # 添加标记（冲刺段）
        marker = ""
        if avg_hr > 170:
            marker = "🔥"
        elif avg_hr > 160:
            marker = "⚡"
        
        print(f"第{split_num:2d}公里: {pace_str}/km | 用时 {dur_str} | 心率 {avg_hr}/{max_hr} bpm {marker}")
    
    return details

if __name__ == "__main__":
    args = parse_args()
    result = get_activity_splits(
        activity_id=args.activity_id,
        date_str=args.date,
        domain=args.domain,
    )
