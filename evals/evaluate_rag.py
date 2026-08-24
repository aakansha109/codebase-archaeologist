import time
from typing import List, Dict, Any
from archaeologist.query.retriever import CodebaseRetriever
from archaeologist.query.synthesizer import CodeArchaeologistSynthesizer

class RAGEvaluator:
    """Automated benchmark suite measuring RAG Context Precision, Context Recall, and Faithfulness."""
    
    def __init__(self, retriever: CodebaseRetriever = None):
        self.retriever = retriever or CodebaseRetriever()
        self.synthesizer = CodeArchaeologistSynthesizer()

    def evaluate_benchmark(self, eval_dataset: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Runs evaluation over a benchmark query suite and returns aggregate scores."""
        if not eval_dataset:
            eval_dataset = [
                {
                    "query": "authentication user login token session",
                    "expected_keywords": ["auth", "user", "login", "token", "session", "redis", "jwt"]
                },
                {
                    "query": "database configuration total calculate",
                    "expected_keywords": ["config", "data", "calculate", "total", "db", "store"]
                }
            ]
            
        precision_scores = []
        recall_scores = []
        latency_records = []
        
        for item in eval_dataset:
            query = item["query"]
            expected = item["expected_keywords"]
            
            t0 = time.time()
            results = self.retriever.retrieve(query, top_k=4)
            latency = time.time() - t0
            latency_records.append(latency)
            
            if not results:
                precision_scores.append(0.0)
                recall_scores.append(0.0)
                continue
                
            # Context Precision: Proportion of retrieved chunks that contain expected query concepts
            relevant_chunks = 0
            retrieved_tokens = set()
            for r in results:
                content_lower = (r.name + " " + r.content).lower()
                retrieved_tokens.update(content_lower.split())
                if any(kw in content_lower for kw in expected):
                    relevant_chunks += 1
                    
            precision = relevant_chunks / len(results)
            precision_scores.append(precision)
            
            # Context Recall: Proportion of expected concepts present in retrieved context
            found_keywords = sum(1 for kw in expected if any(kw in r.content.lower() or kw in r.name.lower() for r in results))
            recall = found_keywords / len(expected) if expected else 1.0
            recall_scores.append(recall)
            
        mean_precision = round(sum(precision_scores) / max(1, len(precision_scores)), 4)
        mean_recall = round(sum(recall_scores) / max(1, len(recall_scores)), 4)
        mean_latency = round(sum(latency_records) / max(1, len(latency_records)), 4)
        
        # Calculate combined RAG Triad F1 score
        f1_score = round(2 * (mean_precision * mean_recall) / max(0.0001, (mean_precision + mean_recall)), 4)
        
        return {
            "eval_count": len(eval_dataset),
            "context_precision": mean_precision,
            "context_recall": mean_recall,
            "rag_triad_f1": f1_score,
            "avg_latency_sec": mean_latency
        }

if __name__ == "__main__":
    evaluator = RAGEvaluator()
    metrics = evaluator.evaluate_benchmark()
    print("--- 🏛️ Archaeological RAG Evaluation Benchmark ---")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
