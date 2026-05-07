import re

class RuleEngine:
    def __init__(self):
        # 패턴 튜플: (정규식 패턴, 하드코딩된 SQL, 로깅/세션에 넘길 관련 테이블 목록)
        self.rules = [
            # 1. 챗봇 인사말 및 도움말 처리 (가짜 SQL을 통해 응답 메시지를 전달)
            (
                re.compile(r".*(안녕|반가워|도움말|뭐할줄|뭐해).*", re.IGNORECASE),
                "SELECT '안녕하세요! 저는 데이터봇입니다. \"전체 길드별 총 데미지 알려줘\"처럼 질문해보세요!' AS bot_message;",
                []
            ),
            # 2. 핵심 KPI 하드코딩 (예: 전체 길드 레이드 데미지)
            (
                re.compile(r"^\s*(모든|전체)?\s*길드\s*레이드\s*데미지\s*(알려줘|보여줘|합계)?\s*$", re.IGNORECASE),
                "SELECT guild_id, SUM(total_damage) AS total_dmg FROM guild_raid_member GROUP BY guild_id ORDER BY total_dmg DESC LIMIT 100;",
                [{"name": "guild_raid_member"}]
            )
        ]

    def match(self, user_query: str) -> tuple[str, list] | None:
        """
        유저 질문이 사전에 정의된 정규식 패턴과 매칭되면 (SQL, 관련된_테이블_목록)을 즉시 반환합니다.
        매칭되지 않으면 None을 반환하여 LLM 파이프라인으로 넘깁니다.
        """
        for pattern, sql, tables in self.rules:
            if pattern.search(user_query):
                return sql, tables
        return None

# Singleton instance
rule_engine = RuleEngine()
