# TMDB 信息生成工具 - 前端页面

这是一个简洁优雅的 React 前端页面，用于与 TMDB 信息生成工具的后端 API 进行交互。

## 功能特性

- **简洁优雅的界面设计** - 现代化的渐变背景和卡片式布局
- **响应式设计** - 适配移动端和桌面端
- **智能表单验证** - 前端验证必填字段
- **加载状态指示** - 请求过程中显示加载动画
- **错误处理** - 友好的错误信息显示
- **结果展示** - 大文本框显示生成的影视简介

## 页面组件

### 输入字段
1. **TMDB 链接** (必填) - 支持电影和电视剧的 TMDB 链接
2. **剧集季度** (可选) - 仅适用于电视剧，输入季度号

### 功能按钮
- **获取按钮** - 提交表单并请求后端 API

### 结果显示
- **输出结果文本框** - 显示生成的 BBCode 格式影视简介
- **错误信息提示** - 当请求失败时显示错误原因

## 使用方法

### 1. 启动后端服务
确保后端服务正在运行（默认端口 23333）：
```bash
cd ..  # 回到项目根目录
python main.py
```

### 2. 启动前端页面
在 `frontend` 目录中运行：

**方法一：使用 Python 内置服务器**
```bash
cd frontend
python -m http.server 8080 --directory public
```

**方法二：使用 Node.js serve**
```bash
cd frontend
npx serve public -p 8080
```

### 3. 访问页面
打开浏览器访问：`http://localhost:8080`

## 使用示例

1. **电影示例**
   - TMDB 链接：`https://www.themoviedb.org/movie/550`
   - 剧集季度：留空
   - 点击"获取"按钮

2. **电视剧示例**
   - TMDB 链接：`https://www.themoviedb.org/tv/1399`
   - 剧集季度：`1`
   - 点击"获取"按钮

## 技术栈

- **React 18** - 现代化的前端框架
- **Vanilla CSS** - 自定义样式，无外部依赖
- **Fetch API** - 与后端 API 通信
- **CDN 引入** - 无需构建过程，开箱即用

## 浏览器兼容性

支持所有现代浏览器：
- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

## 页面特性

### 响应式设计
- 桌面端：最大宽度 800px，居中显示
- 移动端：自适应宽度，优化触摸体验

### 交互体验
- 按钮悬停效果和点击反馈
- 输入框聚焦样式
- 加载状态动画
- 成功/错误状态视觉反馈

### 错误处理
- 网络连接错误
- 后端服务异常
- TMDB 链接格式错误
- 参数验证错误

## 注意事项

1. 确保后端服务运行在正确的端口（默认 23333）
2. 如果后端运行在其他端口，请修改 `app.js` 中的端口配置
3. 需要配置 CORS 允许跨域请求（如果前后端不在同一域名） 