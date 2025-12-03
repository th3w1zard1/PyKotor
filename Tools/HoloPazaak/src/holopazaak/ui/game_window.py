"""Main game window for HoloPazaak.

This module provides the main game UI combining features from:
- pazaak-eggborne: Game layout and flow
- PazaakApp (Vue): State management and UI updates
- pazaak-iron-ginger: Player/opponent layout

References:
- vendor/pazaak-eggborne/src/App.vue: lines 1-400
- vendor/PazaakApp/src/App.vue: lines 1-300
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import QTimer, Qt, Signal
from qtpy.QtGui import QFont
from qtpy.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from holopazaak.ai.bot import AIPlayer
from holopazaak.data.opponents import OPPONENTS, OpponentDifficulty, get_opponent
from holopazaak.game.card import Card, CardType
from holopazaak.game.engine import PazaakGame
from holopazaak.game.player import Player
from holopazaak.ui.styles import Theme, ThemeColors
from holopazaak.ui.widgets import (
    ActionButton,
    BoardWidget,
    CardWidget,
    HandWidget,
    MessageLogWidget,
    ScoreWidget,
)

if TYPE_CHECKING:
    from holopazaak.data.opponents import OpponentProfile


class OpponentSelectDialog(QDialog):
    """Dialog for selecting an opponent.
    
    Displays opponents grouped by difficulty with their
    descriptions and phrases.
    """
    
    opponent_selected = Signal(str)  # Emits opponent ID
    
    def __init__(self, theme: ThemeColors | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme = theme or Theme.SITH
        self.selected_opponent_id: str | None = None
        
        self.setWindowTitle("Select Opponent")
        self.setMinimumSize(600, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Choose Your Opponent")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Scrollable opponent list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Group opponents by difficulty
        difficulties = [
            OpponentDifficulty.NOVICE,
            OpponentDifficulty.EASY,
            OpponentDifficulty.NORMAL,
            OpponentDifficulty.HARD,
            OpponentDifficulty.EXPERT,
            OpponentDifficulty.MASTER,
        ]
        
        for difficulty in difficulties:
            opponents = [o for o in OPPONENTS if o.difficulty == difficulty]
            if not opponents:
                continue
            
            # Difficulty header
            header = QLabel(f"═══ {difficulty.name} ═══")
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(header)
            
            # Opponent buttons
            for opp in opponents:
                btn = QPushButton(f"{opp.name}")
                btn.setToolTip(f"{opp.description}\n\nSkill Level: {opp.skill_level}")
                btn.clicked.connect(lambda checked, oid=opp.id: self._select_opponent(oid))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme.get('panel', '#3c3c3c')};
                        color: {self.theme.get('text', '#e0e0e0')};
                        border: 1px solid #555;
                        border-radius: 5px;
                        padding: 10px;
                        text-align: left;
                        font-size: 14px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #FFD700;
                    }}
                """)
                scroll_layout.addWidget(btn)
            
            scroll_layout.addSpacing(10)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply theme to dialog."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme.get('background', '#2b2b2b')};
            }}
            QLabel {{
                color: {self.theme.get('text', '#e0e0e0')};
            }}
            QScrollArea {{
                border: none;
                background-color: {self.theme.get('background', '#2b2b2b')};
            }}
        """)
    
    def _select_opponent(self, opponent_id: str):
        """Handle opponent selection."""
        self.selected_opponent_id = opponent_id
        self.opponent_selected.emit(opponent_id)
        self.accept()


class DeckBuilderDialog(QDialog):
    """Dialog for building the player's side deck.
    
    Allows selecting 10 cards from available card types.
    """
    
    deck_confirmed = Signal(list)  # Emits list of selected Cards
    
    AVAILABLE_CARDS = [
        # Plus cards
        (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
        (4, CardType.PLUS), (5, CardType.PLUS), (6, CardType.PLUS),
        # Minus cards
        (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
        (4, CardType.MINUS), (5, CardType.MINUS), (6, CardType.MINUS),
        # Flip cards
        (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
        (4, CardType.FLIP), (5, CardType.FLIP), (6, CardType.FLIP),
        # Special cards
        (2, CardType.DOUBLE),
        (1, CardType.TIEBREAKER),
        (3, CardType.PLUS_MINUS_3_6),
    ]
    
    def __init__(self, theme: ThemeColors | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.theme = theme or Theme.SITH
        self.selected_cards: list[tuple[int, CardType]] = []
        
        self.setWindowTitle("Build Your Deck")
        self.setMinimumSize(700, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select 10 Cards for Your Side Deck")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Click cards to add them to your deck. "
            "Right-click to remove. Flip cards (±) can be toggled during play."
        )
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instructions)
        
        # Selected count
        self.count_label = QLabel("Selected: 0/10")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)
        
        # Available cards grid
        cards_frame = QFrame()
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(10)
        
        row, col = 0, 0
        for val, ctype in self.AVAILABLE_CARDS:
            card = Card(f"{val}", val if ctype != CardType.MINUS else -val, ctype)
            widget = CardWidget(card=card, theme=self.theme, is_playable=True)
            widget.clicked.connect(lambda idx, v=val, t=ctype: self._add_card(v, t))
            cards_layout.addWidget(widget, row, col)
            
            col += 1
            if col >= 7:
                col = 0
                row += 1
        
        layout.addWidget(cards_frame)
        
        # Selected deck display
        deck_label = QLabel("Your Deck:")
        layout.addWidget(deck_label)
        
        self.deck_display = QLabel("Empty")
        self.deck_display.setWordWrap(True)
        self.deck_display.setStyleSheet(f"""
            background-color: {self.theme.get('panel', '#3c3c3c')};
            padding: 10px;
            border-radius: 5px;
        """)
        layout.addWidget(self.deck_display)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_deck)
        btn_layout.addWidget(clear_btn)
        
        default_btn = QPushButton("Default Deck")
        default_btn.clicked.connect(self._use_default_deck)
        btn_layout.addWidget(default_btn)
        
        confirm_btn = QPushButton("Confirm")
        confirm_btn.clicked.connect(self._confirm_deck)
        btn_layout.addWidget(confirm_btn)
        
        layout.addLayout(btn_layout)
        
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply theme to dialog."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme.get('background', '#2b2b2b')};
            }}
            QLabel {{
                color: {self.theme.get('text', '#e0e0e0')};
            }}
            QPushButton {{
                background-color: {self.theme.get('button', '#4CAF50')};
                color: {self.theme.get('button_text', 'white')};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #666;
            }}
        """)
    
    def _add_card(self, value: int, card_type: CardType):
        """Add a card to the deck."""
        if len(self.selected_cards) >= 10:
            return
        
        self.selected_cards.append((value, card_type))
        self._update_display()
    
    def _clear_deck(self):
        """Clear the deck."""
        self.selected_cards.clear()
        self._update_display()
    
    def _use_default_deck(self):
        """Use a default balanced deck."""
        self.selected_cards = [
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP),
        ]
        self._update_display()
    
    def _update_display(self):
        """Update the deck display."""
        self.count_label.setText(f"Selected: {len(self.selected_cards)}/10")
        
        if not self.selected_cards:
            self.deck_display.setText("Empty")
        else:
            cards_text = []
            for val, ctype in self.selected_cards:
                if ctype == CardType.PLUS:
                    cards_text.append(f"+{val}")
                elif ctype == CardType.MINUS:
                    cards_text.append(f"-{val}")
                elif ctype == CardType.FLIP:
                    cards_text.append(f"±{val}")
                elif ctype == CardType.DOUBLE:
                    cards_text.append("x2")
                elif ctype == CardType.TIEBREAKER:
                    cards_text.append("T")
                elif ctype == CardType.PLUS_MINUS_3_6:
                    cards_text.append("+3/-6")
            
            self.deck_display.setText(", ".join(cards_text))
    
    def _confirm_deck(self):
        """Confirm the deck selection."""
        if len(self.selected_cards) != 10:
            QMessageBox.warning(
                self, "Invalid Deck", 
                f"Please select exactly 10 cards. You have {len(self.selected_cards)}."
            )
            return
        
        # Convert to Card objects
        cards = []
        for val, ctype in self.selected_cards:
            actual_val = val if ctype != CardType.MINUS else -val
            cards.append(Card(f"{val}", actual_val, ctype))
        
        self.deck_confirmed.emit(cards)
        self.accept()


