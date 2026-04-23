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
            logger.info("[OK] NEO4J AURA CONNECTED SUCCESSFULLY!")
            
        except AuthError:
            logger.error("[AUTH ERROR] Wrong Username or Password. Check your .env file!")
        except ServiceUnavailable:
            logger.error("[NETWORK ERROR] Aura may be paused. Go to Neo4j Aura console to 'Resume' database.")
        except Exception as e:
            logger.error(f"[UNKNOWN ERROR] {e}")

    async def close(self):
        """Đóng connection pool an toàn khi tắt server"""
        if self.driver:
            await self.driver.close()
            logger.info("[OK] NEO4J CONNECTION CLOSED SAFELY.")

# Khởi tạo một instance duy nhất (Singleton)
db = Neo4jConnection()