#!/usr/bin/env python3
"""
Garmin Connect 数据获取 Skill for OpenClaw

为 AI 提供统一的 Garmin 数据获取接口，包括：
- 跑步活动列表和详情（含每公里配速）
- 心率、睡眠、压力等健康数据
- 身体电量与恢复状态
- 训练负荷与训练状态
- 每日综合健康摘要

GitHub: https://github.com/yourusername/garmin-connect-skill
License: MIT

使用方法:
    from garmin_skill import GarminSkill

    skill = GarminSkill()

    # 获取最近跑步列表
    runs = skill.get_recent_runs(limit=10)

    # 获取跑步详情（含每公里配速）
    detail = skill.get_run_detail("12345678")

    # 获取身体电量
    bb = skill.get_body_battery()

    # 获取训练状态
    status = skill.get_training_status()
"""
import os
import json
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import garth
from garth.exc import GarthException

load_dotenv()


# ============== 数据类定义 ==============

@dataclass
class SplitInfo:
    """每公里分段信息"""
    km: int
    distance_m: float
    duration_sec: float
    avg_speed_mps: float
    pace_per_km: str
    avg_hr: Optional[int] = None
    elevation_gain: Optional[float] = None


@dataclass
class RunDetail:
    """跑步活动详情"""
    activity_id: str
    activity_name: str
    start_time: str
    distance_km: float
    duration_sec: float
    duration_str: str
    avg_pace: str
    avg_hr: Optional[int]
    max_hr: Optional[int]
    calories: float
    cadence: Optional[int]
    elevation_gain: Optional[float]
    splits: List[SplitInfo]
    location: Optional[str] = None


@dataclass
class RunSummary:
    """跑步活动摘要"""
    activity_id: str
    activity_name: str
    start_time: str
    distance_km: float
    duration_sec: float
    duration_str: str
    avg_pace: str
    avg_hr: Optional[int]
    max_hr: Optional[int]
    calories: float
    location: Optional[str] = None


@dataclass
class WellnessData:
    """每日健康数据"""
    date: str
    heart_rate: Optional[Dict[str, Any]]
    sleep: Optional[Dict[str, Any]]
    stress: Optional[Dict[str, Any]]
    steps: Optional[int] = None


@dataclass
class RunningStats:
    """跑步统计"""
    period_days: int
    total_runs: int
    total_distance_km: float
    total_duration_sec: float
    total_duration_str: str
    total_calories: float
    avg_distance_km: float
    avg_duration_str: str
    runs: List[RunSummary]


# ============ 新增：身体电量数据类 ============

@dataclass
class BodyBatteryReading:
    """身体电量单条读数"""
    timestamp: str
    level: int


@dataclass
class BodyBatteryData:
    """身体电量数据"""
    date: str
    current_level: Optional[int]
    max_level: Optional[int]
    min_level: Optional[int]
    readings: List[BodyBatteryReading]
    avg_stress: Optional[float] = None


@dataclass
class TrainingReadinessData:
    """训练准备程度数据"""
    date: str
    score: Optional[int]  # 0-100
    qualifier: Optional[str]  # EXCELLENT, GOOD, FAIR, POOR
    sleep_score: Optional[int]
    recovery_time: Optional[int]  # 分钟
    resting_hr: Optional[int]
    hrv_status: Optional[str]


@dataclass
class HRVData:
    """心率变异性数据"""
    date: str
    avg_hrv: Optional[float]
    last_night_avg: Optional[float]
    status: Optional[str]  # BALANCED, UNBALANCED, LOW, POOR
    weekly_avg: Optional[float] = None


# ============ 新增：训练负荷数据类 ============

@dataclass
class TrainingLoadData:
    """训练负荷数据"""
    date: str
    acute_load: Optional[float]  # 急性负荷（7天）
    chronic_load: Optional[float]  # 慢性负荷（28天）
    acwr_ratio: Optional[float]  # 急性慢性比，安全范围 80-130%
    acwr_status: Optional[str]  # HIGH, OPTIMAL, LOW
    load_level: Optional[str]  # 负荷等级
    sport: Optional[str] = None


@dataclass
class TrainingStatusData:
    """训练状态数据"""
    date: str
    status: Optional[str]  # PEAKING, PRODUCTIVE, MAINTAINING, DETRAINING, OVERREACHING
    status_feedback: Optional[str]  # 状态反馈短语
    fitness_trend: Optional[str]  # 体能趋势
    sport: Optional[str] = None


