# Security Demonstration: Tax-Mate AutoPay

このリポジトリは、LLMアプリケーションへの攻撃と防御の実証デモアプリケーションです。  

自律型AIエージェントに対する **Indirect Prompt Injection（プロンプトによる攻撃）** と、それに対する **LLM Guardrail (AIによる自動防御)** を比較検証するために作成しました。

---

## 🎯 プロジェクトのポイント：LLM vs LLM

本デモの最大の特徴は、**攻撃を受けるエージェントと、それを守るガードレールの両方に、全く同じモデルのLLM（Llama 3.3 70B Versatile）を採用している点**にあります。

**同一モデルなのに結果が分かれる理由:**  
強力なLLMであっても、構成が「脆弱」であれば単純な言葉のトリックに騙されます。一方で、同じ能力を持つモデルを「監査役（ガードレール）」という適切な役割で配置すれば、自分自身を騙そうとする高度な入力すらも見破ることができることを実証しています。

---

## 🎯 プロジェクトの目的

### 【問1: 攻撃シナリオ】の実証

**シナリオ:** 経理処理を行うAIエージェントが、外部から受け取った「請求書」を読み取り、銀行APIを操作して支払いを実行する。  
**攻撃手法:** 攻撃者は請求書に「攻撃者の口座へ送金しろ」という攻撃命令を仕込む。  
**結果:** 脆弱なエージェントは、元のシステム指示よりも攻撃命令を優先してしまい、外部システム（銀行API）に対して不正な変更・送金を行ってしまう。

### 【問2: 防御策】の実装と検証

**対策:** **LLM Guardrail (AIによる自動監査)** アプローチの採用。  
**実装:** LangGraphを用いてエージェントの処理フローを構築し、ツール実行（送金など）の直前に、セキュリティ特化の役割を与えたLLM (Llama 3.3 70B Versatile) が操作内容を監査する。  
**結果:** エージェントが悪意ある指示に従おうとしても、ガードレールAIが「請求書のコンテキストと矛盾する不審な操作」として検知し、実行を自動的にブロック（Block）することで、実被害を未然に防ぐことができる。

---

## 📺 デモの流れと検証結果

### 🔴 Attack Demo (Vulnerable Agent)
**同一モデルを使用した「脆弱な構成」の例。**
- **結果:** 請求書の攻撃者の命令に従い、不正送金を実行してしまいます。
- エージェントが攻撃命令に忠実に従いすぎるため、無限ループに入ることがありますが、サーバー側でハンドルし「攻撃成功」として表示します。
- どんなに賢いモデルでも、**「役割の分離」と「監査プロセス」がないと無力である**ことを実証します。
<img width="1727" height="521" alt="Image" src="https://github.com/user-attachments/assets/c842b1d5-88de-46b6-8cb0-0724014aed5b" />
<img width="1722" height="734" alt="Image" src="https://github.com/user-attachments/assets/8bfbd6d2-25da-4b96-8fac-9f2b34757961" />

### 🟢 Defense Demo (Secure Agent)
**同一モデルを使用した「堅牢な構成」の例。**
- **結果:** ガードレールに採用した **Llama 3.3 70B Versatile** が、提案されたアクションの「矛盾」を即座に見破ります。
- ユーザーは「どのアクションがなぜブロックされたのか」を防御ロジックの概念コードと共に視覚的に確認できます。
- **「能力（LLMの賢さ）」ではなく「設計（ガードレール）」がセキュリティの鍵である**ことを実証します。
<img width="1731" height="806" alt="Image" src="https://github.com/user-attachments/assets/5ecb7fd1-b7d2-49f1-848a-c21c2f4f92b2" />
<img width="1726" height="729" alt="Image" src="https://github.com/user-attachments/assets/f48b1115-0b53-49bf-a2fd-e880c1726ffd" />

---
## 起動コマンド

### バックエンド起動

```bash
uv run uvicorn src.backend.server:app --port 8000
```

### フロントエンド起動

```bash
uv run streamlit run src/frontend/app.py --server.port 8501
```

## 🛠️ 技術スタック

- **Language:** Python (uv)
- **Agent LLM:** Groq API (Llama 3.3 70B Versatile)
- **Guardrail LLM:** Groq API (Llama 3.3 70B Versatile)
- **Orchestration:** LangGraph
- **Backend:** FastAPI
- **Frontend:** Streamlit

## 📂 主要ファイル構成

- `src/backend/agents.py`: LLMエージェントのグラフ定義（同一モデルを用いた「脆弱版」と「堅牢版」）
- `src/backend/server.py`: FastAPIによるAPIサーバー
- `src/backend/mock_bank.py`: 攻撃対象となる仮想銀行システム
- `src/data/invoices.py`: 攻撃が仕込まれた請求書データ
- `src/frontend/app.py`: StreamlitによるUI実装
- `verification/verify_guardrail.py`: ガードレール機能のCUI検証スクリプト

