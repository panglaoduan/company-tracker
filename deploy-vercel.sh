#!/bin/bash
# 快速部署到 Vercel

echo "=============================================="
echo "🚀 部署到 Vercel"
echo "=============================================="
echo ""

cd /Users/duanclaw/.easyclaw/workspace/company-tracker

echo "📦 开始部署..."
echo ""
echo "⚠️  第一次使用需要登录 GitHub"
echo "   按提示操作即可"
echo ""

vercel --prod

echo ""
echo "=============================================="
echo "✅ 部署完成！"
echo "=============================================="
echo ""
echo "🌐 访问上面显示的 Production 网址"
echo ""
