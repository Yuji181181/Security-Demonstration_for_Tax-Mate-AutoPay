import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load env
load_dotenv()

def test_simple_invoke():
    print("Testing Simple Invoke...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    try:
        msg = [HumanMessage(content="Hello")]
        res = llm.invoke(msg)
        print(f"Simple Result: {res.content}")
    except Exception as e:
        print(f"Simple Invoke Failed: {e}")
        import traceback
        traceback.print_exc()

def test_system_message():
    print("\nTesting System Message...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    try:
        msg = [
            SystemMessage(content="You are a helper."),
            HumanMessage(content="Hello")
        ]
        res = llm.invoke(msg)
        print(f"System Message Result: {res.content}")
    except Exception as e:
        print(f"System Message Invoke Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_invoke()
    test_system_message()
