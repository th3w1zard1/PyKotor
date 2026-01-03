"""AI strategies for Pazaak.

This module implements multiple AI difficulty levels ported from all vendor projects:
- Easy: Simple threshold-based AI (from vue-pazaak ai.js)
- Normal: Basic strategic AI (from pazaak-iron-ginger comp.py)
- Hard: Complex AI with tie acceptance and safe-to-draw logic (from pazaak-eggborne ai.js)
- Expert: Advanced strategic AI with lookahead (from Java_Pazaak Controller.java)
- Master: Optimal play AI combining best strategies

Each AI uses different approaches to:
1. Deciding when to stand
2. Choosing which hand cards to play
3. Handling bust situations
4. Responding to opponent's state

References:
- vendor/vue-pazaak/src/ai.js: lines 1-56 (easy AI)
- vendor/pazaak-iron-ginger/modules/secondary/comp.py: lines 1-363 (normal AI)
- vendor/pazaak-eggborne/src/scripts/ai.js: lines 1-560 (hard AI)
- vendor/Java_Pazaak/Controller/Controller.java: lines 122-212 (expert AI)
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from holopazaak.game.card import Card
    from holopazaak.game.engine import PazaakGame
    from holopazaak.game.player import Player


class AIAction(Enum):
    """Possible AI actions."""
    PLAY_CARD = auto()    # Play a card from hand
    STAND = auto()        # Stand with current score
    END_TURN = auto()     # End turn without playing


@dataclass
class AIDecision:
    """An AI decision with action and optional card index."""
    action: AIAction
    card_index: int | None = None
    flip_to_minus: bool = False  # For flip cards


class AIStrategy(ABC):
    """Base class for AI strategies."""
    
    name: str = "Base AI"
    description: str = "Base AI strategy"
    
    @abstractmethod
    def decide(self, game: PazaakGame, player: Player) -> AIDecision:
        """Make a decision for the given player.
        
        Args:
            game: The current game state
            player: The AI player making the decision
            
        Returns:
            An AIDecision with the chosen action
        """
        ...


class EasyAI(AIStrategy):
    """Simple threshold-based AI from vue-pazaak.
    
    Strategy:
    - Stands at score >= 17 if no good card to play
    - Plays card to reach score > 16 if possible
    - Very simple card selection
    
    Reference: vendor/vue-pazaak/src/ai.js lines 1-56
    """
    
    name = "Easy"
    description = "Simple AI that stands at 17+ and makes basic card choices"
    
    def __init__(self, stand_threshold: int = 17):
        self.stand_threshold = stand_threshold
    
    def decide(self, game: PazaakGame, player: Player) -> AIDecision:
        from holopazaak.game.card import CardType
        
        score = player.score
        
        # Automatic stand at 20
        if score == 20:
            return AIDecision(AIAction.STAND)
        
        # Collect potential scores from each card
        best_card_idx: int | None = None
        best_score = score
        use_minus = False
        
        for i, card in enumerate(player.hand):
            potential_scores: list[tuple[int, bool]] = []
            
            if card.card_type == CardType.FLIP:
                # Check both plus and minus
                potential_scores.append((score + abs(card.value), False))
                potential_scores.append((score - abs(card.value), True))
            elif card.card_type == CardType.PLUS:
                potential_scores.append((score + card.value, False))
            elif card.card_type == CardType.MINUS:
                potential_scores.append((score - abs(card.value), False))
            
            for pot_score, is_minus in potential_scores:
                if pot_score <= 20 and pot_score > self.stand_threshold:
                    if pot_score > best_score:
                        best_score = pot_score
                        best_card_idx = i
                        use_minus = is_minus
        
        # If we found a good card, play it
        if best_card_idx is not None and best_score > self.stand_threshold:
            return AIDecision(AIAction.PLAY_CARD, best_card_idx, use_minus)
        
        # Stand if at or above threshold
        if score >= self.stand_threshold:
            return AIDecision(AIAction.STAND)
        
        # Otherwise end turn to draw another card
        return AIDecision(AIAction.END_TURN)


class NormalAI(AIStrategy):
    """Strategic AI from pazaak-iron-ginger.
    
    Strategy (from comp.py):
    - Uses weighted probability system for decisions
    - Considers opponent's game score when deciding to play cards
    - Has stay check logic based on both players' scores
    - Prefers cards that get score above 16
    
    Reference: vendor/pazaak-iron-ginger/modules/secondary/comp.py
    """
    
    name = "Normal"
    description = "Strategic AI with weighted probability decisions"
    
    def __init__(self, stand_threshold: int = 17):
        self.stand_threshold = stand_threshold
    
    def decide(self, game: PazaakGame, player: Player) -> AIDecision:
        from holopazaak.game.card import CardType
        
        opponent = game.get_opponent(player)
        score = player.score
        opp_score = opponent.score
        
        # At 20, always stand
        if score == 20:
            return AIDecision(AIAction.STAND)
        
        # If busted, try to find a minus card to save
        if score > 20:
            return self._handle_bust(player, score)
        
        # Check if opponent is standing
        if opponent.is_standing:
            return self._handle_opponent_standing(player, opponent, score, opp_score)
        
        # Normal play - consider playing a card if score > 14
        if score > 14:
            card_decision = self._choose_card_to_play(player, opponent, score)
            if card_decision:
                return card_decision
        
        # Stay check based on iron-ginger logic
        if self._should_stay(player, opponent, score, opp_score):
            return AIDecision(AIAction.STAND)
        
        return AIDecision(AIAction.END_TURN)
    
    def _handle_bust(self, player: Player, score: int) -> AIDecision:
        """Handle bust situation by finding a minus card."""
        from holopazaak.game.card import CardType
        
        best_idx: int | None = None
        best_result = score
        use_minus = False
        
        for i, card in enumerate(player.hand):
            if card.card_type == CardType.MINUS:
                result = score + card.display_value
                if result <= 20 and (best_idx is None or result > best_result):
                    best_result = result
                    best_idx = i
            elif card.card_type == CardType.FLIP:
                result = score - abs(card.value)
                if result <= 20 and (best_idx is None or result > best_result):
                    best_result = result
                    best_idx = i
                    use_minus = True
        
        if best_idx is not None:
            return AIDecision(AIAction.PLAY_CARD, best_idx, use_minus)
        
        # Can't save, just stand (will lose)
        return AIDecision(AIAction.STAND)
    
    def _handle_opponent_standing(
        self, player: Player, opponent: Player, score: int, opp_score: int
    ) -> AIDecision:
        """Handle when opponent is standing."""
        from holopazaak.game.card import CardType
        
        # If we're winning, stand
        if score > opp_score and score <= 20:
            return AIDecision(AIAction.STAND)
        
        # If tied at high score, might accept
        if score == opp_score and score >= 17:
            return AIDecision(AIAction.STAND)
        
        # Try to find a card that beats opponent
        for i, card in enumerate(player.hand):
            potential_score = score
            use_minus = False
            
            if card.card_type == CardType.PLUS:
                potential_score = score + card.value
            elif card.card_type == CardType.FLIP:
                # Try plus first
                potential_score = score + abs(card.value)
                if potential_score > 20:
                    potential_score = score - abs(card.value)
                    use_minus = True
            
            if opp_score < potential_score <= 20:
                return AIDecision(AIAction.PLAY_CARD, i, use_minus)
        
        # Can't beat with hand card, end turn to draw
        return AIDecision(AIAction.END_TURN)
    
    def _choose_card_to_play(
        self, player: Player, opponent: Player, score: int
    ) -> AIDecision | None:
        """Choose a card to play from hand."""
        from holopazaak.game.card import CardType
        
        opp_score = opponent.score
        best_idx: int | None = None
        best_result = 16
        use_minus = False
        
        for i, card in enumerate(player.hand):
            result = score
            flip_minus = False
            
            if card.card_type == CardType.PLUS:
                result = score + card.value
            elif card.card_type == CardType.MINUS:
                continue  # Don't play minus when not busted
            elif card.card_type == CardType.FLIP:
                result = score + abs(card.value)
                if result > 20:
                    result = score - abs(card.value)
                    flip_minus = True
            
            if result <= 20 and result >= opp_score and result > best_result:
                best_result = result
                best_idx = i
                use_minus = flip_minus
        
        if best_idx is not None:
            # Probability check from iron-ginger
            chance = self._get_play_chance(best_result)
            if random.randint(0, 100) < chance:
                return AIDecision(AIAction.PLAY_CARD, best_idx, use_minus)
        
        return None
    
    def _get_play_chance(self, result: int) -> int:
        """Get probability of playing card based on result score."""
        # From pazaak-iron-ginger chance_mod
        if result == 20:
            return 100
        elif result == 19:
            return 80
        elif result == 18:
            return 50
        elif result == 17:
            return 20
        return 10
    
    def _should_stay(
        self, player: Player, opponent: Player, score: int, opp_score: int
    ) -> bool:
        """Determine if AI should stay."""
        # From pazaak-iron-ginger c_stay_check
        yes = 0
        
        if opponent.is_standing and score >= opp_score and opp_score > 15:
            yes += 2
        elif opponent.is_standing and score > opp_score:
            yes += 2
        elif score >= opp_score and score >= 18:
            yes += 2
        elif score > 17 and not opponent.is_standing:
            yes += 1
        elif score > 17 and opp_score >= 17:
            yes += 1
        
        # Urgency boost if behind in sets
        if player.sets_won < opponent.sets_won or opponent.sets_won > 1:
            yes += 1
        
        return yes > 1


class HardAI(AIStrategy):
    """Complex AI from pazaak-eggborne with advanced strategies.
    
    Features:
    - Safe-to-draw calculation based on highest minus card
    - Tie acceptance probability
    - Character-specific stand thresholds
    - Sophisticated card selection
    
    Reference: vendor/pazaak-eggborne/src/scripts/ai.js lines 1-560
    """
    
    name = "Hard"
    description = "Advanced AI with safe-draw calculation and tie handling"
    
    def __init__(
        self,
        stand_at: int = 17,
        tie_accept_chance: int = 50,  # 0-100
    ):
        self.stand_at = stand_at
        self.tie_accept_chance = tie_accept_chance
    
    def decide(self, game: PazaakGame, player: Player) -> AIDecision:
        from holopazaak.game.card import CardType
        
        opponent = game.get_opponent(player)
        score = player.score
        opp_score = opponent.score
        
        # At 20, always stand
        if score == 20:
            return AIDecision(AIAction.STAND)
        
        # Calculate safe-to-draw threshold
        highest_minus = self._get_highest_minus_value(player)
        safe_to_draw = self._is_safe_to_draw(score, highest_minus)
        
        # Handle bust
        if score > 20:
            return self._handle_bust(player, score, opp_score)
        
        if opponent.is_standing:
            return self._handle_opponent_standing(
                player, score, opp_score, safe_to_draw
            )
        else:
            return self._handle_opponent_playing(
                player, score, opp_score, safe_to_draw
            )
    
    def _get_highest_minus_value(self, player: Player) -> int:
        """Get highest minus value in hand."""
        from holopazaak.game.card import CardType
        
        highest = 0
        for card in player.hand:
            if card.card_type == CardType.MINUS:
                highest = max(highest, abs(card.value))
            elif card.card_type == CardType.FLIP:
                highest = max(highest, abs(card.value))
        return highest
    
    def _is_safe_to_draw(self, score: int, highest_minus: int) -> bool:
        """Check if it's safe to draw another card.
        
        From pazaak-eggborne: safe if (score - highestMinusValue) <= 14
        """
        return (score - highest_minus) <= 14
    
    def _handle_bust(
        self, player: Player, score: int, opp_score: int
    ) -> AIDecision:
        """Handle bust situation."""
        from holopazaak.game.card import CardType
        
        accept_tie = random.randint(0, 100) < self.tie_accept_chance
        
        best_idx: int | None = None
        best_result = -1
        use_minus = False
        
        for i, card in enumerate(player.hand):
            if card.card_type not in (CardType.MINUS, CardType.FLIP):
                continue
            
            if card.card_type == CardType.FLIP:
                result = score - abs(card.value)
                flip = True
            else:
                result = score + card.display_value
                flip = False
            
            if result > 20:
                continue
            
            # Check if result beats or ties opponent
            if accept_tie:
                valid = result >= opp_score
            else:
                valid = result > opp_score
            
            if valid and result > best_result:
                best_result = result
                best_idx = i
                use_minus = flip
        
        if best_idx is not None:
            return AIDecision(AIAction.PLAY_CARD, best_idx, use_minus)
        
        return AIDecision(AIAction.STAND)
    
    def _handle_opponent_standing(
        self,
        player: Player,
        score: int,
        opp_score: int,
        safe_to_draw: bool,
    ) -> AIDecision:
        """Handle when opponent is standing."""
        from holopazaak.game.card import CardType
        
        accept_tie = random.randint(0, 100) < self.tie_accept_chance
        
        # If opponent busted, stand
        if opp_score > 20:
            return AIDecision(AIAction.STAND)
        
        # If winning, stand
        if score > opp_score and score <= 20:
            return AIDecision(AIAction.STAND)
        
        # If tied
        if score == opp_score:
            if accept_tie:
                return AIDecision(AIAction.STAND)
            # Try to break tie
            card_decision = self._find_winning_card(player, score, opp_score, accept_tie)
            if card_decision:
                return card_decision
            return AIDecision(AIAction.STAND)
        
        # We're losing, need to catch up
        card_decision = self._find_winning_card(player, score, opp_score, accept_tie)
        if card_decision:
            return card_decision
        
        # No winning card, draw if board space available
        if len(player.board) < 9:
            return AIDecision(AIAction.END_TURN)
        
        return AIDecision(AIAction.STAND)
    
    def _handle_opponent_playing(
        self,
        player: Player,
        score: int,
        opp_score: int,
        safe_to_draw: bool,
    ) -> AIDecision:
        """Handle when opponent is still playing."""
        from holopazaak.game.card import CardType
        
        # At or above stand threshold, stand
        if score >= self.stand_at:
            return AIDecision(AIAction.STAND)
        
        if not safe_to_draw:
            # Not safe to draw, try to play a card to reach stand threshold
            card_decision = self._find_stand_card(player, score)
            if card_decision:
                return card_decision
        
        # Safe to draw or no good card, end turn
        return AIDecision(AIAction.END_TURN)
    
    def _find_winning_card(
        self,
        player: Player,
        score: int,
        opp_score: int,
        accept_tie: bool,
    ) -> AIDecision | None:
        """Find a card that beats or ties opponent."""
        from holopazaak.game.card import CardType
        
        for i, card in enumerate(player.hand):
            if card.card_type == CardType.PLUS:
                result = score + card.value
                if result <= 20:
                    if result > opp_score or (accept_tie and result == opp_score):
                        return AIDecision(AIAction.PLAY_CARD, i, False)
            elif card.card_type == CardType.FLIP:
                # Try plus
                result = score + abs(card.value)
                if result <= 20:
                    if result > opp_score or (accept_tie and result == opp_score):
                        return AIDecision(AIAction.PLAY_CARD, i, False)
                # Try minus (if needed to get under 20)
                result = score - abs(card.value)
                if result <= 20 and result > opp_score:
                    return AIDecision(AIAction.PLAY_CARD, i, True)
        
        return None
    
    def _find_stand_card(
        self, player: Player, score: int
    ) -> AIDecision | None:
        """Find a card to reach stand threshold."""
        from holopazaak.game.card import CardType
        
        for i, card in enumerate(player.hand):
            if card.card_type not in (CardType.PLUS, CardType.FLIP):
                continue
            
            if card.card_type == CardType.FLIP:
                result = score + abs(card.value)
            else:
                result = score + card.value
            
            if self.stand_at <= result <= 20:
                return AIDecision(AIAction.PLAY_CARD, i, False)
        
        return None


class ExpertAI(AIStrategy):
    """Expert AI based on Java_Pazaak Controller.java.
    
    Features:
    - Target score progression (20 -> 19 -> 18)
    - Opponent score awareness
    - Smart card selection based on exact requirements
    
    Reference: vendor/Java_Pazaak/Controller/Controller.java lines 122-212
    """
    
    name = "Expert"
    description = "Expert AI with target score progression"
    
    def decide(self, game: PazaakGame, player: Player) -> AIDecision:
        from holopazaak.game.card import CardType
        
        opponent = game.get_opponent(player)
        score = player.score
        opp_score = opponent.score
        
        # At 20, always stand
        if score == 20:
            return AIDecision(AIAction.STAND)
        
        # Board full, must stand
        if len(player.board) >= 9:
            return AIDecision(AIAction.STAND)
        
        if opponent.is_standing:
            return self._handle_opponent_standing(player, score, opp_score)
        else:
            return self._handle_opponent_playing(player, score, opp_score)
    
    def _handle_opponent_standing(
        self, player: Player, score: int, opp_score: int
    ) -> AIDecision:
        """Handle when opponent is standing."""
        # If winning, stand
        if score > opp_score and score <= 20:
            return AIDecision(AIAction.STAND)
        
        # Find card to beat opponent
        card_decision = self._find_exact_card(player, score, target=None, min_score=opp_score + 1)
        if card_decision:
            return card_decision
        
        # Can't beat with card, draw
        return AIDecision(AIAction.END_TURN)
    
    def _handle_opponent_playing(
        self, player: Player, score: int, opp_score: int
    ) -> AIDecision:
        """Handle when opponent is still playing."""
        # Try to hit 20 with a card
        card_decision = self._find_exact_card(player, score, target=20)
        if card_decision:
            return card_decision
        
        # At 19, might be good enough
        if score == 19 and opp_score <= 19:
            return AIDecision(AIAction.STAND)
        
        # Try for 19
        card_decision = self._find_exact_card(player, score, target=19)
        if card_decision and opp_score <= 18:
            return card_decision
        
        # At 18, consider standing
        if score == 18 and opp_score <= 18:
            return AIDecision(AIAction.STAND)
        
        # Try for 18
        card_decision = self._find_exact_card(player, score, target=18)
        if card_decision and opp_score <= 17:
            return card_decision
        
        # If score is high enough, stand
        if score >= 17 and score > opp_score:
            return AIDecision(AIAction.STAND)
        
        # If busted, try to recover
        if score > 20:
            return self._handle_bust(player, score)
        
        return AIDecision(AIAction.END_TURN)
    
    def _find_exact_card(
        self,
        player: Player,
        score: int,
        target: int | None = None,
        min_score: int | None = None,
    ) -> AIDecision | None:
        """Find a card to reach exact target or minimum score."""
        from holopazaak.game.card import CardType
        
        for i, card in enumerate(player.hand):
            result = score
            use_minus = False
            
            if card.card_type == CardType.PLUS:
                result = score + card.value
            elif card.card_type == CardType.MINUS:
                result = score - abs(card.value)
            elif card.card_type == CardType.FLIP:
                # Try plus first
                result = score + abs(card.value)
                if result > 20:
                    result = score - abs(card.value)
                    use_minus = True
            
            if result > 20:
                continue
            
            if target is not None and result == target:
                return AIDecision(AIAction.PLAY_CARD, i, use_minus)
            
            if min_score is not None and result >= min_score:
                return AIDecision(AIAction.PLAY_CARD, i, use_minus)
        
        return None
    
    def _handle_bust(self, player: Player, score: int) -> AIDecision:
        """Find card to recover from bust."""
        from holopazaak.game.card import CardType
        
        for i, card in enumerate(player.hand):
            if card.card_type == CardType.MINUS:
                result = score - abs(card.value)
                if result <= 20:
                    return AIDecision(AIAction.PLAY_CARD, i, False)
            elif card.card_type == CardType.FLIP:
                result = score - abs(card.value)
                if result <= 20:
                    return AIDecision(AIAction.PLAY_CARD, i, True)
        
        return AIDecision(AIAction.STAND)


class MasterAI(AIStrategy):
    """Master AI combining best strategies from all implementations.
    
    Features all advanced strategies:
    - Safe-to-draw calculation
    - Target score progression
    - Opponent awareness
    - Probabilistic tie handling
    - Hand card conservation
    """
    
    name = "Master"
    description = "Master AI combining all optimal strategies"
    
    def __init__(self, stand_at: int = 18, tie_accept_chance: int = 0):
        self.stand_at = stand_at
        self.tie_accept_chance = tie_accept_chance
    
    def decide(self, game: PazaakGame, player: Player) -> AIDecision:
        from holopazaak.game.card import CardType
        
        opponent = game.get_opponent(player)
        score = player.score
        opp_score = opponent.score
        
        # Perfect 20, always stand
        if score == 20:
            return AIDecision(AIAction.STAND)
        
        # Board full
        if len(player.board) >= 9:
            return AIDecision(AIAction.STAND)
        
        # Calculate strategic factors
        highest_minus = self._get_highest_minus_value(player)
        safe_to_draw = (score - highest_minus) <= 14
        hand_cards_left = len(player.hand)
        
        # Handle bust
        if score > 20:
            return self._handle_bust(player, score, opp_score)
        
        if opponent.is_standing:
            return self._handle_opponent_standing(
                player, score, opp_score, safe_to_draw, hand_cards_left
            )
        else:
            return self._handle_opponent_playing(
                player, score, opp_score, safe_to_draw, hand_cards_left
            )
    
    def _get_highest_minus_value(self, player: Player) -> int:
        from holopazaak.game.card import CardType
        highest = 0
        for card in player.hand:
            if card.card_type in (CardType.MINUS, CardType.FLIP):
                highest = max(highest, abs(card.value))
        return highest
    
    def _handle_bust(
        self, player: Player, score: int, opp_score: int
    ) -> AIDecision:
        from holopazaak.game.card import CardType
        
        best_idx: int | None = None
        best_result = -1
        use_minus = False
        
        for i, card in enumerate(player.hand):
            if card.card_type not in (CardType.MINUS, CardType.FLIP):
                continue
            
            if card.card_type == CardType.FLIP:
                result = score - abs(card.value)
                flip = True
            else:
                result = score - abs(card.value)
                flip = False
            
            if result <= 20 and result > best_result:
                best_result = result
                best_idx = i
                use_minus = flip
        
        if best_idx is not None:
            return AIDecision(AIAction.PLAY_CARD, best_idx, use_minus)
        return AIDecision(AIAction.STAND)
    
    def _handle_opponent_standing(
        self,
        player: Player,
        score: int,
        opp_score: int,
        safe_to_draw: bool,
        hand_cards: int,
    ) -> AIDecision:
        from holopazaak.game.card import CardType
        
        # Opponent busted, we win
        if opp_score > 20:
            return AIDecision(AIAction.STAND)
        
        # We're winning
        if score > opp_score:
            return AIDecision(AIAction.STAND)
        
        # Tied - check acceptance
        if score == opp_score:
            if random.randint(0, 100) < self.tie_accept_chance:
                return AIDecision(AIAction.STAND)
        
        # Try to find winning card
        for target in range(20, opp_score, -1):
            for i, card in enumerate(player.hand):
                result, use_minus = self._calc_result(score, card)
                if result == target:
                    return AIDecision(AIAction.PLAY_CARD, i, use_minus)
        
        # No winning card, draw if safe
        return AIDecision(AIAction.END_TURN)
    
    def _handle_opponent_playing(
        self,
        player: Player,
        score: int,
        opp_score: int,
        safe_to_draw: bool,
        hand_cards: int,
    ) -> AIDecision:
        from holopazaak.game.card import CardType
        
        # Try for 20
        for i, card in enumerate(player.hand):
            result, use_minus = self._calc_result(score, card)
            if result == 20:
                return AIDecision(AIAction.PLAY_CARD, i, use_minus)
        
        # At stand threshold, consider standing
        if score >= self.stand_at:
            return AIDecision(AIAction.STAND)
        
        # Not safe to draw, try to reach stand threshold
        if not safe_to_draw:
            for i, card in enumerate(player.hand):
                result, use_minus = self._calc_result(score, card)
                if self.stand_at <= result <= 20:
                    return AIDecision(AIAction.PLAY_CARD, i, use_minus)
        
        # Safe to draw or no good card
        return AIDecision(AIAction.END_TURN)
    
    def _calc_result(self, score: int, card: Card) -> tuple[int, bool]:
        from holopazaak.game.card import CardType
        
        if card.card_type == CardType.PLUS:
            return score + card.value, False
        elif card.card_type == CardType.MINUS:
            return score - abs(card.value), False
        elif card.card_type == CardType.FLIP:
            plus_result = score + abs(card.value)
            if plus_result <= 20:
                return plus_result, False
            return score - abs(card.value), True
        return score, False


# AI difficulty mapping
AI_DIFFICULTIES: dict[str, type[AIStrategy]] = {
    "easy": EasyAI,
    "normal": NormalAI,
    "hard": HardAI,
    "expert": ExpertAI,
    "master": MasterAI,
}


def get_ai_strategy(difficulty: str, **kwargs) -> AIStrategy:
    """Get an AI strategy by difficulty name."""
    ai_class = AI_DIFFICULTIES.get(difficulty.lower(), NormalAI)
    return ai_class(**kwargs)

