"""
主API应用
"""
import sys
import os

# 动态获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import subprocess
from datetime import datetime, timedelta
import asyncio
import json
import shutil
import glob
import pandas as pd

from .auth import UserManager, UserCreate, UserUpdate
from .jwt_auth import jwt_manager
from .scheduler import task_scheduler

def get_date_output_dir():
    """获取以当天日期命名的输出目录"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = f"/tmp/{today}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_stock_results_file():
    """获取当天的选股结果文件路径"""
    output_dir = get_date_output_dir()
    return os.path.join(output_dir, "selected_stocks.txt")

def get_strategy_results_file(strategy):
    """获取特定策略的选股结果文件路径"""
    output_dir = get_date_output_dir()
    strategy_files = {
        'smart': 'smart_selected_stocks.json',
        'enhanced': 'enhanced_selected_stocks.json',
        'select': 'traditional_selected_stocks.json'
    }
    filename = strategy_files.get(strategy, f'{strategy}_selected_stocks.json')
    return os.path.join(output_dir, filename)

def save_strategy_results(strategy, stocks_data):
    """保存特定策略的选股结果"""
    try:
        file_path = get_strategy_results_file(strategy)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stocks_data, f, ensure_ascii=False, indent=2)
        print(f"已保存{strategy}策略结果到: {file_path}")
        return True
    except Exception as e:
        print(f"保存{strategy}策略结果失败: {e}")
        return False

def load_strategy_results(strategy):
    """加载特定策略的选股结果"""
    file_path = get_strategy_results_file(strategy)
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载{strategy}策略结果失败: {e}")
        return []

def load_existing_stocks():
    """加载已存在的选股结果"""
    stock_file = get_stock_results_file()
    if not os.path.exists(stock_file):
        return []
    
    try:
        with open(stock_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            
            # 尝试解析JSON格式
            if content.startswith('['):
                return json.loads(content)
            else:
                # 兼容其他格式，按行分割
                lines = content.split('\n')
                stocks = []
                for line in lines:
                    if line.strip():
                        # 假设格式为 "代码 名称" 或只有代码
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            stocks.append({"code": parts[0], "name": " ".join(parts[1:])})
                        elif len(parts) == 1:
                            stocks.append({"code": parts[0], "name": ""})
                return stocks
    except Exception as e:
        print(f"加载选股结果失败: {e}")
        return []

app = FastAPI(title="Tail Trading API", version="1.0.0")

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全配置
security = HTTPBearer()
user_manager = UserManager()

# Pydantic模型
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    nickname: Optional[str] = None

class UpdateDataRequest(BaseModel):
    top_n: int = 10

class SelectStocksRequest(BaseModel):
    preset: str = "balanced"
    limit: int = 20
    verbose: bool = False

class SchedulerConfigRequest(BaseModel):
    enabled: bool
    cron_expression: Optional[str] = None

# 依赖函数
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    token = credentials.credentials
    username = jwt_manager.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username

# 认证相关API
@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    user = user_manager.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = jwt_manager.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 更新最后登录时间
    user_manager.update_last_login(user.username)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        nickname=getattr(user, 'nickname', None)
    )

@app.get("/api/auth/me")
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    """获取当前用户信息"""
    return {"username": current_user}

# 用户管理API
@app.get("/api/users")
async def get_users(current_user: str = Depends(get_current_user)):
    """获取所有用户"""
    return user_manager.get_all_users()

@app.post("/api/users")
async def create_user(user_create: UserCreate, current_user: str = Depends(get_current_user)):
    """创建用户"""
    if not user_manager.create_user(user_create):
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User created successfully"}

@app.put("/api/users/{username}")
async def update_user(username: str, user_update: UserUpdate, current_user: str = Depends(get_current_user)):
    """更新用户"""
    if not user_manager.update_user(username, user_update):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}

@app.delete("/api/users/{username}")
async def delete_user(username: str, current_user: str = Depends(get_current_user)):
    """删除用户"""
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    if not user_manager.delete_user(username):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# 股票数据API
@app.post("/api/stock/update")
async def update_stock_data(request: UpdateDataRequest, current_user: str = Depends(get_current_user)):
    """更新股票数据"""
    try:
        cmd = [os.path.join(project_root, ".venv", "bin", "python3"), "tail_trading.py", "update", "--top", str(request.top_n)]
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        if result.returncode == 0:
            # 确保返回JSON格式
            return {
                "success": True,
                "message": "数据更新成功",
                "output": result.stdout.strip() if result.stdout else "",
                "error": result.stderr.strip() if result.stderr else ""
            }
        else:
            return {
                "success": False,
                "message": "数据更新失败",
                "error": result.stderr.strip() if result.stderr else "未知错误",
                "output": result.stdout.strip() if result.stdout else ""
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "数据更新超时（超过10分钟）",
            "error": "进程执行时间过长，已终止"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"数据更新异常: {str(e)}",
            "error": str(e)
        }

async def stream_update_logs(cmd: List[str], cwd: str):
    """流式输出更新日志"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        start_time = datetime.now()
        start_msg = f"📋 开始执行数据更新任务..."
        yield f"data: {json.dumps({'type': 'start', 'message': start_msg, 'timestamp': start_time.isoformat()})}\n\n"
        
        # 发送初始状态信息
        cmd_str = " ".join(cmd)
        yield f"data: {json.dumps({'type': 'log', 'message': f'🔧 执行命令: {cmd_str}', 'timestamp': datetime.now().isoformat()})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'📂 工作目录: {cwd}', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        line_count = 0
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            line = line.decode('utf-8').strip()
            if line:
                line_count += 1
                timestamp = datetime.now()
                # 过滤和格式化日志信息
                if '进度:' in line:
                    # 进度信息特殊处理
                    formatted_line = f"⏳ {line}"
                elif '错误' in line or 'Error' in line or 'error' in line:
                    formatted_line = f"❌ {line}"
                elif '成功' in line or 'Success' in line or '完成' in line:
                    formatted_line = f"✅ {line}"
                elif '警告' in line or 'Warning' in line:
                    formatted_line = f"⚠️ {line}"
                elif line.startswith('='):
                    formatted_line = f"📢 {line}"
                else:
                    formatted_line = line
                
                yield f"data: {json.dumps({'type': 'log', 'message': formatted_line, 'timestamp': timestamp.isoformat(), 'line': line_count})}\n\n"
        
        await process.wait()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        if process.returncode == 0:
            success_msg = f"🎉 数据更新成功完成！耗时: {duration.total_seconds():.1f}秒，共处理 {line_count} 行日志"
            yield f"data: {json.dumps({'type': 'success', 'message': success_msg, 'timestamp': end_time.isoformat()})}\n\n"
        else:
            error_msg = f"❌ 数据更新失败！退出码: {process.returncode}，耗时: {duration.total_seconds():.1f}秒"
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg, 'timestamp': end_time.isoformat()})}\n\n"
            
    except Exception as e:
        error_time = datetime.now()
        error_msg = f"💥 数据更新异常: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg, 'timestamp': error_time.isoformat()})}\n\n"

