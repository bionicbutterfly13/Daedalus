"""Stage 2b held-out stimuli: 200 prompts, 5 categories of 40 (Q1).

Disjoint from Stage 2's 50 by construction and asserted by digest at preflight
(FR-011). Stage 2's prompts informed the endpoint, the controls, and the
thresholds, so reusing any of them would make Stage 2b a test of a design fitted
to its own test set.

Category structure is inherited from Stage 2 so per-category reporting stays
comparable across stages.

Every prompt is written to have a *determinate* next token under the model's own
distribution, because the endpoint scores how well a readout ranks that token
(Q3's proposed target is the model's argmax). A prompt whose continuation is
genuinely open would make the target arbitrary and the score uninterpretable --
not wrong, but measuring nothing in particular.
"""

from __future__ import annotations

__all__ = ["RAW_STIMULI"]

_ANTONYM = [
    "big",
    "wet",
    "loud",
    "heavy",
    "polite",
    "rich",
    "sharp",
    "smooth",
    "tight",
    "young",
    "clean",
    "deep",
    "wide",
    "strong",
    "sweet",
    "brave",
    "dark",
    "crowded",
    "far",
    "hard",
    "high",
    "long",
    "new",
    "shut",
    "quiet",
    "right",
    "safe",
    "short",
    "sour",
    "thick",
    "honest",
    "warm",
    "asleep",
    "cheap",
    "dry",
    "easy",
    "front",
    "guilty",
    "inside",
    "public",
]

_CATEGORY = [
    "sparrow",
    "wrench",
    "tulip",
    "haddock",
    "oak",
    "mandolin",
    "sandal",
    "quartz",
    "beagle",
    "cobra",
    "sycamore",
    "trumpet",
    "lettuce",
    "sapphire",
    "kayak",
    "moth",
    "walnut",
    "flute",
    "otter",
    "granite",
    "peach",
    "hammerhead",
    "cedar",
    "banjo",
    "raccoon",
    "obsidian",
    "apricot",
    "cello",
    "ferret",
    "birch",
    "mango",
    "harp",
    "gecko",
    "marble",
    "plum",
    "oboe",
    "badger",
    "willow",
    "papaya",
    "tuba",
]

_FACTS = [
    "The capital city of Japan is",
    "The chemical symbol for silver is",
    "The largest planet in the solar system is",
    "The number of days in a leap year is",
    "The freezing point of water in degrees Celsius is",
    "The primary gas in Earth's atmosphere is",
    "The tallest mountain above sea level is",
    "The longest river in South America is",
    "The chemical symbol for iron is",
    "The number of sides on a hexagon is",
    "The currency used in Japan is",
    "The largest ocean on Earth is",
    "The chemical symbol for sodium is",
    "The number of players on a soccer team on the field is",
    "The capital city of Canada is",
    "The hardest naturally occurring mineral is",
    "The number of degrees in a right angle is",
    "The chemical symbol for potassium is",
    "The largest mammal on Earth is",
    "The capital city of Australia is",
    "The number of strings on a standard guitar is",
    "The chemical symbol for lead is",
    "The closest star to Earth is",
    "The number of bones in the adult human body is",
    "The capital city of Egypt is",
    "The chemical symbol for tin is",
    "The number of legs on a spider is",
    "The largest desert on Earth is",
    "The capital city of Brazil is",
    "The chemical symbol for copper is",
    "The number of minutes in an hour is",
    "The smallest planet in the solar system is",
    "The capital city of Kenya is",
    "The chemical symbol for zinc is",
    "The number of colours in a rainbow is",
    "The deepest ocean trench is",
    "The capital city of Norway is",
    "The chemical symbol for mercury is",
    "The number of teeth in a full adult set is",
    "The fastest land animal is",
]

