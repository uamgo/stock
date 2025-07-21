"""
数据更新命令

用于更新股票数据
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from data.est.req.est_prepare_data import EstStockPipeline

def add_update_parser(subparsers):
    """添加数据更新命令解析器"""
    parser = subparsers.add_parser(
        "update",
        help="更新股票数据",
        description="更新股票数据，包括概念板块、日线和分钟线数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  tail-trading update                    # 更新默认top10板块数据
  tail-trading update --top-n 20        # 更新top20板块数据
  tail-trading update --top-n 5 --skip-minute  # 更新top5板块，跳过分钟线
  tail-trading update --daily-only       # 仅更新日线数据
        """
    )
    
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="更新前N个涨幅最高的板块 (默认: 10)"
    )
    
    parser.add_argument(
        "--skip-minute",
        action="store_true",
        help="跳过分钟线数据更新"
    )
    
    parser.add_argument(
        "--daily-only",
        action="store_true",
        help="仅更新日线数据，不更新分钟线"
    )
    
    parser.add_argument(
        "--use-proxy",
        action="store_true",
        help="使用代理进行数据获取"
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=20,
        help="并发数量 (默认: 20)"
    )
    
    return parser

def execute_update(args) -> int:
    """执行数据更新命令"""
    from datetime import datetime
    
    print("=== 数据更新系统 ===")
    print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"更新板块数量: TOP {args.top_n}")
    print(f"并发数量: {args.concurrent}")
    
    if args.use_proxy:
        print("✓ 使用代理模式")
    
    if args.daily_only or args.skip_minute:
        print("✓ 跳过分钟线数据更新")
    
    print("-" * 50)
    
    try:
        # 导入数据更新模块
        from data.est.req.est_prepare_data import EstStockPipeline
        
        # 创建数据更新管道
        pipeline = EstStockPipeline(
            top_n=args.top_n,
            use_proxy=args.use_proxy
        )
        
        # 运行数据更新
        asyncio.run(run_update_pipeline(pipeline, args))
        
        print("\n✅ 数据更新完成")
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ 用户中断了数据更新")
        return 1
    except Exception as e:
        print(f"\n❌ 数据更新失败: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1

async def run_update_pipeline(pipeline, args):
    """运行完整的数据更新管道"""
    
    print("开始运行数据更新管道...")
    
    # 步骤1: 获取前N涨幅概念板块代码
    print(f"📊 步骤1: 获取TOP {args.top_n}涨幅概念板块...")
    concept_codes = await pipeline.get_top_n_concepts()
    print(f"✓ 获取到 {len(concept_codes)} 个概念板块")
    
    # 步骤1.5: 更新概念板块成员数据
    print("📈 步骤1.5: 更新概念板块成员数据...")
    pipeline.concept_manager.update_all_concepts(concept_codes, use_proxy_and_concurrent=5)
    print("✓ 概念板块成员数据更新完成")
    
    # 步骤2: 获取所有成员股票数据
    print("📈 步骤2: 获取板块成员股票...")
    members_df = pipeline.get_all_members(concept_codes)
    
    if members_df is None or members_df.empty:
        print("❌ 未获取到有效的成员股票")
        return
    
    print(f"✓ 获取到 {len(members_df)} 只成员股票")
    
    # 保存成员股票数据
    from data.est.req.est_prepare_data import MEMBERS_DF_PATH
    from data.est.req import est_common
    est_common.save_df_to_file(members_df, MEMBERS_DF_PATH)
    print(f"✓ 已保存成员股票数据到 {MEMBERS_DF_PATH}")
    
    # 步骤3: 更新日线数据
    print("📊 步骤3: 更新股票日线数据...")
    await pipeline.update_daily_for_members(members_df)
    print("✓ 日线数据更新完成")
    
    # 步骤4: 更新分钟线数据（如果未跳过）
    if not (args.daily_only or args.skip_minute):
        print("📊 步骤4: 更新股票分钟线数据...")
        await pipeline.update_minute_for_members(members_df)
        print("✓ 分钟线数据更新完成")
    else:
        print("⏭️ 跳过分钟线数据更新")
    
    print("🎉 数据更新管道执行完成！")
