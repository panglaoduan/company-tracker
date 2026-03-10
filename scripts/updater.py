#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时更新脚本
每天自动采集最新数据
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_collector():
    """运行数据采集器"""
    print("=" * 60)
    print(f"🕐 定时更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    script_path = Path(__file__).parent / 'collector.py'
    
    try:
        # 运行采集器
        result = subprocess.run(
            [sys.executable, str(script_path), '--companies', 'all'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误信息:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⚠️  采集超时")
        return False
    except Exception as e:
        print(f"❌ 采集失败：{e}")
        return False


def send_telegram_notification(message: str):
    """发送 Telegram 通知"""
    # 这里集成 EasyClaw 的 message 工具
    print(f"📤 Telegram 通知：{message}")
    # 实际使用时调用 EasyClaw API


def main():
    """主函数"""
    success = run_collector()
    
    if success:
        message = "✅ 公司追踪数据更新完成"
        print(message)
        # send_telegram_notification(message)
    else:
        message = "⚠️  公司追踪数据更新失败"
        print(message)
        # send_telegram_notification(message)


if __name__ == '__main__':
    main()
