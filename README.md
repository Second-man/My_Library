# 我的藏书馆 (My Library)

一个基于 Flask 的私人数字阅读平台，支持多用户注册、书籍管理、在线阅读与个人收藏。

---

## 功能特性

### 用户端
- 用户注册 / 登录 / 退出（Session 认证）
- 首页视频背景 + 可选背景音乐播放器，沉浸式阅读氛围
- 按书名或作者搜索书籍
- 书籍卡片网格展示（封面图 + 阅读/收藏按钮）
- 在线阅读器（读取 .txt 文件，衬线字体排版）
- 个人收藏夹（收藏/取消收藏，已登录可见）

### 管理员端
- 仅 admin 账号可访问管理后台
- 添加书籍（上传 .txt 文件 + 填写书名、作者、封面 URL）
- 修改书籍元信息（模态框编辑）
- 删除书籍（同时删除数据库记录和本地文件）
- 默认管理员账号：`admin` / `admin123`

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask ≥3.0 |
| 数据库 | SQLite（`database.db`） |
| 前端 | Jinja2 模板 + HTML5/CSS3/原生 JavaScript |
| 图标 | Font Awesome 6.4 |
| 字体 | Google Fonts (Poppins) |

---

## 项目结构

```
My_Library/
├── app.py                        # Flask 主应用（路由、业务逻辑）
├── database.db                   # SQLite 数据库文件
├── requirements.txt              # Python 依赖
├── books/                        # 上传的 .txt 书籍文件
├── static/
│   ├── style.css                 # 基础样式表
│   ├── music/                    # 背景音乐文件
│   └── videos/                   # 背景视频文件
└── templates/
    ├── index.html                # 首页（视频背景、搜索、书籍网格、音乐播放器）
    ├── login.html                # 登录页
    ├── register.html             # 注册页
    ├── read.html                 # 阅读页
    ├── profile.html              # 我的收藏页
    └── admin.html                # 管理员后台（CRUD 操作）
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python app.py
```

首次运行会自动：
- 创建 `database.db` 并初始化数据表
- 创建默认管理员账号 `admin` / `admin123`

### 3. 访问

打开浏览器访问 `http://127.0.0.1:5000`

---

## 使用指南

### 普通用户
1. 点击 **注册** 创建账号
2. 登录后在首页浏览书籍，点击 **阅读** 打开阅读器
3. 点击 **收藏** 将书籍加入个人收藏，在 **我的收藏** 中查看

### 管理员
1. 使用 `admin` / `admin123` 登录
2. 导航栏出现 **管理书籍** 入口
3. 在管理后台可 **添加**（上传 .txt 文件）、**修改**（点击编辑按钮）、**删除** 书籍

### 背景音乐
- 首页左下角 **开启音乐** 按钮控制播放/暂停
- 鼠标悬停显示歌曲下拉列表
- 播放状态自动保存到浏览器 localStorage

---

## 数据库设计

### `users` 用户表

| 字段 | 类型 | 约束 |
|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| username | TEXT | UNIQUE, NOT NULL |
| password | TEXT | NOT NULL |

### `books` 书籍表

| 字段 | 类型 | 约束 |
|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| title | TEXT | NOT NULL |
| author | TEXT | NOT NULL |
| cover_url | TEXT | 可为空（封面图片 URL） |
| file_path | TEXT | NOT NULL（本地 txt 路径） |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### `user_favorites` 收藏表

| 字段 | 类型 | 约束 |
|------|------|------|
| user_id | INTEGER | FOREIGN KEY → users(id) |
| book_id | INTEGER | FOREIGN KEY → books(id) |
| (user_id, book_id) | - | PRIMARY KEY（联合主键） |

---

## 注意事项

- 密码以明文存储，仅供本地/个人使用环境；生产部署前应使用 `werkzeug.security` 进行哈希处理
- `app.secret_key` 为硬编码占位值，正式使用时应更换
- 仅支持上传 `.txt` 格式的书籍文件
- Flask 运行在 `debug=True` 模式，生产环境应关闭
- 依赖外部 CDN（Font Awesome、Google Fonts），离线环境可能需要本地化

---

## 未来可改进方向

- 密码哈希加密（bcrypt / werkzeug.security）
- 书籍分章 / 目录解析
- 支持更多格式（PDF、EPUB）
- 阅读进度记录
- 用户头像与个人资料编辑
- 评论 / 评分功能
- 生产级部署（Gunicorn / Waitress）
