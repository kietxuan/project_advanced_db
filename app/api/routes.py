import time
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
from app.core.database import db
from app.models.schemas import NetworkResponse

router = APIRouter(prefix="/api/network", tags=["Graph Network"])

@router.get("/longest-chain", response_model=NetworkResponse)
async def get_longest_chain():
    if not db.driver:
        raise HTTPException(status_code=503, detail="Database connection missing")

    query = """
    MATCH path = (leaf:Post)-[r:SHARED_FROM*]->(root:Post)
    WHERE NOT EXISTS { ()-[:SHARED_FROM]->(leaf) }
      AND NOT EXISTS { (root)-[:SHARED_FROM]->() }
    RETURN path, length(path) AS depth
    ORDER BY depth DESC
    LIMIT 1
    """
    
    start_time = time.time()
    async with db.driver.session() as session:
        result = await session.run(query)
        record = await result.single()

        if not record:
             return NetworkResponse(nodes=[], edges=[], metadata={"message": "No data found"})

        path = record["path"]
        depth = record["depth"]

        nodes_dict = {}
        edges_list = []

        for node in path.nodes:
            node_id = node["post_id"]
            if node_id not in nodes_dict:
                nodes_dict[node_id] = {
                    "id": node_id,
                    "label": f"Post\n{node_id[-4:]}",
                    "group": "Post",
                    "title": node.get("content", "")
                }

        for rel in path.relationships:
            edges_list.append({
                "from": rel.start_node["post_id"],
                "to": rel.end_node["post_id"],
                "label": "SHARED_FROM"
            })

        execution_time = round((time.time() - start_time) * 1000, 2)

        return NetworkResponse(
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            metadata={"depth": depth, "execution_time_ms": execution_time}
        )

@router.get("/trace", response_model=NetworkResponse)
async def trace_custom_network(
    root_post_id: str = Query(None),
    depth_limit: int = Query(5, ge=1, le=10)
):
    if not db.driver:
        raise HTTPException(status_code=503, detail="Database connection missing")

    start_time = time.time()
    
    if root_post_id:
        query = f"""
        MATCH path = (leaf:Post)-[:SHARED_FROM*1..{depth_limit}]->(root:Post {{post_id: $post_id}})
        RETURN path, length(path) AS depth
        """
        params = {"post_id": root_post_id}
    else:
        query = f"""
        MATCH path = (leaf:Post)-[:SHARED_FROM*1..{depth_limit}]->(root:Post)
        WHERE NOT EXISTS {{ ()-[:SHARED_FROM]->(leaf) }}
          AND NOT EXISTS {{ (root)-[:SHARED_FROM]->() }}
        RETURN path, length(path) AS depth
        ORDER BY depth DESC LIMIT 1
        """
        params = {} 

    async with db.driver.session() as session:
        result = await session.run(query, params)
        
        # FIX: fetch_all() is not supported in neo4j driver, use async loop instead
        records = [record async for record in result]

        if not records:
             return NetworkResponse(nodes=[], edges=[], metadata={"message": "No data found"})

        nodes_dict = {}
        edges_list = []
        max_depth = 0

        for record in records:
            path = record["path"]
            if record["depth"] > max_depth:
                max_depth = record["depth"]
                
            for node in path.nodes:
                node_id = node["post_id"]
                if node_id not in nodes_dict:
                    is_root = (node_id == root_post_id) if root_post_id else False
                    
                    nodes_dict[node_id] = {
                        "id": node_id,
                        "label": f"Post\n{node_id[-4:]}",
                        "group": "Root" if is_root else "Post", 
                        "title": node.get("content", "")
                    }

            for rel in path.relationships:
                edges_list.append({
                    "from": rel.start_node["post_id"],
                    "to": rel.end_node["post_id"],
                    "label": "SHARED_FROM"
                })

        execution_time = round((time.time() - start_time) * 1000, 2)

        return NetworkResponse(
            nodes=list(nodes_dict.values()),
            edges=edges_list,
            metadata={"depth_rendered": max_depth, "execution_time_ms": execution_time}
        )

