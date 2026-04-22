from pydantic import BaseModel, Field, field_validator
import re
from typing import Optional
from typing import List, Dict, Any

class AccountCreate(BaseModel):
    account_id: str = Field(..., description="Mã định danh duy nhất của tài khoản")
    username: str = Field(..., description="Tên hiển thị của người dùng")

    @field_validator('account_id', 'username')
    @classmethod
    def strict_clean_strings(cls, value: str) -> str:
        """Bộ lọc tiêu diệt chuỗi rỗng và giá trị NULL ẩn"""
        cleaned = value.strip()
        
        # Bắt các trường hợp string nhưng chứa chữ "NULL", "N/A" (Lỗi kinh điển khi crawl data)
        if not cleaned or cleaned.upper() in ["NULL", "N/A", "NONE", "NAN"]:
            raise ValueError(f"Lỗi: Dữ liệu bị rỗng hoặc chứa giá trị rác ({value})")
        
        return cleaned


class PostCreate(BaseModel):
    post_id: str
    content: str
    is_misinfo: bool = False
    timestamp: int = Field(..., gt=0, description="Unix timestamp phải lớn hơn 0")

    @field_validator('content')
    @classmethod
    def advanced_clean_content(cls, value: str) -> str:
        """Bộ lọc bóc tách ký tự nhiễu đúng chuẩn Rubric Tiêu chí 3"""
        cleaned = value.strip()
        

        cleaned = re.sub(r'\bV\b', '', cleaned)
        

        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if not cleaned:
            raise ValueError("Nội dung bài viết không được để trống sau khi đã lọc rác")
            
        return cleaned

class ShareAction(BaseModel):
    account_id: str
    source_post_id: str
    new_post_id: str
    content: Optional[str] = "" 
    timestamp: int

class GraphNode(BaseModel):
    id: str
    label: str
    group: str  
    title: Optional[str] = None 

class GraphEdge(BaseModel):
    from_: str = Field(alias="from") 
    to: str
    label: str

class NetworkResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = {}