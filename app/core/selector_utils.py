def expand_with_relations(selected_tables, schema_full, max_depth: int = 1, max_tables: int = 10):
    table_map = {t["name"]: t for t in schema_full["tables"]}
    relations = schema_full.get("relations", [])

    # 삽입 순서를 유지하기 위해 dict 사용 (점수 높은 테이블이 앞에 위치)
    ordered = {t["name"]: None for t in selected_tables}
    frontier = set(ordered)

    for _ in range(max_depth):
        if len(ordered) >= max_tables:
            break
        next_frontier = set()
        for rel in relations:
            if len(ordered) + len(next_frontier) >= max_tables:
                break
            if rel["from_table"] in frontier and rel["to_table"] not in ordered and rel["to_table"] not in next_frontier:
                next_frontier.add(rel["to_table"])
            if rel["to_table"] in frontier and rel["from_table"] not in ordered and rel["from_table"] not in next_frontier:
                next_frontier.add(rel["from_table"])
        if not next_frontier:
            break
        for name in sorted(next_frontier):  # 확장 테이블은 이름 정렬로 결정론적 순서 보장
            ordered[name] = None
        frontier = next_frontier

    return [table_map[name] for name in ordered if name in table_map]