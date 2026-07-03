from langchain_core.messages import HumanMessage, AIMessage
import database.db as db
from database.models import ChatMessage
from datetime import datetime

def load_chat_history_for_agent(limit: int = 20):
    """
    Loads chat history from SQLite and converts it to a list of LangChain Messages.
    """
    db.init_db()
    messages = db.get_chat_history(limit=limit)
    lc_messages = []
    for msg in messages:
        if msg.role == 'user':
            lc_messages.append(HumanMessage(content=msg.content))
        elif msg.role == 'assistant':
            lc_messages.append(AIMessage(content=msg.content))
    return lc_messages

def save_chat_message(role: str, content: str):
    """
    Saves a message to the SQLite database.
    """
    db.init_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = ChatMessage(role=role, content=content, timestamp=timestamp)
    db.add_chat_message(msg)

def clear_chat_history():
    """
    Clears all messages from the SQLite database.
    """
    db.init_db()
    db.clear_chat_history()