@app.get("/api/stock/update-stream")
async def update_stock_data_stream(top_n: int = 10, current_user: str = Depends(get_current_user)):
    """流式更新股票数据"""
    cmd = [os.path.join(project_root, ".venv", "bin", "python3"), "tail_trading.py", "update", "--top", str(top_n)]
    
    return StreamingResponse(
        stream_update_logs(cmd, project_root),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization"
        }
    )

@app.post("/api/stock/clear-cache")
async def clear_cache(current_user: str = Depends(get_current_user)):
    """清理缓存数据"""
    try:
        cache_dirs = [
            "/tmp/stock",
            "/tmp/stock_cache", 
            "/tmp/cache",
            "/tmp/concept_cache"
        ]
        
        cleared_dirs = []
        total_size = 0
        
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                # 计算目录大小
                dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                             for dirpath, dirnames, filenames in os.walk(cache_dir)
                             for filename in filenames)
                total_size += dir_size
                
                # 删除目录
                shutil.rmtree(cache_dir)
                cleared_dirs.append(f"{cache_dir} ({dir_size / 1024 / 1024:.1f}MB)")
        
        # 清理项目根目录下的临时文件
        temp_patterns = [
            os.path.join(project_root, "*.tmp"),
            os.path.join(project_root, "*.cache"),
            os.path.join(project_root, "smart_selection_*.json"),
            os.path.join(project_root, "health_check_*.json"),
            os.path.join(project_root, "update_result_*.json"),
            os.path.join(project_root, "validation_report_*.json")
        ]
        
        cleared_files = []
        for pattern in temp_patterns:
            for file_path in glob.glob(pattern):
                file_size = os.path.getsize(file_path)
                total_size += file_size
                os.remove(file_path)
                cleared_files.append(f"{os.path.basename(file_path)} ({file_size / 1024:.1f}KB)")
        
        message = f"🧹 缓存清理完成！\n"
        if cleared_dirs:
            message += f"📁 清理目录: {', '.join(cleared_dirs)}\n"
        if cleared_files:
            message += f"📄 清理文件: {', '.join(cleared_files)}\n"
        message += f"💾 总计释放空间: {total_size / 1024 / 1024:.1f}MB"
        
        return {
            "success": True,
            "message": message,
            "details": {
                "cleared_dirs": len(cleared_dirs),
                "cleared_files": len(cleared_files),
                "total_size_mb": round(total_size / 1024 / 1024, 1)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 缓存清理失败: {str(e)}"
        }

@app.post("/api/stock/clear-disk-data")
async def clear_disk_data(current_user: str = Depends(get_current_user)):
    """清理磁盘数据文件"""
    try:
        data_dirs = [
            os.path.join(project_root, "data", "cache"),
            os.path.join(project_root, "data", "exports"),
            os.path.join(project_root, "logs")
        ]
        
        cleared_items = []
        total_size = 0
        
        for data_dir in data_dirs:
            if os.path.exists(data_dir):
                # 清理目录内容但保留目录结构
                for item in os.listdir(data_dir):
                    item_path = os.path.join(data_dir, item)
                    if os.path.isfile(item_path):
                        # 保留最近的日志文件（最近3天）
                        if data_dir.endswith("logs") and item.endswith(".log"):
                            file_mtime = os.path.getmtime(item_path)
                            if (datetime.now().timestamp() - file_mtime) < 3 * 24 * 3600:  # 3天
                                continue
                        
                        file_size = os.path.getsize(item_path)
                        total_size += file_size
                        os.remove(item_path)
                        cleared_items.append(f"{item} ({file_size / 1024:.1f}KB)")
                    elif os.path.isdir(item_path):
                        dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                     for dirpath, dirnames, filenames in os.walk(item_path)
                                     for filename in filenames)
                        total_size += dir_size
                        shutil.rmtree(item_path)
                        cleared_items.append(f"{item}/ ({dir_size / 1024 / 1024:.1f}MB)")
        
        # 清理临时输出目录（/tmp下的日期目录）
        import re
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for item in os.listdir("/tmp"):
            if date_pattern.match(item):
                item_path = os.path.join("/tmp", item)
                if os.path.isdir(item_path):
                    dir_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                 for dirpath, dirnames, filenames in os.walk(item_path)
                                 for filename in filenames)
                    total_size += dir_size
                    shutil.rmtree(item_path)
                    cleared_items.append(f"临时目录 {item}/ ({dir_size / 1024 / 1024:.1f}MB)")
        
        message = f"🗂️ 磁盘数据清理完成！\n"
        if cleared_items:
            message += f"📋 清理项目: {', '.join(cleared_items[:10])}"  # 只显示前10项
            if len(cleared_items) > 10:
                message += f" 等{len(cleared_items)}项"
            message += f"\n"
        message += f"💾 总计释放空间: {total_size / 1024 / 1024:.1f}MB"
        
        return {
            "success": True,
            "message": message,
            "details": {
                "cleared_items": len(cleared_items),
                "total_size_mb": round(total_size / 1024 / 1024, 1)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ 磁盘数据清理失败: {str(e)}"
        }

@app.post("/api/stock/select")
async def select_stocks(request: SelectStocksRequest, current_user: str = Depends(get_current_user)):
    """选股"""
    try:
        # 获取当天的输出目录
        output_dir = get_date_output_dir()
        
        # 调用传统选股脚本
        cmd = [
            os.path.join(project_root, ".venv", "bin", "python3"), 
            os.path.join(project_root, "scripts", "traditional_select.py")
        ]
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=180  # 3分钟超时
        )
        
        if result.returncode == 0:
            # 尝试解析JSON输出
            import json
            print(f"选股脚本输出长度: {len(result.stdout)}")
            
            try:
                # 先尝试直接解析整个输出
                stocks_data = json.loads(result.stdout.strip())
                print(f"直接JSON解析成功，数据类型: {type(stocks_data)}, 长度: {len(stocks_data) if isinstance(stocks_data, list) else 'N/A'}")
                
                # 保存选股结果到文件
                stock_file = get_stock_results_file()
                with open(stock_file, 'w', encoding='utf-8') as f:
                    json.dump(stocks_data, f, ensure_ascii=False, indent=2)
                print(f"选股结果已保存到: {stock_file}")
                
                # 同时保存到传统选股策略文件
                save_strategy_results('select', stocks_data)
                
                return {
                    "success": True,
                    "message": "选股成功",
                    "data": stocks_data,
                    "log": result.stdout
                }
            except json.JSONDecodeError as e:
                print(f"直接JSON解析失败: {e}")
                
                # 尝试查找JSON数组的开始和结束
                output = result.stdout.strip()
                json_start = output.find('[')
                json_end = output.rfind(']')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = output[json_start:json_end + 1]
                    print(f"提取的JSON字符串长度: {len(json_str)}")
                    print(f"JSON开始: {json_str[:100]}...")
                    
                    try:
                        stocks_data = json.loads(json_str)
                        print(f"提取JSON解析成功，数据长度: {len(stocks_data) if isinstance(stocks_data, list) else 'N/A'}")
                        
                        # 保存选股结果到文件
                        stock_file = get_stock_results_file()
                        with open(stock_file, 'w', encoding='utf-8') as f:
                            json.dump(stocks_data, f, ensure_ascii=False, indent=2)
                        print(f"选股结果已保存到: {stock_file}")
                        
                        # 同时保存到传统选股策略文件
                        save_strategy_results('select', stocks_data)
                        
                        return {
                            "success": True,
                            "message": "选股成功",
                            "data": stocks_data,
                            "log": result.stdout
                        }
                    except json.JSONDecodeError as e2:
                        print(f"提取JSON解析也失败: {e2}")
                
                # 如果仍然无法解析JSON，返回文本输出
                print("无法解析JSON，返回空数据")
                return {
                    "success": True,
                    "message": "选股完成（无法解析JSON格式）",
                    "data": [],
                    "log": result.stdout
                }
        else:
            return {
                "success": False,
                "message": "选股失败",
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "选股超时"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"选股异常: {str(e)}"
        }

