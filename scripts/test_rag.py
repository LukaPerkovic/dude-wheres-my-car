from src.rag.query_engine import create_query_engine

engine = create_query_engine()

questions = [
    "Walk me through the full step-by-step booking process from start to finish",
    "What exactly is the cancellation policy and are there any exceptions?",
]

for q in questions:
    print(f"\nQ: {q}")
    response = engine.query(q)
    print(f"A: {response}")
    print(
        f"Sources: {[n.node.metadata.get('file_name') for n in response.source_nodes]}"
    )
