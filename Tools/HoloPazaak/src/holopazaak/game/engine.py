"""Pazaak game engine.

This module implements the complete game logic combining all vendor implementations:
- pazaak-eggborne: Turn management, win conditions, tie handling
- vue-pazaak: IGame.js - set/round structure, current player management
- pazaak-iron-ginger: sections.py - game loop, round resolution
- Java_Pazaak: Controller.java - card dealing, AI actions, win checking
- PazaakApp: store/index.js - round winner determination
- GetLucky33: Game.java - score checking, round management

References:
- vendor/pazaak-eggborne/src/scripts/ai.js: lines 1-560
- vendor/vue-pazaak/src/IGame.js: lines 1-162
- vendor/pazaak-iron-ginger/modules/primary/sections.py: lines 1-186
- vendor/Java_Pazaak/Controller/Controller.java: lines 1-212
- vendor/PazaakApp/src/store/index.js: lines 1-146
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

from holopazaak.game.card import (
    Card,
    CardType,
    apply_double_card_effect,
    apply_flip_card_effect,
    create_main_deck_card,
)
from holopazaak.game.player import Player, PlayerState

if TYPE_CHECKING:
    from holopazaak.ai.strategies import AIStrategy


class GamePhase(Enum):
    """Current phase of the game."""
    SETUP = auto()           # Before game starts
    ROUND_START = auto()     # Starting a new round
    TURN_START = auto()      # Drawing main deck card
    TURN_ACTION = auto()     # Player can play hand card
    TURN_DECISION = auto()   # Player decides to stand or end turn
    ROUND_END = auto()       # Round has ended
    MATCH_END = auto()       # Match has ended


class RoundResult(Enum):
    """Result of a round."""
    PLAYER1_WIN = auto()
    PLAYER2_WIN = auto()
    TIE = auto()
    IN_PROGRESS = auto()


@dataclass
class GameEvent:
    """An event that occurred in the game."""
    event_type: str
    player: str | None = None
    card: Card | None = None
    message: str = ""
    data: dict = field(default_factory=dict)


class PazaakGame:
    """The main Pazaak game engine.
    
    Implements the complete game logic with:
    - Main deck card dealing (1-10, 4 copies each)
    - Turn management with proper phase tracking
    - Round resolution with all win conditions
    - Match management (best of 5 sets)
    - Special card effects (double, flip, tiebreaker)
    - Event system for UI updates
    
    Based on the combined logic from all vendor Pazaak implementations.
    
    Win conditions (from PazaakApp store/index.js):
    1. Bust: Score over 20 = other player wins
    2. Fill Table: 9 cards without bust = automatic win
    3. Outscore: Both standing, higher score wins
    4. Tiebreaker: Tie with tiebreaker card = tiebreaker holder wins
    """
    
    WIN_SCORE: int = 20
    MAX_BOARD_SIZE: int = 9
    SETS_TO_WIN: int = 3

    def __init__(
        self,
        player1: Player,
        player2: Player,
        on_event: Callable[[GameEvent], None] | None = None,
    ):
        """Initialize the game.
        
        Args:
            player1: First player (usually human)
            player2: Second player (human or AI)
            on_event: Optional callback for game events
        """
        self.player1 = player1
        self.player2 = player2
        self.on_event = on_event
        
        # Game state
        self.current_player: Player = player1
        self.winner: Player | None = None
        self.round_winner: Player | None = None
        self.round_result: RoundResult = RoundResult.IN_PROGRESS
        self.phase: GamePhase = GamePhase.SETUP
        
        # Main deck (4 copies of 1-10, shuffled)
        # Based on PazaakApp dealer.js
        self.main_deck: list[Card] = []
        self._build_main_deck()
        
        # Turn tracking (from pazaak-eggborne)
        self.turn_number: int = 0
        self.round_number: int = 0
        
        # For tracking who goes first
        self.first_player: Player = player1

    def _build_main_deck(self):
        """Build and shuffle the main deck.
        
        From PazaakApp dealer.js: 4 copies of cards 1-10.
        """
        self.main_deck = []
        for value in range(1, 11):
            for _ in range(4):
                self.main_deck.append(create_main_deck_card(value))
        random.shuffle(self.main_deck)

    def _emit_event(self, event_type: str, **kwargs):
        """Emit a game event."""
        if self.on_event:
            event = GameEvent(event_type, **kwargs)
            self.on_event(event)

    def draw_main_deck_card(self) -> Card:
        """Draw a card from the main deck.
        
        From pazaak-iron-ginger deck_phase.
        """
        # Rebuild deck if empty
        if not self.main_deck:
            self._build_main_deck()
        
        return self.main_deck.pop()

    def get_opponent(self, player: Player) -> Player:
        """Get the opponent of a player."""
        return self.player2 if player == self.player1 else self.player1

    def start_game(self):
        """Start a new game/match.
        
        Based on pazaak-iron-ginger game() function setup.
        """
        self.player1.reset_game()
        self.player2.reset_game()
        self.winner = None
        self.round_number = 0
        
        # Coin flip for first player (pazaak-iron-ginger coin_flip)
        self.first_player = random.choice([self.player1, self.player2])
        
        self._emit_event("game_start", message=f"Game started! {self.first_player.name} goes first.")
        self.start_round()

    def start_round(self):
        """Start a new round.
        
        From vue-pazaak IGame.js newSet() and pazaak-iron-ginger game loop.
        """
        self.round_number += 1
        self.turn_number = 0
        self.round_winner = None
        self.round_result = RoundResult.IN_PROGRESS
        self.phase = GamePhase.ROUND_START
        
        # Reset players for new round
        self.player1.reset_round()
        self.player2.reset_round()
        
        # Rebuild and shuffle main deck
        self._build_main_deck()
        
        # Loser of previous round goes first, or first_player for first round
        # Based on pazaak-iron-ginger switch_order
        if self.round_winner:
            self.current_player = self.get_opponent(self.round_winner)
        else:
            self.current_player = self.first_player
        
        self._emit_event(
            "round_start",
            message=f"Round {self.round_number} started. {self.current_player.name}'s turn.",
            data={"round": self.round_number}
        )
        
        self.start_turn()

    def start_turn(self):
        """Start a new turn for the current player.
        
        From vue-pazaak IGame.js nextTurn() and pazaak-iron-ginger turns().
        """
        if self.phase in (GamePhase.ROUND_END, GamePhase.MATCH_END):
            return
        
        # Skip if player is standing
        if self.current_player.is_standing:
            # Check if both standing
            if self.player1.is_standing and self.player2.is_standing:
                self.resolve_round()
                return
            # Switch to other player
            self._switch_player()
            self.start_turn()
            return
        
        self.turn_number += 1
        self.phase = GamePhase.TURN_START
        self.current_player.played_card_this_turn = False
        
        # Auto-draw card at start of turn
        card = self.draw_main_deck_card()
        self.current_player.add_card_to_board(card)
        
        self._emit_event(
            "card_drawn",
            player=self.current_player.name,
            card=card,
            message=f"{self.current_player.name} drew {card}",
            data={"score": self.current_player.score}
        )
        
        # Check for bust immediately after draw
        if self.current_player.is_bust:
            self._emit_event(
                "bust",
                player=self.current_player.name,
                message=f"{self.current_player.name} busted with {self.current_player.score}!"
            )
            self.resolve_round()
            return
        
        # Check for full board (9 cards) - automatic win
        # From Java_Pazaak check() method
        if self.current_player.is_full:
            self._emit_event(
                "board_full",
                player=self.current_player.name,
                message=f"{self.current_player.name} filled the board without busting!"
            )
            self.round_winner = self.current_player
            self.resolve_round()
            return
        
        # Move to action phase
        self.phase = GamePhase.TURN_ACTION
        
        self._emit_event(
            "turn_start",
            player=self.current_player.name,
            message=f"{self.current_player.name}'s turn. Score: {self.current_player.score}",
            data={"score": self.current_player.score}
        )

    def play_hand_card(self, player: Player, card_index: int, flip_to_minus: bool = False) -> bool:
        """Play a card from the player's hand.
        
        From vue-pazaak IGame.js playCard() and pazaak-iron-ginger hand_phase.
        
        Args:
            player: The player playing the card
            card_index: Index of the card in the player's hand
            flip_to_minus: For FLIP cards, whether to use as minus
            
        Returns:
            True if card was played successfully
        """
        if self.phase != GamePhase.TURN_ACTION:
            return False
        
        if player != self.current_player:
            return False
        
        if player.played_card_this_turn:
            return False
        
        if not (0 <= card_index < len(player.hand)):
            return False
        
        card = player.hand[card_index]
        
        # Handle flip cards
        if card.card_type == CardType.FLIP:
            if flip_to_minus:
                card.is_flipped = True
        
        # Handle special card effects
        if card.card_type == CardType.DOUBLE:
            player.board = apply_double_card_effect(player.board)
            player.hand.pop(card_index)
            player.played_card_this_turn = True
            
            self._emit_event(
                "card_played",
                player=player.name,
                card=card,
                message=f"{player.name} played Double card!"
            )
            return True
        
        if card.card_type in (CardType.FLIP_TWO_FOUR, CardType.FLIP_THREE_SIX):
            player.board = apply_flip_card_effect(card, player.board)
            player.hand.pop(card_index)
            player.played_card_this_turn = True
            
            target_vals = "2&4" if card.card_type == CardType.FLIP_TWO_FOUR else "3&6"
            self._emit_event(
                "card_played",
                player=player.name,
                card=card,
                message=f"{player.name} flipped all {target_vals}!"
            )
            return True
        
        # Standard card play
        played_card = player.play_card_from_hand(card_index)
        if played_card:
            self._emit_event(
                "card_played",
                player=player.name,
                card=played_card,
                message=f"{player.name} played {played_card}",
                data={"score": player.score}
            )
            
            # Check for bust after playing
            if player.is_bust:
                self._emit_event(
                    "bust",
                    player=player.name,
                    message=f"{player.name} busted with {player.score}!"
                )
                self.resolve_round()
            
            return True
        
        return False

    def stand(self, player: Player):
        """Player chooses to stand.
        
        From vue-pazaak IGame.js stand() and pazaak-iron-ginger stay_check.
        """
        if player != self.current_player:
            return
        
        if player.is_standing:
            return
        
        player.stand()
        
        self._emit_event(
            "stand",
            player=player.name,
            message=f"{player.name} stands at {player.score}",
            data={"score": player.score}
        )
        
        self.end_turn()

    def end_turn(self):
        """End the current turn.
        
        From vue-pazaak IGame.js endTurn() and pazaak-iron-ginger rounds.
        """
        if self.phase in (GamePhase.ROUND_END, GamePhase.MATCH_END):
            return
        
        # Check for bust
        if self.current_player.is_bust:
            self.resolve_round()
            return
        
        # Check for full board
        if self.current_player.is_full:
            self.round_winner = self.current_player
            self.resolve_round()
            return
        
        self.current_player.end_turn()
        
        # Check if both players are standing
        if self.player1.is_standing and self.player2.is_standing:
            self.resolve_round()
            return
        
        # Switch to other player
        self._switch_player()
        
        self._emit_event(
            "turn_end",
            message=f"Turn ended. {self.current_player.name}'s turn.",
        )
        
        # Start next turn
        self.start_turn()

    def _switch_player(self):
        """Switch to the other player."""
        if self.current_player == self.player1:
            self.current_player = self.player2
        else:
            self.current_player = self.player1

    def resolve_round(self):
        """Resolve the round and determine winner.
        
        Based on PazaakApp checkBust/checkFillTable/checkOutScore and
        Java_Pazaak Controller.java check() method.
        """
        if self.phase == GamePhase.ROUND_END:
            return
        
        self.phase = GamePhase.ROUND_END
        
        p1_score = self.player1.score
        p2_score = self.player2.score
        
        # Determine winner if not already set
        if self.round_winner is None:
            # Check for bust
            if self.player1.is_bust and not self.player2.is_bust:
                self.round_winner = self.player2
                self.round_result = RoundResult.PLAYER2_WIN
            elif self.player2.is_bust and not self.player1.is_bust:
                self.round_winner = self.player1
                self.round_result = RoundResult.PLAYER1_WIN
            elif self.player1.is_bust and self.player2.is_bust:
                # Both bust - based on who busted first (current player)
                self.round_winner = self.get_opponent(self.current_player)
                self.round_result = (
                    RoundResult.PLAYER1_WIN
                    if self.round_winner == self.player1
                    else RoundResult.PLAYER2_WIN
                )
            else:
                # Compare scores (both must be standing or at 20)
                if p1_score > p2_score:
                    self.round_winner = self.player1
                    self.round_result = RoundResult.PLAYER1_WIN
                elif p2_score > p1_score:
                    self.round_winner = self.player2
                    self.round_result = RoundResult.PLAYER2_WIN
                else:
                    # Tie - check for tiebreaker
                    if self.player1.has_tiebreaker and not self.player2.has_tiebreaker:
                        self.round_winner = self.player1
                        self.round_result = RoundResult.PLAYER1_WIN
                    elif self.player2.has_tiebreaker and not self.player1.has_tiebreaker:
                        self.round_winner = self.player2
                        self.round_result = RoundResult.PLAYER2_WIN
                    else:
                        self.round_winner = None
                        self.round_result = RoundResult.TIE
        else:
            # Round winner was set (full board, etc.)
            self.round_result = (
                RoundResult.PLAYER1_WIN
                if self.round_winner == self.player1
                else RoundResult.PLAYER2_WIN
            )
        
        # Award set to winner
        if self.round_winner:
            self.round_winner.sets_won += 1
        
        # Emit round result
        if self.round_result == RoundResult.TIE:
            self._emit_event(
                "round_end",
                message=f"Round {self.round_number} is a tie! ({p1_score} - {p2_score})",
                data={
                    "result": "tie",
                    "p1_score": p1_score,
                    "p2_score": p2_score,
                    "p1_sets": self.player1.sets_won,
                    "p2_sets": self.player2.sets_won,
                }
            )
        else:
            winner_name = self.round_winner.name if self.round_winner else "Unknown"
            self._emit_event(
                "round_end",
                player=winner_name,
                message=f"Round {self.round_number} winner: {winner_name}! ({p1_score} - {p2_score})",
                data={
                    "result": "win",
                    "winner": winner_name,
                    "p1_score": p1_score,
                    "p2_score": p2_score,
                    "p1_sets": self.player1.sets_won,
                    "p2_sets": self.player2.sets_won,
                }
            )
        
        # Check for match end
        if self.player1.sets_won >= self.SETS_TO_WIN:
            self.winner = self.player1
            self.phase = GamePhase.MATCH_END
            self._emit_event(
                "match_end",
                player=self.player1.name,
                message=f"{self.player1.name} wins the match!",
                data={"winner": self.player1.name}
            )
        elif self.player2.sets_won >= self.SETS_TO_WIN:
            self.winner = self.player2
            self.phase = GamePhase.MATCH_END
            self._emit_event(
                "match_end",
                player=self.player2.name,
                message=f"{self.player2.name} wins the match!",
                data={"winner": self.player2.name}
            )

    @property
    def is_round_over(self) -> bool:
        """Check if the current round is over."""
        return self.phase in (GamePhase.ROUND_END, GamePhase.MATCH_END)

    @property
    def is_game_over(self) -> bool:
        """Check if the match is over."""
        return self.phase == GamePhase.MATCH_END

    def can_continue_round(self) -> bool:
        """Check if another round can be played."""
        return (
            self.phase == GamePhase.ROUND_END
            and not self.is_game_over
        )

    def get_game_state(self) -> dict:
        """Get the current game state as a dictionary.
        
        Useful for multiplayer synchronization and AI decision making.
        """
        return {
            "phase": self.phase.name,
            "round": self.round_number,
            "turn": self.turn_number,
            "current_player": self.current_player.name,
            "player1": {
                "name": self.player1.name,
                "score": self.player1.score,
                "sets_won": self.player1.sets_won,
                "is_standing": self.player1.is_standing,
                "is_bust": self.player1.is_bust,
                "hand_size": len(self.player1.hand),
                "board_size": len(self.player1.board),
            },
            "player2": {
                "name": self.player2.name,
                "score": self.player2.score,
                "sets_won": self.player2.sets_won,
                "is_standing": self.player2.is_standing,
                "is_bust": self.player2.is_bust,
                "hand_size": len(self.player2.hand),
                "board_size": len(self.player2.board),
            },
            "winner": self.winner.name if self.winner else None,
            "round_winner": self.round_winner.name if self.round_winner else None,
        }
