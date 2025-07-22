from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Tuple, Union
import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
import logging
import atexit

# Config 모듈 import
from config import Config, SupportedModels, SupportedBenchmarks, mysql_config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection Pool 설정
class DatabaseManager:
    """데이터베이스 연결 풀 관리"""
    
    def __init__(self):
        self.pool = None
        self.setup_pool()
    
    def setup_pool(self):
        """Connection Pool 설정"""
        try:
            pool_config = mysql_config.to_dict()
            pool_config.update({
                'pool_name': 'ai_evaluation_pool',
                'pool_size': 10,
                'pool_reset_session': True,
                'autocommit': True
            })
            
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info("데이터베이스 Connection Pool 생성 완료")
            
            atexit.register(self.close_pool)
            
        except Error as e:
            logger.error(f"Connection Pool 생성 실패: {e}")
            raise RuntimeError(f"데이터베이스 풀 설정 실패: {str(e)}")
    
    @contextmanager
    def get_connection(self):
        """Context Manager로 연결 관리"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"데이터베이스 연결 오류: {e}")
            raise HTTPException(status_code=500, detail=f"데이터베이스 연결 실패: {str(e)}")
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def close_pool(self):
        """Connection Pool 종료"""
        if self.pool:
            logger.info("데이터베이스 Connection Pool 종료")

# 전역 DB 매니저
db_manager = DatabaseManager()

# FastAPI 앱 생성
app = FastAPI(
    title="AI 평가 데이터 분석 API",
    description="AI 모델의 벤치마크 성능 분석을 위한 API",
    version="1.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic 모델들
class AnalysisRequest(BaseModel):
    """성능 분석 요청 모델 - 다중 벤치마크 지원"""
    models: List[SupportedModels] = Field(..., description="분석할 모델 리스트")
    benchmarks: List[SupportedBenchmarks] = Field(..., description="분석할 벤치마크 리스트")
    metadata_level: Union[List[str], Dict[str, List[str]]] = Field(
        default=[], 
        description="메타데이터 레벨 설정. 벤치마크가 1개면 List[str], 2개 이상이면 Dict[benchmark_name, List[str]]"
    )
    
    def get_metadata_for_benchmark(self, benchmark: str) -> List[str]:
        """특정 벤치마크의 메타데이터 레벨 반환"""
        if isinstance(self.metadata_level, dict):
            return self.metadata_level.get(benchmark, [])
        elif isinstance(self.metadata_level, list):
            # 벤치마크가 1개인 경우, 모든 벤치마크에 동일한 메타데이터 적용
            return self.metadata_level
        else:
            return []

class MetadataInfo(BaseModel):
    """메타데이터 정보 모델"""
    available_metadata: List[str]

class MetadataOptions(BaseModel):
    """동적 메타데이터 옵션"""
    level1_selected: List[str]
    level2_options: List[str]

class BenchmarkAnalysisResult(BaseModel):
    """개별 벤치마크 분석 결과"""
    benchmark: str
    metadata_columns: List[str]
    results: List[Dict[str, Any]]
    summary: Dict[str, Any]

# 의존성 함수
def get_db():
    """FastAPI Dependency로 DB 연결 제공"""
    return db_manager.get_connection()


def build_analysis_query(benchmark: str, models: List[str], metadata_columns: List[str]) -> Tuple[str, List[str]]:
    """단일 벤치마크에 대한 동적 SQL 쿼리 생성 - 모델별 개별 점수 지원"""
    table_name = Config.get_table_name(benchmark)
    
    where_conditions = []
    params = []
    
    # 모델 필터
    model_placeholders = ', '.join(['%s'] * len(models))
    where_conditions.append(f"model_name IN ({model_placeholders})")
    params.extend(models)
    
    if metadata_columns:
        # 그룹화 있음 - 메타데이터 + 모델명으로 그룹화하여 각 모델의 개별 점수 구함
        select_columns = metadata_columns + [
            "model_name",  # 모델명 추가
            "AVG(match_score) as avg_match_score",
            "COUNT(*) as total_questions"
        ]
        
        # NULL 값 제외
        for column in metadata_columns:
            where_conditions.append(f"{column} IS NOT NULL")
        
        # 메타데이터 + 모델명으로 그룹화
        group_by_columns = metadata_columns + ["model_name"]
        
        query = f"""
        SELECT {', '.join(select_columns)}
        FROM {table_name}
        WHERE {' AND '.join(where_conditions)}
        GROUP BY {', '.join(group_by_columns)}
        ORDER BY {', '.join(metadata_columns)}, avg_match_score DESC
        """
    else:
        # 메타데이터 그룹화 없이 모델별 평균
        query = f"""
        SELECT model_name,
            AVG(match_score) as avg_match_score,
            COUNT(*) as total_questions
        FROM {table_name}
        WHERE {' AND '.join(where_conditions)}
        GROUP BY model_name
        ORDER BY avg_match_score DESC
        """
    
    return query, params

def execute_benchmark_analysis(connection, benchmark: str, models: List[str], metadata_columns: List[str]) -> Dict[str, Any]:
    """단일 벤치마크 분석 실행 - 모델별 개별 결과 처리"""
    cursor = connection.cursor(dictionary=True)
    
    try:
        # 쿼리 생성 및 실행
        query, params = build_analysis_query(benchmark, models, metadata_columns)
        logger.info(f"[{benchmark}] 실행할 쿼리: {query}")
        
        cursor.execute(query, params)
        raw_results = cursor.fetchall()
        
        if not metadata_columns:
            # 메타데이터 그룹화 없는 경우 - 기존 로직 유지
            processed_results = []
            for row in raw_results:
                result_item = {
                    "model_name": row["model_name"],
                    "avg_match_score": round(float(row["avg_match_score"]), 4),
                    "total_questions": row["total_questions"],
                    "models": [row["model_name"]],  # 단일 모델
                    "benchmark": benchmark
                }
                processed_results.append(result_item)
            
            # 요약 통계 계산
            if processed_results:
                scores = [item["avg_match_score"] for item in processed_results]
                summary = {
                    "total_groups": len(processed_results),
                    "avg_score": round(sum(scores) / len(scores), 4),
                    "max_score": max(scores),
                    "min_score": min(scores),
                    "total_questions": sum(item["total_questions"] for item in processed_results)
                }
            else:
                summary = {
                    "total_groups": 0,
                    "avg_score": 0,
                    "max_score": 0,
                    "min_score": 0,
                    "total_questions": 0
                }
        else:
            # 메타데이터 그룹화가 있는 경우 - 메타데이터별로 모델들을 그룹화
            metadata_groups = {}
            
            # 메타데이터 조합별로 모델 결과들을 그룹화
            for row in raw_results:
                # 메타데이터 키 생성
                metadata_key = tuple(row[col] for col in metadata_columns)
                
                if metadata_key not in metadata_groups:
                    metadata_groups[metadata_key] = {
                        'metadata': {col: row[col] for col in metadata_columns},
                        'models': {},
                        'total_questions': 0
                    }
                
                # 각 모델의 결과 저장
                model_name = row["model_name"]
                metadata_groups[metadata_key]['models'][model_name] = {
                    'score': round(float(row["avg_match_score"]), 4),
                    'questions': row["total_questions"]
                }
                metadata_groups[metadata_key]['total_questions'] += row["total_questions"]
            
            # 최종 결과 구성
            processed_results = []
            all_scores = []
            
            for metadata_key, group_data in metadata_groups.items():
                result_item = {}
                
                # 메타데이터 정보 추가
                result_item.update(group_data['metadata'])
                
                # 모델별 점수 정보 추가
                result_item['model_scores'] = group_data['models']
                
                # 평균 점수 계산 (모든 모델의 평균)
                scores = [model_data['score'] for model_data in group_data['models'].values()]
                result_item['avg_match_score'] = round(sum(scores) / len(scores), 4)
                result_item['total_questions'] = group_data['total_questions'] // len(group_data['models'])  # 중복 제거
                
                # 참여 모델 리스트
                result_item['models'] = list(group_data['models'].keys())
                result_item['benchmark'] = benchmark
                
                processed_results.append(result_item)
                all_scores.extend(scores)
            
            # 요약 통계 계산
            if all_scores:
                summary = {
                    "total_groups": len(metadata_groups),
                    "avg_score": round(sum(all_scores) / len(all_scores), 4),
                    "max_score": max(all_scores),
                    "min_score": min(all_scores),
                    "total_questions": sum(item["total_questions"] for item in processed_results)
                }
            else:
                summary = {
                    "total_groups": 0,
                    "avg_score": 0,
                    "max_score": 0,
                    "min_score": 0,
                    "total_questions": 0
                }
        
        return {
            "benchmark": benchmark,
            "metadata_columns": metadata_columns,
            "results": processed_results,
            "summary": summary
        }
        
    finally:
        cursor.close()

        

# API 엔드포인트들
@app.get("/")
async def root():
    """API 상태 확인"""
    return {
        "message": "AI 평가 데이터 분석 API",
        "version": "1.0.0",
        "status": "running",
        "features": ["connection_pool", "multi_benchmark_support", "dynamic_metadata", "pandas_style_groupby"]
    }

@app.get("/models", response_model=List[str])
async def get_models():
    """사용 가능한 모델 리스트 반환"""
    return Config.MODELS

@app.get("/benchmarks", response_model=List[str])
async def get_benchmarks():
    """사용 가능한 벤치마크 리스트 반환"""
    return Config.BENCHMARKS

@app.get("/benchmarks/{benchmark}/metadata", response_model=MetadataInfo)
async def get_benchmark_metadata(benchmark: str):
    """특정 벤치마크의 사용 가능한 모든 메타데이터 반환"""
    if not Config.is_valid_benchmark(benchmark):
        raise HTTPException(status_code=404, detail=f"벤치마크를 찾을 수 없습니다: {benchmark}")
    
    available_metadata = Config.get_available_metadata(benchmark)
    return MetadataInfo(available_metadata=available_metadata)

@app.post("/benchmarks/{benchmark}/metadata/options", response_model=MetadataOptions)
async def get_metadata_options(benchmark: str, level1_selected: List[str]):
    """선택된 level1에 따른 level2 옵션 반환"""
    if not Config.is_valid_benchmark(benchmark):
        raise HTTPException(status_code=404, detail=f"벤치마크를 찾을 수 없습니다: {benchmark}")
    
    level2_options = Config.get_remaining_metadata(benchmark, level1_selected)
    return MetadataOptions(
        level1_selected=level1_selected,
        level2_options=level2_options
    )

@app.post("/analysis")
async def analyze_performance(request: AnalysisRequest, db_conn=Depends(get_db)):
    """다중 벤치마크 메타데이터별 성능 분석"""
    

    model_names = [model.value for model in request.models]
    results = []
    
    with db_conn as connection:
        try:
            # 각 벤치마크별로 분석 실행
            for benchmark in request.benchmarks:
                benchmark_name = benchmark.value
                metadata_columns = request.get_metadata_for_benchmark(benchmark_name)
                
                logger.info(f"[{benchmark_name}] 분석 시작 - 메타데이터: {metadata_columns}")
                
                # 개별 벤치마크 분석
                benchmark_result = execute_benchmark_analysis(
                    connection, 
                    benchmark_name, 
                    model_names, 
                    metadata_columns
                )
                
                results.append(benchmark_result)
                logger.info(f"[{benchmark_name}] 분석 완료 - {len(benchmark_result['results'])}개 결과")
            
            # 전체 요약 정보 생성
            total_summary = {
                "total_benchmarks": len(request.benchmarks),
                "benchmarks_analyzed": [r["benchmark"] for r in results],
                "total_result_groups": sum(r["summary"]["total_groups"] for r in results),
                "models_analyzed": model_names,
                "analysis_type": "multi_benchmark" if len(request.benchmarks) > 1 else "single_benchmark"
            }
            
            return {
                "summary": total_summary,
                "benchmark_results": results
            }
            
        except Exception as e:
            logger.error(f"분석 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"분석 실행 중 오류가 발생했습니다: {str(e)}")

@app.get("/analysis/summary")
async def get_analysis_summary(db_conn=Depends(get_db)):
    """전체 데이터 요약 정보"""
    with db_conn as connection:
        cursor = connection.cursor(dictionary=True)
        summary = {}
        
        try:
            for benchmark in Config.BENCHMARKS:
                table_name = Config.get_table_name(benchmark)
                
                try:
                    cursor.execute(f"""
                            SELECT
                                COUNT(*) as total_records,
                                COUNT(DISTINCT model_name) as unique_models,
                                AVG(match_score) as avg_score,
                                STDDEV(match_score) as std_score,
                                -- 분위수 계산 (MySQL 8.0+)
                                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY match_score) as q1_score,
                                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY match_score) as median_score,
                                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY match_score) as q3_score
                            FROM {table_name}
                    """)
                    
                    result = cursor.fetchone()
                    if result and result['total_records'] > 0:
                        summary[benchmark] = {
                            "total_records": result['total_records'],
                            "unique_models": result['unique_models'], 
                            "avg_score": round(float(result['avg_score']), 4),
                            "std_score": round(float(result['std_score']), 4),
                            "q1_score": round(float(result['q1_score']), 4),
                            "median_score": round(float(result['median_score']), 4),
                            "q3_score": round(float(result['q3_score']), 4),
                            "table_name": table_name,
                            "available_metadata": Config.get_available_metadata(benchmark)
                        }
                except Error as table_error:
                    logger.warning(f"테이블 {table_name} 조회 실패: {table_error}")
                    summary[benchmark] = {
                        "error": f"테이블 조회 실패: {str(table_error)}",
                        "table_name": table_name
                    }
            
            return summary
            
        finally:
            cursor.close()

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    try:
        with db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"데이터베이스 연결 테스트 실패: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "message": "서버가 정상적으로 실행 중입니다.",
        "connection_pool": "active"
    }

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    logger.info("AI 평가 API 서버 시작")
    logger.info(f"Connection Pool 설정 완료: {mysql_config.host}:{mysql_config.port}")

@app.on_event("shutdown") 
async def shutdown_event():
    """앱 종료 시 실행"""
    logger.info("AI 평가 API 서버 종료")
    db_manager.close_pool()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)