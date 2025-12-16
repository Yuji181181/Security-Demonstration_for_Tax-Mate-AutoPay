# ベースイメージ: Python 3.11を使用
FROM python:3.11-slim

# 高速パッケージマネージャー 'uv' を公式イメージからコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY pyproject.toml uv.lock ./

# uvを使ってライブラリをインストール
# --system: 仮想環境を作らずコンテナ環境に直接インストール
# --frozen: uv.lockの内容を厳密に守る
RUN uv sync --frozen --system

# ソースコード一式をコピー
COPY . .

# Cloud Runで必要なポート設定
ENV PORT=8080

# Streamlitの起動コマンド
# ファイルパス src/frontend/app.py を指定
CMD ["streamlit", "run", "src/frontend/app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]