from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + failure analysis."""

import os, sys, json
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON. (Đã implement sẵn)"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation."""
    import math
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
        from datasets import Dataset

        dataset = Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            raise_exceptions=False,
        )
        df = result.to_pandas()
        per_question = []
        for _, row in df.iterrows():
            f_val = row.get("faithfulness", 0.0)
            f_val = float(f_val) if f_val is not None and not (isinstance(f_val, float) and math.isnan(f_val)) else 0.0
            
            ar_val = row.get("answer_relevancy", 0.0)
            ar_val = float(ar_val) if ar_val is not None and not (isinstance(ar_val, float) and math.isnan(ar_val)) else 0.0
            
            cp_val = row.get("context_precision", 0.0)
            cp_val = float(cp_val) if cp_val is not None and not (isinstance(cp_val, float) and math.isnan(cp_val)) else 0.0
            
            cr_val = row.get("context_recall", 0.0)
            cr_val = float(cr_val) if cr_val is not None and not (isinstance(cr_val, float) and math.isnan(cr_val)) else 0.0

            ctxs = row.get("contexts", [])
            if not isinstance(ctxs, list):
                ctxs = [str(ctxs)]

            per_question.append(EvalResult(
                question=str(row.get("question", "")),
                answer=str(row.get("answer", "")),
                contexts=ctxs,
                ground_truth=str(row.get("ground_truth", "")),
                faithfulness=f_val,
                answer_relevancy=ar_val,
                context_precision=cp_val,
                context_recall=cr_val,
            ))

        avg_faithfulness = sum(p.faithfulness for p in per_question) / max(len(per_question), 1)
        avg_relevancy = sum(p.answer_relevancy for p in per_question) / max(len(per_question), 1)
        avg_precision = sum(p.context_precision for p in per_question) / max(len(per_question), 1)
        avg_recall = sum(p.context_recall for p in per_question) / max(len(per_question), 1)

        return {
            "faithfulness": avg_faithfulness,
            "answer_relevancy": avg_relevancy,
            "context_precision": avg_precision,
            "context_recall": avg_recall,
            "per_question": per_question,
        }
    except Exception as e:
        print(f"  ⚠️  RAGAS evaluation failed: {e}")
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
            "context_recall": 0.0,
            "per_question": [],
        }


def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    """Analyze bottom-N worst questions using Diagnostic Tree."""
    diagnostic_tree = {
        "faithfulness": ("LLM hallucinating", "Tighten prompt, lower temperature"),
        "context_recall": ("Missing relevant chunks", "Improve chunking or add BM25"),
        "context_precision": ("Too many irrelevant chunks", "Add reranking or metadata filter"),
        "answer_relevancy": ("Answer doesn't match question", "Improve prompt template"),
    }
    scored_items = []
    for item in eval_results:
        metrics = {
            "faithfulness": item.faithfulness,
            "answer_relevancy": item.answer_relevancy,
            "context_precision": item.context_precision,
            "context_recall": item.context_recall,
        }
        worst_metric = min(metrics, key=metrics.get)
        worst_score = metrics[worst_metric]
        avg_score = sum(metrics.values()) / len(metrics)
        diagnosis, suggested_fix = diagnostic_tree.get(worst_metric, ("Unknown error", "Review pipeline"))
        scored_items.append({
            "question": item.question,
            "answer": item.answer,
            "ground_truth": item.ground_truth,
            "worst_metric": worst_metric,
            "score": worst_score,
            "avg_score": avg_score,
            "diagnosis": diagnosis,
            "suggested_fix": suggested_fix,
        })
    scored_items.sort(key=lambda x: x["avg_score"])
    return scored_items[:bottom_n]


def save_report(results: dict, failures: list[dict], path: str = "ragas_report.json"):
    """Save evaluation report to JSON. (Đã implement sẵn)"""
    report = {
        "aggregate": {k: v for k, v in results.items() if k != "per_question"},
        "num_questions": len(results.get("per_question", [])),
        "failures": failures,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report saved to {path}")


if __name__ == "__main__":
    test_set = load_test_set()
    print(f"Loaded {len(test_set)} test questions")
    print("Run pipeline.py first to generate answers, then call evaluate_ragas().")
