# Open deep research 폴더를 검토하여 해당 폴더의 아키텍쳐가 어떻게 구성되어 있는지 분석하세요: 이는 Supervisor Agent + Sub-Agents로 구성된 대규모 Multi Agent 시스템입니다.

open_deep_research

 - configuration.py: 
 - deep_researcher.py:
 - prompts.py: 
 - state.py:
 - utils.py:

주의) 해당 open deep research 프로젝트는 LangGraph에서 만든 프로젝트로, LangSmith와 Supabase를 연동해야 하는 시스템입니다. 하지만, 현재 구축하려고 하는 Open Eval Agents의 경우 완전한 오픈소스로 OpenAI에서 제공하는 LLM API만 활용할 수 있도록 합니다. 이에 따라 VectorDB, MySQL의 경우 Self-Hosted된 버전으로 구성되어야만 합니다.

 # 구현 계획
open_deep_research는 매우 훌륭하게 구성된 Multi Agent 시스템입니다. 나는 이 Architecture를 본받아, open-eval-agents를 만들려고 합니다. 절차는 아래와 같습니다.

* 내가 해야할 일 * 
- MySQL DB 확인
 MySQL DB (Benchmark Results)에 구축되어 있는 테이블 만들어 놓기 (예전 대시보드 프로젝트에서 활용한 FakeGenerator 활용)
 => mySQL DB가 어떻게 저장되어 있는지 알려줘야 할듯?

- UI의 경우 Open Agent Platform이 완전한 로컬에서 활용 가능한지 검토/ 만약 안된다면, 이전에 보았던 LangGraph Agent Chat UI를 활용할 것. 


2. open-eval-agent build 
(1) 특정 AI 모델의 평가 결과가 저장된 MySQL DB를 활용하여 통계치를 추출하는 Agent (DB 분석 Sub-Agent) 
 Tool: MySQL DB Tool + SQL Interface Tool


(2) 해당 모델의 논문, Technical Reports가 저장된 vector DB System를 기반으로 (1)의 결과와 함께 Insight를 도출하는 Agent (Agentic RAG Sub-Agent) 
 Tool: 

(3) (1)의 통계치를 기반으로 (2)의 Insight를 뒷받침하는 Data Analysis Figure (Bar Chart, Pie Chart, etc)를 만드는 Image Generator Agent 
 Tool: 

(4) 이를 관리하는 SuperVisor Agent
 Tool: 


(5) 최종적으로 모아진 결과를 바탕으로 Markdown 형식으로 Report를 제작하는 One-Shot report Generator Agent
 Tool: 


로 구성되어 있습니다. 이러한 Open-eval-agents의 최종 산출물은 open deep research와 유사하게 잘 정리된 레포트이며, 차별점은 이미지를 포함한다는 점입니다.

따라서, 실제 수행하기 전에 prd.md를 생성하여 수행하고자하는 Task를 정리하세요. (혹은 AWS AGent를 활용하여 TaskMaker 활용할 것)

고려해야할 점:
 1. open-deep-research에서 적용된 비동기 루틴을 모방하세요. 
 Ex) open_deep_research/utils.py 76 lines
 ```python

    async def summarize_webpage(model: BaseChatModel, webpage_content: str) -> str:
        try:
            summary = await asyncio.wait_for(
                model.ainvoke([HumanMessage(content=summarize_webpage_prompt.format(webpage_content=webpage_content, date=get_today_str()))]),
                timeout=60.0
            )
            return f"""<summary>\n{summary.summary}\n</summary>\n\n<key_excerpts>\n{summary.key_excerpts}\n</key_excerpts>"""
        except (asyncio.TimeoutError, Exception) as e:
            print(f"Failed to summarize webpage: {str(e)}")
            return webpage_content


     summarization_tasks = [
        noop() if not result.get("raw_content") else summarize_webpage(
            summarization_model, 
            result['raw_content'][:max_char_to_include],
        )
        for result in unique_results.values()
    ]
    summaries = await asyncio.gather(*summarization_tasks)
```
2. open-deep-research처럼 modern python Architecture를 따르세요.
   2.1 structured_output을 pydantic의 BaseModel로 정의
   2.2 매개변수/리턴 타입 힌트(Type Hints) 

최선을 다하세요. 주저하지 마세요.