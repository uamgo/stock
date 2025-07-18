"""
用户管理模块
"""
import json
import os
from typing import Dict, List, Optional
from passlib.context import CryptContext
from pydantic import BaseModel

class User(BaseModel):
    username: str
    hashed_password: str
    nickname: Optional[str] = None
    is_active: bool = True
    created_at: str
    last_login: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    password: Optional[str] = None
    nickname: Optional[str] = None
    is_active: Optional[bool] = None

class UserManager:
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = users_file
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self._ensure_users_file()
        self._init_default_user()
    
    def _ensure_users_file(self):
        """确保用户文件存在"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def _init_default_user(self):
        """初始化默认用户"""
        users = self._load_users()
        if not users:
            default_user = User(
                username="admin",
                hashed_password=self.get_password_hash("admin000"),
                created_at="2025-07-18T00:00:00"
            )
            users["admin"] = default_user.dict()
            self._save_users(users)
    
    def _load_users(self) -> Dict:
        """加载用户数据"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_users(self, users: Dict):
        """保存用户数据"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return self.pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        users = self._load_users()
        user_data = users.get(username)
        if not user_data:
            return None
        
        user = User(**user_data)
        if not user.is_active:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_user(self, user_create: UserCreate) -> bool:
        """创建用户"""
        users = self._load_users()
        if user_create.username in users:
            return False
        
        from datetime import datetime
        new_user = User(
            username=user_create.username,
            hashed_password=self.get_password_hash(user_create.password),
            created_at=datetime.now().isoformat()
        )
        users[user_create.username] = new_user.dict()
        self._save_users(users)
        return True
    
    def update_user(self, username: str, user_update: UserUpdate) -> bool:
        """更新用户"""
        users = self._load_users()
        if username not in users:
            return False
        
        user_data = users[username]
        if user_update.password:
            user_data["hashed_password"] = self.get_password_hash(user_update.password)
        if user_update.nickname is not None:
            user_data["nickname"] = user_update.nickname
        if user_update.is_active is not None:
            user_data["is_active"] = user_update.is_active
        
        users[username] = user_data
        self._save_users(users)
        return True
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        users = self._load_users()
        if username not in users or username == "admin":  # 不允许删除admin用户
            return False
        
        del users[username]
        self._save_users(users)
        return True
    
    def get_all_users(self) -> List[Dict]:
        """获取所有用户"""
        users = self._load_users()
        result = []
        for username, user_data in users.items():
            user_info = {
                "username": username,
                "is_active": user_data.get("is_active", True),
                "created_at": user_data.get("created_at", ""),
                "last_login": user_data.get("last_login", "")
            }
            result.append(user_info)
        return result
    
    def update_last_login(self, username: str):
        """更新最后登录时间"""
        users = self._load_users()
        if username in users:
            from datetime import datetime
            users[username]["last_login"] = datetime.now().isoformat()
            self._save_users(users)
