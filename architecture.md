Sub Agent 1: Agentic RAG

# dataset semantic search
이건 데이터셋에 RAG를 붙이는 것인데,
우선 Problem + examples -> embedding을 진행한다.

그런 후, 어떠한 질문을 하였을 때 먼저, 이 질문에 대한 여러 유사도 높은 질문을 Reasoning 모델을 통해 Generation (10개 정도)하고, 이 10개의 질문에 대해 쿼리 유사도가 높은 100개의 문항(중복은 제외하고 총 100개가 되도록)에 대해 불러온다.
그 이후 이 문제에 정답을 가장 잘 맞춘 모델은 무엇인지 살펴본다.

# 모델에 대한 semantic search

Sub Agent 2: SQL Agent

현재 갖고 있는 DB에서 Agent가 원하는 값들을 불러올 수 있도록 한다. 이때 중요한 점은 SQL 쿼리문을 직접 생성할 수 있도록 해야 Agentic Capability가 있는 것이므로 이를 잘 설계해야 한다.

Sub Agent 3: Table & Image Generator Agent

