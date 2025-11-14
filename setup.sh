#!/bin/bash
# 项目初始化脚本

set -e

echo "🚀 初始化爬虫框架项目..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装 uv:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv 已安装"

# 同步依赖
echo "📦 安装依赖..."
uv sync

# 安装 Playwright 浏览器
echo "🌐 安装 Playwright 浏览器..."
uv run playwright install

# 初始化数据库
echo "🗄️  初始化数据库..."
uv run python -m infrastructure.database.init_db

echo "✅ 项目初始化完成！"
echo ""
echo "使用方法："
echo "  uv run python examples/basic_crawler.py  # 运行基础示例"
echo "  uv run python examples/database_demo.py  # 运行数据库示例"
echo "  uv run crawler crawl https://example.com  # 使用 CLI"

