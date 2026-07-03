from dataclasses import dataclass, asdict
from datetime import date

@dataclass
class Transaction:
    type: str  # 'income' or 'expense'
    category: str
    amount: float
    date: str  # YYYY-MM-DD
    description: str = ""
    id: int = None

    def to_dict(self):
        return asdict(self)

@dataclass
class Budget:
    category: str
    amount: float
    id: int = None

    def to_dict(self):
        return asdict(self)

@dataclass
class SavingsGoal:
    name: str
    target_amount: float
    current_amount: float
    target_date: str  # YYYY-MM-DD
    id: int = None

    def to_dict(self):
        return asdict(self)

@dataclass
class ChatMessage:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str  # YYYY-MM-DD HH:MM:SS
    id: int = None

    def to_dict(self):
        return asdict(self)
