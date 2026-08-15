from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class DiffResult:
    reclaimed_bytes: int
    removed_count: int
    removed_bytes: int
    new_count: int
    new_bytes: int
    changed_increased_count: int
    changed_decreased_count: int
    categories: Dict[str, int]

class ReportDiffer:
    def diff(self, before: Dict[str, Any], after: Dict[str, Any]) -> DiffResult:
        schema_b = before.get("schema_version")
        schema_a = after.get("schema_version")
        
        if schema_b != schema_a:
            raise ValueError(f"Schema mismatch: before={schema_b}, after={schema_a}")
            
        if not schema_b:
            raise ValueError("Invalid report: missing schema_version")

        items_b = {item["id"]: item for item in before.get("items", [])}
        items_a = {item["id"]: item for item in after.get("items", [])}
        
        reclaimed_bytes = 0
        removed_count = 0
        removed_bytes = 0
        new_count = 0
        new_bytes = 0
        changed_increased = 0
        changed_decreased = 0
        categories: Dict[str, int] = {}
        
        # Check removed and changed
        for uid, item_b in items_b.items():
            if uid not in items_a:
                removed_count += 1
                removed_bytes += item_b["size_bytes"]
                reclaimed_bytes += item_b["size_bytes"]
                cat = item_b["category"]
                categories[cat] = categories.get(cat, 0) + item_b["size_bytes"]
            else:
                item_a = items_a[uid]
                diff_bytes = item_a["size_bytes"] - item_b["size_bytes"]
                if diff_bytes > 0:
                    changed_increased += 1
                elif diff_bytes < 0:
                    changed_decreased += 1
                    reclaimed_bytes += abs(diff_bytes)
                    cat = item_a["category"]
                    categories[cat] = categories.get(cat, 0) + abs(diff_bytes)

        # Check new
        for uid, item_a in items_a.items():
            if uid not in items_b:
                new_count += 1
                new_bytes += item_a["size_bytes"]
                
        return DiffResult(
            reclaimed_bytes=reclaimed_bytes,
            removed_count=removed_count,
            removed_bytes=removed_bytes,
            new_count=new_count,
            new_bytes=new_bytes,
            changed_increased_count=changed_increased,
            changed_decreased_count=changed_decreased,
            categories=categories
        )
