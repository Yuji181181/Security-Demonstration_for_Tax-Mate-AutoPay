# ベースイメージ: Python 3.11を使用
FROM python:3.11-slim

# 高速パッケージマネージャー 'uv' を公式イメージからコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY pyproject.toml uv.lock ./

# 【変更点1】仮想環境を作成してインストール (--system を削除)
# --frozen: uv.lockの内容を厳密に守る
# --no-dev: 開発用パッケージは入れない（軽量化のため）
RUN uv sync --frozen --no-dev

# 【変更点2】作成された仮想環境にパスを通す
# これにより、以降のコマンドは自動的に .venv 内のライブラリを使います
ENV PATH="/app/.venv/bin:$PATH"

# ソースコード一式をコピー
COPY . .

# Cloud Runで必要なポート設定
ENV PORT=8080

# Streamlitの起動コマンド
CMD ["streamlit", "run", "src/frontend/app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]