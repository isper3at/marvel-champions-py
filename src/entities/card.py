from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class Card:
    """
    A single card definition in Marvel Champions.
    
    Card is a minimal representation of a card that primarily serves as
    an identifier and display medium. It does NOT contain game rules,
    costs, or effects - those are stored externally (e.g., in MarvelCDB).
    
    This design philosophy:
    - Keep entities simple and serializable
    - Store full card metadata in external sources (MarvelCDB)
    - Use codes to reference cards when needed
    - Store minimal UI data (name, text for accessibility)
    
    Attributes:
        code: Unique card identifier (e.g., "01001a")
              Format is typically set/number/letter per MarvelCDB convention
        name: Display name for the card (required for accessibility)
        text: Card text/description (for screen readers and help)
        created_at: When this card was first registered
        updated_at: When card data was last synchronized with source
    
    Architecture:
    - Entity: This class (pure data)
    - Interactor: CardInteractor handles import/sync logic
    - Boundary: MarvelCDB gateway fetches authoritative data
    - Repository: Stores cards in database for quick lookup
    
    Example:
        >>> card = Card(
        ...     code='01001a',
        ...     name='Spider-Man',
        ...     text='Hero - Can spend resource, flip to alter ego'
        ... )
        >>> assert card.code == '01001a'
        >>> # Cards are immutable - no modifications needed
    """
    code: str  # Unique card identifier (e.g., "01001a")
    name: str  # Display name (required for accessibility)
    text: Optional[str] = None  # Card text for accessibility/help
    
    # Audit trail for tracking synchronization with external sources
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """
        Validate card invariants.
        
        Ensures that code and name are present, as these are the minimum
        required for identifying and displaying a card.
        
        Raises:
            ValueError: If code or name is empty
        """
        if not self.code:
            raise ValueError("Card code cannot be empty")
        if not self.name:
            raise ValueError("Card name cannot be empty")