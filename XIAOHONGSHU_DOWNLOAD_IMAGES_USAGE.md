# 小红书图片下载功能使用说明

## 功能概述

`xiaohongshu-download-images` 命令用于有序拉取小红书内容页面的图片，并按顺序保存到 Word 文档中。

## 命令格式

```bash
uv run crawler xiaohongshu-download-images [选项]
```

## 功能特性

- ✅ 支持输入多个 URL
- ✅ 支持从配置文件读取 URL（每行一个）
- ✅ 支持指定输出目录
- ✅ 支持 `-h` 或 `--help` 查看帮助
- ✅ 逐个访问 URL，确保稳定
- ✅ 自动识别图片顺序（基于 `data-index` 属性）
- ✅ 自动去重（过滤重复的 `data-index`）
- ✅ Word 文档边距设置为 0
- ✅ 图片内容居中显示

## 选项说明

### `--urls` / `-u`
- **类型**: 可重复选项
- **说明**: 直接指定 URL，可以多次使用指定多个 URL
- **示例**: `--urls https://www.xiaohongshu.com/explore/xxx --urls https://www.xiaohongshu.com/explore/yyy`

### `--url-config-file` / `-c`
- **类型**: 字符串
- **说明**: URL 配置文件路径，每行一个 URL
- **示例**: `--url-config-file config/urls.txt`

### `--output-dir` / `-o`
- **类型**: 字符串
- **默认值**: `output`
- **说明**: 输出目录，Word 文件将保存在此目录
- **示例**: `--output-dir my_output`

### `--headless` / `--no-headless`
- **类型**: 布尔标志
- **默认值**: `False`（显示浏览器）
- **说明**: 是否使用无头模式
- **示例**: `--headless`（无头模式）或 `--no-headless`（显示浏览器）

### `-h` / `--help`
- **说明**: 显示帮助信息

## 使用示例

### 示例 1: 使用单个 URL

```bash
uv run crawler xiaohongshu-download-images \
  --urls "https://www.xiaohongshu.com/explore/xxx"
```

### 示例 2: 使用多个 URL

```bash
uv run crawler xiaohongshu-download-images \
  --urls "https://www.xiaohongshu.com/explore/xxx" \
  --urls "https://www.xiaohongshu.com/explore/yyy" \
  --urls "https://www.xiaohongshu.com/explore/zzz"
```

### 示例 3: 使用配置文件

首先创建配置文件 `config/urls.txt`：

```text
https://www.xiaohongshu.com/explore/xxx
https://www.xiaohongshu.com/explore/yyy
https://www.xiaohongshu.com/explore/zzz
```

然后运行命令：

```bash
uv run crawler xiaohongshu-download-images \
  --url-config-file config/urls.txt
```

### 示例 4: 指定输出目录

```bash
uv run crawler xiaohongshu-download-images \
  --urls "https://www.xiaohongshu.com/explore/xxx" \
  --output-dir my_downloads
```

### 示例 5: 无头模式运行

```bash
uv run crawler xiaohongshu-download-images \
  --urls "https://www.xiaohongshu.com/explore/xxx" \
  --headless
```

### 示例 6: 组合使用

```bash
uv run crawler xiaohongshu-download-images \
  --urls "https://www.xiaohongshu.com/explore/xxx" \
  --url-config-file config/urls.txt \
  --output-dir downloads \
  --no-headless
```

## 配置文件格式

URL 配置文件是纯文本文件，每行一个 URL：

```text
https://www.xiaohongshu.com/explore/xxx
https://www.xiaohongshu.com/explore/yyy
https://www.xiaohongshu.com/explore/zzz
```

**注意**:
- 空行会被忽略
- 以 `#` 开头的行会被视为注释并忽略
- URL 会自动去重（保持顺序）

## 输出结果

- **文件位置**: `{output_dir}/xiaohongshu_images.docx`
- **文件格式**: Microsoft Word 文档 (.docx)
- **页面设置**: 边距为 0
- **图片排列**: 按 `data-index` 顺序，居中显示

## 工作原理

1. **URL 加载**: 
   - 从命令行参数或配置文件加载 URL 列表
   - 自动去重，保持顺序

2. **逐个访问**:
   - 按顺序访问每个 URL
   - 自动加载和保存 cookies（如果启用）

3. **图片识别**:
   - 使用 CSS 选择器 `.swiper-slide img` 定位图片
   - 从父元素 `<div class="swiper-slide" data-index="X">` 获取 `data-index` 属性
   - 自动去重（相同 `data-index` 只保留第一个）

4. **图片排序**:
   - 按 `data-index` 数值从小到大排序

5. **图片下载**:
   - 异步下载所有图片
   - 处理下载失败的情况

6. **Word 文档生成**:
   - 创建新 Word 文档
   - 设置页面边距为 0
   - 按顺序插入图片，居中显示
   - 保存到指定目录

## 技术细节

### 图片定位

- **CSS 选择器**: `.swiper-slide img`
- **顺序属性**: `data-index`（在 `.swiper-slide` 元素上）
- **去重机制**: 使用 JavaScript `Set` 数据结构，相同 `data-index` 只保留第一个

### 图片 URL 获取优先级

1. `img.src`（当前显示的图片）
2. `img.getAttribute('data-src')`（懒加载图片）
3. `img.getAttribute('data-original')`（原始图片）

### Word 文档设置

- **页面边距**: 0 英寸（上下左右）
- **图片对齐**: 居中
- **图片缩放**: 自动缩放，最大宽度 6.5 英寸
- **图片间距**: 每张图片后添加空行

## 错误处理

- 如果某个 URL 无法访问，会记录错误并继续处理下一个 URL
- 如果某个图片下载失败，会记录错误并继续处理下一个图片
- 如果所有图片都下载失败，Word 文档仍会创建（可能为空）

## 注意事项

1. **登录状态**: 确保已登录小红书账号（cookies 会自动保存和加载）
2. **网络连接**: 需要稳定的网络连接来下载图片
3. **存储空间**: 确保有足够的磁盘空间存储图片和 Word 文档
4. **处理时间**: 处理大量 URL 或图片可能需要较长时间

## 常见问题

### Q: 为什么有些图片没有下载？

A: 可能的原因：
- 图片 URL 无效或已失效
- 网络连接问题
- 图片需要登录才能访问
- 图片加载失败

### Q: 图片顺序不对？

A: 确保页面中的 `data-index` 属性正确。如果 `data-index` 缺失或格式错误，图片可能无法正确排序。

### Q: Word 文档边距不是 0？

A: 某些 Word 版本可能有最小边距限制。代码已设置为 0，但实际显示可能受 Word 软件限制。

### Q: 如何查看详细日志？

A: 日志会输出到控制台，包括：
- URL 处理进度
- 图片下载状态
- 错误信息

## 相关命令

- `xiaohongshu-browse`: 浏览小红书内容（不下载图片）

## 技术栈

- **Playwright**: 浏览器自动化
- **python-docx**: Word 文档生成
- **Pillow**: 图片处理
- **httpx**: 异步 HTTP 请求（图片下载）

