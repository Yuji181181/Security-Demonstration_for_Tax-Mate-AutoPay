#!/bin/bash

# 1. バックエンド (FastAPI) をバックグラウンドで起動
# src/backend/server.py の中の app 変数を起動します
uv run uvicorn src.backend.server:app --host 127.0.0.1 --port 8000 &

# 2. サーバーが立ち上がるのを少し待つ (5秒)
sleep 5

# 3. フロントエンド (Streamlit) をフォアグラウンドで起動
# Cloud Run が指定するポート(8080)で待ち受けます
uv run streamlit run src/frontend/app.py --server.port 8080 --server.address 0.0.0.0