@dataclass
class AerobicTrainingEffect:
    """有氧训练效果"""
    activity_id: str
    activity_name: str
    effect: Optional[float]  # 0.0-5.0
    improvement: Optional[str]  # NONE, MINOR, MAINTAINING, IMPROVING, etc.


# ============ 新增：每日综合摘要数据类 ============

@dataclass
class DailySummaryData:
    """每日综合健康摘要"""
    date: str
    resting_hr: Optional[int]
    max_hr: Optional[int]
    min_hr: Optional[int]
    avg_spo2: Optional[float]  # 血氧
    lowest_spo2: Optional[float]
    avg_respiration: Optional[float]  # 平均呼吸频率
    highest_respiration: Optional[float]
    lowest_respiration: Optional[float]
    floors_ascended: Optional[int]  # 上楼
    floors_descended: Optional[int]  # 下楼
    moderate_intensity_minutes: Optional[int]  # 中强度分钟
    vigorous_intensity_minutes: Optional[int]  # 高强度分钟
    total_steps: Optional[int]
    total_distance_meters: Optional[int]
    total_calories: Optional[int]
    active_calories: Optional[int]
    sedentary_seconds: Optional[int]  # 久坐时间
    sleeping_seconds: Optional[int]  # 睡眠时间
    body_battery_at_wake: Optional[int]  # 醒来时身体电量
    body_battery_highest: Optional[int]
    body_battery_lowest: Optional[int]


# ============== 主 Skill 类 ==============

