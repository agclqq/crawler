# Interface Layer (接口层)

## 概述

接口层是系统与外部世界的边界，负责接收外部请求并将其转换为应用层的调用。这一层处理输入验证、序列化、路由等。

## 职责

1. **API 端点**: RESTful API 或 GraphQL 端点
2. **CLI 命令**: 命令行接口
3. **请求验证**: 输入数据验证
4. **响应序列化**: 输出数据格式化

## 最佳实践

### 1. API 设计

使用 FastAPI 或类似框架创建 RESTful API：

```python
# ✅ API 端点设计
from fastapi import FastAPI, Depends

app = FastAPI()

@app.post("/api/v1/crawl")
async def crawl_url(
    request: CrawlUrlRequest,
    use_case: CrawlUrlUseCase = Depends(get_crawl_use_case),
) -> CrawlUrlResponse:
    """爬取 URL 的 API 端点"""
    command = CrawlUrlCommand(url=request.url, options=request.options)
    result = await use_case.execute(command)
    return CrawlUrlResponse.from_result(result)
```

### 2. CLI 设计

使用 Click 或 argparse 创建命令行接口：

```python
# ✅ CLI 命令设计
import click

@click.command()
@click.argument('url')
@click.option('--output', '-o', help='Output file')
def crawl(url: str, output: Optional[str]):
    """爬取指定 URL"""
    use_case = get_crawl_use_case()
    result = asyncio.run(use_case.execute(CrawlUrlCommand(url=url)))
    # 处理结果...
```

### 3. 输入验证

在接口层验证输入：

```python
from pydantic import BaseModel, HttpUrl, validator

class CrawlUrlRequest(BaseModel):
    """爬取请求"""
    url: HttpUrl
    options: Optional[Dict[str, Any]] = None
    
    @validator('url')
    def validate_url(cls, v):
        # 自定义验证逻辑
        return v
```

### 4. 错误处理

统一处理异常并返回适当的 HTTP 状态码：

```python
from fastapi import HTTPException

@app.exception_handler(DomainError)
async def domain_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )
```

### 5. 依赖注入

使用依赖注入获取用例实例：

```python
def get_crawl_use_case() -> CrawlUrlUseCase:
    """获取爬取用例实例"""
    # 从依赖容器获取
    return container.get(CrawlUrlUseCase)
```

## 目录结构

```
interface/
├── api/               # RESTful API
│   ├── routes/       # 路由定义
│   ├── schemas/      # 请求/响应模型
│   └── dependencies/ # 依赖注入
├── cli/              # 命令行接口
└── middleware/       # 中间件（认证、日志等）
```

## 注意事项

- 接口层只负责输入输出转换，不包含业务逻辑
- 使用 DTO 在接口层和应用层之间传输数据
- 统一处理异常和错误响应
- 保持接口的简洁和易用性

