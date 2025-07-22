"""
AI 평가 시스템 설정 파일

이 모듈은 지원되는 모델, 벤치마크, 그리고 각 벤치마크별 메타데이터 구조를 정의합니다.
"""
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class MySQLConfig:
    """MySQL 데이터베이스 설정"""
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = 'utf8mb4'
    
    @classmethod
    def from_env(cls) -> 'MySQLConfig':
        """환경변수에서 설정 로드"""
        return cls(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', 3306)),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DATABASE', 'ai_evaluation')
        )
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (mysql.connector.connect에 바로 사용)"""
        return {
            'host': self.host,
            'port': self.port,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'charset': self.charset
        }


class SupportedModels(Enum):
    """지원되는 모델 목록"""
    DEEPSEEK_R1 = 'deepseek-r1'
    DEEPSEEK_V3 = 'deepseek-v3'
    LLAMA_4 = 'llama-4'
    GPT_4O = 'gpt-4o'
    CLAUDE_3_5_SONNET = 'claude-3.5-sonnet'
    QWEN_MAX = 'qwen-max'
    GEMINI_PRO = 'gemini-pro'
    LLAMA_3_1_405B = 'llama-3.1-405b'
    MISTRAL_LARGE = 'mistral-large'
    LLAMA_4_MAVERICK = 'llama-4-Maverick'
    LLAMA_4_SCOUT = 'llama-4-Scout'
    GAUSSO_THINK = 'GaussO-Think'
    GAUSSO_THINK_ULTRA = 'GaussO-Think-Ultra'
    KIMI_K2 = 'KIMI-K2'
    KIMI_K2_AWQ = 'KIMI-K2-AWQ'

    @classmethod
    def get_all_models(cls) -> List[str]:
        """모든 모델명을 리스트로 반환"""
        return [model.value for model in cls]


class SupportedBenchmarks(Enum):
    """지원되는 벤치마크 목록"""
    AIME = 'aime'
    MMLU = 'mmlu'
    MMLU_REDUX = 'mmlu-redux'
    MMLU_PRO = 'mmlu-pro'
    MATH500 = 'math500'
    DS_MMLU = 'ds-mmlu'
    HLE = 'hle'

    @classmethod
    def get_all_benchmarks(cls) -> List[str]:
        """모든 벤치마크명을 리스트로 반환"""
        return [benchmark.value for benchmark in cls]


class Config:
    """애플리케이션 설정 클래스"""
    
    # 모델 목록
    MODELS: List[str] = SupportedModels.get_all_models()
    
    # 벤치마크 목록
    BENCHMARKS: List[str] = SupportedBenchmarks.get_all_benchmarks()
    
    # 벤치마크별 테이블 매핑
    BENCHMARK_TABLE_MAPPING: Dict[str, str] = {
        SupportedBenchmarks.AIME.value: 'aime_results',
        SupportedBenchmarks.MMLU.value: 'mmlu_results',
        SupportedBenchmarks.MMLU_REDUX.value: 'mmlu_redux_results',
        SupportedBenchmarks.MMLU_PRO.value: 'mmlu_pro_results',
        SupportedBenchmarks.MATH500.value: 'math500_results',
        SupportedBenchmarks.DS_MMLU.value: 'ds_mmlu_results',
        SupportedBenchmarks.HLE.value: 'hle_results'
    }
    
    # 벤치마크별 사용 가능한 전체 메타데이터 (level1/level2 구분 없음)
    BENCHMARK_METADATA: Dict[str, List[str]] = {
        SupportedBenchmarks.AIME.value: [
            'difficulty', 'business_category', 'competition_year', 'problem_number', 'solution_steps'
        ],
        SupportedBenchmarks.MMLU.value: [
            'difficulty', 'business_category', 'subject', 'category', 'knowledge_source'
        ],
        SupportedBenchmarks.MMLU_REDUX.value: [
            'difficulty', 'business_category', 'subject', 'category', 'cultural_context'
        ],
        SupportedBenchmarks.MMLU_PRO.value: [
            'difficulty', 'business_category', 'subject', 'category', 'complexity', 'interdisciplinary'
        ],
        SupportedBenchmarks.MATH500.value: [
            'difficulty', 'business_category', 'topic', 'level', 'proof_required', 'theorem_dependency'
        ],
        SupportedBenchmarks.DS_MMLU.value: [
            'difficulty', 'business_category', 'subject', 'category', 'industry_relevance'
        ],
        SupportedBenchmarks.HLE.value: [
            'difficulty', 'business_category', 'category', 'philosophical_domain', 'consensus_level', 'complexity'
        ]
    }
    
    @classmethod
    def get_table_name(cls, benchmark: str) -> str:
        """벤치마크명으로 테이블명 조회"""
        return cls.BENCHMARK_TABLE_MAPPING.get(benchmark, f"{benchmark}_results")
    
    @classmethod
    def get_available_metadata(cls, benchmark: str) -> List[str]:
        """벤치마크의 사용 가능한 모든 메타데이터 반환"""
        return cls.BENCHMARK_METADATA.get(benchmark, [])
    
    @classmethod
    def get_remaining_metadata(cls, benchmark: str, selected_metadata: List[str]) -> List[str]:
        """선택된 메타데이터를 제외한 나머지 메타데이터 반환"""
        all_metadata = cls.get_available_metadata(benchmark)
        return [meta for meta in all_metadata if meta not in selected_metadata]
    
    @classmethod
    def is_valid_model(cls, model: str) -> bool:
        """유효한 모델인지 확인"""
        return model in cls.MODELS
    
    @classmethod
    def is_valid_benchmark(cls, benchmark: str) -> bool:
        """유효한 벤치마크인지 확인"""
        return benchmark in cls.BENCHMARKS
    
    @classmethod
    def is_valid_metadata(cls, benchmark: str, metadata: str) -> bool:
        """특정 벤치마크에서 유효한 메타데이터인지 확인"""
        return metadata in cls.get_available_metadata(benchmark)


# 전역 설정 인스턴스
mysql_config = MySQLConfig.from_env()

# 하위 호환성을 위한 기존 변수들 (deprecated)
MODELS = Config.MODELS
BENCHMARKS = Config.BENCHMARKS
BENCHMARK_TABLE_MAPPING = Config.BENCHMARK_TABLE_MAPPING