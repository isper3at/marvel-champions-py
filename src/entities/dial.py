from dataclasses import dataclass

@dataclass(frozen=True)
class Dial:
    """
    Dial entity - represents a dial on a card.
    
    Attributes:
        value: Current value of the dial
        min_value: Minimum value of the dial
        max_value: Maximum value of the dial
    """
    value: int

    def __post_init__(self):
        if not (self.min_value <= self.value <= self.max_value):
            raise ValueError("Dial value must be within min and max bounds")
        
    def increase(self, amount: int = 1) -> 'Dial':
        """Return new Dial with increased value"""
        new_value = self.value + amount
        return Dial(value=new_value)
    
    def decrease(self, amount: int = 1) -> 'Dial':
        """Return new Dial with decreased value"""
        new_value = self.value - amount
        return Dial(value=new_value)