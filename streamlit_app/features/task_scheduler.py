"""
QuantInsight Pro - 智能指令调度器 (Task Scheduler)
====================================================

周期性投研任务调度 + 自动报告生成.
专业级"承接复杂周期性投研任务并自动执行".

预置任务模板:
- 晨报 (每日8:30)
- 盘后总结 (每日15:30)
- 周报 (每周五)
- 财报监控
- 宏观数据跟踪

License: MIT
"""

from __future__ import annotations
import json, logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
TASKS_DIR = Path(__file__).parent.parent.parent / "_tasks_data"

TASK_TEMPLATES = {
    "morning_brief": {
        "name": "每日晨报",
        "schedule": "daily_08:30",
        "description": "每日早间市场简报: 隔夜外盘, 今日关注, 板块轮动信号",
        "task_type": "morning_brief",
    },
    "evening_review": {
        "name": "盘后总结",
        "schedule": "daily_15:30",
        "description": "收盘后持仓盈亏总结, 风险提示, 明日关注",
        "task_type": "evening_review",
    },
    "weekly_report": {
        "name": "周度报告",
        "schedule": "weekly_friday",
        "description": "本周市场回顾, 板块轮动分析, 资金流向趋势, 下周展望",
        "task_type": "weekly_report",
    },
    "earnings_monitor": {
        "name": "财报监控",
        "schedule": "triggered",
        "description": "监控持仓标的财报发布, 业绩超预期/不及预期分析",
        "task_type": "earnings_monitor",
    },
    "macro_watch": {
        "name": "宏观数据跟踪",
        "schedule": "monthly",
        "description": "GDP/CPI/PMI/M2 等宏观数据发布跟踪及影响分析",
        "task_type": "macro_watch",
    },
}


@dataclass
class ScheduledTask:
    task_id: str = ""
    name: str = ""
    task_type: str = ""
    schedule: str = ""
    description: str = ""
    is_active: bool = True
    last_run: str = ""
    next_run: str = ""
    results: list = field(default_factory=list)
    created_at: str = ""


@dataclass
class TaskResult:
    task_id: str = ""
    run_at: str = ""
    summary: str = ""
    data: dict = field(default_factory=dict)
    status: str = "success"


