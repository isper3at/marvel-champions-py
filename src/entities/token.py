from dataclasses import dataclass

@dataclass(frozen=True)
class Token:
    """
    Token entity - represents a token/counter on a card.
    
    Attributes:
        type: Type of token (e.g., 'damage', 'resource', etc.)
        amount: Number of tokens of this type
    """
    type: str
    amount: int = 1

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Token amount cannot be negative")