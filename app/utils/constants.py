APP_VERSION = "1.0.0-rc1"

APP_BG = "#0A0A0D"
CARD_BG = "#141419"
CARD_BG_ALT = "#191920"
BORDER = "#282832"
TEXT_PRIMARY = "#F7F7FA"
TEXT_MUTED = "#9292A1"
ACCENT = "#7C5CFC"
ACCENT_SOFT = "#26203E"
SUCCESS = "#62D99A"
SUCCESS_SOFT = "#153326"
STREAK = "#FF9A4A"
STREAK_SOFT = "#3A2417"
DANGER = "#FF6B72"

HABIT_CATEGORIES = [
    "Fitness",
    "Health",
    "Study",
    "Coding",
    "Mental Health",
    "Personal Growth",
    "Nutrition",
    "Sleep",
    "Productivity",
    "Custom",
]

WEEKDAY_CODES = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
WEEKDAY_LABELS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

MOTIVATION = (
    "Consistency beats motivation.",
    "Don't break the streak.",
    "Small wins become massive results.",
    "You're building the person you said you wanted to become.",
)

STARTER_HABITS = [
    {"name": "10,000 Steps", "icon": "directions_walk", "category": "Fitness", "goal_type": "number", "goal_amount": 10000, "unit": "steps", "required": 1, "schedule": "daily"},
    {"name": "Workout", "icon": "fitness_center", "category": "Fitness", "goal_type": "boolean", "goal_amount": 1, "unit": "completion", "required": 1, "schedule": "daily"},
    {"name": "Water", "icon": "water_drop", "category": "Health", "goal_type": "number", "goal_amount": 3500, "unit": "ml", "required": 1, "schedule": "daily"},
    {"name": "Study", "icon": "school", "category": "Study", "goal_type": "number", "goal_amount": 120, "unit": "minutes", "required": 1, "schedule": "daily"},
    {"name": "Coding / Skill Learning", "icon": "code", "category": "Coding", "goal_type": "boolean", "goal_amount": 1, "unit": "completion", "required": 1, "schedule": "daily"},
    {"name": "Skincare", "icon": "spa", "category": "Personal Growth", "goal_type": "boolean", "goal_amount": 1, "unit": "completion", "required": 1, "schedule": "daily"},
    {"name": "Read", "icon": "menu_book", "category": "Personal Growth", "goal_type": "boolean", "goal_amount": 1, "unit": "completion", "required": 0, "schedule": "daily"},
    {"name": "Sleep on Time", "icon": "bedtime", "category": "Sleep", "goal_type": "boolean", "goal_amount": 1, "unit": "completion", "required": 1, "schedule": "daily"},
]
