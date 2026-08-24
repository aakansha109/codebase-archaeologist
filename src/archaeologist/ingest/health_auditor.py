from typing import List, Dict, Any
from archaeologist.ingest.ast_parser import CodeChunk

class CodebaseHealthAuditor:
    """Audits codebase health, AST complexity metrics, churn hotspots, and technical debt risk."""
    
    def analyze_health(self, chunks: List[CodeChunk], lineage_map: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculates AST complexity, churn hotspots, function size metrics, and overall technical debt score."""
        if not chunks:
            return {
                "health_score": 100,
                "risk_level": "Low",
                "avg_chunk_lines": 0,
                "oversized_chunks": 0,
                "churn_hotspots": [],
                "total_chunks": 0
            }

        lineage_map = lineage_map or {}
        
        # 1. Function / Chunk Size Distribution
        chunk_lengths = [max(1, chunk.end_line - chunk.start_line + 1) for chunk in chunks]
        avg_chunk_lines = round(sum(chunk_lengths) / len(chunk_lengths), 1)
        oversized_chunks = sum(1 for length in chunk_lengths if length > 80)
        oversized_ratio = oversized_chunks / len(chunks)
        
        # 2. Git Churn Hotspots (files modified most frequently)
        churn_counts = {fp: len(commits) for fp, commits in lineage_map.items()}
        sorted_churn = sorted(churn_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        churn_hotspots = [{"file": fp, "commit_count": count} for fp, count in sorted_churn]
        
        # 3. Overall Technical Debt Risk Calculation
        # Risk factors: high average chunk length, high oversized chunk ratio, heavy git churn
        penalty = (avg_chunk_lines * 0.2) + (oversized_ratio * 40)
        if sorted_churn and sorted_churn[0][1] >= 5:
            penalty += 10
            
        health_score = max(0, round(100 - penalty, 1))
        
        if health_score >= 80:
            risk_level = "Low Risk 🟢"
        elif health_score >= 60:
            risk_level = "Moderate Risk 🟡"
        else:
            risk_level = "High Risk 🔴"
            
        return {
            "health_score": health_score,
            "risk_level": risk_level,
            "avg_chunk_lines": avg_chunk_lines,
            "oversized_chunks": oversized_chunks,
            "oversized_ratio_percent": round(oversized_ratio * 100, 1),
            "churn_hotspots": churn_hotspots,
            "total_chunks": len(chunks)
        }
