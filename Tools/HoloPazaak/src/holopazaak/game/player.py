"""Player class for Pazaak.

This module implements the player functionality combining features from:
- pazaak-eggborne: Turn status tracking, playedCard flag
- vue-pazaak: IPlayer.js - player state with rounds, hand management
- pazaak-iron-ginger: Player attributes (gs/rs for game/round score, state)
- Java_Pazaak: Player.java - deck/table management, score calculation
- PazaakApp: store/player.js - card arrays, standing state

References:
- vendor/vue-pazaak/src/IPlayer.js: lines 1-27
- vendor/pazaak-iron-ginger/modules/primary/pazaak.py: lines 20-45
- vendor/Java_Pazaak/Domain/Player.java: lines 1-52
- vendor/PazaakApp/src/store/player.js
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from holopazaak.game.card import Card


class PlayerState(Enum):
    """Player state in a round.
    
    Based on pazaak-iron-ginger state attribute (None, 'stay', 'bust').
    """
    PLAYING = auto()   # Still in the round
    STANDING = auto()  # Chose to stand
    BUST = auto()      # Score exceeded 20


@dataclass
class PlayerStats:
    """Player statistics tracking.
    
    Tracks comprehensive stats across games for the hall of fame feature
    inspired by pazaak-eggborne.
    """
    total_games: int = 0
    games_won: int = 0
    games_lost: int = 0
    games_tied: int = 0
    total_sets: int = 0
    sets_won: int = 0
    perfect_20s: int = 0   # Times player hit exactly 20
    comebacks: int = 0     # Won after being down 0-2
    nine_card_wins: int = 0  # Won by filling the board


class Player:
    """A Pazaak player.
    
    Combines player functionality from all vendor implementations:
    - vue-pazaak: score, rounds, hand management
    - pazaak-iron-ginger: gs (game score/sets won), rs (round score), state
    - Java_Pazaak: deck/table arrays, total calculation
    - PazaakApp: isStanding, isPlayedCard, cardArray
    
    Attributes:
        name: Player display name
        is_ai: Whether this player is AI controlled
        hand: Current hand of side deck cards (4 cards)
        board: Cards played to the board this round (max 9)
        sideboard: Full side deck (10 cards)
        sets_won: Number of sets won this match (gs in iron-ginger)
        state: Current player state (PLAYING, STANDING, BUST)
        played_card_this_turn: Whether a hand card was played this turn
        has_tiebreaker: Whether player has an active tiebreaker
        stats: Player statistics
    """
    
    WIN_SCORE: int = 20
    MAX_BOARD_SIZE: int = 9
    HAND_SIZE: int = 4
    SIDE_DECK_SIZE: int = 10
    
    def __init__(self, name: str, is_ai: bool = False):
        self.name = name
        self.is_ai = is_ai
        self.hand: list[Card] = []
        self.board: list[Card] = []
        self.sideboard: list[Card] = []
        self.sets_won: int = 0
        self.state: PlayerState = PlayerState.PLAYING
        self.played_card_this_turn: bool = False
        self.has_tiebreaker: bool = False
        self.stats: PlayerStats = PlayerStats()

    @property
    def score(self) -> int:
        """Calculate total score from board cards.
        
        Based on Java_Pazaak Player.java calculateTotal() and
        PazaakApp interpretArrayScore().
        """
        return sum(c.display_value for c in self.board)

    @property
    def is_standing(self) -> bool:
        """Check if player is standing."""
        return self.state == PlayerState.STANDING

    @property
    def is_bust(self) -> bool:
        """Check if player is bust (score > 20).
        
        Auto-updates state if bust detected.
        """
        if self.score > self.WIN_SCORE:
            self.state = PlayerState.BUST
            return True
        return False

    @property
    def is_full(self) -> bool:
        """Check if board is full (9 cards).
        
        Based on Java_Pazaak check for getTableLength() == 9.
        """
        return len(self.board) >= self.MAX_BOARD_SIZE

    @property
    def is_at_20(self) -> bool:
        """Check if player has exactly 20."""
        return self.score == self.WIN_SCORE

    @property
    def can_act(self) -> bool:
        """Check if player can still take actions."""
        return self.state == PlayerState.PLAYING and not self.is_bust

    def reset_round(self):
        """Reset for a new round.
        
        Based on vue-pazaak IGame.js newSet() and pazaak-iron-ginger reset.
        """
        self.board = []
        self.state = PlayerState.PLAYING
        self.played_card_this_turn = False
        self.has_tiebreaker = False
        
        # Redraw hand from sideboard
        if self.sideboard:
            self.draw_hand_from_sideboard()

    def reset_game(self):
        """Reset for a new game/match.
        
        Based on Java_Pazaak Player.java restart().
        """
        self.sets_won = 0
        self.hand = []
        self.reset_round()

    def draw_hand_from_sideboard(self):
        """Draw 4 cards from sideboard for the hand.
        
        Based on vue-pazaak IPlayer.js getHand().
        """
        if len(self.sideboard) >= self.HAND_SIZE:
            # Random sample without replacement
            indices = random.sample(range(len(self.sideboard)), self.HAND_SIZE)
            self.hand = [self.sideboard[i].copy() for i in indices]
        else:
            self.hand = [card.copy() for card in self.sideboard]

    def add_card_to_board(self, card: Card):
        """Add a card to the board.
        
        Based on Java_Pazaak Player.java addTableCard().
        """
        self.board.append(card)
        
        # Check for bust after adding
        if self.score > self.WIN_SCORE:
            self.state = PlayerState.BUST
        
        # Track perfect 20s
        if self.score == self.WIN_SCORE:
            self.stats.perfect_20s += 1

    def play_card_from_hand(self, index: int) -> Card | None:
        """Play a card from hand to the board.
        
        Based on vue-pazaak IGame.js playCard().
        
        Returns the played card or None if invalid.
        """
        if not (0 <= index < len(self.hand)):
            return None
        
        if self.played_card_this_turn:
            return None  # Only one card per turn
        
        card = self.hand.pop(index)
        self.add_card_to_board(card)
        self.played_card_this_turn = True
        
        # Track tiebreaker
        from holopazaak.game.card import CardType
        if card.card_type == CardType.TIEBREAKER:
            self.has_tiebreaker = True
        
        return card

    def stand(self):
        """Stand with current score.
        
        Based on vue-pazaak IGame.js stand().
        """
        self.state = PlayerState.STANDING

    def end_turn(self):
        """End the current turn."""
        self.played_card_this_turn = False

    def get_cards_by_value(self, value: int) -> list[Card]:
        """Get all board cards with a specific absolute value.
        
        Used for flip card effects from Java_Pazaak.
        """
        return [c for c in self.board if abs(c.value) == value]

    def has_minus_cards(self) -> bool:
        """Check if player has minus cards in hand.
        
        Based on pazaak-eggborne getHighestMinusValue check.
        """
        from holopazaak.game.card import CardType
        return any(
            c.card_type in (CardType.MINUS, CardType.FLIP)
            for c in self.hand
        )

    def get_highest_minus_value(self) -> int:
        """Get the highest minus value available in hand.
        
        From pazaak-eggborne ai.js getHighestMinusValue().
        Used to determine safe drawing threshold.
        """
        from holopazaak.game.card import CardType
        highest = 0
        for card in self.hand:
            if card.card_type == CardType.MINUS:
                highest = max(highest, abs(card.value))
            elif card.card_type == CardType.FLIP:
                highest = max(highest, abs(card.value))
        return highest

    def can_reach_score(self, target: int) -> tuple[bool, int | None]:
        """Check if player can reach a target score with hand cards.
        
        Returns (can_reach, card_index) tuple.
        Based on pazaak-eggborne checkHandPluses logic.
        """
        from holopazaak.game.card import CardType
        
        for i, card in enumerate(self.hand):
            if card.card_type == CardType.PLUS:
                if self.score + card.value == target:
                    return True, i
            elif card.card_type == CardType.MINUS:
                if self.score + card.display_value == target:
                    return True, i
            elif card.card_type == CardType.FLIP:
                # Check both positive and negative
                if self.score + abs(card.value) == target:
                    return True, i
                if self.score - abs(card.value) == target:
                    return True, i
        return False, None

    def get_best_card_to_avoid_bust(self) -> int | None:
        """Find the best card to play to get under 20.
        
        Based on pazaak-iron-ginger choice_mod logic.
        """
        from holopazaak.game.card import CardType
        
        if self.score <= self.WIN_SCORE:
            return None
        
        best_idx: int | None = None
        best_score = self.score
        
        for i, card in enumerate(self.hand):
            potential_score = self.score
            
            if card.card_type == CardType.MINUS:
                potential_score = self.score + card.display_value
            elif card.card_type == CardType.FLIP:
                # Use as minus
                potential_score = self.score - abs(card.value)
            else:
                continue
            
            if potential_score <= self.WIN_SCORE:
                if best_idx is None or potential_score > best_score:
                    best_score = potential_score
                    best_idx = i
        
        return best_idx

    def __repr__(self) -> str:
        return f"Player({self.name!r}, score={self.score}, state={self.state.name})"
