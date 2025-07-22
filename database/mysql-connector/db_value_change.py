import mysql.connector
from mysql.connector import Error
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelNameUpdater:
    def __init__(self, host, database, username, password, port=3306):
        self.connection_config = {
            'host': host,
            'database': database,
            'user': username,
            'password': password,
            'port': port
        }
        self.connection = None
        
    def connect(self):
        """MySQL 데이터베이스에 연결"""
        try:
            self.connection = mysql.connector.connect(**self.connection_config)
            if self.connection.is_connected():
                logger.info(f"MySQL 데이터베이스 '{self.connection_config['database']}'에 성공적으로 연결되었습니다.")
                return True
        except Error as e:
            logger.error(f"데이터베이스 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """MySQL 연결 종료"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL 연결이 종료되었습니다.")
    
    def get_tables_with_model_name(self):
        """model_name 컬럼이 있는 테이블들을 찾기"""
        try:
            cursor = self.connection.cursor()
            query = """
            SELECT DISTINCT TABLE_NAME
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
              AND COLUMN_NAME = 'model_name'
            """
            cursor.execute(query, (self.connection_config['database'],))
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            logger.info(f"model_name 컬럼이 있는 테이블: {tables}")
            return tables
        except Error as e:
            logger.error(f"테이블 조회 오류: {e}")
            return []
    
    def check_data_before_update(self, table_name):
        """업데이트 전 데이터 확인"""
        try:
            cursor = self.connection.cursor()
            query = f"""
            SELECT model_name, COUNT(*) as count
            FROM `{table_name}`
            WHERE model_name IN ('KIMI K2', 'KIMI K2-AWQ')
            GROUP BY model_name
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            if results:
                logger.info(f"테이블 '{table_name}'에서 변경될 데이터:")
                for model_name, count in results:
                    logger.info(f"  - '{model_name}': {count}개 행")
                return True
            else:
                logger.info(f"테이블 '{table_name}'에 변경할 데이터가 없습니다.")
                return False
                
        except Error as e:
            logger.error(f"테이블 '{table_name}' 데이터 확인 오류: {e}")
            return False
    
    def update_model_names_in_table(self, table_name):
        """특정 테이블의 model_name 값들을 업데이트"""
        try:
            cursor = self.connection.cursor()
            
            # 업데이트 쿼리 실행
            update_query = f"""
            UPDATE `{table_name}` 
            SET model_name = CASE 
                WHEN model_name = 'KIMI K2' THEN 'KIMI-K2'
                WHEN model_name = 'KIMI K2-AWQ' THEN 'KIMI-K2-AWQ'
                ELSE model_name 
            END 
            WHERE model_name IN ('KIMI K2', 'KIMI K2-AWQ')
            """
            
            cursor.execute(update_query)
            affected_rows = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            logger.info(f"테이블 '{table_name}': {affected_rows}개 행이 업데이트되었습니다.")
            return affected_rows
            
        except Error as e:
            logger.error(f"테이블 '{table_name}' 업데이트 오류: {e}")
            self.connection.rollback()
            return 0
    
    def verify_update(self, table_name):
        """업데이트 후 결과 확인"""
        try:
            cursor = self.connection.cursor()
            query = f"""
            SELECT model_name, COUNT(*) as count
            FROM `{table_name}`
            WHERE model_name LIKE 'KIMI%'
            GROUP BY model_name
            ORDER BY model_name
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            if results:
                logger.info(f"테이블 '{table_name}' 업데이트 후 상태:")
                for model_name, count in results:
                    logger.info(f"  - '{model_name}': {count}개 행")
            else:
                logger.info(f"테이블 '{table_name}'에 KIMI 관련 데이터가 없습니다.")
                
        except Error as e:
            logger.error(f"테이블 '{table_name}' 검증 오류: {e}")
    
    def run_update(self, dry_run=True):
        """전체 업데이트 프로세스 실행"""
        if not self.connect():
            return False
        
        try:
            # model_name 컬럼이 있는 테이블들 찾기
            tables = self.get_tables_with_model_name()
            
            if not tables:
                logger.warning("model_name 컬럼이 있는 테이블을 찾을 수 없습니다.")
                return False
            
            total_affected = 0
            
            for table in tables:
                logger.info(f"\n{'='*50}")
                logger.info(f"테이블 '{table}' 처리 중...")
                
                # 업데이트 전 데이터 확인
                has_data = self.check_data_before_update(table)
                
                if has_data:
                    if dry_run:
                        logger.info(f"DRY RUN: 테이블 '{table}'을 업데이트할 예정입니다.")
                    else:
                        # 실제 업데이트 실행
                        affected = self.update_model_names_in_table(table)
                        total_affected += affected
                        
                        # 업데이트 후 검증
                        self.verify_update(table)
            
            if dry_run:
                logger.info(f"\n{'='*50}")
                logger.info("DRY RUN 완료! 실제 업데이트를 하려면 dry_run=False로 설정하세요.")
            else:
                logger.info(f"\n{'='*50}")
                logger.info(f"전체 업데이트 완료! 총 {total_affected}개 행이 변경되었습니다.")
            
            return True
            
        except Exception as e:
            logger.error(f"업데이트 프로세스 오류: {e}")
            return False
        finally:
            self.disconnect()


def main():
    # 데이터베이스 연결 정보 설정
    DB_CONFIG = {
        'host': 'localhost',  # 또는 실제 호스트 주소
        'database': 'ai_evaluation',
        'username': 'kimhc30918',  # 실제 사용자명으로 변경
        'password': 'wlscjfdl9!',  # 실제 비밀번호로 변경
        'port': 3306
    }
    
    # ModelNameUpdater 인스턴스 생성
    updater = ModelNameUpdater(
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        username=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port']
    )
    
    print("MySQL Model Name Updater")
    print("=" * 50)
    print("이 스크립트는 다음 변경을 수행합니다:")
    print("- 'KIMI K2' -> 'KIMI-K2'")
    print("- 'KIMI K2-AWQ' -> 'KIMI-K2-AWQ'")
    print("=" * 50)
    
    # 먼저 DRY RUN으로 실행 (실제 변경하지 않고 확인만)
    print("\n1단계: DRY RUN (실제 변경하지 않고 확인만)")
    success = updater.run_update(dry_run=True)
    
    if success:
        # 사용자 확인 후 실제 실행
        response = input("\n실제 업데이트를 진행하시겠습니까? (yes/no): ").lower().strip()
        
        if response in ['yes', 'y']:
            print("\n2단계: 실제 업데이트 실행")
            updater.run_update(dry_run=False)
        else:
            print("업데이트가 취소되었습니다.")
    else:
        print("DRY RUN에서 오류가 발생했습니다. 연결 정보를 확인하세요.")


if __name__ == "__main__":
    main()
