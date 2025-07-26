"""
AI 모델 성능 분석 MCP 서버 (시각화 기능 포함)

FastAPI 백엔드와 연동하여 AI 모델들의 벤치마크 성능을 분석하는 MCP 서버입니다.
다중 벤치마크 분석 및 메타데이터 기반 분석을 지원하며, 바 차트 시각화 기능을 제공합니다.
"""

import asyncio
import os
import tempfile
from typing import List, Dict, Any, Optional, Union
import httpx
from fastmcp import FastMCP

# 시각화 라이브러리
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# MCP 서버 초기화
mcp = FastMCP("ai-evaluation-server")

# FastAPI 백엔드 URL 설정
BACKEND_URL = "http://127.0.0.1:8000"

class AIEvaluationClient:
    """FastAPI 백엔드와 통신하는 클라이언트"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
    
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
        benchmarks: List[str],
        metadata_level: Optional[Union[List[str], Dict[str, List[str]]]] = None
    ) -> Dict[str, Any]:
        """다중 벤치마크 모델 성능 분석"""
        payload = {
            "models": models,
            "benchmarks": benchmarks,
            "metadata_level": metadata_level or []
        }
        
        response = await self.client.post("/analysis", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def get_analysis_summary(self) -> Dict[str, Any]:
        """전체 데이터 요약 정보 조회"""
        response = await self.client.get("/analysis/summary")
        response.raise_for_status()
        return response.json()

# 클라이언트 인스턴스
client = AIEvaluationClient()

async def generate_visualization(
    data: List[Dict], 
    title: str,
    metadata_columns: Optional[List[str]] = None,
    models: Optional[List[str]] = None,
    benchmark_name: Optional[str] = None,
    chart_type: str = "performance"
) -> str:
    """
    데이터를 바탕으로 바 차트 시각화를 생성합니다.
    
    Args:
        data: 분석 결과 데이터
        title: 차트 제목
        metadata_columns: 메타데이터 컬럼들 (최대 2개)
        models: 모델 리스트 (다중 모델 비교용)
        benchmark_name: 벤치마크 이름
        chart_type: 차트 타입 ("performance", "comparison", "metadata")
        
    Returns:
        생성된 이미지 파일의 경로
    """
    try:
        if not data:
            return "데이터가 없어 차트를 생성할 수 없습니다."
        
        # 시각화 스타일 설정
        sns.set_style("whitegrid")
        plt.style.use('seaborn-v0_8')
        
        # 데이터프레임 생성
        df = pd.DataFrame(data)
        
        # 차트 크기 설정
        if metadata_columns and len(metadata_columns) == 2:
            fig, ax = plt.subplots(figsize=(14, 8))
        elif metadata_columns and len(metadata_columns) == 1:
            fig, ax = plt.subplots(figsize=(12, 6))
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "comparison" and models and len(models) > 1:
            # 다중 모델 비교 차트
            if metadata_columns and len(metadata_columns) >= 1:
                # 메타데이터별 모델 비교
                x_col = metadata_columns[0]
                if len(metadata_columns) == 2:
                    hue_col = metadata_columns[1]
                    # 2차원 메타데이터: x축은 첫 번째, hue는 두 번째
                    sns.barplot(data=df, x=x_col, y='avg_match_score', hue=hue_col, ax=ax, palette='viridis')
                else:
                    # 1차원 메타데이터: x축은 메타데이터, hue는 모델
                    sns.barplot(data=df, x=x_col, y='avg_match_score', hue='model', ax=ax, palette='Set2')
            else:
                # 메타데이터 없이 모델별 직접 비교
                sns.barplot(data=df, x='model', y='avg_match_score', ax=ax, palette='Set1')
                
        elif metadata_columns:
            # 메타데이터 기반 단일 모델 분석
            if len(metadata_columns) == 2:
                # 2차원 메타데이터: 첫 번째를 x축, 두 번째를 hue로
                x_col, hue_col = metadata_columns[0], metadata_columns[1]
                sns.barplot(data=df, x=x_col, y='avg_match_score', hue=hue_col, ax=ax, palette='viridis')
                ax.legend(title=hue_col.title(), bbox_to_anchor=(1.05, 1), loc='upper left')
            else:
                # 1차원 메타데이터
                x_col = metadata_columns[0]
                sns.barplot(data=df, x=x_col, y='avg_match_score', ax=ax, palette='viridis')
                
            # x축 레이블 회전 (메타데이터 값이 긴 경우)
            plt.xticks(rotation=45, ha='right')
            
        else:
            # 단순 성능 바 차트 (메타데이터 없음)
            if 'model' in df.columns:
                sns.barplot(data=df, x='model', y='avg_match_score', ax=ax, palette='Set1')
            else:
                # 단일 모델인 경우
                ax.bar(['Score'], [df['avg_match_score'].iloc[0] if len(df) > 0 else 0], color='skyblue')
        
        # 차트 꾸미기
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('Average Match Score', fontsize=12)
        ax.set_xlabel(ax.get_xlabel(), fontsize=12)
        
        # y축 범위 설정 (0부터 최대값의 110%까지)
        if len(df) > 0 and 'avg_match_score' in df.columns:
            max_score = df['avg_match_score'].max()
            ax.set_ylim(0, max_score * 1.1)
            
            # 값 표시
            for container in ax.containers:
                ax.bar_label(container, fmt='%.3f', fontsize=10)
        
        # 레이아웃 조정
        plt.tight_layout()
        
        # 임시 파일로 저장
        temp_dir = tempfile.gettempdir()
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_evaluation_chart_{timestamp}.png"
        filepath = os.path.join(temp_dir, filename)
        
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return f"차트가 생성되었습니다: {filepath}"
        
    except Exception as e:
        plt.close()  # 오류 시에도 figure 정리
        return f"차트 생성 실패: {str(e)}"

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
async def analyze_single_model(
    model: str,
    benchmarks: List[str],
    metadata_level: Optional[List[str]] = None,
    generate_chart: bool = False
) -> str:
    """
    단일 모델에 대해 하나 이상의 벤치마크에서 성능을 분석합니다.
    
    Args:
        model: 분석할 모델명 (예: "gpt-4o")
        benchmarks: 분석할 벤치마크 리스트 (예: ["mmlu-redux", "hellaswag"])
        metadata_level: 분류 기준 리스트 (예: ["category", "subject"])
        generate_chart: 차트 생성 여부 (기본값: False)
        
    Returns:
        모델의 벤치마크별 성능 분석 결과를 포맷된 문자열로 반환
    """
    try:
        if not benchmarks:
            return "오류: 최소 하나의 벤치마크를 지정해야 합니다."
        
        # 성능 분석 요청
        results = await client.analyze_performance(
            models=[model],
            benchmarks=benchmarks,
            metadata_level=metadata_level or []
        )
        
        if not results or not results.get("benchmark_results"):
            return f"모델 '{model}'에 대한 데이터를 찾을 수 없습니다."
        
        # 결과 포맷팅
        output = [f"모델 성능 분석 결과: {model}"]
        output.append(f"분석 벤치마크: {', '.join(benchmarks)}")
        
        if metadata_level:
            output.append(f"분류 기준: {' > '.join(metadata_level)}")
        
        output.append("=" * 60)
        
        # 차트 생성을 위한 데이터 수집
        chart_data = []
        
        # 각 벤치마크별 결과 처리
        for benchmark_result in results["benchmark_results"]:
            benchmark_name = benchmark_result["benchmark"]
            benchmark_summary = benchmark_result["summary"]
            benchmark_data = benchmark_result["results"]
            
            output.append(f"\n[{benchmark_name}] 벤치마크 결과")
            output.append("-" * 40)
            
            if not metadata_level:
                # 메타데이터 그룹화 없는 경우 - 전체 평균
                if benchmark_data:
                    result = benchmark_data[0]
                    output.append(f"전체 평균 점수: {result['avg_match_score']:.4f}")
                    output.append(f"총 문제 수: {result['total_questions']:,}개")
                    
                    # 차트 데이터 추가
                    chart_data.append({
                        'benchmark': benchmark_name,
                        'avg_match_score': result['avg_match_score'],
                        'total_questions': result['total_questions']
                    })
                else:
                    output.append("데이터 없음")
            else:
                # 메타데이터별 그룹 결과 - 전체 테이블 형태로 표시
                output.append(f"총 {benchmark_summary['total_groups']}개 그룹 분석")
                output.append(f"벤치마크 평균: {benchmark_summary['avg_score']:.4f}")
                output.append(f"최고 점수: {benchmark_summary['max_score']:.4f}")
                output.append(f"최저 점수: {benchmark_summary['min_score']:.4f}")
                output.append("")
                
                if benchmark_data:
                    # 성능순 정렬
                    sorted_results = sorted(benchmark_data, key=lambda x: x['avg_match_score'], reverse=True)
                    
                    # 마크다운 테이블 헤더 생성
                    headers = []
                    for col in metadata_level:
                        headers.append(col.title())
                    headers.extend(["Score", "Questions"])
                    
                    # 테이블 헤더
                    output.append("| " + " | ".join(headers) + " |")
                    output.append("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|")
                    
                    # 테이블 데이터 행
                    for result in sorted_results:
                        row_data = []
                        
                        # 메타데이터 컬럼들
                        for col in metadata_level:
                            value = result.get(col, "N/A")
                            row_data.append(str(value))
                        
                        # 점수와 문제 수
                        row_data.append(f"{result['avg_match_score']:.4f}")
                        row_data.append(f"{result['total_questions']:,}")
                        
                        output.append("| " + " | ".join(row_data) + " |")
                        
                        # 차트 데이터 추가 (메타데이터 포함)
                        chart_entry = {
                            'benchmark': benchmark_name,
                            'avg_match_score': result['avg_match_score'],
                            'total_questions': result['total_questions']
                        }
                        for col in metadata_level:
                            chart_entry[col] = result.get(col, "N/A")
                        chart_data.append(chart_entry)
                    
                    output.append("")  # 테이블 후 빈 줄
                else:
                    output.append("데이터 없음")
        
        # 전체 요약
        summary = results["summary"]
        output.append(f"\n전체 분석 요약:")
        output.append(f"  분석된 벤치마크: {summary['total_benchmarks']}개")
        output.append(f"  총 분석 그룹: {summary['total_result_groups']}개")
        output.append(f"  분석 유형: {summary['analysis_type']}")
        
        # 차트 생성
        if generate_chart and chart_data:
            chart_title = f"{model} - Performance Analysis"
            if len(benchmarks) == 1:
                chart_title += f" ({benchmarks[0]})"
            
            chart_result = await generate_visualization(
                data=chart_data,
                title=chart_title,
                metadata_columns=metadata_level[:2] if metadata_level else None,  # 최대 2개까지
                models=[model],
                chart_type="performance"
            )
            output.append(f"\n{chart_result}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"성능 분석 실패: {str(e)}"

@mcp.tool()
async def analyze_single_model_with_metadata(
    model: str,
    benchmark: str,
    metadata_columns: List[str],
    generate_chart: bool = False
) -> str:
    """
    단일 모델에 대해 특정 벤치마크에서 메타데이터별 세부 성능을 분석합니다.
    
    Args:
        model: 분석할 모델명
        benchmark: 분석할 벤치마크 (단일)
        metadata_columns: 세부 분석할 메타데이터 컬럼들
        generate_chart: 차트 생성 여부 (기본값: False)
        
    Returns:
        메타데이터별 세부 성능 분석 결과
    """
    try:
        if not metadata_columns:
            return "오류: 최소 하나의 메타데이터 컬럼을 지정해야 합니다."
        
        results = await client.analyze_performance(
            models=[model],
            benchmarks=[benchmark],
            metadata_level=metadata_columns
        )
        
        if not results or not results.get("benchmark_results"):
            return f"모델 '{model}'과 벤치마크 '{benchmark}'에 대한 데이터를 찾을 수 없습니다."
        
        benchmark_result = results["benchmark_results"][0]
        benchmark_data = benchmark_result["results"]
        benchmark_summary = benchmark_result["summary"]
        
        output = [f"메타데이터별 세부 성능 분석"]
        output.append(f"모델: {model}")
        output.append(f"벤치마크: {benchmark}")
        output.append(f"분석 기준: {' > '.join(metadata_columns)}")
        output.append("=" * 60)
        
        # 요약 통계
        output.append(f"\n전체 요약:")
        output.append(f"  총 분석 그룹: {benchmark_summary['total_groups']}개")
        output.append(f"  평균 점수: {benchmark_summary['avg_score']:.4f}")
        output.append(f"  점수 범위: {benchmark_summary['min_score']:.4f} ~ {benchmark_summary['max_score']:.4f}")
        output.append(f"  총 문제 수: {benchmark_summary['total_questions']:,}개")
        
        # 성능순 정렬하여 모든 결과 표시
        sorted_results = sorted(benchmark_data, key=lambda x: x['avg_match_score'], reverse=True)
        
        # 상대값 기반 성능 레벨 계산을 위한 percentile 계산
        scores = [result['avg_match_score'] for result in sorted_results]
        total_groups = len(scores)
        
        def get_performance_level(score: float, rank: int) -> str:
            """상대값 기반 성능 레벨 계산"""
            if total_groups <= 1:
                return "단일"
            elif total_groups <= 3:
                if rank == 1:
                    return "높음"
                elif rank == total_groups:
                    return "낮음"
                else:
                    return "중간"
            elif total_groups >= 10:
                # 10개 이상일 때: 최상위, 높음, 중간, 낮음, 최하위
                top_10_cutoff = max(1, int(total_groups * 0.1))  # 상위 10%
                top_25_cutoff = max(1, int(total_groups * 0.25))  # 상위 25%
                bottom_25_cutoff = max(1, int(total_groups * 0.75))  # 하위 25%
                bottom_10_cutoff = max(1, int(total_groups * 0.9))  # 하위 10%
                
                if rank <= top_10_cutoff:
                    return "최상위"
                elif rank <= top_25_cutoff:
                    return "높음"
                elif rank <= bottom_25_cutoff:
                    return "중간"
                elif rank <= bottom_10_cutoff:
                    return "낮음"
                else:
                    return "최하위"
            else:
                # 4-9개일 때: 기존 3단계 로직
                top_25_cutoff = max(1, int(total_groups * 0.25))
                bottom_25_cutoff = max(1, int(total_groups * 0.75))
                
                if rank <= top_25_cutoff:
                    return "높음"
                elif rank <= bottom_25_cutoff:
                    return "중간"
                else:
                    return "낮음"
        
        output.append(f"\n세부 결과 ({len(sorted_results)}개 그룹):")
        output.append("-" * 50)
        
        chart_data = []
        
        if sorted_results:
            # 마크다운 테이블 헤더 생성
            headers = ["Rank"]
            for col in metadata_columns:
                headers.append(col.title())
            headers.extend(["Score", "Questions", "Performance Level", "Percentile"])
            
            # 테이블 헤더
            output.append("| " + " | ".join(headers) + " |")
            output.append("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|")
            
            # 테이블 데이터 행
            for i, result in enumerate(sorted_results, 1):
                row_data = []
                
                # 순위
                row_data.append(str(i))
                
                # 메타데이터 컬럼들
                for col in metadata_columns:
                    value = result.get(col, "N/A")
                    row_data.append(str(value))
                
                # 점수와 문제 수
                row_data.append(f"{result['avg_match_score']:.4f}")
                row_data.append(f"{result['total_questions']:,}")
                
                # 상대값 기반 성능 레벨과 백분위
                level = get_performance_level(result['avg_match_score'], i)
                percentile = int((1 - (i - 1) / total_groups) * 100) if total_groups > 1 else 100
                row_data.append(level)
                row_data.append(f"상위 {percentile}%")
                
                output.append("| " + " | ".join(row_data) + " |")
                
                # 차트 데이터 추가
                chart_entry = {
                    'avg_match_score': result['avg_match_score'],
                    'total_questions': result['total_questions'],
                    'rank': i
                }
                for col in metadata_columns:
                    chart_entry[col] = result.get(col, "N/A")
                chart_data.append(chart_entry)
            
            output.append("")  # 테이블 후 빈 줄
        else:
            output.append("데이터 없음")
        
        # 차트 생성
        if generate_chart and chart_data:
            chart_title = f"{model} - {benchmark} Metadata Analysis"
            chart_result = await generate_visualization(
                data=chart_data,
                title=chart_title,
                metadata_columns=metadata_columns[:2],  # 최대 2개까지
                models=[model],
                benchmark_name=benchmark,
                chart_type="metadata"
            )
            output.append(f"\n{chart_result}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"메타데이터별 분석 실패: {str(e)}"


@mcp.tool()
async def compare_models_multi_benchmark(
    models: List[str],
    benchmarks: List[str],
    metadata_level: Optional[Union[List[str], Dict[str, List[str]]]] = None,
    generate_chart: bool = False
) -> str:
    """
    여러 모델을 여러 벤치마크에서 비교 분석합니다.
    
    Args:
        models: 비교할 모델들의 리스트
        benchmarks: 분석할 벤치마크들의 리스트  
        metadata_level: 벤치마크별 메타데이터 설정 (Dict) 또는 공통 메타데이터 (List)
        generate_chart: 차트 생성 여부 (기본값: False)
        
    Returns:
        다중 벤치마크에서의 모델 비교 결과
    """
    try:
        if not models:
            return "오류: 최소 하나의 모델을 지정해야 합니다."
        if not benchmarks:
            return "오류: 최소 하나의 벤치마크를 지정해야 합니다."
        
        results = await client.analyze_performance(
            models=models,
            benchmarks=benchmarks,
            metadata_level=metadata_level
        )
        
        if not results or not results.get("benchmark_results"):
            return "지정된 조건에 해당하는 데이터를 찾을 수 없습니다."
        
        output = [f"다중 벤치마크 모델 비교 분석"]
        output.append(f"비교 모델: {', '.join(models)}")
        output.append(f"분석 벤치마크: {', '.join(benchmarks)}")
        output.append("=" * 60)
        
        # 전체 벤치마크 요약을 위한 데이터 저장
        benchmark_summaries = {}
        chart_data = []
        
        for benchmark_result in results["benchmark_results"]:
            benchmark_name = benchmark_result["benchmark"]
            benchmark_data = benchmark_result["results"]
            benchmark_summary = benchmark_result["summary"]
            
            output.append(f"\n[{benchmark_name}] 벤치마크 결과")
            output.append("-" * 40)
            
            if not metadata_level or (isinstance(metadata_level, list) and not metadata_level):
                # 메타데이터 그룹화 없는 경우 - 단순한 모델별 비교 테이블
                model_scores = {}
                for result in benchmark_data:
                    # 결과에서 모델별 점수를 추출 (현재는 models가 리스트로 오는 것 같음)
                    if result.get('models'):
                        for model in result['models']:
                            if model in models:  # 요청한 모델들 중에서만
                                model_scores[model] = {
                                    'score': result['avg_match_score'],
                                    'questions': result['total_questions']
                                }
                
                if model_scores:
                    # 모델 비교 테이블
                    output.append("| Model | Score | Questions |")
                    output.append("|-------|-------|-----------|")
                    
                    # 점수순으로 정렬
                    sorted_models = sorted(model_scores.items(), key=lambda x: x[1]['score'], reverse=True)
                    for model, data in sorted_models:
                        output.append(f"| {model} | {data['score']:.4f} | {data['questions']:,} |")
                        
                        # 차트 데이터 추가
                        chart_data.append({
                            'model': model,
                            'benchmark': benchmark_name,
                            'avg_match_score': data['score'],
                            'total_questions': data['questions']
                        })
                    
                    output.append("")
                
                # 요약 정보 저장
                benchmark_summaries[benchmark_name] = {model: data['score'] for model, data in model_scores.items()}
                
            else:
                # 메타데이터 그룹화가 있는 경우 - 피벗 테이블 형태
                output.append(f"총 분석 그룹: {benchmark_summary['total_groups']}개")
                output.append(f"벤치마크 평균: {benchmark_summary['avg_score']:.4f}")
                output.append(f"점수 범위: {benchmark_summary['min_score']:.4f} ~ {benchmark_summary['max_score']:.4f}")
                output.append("")
                
                if benchmark_data:
                    # 메타데이터 컬럼 확인
                    if isinstance(metadata_level, dict):
                        current_metadata_cols = metadata_level.get(benchmark_name, [])
                    else:
                        current_metadata_cols = metadata_level
                    
                    if current_metadata_cols:
                        # 데이터를 피벗 테이블 형태로 재구성
                        # 각 메타데이터 조합별로 모델별 점수를 매핑
                        pivot_data = {}
                        
                        for result in benchmark_data:
                            # 메타데이터 키 생성
                            metadata_key = tuple(result.get(col, "N/A") for col in current_metadata_cols)
                            
                            if metadata_key not in pivot_data:
                                pivot_data[metadata_key] = {}
                            
                            # 백엔드에서 제공하는 model_scores 활용 (각 모델의 개별 점수)
                            if 'model_scores' in result and result['model_scores']:
                                # model_scores가 있는 경우 - 각 모델의 개별 점수 사용
                                for model_name, model_data in result['model_scores'].items():
                                    if model_name in models:
                                        pivot_data[metadata_key][model_name] = {
                                            'score': model_data['score'],
                                            'questions': model_data['questions']
                                        }
                            else:
                                # model_scores가 없는 경우 - 기존 로직 사용 (하위 호환성)
                                result_models = result.get('models', [])
                                score = result['avg_match_score']
                                questions = result['total_questions']
                                
                                for model in result_models:
                                    if model in models:
                                        pivot_data[metadata_key][model] = {
                                            'score': score,
                                            'questions': questions
                                        }
                        
                        # 피벗 테이블 생성
                        if pivot_data:
                            # 헤더 생성
                            headers = []
                            for col in current_metadata_cols:
                                headers.append(col.title())
                            headers.extend(models)  # 각 모델을 컬럼으로
                            
                            # 테이블 헤더
                            output.append("| " + " | ".join(headers) + " |")
                            output.append("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|")
                            
                            # 메타데이터 키별로 정렬 (점수 기준)
                            def get_avg_score(item):
                                _, model_data = item
                                scores = [data['score'] for data in model_data.values() if 'score' in data]
                                return sum(scores) / len(scores) if scores else 0
                            
                            sorted_pivot_data = sorted(pivot_data.items(), key=get_avg_score, reverse=True)
                            
                            # 데이터 행 생성
                            for metadata_key, model_data in sorted_pivot_data:
                                row_data = []
                                
                                # 메타데이터 컬럼들
                                for meta_value in metadata_key:
                                    row_data.append(str(meta_value))
                                
                                # 각 모델의 점수
                                for model in models:
                                    if model in model_data:
                                        score = model_data[model]['score']
                                        row_data.append(f"{score:.4f}")
                                    else:
                                        row_data.append("N/A")
                                
                                output.append("| " + " | ".join(row_data) + " |")
                                
                                # 차트 데이터 추가 (메타데이터 포함)
                                for model in models:
                                    if model in model_data:
                                        chart_entry = {
                                            'model': model,
                                            'benchmark': benchmark_name,
                                            'avg_match_score': model_data[model]['score'],
                                            'total_questions': model_data[model]['questions']
                                        }
                                        for i, col in enumerate(current_metadata_cols):
                                            chart_entry[col] = metadata_key[i]
                                        chart_data.append(chart_entry)
                            
                            output.append("")
                
                # 메타데이터가 있는 경우에는 종합 순위 테이블을 생성하지 않음
                # (메타데이터별로 세분화된 결과이므로)
        
        # 전체 벤치마크 종합 순위 (메타데이터 그룹화가 없는 경우만)
        if not metadata_level or (isinstance(metadata_level, list) and not metadata_level):
            if len(benchmarks) > 1 and benchmark_summaries:
                output.append(f"\n전체 벤치마크 종합 순위:")
                output.append("=" * 40)
                
                # 각 모델의 평균 점수 계산
                model_avg_scores = {}
                model_detailed_scores = {}
                
                for model in models:
                    scores = []
                    detailed_scores = {}
                    for benchmark_name, model_scores in benchmark_summaries.items():
                        if model in model_scores:
                            score = model_scores[model]
                            scores.append(score)
                            detailed_scores[benchmark_name] = score
                    
                    if scores:
                        model_avg_scores[model] = sum(scores) / len(scores)
                        model_detailed_scores[model] = detailed_scores
                
                # 종합 순위를 테이블로 표시
                if model_avg_scores:
                    sorted_models = sorted(model_avg_scores.items(), key=lambda x: x[1], reverse=True)
                    
                    # 테이블 헤더 생성
                    headers = ["Rank", "Model", "Average"]
                    headers.extend(benchmarks)
                    
                    output.append("| " + " | ".join(headers) + " |")
                    output.append("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|")
                    
                    # 테이블 데이터 행
                    for rank, (model, avg_score) in enumerate(sorted_models, 1):
                        row_data = [str(rank), model, f"{avg_score:.4f}"]
                        
                        # 각 벤치마크별 점수
                        for benchmark_name in benchmarks:
                            if model in model_detailed_scores and benchmark_name in model_detailed_scores[model]:
                                score = model_detailed_scores[model][benchmark_name]
                                row_data.append(f"{score:.4f}")
                            else:
                                row_data.append("N/A")
                        
                        output.append("| " + " | ".join(row_data) + " |")
                    
                    output.append("")
        
        # 분석 요약
        summary = results["summary"]
        output.append(f"\n분석 요약:")
        output.append(f"  분석된 모델: {len(summary['models_analyzed'])}개")
        output.append(f"  분석된 벤치마크: {summary['total_benchmarks']}개")
        output.append(f"  총 분석 그룹: {summary['total_result_groups']}개")
        
        # 차트 생성
        if generate_chart and chart_data:
            chart_title = f"Multi-Model Multi-Benchmark Comparison"
            
            # 메타데이터 존재 여부에 따라 차트 설정
            if metadata_level and isinstance(metadata_level, list) and metadata_level:
                metadata_cols = metadata_level[:2]  # 최대 2개
            elif metadata_level and isinstance(metadata_level, dict):
                # dict인 경우 첫 번째 벤치마크의 메타데이터 사용
                first_benchmark = list(metadata_level.keys())[0]
                metadata_cols = metadata_level[first_benchmark][:2]
            else:
                metadata_cols = None
            
            chart_result = await generate_visualization(
                data=chart_data,
                title=chart_title,
                metadata_columns=metadata_cols,
                models=models,
                chart_type="comparison"
            )
            output.append(f"\n{chart_result}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"다중 벤치마크 비교 분석 실패: {str(e)}"


@mcp.tool()
async def get_data_overview() -> str:
    """
    전체 데이터 현황 및 요약 정보를 조회합니다.
    
    Returns:
        각 벤치마크별 데이터 현황 요약
    """
    try:
        summary = await client.get_analysis_summary()
        
        if not summary:
            return "데이터 요약 정보를 가져올 수 없습니다."
        
        output = ["AI 평가 데이터 현황"]
        output.append("=" * 50)
        
        for benchmark, info in summary.items():
            output.append(f"\n[{benchmark}] 벤치마크")
            
            if "error" in info:
                output.append(f"  상태: 오류 - {info['error']}")
                continue
            
            output.append(f"  총 레코드: {info['total_records']:,}개")
            output.append(f"  고유 모델: {info['unique_models']}개")
            output.append(f"  평균 점수: {info['avg_score']:.4f}")
            output.append(f"  표준편차: {info['std_score']:.4f}")
            output.append(f"  점수 분포:")
            output.append(f"    - 1분위수 (Q1): {info['q1_score']:.4f}")
            output.append(f"    - 중앙값 (Median): {info['median_score']:.4f}")
            output.append(f"    - 3분위수 (Q3): {info['q3_score']:.4f}")
            
            if info.get('available_metadata'):
                output.append(f"  사용가능 메타데이터: {', '.join(info['available_metadata'])}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"데이터 현황 조회 실패: {str(e)}"

if __name__ == "__main__":
    # MCP 서버 실행
    mcp.run()