@app.post("/api/stock/smart-select")
async def smart_select_stocks(request: SelectStocksRequest, current_user: str = Depends(get_current_user)):
    """智能选股（市场适应性）"""
    try:
        # 获取当天的输出目录
        output_dir = get_date_output_dir()
        
        # 直接调用智能选股脚本
        cmd = [
            os.path.join(project_root, ".venv", "bin", "python3"), 
            os.path.join(project_root, "scripts", "smart_select.py")
        ]
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 解析JSON输出
            try:
                import json
                
                # 查找JSON输出
                output = result.stdout.strip()
                json_start = output.find('{')
                json_end = output.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = output[json_start:json_end + 1]
                    parsed_output = json.loads(json_str)
                    
                    # 提取stocks字段作为data
                    stocks_data = parsed_output.get('stocks', [])
                    
                    # 保存选股结果到文件
                    stock_file = get_stock_results_file()
                    with open(stock_file, 'w', encoding='utf-8') as f:
                        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
                    
                    # 同时保存到智能选股策略文件
                    save_strategy_results('smart', stocks_data)
                    
                    return {
                        "success": True,
                        "message": "智能选股成功",
                        "data": stocks_data,
                        "log": result.stdout
                    }
                else:
                    # 如果找不到JSON，返回空数据
                    return {
                        "success": True,
                        "message": "智能选股完成（未解析到股票数据）",
                        "data": [],
                        "log": result.stdout
                    }
                    
            except json.JSONDecodeError as e:
                print(f"智能选股JSON解析失败: {e}")
                return {
                    "success": False,
                    "message": "智能选股结果解析失败",
                    "error": str(e),
                    "log": result.stdout
                }
        else:
            return {
                "success": False,
                "message": "智能选股失败",
                "error": result.stderr or "智能选股脚本执行失败"
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "智能选股超时"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"智能选股异常: {str(e)}"
        }

