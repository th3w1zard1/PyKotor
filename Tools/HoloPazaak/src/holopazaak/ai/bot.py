"""AI player implementation for Pazaak.

This module provides the AIPlayer class that uses different AI strategies
based on opponent profiles. It combines functionality from:
- pazaak-eggborne: Character-specific strategies
- pazaak-iron-ginger: Opponent profiles and difficulty
- Java_Pazaak: AI decision making

References:
- vendor/pazaak-eggborne/src/scripts/characters.js: lines 1-750
- vendor/pazaak-iron-ginger/modules/secondary/comp.py: lines 1-363
- vendor/Java_Pazaak/Controller/Controller.java: lines 122-212
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from holopazaak.ai.strategies import (
    AIAction,
    AIDecision,
    AIStrategy,
    EasyAI,
    ExpertAI,
    HardAI,
    MasterAI,
    NormalAI,
)
from holopazaak.game.card import Card, CardType
from holopazaak.game.player import Player

if TYPE_CHECKING:
    from holopazaak.data.opponents import OpponentDifficulty, OpponentProfile
    from holopazaak.game.engine import PazaakGame


def get_strategy_for_profile(profile: OpponentProfile) -> AIStrategy:
    """Get the appropriate AI strategy for an opponent profile.
    
    Maps opponent profiles to AI strategies based on their difficulty
    and stand_at/tie_chance settings.
    """
    from holopazaak.data.opponents import OpponentDifficulty
    
    difficulty = profile.difficulty
    stand_at = profile.stand_at
    tie_chance = profile.tie_chance
    
    if difficulty == OpponentDifficulty.NOVICE:
        return EasyAI(stand_threshold=15)
    elif difficulty == OpponentDifficulty.EASY:
        return EasyAI(stand_threshold=stand_at)
    elif difficulty == OpponentDifficulty.NORMAL:
        return NormalAI(stand_threshold=stand_at)
    elif difficulty == OpponentDifficulty.HARD:
        return HardAI(stand_at=stand_at, tie_accept_chance=tie_chance)
    elif difficulty == OpponentDifficulty.EXPERT:
        return ExpertAI()
    elif difficulty == OpponentDifficulty.MASTER:
        return MasterAI(stand_at=stand_at, tie_accept_chance=tie_chance)
    else:
        return NormalAI(stand_threshold=stand_at)


class AIPlayer(Player):
    """An AI-controlled Pazaak player.
    
    Extends the base Player class with AI decision-making capabilities.
    Uses different strategies based on the opponent profile's difficulty.
    
    Attributes:
        profile: The opponent profile with character info and settings
        strategy: The AI strategy used for decisions
    """
    
    def __init__(self, profile: OpponentProfile):
        """Initialize the AI player.
        
        Args:
            profile: The opponent profile to use
        """
        super().__init__(profile.name, is_ai=True)
        self.profile = profile
        self.strategy = get_strategy_for_profile(profile)
        
        # Setup the sideboard from profile
        self._setup_sideboard()
    
    def _setup_sideboard(self):
        """Setup the sideboard from the profile configuration.
        
        Converts the profile's sideboard tuples to Card objects.
        """
        self.sideboard = []
        
        for value, card_type in self.profile.sideboard:
            actual_value = value
            
            # Adjust value based on card type
            if card_type == CardType.MINUS:
                actual_value = -abs(value)
            elif card_type == CardType.FLIP:
                actual_value = abs(value)
            
            # Create the card
            if card_type == CardType.PLUS:
                name = f"+{value}"
            elif card_type == CardType.MINUS:
                name = f"-{value}"
            elif card_type == CardType.FLIP:
                name = f"±{value}"
            elif card_type == CardType.DOUBLE:
                name = "Double"
                actual_value = 0
            elif card_type == CardType.TIEBREAKER:
                name = f"Tiebreaker {value}"
            elif card_type == CardType.FLIP_TWO_FOUR:
                name = "Flip 2&4"
                actual_value = 24
            elif card_type == CardType.FLIP_THREE_SIX:
                name = "Flip 3&6"
                actual_value = 36
            else:
                name = f"Card {value}"
            
            card = Card(name, actual_value, card_type)
            self.sideboard.append(card)
        
        # Ensure we have at least 10 cards (pad with basic plus cards)
        while len(self.sideboard) < 10:
            val = (len(self.sideboard) % 6) + 1  # 1-6 cycling
            self.sideboard.append(Card(f"+{val}", val, CardType.PLUS))
    
    def decide_move(self, game: PazaakGame) -> tuple[str, int | None]:
        """Decide the next move using the AI strategy.
        
        This is the main interface called by the game UI.
        
        Args:
            game: The current game state
            
        Returns:
            A tuple of (action_type, card_index) where:
            - action_type is "play_card", "stand", or "end_turn"
            - card_index is the hand card index (for play_card) or None
        """
        decision = self.strategy.decide(game, self)
        
        # Handle flip cards - if flip_to_minus is set, flip the card first
        if decision.action == AIAction.PLAY_CARD and decision.card_index is not None:
            if decision.flip_to_minus and decision.card_index < len(self.hand):
                card = self.hand[decision.card_index]
                if card.card_type == CardType.FLIP:
                    card.is_flipped = True
        
        # Convert AIAction to string format expected by UI
        if decision.action == AIAction.PLAY_CARD:
            return ("play_card", decision.card_index)
        elif decision.action == AIAction.STAND:
            return ("stand", None)
        else:
            return ("end_turn", None)
    
    def get_phrase(self, event: str) -> str:
        """Get a character phrase for a game event.
        
        Args:
            event: The event type (chosen, play, stand, win_round, etc.)
            
        Returns:
            The appropriate phrase for the character
        """
        phrases = self.profile.phrases
        
        phrase_map = {
            "chosen": phrases.chosen,
            "play": phrases.play,
            "stand": phrases.stand,
            "win_round": phrases.win_round,
            "lose_round": phrases.lose_round,
            "win_game": phrases.win_game,
            "lose_game": phrases.lose_game,
        }
        
        return phrase_map.get(event, "")
    
    def __repr__(self) -> str:
        return f"AIPlayer({self.profile.name!r}, difficulty={self.profile.difficulty.name})"
