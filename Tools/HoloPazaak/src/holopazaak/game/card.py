"""Card system for Pazaak.

This module implements all card types found across vendor Pazaak implementations:
- Main deck cards (1-10, drawn each turn)
- Plus cards (+1 to +6)
- Minus cards (-1 to -6)  
- Flip cards (±1 to ±6, can toggle between + and -)
- Double cards (doubles the last card played) - from PazaakApp
- Tiebreaker cards (wins on ties) - from PazaakApp
- Flip 3&6 cards (flips all 3s and 6s on board) - from Java_Pazaak

References:
- vendor/pazaak-eggborne/src/scripts/characters.js: lines 16-51 (prize cards)
- vendor/vue-pazaak/src/ICard.js: lines 1-11 (card class)
- vendor/Java_Pazaak/Domain/Card.java: lines 1-99 (special cards)
- vendor/PazaakApp/src/utils/CardHelper.js: lines 1-95 (card helper functions)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable


class CardType(Enum):
    """All card types in Pazaak.
    
    Based on implementations from:
    - pazaak-eggborne: +, -, ± types
    - Java_Pazaak: flip specific values, double, special cards
    - PazaakApp: double, tiebreaker cards
    """
    MAIN = auto()       # Main deck cards (1-10), drawn each turn
    PLUS = auto()       # Side deck +1 to +6
    MINUS = auto()      # Side deck -1 to -6
    FLIP = auto()       # Side deck ±1 to ±6 (can flip sign)
    DOUBLE = auto()     # Doubles the value of the last card played
    TIEBREAKER = auto() # Acts as +1/-1 but wins on ties
    FLIP_TWO_FOUR = auto()   # Flips all 2s and 4s on the board
    FLIP_THREE_SIX = auto()  # Flips all 3s and 6s on the board
    PLUS_MINUS_3_6 = auto()  # +3/-6 card from KOTOR 1


class CardAction(Enum):
    """Card action states for flip cards."""
    PLUS = auto()
    MINUS = auto()
    NEUTRAL = auto()


@dataclass
class Card:
    """A Pazaak card.
    
    This implements the union of card functionality from all vendor projects:
    - pazaak-eggborne: Basic +/- and ± cards with value
    - vue-pazaak: isChangeable flag for flip cards
    - Java_Pazaak: Complex card IDs and special abilities
    - PazaakApp: cardType and cardValue structure
    
    Attributes:
        name: Display name of the card
        value: Absolute value of the card (1-10)
        card_type: Type of card (MAIN, PLUS, MINUS, FLIP, etc.)
        is_flipped: For FLIP cards, whether currently negative
        action: Current action state for flip cards
        flip_targets: For FLIP_TWO_FOUR/THREE_SIX, which values to flip
        is_frozen: If card value is locked (from GetLucky33)
        is_hidden: If card is hidden from view
        is_used: If card has been played from hand
        is_face_down: If card is shown face down (opponent's hidden cards)
    """
    name: str
    value: int
    card_type: CardType
    is_flipped: bool = False
    action: CardAction = CardAction.NEUTRAL
    flip_targets: tuple[int, ...] = field(default_factory=tuple)
    is_frozen: bool = False
    is_hidden: bool = False
    is_used: bool = False
    is_face_down: bool = False

    def __post_init__(self):
        """Initialize action based on card type."""
        if self.card_type == CardType.PLUS:
            self.action = CardAction.PLUS
        elif self.card_type == CardType.MINUS:
            self.action = CardAction.MINUS
        elif self.card_type == CardType.FLIP:
            self.action = CardAction.MINUS if self.is_flipped else CardAction.PLUS
        elif self.card_type in (CardType.FLIP_TWO_FOUR, CardType.FLIP_THREE_SIX):
            self.action = CardAction.NEUTRAL
            if self.card_type == CardType.FLIP_TWO_FOUR:
                self.flip_targets = (2, 4)
            else:
                self.flip_targets = (3, 6)

    @property
    def display_value(self) -> int:
        """Get the effective value for scoring.
        
        Based on interpretArrayScore from PazaakApp CardHelper.js
        """
        if self.card_type == CardType.FLIP:
            return -abs(self.value) if self.is_flipped else abs(self.value)
        elif self.card_type == CardType.MINUS:
            return -abs(self.value)
        elif self.card_type in (CardType.PLUS, CardType.MAIN, CardType.TIEBREAKER):
            return abs(self.value)
        elif self.card_type == CardType.DOUBLE:
            # Double card's value is determined by the card it doubles
            return 0  # Handled specially in game logic
        elif self.card_type in (CardType.FLIP_TWO_FOUR, CardType.FLIP_THREE_SIX):
            return 0  # These cards don't add to score directly
        elif self.card_type == CardType.PLUS_MINUS_3_6:
            # +3 or -6 card
            return 3 if not self.is_flipped else -6
        return self.value

    def flip(self) -> bool:
        """Flip the card sign if it's a FLIP type.
        
        Returns True if the card was flipped, False otherwise.
        """
        if self.card_type == CardType.FLIP:
            self.is_flipped = not self.is_flipped
            self.action = CardAction.MINUS if self.is_flipped else CardAction.PLUS
            return True
        elif self.card_type == CardType.PLUS_MINUS_3_6:
            self.is_flipped = not self.is_flipped
            return True
        return False

    def set_action(self, action: CardAction):
        """Set the card action (for flip cards)."""
        if self.card_type == CardType.FLIP:
            self.action = action
            self.is_flipped = action == CardAction.MINUS

    def copy(self) -> Card:
        """Create a copy of this card."""
        return Card(
            name=self.name,
            value=self.value,
            card_type=self.card_type,
            is_flipped=self.is_flipped,
            action=self.action,
            flip_targets=self.flip_targets,
            is_frozen=self.is_frozen,
            is_hidden=self.is_hidden,
            is_used=self.is_used,
        )

    def __str__(self) -> str:
        """String representation based on pazaak-eggborne display format."""
        if self.is_face_down:
            return "?"
        val_str = str(abs(self.value))
        if self.card_type == CardType.PLUS:
            return f"+{val_str}"
        elif self.card_type == CardType.MINUS:
            return f"-{val_str}"
        elif self.card_type == CardType.FLIP:
            if self.is_flipped:
                return f"±{val_str}(-)"
            return f"±{val_str}(+)"
        elif self.card_type == CardType.DOUBLE:
            return "2x"
        elif self.card_type == CardType.TIEBREAKER:
            return f"T±{val_str}"
        elif self.card_type == CardType.FLIP_TWO_FOUR:
            return "F2&4"
        elif self.card_type == CardType.FLIP_THREE_SIX:
            return "F3&6"
        elif self.card_type == CardType.PLUS_MINUS_3_6:
            return "+3/-6" if not self.is_flipped else "-6/+3"
        return val_str

    def __repr__(self) -> str:
        return f"Card({self.name!r}, {self.value}, {self.card_type.name})"


def create_main_deck_card(value: int) -> Card:
    """Create a main deck card (1-10).
    
    Based on dealer.js from PazaakApp: main deck has 4 copies of each 1-10.
    """
    return Card(f"Main {value}", value, CardType.MAIN)


def create_plus_card(value: int) -> Card:
    """Create a plus side deck card (+1 to +6)."""
    return Card(f"+{value}", value, CardType.PLUS)


def create_minus_card(value: int) -> Card:
    """Create a minus side deck card (-1 to -6)."""
    return Card(f"-{value}", value, CardType.MINUS)


def create_flip_card(value: int) -> Card:
    """Create a flip side deck card (±1 to ±6)."""
    return Card(f"±{value}", value, CardType.FLIP)


def create_double_card() -> Card:
    """Create a double card that doubles the last played card.
    
    From PazaakApp CardHelper.js doubleCardValue function.
    """
    return Card("Double", 0, CardType.DOUBLE)


def create_tiebreaker_card(value: int = 1) -> Card:
    """Create a tiebreaker card that wins on ties.
    
    Acts as +/-1 but wins ties. From PazaakApp CardHelper.js.
    """
    return Card(f"Tiebreaker {value}", value, CardType.TIEBREAKER)


def create_flip_two_four_card() -> Card:
    """Create a card that flips all 2s and 4s on the board.
    
    From Java_Pazaak Controller.java cardAction method.
    """
    return Card("Flip 2&4", 24, CardType.FLIP_TWO_FOUR)


def create_flip_three_six_card() -> Card:
    """Create a card that flips all 3s and 6s on the board.
    
    From Java_Pazaak Controller.java cardAction method.
    """
    return Card("Flip 3&6", 36, CardType.FLIP_THREE_SIX)


def get_all_side_deck_cards() -> list[Card]:
    """Get all available side deck cards.
    
    Returns a list of all possible side deck card types.
    Based on pazaak-iron-ginger cards.py side_deck range.
    """
    cards: list[Card] = []
    
    # Plus cards +1 to +6
    for val in range(1, 7):
        cards.append(create_plus_card(val))
    
    # Minus cards -1 to -6
    for val in range(1, 7):
        cards.append(create_minus_card(val))
    
    # Flip cards ±1 to ±6
    for val in range(1, 7):
        cards.append(create_flip_card(val))
    
    # Special cards (less common, from Java_Pazaak)
    cards.append(create_double_card())
    cards.append(create_tiebreaker_card(1))
    cards.append(create_flip_two_four_card())
    cards.append(create_flip_three_six_card())
    
    return cards


def apply_flip_card_effect(flip_card: Card, board: list[Card]) -> list[Card]:
    """Apply a flip card effect to the board.
    
    Based on Java_Pazaak Controller.java cardAction for flip cards (ids 42-45).
    
    Args:
        flip_card: The flip card being played (FLIP_TWO_FOUR or FLIP_THREE_SIX)
        board: The current board cards
        
    Returns:
        Modified board with flipped cards
    """
    if flip_card.card_type not in (CardType.FLIP_TWO_FOUR, CardType.FLIP_THREE_SIX):
        return board
    
    targets = flip_card.flip_targets
    new_board: list[Card] = []
    
    for card in board:
        if abs(card.value) in targets and not card.is_frozen:
            # Flip the sign
            new_card = card.copy()
            if new_card.card_type == CardType.MAIN:
                # Convert to plus/minus and flip
                new_card.value = -new_card.value
            elif new_card.card_type == CardType.PLUS:
                new_card.card_type = CardType.MINUS
                new_card.value = -abs(new_card.value)
            elif new_card.card_type == CardType.MINUS:
                new_card.card_type = CardType.PLUS
                new_card.value = abs(new_card.value)
            new_board.append(new_card)
        else:
            new_board.append(card)
    
    return new_board


def apply_double_card_effect(board: list[Card]) -> list[Card]:
    """Apply a double card effect to the board.
    
    Doubles the value of the last non-special card played.
    Based on PazaakApp CardHelper.js doubleCardValue.
    """
    if not board:
        return board
    
    new_board = list(board)
    # Find the last non-special card
    for i in range(len(new_board) - 1, -1, -1):
        card = new_board[i]
        if card.card_type in (CardType.MAIN, CardType.PLUS, CardType.MINUS, CardType.FLIP):
            new_card = card.copy()
            new_card.value = card.value * 2
            new_card.name = f"2x{card.name}"
            new_board[i] = new_card
            break
    
    return new_board
