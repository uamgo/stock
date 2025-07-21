#!/usr/bin/env python3
"""
生产环境数据源健康检查

确保所有数据源可用，数据质量符合生产要求
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ProductionDataHealthCheck:
    """生产环境数据健康检查"""
    
    def __init__(self):
        self.check_results = {}
        self.critical_issues = []
        self.warnings = []
        
    def check_eastmoney_data_source(self) -> Dict[str, Any]:
        """检查东方财富数据源"""
        print("🔍 检查东方财富数据源...")
        
        result = {
            "status": "unknown",
            "issues": [],
            "details": {}
        }
        
        try:
            # 检查日线数据模块
            from data.est.req.est_daily import EastmoneyDailyStockFetcher
            daily_fetcher = EastmoneyDailyStockFetcher()
            
            # 测试获取单只股票数据
            test_codes = ["000001", "600519", "000858"]
            successful_fetches = 0
            
            for code in test_codes:
                try:
                    df = daily_fetcher.get_daily_df(code)
                    if df is not None and not df.empty and len(df) > 10:
                        successful_fetches += 1
                        result["details"][f"{code}_rows"] = len(df)
                        
                        # 检查数据完整性
                        required_columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量"]
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        if missing_columns:
                            result["issues"].append(f"{code} 缺少列: {missing_columns}")
                        
                        # 检查数据新鲜度
                        latest_date = pd.to_datetime(df["日期"].iloc[-1])
                        days_old = (datetime.now() - latest_date).days
                        if days_old > 7:
                            result["issues"].append(f"{code} 数据过期 {days_old} 天")
                            
                except Exception as e:
                    result["issues"].append(f"{code} 数据获取失败: {str(e)}")
            
            result["details"]["successful_rate"] = f"{successful_fetches}/{len(test_codes)}"
            
            if successful_fetches >= len(test_codes) * 0.8:
                result["status"] = "healthy"
            elif successful_fetches > 0:
                result["status"] = "degraded"
            else:
                result["status"] = "failed"
                
        except ImportError as e:
            result["status"] = "failed"
            result["issues"].append(f"模块导入失败: {e}")
        except Exception as e:
            result["status"] = "failed"
            result["issues"].append(f"检查异常: {e}")
        
        return result
    
    def check_concept_data_source(self) -> Dict[str, Any]:
        """检查概念数据源"""
        print("🔍 检查概念数据源...")
        
        result = {
            "status": "unknown",
            "issues": [],
            "details": {}
        }
        
        try:
            from data.est.req.est_concept import EastmoneyConceptStockFetcher
            concept_fetcher = EastmoneyConceptStockFetcher()
            
            # 检查概念数据
            concept_df = concept_fetcher.get_concept_df()
            
            if concept_df is not None and not concept_df.empty:
                result["details"]["total_stocks"] = len(concept_df)
                result["details"]["columns"] = list(concept_df.columns)
                
                # 检查涨停股票数量
                if "涨跌幅" in concept_df.columns:
                    limit_up_count = len(concept_df[concept_df["涨跌幅"] >= 9.8])
                    result["details"]["limit_up_count"] = limit_up_count
                
                result["status"] = "healthy"
            else:
                result["status"] = "failed"
                result["issues"].append("概念数据为空")
                
        except ImportError as e:
            result["status"] = "failed"
            result["issues"].append(f"概念模块导入失败: {e}")
        except Exception as e:
            result["status"] = "failed"
            result["issues"].append(f"概念数据检查异常: {e}")
        
        return result
    
    def check_stock_list_source(self) -> Dict[str, Any]:
        """检查股票列表数据源"""
        print("🔍 检查股票列表数据源...")
        
        result = {
            "status": "unknown",
            "issues": [],
            "details": {}
        }
        
        try:
            # 检查主要数据获取器
            from tail_trading.data.eastmoney.daily_fetcher import EastmoneyDataFetcher
            fetcher = EastmoneyDataFetcher()
            
            stock_list = fetcher.get_stock_list()
            
            if stock_list is not None and not stock_list.empty:
                result["details"]["total_stocks"] = len(stock_list)
                result["details"]["columns"] = list(stock_list.columns)
                
                # 检查关键列是否存在
                required_columns = ["代码", "名称"]
                missing_columns = [col for col in required_columns if col not in stock_list.columns]
                if missing_columns:
                    result["issues"].append(f"缺少关键列: {missing_columns}")
                
                # 检查数据质量
                if "代码" in stock_list.columns:
                    empty_codes = stock_list["代码"].isna().sum()
                    if empty_codes > 0:
                        result["issues"].append(f"{empty_codes} 个股票代码为空")
                
                if len(stock_list) < 100:
                    result["issues"].append(f"股票数量过少: {len(stock_list)}")
                    result["status"] = "degraded"
                else:
                    result["status"] = "healthy"
            else:
                result["status"] = "failed"
                result["issues"].append("股票列表为空")
                
        except Exception as e:
            result["status"] = "failed"
            result["issues"].append(f"股票列表检查异常: {e}")
        
        return result
    
    def check_cache_system(self) -> Dict[str, Any]:
        """检查缓存系统"""
        print("🔍 检查缓存系统...")
        
        result = {
            "status": "unknown",
            "issues": [],
            "details": {}
        }
        
        try:
            # 检查缓存目录
            cache_paths = [
                "/tmp/stock/cache",
                "/tmp/stock/daily",
                "/tmp/stock/est_prepare_data"
            ]
            
            accessible_caches = 0
            for cache_path in cache_paths:
                if os.path.exists(cache_path):
                    accessible_caches += 1
                    files_count = len([f for f in os.listdir(cache_path) if f.endswith('.pkl')])
                    result["details"][f"cache_{os.path.basename(cache_path)}"] = f"{files_count} files"
                else:
                    result["issues"].append(f"缓存目录不存在: {cache_path}")
            
            result["details"]["accessible_caches"] = f"{accessible_caches}/{len(cache_paths)}"
            
            if accessible_caches >= len(cache_paths) * 0.7:
                result["status"] = "healthy"
            elif accessible_caches > 0:
                result["status"] = "degraded"
            else:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "failed"
            result["issues"].append(f"缓存检查异常: {e}")
        
        return result
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """检查网络连接"""
        print("🔍 检查网络连接...")
        
        result = {
            "status": "unknown",
            "issues": [],
            "details": {}
        }
        
        try:
            import requests
            
            # 测试关键API端点
            test_urls = [
                "https://push2his.eastmoney.com/api/qt/stock/kline/get",
                "https://push2.eastmoney.com/api/qt/clist/get"
            ]
            
            successful_requests = 0
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=10, params={"test": "1"})
                    if response.status_code < 500:  # 400-499 也算成功，因为参数可能不对
                        successful_requests += 1
                        result["details"][f"url_{len(result['details'])}"] = f"HTTP {response.status_code}"
                    else:
                        result["issues"].append(f"URL访问失败: {url} (HTTP {response.status_code})")
                except Exception as e:
                    result["issues"].append(f"网络请求失败: {str(e)}")
            
            result["details"]["successful_rate"] = f"{successful_requests}/{len(test_urls)}"
            
            if successful_requests >= len(test_urls) * 0.8:
                result["status"] = "healthy"
            elif successful_requests > 0:
                result["status"] = "degraded"
            else:
                result["status"] = "failed"
                
        except Exception as e:
            result["status"] = "failed"
            result["issues"].append(f"网络检查异常: {e}")
        
        return result
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """运行综合健康检查"""
        print("🏥 开始生产环境健康检查")
        print("=" * 50)
        
        # 执行各项检查
        checks = {
            "eastmoney_data": self.check_eastmoney_data_source(),
            "concept_data": self.check_concept_data_source(),
            "stock_list": self.check_stock_list_source(),
            "cache_system": self.check_cache_system(),
            "network": self.check_network_connectivity()
        }
        
        # 汇总结果
        total_checks = len(checks)
        healthy_checks = sum(1 for check in checks.values() if check["status"] == "healthy")
        degraded_checks = sum(1 for check in checks.values() if check["status"] == "degraded")
        failed_checks = sum(1 for check in checks.values() if check["status"] == "failed")
        
        # 确定整体状态
        if failed_checks == 0 and degraded_checks == 0:
            overall_status = "healthy"
        elif failed_checks == 0:
            overall_status = "degraded"
        elif failed_checks < total_checks * 0.5:
            overall_status = "degraded"
        else:
            overall_status = "critical"
        
        # 收集关键问题
        critical_issues = []
        warnings = []
        
        for name, check in checks.items():
            if check["status"] == "failed":
                critical_issues.extend([f"{name}: {issue}" for issue in check["issues"]])
            elif check["status"] == "degraded":
                warnings.extend([f"{name}: {issue}" for issue in check["issues"]])
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "healthy": healthy_checks,
                "degraded": degraded_checks,
                "failed": failed_checks
            },
            "detailed_results": checks,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "recommendations": self._generate_recommendations(checks)
        }
    
    def _generate_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于检查结果生成建议
        if checks["eastmoney_data"]["status"] == "failed":
            recommendations.append("检查东方财富数据模块配置和网络连接")
        
        if checks["concept_data"]["status"] == "failed":
            recommendations.append("更新概念数据源或检查API配置")
        
        if checks["stock_list"]["status"] != "healthy":
            recommendations.append("确保股票列表数据源正常更新")
        
        if checks["cache_system"]["status"] != "healthy":
            recommendations.append("检查缓存目录权限和磁盘空间")
        
        if checks["network"]["status"] != "healthy":
            recommendations.append("检查网络连接和防火墙设置")
        
        # 通用建议
        recommendations.extend([
            "定期运行健康检查",
            "监控数据更新频率",
            "备份关键数据文件",
            "设置数据质量告警"
        ])
        
        return recommendations

def main():
    """主函数"""
    print("🏥 生产环境数据源健康检查")
    print("=" * 50)
    
    checker = ProductionDataHealthCheck()
    
    try:
        # 运行综合检查
        results = checker.run_comprehensive_check()
        
        # 显示结果
        print(f"\n📊 检查结果摘要")
        print("-" * 30)
        print(f"整体状态: {results['overall_status'].upper()}")
        print(f"检查时间: {results['timestamp']}")
        print(f"总检查项: {results['summary']['total_checks']}")
        print(f"健康: {results['summary']['healthy']}")
        print(f"降级: {results['summary']['degraded']}")
        print(f"失败: {results['summary']['failed']}")
        
        # 详细结果
        print(f"\n📋 详细检查结果")
        print("-" * 30)
        for name, check in results["detailed_results"].items():
            status_emoji = {"healthy": "✅", "degraded": "⚠️", "failed": "❌"}.get(check["status"], "❓")
            print(f"{status_emoji} {name.replace('_', ' ').title()}: {check['status'].upper()}")
            
            if check["details"]:
                for key, value in check["details"].items():
                    print(f"   {key}: {value}")
            
            if check["issues"]:
                for issue in check["issues"]:
                    print(f"   ⚠️ {issue}")
        
        # 关键问题
        if results["critical_issues"]:
            print(f"\n🚨 关键问题")
            print("-" * 30)
            for issue in results["critical_issues"]:
                print(f"❌ {issue}")
        
        # 警告
        if results["warnings"]:
            print(f"\n⚠️ 警告")
            print("-" * 30)
            for warning in results["warnings"]:
                print(f"⚠️ {warning}")
        
        # 建议
        print(f"\n💡 改进建议")
        print("-" * 30)
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")
        
        # 保存结果
        import json
        result_file = f"scripts/health_check_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 检查结果已保存到: {result_file}")
        except Exception as e:
            print(f"⚠️ 结果保存失败: {e}")
        
        # 返回状态码
        if results["overall_status"] == "critical":
            return 2
        elif results["overall_status"] == "degraded":
            return 1
        else:
            return 0
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消检查")
        return 130
    except Exception as e:
        print(f"\n❌ 健康检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