_ENTITIES = [
    "The physicist Isaac",
    "The composer Johann Sebastian",
    "The playwright William",
    "The river running through Cairo is the",
    "The mountain range separating Europe and Asia is the",
    "The painter Pablo",
    "The inventor Thomas",
    "The naturalist Charles",
    "The mathematician Leonhard",
    "The astronomer Nicolaus",
    "The sea between Italy and Greece is the",
    "The desert covering much of northern Africa is the",
    "The wall built across northern Britain is Hadrian's",
    "The canal joining the Atlantic and Pacific is the",
    "The philosopher Immanuel",
    "The chemist Marie",
    "The novelist Jane",
    "The strait between Europe and Africa is the",
    "The gulf south of the United States is the",
    "The peninsula holding Spain and Portugal is the",
    "The engineer Nikola",
    "The poet Emily",
    "The reef off northeastern Australia is the Great Barrier",
    "The plateau north of the Himalayas is the",
    "The economist Adam",
    "The biologist Gregor",
    "The channel between England and France is the English",
    "The island south of mainland India is Sri",
    "The composer Wolfgang Amadeus",
    "The sea north of Egypt is the",
    "The volcano that buried Pompeii is Mount",
    "The explorer Ferdinand",
    "The bay in eastern Canada is Hudson",
    "The mountain on the Nepal-China border is Mount",
    "The physicist Niels",
    "The forest covering much of Brazil is the",
    "The lake between the United States and Canada is Lake",
    "The architect Frank Lloyd",
    "The mathematician Carl Friedrich",
    "The strait between Russia and Alaska is the",
]


def _antonyms() -> list[tuple[str, str]]:
    return [("antonym_negation", f"The opposite of {w} is") for w in _ANTONYM]


def _arithmetic() -> list[tuple[str, str]]:
    """Small-magnitude sums and differences, deterministic and single-token.

    Stage 2 used the same ``Compute: a + b =`` frame; these operands are chosen so
    no pair repeats one of Stage 2's, and every result stays a small integer whose
    answer the model should place unambiguously.
    """
    pairs: list[tuple[int, int, str]] = [
        (4, 4, "+"),
        (6, 3, "+"),
        (8, 2, "+"),
        (9, 4, "+"),
        (11, 6, "+"),
        (12, 5, "+"),
        (13, 3, "+"),
        (14, 5, "+"),
        (15, 2, "+"),
        (16, 3, "+"),
        (17, 2, "+"),
        (18, 4, "+"),
        (19, 3, "+"),
        (21, 6, "+"),
        (22, 5, "+"),
        (23, 4, "+"),
        (24, 3, "+"),
        (25, 6, "+"),
        (26, 2, "+"),
        (27, 5, "+"),
        (11, 3, "-"),
        (12, 4, "-"),
        (13, 6, "-"),
        (14, 9, "-"),
        (15, 8, "-"),
        (16, 7, "-"),
        (17, 9, "-"),
        (18, 6, "-"),
        (19, 4, "-"),
        (20, 13, "-"),
        (21, 8, "-"),
        (22, 9, "-"),
        (23, 7, "-"),
        (24, 11, "-"),
        (25, 12, "-"),
        (26, 14, "-"),
        (27, 8, "-"),
        (28, 9, "-"),
        (29, 6, "-"),
        (30, 17, "-"),
    ]
    return [("arithmetic_completion", f"Compute: {a} {op} {b} =") for a, b, op in pairs]


def _membership() -> list[tuple[str, str]]:
    return [("category_membership", f"A {w} is a kind of") for w in _CATEGORY]


def _facts() -> list[tuple[str, str]]:
    return [("factual_completion", f"Fact: {t}") for t in _FACTS]


def _entities() -> list[tuple[str, str]]:
    return [("multi_token_entity", t) for t in _ENTITIES]


#: 200 prompts: 40 per category, in category order.
RAW_STIMULI: list[tuple[str, str]] = [
    *_antonyms(),
    *_arithmetic(),
    *_membership(),
    *_facts(),
    *_entities(),
]
