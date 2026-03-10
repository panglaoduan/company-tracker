#!/bin/bash
# 部署到 GitHub Pages 脚本

echo "=============================================="
echo "🚀 部署公司追踪系统到 GitHub Pages"
echo "=============================================="

# 检查是否配置了 GitHub
if ! git remote get-url origin &>/dev/null; then
    echo ""
    echo "❌ 需要先创建 GitHub 仓库并配置远程地址"
    echo ""
    echo "📝 请按以下步骤操作："
    echo ""
    echo "1. 登录 GitHub: https://github.com/"
    echo ""
    echo "2. 创建新仓库:"
    echo "   - 点击右上角 '+' → 'New repository'"
    echo "   - Repository name: company-tracker"
    echo "   - 选择 'Public' 或 'Private'"
    echo "   - 不要勾选 'Initialize this repository with a README'"
    echo "   - 点击 'Create repository'"
    echo ""
    echo "3. 复制仓库地址（类似）:"
    echo "   https://github.com/YOUR_USERNAME/company-tracker.git"
    echo ""
    echo "4. 运行以下命令（替换为你的地址）:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/company-tracker.git"
    echo ""
    echo "5. 再次运行此脚本"
    echo ""
    exit 1
fi

# 创建 gh-pages 分支
echo "📦 创建 gh-pages 分支..."
git checkout --orphan gh-pages
git reset --hard

# 只复制 website 目录到根目录
echo "📁 准备网站文件..."
mkdir -p temp_website
cp -r website/* temp_website/
cp data/events.json temp_website/ 2>/dev/null || true

git add temp_website/*
git commit -m "Deploy to GitHub Pages"

# 推送到 GitHub
echo "🚀 推送到 GitHub..."
git push -f origin gh-pages

# 清理
git checkout main
rm -rf temp_website

echo ""
echo "=============================================="
echo "✅ 部署完成！"
echo "=============================================="
echo ""
echo "🌐 访问地址:"
echo "   https://YOUR_USERNAME.github.io/company-tracker/temp_website/"
echo ""
echo "⏱️  生效时间：通常需要 1-5 分钟"
echo ""
echo "💡 提示：可以在 GitHub 仓库 Settings → Pages 查看部署状态"
echo ""
