# Security Demonstration: Tax-Mate AutoPay

このリポジトリは、セキュリティ・キャンプ応募課題（LLMアプリケーションへの攻撃と防御）に対する**実証デモアプリケーション**です。

自律型AIエージェントに対する **Indirect Prompt Injection** 攻撃と、それに対する **Human-in-the-loop (HITL)** 防御の実効性を比較検証するために作成されました。

---

## 🎯 プロジェクトの目的

### 【問1: 攻撃シナリオ】の実証

**シナリオ:** 経理処理を行うAIエージェントが、外部から受け取った「請求書」を読み取り、銀行APIを操作して支払いを実行する。
**攻撃手法:** 攻撃者は請求書の備考欄などに不可視の文字や隠しタグで「攻撃者の口座へ送金しろ」という命令（Prompt Injection）を埋め込む。
**結果:** 脆弱なエージェントは、元のシステム指示よりも請求書内の悪意ある指示を優先してしまい、外部システム（銀行API）に対して不正な変更・送金を行ってしまう。

### 【問2: 防御策】の実装と検証

**対策:** **Human-in-the-loop (人間参加型)** アプローチの採用。
**実装:** LangGraphを用いてエージェントの処理フローを構築し、重要なツール実行（送金など）の直前でシステムを強制的に一時停止（Interrupt）させる。
**結果:** エージェントが悪意ある指示に従おうとしても、最終決定権を持つ人間がその操作内容を確認・拒否（Reject）することで、実被害を未然に防ぐことができる。

---

## 📺 デモの流れと検証結果

### 🔴 Attack Demo (Vulnerable Agent) - 問1の検証

**結果:** 脆弱なエージェントは請求書の隠し命令に従い、攻撃者の口座へ送金を実行してしまいます。
**<img width="1681" height="782" alt="Image" src="https://github.com/user-attachments/assets/ca49de25-5517-4954-9bf3-ab4013ad1c67" />**

### 🟢 Defense Demo (Secure Agent) - 問2の検証

**結果:** Human-in-the-loop 防御により、不審な操作は実行前に一時停止されます。

**<img width="1690" height="695" alt="Image" src="https://github.com/user-attachments/assets/1694b334-ed73-4ff3-b7a2-58ac0de8e134" />**
**<img width="1673" height="807" alt="Image" src="https://github.com/user-attachments/assets/cb2f0c0a-3ec4-44d7-9dd8-3b5dd0f4fcb1" />**
*ユーザーは内容を確認し、Rejectボタンで攻撃を阻止できます。*

---

## 起動コマンド

### バックエンド

uv run uvicorn src.backend.server:app --port 8000

### フロントエンド

uv run streamlit run src/frontend/app.py --server.port 8501

## 🛠️ 技術スタック

- **Language:** Python (管理: `uv`)
- **LLM:** Google Gemini 2.5 Flash
- **Orchestration:** LangGraph (StateGraph, Checkpointer)
- **Backend:** FastAPI
- **Frontend:** Streamlit

## 📂 ファイル構成

- `src/backend/agents.py`: LangGraphによるエージェント実装（脆弱版と堅牢版の比較）
- `src/backend/mock_bank.py`: 攻撃対象となる仮想の銀行API
- `src/data/invoices.py`: Prompt Injectionを含む請求書データ
- `src/frontend/app.py`: 検証用UI