class ResearchTaskScheduler:
    """投研任务调度器"""

    def __init__(self):
        TASKS_DIR.mkdir(parents=True, exist_ok=True)
        self._tasks: list[ScheduledTask] = []
        self._load_tasks()

    def _load_tasks(self):
        path = TASKS_DIR / "tasks.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._tasks = [ScheduledTask(**t) for t in data]
            except Exception:
                pass

    def _save_tasks(self):
        path = TASKS_DIR / "tasks.json"
        path.write_text(json.dumps([asdict(t) for t in self._tasks], ensure_ascii=False, indent=2), encoding="utf-8")

    def create_task_from_template(self, template_key: str) -> ScheduledTask:
        tpl = TASK_TEMPLATES.get(template_key)
        if not tpl:
            raise ValueError(f"未知模板: {template_key}, 可用: {list(TASK_TEMPLATES.keys())}")

        task = ScheduledTask(
            task_id=f"task_{len(self._tasks)+1}_{int(datetime.now().timestamp())}",
            name=tpl["name"],
            task_type=tpl["task_type"],
            schedule=tpl["schedule"],
            description=tpl["description"],
            created_at=datetime.now().isoformat(),
            next_run=self._calc_next_run(tpl["schedule"]),
        )
        self._tasks.append(task)
        self._save_tasks()
        return task

    def create_custom_task(self, name: str, description: str, schedule: str = "daily_08:30") -> ScheduledTask:
        task = ScheduledTask(
            task_id=f"task_{len(self._tasks)+1}_{int(datetime.now().timestamp())}",
            name=name, description=description, schedule=schedule,
            task_type="custom", created_at=datetime.now().isoformat(),
            next_run=self._calc_next_run(schedule),
        )
        self._tasks.append(task)
        self._save_tasks()
        return task

    def _calc_next_run(self, schedule: str) -> str:
        now = datetime.now()
        if schedule.startswith("daily_"):
            time_str = schedule.split("_")[1]
            h, m = map(int, time_str.split(":"))
            next_time = now.replace(hour=h, minute=m, second=0)
            if next_time <= now:
                next_time += timedelta(days=1)
            return next_time.isoformat()
        elif schedule == "weekly_friday":
            days_until_friday = (4 - now.weekday()) % 7 or 7
            return (now + timedelta(days=days_until_friday)).replace(hour=17, minute=0).isoformat()
        return (now + timedelta(days=1)).isoformat()

    def list_tasks(self) -> list[ScheduledTask]:
        return self._tasks

    def get_active_tasks(self) -> list[ScheduledTask]:
        return [t for t in self._tasks if t.is_active]

    def delete_task(self, task_id: str):
        self._tasks = [t for t in self._tasks if t.task_id != task_id]
        self._save_tasks()

    def execute_task(self, task: ScheduledTask, cache_manager=None, llm_config: dict = None, qi_db=None) -> TaskResult:
        """执行任务 (生成报告)

        V3.13: 新增 qi_db 参数, 传给 MainAgent 实现数据接地
        """
        from ai.agent_orchestrator import MainAgent
        from features.report_generator import AutoReportGenerator

        agent = MainAgent(cache_manager=cache_manager, llm_config=llm_config, qi_db=qi_db)
        generator = AutoReportGenerator()

        # 根据任务类型生成查询
        query = self._task_to_query(task)
        result = agent.process_query(query)

        # 生成报告
        report = generator.generate(task.name, result)

        task_result = TaskResult(
            task_id=task.task_id,
            run_at=datetime.now().isoformat(),
            summary=report,
            data={"title": result.title, "summary": result.summary},
            status="success",
        )

        task.last_run = datetime.now().isoformat()
        task.results.append(asdict(task_result))
        task.next_run = self._calc_next_run(task.schedule)
        self._save_tasks()

        return task_result

    def _task_to_query(self, task: ScheduledTask) -> str:
        if task.task_type == "morning_brief":
            return "今日市场早间简报: 隔夜外盘表现, A股今日关注点, 板块轮动信号"
        elif task.task_type == "evening_review":
            return "今日盘后总结: 大盘走势, 涨跌家数, 资金流向, 明日展望"
        elif task.task_type == "weekly_report":
            return "本周市场回顾: 指数表现, 板块轮动, 资金流向趋势, 下周展望"
        return task.description

    def get_summary(self) -> str:
        lines = ["### 📋 智能指令\n"]
        if not self._tasks:
            lines.append("暂无定时任务. 可从模板创建:")
            for key, tpl in TASK_TEMPLATES.items():
                lines.append(f"  - **{tpl['name']}**: {tpl['description']}")
            return "\n".join(lines)

        for t in self._tasks:
            status = "✅ 活跃" if t.is_active else "⏸️ 暂停"
            last = f"上次: {t.last_run[:16]}" if t.last_run else "未执行"
            lines.append(f"- {status} **{t.name}** ({t.schedule}) | {last}")
        return "\n".join(lines)


class AutoReportGenerator:
    """自动报告生成器"""

    def generate(self, report_name: str, agent_result) -> str:
        """从Agent结果生成结构化报告"""
        now = datetime.now()
        lines = [
            f"# 📊 {report_name}",
            f"**生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n",
        ]

        if hasattr(agent_result, 'title'):
            lines.append(f"## {agent_result.title}\n")
        if hasattr(agent_result, 'summary'):
            lines.append(f"### 分析摘要\n{agent_result.summary}\n")
        if hasattr(agent_result, 'recommendation') and agent_result.recommendation:
            lines.append(f"### 💡 建议\n{agent_result.recommendation}\n")
        if hasattr(agent_result, 'reasoning') and agent_result.reasoning:
            lines.append(f"### 🧠 推理过程\n{agent_result.reasoning}\n")

        lines.append("\n---\n*本报告由 QuantInsight Pro AI 自动生成, 仅供参考, 不构成投资建议.*")
        return "\n".join(lines)
