#!/usr/bin/env python3
"""
生产环境性能监控脚本

监控系统运行状态、资源使用情况和数据质量
"""

import psutil
import time
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.monitoring_data = []
        self.alert_thresholds = {
            "cpu_usage": 80.0,        # CPU使用率超过80%
            "memory_usage": 85.0,     # 内存使用率超过85%
            "disk_usage": 90.0,       # 磁盘使用率超过90%
            "response_time": 5.0,     # 响应时间超过5秒
            "error_rate": 10.0        # 错误率超过10%
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            
            # 网络统计
            network = psutil.net_io_counters()
            
            # 进程信息
            process_count = len(psutil.pids())
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "used_gb": memory.used / (1024**3),
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "usage_percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "count": process_count
                }
            }
            
            return metrics
            
        except Exception as e:
            return {"error": f"获取系统指标失败: {e}"}
    
    def check_data_freshness(self) -> Dict[str, Any]:
        """检查数据新鲜度"""
        try:
            freshness_report = {
                "timestamp": datetime.now().isoformat(),
                "checks": {}
            }
            
            # 检查各种数据文件的时间戳
            data_files = [
                {
                    "name": "概念数据",
                    "path": "/tmp/stock/est_concept/concept_df.pkl",
                    "max_age_hours": 24
                },
                {
                    "name": "股票列表",
                    "path": "/tmp/stock/est_prepare_data/members_df.pkl",
                    "max_age_hours": 24
                },
                {
                    "name": "日线数据",
                    "path": "/tmp/stock/daily",
                    "max_age_hours": 24,
                    "is_directory": True
                }
            ]
            
            for data_file in data_files:
                file_path = data_file["path"]
                max_age = data_file["max_age_hours"]
                
                check_result = {
                    "status": "unknown",
                    "message": "",
                    "age_hours": None,
                    "last_modified": None
                }
                
                try:
                    if data_file.get("is_directory", False):
                        # 检查目录中的文件
                        if os.path.exists(file_path):
                            files = os.listdir(file_path)
                            if files:
                                # 取最新文件的时间
                                latest_time = 0
                                for filename in files:
                                    full_path = os.path.join(file_path, filename)
                                    if os.path.isfile(full_path):
                                        latest_time = max(latest_time, os.path.getmtime(full_path))
                                
                                if latest_time > 0:
                                    last_modified = datetime.fromtimestamp(latest_time)
                                    age_hours = (datetime.now() - last_modified).total_seconds() / 3600
                                    
                                    check_result["last_modified"] = last_modified.isoformat()
                                    check_result["age_hours"] = age_hours
                                    
                                    if age_hours <= max_age:
                                        check_result["status"] = "fresh"
                                        check_result["message"] = f"数据新鲜（{age_hours:.1f}小时前）"
                                    else:
                                        check_result["status"] = "stale"
                                        check_result["message"] = f"数据过期（{age_hours:.1f}小时前）"
                                else:
                                    check_result["status"] = "error"
                                    check_result["message"] = "目录为空"
                            else:
                                check_result["status"] = "error"
                                check_result["message"] = "目录为空"
                        else:
                            check_result["status"] = "missing"
                            check_result["message"] = "目录不存在"
                    else:
                        # 检查单个文件
                        if os.path.exists(file_path):
                            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                            age_hours = (datetime.now() - last_modified).total_seconds() / 3600
                            
                            check_result["last_modified"] = last_modified.isoformat()
                            check_result["age_hours"] = age_hours
                            
                            if age_hours <= max_age:
                                check_result["status"] = "fresh"
                                check_result["message"] = f"数据新鲜（{age_hours:.1f}小时前）"
                            else:
                                check_result["status"] = "stale"
                                check_result["message"] = f"数据过期（{age_hours:.1f}小时前）"
                        else:
                            check_result["status"] = "missing"
                            check_result["message"] = "文件不存在"
                            
                except Exception as e:
                    check_result["status"] = "error"
                    check_result["message"] = f"检查失败: {e}"
                
                freshness_report["checks"][data_file["name"]] = check_result
            
            return freshness_report
            
        except Exception as e:
            return {"error": f"数据新鲜度检查失败: {e}"}
    
    def test_api_performance(self) -> Dict[str, Any]:
        """测试API性能"""
        try:
            performance_report = {
                "timestamp": datetime.now().isoformat(),
                "tests": {}
            }
            
            # 测试数据获取性能
            tests = [
                {
                    "name": "概念数据获取",
                    "test_func": self._test_concept_data_fetch
                },
                {
                    "name": "日线数据获取",
                    "test_func": self._test_daily_data_fetch
                },
                {
                    "name": "选股算法执行",
                    "test_func": self._test_stock_selection_performance
                }
            ]
            
            for test in tests:
                test_name = test["name"]
                test_func = test["test_func"]
                
                try:
                    start_time = time.time()
                    result = test_func()
                    end_time = time.time()
                    
                    duration = end_time - start_time
                    
                    test_result = {
                        "duration_seconds": duration,
                        "status": "success" if result.get("success", False) else "error",
                        "message": result.get("message", ""),
                        "details": result.get("details", {})
                    }
                    
                    # 判断性能是否达标
                    if duration <= self.alert_thresholds["response_time"]:
                        test_result["performance"] = "good"
                    elif duration <= self.alert_thresholds["response_time"] * 2:
                        test_result["performance"] = "fair"
                    else:
                        test_result["performance"] = "poor"
                    
                except Exception as e:
                    test_result = {
                        "duration_seconds": None,
                        "status": "error",
                        "message": f"测试执行失败: {e}",
                        "performance": "error"
                    }
                
                performance_report["tests"][test_name] = test_result
            
            return performance_report
            
        except Exception as e:
            return {"error": f"API性能测试失败: {e}"}
    
    def _test_concept_data_fetch(self) -> Dict[str, Any]:
        """测试概念数据获取"""
        try:
            from data.est.req.est_concept import EastmoneyConceptStockFetcher
            
            fetcher = EastmoneyConceptStockFetcher()
            concept_df = fetcher.fetch_and_save(force_update=False)
            
            if concept_df is not None and not concept_df.empty:
                return {
                    "success": True,
                    "message": f"获取 {len(concept_df)} 条概念数据",
                    "details": {
                        "records_count": len(concept_df),
                        "columns": list(concept_df.columns)
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "概念数据为空"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"概念数据获取失败: {e}"
            }
    
    def _test_daily_data_fetch(self) -> Dict[str, Any]:
        """测试日线数据获取"""
        try:
            from data.est.req.est_daily import EastmoneyDailyStockFetcher
            
            fetcher = EastmoneyDailyStockFetcher()
            
            # 测试获取一只股票的数据
            test_stock = "000001"  # 平安银行
            df = fetcher.get_daily_df(test_stock)
            
            if df is not None and not df.empty:
                return {
                    "success": True,
                    "message": f"获取 {test_stock} 的 {len(df)} 条日线数据",
                    "details": {
                        "stock_code": test_stock,
                        "records_count": len(df),
                        "date_range": f"{df.index.min()} 到 {df.index.max()}"
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"获取 {test_stock} 日线数据失败"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"日线数据获取失败: {e}"
            }
    
    def _test_stock_selection_performance(self) -> Dict[str, Any]:
        """测试选股算法性能"""
        try:
            from scripts.enhanced_stock_selector import EnhancedStockSelector
            
            selector = EnhancedStockSelector()
            
            # 执行简化的选股测试
            test_stocks = ["000001", "000002", "600000", "600036"]
            
            selected_stocks = []
            for stock_code in test_stocks:
                try:
                    analysis = selector.comprehensive_stock_analysis(stock_code)
                    if analysis.get("final_score", 0) > 0.6:
                        selected_stocks.append(stock_code)
                except:
                    continue
            
            return {
                "success": True,
                "message": f"测试 {len(test_stocks)} 只股票，选出 {len(selected_stocks)} 只",
                "details": {
                    "tested_stocks": len(test_stocks),
                    "selected_stocks": len(selected_stocks),
                    "selection_rate": f"{len(selected_stocks)/len(test_stocks)*100:.1f}%"
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"选股算法测试失败: {e}"
            }
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查是否需要发出警报"""
        alerts = []
        
        try:
            # CPU使用率警报
            if "cpu" in metrics and "usage_percent" in metrics["cpu"]:
                cpu_usage = metrics["cpu"]["usage_percent"]
                if cpu_usage > self.alert_thresholds["cpu_usage"]:
                    alerts.append({
                        "type": "cpu_high",
                        "level": "warning",
                        "message": f"CPU使用率过高: {cpu_usage:.1f}%",
                        "value": cpu_usage,
                        "threshold": self.alert_thresholds["cpu_usage"]
                    })
            
            # 内存使用率警报
            if "memory" in metrics and "usage_percent" in metrics["memory"]:
                memory_usage = metrics["memory"]["usage_percent"]
                if memory_usage > self.alert_thresholds["memory_usage"]:
                    alerts.append({
                        "type": "memory_high",
                        "level": "warning",
                        "message": f"内存使用率过高: {memory_usage:.1f}%",
                        "value": memory_usage,
                        "threshold": self.alert_thresholds["memory_usage"]
                    })
            
            # 磁盘使用率警报
            if "disk" in metrics and "usage_percent" in metrics["disk"]:
                disk_usage = metrics["disk"]["usage_percent"]
                if disk_usage > self.alert_thresholds["disk_usage"]:
                    alerts.append({
                        "type": "disk_high",
                        "level": "critical",
                        "message": f"磁盘使用率过高: {disk_usage:.1f}%",
                        "value": disk_usage,
                        "threshold": self.alert_thresholds["disk_usage"]
                    })
            
        except Exception as e:
            alerts.append({
                "type": "monitor_error",
                "level": "error",
                "message": f"警报检查失败: {e}"
            })
        
        return alerts
    
    def generate_monitoring_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        print("📊 生成监控报告...")
        
        report = {
            "report_time": datetime.now().isoformat(),
            "summary": {
                "overall_status": "unknown",
                "critical_issues": 0,
                "warnings": 0,
                "system_health": "unknown"
            }
        }
        
        try:
            # 1. 系统性能指标
            print("🔧 检查系统性能...")
            system_metrics = self.get_system_metrics()
            report["system_metrics"] = system_metrics
            
            # 2. 数据新鲜度检查
            print("📅 检查数据新鲜度...")
            freshness_report = self.check_data_freshness()
            report["data_freshness"] = freshness_report
            
            # 3. API性能测试
            print("⚡ 测试API性能...")
            performance_report = self.test_api_performance()
            report["api_performance"] = performance_report
            
            # 4. 检查警报
            alerts = self.check_alerts(system_metrics)
            report["alerts"] = alerts
            
            # 5. 汇总状态
            critical_issues = len([a for a in alerts if a.get("level") == "critical"])
            warnings = len([a for a in alerts if a.get("level") == "warning"])
            
            # 判断整体状态
            if critical_issues > 0:
                overall_status = "critical"
                system_health = "poor"
            elif warnings > 0:
                overall_status = "warning"
                system_health = "fair"
            else:
                overall_status = "healthy"
                system_health = "good"
            
            # 检查数据状态
            stale_data_count = 0
            if "checks" in freshness_report:
                stale_data_count = len([
                    check for check in freshness_report["checks"].values() 
                    if check.get("status") == "stale"
                ])
            
            if stale_data_count > 0:
                if overall_status == "healthy":
                    overall_status = "warning"
                    system_health = "fair"
            
            report["summary"] = {
                "overall_status": overall_status,
                "critical_issues": critical_issues,
                "warnings": warnings,
                "stale_data_sources": stale_data_count,
                "system_health": system_health
            }
            
        except Exception as e:
            report["error"] = f"报告生成失败: {e}"
            report["summary"]["overall_status"] = "error"
        
        return report
    
    def save_monitoring_data(self, report: Dict[str, Any]) -> str:
        """保存监控数据"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"scripts/monitoring_report_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            return filename
            
        except Exception as e:
            print(f"⚠️ 监控数据保存失败: {e}")
            return ""

def display_monitoring_report(report: Dict[str, Any]):
    """显示监控报告"""
    print("\n" + "="*60)
    print("📊 系统监控报告")
    print("="*60)
    
    # 总体状态
    summary = report.get("summary", {})
    overall_status = summary.get("overall_status", "unknown")
    
    status_emoji = {
        "healthy": "✅",
        "warning": "⚠️",
        "critical": "🚨",
        "error": "❌",
        "unknown": "❓"
    }
    
    print(f"\n🎯 总体状态: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
    print(f"🔧 系统健康度: {summary.get('system_health', 'unknown')}")
    print(f"🚨 严重问题: {summary.get('critical_issues', 0)}")
    print(f"⚠️ 警告: {summary.get('warnings', 0)}")
    print(f"📅 过期数据源: {summary.get('stale_data_sources', 0)}")
    
    # 系统性能
    system_metrics = report.get("system_metrics", {})
    if "error" not in system_metrics:
        print(f"\n💻 系统性能")
        print("-" * 30)
        
        if "cpu" in system_metrics:
            cpu = system_metrics["cpu"]
            print(f"CPU使用率: {cpu.get('usage_percent', 0):.1f}% ({cpu.get('count', 0)} 核心)")
        
        if "memory" in system_metrics:
            memory = system_metrics["memory"]
            print(f"内存使用: {memory.get('usage_percent', 0):.1f}% "
                  f"({memory.get('used_gb', 0):.1f}GB / {memory.get('total_gb', 0):.1f}GB)")
        
        if "disk" in system_metrics:
            disk = system_metrics["disk"]
            print(f"磁盘使用: {disk.get('usage_percent', 0):.1f}% "
                  f"({disk.get('used_gb', 0):.1f}GB / {disk.get('total_gb', 0):.1f}GB)")
    
    # 数据新鲜度
    freshness_report = report.get("data_freshness", {})
    if "checks" in freshness_report:
        print(f"\n📅 数据新鲜度")
        print("-" * 30)
        
        for data_name, check_result in freshness_report["checks"].items():
            status = check_result.get("status", "unknown")
            message = check_result.get("message", "")
            
            status_emoji_map = {
                "fresh": "✅",
                "stale": "⚠️",
                "missing": "❌",
                "error": "❌"
            }
            
            emoji = status_emoji_map.get(status, "❓")
            print(f"{emoji} {data_name}: {message}")
    
    # API性能
    performance_report = report.get("api_performance", {})
    if "tests" in performance_report:
        print(f"\n⚡ API性能测试")
        print("-" * 30)
        
        for test_name, test_result in performance_report["tests"].items():
            duration = test_result.get("duration_seconds")
            status = test_result.get("status", "unknown")
            performance = test_result.get("performance", "unknown")
            
            perf_emoji = {
                "good": "✅",
                "fair": "⚠️",
                "poor": "🚨",
                "error": "❌"
            }
            
            emoji = perf_emoji.get(performance, "❓")
            duration_str = f"{duration:.2f}s" if duration else "N/A"
            print(f"{emoji} {test_name}: {duration_str} ({performance})")
            
            if test_result.get("message"):
                print(f"   {test_result['message']}")
    
    # 警报信息
    alerts = report.get("alerts", [])
    if alerts:
        print(f"\n🚨 系统警报 ({len(alerts)} 个)")
        print("-" * 30)
        
        for alert in alerts:
            level = alert.get("level", "info")
            message = alert.get("message", "")
            
            level_emoji = {
                "critical": "🚨",
                "warning": "⚠️",
                "error": "❌",
                "info": "ℹ️"
            }
            
            emoji = level_emoji.get(level, "ℹ️")
            print(f"{emoji} {level.upper()}: {message}")
    
    print(f"\n📊 报告时间: {report.get('report_time', 'unknown')}")
    print("="*60)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生产环境性能监控")
    parser.add_argument("--save", action="store_true", help="保存监控报告")
    parser.add_argument("--watch", type=int, help="持续监控模式，指定监控间隔（秒）")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    try:
        if args.watch:
            print(f"🔄 开始持续监控模式（每{args.watch}秒刷新）")
            print("按 Ctrl+C 退出监控...")
            
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                
                report = monitor.generate_monitoring_report()
                display_monitoring_report(report)
                
                if args.save:
                    filename = monitor.save_monitoring_data(report)
                    if filename:
                        print(f"\n💾 报告已保存: {filename}")
                
                time.sleep(args.watch)
        else:
            # 单次监控
            report = monitor.generate_monitoring_report()
            display_monitoring_report(report)
            
            if args.save:
                filename = monitor.save_monitoring_data(report)
                if filename:
                    print(f"\n💾 报告已保存: {filename}")
    
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")
        return 130
    except Exception as e:
        print(f"\n❌ 监控失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