class PazaakWindow(QMainWindow):
    """Main game window for HoloPazaak.
    
    Provides the complete game UI with:
    - Player and opponent boards
    - Score tracking
    - Action buttons
    - Message log
    - Theme switching
    """
    
    def __init__(self):
        super().__init__()
        
        self.theme = Theme.SITH
        self.game: PazaakGame | None = None
        self.player: Player | None = None
        self.opponent: AIPlayer | None = None
        self.player_sideboard: list[Card] = []
        
        self.setWindowTitle("HoloPazaak - The Best Pazaak Game")
        self.setMinimumSize(1000, 700)
        
        self._setup_ui()
        self._connect_signals()
        
        # Start with opponent selection
        QTimer.singleShot(100, self._show_opponent_selection)
    
    def _setup_ui(self):
        """Setup the main window UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Top bar with title and theme toggle
        top_bar = QHBoxLayout()
        
        title = QLabel("HoloPazaak")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        top_bar.addWidget(title)
        
        top_bar.addStretch()
        
        self.theme_btn = QPushButton("Toggle Theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        top_bar.addWidget(self.theme_btn)
        
        self.new_game_btn = QPushButton("New Game")
        self.new_game_btn.clicked.connect(self._show_opponent_selection)
        top_bar.addWidget(self.new_game_btn)
        
        main_layout.addLayout(top_bar)
        
        # Game area
        game_area = QHBoxLayout()
        
        # Left side - Opponent info
        opponent_panel = QVBoxLayout()
        
        self.opponent_score = ScoreWidget("Opponent", self.theme)
        opponent_panel.addWidget(self.opponent_score)
        
        self.opponent_board = BoardWidget(self.theme)
        opponent_panel.addWidget(self.opponent_board)
        
        self.opponent_hand = HandWidget(self.theme, is_interactive=False)
        opponent_panel.addWidget(self.opponent_hand)
        
        opponent_panel.addStretch()
        
        game_area.addLayout(opponent_panel, 1)
        
        # Center - Message log and status
        center_panel = QVBoxLayout()
        
        self.message_log = MessageLogWidget(self.theme)
        self.message_log.setMinimumWidth(200)
        center_panel.addWidget(self.message_log)
        
        center_panel.addStretch()
        
        game_area.addLayout(center_panel)
        
        # Right side - Player info
        player_panel = QVBoxLayout()
        
        self.player_score = ScoreWidget("Player", self.theme)
        player_panel.addWidget(self.player_score)
        
        self.player_board = BoardWidget(self.theme)
        player_panel.addWidget(self.player_board)
        
        self.player_hand = HandWidget(self.theme, is_interactive=True)
        player_panel.addWidget(self.player_hand)
        
        player_panel.addStretch()
        
        game_area.addLayout(player_panel, 1)
        
        main_layout.addLayout(game_area, 1)
        
        # Action buttons
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        
        self.stand_btn = ActionButton("Stand", self.theme)
        self.stand_btn.clicked.connect(self._on_stand)
        action_bar.addWidget(self.stand_btn)
        
        self.end_turn_btn = ActionButton("End Turn", self.theme)
        self.end_turn_btn.clicked.connect(self._on_end_turn)
        action_bar.addWidget(self.end_turn_btn)
        
        action_bar.addStretch()
        
        main_layout.addLayout(action_bar)
        
        self._apply_theme()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.player_hand.card_clicked.connect(self._on_card_clicked)
        self.player_hand.card_flip_requested.connect(self._on_flip_card)
    
    def _apply_theme(self):
        """Apply the current theme to all widgets."""
        bg_color = self.theme.get("background", "#2b2b2b")
        text_color = self.theme.get("text", "#e0e0e0")
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            QPushButton {{
                background-color: {self.theme.get('button', '#4CAF50')};
                color: {self.theme.get('button_text', 'white')};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #555;
            }}
        """)
        
        # Update all widgets
        self.opponent_score.set_theme(self.theme)
        self.opponent_board.set_theme(self.theme)
        self.opponent_hand.set_theme(self.theme)
        self.player_score.set_theme(self.theme)
        self.player_board.set_theme(self.theme)
        self.player_hand.set_theme(self.theme)
        self.message_log.set_theme(self.theme)
        self.stand_btn.set_theme(self.theme)
        self.end_turn_btn.set_theme(self.theme)
    
    def _toggle_theme(self):
        """Toggle between Republic and Sith themes."""
        if self.theme == Theme.SITH:
            self.theme = Theme.REPUBLIC
        else:
            self.theme = Theme.SITH
        
        self._apply_theme()
    
    def _show_opponent_selection(self):
        """Show the opponent selection dialog."""
        dialog = OpponentSelectDialog(self.theme, self)
        dialog.opponent_selected.connect(self._on_opponent_selected)
        dialog.exec()
    
    def _on_opponent_selected(self, opponent_id: str):
        """Handle opponent selection."""
        profile = get_opponent(opponent_id)
        self.opponent = AIPlayer(profile)
        self.opponent_score.set_name(profile.name)
        
        self.message_log.clear_messages()
        self.message_log.add_message(f"Opponent: {profile.name}")
        self.message_log.add_message(profile.phrases.chosen)
        
        # Show deck builder
        self._show_deck_builder()
    
    def _show_deck_builder(self):
        """Show the deck builder dialog."""
        dialog = DeckBuilderDialog(self.theme, self)
        dialog.deck_confirmed.connect(self._on_deck_confirmed)
        dialog.exec()
    
    def _on_deck_confirmed(self, cards: list[Card]):
        """Handle deck confirmation."""
        self.player_sideboard = cards
        self._start_game()
    
    def _start_game(self):
        """Start a new game."""
        if not self.opponent:
            return
        
        self.player = Player("Player", is_ai=False)
        self.player.sideboard = self.player_sideboard.copy()
        
        self.game = PazaakGame(self.player, self.opponent)
        self.game.start_game()
        
        self.message_log.add_message("Game started!")
        self._update_ui()
        
        # If AI goes first, process their turn
        self._check_ai_turn()
    
    def _update_ui(self):
        """Update all UI elements from game state."""
        if not self.game or not self.player or not self.opponent:
            return
        
        # Update scores
        self.player_score.update_score(self.player.score, self.player.is_bust)
        self.player_score.update_sets_won(self.player.sets_won)
        self.player_score.set_standing(self.player.is_standing)
        
        self.opponent_score.update_score(self.opponent.score, self.opponent.is_bust)
        self.opponent_score.update_sets_won(self.opponent.sets_won)
        self.opponent_score.set_standing(self.opponent.is_standing)
        
        # Update active turn indicator
        is_player_turn = self.game.current_player == self.player
        self.player_score.set_active_turn(is_player_turn)
        self.opponent_score.set_active_turn(not is_player_turn)
        
        # Update boards
        self.player_board.update_board(self.player.board)
        self.opponent_board.update_board(self.opponent.board)
        
        # Update hands
        self.player_hand.update_hand(self.player.hand)
        # Show opponent hand face down
        opponent_hand_display = [Card("?", 0, CardType.MAIN, is_face_down=True) for _ in self.opponent.hand]
        self.opponent_hand.update_hand(opponent_hand_display)
        
        # Enable/disable buttons based on game state
        can_act = is_player_turn and not self.game.is_round_over and not self.player.is_standing
        self.stand_btn.setEnabled(can_act)
        self.end_turn_btn.setEnabled(can_act)
        self.player_hand.set_interactive(can_act and not self.player.played_card_this_turn)
        
        # Check for round/game end
        if self.game.is_round_over:
            self._handle_round_end()
        
        if self.game.is_game_over:
            self._handle_game_end()
    
    def _on_card_clicked(self, index: int):
        """Handle player clicking a card in their hand."""
        if not self.game or not self.player:
            return
        
        if self.game.play_hand_card(self.player, index):
            card = self.player.board[-1] if self.player.board else None
            if card:
                self.message_log.add_message(f"You played: {card}")
            self._update_ui()
    
    def _on_flip_card(self, index: int):
        """Handle player flipping a card in their hand."""
        if not self.player or index >= len(self.player.hand):
            return
        
        card = self.player.hand[index]
        if card.card_type in [CardType.FLIP, CardType.PLUS_MINUS_3_6]:
            card.flip()
            self.player_hand.update_hand(self.player.hand)
            self.message_log.add_message(f"Flipped card to: {card}")
    
    def _on_stand(self):
        """Handle player standing."""
        if not self.game or not self.player:
            return
        
        self.game.stand(self.player)
        self.message_log.add_message("You stand.")
        self._update_ui()
        
        # Check if AI needs to play
        self._check_ai_turn()
    
    def _on_end_turn(self):
        """Handle player ending their turn."""
        if not self.game or not self.player:
            return
        
        self.game.end_turn()
        self.message_log.add_message("Your turn ends.")
        self._update_ui()
        
        # AI turn
        self._check_ai_turn()
    
    def _check_ai_turn(self):
        """Check and process AI turn if needed."""
        if not self.game or not self.opponent:
            return
        
        if self.game.is_round_over or self.game.is_game_over:
            return
        
        if self.game.current_player == self.opponent and not self.opponent.is_standing:
            # Delay AI turn for visual effect
            QTimer.singleShot(800, self._process_ai_turn)
    
    def _process_ai_turn(self):
        """Process the AI's turn."""
        if not self.game or not self.opponent:
            return
        
        # AI decides move
        action, card_index = self.opponent.decide_move(self.game)
        
        if action == "play_card" and card_index is not None:
            if self.game.play_hand_card(self.opponent, card_index):
                card = self.opponent.board[-1] if self.opponent.board else None
                if card:
                    self.message_log.add_message(f"{self.opponent.name} played: {card}")
                    self.message_log.add_message(self.opponent.profile.phrases.play)
        
        elif action == "stand":
            self.game.stand(self.opponent)
            self.message_log.add_message(f"{self.opponent.name} stands.")
            self.message_log.add_message(self.opponent.profile.phrases.stand)
        
        else:  # end_turn
            self.game.end_turn()
            self.message_log.add_message(f"{self.opponent.name} ends turn.")
        
        self._update_ui()
        
        # Continue AI turn if still their turn
        self._check_ai_turn()
    
    def _handle_round_end(self):
        """Handle end of a round."""
        if not self.game or not self.opponent:
            return
        
        if self.game.round_winner:
            winner_name = self.game.round_winner.name
            self.message_log.add_message(f"Round winner: {winner_name}!")
            
            if self.game.round_winner == self.opponent:
                self.message_log.add_message(self.opponent.profile.phrases.win_round)
            else:
                self.message_log.add_message(self.opponent.profile.phrases.lose_round)
        else:
            self.message_log.add_message("Round is a tie!")
        
        # Start next round after delay
        if not self.game.is_game_over:
            QTimer.singleShot(2000, self._start_next_round)
    
    def _start_next_round(self):
        """Start the next round."""
        if not self.game:
            return
        
        self.game.start_round()
        self.message_log.add_message("New round starting!")
        self._update_ui()
        
        self._check_ai_turn()
    
    def _handle_game_end(self):
        """Handle end of the game."""
        if not self.game or not self.opponent:
            return
        
        if self.game.winner:
            winner_name = self.game.winner.name
            
            if self.game.winner == self.opponent:
                self.message_log.add_message(f"Game Over! {winner_name} wins!")
                self.message_log.add_message(self.opponent.profile.phrases.win_game)
            else:
                self.message_log.add_message(f"Congratulations! You win!")
                self.message_log.add_message(self.opponent.profile.phrases.lose_game)
        
        # Disable actions
        self.stand_btn.setEnabled(False)
        self.end_turn_btn.setEnabled(False)
        self.player_hand.set_interactive(False)

