from core.query_planner import plan_query
from core.query_executor import execute_query
from core.answer_synthesizer import synthesize_answer


def ask(question, backend):
    """
    End-to-end Librarian query pipeline.
    
    Args:
        question: Natural language question
        backend: StorageBackend instance
    
    Returns:
        Dict with question, plan, evidence, and answer
    """
    plan = plan_query(question)
    
    evidence_package = execute_query(
        plan,
        backend
    )
    
    answer = synthesize_answer(
        question,
        {
            "question": question,
            "intent": plan.get("intent"),
            "evidence": evidence_package.get("evidence", {})
        }
    )
    
    return {
        "question": question,
        "plan": plan,
        "evidence": evidence_package,
        "answer": answer
    }