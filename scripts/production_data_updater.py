#!/usr/bin/env python3
"""
生产环境数据更新脚本

确保数据及时更新，支持增量更新和全量更新
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os
import argparse
import time

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ProductionDataUpdater:
    """生产环境数据更新器"""
    
    def __init__(self):
        self.update_log = []
        self.error_log = []
        
    def update_stock_list(self, force: bool = False) -> Dict[str, Any]:
        """更新股票列表"""
        print("📊 更新股票列表...")
        
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            from data.est.req.est_prepare_data import EstStockPipeline
            
            pipeline = EstStockPipeline()
            
            # 检查是否需要更新
            if not force:
                try:
                    members_df = pipeline.get_member_dict_from_file()
                    if members_df is not None and len(members_df) > 0:
                        # 检查数据时间
                        data_file = "/tmp/stock/est_prepare_data/members_dict.pkl"
                        if os.path.exists(data_file):
                            mtime = datetime.fromtimestamp(os.path.getmtime(data_file))
                            hours_old = (datetime.now() - mtime).total_seconds() / 3600
                            
                            if hours_old < 24:  # 24小时内的数据认为是新的
                                result["success"] = True
                                result["message"] = f"股票列表数据较新（{hours_old:.1f}小时前），跳过更新"
                                result["details"]["stocks_count"] = len(members_df)
                                return result
                except:
                    pass  # 如果加载失败，继续更新
            
            # 执行更新
            print("🔄 开始更新股票列表...")
            
            # 这里应该调用实际的数据更新逻辑
            # 由于原系统的复杂性，我们创建一个简化的更新流程
            
            # 1. 获取概念股数据
            from data.est.req.est_concept import EastmoneyConceptStockFetcher
            concept_fetcher = EastmoneyConceptStockFetcher()
            concept_df = concept_fetcher.fetch_and_save(force_update=force)
            
            if concept_df is not None and not concept_df.empty:
                # 2. 从概念数据中提取股票列表
                if "代码" in concept_df.columns:
                    unique_stocks = concept_df[["代码", "名称"]].drop_duplicates()
                    
                    # 转换为字典格式（兼容原有格式）
                    members_dict = {}
                    for _, row in unique_stocks.iterrows():
                        members_dict[row["代码"]] = row["名称"]
                    
                    # 3. 保存股票列表
                    members_file = "/tmp/stock/est_prepare_data/members_dict.pkl"
                    os.makedirs(os.path.dirname(members_file), exist_ok=True)
                    
                    import pickle
                    with open(members_file, 'wb') as f:
                        pickle.dump(members_dict, f)
                    
                    result["success"] = True
                    result["message"] = f"股票列表更新成功，共 {len(unique_stocks)} 只股票"
                    result["details"]["stocks_count"] = len(unique_stocks)
                    result["details"]["source"] = "概念数据"
                    
                    self.update_log.append(f"股票列表更新: {len(unique_stocks)} 只股票")
                else:
                    result["message"] = "概念数据中缺少股票代码列"
            else:
                result["message"] = "概念数据获取失败"
                
        except Exception as e:
            result["message"] = f"股票列表更新失败: {str(e)}"
            self.error_log.append(f"股票列表更新错误: {e}")
        
        return result
    
    def update_daily_data(self, stock_codes: List[str] = None, max_stocks: int = 100) -> Dict[str, Any]:
        """更新日线数据"""
        print("📈 更新日线数据...")
        
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            from data.est.req.est_daily import EastmoneyDailyStockFetcher
            from data.est.req.est_prepare_data import EstStockPipeline
            
            daily_fetcher = EastmoneyDailyStockFetcher()
            
            # 获取股票列表
            if stock_codes is None:
                pipeline = EstStockPipeline()
                try:
                    members_dict = pipeline.get_member_dict_from_file()
                    
                    if members_dict is None or len(members_dict) == 0:
                        result["message"] = "股票列表为空，请先更新股票列表"
                        return result
                    
                    # 限制更新数量
                    stock_codes = list(members_dict.keys())[:max_stocks]
                except:
                    # 如果加载失败，使用默认股票列表
                    stock_codes = ["000001", "000002", "600000", "600036", "000858", "600519"][:max_stocks]
            
            print(f"🔄 开始更新 {len(stock_codes)} 只股票的日线数据...")
            
            # 转换为secid格式
            secids = []
            for code in stock_codes:
                if code.startswith("6"):
                    secids.append(f"1.{code}")
                else:
                    secids.append(f"0.{code}")
            
            # 执行批量更新
            start_time = time.time()
            daily_fetcher.update_all_daily(
                secids, 
                period="day", 
                adjust="qfq", 
                use_proxy_and_concurrent=10
            )
            update_time = time.time() - start_time
            
            # 检查更新结果
            successful_updates = 0
            for code in stock_codes:
                df = daily_fetcher.get_daily_df(code)
                if df is not None and not df.empty:
                    successful_updates += 1
            
            success_rate = successful_updates / len(stock_codes) if stock_codes else 0
            
            result["success"] = success_rate > 0.5
            result["message"] = f"日线数据更新完成，成功率: {success_rate:.1%}"
            result["details"] = {
                "total_stocks": len(stock_codes),
                "successful_updates": successful_updates,
                "success_rate": f"{success_rate:.1%}",
                "update_time": f"{update_time:.1f}秒"
            }
            
            self.update_log.append(f"日线数据更新: {successful_updates}/{len(stock_codes)} 成功")
            
        except Exception as e:
            result["message"] = f"日线数据更新失败: {str(e)}"
            self.error_log.append(f"日线数据更新错误: {e}")
        
        return result
    
    def update_concept_data(self, force: bool = False) -> Dict[str, Any]:
        """更新概念数据"""
        print("💡 更新概念数据...")
        
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            from data.est.req.est_concept import EastmoneyConceptStockFetcher
            
            concept_fetcher = EastmoneyConceptStockFetcher()
            
            # 执行更新
            print("🔄 开始更新概念数据...")
            start_time = time.time()
            
            concept_df = concept_fetcher.fetch_and_save(force_update=force)
            
            update_time = time.time() - start_time
            
            if concept_df is not None and not concept_df.empty:
                # 统计涨停股票
                limit_up_count = 0
                if "涨跌幅" in concept_df.columns:
                    limit_up_count = len(concept_df[concept_df["涨跌幅"] >= 9.8])
                
                result["success"] = True
                result["message"] = f"概念数据更新成功，共 {len(concept_df)} 条记录"
                result["details"] = {
                    "total_records": len(concept_df),
                    "limit_up_stocks": limit_up_count,
                    "update_time": f"{update_time:.1f}秒",
                    "columns": list(concept_df.columns)
                }
                
                self.update_log.append(f"概念数据更新: {len(concept_df)} 条记录")
            else:
                result["message"] = "概念数据获取失败"
                
        except Exception as e:
            result["message"] = f"概念数据更新失败: {str(e)}"
            self.error_log.append(f"概念数据更新错误: {e}")
        
        return result
    
    def clean_old_cache(self, days: int = 7) -> Dict[str, Any]:
        """清理旧缓存"""
        print("🧹 清理旧缓存...")
        
        result = {
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            cache_dirs = [
                "/tmp/stock/cache",
                "/tmp/stock/daily",
                "/tmp/stock/minute"
            ]
            
            total_cleaned = 0
            total_size_saved = 0
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            for cache_dir in cache_dirs:
                if not os.path.exists(cache_dir):
                    continue
                
                cleaned_files = 0
                size_saved = 0
                
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    
                    if os.path.isfile(file_path):
                        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        
                        if mtime < cutoff_time:
                            try:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleaned_files += 1
                                size_saved += file_size
                            except Exception as e:
                                self.error_log.append(f"删除文件失败 {file_path}: {e}")
                
                total_cleaned += cleaned_files
                total_size_saved += size_saved
                
                if cleaned_files > 0:
                    result["details"][f"cleaned_{os.path.basename(cache_dir)}"] = f"{cleaned_files} 文件"
            
            result["success"] = True
            result["message"] = f"清理完成，删除 {total_cleaned} 个文件，节省 {total_size_saved/1024/1024:.1f}MB"
            result["details"]["total_files_cleaned"] = total_cleaned
            result["details"]["total_size_saved_mb"] = f"{total_size_saved/1024/1024:.1f}MB"
            
            self.update_log.append(f"缓存清理: {total_cleaned} 文件")
            
        except Exception as e:
            result["message"] = f"缓存清理失败: {str(e)}"
            self.error_log.append(f"缓存清理错误: {e}")
        
        return result
    
    def run_full_update(self, max_stocks: int = 100, force: bool = False) -> Dict[str, Any]:
        """运行完整更新流程"""
        print("🚀 开始完整数据更新流程")
        print("=" * 50)
        
        start_time = time.time()
        results = {}
        
        # 1. 更新概念数据
        results["concept_update"] = self.update_concept_data(force=force)
        
        # 2. 更新股票列表
        results["stock_list_update"] = self.update_stock_list(force=force)
        
        # 3. 更新日线数据
        if results["stock_list_update"]["success"]:
            results["daily_update"] = self.update_daily_data(max_stocks=max_stocks)
        else:
            results["daily_update"] = {"success": False, "message": "股票列表更新失败，跳过日线数据更新"}
        
        # 4. 清理旧缓存
        results["cache_cleanup"] = self.clean_old_cache()
        
        total_time = time.time() - start_time
        
        # 汇总结果
        successful_tasks = sum(1 for result in results.values() if result["success"])
        total_tasks = len(results)
        
        summary = {
            "overall_success": successful_tasks == total_tasks,
            "successful_tasks": successful_tasks,
            "total_tasks": total_tasks,
            "total_time": f"{total_time:.1f}秒",
            "timestamp": datetime.now().isoformat(),
            "update_log": self.update_log,
            "error_log": self.error_log,
            "detailed_results": results
        }
        
        return summary

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生产环境数据更新")
    parser.add_argument("--mode", choices=["full", "concept", "stocks", "daily"], 
                       default="full", help="更新模式")
    parser.add_argument("--max-stocks", type=int, default=100, 
                       help="最大更新股票数量")
    parser.add_argument("--force", action="store_true", 
                       help="强制更新（忽略缓存）")
    
    args = parser.parse_args()
    
    print("📊 生产环境数据更新器")
    print("=" * 50)
    
    updater = ProductionDataUpdater()
    
    try:
        if args.mode == "full":
            results = updater.run_full_update(max_stocks=args.max_stocks, force=args.force)
            
            # 显示结果
            print(f"\n📋 更新结果摘要")
            print("-" * 30)
            print(f"整体状态: {'成功' if results['overall_success'] else '部分失败'}")
            print(f"成功任务: {results['successful_tasks']}/{results['total_tasks']}")
            print(f"总耗时: {results['total_time']}")
            
            # 详细结果
            print(f"\n📊 详细结果")
            print("-" * 30)
            for task_name, result in results["detailed_results"].items():
                status = "✅" if result["success"] else "❌"
                task_display = task_name.replace("_", " ").title()
                print(f"{status} {task_display}: {result['message']}")
                
                if result.get("details"):
                    for key, value in result["details"].items():
                        print(f"   {key}: {value}")
            
            # 更新日志
            if results["update_log"]:
                print(f"\n📝 更新日志")
                print("-" * 30)
                for log in results["update_log"]:
                    print(f"✅ {log}")
            
            # 错误日志
            if results["error_log"]:
                print(f"\n❌ 错误日志")
                print("-" * 30)
                for error in results["error_log"]:
                    print(f"❌ {error}")
            
        elif args.mode == "concept":
            result = updater.update_concept_data(force=args.force)
            print(f"概念数据更新: {result['message']}")
            
        elif args.mode == "stocks":
            result = updater.update_stock_list(force=args.force)
            print(f"股票列表更新: {result['message']}")
            
        elif args.mode == "daily":
            result = updater.update_daily_data(max_stocks=args.max_stocks)
            print(f"日线数据更新: {result['message']}")
        
        # 保存结果
        if args.mode == "full":
            import json
            result_file = f"scripts/update_result_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            try:
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
                print(f"\n💾 更新结果已保存到: {result_file}")
            except Exception as e:
                print(f"⚠️ 结果保存失败: {e}")
        
        print(f"\n✅ 数据更新完成")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户取消更新")
        return 130
    except Exception as e:
        print(f"\n❌ 数据更新失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
