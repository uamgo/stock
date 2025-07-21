#!/usr/bin/env python3
"""
生产环境最终验证脚本

全面验证系统各个组件的完整性和可用性
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ProductionValidator:
    """生产环境验证器"""
    
    def __init__(self):
        self.validation_results = []
        self.critical_issues = []
        self.warnings = []
    
    def validate_core_modules(self) -> Dict[str, Any]:
        """验证核心模块"""
        print("🔍 验证核心模块...")
        
        result = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        core_modules = [
            ("数据获取模块", "data.est.req.est_concept"),
            ("日线数据模块", "data.est.req.est_daily"),
            ("数据准备模块", "data.est.req.est_prepare_data"),
            ("智能选股模块", "scripts.enhanced_stock_selector"),
            ("放量回调分析", "scripts.volume_retracement_analyzer"),
            ("涨停逻辑分析", "scripts.limit_up_logic_analyzer"),
            ("市场分析模块", "scripts.real_market_analyzer")
        ]
        
        successful_imports = 0
        total_modules = len(core_modules)
        
        for module_name, module_path in core_modules:
            try:
                __import__(module_path)
                result["details"][module_name] = "✅ 导入成功"
                successful_imports += 1
            except Exception as e:
                error_msg = f"❌ 导入失败: {str(e)}"
                result["details"][module_name] = error_msg
                result["errors"].append(f"{module_name}: {str(e)}")
        
        success_rate = successful_imports / total_modules
        
        if success_rate == 1.0:
            result["status"] = "healthy"
        elif success_rate >= 0.8:
            result["status"] = "warning"
        else:
            result["status"] = "critical"
        
        result["success_rate"] = f"{success_rate:.1%}"
        result["successful_imports"] = f"{successful_imports}/{total_modules}"
        
        return result
    
    def validate_data_sources(self) -> Dict[str, Any]:
        """验证数据源"""
        print("📊 验证数据源...")
        
        result = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        try:
            # 测试概念数据获取
            from data.est.req.est_concept import EastmoneyConceptStockFetcher
            concept_fetcher = EastmoneyConceptStockFetcher()
            
            start_time = time.time()
            concept_df = concept_fetcher.fetch_and_save(force_update=False)
            concept_time = time.time() - start_time
            
            if concept_df is not None and not concept_df.empty:
                result["details"]["概念数据"] = f"✅ 获取成功 ({len(concept_df)} 条记录, {concept_time:.1f}s)"
                
                # 检查涨停股票
                if "涨跌幅" in concept_df.columns:
                    limit_up_count = len(concept_df[concept_df["涨跌幅"] >= 9.8])
                    result["details"]["涨停股票"] = f"📈 {limit_up_count} 只涨停股"
            else:
                result["details"]["概念数据"] = "❌ 获取失败"
                result["errors"].append("概念数据获取失败")
            
            # 测试日线数据获取
            from data.est.req.est_daily import EastmoneyDailyStockFetcher
            daily_fetcher = EastmoneyDailyStockFetcher()
            
            test_stock = "000001"
            start_time = time.time()
            daily_df = daily_fetcher.get_daily_df(test_stock)
            daily_time = time.time() - start_time
            
            if daily_df is not None and not daily_df.empty:
                result["details"]["日线数据"] = f"✅ 获取成功 ({len(daily_df)} 条记录, {daily_time:.1f}s)"
            else:
                result["details"]["日线数据"] = "❌ 获取失败"
                result["errors"].append("日线数据获取失败")
            
            # 判断整体状态
            if len(result["errors"]) == 0:
                result["status"] = "healthy"
            elif len(result["errors"]) == 1:
                result["status"] = "warning"
            else:
                result["status"] = "critical"
                
        except Exception as e:
            result["status"] = "critical"
            result["errors"].append(f"数据源验证异常: {str(e)}")
        
        return result
    
    def validate_algorithms(self) -> Dict[str, Any]:
        """验证算法模块"""
        print("🧠 验证算法模块...")
        
        result = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        algorithm_tests = [
            {
                "name": "增强选股算法",
                "module": "scripts.enhanced_stock_selector",
                "class": "EnhancedStockSelector",
                "method": "enhanced_stock_selection",
                "args": {"max_stocks": 5}
            },
            {
                "name": "放量回调分析",
                "module": "scripts.volume_retracement_analyzer",
                "class": "VolumeRetracementAnalyzer",
                "method": "comprehensive_analysis",
                "args": {"code": "000001"}
            },
            {
                "name": "涨停逻辑分析",
                "module": "scripts.limit_up_logic_analyzer",
                "class": "LimitUpLogicAnalyzer", 
                "method": "get_daily_limit_up_stocks",
                "args": {}
            }
        ]
        
        successful_tests = 0
        total_tests = len(algorithm_tests)
        
        for test in algorithm_tests:
            try:
                # 动态导入模块
                module = __import__(test["module"], fromlist=[test["class"]])
                cls = getattr(module, test["class"])
                instance = cls()
                
                # 执行测试方法
                method = getattr(instance, test["method"])
                start_time = time.time()
                
                if test["args"]:
                    test_result = method(**test["args"])
                else:
                    test_result = method()
                
                execution_time = time.time() - start_time
                
                # 判断结果
                if test_result and (
                    (isinstance(test_result, list) and len(test_result) > 0) or
                    (isinstance(test_result, dict) and test_result) or
                    test_result
                ):
                    result["details"][test["name"]] = f"✅ 执行成功 ({execution_time:.1f}s)"
                    successful_tests += 1
                else:
                    result["details"][test["name"]] = f"⚠️ 执行无结果 ({execution_time:.1f}s)"
                    
            except Exception as e:
                result["details"][test["name"]] = f"❌ 执行失败: {str(e)[:50]}..."
                result["errors"].append(f"{test['name']}: {str(e)}")
        
        success_rate = successful_tests / total_tests
        
        if success_rate == 1.0:
            result["status"] = "healthy"
        elif success_rate >= 0.7:
            result["status"] = "warning"
        else:
            result["status"] = "critical"
        
        result["success_rate"] = f"{success_rate:.1%}"
        result["successful_tests"] = f"{successful_tests}/{total_tests}"
        
        return result
    
    def validate_file_structure(self) -> Dict[str, Any]:
        """验证文件结构"""
        print("📁 验证文件结构...")
        
        result = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        required_files = [
            "bot.sh",
            "deploy.sh", 
            "requirements.txt",
            "scripts/enhanced_stock_selector.py",
            "scripts/volume_retracement_analyzer.py",
            "scripts/limit_up_logic_analyzer.py",
            "scripts/production_health_check.py",
            "scripts/production_data_updater.py",
            "scripts/performance_monitor.py",
            "data/est/req/est_concept.py",
            "data/est/req/est_daily.py"
        ]
        
        required_dirs = [
            "scripts",
            "data",
            "docs",
            "backend",
            "frontend"
        ]
        
        existing_files = 0
        existing_dirs = 0
        
        # 检查文件
        for file_path in required_files:
            if os.path.exists(file_path):
                result["details"][f"文件: {file_path}"] = "✅ 存在"
                existing_files += 1
            else:
                result["details"][f"文件: {file_path}"] = "❌ 缺失"
                result["errors"].append(f"缺失文件: {file_path}")
        
        # 检查目录
        for dir_path in required_dirs:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                result["details"][f"目录: {dir_path}"] = "✅ 存在"
                existing_dirs += 1
            else:
                result["details"][f"目录: {dir_path}"] = "❌ 缺失"
                result["errors"].append(f"缺失目录: {dir_path}")
        
        # 计算完整性
        total_items = len(required_files) + len(required_dirs)
        existing_items = existing_files + existing_dirs
        completeness = existing_items / total_items
        
        if completeness == 1.0:
            result["status"] = "healthy"
        elif completeness >= 0.9:
            result["status"] = "warning"
        else:
            result["status"] = "critical"
        
        result["completeness"] = f"{completeness:.1%}"
        result["existing_items"] = f"{existing_items}/{total_items}"
        
        return result
    
    def validate_runtime_environment(self) -> Dict[str, Any]:
        """验证运行环境"""
        print("🔧 验证运行环境...")
        
        result = {
            "status": "unknown",
            "details": {},
            "errors": []
        }
        
        try:
            import platform
            # 如果psutil可用，使用它；否则使用基本检查
            try:
                import psutil
                use_psutil = True
            except ImportError:
                use_psutil = False
            
            # Python版本检查
            python_version = platform.python_version()
            major, minor = map(int, python_version.split('.')[:2])
            
            if major >= 3 and minor >= 8:
                result["details"]["Python版本"] = f"✅ {python_version}"
            else:
                result["details"]["Python版本"] = f"⚠️ {python_version} (建议3.8+)"
                result["errors"].append("Python版本过低")
            
            # 系统资源检查
            if use_psutil:
                memory = psutil.virtual_memory()
                memory_gb = memory.total / (1024**3)
                
                if memory_gb >= 4:
                    result["details"]["系统内存"] = f"✅ {memory_gb:.1f}GB"
                else:
                    result["details"]["系统内存"] = f"⚠️ {memory_gb:.1f}GB (建议4GB+)"
                    result["errors"].append("系统内存不足")
                
                # 磁盘空间检查
                disk = psutil.disk_usage('/')
                disk_free_gb = disk.free / (1024**3)
                
                if disk_free_gb >= 10:
                    result["details"]["磁盘空间"] = f"✅ {disk_free_gb:.1f}GB可用"
                else:
                    result["details"]["磁盘空间"] = f"⚠️ {disk_free_gb:.1f}GB可用 (建议10GB+)"
                    result["errors"].append("磁盘空间不足")
            else:
                result["details"]["系统内存"] = "⚠️ 无法检查（缺少psutil）"
                result["details"]["磁盘空间"] = "⚠️ 无法检查（缺少psutil）"
                result["errors"].append("建议安装psutil包以进行完整的系统资源检查")
            
            # 网络连接检查
            import urllib.request
            try:
                response = urllib.request.urlopen('https://finance.eastmoney.com', timeout=5)
                if response.status == 200:
                    result["details"]["网络连接"] = "✅ 正常"
                else:
                    result["details"]["网络连接"] = f"⚠️ HTTP {response.status}"
                    result["errors"].append("网络连接异常")
            except:
                result["details"]["网络连接"] = "❌ 连接失败"
                result["errors"].append("网络连接失败")
            
            # 判断整体状态
            if len(result["errors"]) == 0:
                result["status"] = "healthy"
            elif len(result["errors"]) <= 2:
                result["status"] = "warning"
            else:
                result["status"] = "critical"
                
        except Exception as e:
            result["status"] = "critical"
            result["errors"].append(f"环境检查异常: {str(e)}")
        
        return result
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """运行全面验证"""
        print("🚀 开始全面生产环境验证")
        print("=" * 60)
        
        start_time = time.time()
        validation_report = {
            "validation_time": datetime.now().isoformat(),
            "validations": {},
            "summary": {},
            "recommendations": []
        }
        
        # 执行各项验证
        validations = [
            ("核心模块", self.validate_core_modules),
            ("数据源", self.validate_data_sources), 
            ("算法模块", self.validate_algorithms),
            ("文件结构", self.validate_file_structure),
            ("运行环境", self.validate_runtime_environment)
        ]
        
        healthy_count = 0
        warning_count = 0
        critical_count = 0
        
        for validation_name, validation_func in validations:
            try:
                validation_result = validation_func()
                validation_report["validations"][validation_name] = validation_result
                
                status = validation_result.get("status", "unknown")
                if status == "healthy":
                    healthy_count += 1
                elif status == "warning":
                    warning_count += 1
                elif status == "critical":
                    critical_count += 1
                    
                # 收集错误和警告
                errors = validation_result.get("errors", [])
                for error in errors:
                    if status == "critical":
                        self.critical_issues.append(f"{validation_name}: {error}")
                    else:
                        self.warnings.append(f"{validation_name}: {error}")
                        
            except Exception as e:
                validation_report["validations"][validation_name] = {
                    "status": "error",
                    "error": str(e)
                }
                critical_count += 1
                self.critical_issues.append(f"{validation_name}: 验证失败 - {str(e)}")
        
        total_time = time.time() - start_time
        
        # 汇总结果
        total_validations = len(validations)
        overall_health = "unknown"
        
        if critical_count == 0 and warning_count == 0:
            overall_health = "excellent"
        elif critical_count == 0:
            overall_health = "good"
        elif critical_count <= 1:
            overall_health = "fair"
        else:
            overall_health = "poor"
        
        validation_report["summary"] = {
            "overall_health": overall_health,
            "total_validations": total_validations,
            "healthy": healthy_count,
            "warnings": warning_count,
            "critical": critical_count,
            "validation_time_seconds": f"{total_time:.1f}",
            "production_ready": critical_count == 0
        }
        
        # 生成建议
        recommendations = []
        if critical_count > 0:
            recommendations.append("立即修复所有严重问题后再部署到生产环境")
        if warning_count > 0:
            recommendations.append("建议在部署前解决警告问题以提升系统稳定性")
        if overall_health in ["excellent", "good"]:
            recommendations.append("系统状态良好，可以部署到生产环境")
        
        recommendations.extend([
            "定期运行健康检查监控系统状态",
            "建立数据备份和恢复机制",
            "监控系统性能和资源使用情况",
            "制定故障应急响应计划"
        ])
        
        validation_report["recommendations"] = recommendations
        validation_report["critical_issues"] = self.critical_issues
        validation_report["warnings"] = self.warnings
        
        return validation_report

def display_validation_report(report: Dict[str, Any]):
    """显示验证报告"""
    print("\n" + "="*60)
    print("🎯 生产环境验证报告")
    print("="*60)
    
    summary = report.get("summary", {})
    overall_health = summary.get("overall_health", "unknown")
    
    # 健康状态图标
    health_icons = {
        "excellent": "🟢",
        "good": "🟡", 
        "fair": "🟠",
        "poor": "🔴",
        "unknown": "⚪"
    }
    
    print(f"\n🎯 总体评估: {health_icons.get(overall_health, '⚪')} {overall_health.upper()}")
    print(f"🔍 验证项目: {summary.get('total_validations', 0)}")
    print(f"✅ 健康: {summary.get('healthy', 0)}")
    print(f"⚠️ 警告: {summary.get('warnings', 0)}")
    print(f"🚨 严重: {summary.get('critical', 0)}")
    print(f"⏱️ 验证耗时: {summary.get('validation_time_seconds', 'N/A')}秒")
    print(f"🚀 生产就绪: {'是' if summary.get('production_ready', False) else '否'}")
    
    # 详细验证结果
    validations = report.get("validations", {})
    if validations:
        print(f"\n📊 详细验证结果")
        print("-" * 40)
        
        for validation_name, validation_result in validations.items():
            status = validation_result.get("status", "unknown")
            
            status_icons = {
                "healthy": "✅",
                "warning": "⚠️",
                "critical": "🚨",
                "error": "❌",
                "unknown": "❓"
            }
            
            icon = status_icons.get(status, "❓")
            print(f"\n{icon} {validation_name} ({status.upper()})")
            
            details = validation_result.get("details", {})
            for key, value in details.items():
                print(f"   {key}: {value}")
            
            # 显示额外信息
            for key in ["success_rate", "successful_imports", "successful_tests", "completeness", "existing_items"]:
                if key in validation_result:
                    display_key = key.replace("_", " ").title()
                    print(f"   {display_key}: {validation_result[key]}")
    
    # 严重问题
    critical_issues = report.get("critical_issues", [])
    if critical_issues:
        print(f"\n🚨 严重问题 ({len(critical_issues)} 个)")
        print("-" * 40)
        for issue in critical_issues:
            print(f"🚨 {issue}")
    
    # 警告
    warnings = report.get("warnings", [])
    if warnings:
        print(f"\n⚠️ 警告 ({len(warnings)} 个)")
        print("-" * 40)
        for warning in warnings:
            print(f"⚠️ {warning}")
    
    # 建议
    recommendations = report.get("recommendations", [])
    if recommendations:
        print(f"\n💡 建议")
        print("-" * 40)
        for i, recommendation in enumerate(recommendations, 1):
            print(f"{i}. {recommendation}")
    
    print(f"\n📅 验证时间: {report.get('validation_time', 'N/A')}")
    print("="*60)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生产环境全面验证")
    parser.add_argument("--save", action="store_true", help="保存验证报告")
    
    args = parser.parse_args()
    
    validator = ProductionValidator()
    
    try:
        # 运行验证
        report = validator.run_comprehensive_validation()
        
        # 显示报告
        display_validation_report(report)
        
        # 保存报告
        if args.save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"scripts/validation_report_{timestamp}.json"
            
            try:
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2, default=str)
                print(f"\n💾 验证报告已保存: {filename}")
            except Exception as e:
                print(f"\n⚠️ 报告保存失败: {e}")
        
        # 返回适当的退出代码
        summary = report.get("summary", {})
        if summary.get("production_ready", False):
            print(f"\n🎉 系统已准备好部署到生产环境！")
            return 0
        else:
            critical_count = summary.get("critical", 0)
            if critical_count > 0:
                print(f"\n⚠️ 发现 {critical_count} 个严重问题，请修复后再部署")
                return 2
            else:
                print(f"\n💡 建议解决警告问题后再部署")
                return 1
    
    except KeyboardInterrupt:
        print("\n\n👋 验证已取消")
        return 130
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
