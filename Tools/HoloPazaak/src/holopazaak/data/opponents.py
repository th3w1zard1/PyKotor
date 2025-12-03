"""Opponent profiles for HoloPazaak.

This module contains all opponent profiles combining characters from:
- pazaak-eggborne: Star Wars and pop culture characters with unique strategies
- pazaak-iron-ginger: Character phrases for different game events
- Java_Pazaak: AI complexity levels

Each opponent has:
- Unique sideboard deck configuration
- Stand threshold (when they choose to stand)
- Tie acceptance probability
- Character quotes/phrases

References:
- vendor/pazaak-eggborne/src/scripts/characters.js: lines 1-750
- vendor/pazaak-iron-ginger/modules/tertiary/opponents.py: lines 1-205
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from holopazaak.game.card import CardType  # type: ignore[import-not-found, note]


class OpponentDifficulty(Enum):
    """Opponent difficulty tiers."""
    NOVICE = auto()      # Very easy
    EASY = auto()        # Beginner-friendly
    NORMAL = auto()      # Balanced
    HARD = auto()        # Challenging
    EXPERT = auto()      # Very challenging
    MASTER = auto()      # Near-perfect play


@dataclass
class OpponentPhrases:
    """Character quotes for different game events.
    
    Based on pazaak-iron-ginger phrases system.
    """
    chosen: str = ""       # When opponent is selected
    play: str = ""         # When playing a card
    stand: str = ""        # When standing
    win_round: str = ""    # When winning a round
    lose_round: str = ""   # When losing a round
    win_game: str = ""     # When winning the match
    lose_game: str = ""    # When losing the match


@dataclass
class OpponentProfile:
    """Complete opponent profile.
    
    Attributes:
        id: Unique identifier
        name: Display name
        description: Flavor text description
        sideboard: Deck configuration as list of (value, CardType)
        stand_at: Score threshold to stand (higher = more aggressive)
        tie_chance: Probability (0-100) to accept a tie instead of risking
        difficulty: Difficulty tier for organization
        species: Character species (for flavor)
        origin: Character origin location
        skill_level: Numeric skill rating 1-20
        prizes: Credits and card rewards for winning
        phrases: Character quotes
    """
    id: str
    name: str
    description: str
    sideboard: list[tuple[int, CardType]]
    stand_at: int = 17
    tie_chance: int = 50
    difficulty: OpponentDifficulty = OpponentDifficulty.NORMAL
    species: str = "Human"
    origin: str = "Unknown"
    skill_level: int = 5
    prizes: dict = field(default_factory=dict)
    phrases: OpponentPhrases = field(default_factory=OpponentPhrases)


# =============================================================================
# OPPONENT DEFINITIONS
# Organized by difficulty tier, porting all characters from vendor projects
# =============================================================================

OPPONENTS = [
    # =========================================================================
    # NOVICE TIER
    # =========================================================================
    OpponentProfile(
        id="jarjar",
        name="Jar Jar Binks",
        description="Meesa not be understandin' the rules too good.",
        species="Gungan",
        origin="Naboo",
        skill_level=1,
        difficulty=OpponentDifficulty.NOVICE,
        stand_at=15,
        tie_chance=100,  # Always accepts ties
        sideboard=[
            (1, CardType.PLUS), (1, CardType.PLUS), (2, CardType.PLUS),
            (2, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (1, CardType.MINUS), (2, CardType.MINUS),
            (2, CardType.MINUS), (5, CardType.MINUS),
        ],
        prizes={"credits": 25, "cards": []},
        phrases=OpponentPhrases(
            chosen="Meesa gonna play da Pazaak with yousa!",
            play="Meesa hope dis works!",
            stand="Meesa staying right here!",
            win_round="Wesa winning!",
            lose_round="Oh no, meesa bombad!",
            win_game="Yousa no match for meesa!",
            lose_game="Ohhh, meesa clumsy.",
        ),
    ),
    
    # =========================================================================
    # EASY TIER
    # =========================================================================
    OpponentProfile(
        id="c3po",
        name="C-3PO",
        description="Please go easy on me. I've just had my logic units calibrated.",
        species="Droid",
        origin="Tatooine",
        skill_level=2,
        difficulty=OpponentDifficulty.EASY,
        stand_at=16,
        tie_chance=80,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (1, CardType.PLUS),
            (2, CardType.MINUS), (3, CardType.MINUS), (1, CardType.MINUS),
        ],
        prizes={"credits": 75, "cards": []},
        phrases=OpponentPhrases(
            chosen="Oh my! I do hope this game doesn't void my warranty.",
            play="I calculate this is the optimal play... probably.",
            stand="I shall remain at this position, if you don't mind.",
            win_round="Oh! Did I actually win? How unexpected!",
            lose_round="Oh dear. That did not go according to my calculations.",
            win_game="I'm quite surprised myself, I assure you!",
            lose_game="I told you I wasn't programmed for this!",
        ),
    ),
    
    OpponentProfile(
        id="butters",
        name="Butters",
        description="Everyone knows it's Butters! That's me!",
        species="Human",
        origin="South Park",
        skill_level=2,
        difficulty=OpponentDifficulty.EASY,
        stand_at=16,
        tie_chance=70,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (1, CardType.PLUS), (2, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
            (1, CardType.MINUS), (2, CardType.MINUS),
        ],
        prizes={"credits": 50, "cards": []},
        phrases=OpponentPhrases(
            chosen="*Everyone knows, it's Butters!* That's me!",
            play="Do you know what I am saying?",
            stand="I love bringing chaos!",
            win_round="This puny world will bow down to me!",
            lose_round="Oh great Jesus, son of Mary, wife of Joseph!",
            win_game="I am the greatest supervillain! Professor Chaos!",
            lose_game="Oh, hamburgers!",
        ),
    ),
    
    # =========================================================================
    # NORMAL TIER
    # =========================================================================
    OpponentProfile(
        id="porkins",
        name="Porkins",
        description="I can hold it. Give me more room to run.",
        species="Human",
        origin="Bestine IV",
        skill_level=3,
        difficulty=OpponentDifficulty.NORMAL,
        stand_at=17,
        tie_chance=50,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (1, CardType.PLUS), (2, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
            (1, CardType.MINUS), (2, CardType.MINUS),
        ],
        prizes={"credits": 150, "cards": []},
        phrases=OpponentPhrases(
            chosen="I can hold it. Give me room to run!",
            play="Cover me, I'm going in!",
            stand="I'll hold this position!",
            win_round="Got 'em!",
            lose_round="I've got a problem here...",
            win_game="Red Six standing by... victorious!",
            lose_game="Eject! Eject!",
        ),
    ),
    
    OpponentProfile(
        id="hk47",
        name="HK-47",
        description="Query: Is there someone you need killed, meatbag?",
        species="Droid",
        origin="Revan's Workshop",
        skill_level=4,
        difficulty=OpponentDifficulty.NORMAL,
        stand_at=17,
        tie_chance=40,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
            (4, CardType.MINUS), (5, CardType.MINUS),
        ],
        prizes={"credits": 200, "cards": []},
        phrases=OpponentPhrases(
            chosen="Query: Is there someone you need killed, meatbag?",
            play="Musing: My motivators have experienced a sudden burst of energy!",
            stand="Smug statement: I hope you enjoy the taste of defeat, meatbag.",
            win_round="Amused Query: How does it feel to lose, meatbag?",
            lose_round="Musing: This game is 90 percent luck anyways.",
            win_game="Recitation: You lose, meatbag.",
            lose_game="Resentful Accolade: Congratulations... meatbag.",
        ),
    ),
    
    OpponentProfile(
        id="hal",
        name="HAL 9000",
        description="Hello, Dave. Shall we play a game?",
        species="AI",
        origin="Discovery One",
        skill_level=4,
        difficulty=OpponentDifficulty.NORMAL,
        stand_at=17,
        tie_chance=30,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (4, CardType.PLUS), (1, CardType.FLIP),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
            (2, CardType.FLIP), (3, CardType.FLIP),
        ],
        prizes={"credits": 200, "cards": []},
        phrases=OpponentPhrases(
            chosen="Hello, Dave.",
            play="I'm sorry, Dave.",
            stand="I'm afraid I can't do that, Dave.",
            win_round="Look Dave, I think you ought to take a stress pill.",
            lose_round="What are you doing, Dave?",
            win_game="Dave, this conversation can serve no purpose anymore. Goodbye.",
            lose_game="I can give you my complete assurance that my work will be back to normal.",
        ),
    ),
    
    OpponentProfile(
        id="republic_soldier",
        name="Republic Soldier",
        description="Standard military training, nothing fancy.",
        species="Human",
        origin="Coruscant",
        skill_level=4,
        difficulty=OpponentDifficulty.NORMAL,
        stand_at=17,
        tie_chance=50,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS), (3, CardType.MINUS),
            (4, CardType.MINUS), (5, CardType.MINUS),
        ],
        prizes={"credits": 100, "cards": []},
        phrases=OpponentPhrases(
            chosen="For the Republic!",
            play="Standard tactics.",
            stand="Holding position.",
            win_round="Mission accomplished.",
            lose_round="We'll regroup.",
            win_game="Victory for the Republic!",
            lose_game="I'll report back to command.",
        ),
    ),
    
    # =========================================================================
    # HARD TIER  
    # =========================================================================
    OpponentProfile(
        id="ig88",
        name="IG-88",
        description="MISSION: DESTROY PLAYER",
        species="Droid",
        origin="Holowan",
        skill_level=5,
        difficulty=OpponentDifficulty.HARD,
        stand_at=18,
        tie_chance=30,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
        ],
        prizes={"credits": 300, "cards": []},
        phrases=OpponentPhrases(
            chosen="TARGET ACQUIRED. INITIATING PAZAAK PROTOCOL.",
            play="CALCULATING OPTIMAL MOVE.",
            stand="STANDING. AWAITING TARGET RESPONSE.",
            win_round="TARGET NEUTRALIZED.",
            lose_round="RECALCULATING STRATEGY.",
            win_game="MISSION COMPLETE. TARGET ELIMINATED.",
            lose_game="SYSTEM ERROR. MISSION FAILED.",
        ),
    ),
    
    OpponentProfile(
        id="trump",
        name="Donald Trump",
        description="Nobody plays Pazaak better than me. Believe me.",
        species="Human",
        origin="Earth",
        skill_level=5,
        difficulty=OpponentDifficulty.HARD,
        stand_at=18,
        tie_chance=20,
        sideboard=[
            (1, CardType.PLUS), (2, CardType.PLUS), (3, CardType.PLUS),
            (4, CardType.PLUS), (5, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
        ],
        prizes={"credits": 350, "cards": []},
        phrases=OpponentPhrases(
            chosen="I have never seen a thin person drinking Diet Coke.",
            play="I am the BEST builder, just look at what I've built!",
            stand="Windmills are the greatest threat in the US.",
            win_round="Nobody knows jobs like I do!",
            lose_round="Fake News!",
            win_game="I am least racist person there is.",
            lose_game="Why is Obama playing basketball today?",
        ),
    ),
    
    # =========================================================================
    # EXPERT TIER
    # =========================================================================
    OpponentProfile(
        id="yoda",
        name="Yoda",
        description="Underestimated not, will I be. Beat you handily I will.",
        species="Unknown",
        origin="Dagobah",
        skill_level=6,
        difficulty=OpponentDifficulty.EXPERT,
        stand_at=18,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
        ],
        prizes={"credits": 600, "cards": []},
        phrases=OpponentPhrases(
            chosen="Play Pazaak, we shall. Hmmmm.",
            play="Wise, this move is.",
            stand="Stand, I will. Strong in the Force, my position is.",
            win_round="Expected, this outcome was.",
            lose_round="Clouded, the future is. Lose sometimes, even Jedi do.",
            win_game="Powerful you have become, but not enough.",
            lose_game="Impressed, I am. Learn from defeat, I will.",
        ),
    ),
    
    OpponentProfile(
        id="theemperor",
        name="The Emperor",
        description="In time you will call me Master.",
        species="Human",
        origin="Naboo",
        skill_level=7,
        difficulty=OpponentDifficulty.EXPERT,
        stand_at=19,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
        ],
        prizes={"credits": 1200, "cards": []},
        phrases=OpponentPhrases(
            chosen="Your feeble skills are no match for the power of the Dark Side.",
            play="Everything proceeds as I have foreseen.",
            stand="Now witness the firepower of this fully armed position!",
            win_round="Your faith in your cards was misplaced.",
            lose_round="Your overconfidence is your weakness.",
            win_game="Now, young Skywalker... you will lose.",
            lose_game="No... NO! You were supposed to lose!",
        ),
    ),
    
    OpponentProfile(
        id="revan",
        name="Darth Revan",
        description="The prodigal knight returns.",
        species="Human",
        origin="Unknown",
        skill_level=8,
        difficulty=OpponentDifficulty.EXPERT,
        stand_at=19,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (6, CardType.FLIP),
            (1, CardType.PLUS), (2, CardType.PLUS),
            (1, CardType.MINUS), (2, CardType.MINUS),
        ],
        prizes={"credits": 1500, "cards": []},
        phrases=OpponentPhrases(
            chosen="I remember... everything.",
            play="As the Force wills.",
            stand="I've seen this outcome before.",
            win_round="The path ahead is clear.",
            lose_round="Even I can be surprised.",
            win_game="The galaxy shall know peace... my way.",
            lose_game="Perhaps redemption takes many forms.",
        ),
    ),
    
    # =========================================================================
    # MASTER TIER
    # =========================================================================
    OpponentProfile(
        id="t1000",
        name="The T-1000",
        description="Say... that's a nice deck.",
        species="Cyborg",
        origin="Earth (Future)",
        skill_level=9,
        difficulty=OpponentDifficulty.MASTER,
        stand_at=19,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
        ],
        prizes={"credits": 4000, "cards": []},
        phrases=OpponentPhrases(
            chosen="Say... that's a nice deck.",
            play="ANALYZING.",
            stand="OPTIMAL POSITION ACHIEVED.",
            win_round="RESISTANCE IS FUTILE.",
            lose_round="TEMPORARY SETBACK DETECTED.",
            win_game="TARGET TERMINATED.",
            lose_game="I'LL BE BACK.",
        ),
    ),
    
    OpponentProfile(
        id="drchannard",
        name="Dr. Channard",
        description="And to think I hesitated.",
        species="Cenobite",
        origin="The Labyrinth",
        skill_level=10,
        difficulty=OpponentDifficulty.MASTER,
        stand_at=19,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
        ],
        prizes={"credits": 12000, "cards": []},
        phrases=OpponentPhrases(
            chosen="And to think... I hesitated.",
            play="The mind is a labyrinth.",
            stand="I have such sights to show you.",
            win_round="Your suffering will be legendary.",
            lose_round="Pain has a face. Allow me to show you.",
            win_game="Hell has no limits.",
            lose_game="Impossible... I was promised eternity!",
        ),
    ),
    
    OpponentProfile(
        id="blaine",
        name="Blaine the Mono",
        description="I WILL TIRE QUICKLY OF BESTING YOU IN THIS SIMPLE ANCIENT GAME.",
        species="AI",
        origin="Mid-World",
        skill_level=12,
        difficulty=OpponentDifficulty.MASTER,
        stand_at=20,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
        ],
        prizes={"credits": 500000, "cards": []},
        phrases=OpponentPhrases(
            chosen="I WILL TIRE QUICKLY OF BESTING YOU IN THIS SIMPLE ANCIENT GAME.",
            play="CALCULATION COMPLETE.",
            stand="DO YOU KNOW THE RIDDLE OF THIS POSITION?",
            win_round="PREDICTABLE. BORING. NEXT.",
            lose_round="A RIDDLE I DID NOT EXPECT.",
            win_game="THE GAME IS DONE. YOUR JOURNEY ENDS.",
            lose_game="AAASK ME A RIDDDDLE!",
        ),
    ),
    
    OpponentProfile(
        id="nu",
        name="Nu",
        description="All matches begin with Nu and end with Nu.",
        species="Unknown",
        origin="Unknown",
        skill_level=20,
        difficulty=OpponentDifficulty.MASTER,
        stand_at=20,
        tie_chance=0,
        sideboard=[
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
            (1, CardType.FLIP), (2, CardType.FLIP), (3, CardType.FLIP),
            (4, CardType.FLIP), (5, CardType.FLIP),
        ],
        prizes={"credits": 99999999, "cards": []},
        phrases=OpponentPhrases(
            chosen="The Beginning and the End... is Nu.",
            play="...",
            stand="All paths lead to Nu.",
            win_round="This outcome was written in the stars.",
            lose_round="Even infinity contains surprises.",
            win_game="All matches begin with Nu and end with Nu.",
            lose_game="Interesting... most interesting.",
        ),
    ),
]


def get_opponent(opp_id: str) -> OpponentProfile:
    """Get an opponent profile by ID.
    
    Returns the first opponent (Jar Jar) if ID not found.
    """
    for opp in OPPONENTS:
        if opp.id == opp_id:
            return opp
    return OPPONENTS[0]


def get_opponents_by_difficulty(difficulty: OpponentDifficulty) -> list[OpponentProfile]:
    """Get all opponents of a specific difficulty."""
    return [opp for opp in OPPONENTS if opp.difficulty == difficulty]


def get_all_opponent_ids() -> list[str]:
    """Get list of all opponent IDs."""
    return [opp.id for opp in OPPONENTS]


def get_random_opponent(difficulty: OpponentDifficulty | None = None) -> OpponentProfile:
    """Get a random opponent, optionally filtered by difficulty."""
    import random
    
    if difficulty:
        pool = get_opponents_by_difficulty(difficulty)
    else:
        pool = OPPONENTS
    
    return random.choice(pool)
