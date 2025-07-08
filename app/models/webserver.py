from pydantic import BaseModel
from typing import Literal, Optional

class WebsiteRequest(BaseModel):
    action: Literal[
        'create', 'delete', 'enable', 'disable' 
    ]
    server_name: str
    root_dir: Optional[str] = None 
    port: int = 80