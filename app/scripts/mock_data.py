import asyncio
import random
import time
from faker import Faker
from neo4j import AsyncGraphDatabase
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

print("--- KIỂM TRA BIẾN MÔI TRƯỜNG ---")
print(f"URI: {URI}")
print(f"USERNAME: {USERNAME}")
print(f"PASSWORD: {'Đã tải thành công (Bảo mật)' if PASSWORD else ' BỊ TRỐNG (LỖI)'}")
print("--------------------------------")

fake = Faker("vi_VN")

NUM_ROOT_POSTS = 5      
NUM_SHARES = 5000       
BATCH_SIZE = 500        

VIETNAMESE_FAKE_NEWS = [
    "SỐC: Độ Mixi dính tin đồn hút thuốc lá điện tử trong bar cùng cựu trung vệ Barcelona - Pique #tinđồn",
    "Phát hiện sinh vật lạ ngoài hành tinh rơi xuống Cao Bằng!!! #ufo",
    "Cảnh báo: Ăn tỏi nướng với sầu riêng sẽ gây ngộ độc ngay lập tức #sứckhỏe",
    "Tin mật: Trái Đất sẽ ngừng quay trong 3 ngày tới, hãy tích trữ lương thực! #tậnthế",
    "Cổ phiếu công ty MixiGaming sắp tăng gấp 10 lần nhờ được tỷ phú Elon Musk mua lại #chứngkhoán"
]