@router.get("/search", response_model=NetworkResponse)
async def search_posts(keyword: str = Query(..., description="Keyword to search")):
    if not db.driver:
        raise HTTPException(status_code=503, detail="Database connection missing")

    start_time = time.time()
    
    # Use Fulltext Index instead of standard MATCH for extreme performance
    query = """
    CALL db.index.fulltext.queryNodes("post_content_index", $keyword) 
    YIELD node, score
    RETURN node.post_id AS post_id, node.content AS content, score
    ORDER BY score DESC LIMIT 10
    """
    
    async with db.driver.session() as session:
        result = await session.run(query, {"keyword": keyword})
        
        # FIX: Async list comprehension for extracting records
        records = [record async for record in result]

        nodes_dict = {}
        for rec in records:
            node_id = rec["post_id"]
            nodes_dict[node_id] = {
                "id": node_id,
                "label": f"Post\n{node_id[-4:]}",
                "group": "Highlight", 
                "title": f"Score: {rec['score']:.2f}\nContent: {rec['content']}"
            }

        execution_time = round((time.time() - start_time) * 1000, 2)

        return NetworkResponse(
            nodes=list(nodes_dict.values()),
            edges=[], 
            metadata={"execution_time_ms": execution_time, "keyword": keyword}
        )

@router.get("/top-spreaders")
async def get_top_spreaders():
    query = """
    MATCH (author:Account)-[:AUTHORED]->(root:Post)
    WHERE NOT EXISTS { (root)-[:SHARED_FROM]->() }
    MATCH path = (leaf:Post)-[:SHARED_FROM*]->(root)
    RETURN author.username AS account, root.post_id AS post_id, 
           count(leaf) AS total_infected
    ORDER BY total_infected DESC LIMIT 5
    """
    async with db.driver.session() as session:
        result = await session.run(query)
        data = [{"account": rec["account"], "post_id": rec["post_id"], "infected_nodes": rec["total_infected"]} async for rec in result]
        return {"status": "success", "data": data}

@router.get("/toxicity-ranking")
async def get_toxicity_ranking():
    query = """
    MATCH (a:Account)-[:AUTHORED]->(p:Post)
    OPTIONAL MATCH (p)-[:SHARED_FROM*]->(root:Post)
    WHERE NOT EXISTS { (root)-[:SHARED_FROM]->() }
    WITH a, count(p) AS Total_Posts, count(root) AS Shares_From_Roots
    RETURN a.username AS username, 
           (Total_Posts * 1.0 + Shares_From_Roots * 5.0) AS toxicity_score
    ORDER BY toxicity_score DESC LIMIT 5
    """
    async with db.driver.session() as session:
        result = await session.run(query)
        data = [{"username": rec["username"], "score": rec["toxicity_score"]} async for rec in result]
        return {"status": "success", "data": data}


@router.get("/top-hashtags")
async def get_top_hashtags():
    """Lấy Top 5 Hashtag được sử dụng nhiều nhất"""
    query = """
    MATCH (p:Post)-[:USED_HASHTAG]->(h:Hashtag)
    RETURN h.name AS hashtag, count(p) AS usage_count
    ORDER BY usage_count DESC LIMIT 5
    """
    async with db.driver.session() as session:
        result = await session.run(query)
        data = [{"hashtag": rec["hashtag"], "count": rec["usage_count"]} async for rec in result]
        return {"status": "success", "data": data}

@router.get("/top-domains")
async def get_top_domains():
    """Lấy Top 3 Domain (Ổ dịch) phát tán tin giả"""
    query = """
    MATCH (p:Post)-[:CITED_FROM]->(d:Domain)
    RETURN d.url AS domain, count(p) AS reference_count
    ORDER BY reference_count DESC LIMIT 3
    """
    async with db.driver.session() as session:
        result = await session.run(query)
        data = [{"domain": rec["domain"], "count": rec["reference_count"]} async for rec in result]
        return {"status": "success", "data": data}

