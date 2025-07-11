import json
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query,Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from gen import TmdbGen

# 导入环境变量
load_dotenv()

api_access_token = os.getenv("ACCESS_TOKEN")
if not api_access_token:
    raise ValueError("未设置ACCESS_TOKEN环境变量")
http_proxy = os.getenv("HTTP_PROXY")
server_port = os.getenv("SERVER_PORT", "23333")
if not server_port.isdigit():
    server_port = "23333"  # 默认端口

app = FastAPI(title="TMDBGen API")

# 添加 CORS 中间件支持前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tmdb_gen = TmdbGen(api_access_token=api_access_token, proxy=http_proxy)

@app.get("/introduction", summary="获取简介",description="获取简介",status_code=200)
async def introduction(
    media_link:str = Query(default=..., description="媒体链接"),
    language:Optional[str] = Query(default="zh-CN", description="语言代码,默认zh-CN"),
    season_number:Optional[int] = Query(default=None, description="季度号,如果是电影则不需要填写"),
):
    response,data = await tmdb_gen.gen_description(
        media_link=media_link,
        language=language,
        season_number=season_number
    )
    if response:
        return Response(status_code=200,
                        content=data,
                        media_type="text/plain")

    else:
        return {
            "code": 400,
            "message": f"获取失败,原因：{data}",
            "data": None
        }


if __name__ == '__main__':

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(server_port),
    )