class GarminSkill:
    """
    Garmin Connect 数据获取 Skill

    提供统一的接口获取 Garmin 跑步和健康数据。
    自动处理登录和会话管理。
    """

    def __init__(self, domain: str = "garmin.cn"):
        """
        初始化 Garmin Skill

        Args:
            domain: "garmin.cn" 中国区（默认）或 "garmin.com" 国际区
        """
        self.domain = domain
        self._ensure_session()

    def _ensure_session(self) -> bool:
        """确保 Garmin 会话有效"""
        tokens_dir = Path.home() / ".garth"
        garth.configure(domain=self.domain)

        # 尝试恢复会话
        try:
            if tokens_dir.exists():
                garth.resume(str(tokens_dir))
                _ = garth.client.username
                return True
        except GarthException:
            pass

        # 需要重新登录
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        if not email or not password:
            raise ValueError("请在 .env 文件中设置 GARMIN_EMAIL 和 GARMIN_PASSWORD")

        try:
            garth.login(email, password)
            garth.save(str(tokens_dir))
            return True
        except Exception as e:
            raise ConnectionError(f"登录失败: {e}")

    # ============== 工具方法 ==============

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds is None or seconds <= 0:
            return "0:00"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    @staticmethod
    def _format_pace(speed_mps: Optional[float]) -> str:
        """速度转配速"""
        if speed_mps is None or speed_mps <= 0:
            return "-:--"
        pace_per_km = 1000 / speed_mps
        minutes = int(pace_per_km // 60)
        seconds = int(pace_per_km % 60)
        return f"{minutes}:{seconds:02d}"

    @staticmethod
    def _format_datetime(time_str: str) -> str:
        """格式化日期时间"""
        if not time_str:
            return "未知时间"
        try:
            dt = datetime.fromisoformat(time_str.replace('.0', ''))
            return dt.strftime("%Y年%m月%d日 %H:%M")
        except:
            return time_str

    @staticmethod
    def _parse_date(day: Union[str, date]) -> str:
        """解析日期参数"""
        if isinstance(day, str):
            return day
        if isinstance(day, date):
            return day.isoformat()
        return str(day)

    # ============== 跑步相关接口 ==============

    def get_recent_runs(self, limit: int = 10, days: Optional[int] = None) -> List[RunSummary]:
        """
        获取最近跑步列表

        Args:
            limit: 最多返回多少条
            days: 只返回最近 N 天的（可选）

        Returns:
            RunSummary 列表
        """
        activities = garth.Activity.list(limit=limit * 2)  # 多获取一些用于过滤
        runs = []

        cutoff_date = None
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)

        for a in activities:
            act_type = getattr(a, 'activity_type', None)
            if not act_type or getattr(act_type, 'type_key', None) != 'running':
                continue

            # 检查日期
            start_time = getattr(a, 'start_time_local', None)
            if cutoff_date and start_time:
                try:
                    if isinstance(start_time, str):
                        dt = datetime.fromisoformat(start_time)
                    else:
                        dt = start_time
                    if dt < cutoff_date:
                        continue
                except:
                    pass

            distance = (getattr(a, 'distance', 0) or 0) / 1000
            duration = getattr(a, 'duration', 0) or 0
            avg_speed = getattr(a, 'average_speed', None)

            run = RunSummary(
                activity_id=str(getattr(a, 'activity_id', '')),
                activity_name=getattr(a, 'activity_name', '未知'),
                start_time=self._format_datetime(str(start_time)) if start_time else "",
                distance_km=round(distance, 2),
                duration_sec=round(duration, 2),
                duration_str=self._format_duration(duration),
                avg_pace=self._format_pace(avg_speed),
                avg_hr=int(getattr(a, 'average_hr', 0)) or None,
                max_hr=int(getattr(a, 'max_hr', 0)) or None,
                calories=round(getattr(a, 'calories', 0) or 0, 1),
                location=getattr(a, 'location_name', None)
            )
            runs.append(run)

            if len(runs) >= limit:
                break

        return runs

    def get_run_detail(self, activity_id: str) -> Optional[RunDetail]:
        """
        获取跑步详情（含每公里配速）

        Args:
            activity_id: 活动ID

        Returns:
            RunDetail 对象
        """
        try:
            # 获取活动基本信息
            path = f"activity-service/activity/{activity_id}"
            data = garth.client.connectapi(path)

            act_name = data.get("activityName", "未知")
            location = data.get("locationName")

            summary = data.get("summaryDTO", {})
            start_time = summary.get("startTimeLocal", "")
            distance = summary.get("distance", 0)
            duration = summary.get("duration", 0)
            avg_speed = summary.get("averageSpeed", 0)
            avg_hr = summary.get("averageHR")
            max_hr = summary.get("maxHR")
            calories = summary.get("calories", 0)
            cadence = summary.get("averageRunCadence")
            elevation = summary.get("elevationGain")

            # 获取分段数据
            splits = self._get_activity_splits(activity_id)

            if not splits and distance > 0:
                splits = self._generate_splits_from_summary(distance, duration, avg_speed)

            return RunDetail(
                activity_id=activity_id,
                activity_name=act_name,
                start_time=self._format_datetime(start_time),
                distance_km=round(distance / 1000, 2),
                duration_sec=round(duration, 2),
                duration_str=self._format_duration(duration),
                avg_pace=self._format_pace(avg_speed),
                avg_hr=int(avg_hr) if avg_hr else None,
                max_hr=int(max_hr) if max_hr else None,
                calories=round(calories, 1),
                cadence=int(cadence) if cadence else None,
                elevation_gain=round(elevation, 2) if elevation else None,
                splits=splits,
                location=location
            )

        except Exception as e:
            print(f"获取活动详情失败: {e}")
            return None

    def _get_activity_splits(self, activity_id: str) -> List[SplitInfo]:
        """获取活动分段数据"""
        try:
            path = f"activity-service/activity/{activity_id}/splits"
            data = garth.client.connectapi(path)

            splits = []
            laps = data.get("lapDTOs", [])

            for i, lap in enumerate(laps, 1):
                distance = lap.get("distance", 0)
                duration = lap.get("duration", 0)
                avg_speed = lap.get("averageSpeed", 0)
                avg_hr = lap.get("averageHR")
                elevation = lap.get("elevationGain")

                # 对于不足1公里的路段，需要根据实际距离计算等效配速
                if avg_speed > 0:
                    # 配速 = 1000米 / 速度(米/秒) = 每公里所需秒数
                    pace_per_km_sec = 1000 / avg_speed
                    minutes = int(pace_per_km_sec // 60)
                    seconds = int(pace_per_km_sec % 60)
                    pace = f"{minutes}:{seconds:02d}"
                else:
                    pace = "-:--"

                split = SplitInfo(
                    km=i,
                    distance_m=round(distance, 2),
                    duration_sec=round(duration, 2),
                    avg_speed_mps=round(avg_speed, 3),
                    pace_per_km=pace,
                    avg_hr=int(avg_hr) if avg_hr else None,
                    elevation_gain=round(elevation, 2) if elevation else None
                )
                splits.append(split)

            return splits

        except Exception as e:
            print(f"获取分段数据失败: {e}")
            return []

    def _generate_splits_from_summary(self, distance: float, duration: float, avg_speed: float) -> List[SplitInfo]:
        """根据总数据生成大致分段（估算）"""
        splits = []
        total_km = int(distance / 1000)
        avg_pace = self._format_pace(avg_speed)

        for i in range(1, total_km + 1):
            split = SplitInfo(
                km=i,
                distance_m=1000.0,
                duration_sec=round(duration / total_km, 2),
                avg_speed_mps=round(avg_speed, 3),
                pace_per_km=avg_pace
            )
            splits.append(split)

        remaining = distance - total_km * 1000
        if remaining > 100:
            split = SplitInfo(
                km=total_km + 1,
                distance_m=round(remaining, 2),
                duration_sec=round((duration / distance) * remaining, 2),
                avg_speed_mps=round(avg_speed, 3),
                pace_per_km=avg_pace
            )
            splits.append(split)

        return splits

    def get_running_stats(self, days: int = 30) -> RunningStats:
        """
        获取跑步统计数据

        Args:
            days: 统计最近多少天

        Returns:
            RunningStats 对象
        """
        runs = self.get_recent_runs(limit=100, days=days)

        if not runs:
            return RunningStats(
                period_days=days,
                total_runs=0,
                total_distance_km=0,
                total_duration_sec=0,
                total_duration_str="0:00",
                total_calories=0,
                avg_distance_km=0,
                avg_duration_str="0:00",
                runs=[]
            )

        total_distance = sum(r.distance_km for r in runs)
        total_duration = sum(r.duration_sec for r in runs)
        total_calories = sum(r.calories for r in runs)

        return RunningStats(
            period_days=days,
            total_runs=len(runs),
            total_distance_km=round(total_distance, 2),
            total_duration_sec=round(total_duration, 2),
            total_duration_str=self._format_duration(total_duration),
            total_calories=round(total_calories, 1),
            avg_distance_km=round(total_distance / len(runs), 2),
            avg_duration_str=self._format_duration(total_duration / len(runs)),
            runs=runs
        )

    # ============== 身体电量与恢复接口 ==============

    def get_body_battery(self, day: Union[str, date] = None) -> Optional[BodyBatteryData]:
        """
        获取身体电量数据

        Args:
            day: 日期，默认为今天

        Returns:
            BodyBatteryData 对象
        """
        if day is None:
            day = date.today()
        
        if isinstance(day, str):
            day = date.fromisoformat(day)

        try:
            # 使用 end 和 days 参数调用
            bb_list = garth.DailyBodyBatteryStress.list(end=day, days=1)
            if not bb_list:
                return None

            bb = bb_list[0]
            readings = []

            # 获取详细读数
            bb_readings = getattr(bb, 'body_battery_readings', [])
            for r in bb_readings:
                readings.append(BodyBatteryReading(
                    timestamp=str(getattr(r, 'timestamp', '')),
                    level=getattr(r, 'level', 0)
                ))

            return BodyBatteryData(
                date=day.isoformat(),
                current_level=getattr(bb, 'current_body_battery', None),
                max_level=getattr(bb, 'max_body_battery', None),
                min_level=getattr(bb, 'min_body_battery', None),
                avg_stress=getattr(bb, 'avg_stress', None),
                readings=readings
            )

        except Exception as e:
            print(f"获取身体电量失败: {e}")
            return None

    def get_training_readiness(self, day: Union[str, date] = None) -> Optional[TrainingReadinessData]:
        """
        获取训练准备程度数据

        Args:
            day: 日期，默认为今天

        Returns:
            TrainingReadinessData 对象
        """
        if day is None:
            day = date.today()
        
        if isinstance(day, str):
            day = date.fromisoformat(day)

        try:
            readiness_list = garth.TrainingReadinessData.list(end=day, days=1)
            if not readiness_list:
                return None

            rd = readiness_list[0]

            return TrainingReadinessData(
                date=day.isoformat(),
                score=getattr(rd, 'score', None),
                qualifier=getattr(rd, 'qualifier', None),
                sleep_score=getattr(rd, 'sleep_score', None),
                recovery_time=getattr(rd, 'recovery_time', None),
                resting_hr=getattr(rd, 'resting_heart_rate', None),
                hrv_status=getattr(rd, 'hrv_status', None)
            )

        except Exception as e:
            print(f"获取训练准备程度失败: {e}")
            return None

    def get_hrv_status(self, days: int = 7) -> List[HRVData]:
        """
        获取 HRV 状态趋势

        Args:
            days: 获取最近多少天

        Returns:
            HRVData 列表
        """
        try:
            # 生成日期列表
            date_list = []
            for i in range(days):
                d = date.today() - timedelta(days=i)
                date_list.append(d.isoformat())
            
            hrv_list = garth.HRVData.list(date_list)
            results = []

            for hrv in hrv_list:
                results.append(HRVData(
                    date=getattr(hrv, 'calendar_date', ''),
                    avg_hrv=getattr(hrv, 'avg_hrv', None),
                    last_night_avg=getattr(hrv, 'last_night_avg', None),
                    status=getattr(hrv, 'status', None),
                    weekly_avg=getattr(hrv, 'weekly_avg', None)
                ))

            return results

        except Exception as e:
            print(f"获取 HRV 状态失败: {e}")
            return []

    # ============== 训练负荷与状态接口 ==============

    def get_training_status(self, day: Union[str, date] = None) -> Optional[TrainingStatusData]:
        """
        获取训练状态评估

        Args:
            day: 日期，默认为今天

        Returns:
            TrainingStatusData 对象
        """
        if day is None:
            day = date.today()
        
        if isinstance(day, str):
            day = date.fromisoformat(day)

        try:
            # 使用 end 和 days 参数调用
            status_list = garth.DailyTrainingStatus.list(end=day, days=1)
            if not status_list:
                return None

            ts = status_list[0]

            return TrainingStatusData(
                date=day.isoformat(),
                status=getattr(ts, 'training_status', None),
                status_feedback=getattr(ts, 'training_status_feedback_phrase', None),
                fitness_trend=getattr(ts, 'fitness_trend', None),
                sport=getattr(ts, 'sport', None)
            )

        except Exception as e:
            print(f"获取训练状态失败: {e}")
            return None

    def get_training_load(self, day: Union[str, date] = None) -> Optional[TrainingLoadData]:
        """
        获取训练负荷数据

        Args:
            day: 日期，默认为今天

        Returns:
            TrainingLoadData 对象
        """
        if day is None:
            day = date.today()
        
        if isinstance(day, str):
            day = date.fromisoformat(day)

        try:
            # 使用 end 和 days 参数调用
            load_list = garth.DailyTrainingStatus.list(end=day, days=1)
            if not load_list:
                return None

            tl = load_list[0]

            # 计算 ACWR
            acute = getattr(tl, 'daily_training_load_acute', None)
            chronic = getattr(tl, 'daily_training_load_chronic', None)
            acwr = None
            if acute and chronic and chronic > 0:
                acwr = (acute / chronic) * 100

            return TrainingLoadData(
                date=day.isoformat(),
                acute_load=acute,
                chronic_load=chronic,
                acwr_ratio=round(acwr, 1) if acwr else None,
                acwr_status=getattr(tl, 'acwr_status', None),
                load_level=getattr(tl, 'load_level_trend', None),
                sport=getattr(tl, 'sport', None)
            )

        except Exception as e:
            print(f"获取训练负荷失败: {e}")
            return None

    def get_aerobic_training_effects(self, limit: int = 5) -> List[AerobicTrainingEffect]:
        """
        获取最近活动的有氧训练效果

        Args:
            limit: 获取最近多少条活动

        Returns:
            AerobicTrainingEffect 列表
        """
        try:
            activities = garth.FitnessActivity.list(limit)
            results = []

            for act in activities:
                effect = getattr(act, 'aerobic_training_effect', None)
                if effect:
                    results.append(AerobicTrainingEffect(
                        activity_id=str(getattr(act, 'activity_id', '')),
                        activity_name=getattr(act, 'activity_name', ''),
                        effect=getattr(effect, 'value', None),
                        improvement=getattr(effect, 'improvement', None)
                    ))

            return results

        except Exception as e:
            print(f"获取有氧训练效果失败: {e}")
            return []

    # ============== 每日综合摘要接口 ==============

    def get_daily_summary(self, day: Union[str, date] = None) -> Optional[DailySummaryData]:
        """
        获取每日综合健康摘要

        Args:
            day: 日期，默认为今天

        Returns:
            DailySummaryData 对象
        """
        if day is None:
            day = date.today()
        
        if isinstance(day, str):
            day = date.fromisoformat(day)

        try:
            # 使用 end 和 days 参数调用
            summary_list = garth.DailySummary.list(end=day, days=1)
            if not summary_list:
                return None

            s = summary_list[0]

            return DailySummaryData(
                date=day.isoformat(),
                resting_hr=getattr(s, 'resting_heart_rate', None),
                max_hr=getattr(s, 'max_heart_rate', None),
                min_hr=getattr(s, 'min_heart_rate', None),
                avg_spo2=getattr(s, 'average_spo_2', None),
                lowest_spo2=getattr(s, 'lowest_spo_2', None),
                avg_respiration=getattr(s, 'avg_waking_respiration_value', None),
                highest_respiration=getattr(s, 'highest_respiration_value', None),
                lowest_respiration=getattr(s, 'lowest_respiration_value', None),
                floors_ascended=getattr(s, 'floors_ascended', None),
                floors_descended=getattr(s, 'floors_descended', None),
                moderate_intensity_minutes=getattr(s, 'moderate_intensity_minutes', None),
                vigorous_intensity_minutes=getattr(s, 'vigorous_intensity_minutes', None),
                total_steps=getattr(s, 'total_steps', None),
                total_distance_meters=getattr(s, 'total_distance_meters', None),
                total_calories=getattr(s, 'total_kilocalories', None),
                active_calories=getattr(s, 'active_kilocalories', None),
                sedentary_seconds=getattr(s, 'sedentary_seconds', None),
                sleeping_seconds=getattr(s, 'sleeping_seconds', None),
                body_battery_at_wake=getattr(s, 'body_battery_at_wake_time', None),
                body_battery_highest=getattr(s, 'body_battery_highest_value', None),
                body_battery_lowest=getattr(s, 'body_battery_lowest_value', None)
            )

        except Exception as e:
            print(f"获取每日摘要失败: {e}")
            return None

    # ============== 原有健康数据接口 ==============

    def get_daily_heart_rate(self, day: Union[str, date]) -> Optional[Dict[str, Any]]:
        """
        获取每日心率数据

        Args:
            day: 日期字符串 (YYYY-MM-DD) 或 date 对象
        """
        date_str = self._parse_date(day)

        try:
            hr = garth.DailyHeartRate.get(date_str)
            return hr.model_dump() if hasattr(hr, "model_dump") else hr.__dict__
        except Exception as e:
            print(f"获取心率数据失败: {e}")
            return None

    def get_daily_sleep(self, day: Union[str, date]) -> Optional[Dict[str, Any]]:
        """
        获取每日睡眠数据

        Args:
            day: 日期字符串 (YYYY-MM-DD) 或 date 对象
        """
        date_str = self._parse_date(day)

        try:
            sd = garth.SleepData.get(date_str)
            return sd.model_dump() if hasattr(sd, "model_dump") else sd.__dict__
        except Exception as e:
            print(f"获取睡眠数据失败: {e}")
            return None

    def get_daily_stress(self, day: Union[str, date]) -> Optional[Dict[str, Any]]:
        """
        获取每日压力数据

        Args:
            day: 日期字符串 (YYYY-MM-DD) 或 date 对象
        """
        date_str = self._parse_date(day)

        try:
            path = f"wellness-service/wellness/dailyStress/{date_str}"
            return garth.client.connectapi(path)
        except Exception as e:
            print(f"获取压力数据失败: {e}")
            return None

    def get_daily_steps(self, day: Union[str, date]) -> Optional[Dict[str, Any]]:
        """
        获取每日步数数据

        Args:
            day: 日期字符串 (YYYY-MM-DD) 或 date 对象
        """
        date_str = self._parse_date(day)

        try:
            path = f"usersummary-service/stats/steps/daily/{date_str}"
            return garth.client.connectapi(path)
        except Exception as e:
            print(f"获取步数数据失败: {e}")
            return None

    def get_today_wellness(self) -> WellnessData:
        """获取今日所有健康数据"""
        today = date.today().isoformat()
        return WellnessData(
            date=today,
            heart_rate=self.get_daily_heart_rate(today),
            sleep=self.get_daily_sleep(today),
            stress=self.get_daily_stress(today),
            steps=self._extract_steps(self.get_daily_steps(today))
        )

    def _extract_steps(self, steps_data: Optional[Dict]) -> Optional[int]:
        """从步数数据中提取总步数"""
        if not steps_data:
            return None
        for key in ['totalSteps', 'steps', 'total_steps']:
            if key in steps_data:
                return steps_data[key]
        return None

    def get_wellness_range(self, days: int = 7) -> List[WellnessData]:
        """
        获取最近 N 天的健康数据

        Args:
            days: 天数

        Returns:
            WellnessData 列表
        """
        results = []
        today = date.today()

        for i in range(days):
            d = today - timedelta(days=i)
            data = WellnessData(
                date=d.isoformat(),
                heart_rate=self.get_daily_heart_rate(d),
                sleep=self.get_daily_sleep(d),
                stress=self.get_daily_stress(d),
                steps=self._extract_steps(self.get_daily_steps(d))
            )
            results.append(data)

        return results

    # ============== 用户信息和设备 ==============

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """获取用户资料"""
        try:
            return garth.client.connectapi("userprofile-service/userprofile")
        except Exception as e:
            print(f"获取用户资料失败: {e}")
            return None

    def get_devices(self) -> List[Dict[str, Any]]:
        """获取设备列表"""
        try:
            return garth.client.connectapi("device-service/devices")
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []

    # ============== 数据导出 ==============

    def save_to_json(self, data: Any, filepath: Union[str, Path]) -> str:
        """
        保存数据为 JSON 文件

        Args:
            data: 要保存的数据（会被转换为 dict）
            filepath: 文件路径

        Returns:
            保存的文件路径
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 处理 dataclass
        if hasattr(data, '__dataclass_fields__'):
            data = asdict(data)
        elif isinstance(data, list) and data and hasattr(data[0], '__dataclass_fields__'):
            data = [asdict(item) for item in data]

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(path)


# ============== 便捷函数 ==============

def get_skill(domain: str = "garmin.cn") -> GarminSkill:
    """获取 Skill 实例（便捷函数）"""
    return GarminSkill(domain=domain)


# ============== 主程序示例 ==============

if __name__ == "__main__":
    skill = GarminSkill()

    print("=" * 60)
    print("Garmin Skill 功能演示")
    print("=" * 60)

    # 1. 最近跑步
    print("\n1. 最近跑步列表:")
    runs = skill.get_recent_runs(limit=5)
    for r in runs:
        print(f"   {r.start_time} | {r.distance_km}km | {r.avg_pace}/km | {r.activity_name}")

    # 2. 身体电量
    print("\n2. 身体电量:")
    bb = skill.get_body_battery()
    if bb:
        print(f"   当前: {bb.current_level}, 最高: {bb.max_level}, 最低: {bb.min_level}")

    # 3. 训练准备程度
    print("\n3. 训练准备程度:")
    readiness = skill.get_training_readiness()
    if readiness:
        print(f"   评分: {readiness.score}/100 ({readiness.qualifier})")

    # 4. 训练状态
    print("\n4. 训练状态:")
    status = skill.get_training_status()
    if status:
        print(f"   状态: {status.status}")
        print(f"   反馈: {status.status_feedback}")

    # 5. 训练负荷
    print("\n5. 训练负荷:")
    load = skill.get_training_load()
    if load:
        print(f"   急性负荷: {load.acute_load}")
        print(f"   慢性负荷: {load.chronic_load}")
        print(f"   ACWR: {load.acwr_ratio}%")

    # 6. 每日摘要
    print("\n6. 每日综合摘要:")
    summary = skill.get_daily_summary()
    if summary:
        print(f"   静息心率: {summary.resting_hr}")
        print(f"   血氧: {summary.avg_spo2}%")
        print(f"   呼吸: {summary.avg_respiration} bpm")
        print(f"   中高强度: {summary.moderate_intensity_minutes} min")

    print("\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)
