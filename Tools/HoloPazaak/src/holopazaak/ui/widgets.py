"""Custom widgets for HoloPazaak UI.

This module contains reusable UI components combining features from:
- pazaak-eggborne: Card flip animations and visual effects
- PazaakApp (Vue): Card component styling and interactions
- pazaak-iron-ginger: Layout and board design

References:
- vendor/pazaak-eggborne/src/components/Card.vue: lines 1-200
- vendor/PazaakApp/src/components/CardComponent.vue: lines 1-150
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import (
    Property,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    Signal,
)
from qtpy.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from qtpy.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from holopazaak.game.card import Card, CardType
    from holopazaak.ui.styles import ThemeColors


class CardWidget(QFrame):
    """Visual representation of a Pazaak card.
    
    Features:
    - Smooth flip animations
    - Card type-based coloring
    - Hover effects
    - Click interactions for playable cards
    
    Based on pazaak-eggborne Card.vue component.
    """
    
    clicked = Signal(int)  # Emits card index when clicked
    flip_requested = Signal(int)  # Emits card index when flip is requested
    
    CARD_WIDTH = 70
    CARD_HEIGHT = 100
    
    def __init__(
        self,
        card: Card | None = None,
        index: int = 0,
        theme: ThemeColors | None = None,
        is_playable: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        from holopazaak.ui.styles import Theme
        self.card = card
        self.index = index
        self.theme = theme or Theme.SITH
        self.is_playable = is_playable
        self._is_hovered = False
        self._flip_angle = 0.0
        self._scale = 1.0
        
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(2)
        
        self._setup_animations()
        self._setup_shadow()
        self._update_style()
        
        if is_playable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _setup_animations(self):
        """Setup card animations."""
        # Flip animation
        self._flip_anim = QPropertyAnimation(self, b"flip_angle")
        self._flip_anim.setDuration(300)
        self._flip_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        # Scale animation for hover
        self._scale_anim = QPropertyAnimation(self, b"card_scale")
        self._scale_anim.setDuration(150)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Deal animation
        self._deal_anim = QPropertyAnimation(self, b"pos")
        self._deal_anim.setDuration(400)
        self._deal_anim.setEasingCurve(QEasingCurve.Type.OutBack)
    
    def _setup_shadow(self):
        """Add drop shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
    
    def _get_card_color(self) -> str:
        """Get the background color based on card type."""
        if not self.card:
            return self.theme.get("panel", "#3c3c3c")
        
        if self.card.is_face_down:
            return self.theme.get("panel", "#3c3c3c")
        
        from holopazaak.game.card import CardType
        
        color_map = {
            CardType.MAIN: self.theme.get("card_main", "#405040"),
            CardType.PLUS: self.theme.get("card_plus", "#304050"),
            CardType.MINUS: self.theme.get("card_minus", "#503030"),
            CardType.FLIP: self.theme.get("card_flip", "#505030"),
            CardType.DOUBLE: self.theme.get("card_double", "#6A0572"),
            CardType.TIEBREAKER: self.theme.get("card_tiebreaker", "#B8860B"),
            CardType.FLIP_THREE_SIX: self.theme.get("card_plus_minus_3_6", "#4682B4"),
        }
        
        return color_map.get(self.card.card_type, self.theme.get("panel", "#3c3c3c"))
    
    def _update_style(self):
        """Update card styling."""
        bg_color = self._get_card_color()
        text_color = self.theme.get("text", "#e0e0e0")
        border_color = "#FFD700" if self._is_hovered and self.is_playable else "#555"
        
        self.setStyleSheet(f"""
            CardWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
        """)
        self.update()
    
    def paintEvent(self, event):
        """Custom paint for card content."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.card:
            # Empty slot
            self._draw_empty_slot(painter)
            return
        
        if self.card.is_face_down:
            self._draw_face_down(painter)
        else:
            self._draw_face_up(painter)
    
    def _draw_empty_slot(self, painter: QPainter):
        """Draw an empty card slot."""
        pen = QPen(QColor(self.theme.get("text", "#e0e0e0")))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.drawRoundedRect(rect, 4, 4)
    
    def _draw_face_down(self, painter: QPainter):
        """Draw the back of a card."""
        # Draw a pattern for card back
        painter.setPen(QPen(QColor("#444")))
        
        # Draw crosshatch pattern
        for i in range(0, self.width(), 10):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 10):
            painter.drawLine(0, i, self.width(), i)
        
        # Draw center "?" 
        painter.setPen(QPen(QColor(self.theme.get("text", "#e0e0e0"))))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "?")
    
    def _draw_face_up(self, painter: QPainter):
        """Draw the front of a card."""
        text_color = QColor(self.theme.get("text", "#e0e0e0"))
        painter.setPen(QPen(text_color))
        
        # Draw card value
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)
        
        value_text = str(self.card) if self.card else ""
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, value_text)
        
        # Draw card type indicator in corner
        if self.card:
            from holopazaak.game.card import CardType
            
            type_text = ""
            if self.card.card_type == CardType.FLIP:
                type_text = "±"
            elif self.card.card_type == CardType.DOUBLE:
                type_text = "x2"
            elif self.card.card_type == CardType.TIEBREAKER:
                type_text = "T"
            elif self.card.card_type == CardType.PLUS_MINUS_3_6:
                type_text = "3/6"
            
            if type_text:
                small_font = QFont("Arial", 10)
                painter.setFont(small_font)
                painter.drawText(5, 15, type_text)
    
    def enterEvent(self, event):
        """Handle mouse enter."""
        self._is_hovered = True
        self._update_style()
        
        if self.is_playable:
            self._scale_anim.stop()
            self._scale_anim.setStartValue(self._scale)
            self._scale_anim.setEndValue(1.1)
            self._scale_anim.start()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self._is_hovered = False
        self._update_style()
        
        if self.is_playable:
            self._scale_anim.stop()
            self._scale_anim.setStartValue(self._scale)
            self._scale_anim.setEndValue(1.0)
            self._scale_anim.start()
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_playable:
            self.clicked.emit(self.index)
        elif event.button() == Qt.MouseButton.RightButton and self.card:
            from holopazaak.game.card import CardType
            if self.card.card_type in [CardType.FLIP, CardType.PLUS_MINUS_3_6]:
                self.flip_requested.emit(self.index)
        
        super().mousePressEvent(event)
    
    def animate_flip(self):
        """Animate card flip."""
        self._flip_anim.setStartValue(0.0)
        self._flip_anim.setEndValue(180.0)
        self._flip_anim.start()
    
    def animate_deal(self, start_pos: QPoint):
        """Animate card being dealt."""
        self._deal_anim.setStartValue(start_pos)
        self._deal_anim.setEndValue(self.pos())
        self._deal_anim.start()
    
    # Properties for animations
    def get_flip_angle(self) -> float:
        return self._flip_angle
    
    def set_flip_angle(self, angle: float):
        self._flip_angle = angle
        self.update()
    
    flip_angle = Property(float, get_flip_angle, set_flip_angle)
    
    def get_card_scale(self) -> float:
        return self._scale
    
    def set_card_scale(self, scale: float):
        self._scale = scale
        # Apply scale transform
        transform_str = f"scale({scale})"
        self.update()
    
    card_scale = Property(float, get_card_scale, set_card_scale)
    
    def set_card(self, card: Card | None):
        """Update the card displayed."""
        self.card = card
        self._update_style()
        self.update()
    
    def set_theme(self, theme: ThemeColors):
        """Update the theme."""
        self.theme = theme
        self._update_style()


class BoardWidget(QFrame):
    """Widget displaying a player's board (played cards).
    
    Shows up to 9 cards in a row, which is the maximum board size.
    """
    
    MAX_CARDS = 9
    
    def __init__(self, theme: ThemeColors | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        from holopazaak.ui.styles import Theme
        self.theme = theme or Theme.SITH
        self.card_widgets: list[CardWidget] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the board layout."""
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create card slots
        for i in range(self.MAX_CARDS):
            card_widget = CardWidget(card=None, index=i, theme=self.theme)
            self.card_widgets.append(card_widget)
            layout.addWidget(card_widget)
        
        self.setStyleSheet(f"""
            BoardWidget {{
                background-color: {self.theme.get('panel', '#3c3c3c')};
                border: 2px solid #555;
                border-radius: 10px;
            }}
        """)
    
    def update_board(self, cards: list):
        """Update the displayed cards."""
        for i, widget in enumerate(self.card_widgets):
            if i < len(cards):
                widget.set_card(cards[i])
            else:
                widget.set_card(None)
    
    def set_theme(self, theme: ThemeColors):
        """Update the theme."""
        self.theme = theme
        for widget in self.card_widgets:
            widget.set_theme(theme)
        
        self.setStyleSheet(f"""
            BoardWidget {{
                background-color: {theme.get('panel', '#3c3c3c')};
                border: 2px solid #555;
                border-radius: 10px;
            }}
        """)


