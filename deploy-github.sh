#!/bin/bash
# GitHub Pages 一键部署脚本

echo "=============================================="
echo "🚀 部署到 GitHub Pages"
echo "=============================================="
echo ""

# 检查远程仓库
if ! git remote get-url origin &>/dev/null; then
    echo "❌ 未配置 GitHub 远程仓库"
    echo ""
    echo "📝 请按以下步骤操作："
    echo ""
    echo "1️⃣  访问：https://github.com/new"
    echo ""
    echo "2️⃣  创建仓库:"
    echo "    - Repository name: company-tracker"
    echo "    - 选择 Public 或 Private"
    echo "    - 不要勾选 Initialize with README"
    echo "    - 点击 Create repository"
    echo ""
    echo "3️⃣  复制仓库地址（类似）:"
    echo "    https://github.com/YOUR_USERNAME/company-tracker.git"
    echo ""
    echo "4️⃣  运行命令（替换为你的地址）:"
    echo "    git remote add origin https://github.com/YOUR_USERNAME/company-tracker.git"
    echo ""
    echo "5️⃣  再次运行：./deploy-github.sh"
    echo ""
    exit 1
fi

# 显示远程仓库
REMOTE_URL=$(git remote get-url origin)
echo "✅ 远程仓库：$REMOTE_URL"
echo ""

# 切换到 gh-pages 分支
echo "📦 准备部署..."
git checkout --orphan gh-pages
git reset --hard

# 复制网站文件到根目录
echo "📁 复制网站文件..."
mkdir -p temp_site
cp -r website/* temp_site/
cp data/events.json temp_site/ 2>/dev/null || true

# 提交
git add temp_site/*
git commit -m "Deploy company tracker website"

# 推送
echo "🚀 推送到 GitHub..."
git push -f origin gh-pages

# 清理
git checkout main
rm -rf temp_site

echo ""
echo "=============================================="
echo "✅ 部署成功！"
echo "=============================================="
echo ""
echo "🌐 访问地址（1-5 分钟后生效）:"
echo "    https://YOUR_USERNAME.github.io/company-tracker/"
echo ""
echo "💡 替换 YOUR_USERNAME 为你的 GitHub 用户名"
echo ""
echo "📊 查看部署状态:"
echo "    https://github.com/YOUR_USERNAME/company-tracker/settings/pages"
echo ""