VIETNAMESE_SHARE_COMMENTS = [

    "Mọi người cẩn thận nhé, sợ quá đi mất",
    "Tin chuẩn không anh em? Mình thấy ai cũng share.",
    "Share gấp để gia đình và người thân cùng biết!!!",
    "Không biết thật giả thế nào nhưng cứ share cho an toàn.",
    "Ôi trời ơi, giờ mới biết vụ này luôn đó.",

    "Nghe mà rùng mình luôn, không biết có thật không nữa",
    "Sợ quá nên share trước cho chắc ăn",
    "Ai xác nhận giúp với, thấy lo quá",
    "Đọc xong thấy bất an thật sự",
    "Hy vọng là tin giả chứ không thì toang",

    "Thấy mọi người share nhiều quá nên mình share theo",
    "Không share thấy thiếu thiếu ",
    "Ai cũng đăng nên mình đăng lại",
    "Hot quá nên phải share ngay",
    "Trend này đang nổi ghê",

    "Nghe hơi vô lý nhưng thôi cứ share",
    "Không biết nguồn ở đâu ra luôn",
    "Tin này check ở đâu vậy mọi người?",
    "Có ai verify chưa?",
    "Ai rành vụ này giải thích với",

    "Tag người thân vào đọc ngay!",
    "Mọi người trong gia đình chú ý nhé",
    "Gửi cho bố mẹ đọc gấp",
    "Ai có người quen thì báo ngay",
    "Nhớ nhắc người nhà cẩn thận",

    "Ủa thật luôn hả trời???",
    "Drama căng vậy luôn á",
    "Nghe sốc quá luôn",
    "Không tin nổi luôn á",
    "Có biến lớn rồi",

    "Ai chơi chứng khoán coi ngay",
    "Kèo này có thơm không anh em?",
    "Tin này mà thật thì đổi đời",
    "Nghe mùi úp bô đâu đây 🤡",
    "Cẩn thận bị lùa gà nhé",

    "Tin này mà cũng có người tin à 😂",
    "Fake rõ mà vẫn share",
    "Internet giờ cái gì cũng có thể xảy ra",
    "Đọc giải trí thôi chứ không tin lắm",
    "Lại thêm một ngày internet dậy sóng",

    "Share!!!",
    "Nóng!!!",
    "Xem ngay!!!",
    "Cẩn thận!!!",
    "Đọc đi!!!"
]
async def generate_mock_data():
    driver = AsyncGraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    print(" BẮT ĐẦU QUÁ TRÌNH BƠM DỮ LIỆU VÀO NEO4J AURA...")
    start_time = time.time()

    async with driver.session() as session:

        print(" Đang dọn dẹp dữ liệu cũ...")
        await session.run("MATCH (n) DETACH DELETE n")


        print(f" Đang tạo {NUM_ROOT_POSTS} nguồn tin giả gốc (Patient Zero)...")
        root_posts_data = []
        available_post_ids = [] 

        for _ in range(NUM_ROOT_POSTS):
            account_id = f"acc_{fake.uuid4()[:8]}"
            post_id = f"post_{fake.uuid4()[:8]}"
            
            root_posts_data.append({
                "account_id": account_id,
                "username": fake.user_name(),
                "post_id": post_id,
                "content": random.choice(VIETNAMESE_FAKE_NEWS),
                "timestamp": int(time.time()) - random.randint(100000, 500000) 
            })
            available_post_ids.append(post_id)


        root_query = """
        UNWIND $batch AS data
        CREATE (a:Account {account_id: data.account_id, username: data.username})
        CREATE (p:Post {post_id: data.post_id, content: data.content, timestamp: data.timestamp, is_misinfo: true})
        CREATE (a)-[:AUTHORED]->(p)
        """
        await session.run(root_query, batch=root_posts_data)

        print(f" Đang mô phỏng {NUM_SHARES} lượt chia sẻ tạo mạng lưới...")
        
        share_batch = []
        for i in range(NUM_SHARES):

            parent_id = random.choice(available_post_ids)
            
            new_account_id = f"acc_{fake.uuid4()[:8]}"
            new_post_id = f"post_{fake.uuid4()[:8]}"
            
            share_batch.append({
                "account_id": new_account_id,
                "username": fake.user_name(),
                "new_post_id": new_post_id,
                "parent_id": parent_id,
                "content": random.choice(VIETNAMESE_SHARE_COMMENTS), 
                "timestamp": int(time.time()) - random.randint(0, 50000)
            })
            

            available_post_ids.append(new_post_id)


            if len(share_batch) >= BATCH_SIZE:
                share_query = """
                UNWIND $batch AS share
                MATCH (parent:Post {post_id: share.parent_id})
                CREATE (a:Account {account_id: share.account_id, username: share.username})
                CREATE (p:Post {post_id: share.new_post_id, content: share.content, timestamp: share.timestamp})
                CREATE (a)-[:AUTHORED]->(p)
                CREATE (p)-[:SHARED_FROM]->(parent)
                WITH p, a, parent, share, ['#fakenews', '#ufo', '#suckhoe', '#tinhot'] AS tagList
                WITH p, a, parent, share, tagList[toInteger(rand() * 4)] AS randomTag
                MERGE (h:Hashtag {name: randomTag})
                CREATE (p)-[:USED_HASHTAG]->(h)
                WITH p, a, parent, share, ['tinnham.vn', 'giatgan.com', 'vuighe.net'] AS domainList
                WITH p, a, parent, share, domainList[toInteger(rand() * 3)] AS randomDomain
                MERGE (d:Domain {url: randomDomain})
                CREATE (p)-[:CITED_FROM]->(d)
                CREATE (c:Comment {comment_id: 'cmt_' + share.new_post_id, content: "Chấm hóng!", timestamp: share.timestamp + 100})
                CREATE (a)-[:COMMENTED]->(c)
                CREATE (c)-[:REPLIED_TO]->(parent)
                """
                await session.run(share_query, batch=share_batch)
                share_batch = []
                print(f"Đã insert {i+1}/{NUM_SHARES} lượt share...")

        if share_batch:
             await session.run(share_query, batch=share_batch)

    await driver.close()
    
    elapsed = time.time() - start_time
    print(f"HOÀN TẤT! Đã tạo mạng lưới trong {elapsed:.2f} giây.")

if __name__ == "__main__":
    asyncio.run(generate_mock_data())