class HandWidget(QFrame):
    """Widget displaying a player's hand (side deck cards).
    
    Shows 4 cards that can be played during the game.
    """
    
    card_clicked = Signal(int)
    card_flip_requested = Signal(int)
    
    def __init__(
        self, 
        theme: ThemeColors | None = None, 
        is_interactive: bool = False,
        parent: QWidget | None = None,
    ):
        from holopazaak.ui.styles import Theme
        super().__init__(parent)
        self.theme = theme or Theme.SITH
        self.is_interactive = is_interactive
        self.card_widgets: list[CardWidget] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the hand layout."""
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create 4 card slots for the hand
        for i in range(4):
            card_widget = CardWidget(
                card=None, 
                index=i, 
                theme=self.theme,
                is_playable=self.is_interactive,
            )
            card_widget.clicked.connect(self._on_card_clicked)
            card_widget.flip_requested.connect(self._on_flip_requested)
            self.card_widgets.append(card_widget)
            layout.addWidget(card_widget)
        
        self.setStyleSheet(f"""
            HandWidget {{
                background-color: {self.theme.get('panel', '#3c3c3c')};
                border: 2px solid #666;
                border-radius: 10px;
            }}
        """)
    
    def _on_card_clicked(self, index: int):
        """Forward card click signal."""
        self.card_clicked.emit(index)
    
    def _on_flip_requested(self, index: int):
        """Forward flip request signal."""
        self.card_flip_requested.emit(index)
    
    def update_hand(self, cards: list, face_down: bool = False):
        """Update the displayed cards."""
        for i, widget in enumerate(self.card_widgets):
            if i < len(cards):
                card = cards[i]
                if face_down:
                    card.is_face_down = True
                widget.set_card(card)
            else:
                widget.set_card(None)
    
    def set_interactive(self, interactive: bool):
        """Set whether cards can be clicked."""
        self.is_interactive = interactive
        for widget in self.card_widgets:
            widget.is_playable = interactive
            if interactive:
                widget.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                widget.setCursor(Qt.CursorShape.ArrowCursor)
    
    def set_theme(self, theme: ThemeColors):
        """Update the theme."""
        self.theme = theme
        for widget in self.card_widgets:
            widget.set_theme(theme)
        
        self.setStyleSheet(f"""
            HandWidget {{
                background-color: {theme.get('panel', '#3c3c3c')};
                border: 2px solid #666;
                border-radius: 10px;
            }}
        """)


class ScoreWidget(QFrame):
    """Widget displaying a player's score and set wins.
    
    Shows:
    - Current round score
    - Sets won (out of 3)
    - Standing indicator
    """
    
    def __init__(
        self, 
        player_name: str = "Player",
        theme: ThemeColors | None = None,
        parent: QWidget | None = None,
    ):
        from holopazaak.ui.styles import Theme
        super().__init__(parent)
        self.theme = theme or Theme.SITH
        self.player_name = player_name
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the score display."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Player name
        self.name_label = QLabel(self.player_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_font = QFont("Arial", 14, QFont.Weight.Bold)
        self.name_label.setFont(name_font)
        layout.addWidget(self.name_label)
        
        # Score display
        self.score_label = QLabel("0")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_font = QFont("Arial", 36, QFont.Weight.Bold)
        self.score_label.setFont(score_font)
        layout.addWidget(self.score_label)
        
        # Sets won
        self.sets_widget = QWidget()
        sets_layout = QHBoxLayout(self.sets_widget)
        sets_layout.setSpacing(5)
        sets_layout.setContentsMargins(0, 0, 0, 0)
        
        self.set_indicators = []
        for i in range(3):
            indicator = QLabel("○")
            indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            indicator.setFont(QFont("Arial", 16))
            self.set_indicators.append(indicator)
            sets_layout.addWidget(indicator)
        
        layout.addWidget(self.sets_widget)
        
        # Standing indicator
        self.standing_label = QLabel("")
        self.standing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.standing_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.standing_label)
        
        self._update_style()
    
    def _update_style(self):
        """Update widget styling."""
        text_color = self.theme.get("text", "#e0e0e0")
        panel_color = self.theme.get("panel", "#3c3c3c")
        
        self.setStyleSheet(f"""
            ScoreWidget {{
                background-color: {panel_color};
                border: 2px solid #555;
                border-radius: 10px;
                padding: 10px;
            }}
            QLabel {{
                color: {text_color};
            }}
        """)
    
    def update_score(self, score: int, is_bust: bool = False):
        """Update the displayed score."""
        self.score_label.setText(str(score))
        
        if is_bust:
            self.score_label.setStyleSheet("color: #FF4444;")
        elif score == 20:
            self.score_label.setStyleSheet("color: #44FF44;")
        else:
            self.score_label.setStyleSheet(f"color: {self.theme.get('text', '#e0e0e0')};")
    
    def update_sets_won(self, sets_won: int):
        """Update the sets won display."""
        for i, indicator in enumerate(self.set_indicators):
            if i < sets_won:
                indicator.setText("●")
                indicator.setStyleSheet("color: #FFD700;")
            else:
                indicator.setText("○")
                indicator.setStyleSheet(f"color: {self.theme.get('text', '#e0e0e0')};")
    
    def set_standing(self, is_standing: bool):
        """Update the standing indicator."""
        if is_standing:
            self.standing_label.setText("STANDING")
            self.standing_label.setStyleSheet("color: #FFD700; font-weight: bold;")
        else:
            self.standing_label.setText("")
    
    def set_active_turn(self, is_active: bool):
        """Highlight when it's this player's turn."""
        if is_active:
            self.setStyleSheet(f"""
                ScoreWidget {{
                    background-color: {self.theme.get('panel', '#3c3c3c')};
                    border: 3px solid #FFD700;
                    border-radius: 10px;
                    padding: 10px;
                }}
                QLabel {{
                    color: {self.theme.get('text', '#e0e0e0')};
                }}
            """)
        else:
            self._update_style()
    
    def set_name(self, name: str):
        """Update player name."""
        self.player_name = name
        self.name_label.setText(name)
    
    def set_theme(self, theme: ThemeColors):
        """Update the theme."""
        self.theme = theme
        self._update_style()


class ActionButton(QPushButton):
    """Styled action button for game controls."""
    
    def __init__(self, text: str, theme: ThemeColors | None = None, parent: QWidget | None = None):
        from holopazaak.ui.styles import Theme
        super().__init__(text, parent)
        self.theme = theme or Theme.SITH
        self._setup_style()
    
    def _setup_style(self):
        """Setup button styling."""
        btn_color = self.theme.get("button", "#4CAF50")
        btn_text = self.theme.get("button_text", "white")
        
        self.setStyleSheet(f"""
            ActionButton {{
                background-color: {btn_color};
                color: {btn_text};
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }}
            ActionButton:hover {{
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {btn_color}, stop:1 #333
                );
            }}
            ActionButton:pressed {{
                background-color: #333;
            }}
            ActionButton:disabled {{
                background-color: #555;
                color: #888;
            }}
        """)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def set_theme(self, theme: ThemeColors):
        """Update the theme."""
        self.theme = theme
        self._setup_style()


class MessageLogWidget(QFrame):
    """Widget for displaying game messages and opponent phrases."""
    
    MAX_MESSAGES = 10
    
    def __init__(self, theme: ThemeColors | None = None, parent: QWidget | None = None):
        from holopazaak.ui.styles import Theme
        super().__init__(parent)
        self.theme = theme or Theme.SITH
        self.messages: list[str] = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the message log."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.message_label = QLabel("")
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.message_label)
        
        self._update_style()
    
    def _update_style(self):
        """Update widget styling."""
        text_color = self.theme.get("text", "#e0e0e0")
        panel_color = self.theme.get("panel", "#3c3c3c")
        
        self.setStyleSheet(f"""
            MessageLogWidget {{
                background-color: {panel_color};
                border: 1px solid #555;
                border-radius: 5px;
            }}
            QLabel {{
                color: {text_color};
                font-size: 12px;
            }}
        """)
    
    def add_message(self, message: str):
        """Add a message to the log."""
        self.messages.append(message)
        
        # Keep only recent messages
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages = self.messages[-self.MAX_MESSAGES:]
        
        self.message_label.setText("\n".join(self.messages))
    
    def clear_messages(self):
        """Clear all messages."""
        self.messages.clear()
        self.message_label.setText("")
    
    def set_theme(self, theme: ThemeColors):
        """Update the theme."""
        self.theme = theme
        self._update_style()

