from pydantic import BaseModel
from typing import Literal, Optional

class UserRequest(BaseModel):
    action: Literal[
        'create', 'delete', 'password',
        'add_group', 'del_group',
        'list_groups', 'list_users','create_group'
    ]
    username: Optional[str] = None
    password: Optional[str] = None
    group:    Optional[str] = None