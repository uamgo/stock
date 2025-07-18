"""
定时任务管理模块
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler

# 动态获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter

class SchedulerConfig:
    def __init__(self):
        self.job_id = "stock_data_update"
        self.default_cron = "0 20 14 * * 1-5"  # 工作日下午2:20
        self.config_file = "data/scheduler_config.json"
        self.log_file = "logs/scheduler.log"
        
    def load_config(self) -> Dict:
        """加载调度配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        if not os.path.exists(self.config_file):
            config = {
                "enabled": False,
                "cron_expression": self.default_cron,
                "last_run": None,
                "next_run": None
            }
            self.save_config(config)
            return config
        
        with open(self.config_file, 'r') as f:
            return json.load(f)
    
    def save_config(self, config: Dict):
        """保存调度配置"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone='Asia/Shanghai')
        self.config = SchedulerConfig()
        self.scheduler.start()
        
    def update_stock_data(self):
        """更新股票数据的任务函数"""
        try:
            # 记录开始时间
            start_time = datetime.now()
            log_msg = f"[{start_time.isoformat()}] 开始更新股票数据\n"
            
            # 执行更新命令
            cmd = [sys.executable, "tail_trading.py", "update", "--top", "10"]
            result = subprocess.run(
                cmd, 
                cwd=project_root,
                capture_output=True, 
                text=True
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.returncode == 0:
                log_msg += f"[{end_time.isoformat()}] 更新成功，耗时 {duration:.2f} 秒\n"
                log_msg += f"输出: {result.stdout}\n"
            else:
                log_msg += f"[{end_time.isoformat()}] 更新失败，错误: {result.stderr}\n"
            
            # 写入日志
            os.makedirs(os.path.dirname(self.config.log_file), exist_ok=True)
            with open(self.config.log_file, 'a', encoding='utf-8') as f:
                f.write(log_msg)
            
            # 更新配置中的最后运行时间
            config = self.config.load_config()
            config["last_run"] = end_time.isoformat()
            self.config.save_config(config)
            
        except Exception as e:
            error_time = datetime.now()
            error_msg = f"[{error_time.isoformat()}] 任务执行异常: {str(e)}\n"
            with open(self.config.log_file, 'a', encoding='utf-8') as f:
                f.write(error_msg)
    
    def start_job(self, cron_expression: str = None) -> bool:
        """启动定时任务"""
        try:
            config = self.config.load_config()
            
            if cron_expression:
                # 验证cron表达式
                if not self.validate_cron_expression(cron_expression):
                    return False
                config["cron_expression"] = cron_expression
            
            # 移除现有任务
            self.stop_job()
            
            # 添加新任务
            trigger = CronTrigger.from_crontab(config["cron_expression"])
            self.scheduler.add_job(
                self.update_stock_data,
                trigger=trigger,
                id=self.config.job_id,
                replace_existing=True
            )
            
            config["enabled"] = True
            config["next_run"] = self.get_next_run_time(config["cron_expression"])
            self.config.save_config(config)
            
            return True
        except Exception as e:
            print(f"启动定时任务失败: {e}")
            return False
    
    def stop_job(self) -> bool:
        """停止定时任务"""
        try:
            if self.scheduler.get_job(self.config.job_id):
                self.scheduler.remove_job(self.config.job_id)
            
            config = self.config.load_config()
            config["enabled"] = False
            config["next_run"] = None
            self.config.save_config(config)
            
            return True
        except Exception as e:
            print(f"停止定时任务失败: {e}")
            return False
    
    def get_status(self) -> Dict:
        """获取定时任务状态"""
        config = self.config.load_config()
        job = self.scheduler.get_job(self.config.job_id)
        
        # 同时检查配置和实际任务状态
        is_enabled = config.get("enabled", False)
        job_exists = job is not None
        is_running = is_enabled and job_exists
        
        status = {
            "enabled": is_enabled,
            "cron_expression": config.get("cron_expression", self.config.default_cron),
            "last_run": config.get("last_run"),
            "next_run": config.get("next_run"),
            "running": is_running,  # 使用running而不是is_running，与前端保持一致
            "job_exists": job_exists
        }
        
        # 如果任务正在运行，更新下次运行时间
        if job and job.next_run_time:
            status["next_run"] = job.next_run_time.isoformat()
        elif not is_running:
            status["next_run"] = None
        
        return status
    
    def validate_cron_expression(self, cron_expr: str) -> bool:
        """验证cron表达式"""
        try:
            croniter(cron_expr)
            return True
        except:
            return False
    
    def get_next_run_time(self, cron_expr: str) -> Optional[str]:
        """获取下次运行时间"""
        try:
            cron = croniter(cron_expr, datetime.now())
            next_time = cron.get_next(datetime)
            return next_time.isoformat()
        except:
            return None
    
    def get_logs(self, lines: int = 100) -> List[str]:
        """获取任务日志"""
        try:
            if not os.path.exists(self.config.log_file):
                return []
            
            with open(self.config.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            return [f"读取日志失败: {str(e)}"]

# 全局调度器实例
task_scheduler = TaskScheduler()
