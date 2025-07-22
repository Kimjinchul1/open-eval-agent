import json
import os
import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Any
import logging
from datetime import datetime
from dotenv import load_dotenv


class JSONToMySQLMigrator:
    def __init__(self, host = 'localhost', port=3306, user = 'root', password='',database = 'ai_evaluation'):

        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'autocommit': True,
            'charset': 'utf8mb4'
        }
        self.connection = None
        self.cursor = None

        logging.basicConfig(
            level = logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers = [logging.FileHandler('migration.log'),
            logging.StreamHandler()]
        )

        self.logger = logging.getLogger(__name__)

    def connect(self):
        """MYSQL 연결"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor()
            self.logger.info("MySQL 연결 성공")
            return True
        except Error as e:
            self.logger.error(f"MysQL 연결 실패: {e}")
            return False

    def close(self):
        """연결 종료"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        self.logger.info("MySQL 연결 종료")

    def get_table_name(self, benchmark: str) -> str:
        """벤치마크명을 테이블명으로 변환"""
        table_mapping = {
            'aime': 'aime_results',
            'mmlu': 'mmlu_results',
            'mmlu-redux': 'mmlu_redux_results',
            'mmlu-pro': 'mmlu_pro_results',
            'math500': 'math500_results',
            'ds-mmlu': 'ds_mmlu_results',
            'hle': 'hle_results'
        }
        return table_mapping.get(benchmark, f"{benchmark}_results")

    def prepare_data_for_insert(self, data: Dict[str, Any], benchmark: str, model_name: str) -> tuple:
        """ 데이터를 MySQL INSERT용으로 변환"""

        base_data = {
            'data_id': data.get('id', 0),
            'model_name': model_name,
            'question': data.get('question', ''),
            'answer': str(data.get('Answer','')),
            'response': data.get('response', ''),
            'filtered_resps': str(data.get('filtered_resps', '')),
            'match_score': float(data.get('match', '0.0')),
            'difficulty': data.get('Difficulty','Medium'),
            'business_category': data.get('business', '') # 오타 유지
        }

        # 벤치마크별 특화 데이터 추가
        if benchmark == 'aime':
            specific_data = {
                'competition_year': data.get('competition_year'),
                'problem_number': data.get('problem_number'),
                'solution_steps': data.get('solution_steps')
            }
            columns = list(base_data.keys()) + list(specific_data.keys())
            values = list(base_data.values()) + list(specific_data.values())
            
        elif benchmark in ['mmlu', 'mmlu-redux']:
            specific_data = {
                'choice_a': data.get('A', ''),
                'choice_b': data.get('B', ''),
                'choice_c': data.get('C', ''),
                'choice_d': data.get('D', ''),
                'subject': data.get('subject', ''),
                'category': data.get('category', '')
            }
            
            if benchmark == 'mmlu':
                specific_data['knowledge_source'] = data.get('knowledge_source', '')
            elif benchmark == 'mmlu-redux':
                specific_data['cultural_context'] = data.get('cultural_context', '')
                
            columns = list(base_data.keys()) + list(specific_data.keys())
            values = list(base_data.values()) + list(specific_data.values())
            
        elif benchmark == 'mmlu-pro':
            specific_data = {
                'choice_a': data.get('A', ''),
                'choice_b': data.get('B', ''),
                'choice_c': data.get('C', ''),
                'choice_d': data.get('D', ''),
                'subject': data.get('subject', ''),
                'category': data.get('category', ''),
                'complexity': data.get('complexity', ''),
                'interdisciplinary': data.get('interdisciplinary', '')
            }
            columns = list(base_data.keys()) + list(specific_data.keys())
            values = list(base_data.values()) + list(specific_data.values())
            
        elif benchmark == 'math500':
            specific_data = {
                'choice_a': data.get('A'),
                'choice_b': data.get('B'),
                'choice_c': data.get('C'),
                'choice_d': data.get('D'),
                'topic': data.get('topic', ''),
                'level': data.get('level', ''),
                'proof_required': data.get('proof_required'),
                'theorem_dependency': data.get('theorem_dependency', '')
            }
            columns = list(base_data.keys()) + list(specific_data.keys())
            values = list(base_data.values()) + list(specific_data.values())
            
        elif benchmark == 'ds-mmlu':
            specific_data = {
                'choice_a': data.get('A', ''),
                'choice_b': data.get('B', ''),
                'choice_c': data.get('C', ''),
                'choice_d': data.get('D', ''),
                'subject': data.get('subject', ''),
                'category': data.get('category', 'Semiconductor Engineering'),
                'industry_relevance': data.get('industry_relevance', '')
            }
            columns = list(base_data.keys()) + list(specific_data.keys())
            values = list(base_data.values()) + list(specific_data.values())
            
        elif benchmark == 'hle':
            specific_data = {
                'choice_a': data.get('A'),
                'choice_b': data.get('B'),
                'choice_c': data.get('C'),
                'choice_d': data.get('D'),
                'choice_e': data.get('E'),
                'choice_f': data.get('F'),
                'choice_g': data.get('G'),
                'choice_h': data.get('H'),
                'choice_i': data.get('I'),
                'choice_j': data.get('J'),
                'category': data.get('category', ''),
                'complexity': data.get('complexity', 'Ultimate'),
                'philosophical_domain': data.get('philosophical_domain', ''),
                'consensus_level': data.get('consensus_level', ''),
                'complexity_breakdown': json.dumps(data.get('complexity_breakdown', {}))
            }
            columns = list(base_data.keys()) + list(specific_data.keys())
            values = list(base_data.values()) + list(specific_data.values())
            
        else:
            columns = list(base_data.keys())
            values = list(base_data.values())

        return columns, values

    def insert_data_batch(self, table_name: str, data_list: List[Dict], benchmark: str, model_name: str):
        """배치로 데이터 삽입"""
        if not data_list:
            return 0

        try:
            columns, _ = self.prepare_data_for_insert(data_list[0], benchmark, model_name)

            placeholders = ', '.join(['%s'] * len(columns))
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            values_list = []
            for data in data_list:
                _, values = self.prepare_data_for_insert(data, benchmark, model_name)
                values_list.append(values)

            self.cursor.executemany(query, values_list)
            self.connection.commit()
            self.logger.info(f"{table_name}에 {len(values_list)}개 레코드 삽입 완료")

            return len(values_list)

        except Error as e:
            self.logger.error(f"데이터 삽입 실패 ({table_name}): {e}")
            self.connection.rollback()
            return 0     


    def migrate_single_file(self, file_path: str, model_name: str, benchmark_name: str) -> int:
        """단일 JSON 파일 이관"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)

            if not isinstance(data_list, list):
                self.logger.error(f"잘못된 JSON 형식: {file_path}")
                return 0
            
            table_name = self.get_table_name(benchmark_name)
            return self.insert_data_batch(table_name, data_list, benchmark_name, model_name)

        except Exception as e:
            self.logger.error(f"파일 처리 실패 ({file_path}): {e}")
            return 0

    def migrate_all_files(self, base_directory: str = './our_results'):
        """모든 JSON 파일 이관"""
        if not os.path.exists(base_directory):
            self.logger.error(f"디렉토리를 찾을 수 없습니다: {base_directory}")
            return

        total_records = 0
        processed_files = 0

        for model_dir in os.listdir(base_directory):
            model_path = os.path.join(base_directory, model_dir)

            if not os.path.isdir(model_path):
                continue

            self.logger.info(f"모델 처리 시작: {model_path}")

            for file_name in os.listdir(model_path):
                if not file_name.endswith('.json'):
                    continue

                benchmark = file_name.replace('.json', '')
                file_path = os.path.join(model_path, file_name)
                self.logger.info(f"파일 처리: {model_dir}/{file_name}")

                # if benchmark == "mmlu-redux":
                records_inserted = self.migrate_single_file(file_path, model_dir, benchmark)
                total_records += records_inserted
                processed_files += 1

        #         self.logger.info(f"완료: {records_inserted}개 레코드 삽입")

        # self.logger.info(f"이관 완료! 총 {processed_files}개 파일, {total_records}개 레코드 처리")


    def verify_migration(self):
        """이관 결과 검증"""

        try:
            self.cursor.execute("SELECT * FROM model_performance_summary")
            results = self.cursor.fetchall()
            self.logger.info("=== 이관 결과 요약 ===")

            for row in results:
                model_name, benchmark, total_questions, avg_score, correct_answers = row
                self.logger.info(f"{model_name} - {benchmark}: {total_questions}문제, 평균점수: {avg_score:.3f}")
        except Error as e:
            self.logger.error(f"검증 실패: {e}")


def main():
    # MySQL 연결 정보 (실제 값으로 변경하세요)
    config = {"host":'localhost',
        "port":3306,
        "user":input("MySQL 아이디: "),
        "password":input("MySQL 비밀번호: "),
        "database":'ai_evaluation'
    }
    migrator = JSONToMySQLMigrator(**config)

    if not migrator.connect():
        print("MySQL 연결 실패!")
        return

    try:
        # 데이터 이관
        print("JSON 파일 이관을 시작합니다...")
        migrator.migrate_all_files('/home/kimhc/open_deep_research/database/our_results')

        print("\n이관 결과를 검증합니다...")
        migrator.verify_migration()

    finally:
        # 연결 종료
        migrator.close()


if __name__ == "__main__":
    main()