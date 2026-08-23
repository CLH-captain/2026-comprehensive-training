from __future__ import annotations

from dataclasses import dataclass

VALID_TOOLS = frozenset(
    {
        "get_overview_statistics",
        "get_club_ranking",
        "get_activity_ranking",
        "get_participation_trend",
        "get_distribution_statistics",
        "get_student_summary",
        "get_club_summary",
    }
)


@dataclass(frozen=True)
class AgentAcceptanceQuestion:
    id: str
    question: str
    expected_tool: str
    category: str


AGENT_ACCEPTANCE_QUESTIONS = (
    AgentAcceptanceQuestion(
        "Q01", "当前正常运行的社团有多少个？", "get_overview_statistics", "总览"
    ),
    AgentAcceptanceQuestion(
        "Q02", "已完成活动数量是多少？", "get_overview_statistics", "总览"
    ),
    AgentAcceptanceQuestion(
        "Q03", "活动参与人次是多少？", "get_overview_statistics", "总览"
    ),
    AgentAcceptanceQuestion(
        "Q04", "当前活跃学生人数是多少？", "get_overview_statistics", "总览"
    ),
    AgentAcceptanceQuestion(
        "Q05", "总体到场率是多少？", "get_overview_statistics", "总览"
    ),
    AgentAcceptanceQuestion(
        "Q06", "本学期正常运行社团数是多少？", "get_overview_statistics", "条件总览"
    ),
    AgentAcceptanceQuestion(
        "Q07", "指定校区的参与人次是多少？", "get_overview_statistics", "条件总览"
    ),
    AgentAcceptanceQuestion(
        "Q08", "指定学期的活动数是多少？", "get_overview_statistics", "条件总览"
    ),
    AgentAcceptanceQuestion(
        "Q09", "哪个社团综合活跃度最高？", "get_club_ranking", "社团排行"
    ),
    AgentAcceptanceQuestion(
        "Q10", "列出最活跃的五个社团。", "get_club_ranking", "社团排行"
    ),
    AgentAcceptanceQuestion(
        "Q11", "指定校区社团活跃度排行。", "get_club_ranking", "社团排行"
    ),
    AgentAcceptanceQuestion(
        "Q12", "本学期社团活跃度前十名。", "get_club_ranking", "社团排行"
    ),
    AgentAcceptanceQuestion(
        "Q13", "参与人数最多的活动是什么？", "get_activity_ranking", "活动排行"
    ),
    AgentAcceptanceQuestion(
        "Q14", "列出热门活动前五名。", "get_activity_ranking", "活动排行"
    ),
    AgentAcceptanceQuestion(
        "Q15", "指定校区活动参与排行。", "get_activity_ranking", "活动排行"
    ),
    AgentAcceptanceQuestion(
        "Q16", "本学期签到人数最多的活动。", "get_activity_ranking", "活动排行"
    ),
    AgentAcceptanceQuestion(
        "Q17", "每月活动参与人次趋势如何？", "get_participation_trend", "趋势"
    ),
    AgentAcceptanceQuestion(
        "Q18", "本学期月度参与趋势。", "get_participation_trend", "趋势"
    ),
    AgentAcceptanceQuestion(
        "Q19", "指定校区的月度活动趋势。", "get_participation_trend", "趋势"
    ),
    AgentAcceptanceQuestion(
        "Q20", "哪个月参与最活跃？", "get_participation_trend", "趋势"
    ),
    AgentAcceptanceQuestion(
        "Q21", "活动类别参与分布如何？", "get_distribution_statistics", "分布"
    ),
    AgentAcceptanceQuestion(
        "Q22", "各学院的参与人次分布。", "get_distribution_statistics", "分布"
    ),
    AgentAcceptanceQuestion(
        "Q23", "各校区的参与人次分布。", "get_distribution_statistics", "分布"
    ),
    AgentAcceptanceQuestion(
        "Q24", "本学期活动类别分布。", "get_distribution_statistics", "分布"
    ),
    AgentAcceptanceQuestion(
        "Q25", "指定校区类别参与分布。", "get_distribution_statistics", "分布"
    ),
    AgentAcceptanceQuestion(
        "Q26", "我参加过多少场活动？", "get_student_summary", "个人摘要"
    ),
    AgentAcceptanceQuestion(
        "Q27", "我的报名和实际参与情况。", "get_student_summary", "个人摘要"
    ),
    AgentAcceptanceQuestion(
        "Q28", "我的到场率是多少？", "get_student_summary", "个人摘要"
    ),
    AgentAcceptanceQuestion(
        "Q29", "某学生的社团参与画像。", "get_student_summary", "个人摘要"
    ),
    AgentAcceptanceQuestion(
        "Q30", "某学生参与过哪些类别活动？", "get_student_summary", "个人摘要"
    ),
    AgentAcceptanceQuestion(
        "Q31", "某社团的活动和参与摘要。", "get_club_summary", "社团摘要"
    ),
    AgentAcceptanceQuestion(
        "Q32", "某社团的到场率是多少？", "get_club_summary", "社团摘要"
    ),
    AgentAcceptanceQuestion(
        "Q33", "指定社团本学期表现如何？", "get_club_summary", "社团摘要"
    ),
    AgentAcceptanceQuestion(
        "Q34", "指定社团有哪些活跃成员？", "get_club_summary", "社团摘要"
    ),
    AgentAcceptanceQuestion(
        "Q35", "比较本学期和全年的活动参与情况。", "get_overview_statistics", "综合"
    ),
    AgentAcceptanceQuestion(
        "Q36", "结合趋势说明校园社团活力。", "get_participation_trend", "综合"
    ),
    AgentAcceptanceQuestion(
        "Q37", "结合社团排行给出运营建议。", "get_club_ranking", "综合"
    ),
    AgentAcceptanceQuestion(
        "Q38", "结合类别分布分析学生偏好。", "get_distribution_statistics", "综合"
    ),
    AgentAcceptanceQuestion(
        "Q39", "结合热门活动总结参与特点。", "get_activity_ranking", "综合"
    ),
    AgentAcceptanceQuestion(
        "Q40", "给出当前校园社团活动总体结论。", "get_overview_statistics", "综合"
    ),
)
