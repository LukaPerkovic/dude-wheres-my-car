"""Module for retrieving vectors from database and tuning the reponse queries."""

from src.config import Settings

settings = Settings()  # type: ignore


TOP_N_NODES = 5
RERANKER_SYSTEM_PROMPT = """ You're an AI in charge of reranking results from
                                RAG retrieval and ranking of obtain results. Ask no 
                                additional questions and deliver ranked list according 
                                to your best judgement.
                            """
CHOICE_BATCH_SIZE = 25


# def rerank_nodes(nodes):
#     ranker = LLMRerank(
#         top_n=TOP_N_NODES,
#         choice_select_prompt=RERANKER_SYSTEM_PROMPT,
#         choice_batch_size=CHOICE_BATCH_SIZE,
#         llm=settings.rag_model,
#     )
