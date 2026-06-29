import json
from core.query_planner import plan_query

test_questions = [
    "Where was I on January 1 2026?",
    "What happened in January 2026?",
    "Show me everything related to HONOR BRP-NX1",
    "Give me the profile of ABC Corp",
    "When did inverter failures begin?",
    "List all manuals mentioning Modbus"
]

for question in test_questions:
    print(f"Question: {question}")
    result = plan_query(question)
    print(json.dumps(result, indent=2))
    print()