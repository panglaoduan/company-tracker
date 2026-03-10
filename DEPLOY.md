# 🌐 发布到公网 - 完整指南

## 方案一：GitHub Pages（推荐 ⭐）

### 步骤 1：创建 GitHub 仓库

1. 访问：https://github.com/
2. 登录你的 GitHub 账号（没有的话先注册）
3. 点击右上角 **"+"** → **"New repository"**
4. 填写：
   - **Repository name**: `company-tracker`
   - **Public** 或 **Private**（建议 Public，免费）
   - **不要勾选** "Initialize this repository with a README"
5. 点击 **"Create repository"**

### 步骤 2：配置远程仓库

复制 GitHub 显示的仓库地址（类似）：
```
https://github.com/YOUR_USERNAME/company-tracker.git
```

在终端运行：
```bash
cd /Users/duanclaw/.easyclaw/workspace/company-tracker
git remote add origin https://github.com/YOUR_USERNAME/company-tracker.git
```

### 步骤 3：部署网站

运行部署脚本：
```bash
chmod +x deploy.sh
./deploy.sh
```

### 步骤 4：访问网站

部署完成后，访问：
```
https://YOUR_USERNAME.github.io/company-tracker/
```

**⏱️ 生效时间**：通常 1-5 分钟

---

## 方案二：Vercel（更简单 ⭐⭐）

### 步骤 1：注册 Vercel

访问：https://vercel.com/
用 GitHub 账号登录

### 步骤 2：安装 Vercel CLI

```bash
npm install -g vercel
```

### 步骤 3：部署

```bash
cd /Users/duanclaw/.easyclaw/workspace/company-tracker/website
vercel --prod
```

按提示操作：
- 第一次会问是否登录，选 **Y**
- 选择用 GitHub 登录
- 其他选项都按 **Enter** 用默认

### 步骤 4：获取网址

部署完成后会显示：
```
🔍  Inspect: https://vercel.com/your-account/xxx
✅  Production: https://xxx.vercel.app
```

访问 **Production** 链接即可！

**优点**：
- ✅ 自动 HTTPS
- ✅ 全球 CDN，速度快
- ✅ 支持自定义域名
- ✅ 完全免费

---

## 方案三：Netlify（拖拽部署 ⭐⭐）

### 步骤 1：访问 Netlify

https://app.netlify.com/drop

### 步骤 2：拖拽文件夹

把 `website` 文件夹拖到网页上的上传区域

### 步骤 3：获取网址

上传完成后会生成一个网址：
```
https://random-name-xxxx.netlify.app
```

**优点**：
- ✅ 最简单，无需命令行
- ✅ 30 秒上线
- ✅ 免费

---

## 方案四：内网穿透（临时用）

如果你只想临时在手机上查看：

### 使用 ngrok

```bash
# 安装
brew install ngrok

# 启动（在另一个终端运行）
ngrok http 8000

# 在 website 目录启动简单服务器
cd /Users/duanclaw/.easyclaw/workspace/company-tracker/website
python3.10 -m http.server 8000
```

ngrok 会生成一个临时公网地址：
```
https://xxx-xxx-xxx.ngrok.io
```

**缺点**：每次重启地址会变，适合临时测试

---

## 📱 访问方式

部署完成后，你可以：

1. **手机浏览器** - 直接访问网址
2. **电脑浏览器** - 收藏网址
3. **添加到主屏幕** - 像 App 一样使用

---

## 🔐 隐私保护

如果不想公开数据：

### GitHub Pages
- 仓库设为 **Private**（免费账号也可以）
- 只有你能访问

### Vercel/Netlify
- 可以设置密码保护
- 或限制访问域名

---

## 💡 推荐方案

| 需求 | 推荐方案 |
|------|----------|
| 长期稳定使用 | **GitHub Pages** |
| 最快部署 | **Vercel** |
| 不想用命令行 | **Netlify 拖拽** |
| 临时测试 | **ngrok** |

---

## 🚀 快速开始（推荐 Vercel）

```bash
# 1. 安装 Vercel
npm install -g vercel

# 2. 部署
cd /Users/duanclaw/.easyclaw/workspace/company-tracker/website
vercel --prod

# 3. 访问显示的网址
```

**全程约 3 分钟！**

---

## 📞 需要帮助？

告诉我你选择的方案，我可以：
- 帮你配置
- 解决部署问题
- 设置自动更新
- 配置自定义域名

---

**选一个方案，我们开始部署！** 🚀