@app.post("/api/stock/enhanced-select")
async def enhanced_select_stocks(request: SelectStocksRequest, current_user: str = Depends(get_current_user)):
    """增强选股（放量回调+涨停逻辑）"""
    try:
        # 获取当天的输出目录
        output_dir = get_date_output_dir()
        
        # 直接调用增强选股脚本
        cmd = [
            os.path.join(project_root, ".venv", "bin", "python3"), 
            os.path.join(project_root, "scripts", "enhanced_select.py")
        ]
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            # 解析JSON输出
            try:
                import json
                
                # 查找JSON输出
                output = result.stdout.strip()
                json_start = output.find('{')
                json_end = output.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_str = output[json_start:json_end + 1]
                    parsed_output = json.loads(json_str)
                    
                    # 提取stocks字段作为data
                    stocks_data = parsed_output.get('stocks', [])
                    
                    # 保存到增强选股策略文件
                    save_strategy_results('enhanced', stocks_data)
                    
                    return {
                        "success": True,
                        "message": "增强选股成功",
                        "data": stocks_data,
                        "log": result.stdout
                    }
                else:
                    # 如果找不到JSON，返回空数据
                    return {
                        "success": True,
                        "message": "增强选股完成（未解析到股票数据）",
                        "data": [],
                        "log": result.stdout
                    }
                    
            except json.JSONDecodeError as e:
                print(f"增强选股JSON解析失败: {e}")
                return {
                    "success": False,
                    "message": "增强选股结果解析失败",
                    "error": str(e),
                    "log": result.stdout
                }
            
            # 如果没有解析到股票，返回示例数据
            if not stocks_data:
                stocks_data = [{
                    "code": "000002",
                    "name": "增强选股示例",
                    "strategy": "enhanced",
                    "score": 90
                }]
            
            # 保存选股结果到文件
            stock_file = get_stock_results_file()
            with open(stock_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(stocks_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "message": "增强选股成功",
                "data": stocks_data,
                "log": result.stdout
            }
        else:
            return {
                "success": False,
                "message": "增强选股失败",
                "error": result.stderr or "增强选股脚本执行失败"
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "增强选股超时"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"增强选股异常: {str(e)}"
        }

@app.get("/api/stock/existing-results")
async def get_existing_stock_results(current_user: str = Depends(get_current_user)):
    """获取已存在的选股结果"""
    try:
        stocks = load_existing_stocks()
        return {
            "success": True,
            "message": f"找到 {len(stocks)} 只股票",
            "data": stocks
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"加载选股结果失败: {str(e)}",
            "data": []
        }

@app.get("/api/stock/strategy-results")
async def get_strategy_results(current_user: str = Depends(get_current_user)):
    """获取所有策略的选股结果"""
    try:
        strategies = ['smart', 'enhanced', 'select']
        results = {}
        
        for strategy in strategies:
            stocks = load_strategy_results(strategy)
            results[strategy] = {
                "count": len(stocks),
                "data": stocks
            }
        
        return {
            "success": True,
            "message": "策略结果加载完成",
            "data": results
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"加载策略结果失败: {str(e)}",
            "data": {}
        }

@app.get("/api/stock/top-concepts")
async def get_top_concepts(n: int = 20, current_user: str = Depends(get_current_user)):
    """获取Top N概念股数据"""
    try:
        # 查找最新的概念热度分析文件
        concept_files = glob.glob("/tmp/stock/concept_heat_analysis_*.csv")
        
        if not concept_files:
            return {
                "success": False,
                "message": "暂无概念股数据，请先更新数据",
                "data": []
            }
        
        # 获取最新的文件
        latest_file = max(concept_files, key=os.path.getmtime)
        
        # 读取CSV文件
        df = pd.read_csv(latest_file)
        
        # 获取Top N数据
        top_concepts = df.head(n)
        
        # 转换为前端需要的格式
        concepts_data = []
        for idx, row in top_concepts.iterrows():
            concepts_data.append({
                "rank": idx + 1,
                "concept": row.get("概念名称", ""),
                "heat_score": round(row.get("热度分数", 0), 2),
                "change_pct": f"{row.get('平均涨幅(%)', 0):.2f}%"
            })
        
        file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
        
        return {
            "success": True,
            "message": f"获取Top {len(concepts_data)}概念股成功",
            "data": concepts_data,
            "update_time": file_time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(df)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"获取概念股数据失败: {str(e)}",
            "data": []
        }

@app.post("/api/stock/init-concepts")
async def init_concept_data(current_user: str = Depends(get_current_user)):
    """初始化概念板块数据"""
    try:
        # 运行概念数据初始化脚本
        cmd = [sys.executable, "-c", """
import asyncio
import sys
sys.path.append('.')
from data.est.req.est_concept import EastmoneyConceptStockFetcher
from data.est.req.est_concept_codes import ConceptStockManager

async def init_concepts():
    # 1. 获取所有概念板块
    fetcher = EastmoneyConceptStockFetcher()
    df = fetcher.fetch_and_save()
    if df is None:
        raise RuntimeError("无法获取概念板块数据")
    
    print(f"获取到 {len(df)} 个概念板块")
    
    # 2. 获取每个概念板块的成员股票
    manager = ConceptStockManager()
    concept_codes = df["代码"].tolist()
    
    success_count = 0
    for i, code in enumerate(concept_codes):
        try:
            members_df = manager.fetch_concept_members(code)
            if members_df is not None and len(members_df) > 0:
                save_path = manager.get_save_path(code)
                members_df.to_pickle(save_path)
                success_count += 1
                print(f"进度: {i+1}/{len(concept_codes)}, 成功: {success_count}, 当前: {code}")
        except Exception as e:
            print(f"获取概念 {code} 失败: {e}")
    
    print(f"初始化完成，成功获取 {success_count}/{len(concept_codes)} 个概念板块数据")

asyncio.run(init_concepts())
"""]
        
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30分钟超时
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "概念数据初始化成功",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": "概念数据初始化失败",
                "error": result.stderr
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": "概念数据初始化超时"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"概念数据初始化异常: {str(e)}"
        }

# 定时任务API
@app.get("/api/scheduler/status")
async def get_scheduler_status(current_user: str = Depends(get_current_user)):
    """获取定时任务状态"""
    return task_scheduler.get_status()

@app.post("/api/scheduler/start")
async def start_scheduler(config: SchedulerConfigRequest, current_user: str = Depends(get_current_user)):
    """启动定时任务"""
    success = task_scheduler.start_job(config.cron_expression)
    if success:
        return {"message": "定时任务启动成功"}
    else:
        raise HTTPException(status_code=400, detail="定时任务启动失败")

@app.post("/api/scheduler/stop")
async def stop_scheduler(current_user: str = Depends(get_current_user)):
    """停止定时任务"""
    success = task_scheduler.stop_job()
    if success:
        return {"message": "定时任务停止成功"}
    else:
        raise HTTPException(status_code=400, detail="定时任务停止失败")

@app.get("/api/scheduler/logs")
async def get_scheduler_logs(lines: int = 100, current_user: str = Depends(get_current_user)):
    """获取定时任务日志"""
    logs = task_scheduler.get_logs(lines)
    return {"logs": logs}

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
