def build_schema_text(schema: dict) -> str:
    lines = []

    # ===== Tables =====
    for table in schema["tables"]:
        if table.get("hidden") or table.get("ignore"):
            continue
            
        lines.append(f"Table: {table['name']}")
        description = table.get("description", "")
        if description:
            lines.append(f"Description: {description}")

        semantic = table.get("semantic", {})
        grain = semantic.get("grain", [])
        level = semantic.get("level", "")

        if grain:
            lines.append(f"Grain: {', '.join(grain)}")
        if level:
            lines.append(f"Level: {level}")

        lines.append("Columns:")

        for col in table["columns"]:
            if col.get("hidden") or col.get("ignore"):
                continue
                
            col_line = f"- {col['name']} ({col['type']})"

            # role
            if "role" in col:
                col_line += f" [{col['role']}]"

            # aggregation
            if col.get("role") == "measure" and "aggregation" in col:
                col_line += f" (agg: {col['aggregation']})"

            # description
            if "desc" in col:
                col_line += f": {col['desc']}"

            lines.append(col_line)

        lines.append("")  # 줄바꿈

    # ===== Relations =====
    if "relations" in schema:
        lines.append("Relationships:")

        for rel in schema["relations"]:
            from_table = rel["from_table"]
            to_table = rel["to_table"]

            if "on" in rel:
                conditions = " AND ".join(
                    [f"{from_table}.{from_col} = {to_table}.{to_col}" for from_col, to_col in rel["on"]]
                )
            else:
                from_col = rel.get("from_column")
                to_col = rel.get("to_column")
                if from_col and to_col:
                    conditions = f"{from_table}.{from_col} = {to_table}.{to_col}"
                else:
                    conditions = ""

            rel_type = rel.get("type", "")

            lines.append(
                f"- {from_table} -> {to_table} "
                f"ON {conditions} ({rel_type})"
            )

        lines.append("")

    return "\n".join(lines)