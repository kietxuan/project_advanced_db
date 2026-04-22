import logging
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from app.core.config import settings

# Cấu hình logging cơ bản để dễ debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self):
        self.uri = settings.NEO4J_URI
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        self.driver = None

    async def connect(self):
        """Khởi tạo connection pool tới Neo4j Aura"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Ping thử DB để xác nhận kết nối
            await self.driver.verify_connectivity()
            logger.info(" KẾT NỐI NEO4J AURA THÀNH CÔNG!")
            
        except AuthError:
            logger.error(" LỖI XÁC THỰC: Sai Username hoặc Password. Hãy kiểm tra file .env!")
        except ServiceUnavailable:
            logger.error(" LỖI MẠNG HOẶC AURA ĐANG TẠM DỪNG: Hãy lên trang chủ Neo4j Aura để 'Resume' database.")
        except Exception as e:
            logger.error(f" LỖI KHÔNG XÁC ĐỊNH: {e}")

    async def close(self):
        """Đóng connection pool an toàn khi tắt server"""
        if self.driver:
            await self.driver.close()
            logger.info(" ĐÃ ĐÓNG KẾT NỐI NEO4J AN TOÀN.")

# Khởi tạo một instance duy nhất (Singleton)
db = Neo4jConnection()