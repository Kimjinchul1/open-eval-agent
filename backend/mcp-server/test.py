"""
AI 모델 성능 분석 MCP 서버

FastAPI 백엔드와 연동하여 AI 모델들의 벤치마크 성능을 분석하는 MCP 서버입니다.
"""

import asyncio
from typing import List, Dict, Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP

# MCP 서버 초기화
mcp = FastMCP("ai-evaluation-server")

# FastAPI 백엔드 URL 설정
BACKEND_URL = "http://127.0.0.1:8000"

class AIEvaluationClient:
    """FastAPI 백엔드와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url = self.base_url, timeout=30.0)
    
    async def get_models(self) -> List[str]:
        """사용 가능한 모델 목록 조회"""
        response = await self.client.get("/models")
        response.raise_for_status()
        return response.json()
    
    async def get_benchmarks(self) -> List[str]:
        """사용 가능한 벤치마크 목록 조회"""
        response = await self.client.get("/benchmarks")
        response.raise_for_status()
        return response.json()
    
    async def get_benchmark_metadata(self, benchmark: str) -> Dict[str, Any]:
        """벤치마크별 메타데이터 조회"""
        response = await self.client.get(f"/benchmarks/{benchmark}/metadata")
        response.raise_for_status()
        return response.json()
    
    async def analyze_performance(
        self,
        models: List[str],
        benchmark: str,
        metadata_level: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """모델 성능 분석"""
        payload = {
            "models": models,
            "benchmark": benchmark,
            "metadata_level": metadata_level or []
        }
        
        response = await self.client.post("/analysis", json=payload)
        response.raise_for_status()
        return response.json()

# 클라이언트 인스턴스
client = AIEvaluationClient()

@mcp.tool()
async def get_available_models() -> str:
    """
    사용 가능한 AI 모델 목록을 조회합니다.
    
    Returns:
        사용 가능한 모델들의 목록을 문자열로 반환
    """
    try:
        models = await client.get_models()
        return f"사용 가능한 모델들:\n" + "\n".join([f"- {model}" for model in models])
    except Exception as e:
        return f"모델 목록 조회 실패: {str(e)}"

@mcp.tool()
async def get_available_benchmarks() -> str:
    """
    사용 가능한 벤치마크 목록을 조회합니다.
    
    Returns:
        사용 가능한 벤치마크들의 목록을 문자열로 반환
    """
    try:
        benchmarks = await client.get_benchmarks()
        return f"사용 가능한 벤치마크들:\n" + "\n".join([f"- {benchmark}" for benchmark in benchmarks])
    except Exception as e:
        return f"벤치마크 목록 조회 실패: {str(e)}"

@mcp.tool()
async def get_benchmark_metadata(benchmark: str) -> str:
    """
    특정 벤치마크에서 사용 가능한 메타데이터를 조회합니다.
    
    Args:
        benchmark: 조회할 벤치마크 이름
        
    Returns:
        해당 벤치마크에서 사용 가능한 메타데이터 목록
    """
    try:
        metadata_info = await client.get_benchmark_metadata(benchmark)
        available_metadata = metadata_info.get("available_metadata", [])
        
        return (f"벤치마크 '{benchmark}'에서 사용 가능한 메타데이터:\n" + 
                "\n".join([f"- {meta}" for meta in available_metadata]))
    except Exception as e:
        return f"메타데이터 조회 실패: {str(e)}"


@mcp.tool()
async def compare_models(
    models: List[str],
    benchmark: str,
    breakdown_level: Optional[List[str]] = None,
) -> str:
    """
    여러 AI 모델들의 성능을 비교 분석합니다. 혹은, 단일 모델에 대한 벤치마크 성능 또한 분석합니다.

    Args:
        models: 비교할 모델들의 리스트 (예: ["gpt-4o", "claude-3.5-sonnet"])
        benchmark: 분석할 벤치마크 (예: "mmlu-redux")
        breakdown_level: 분류 기준 리스트 (예: ["category", "subject", "difficulty"])
        
    Returns:
        모델들의 성능 비교 결과를 포맷된 문자열로 반환
    """