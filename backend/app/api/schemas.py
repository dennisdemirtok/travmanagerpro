"""TravManager — API Request/Response Schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# === AUTH ===
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)
    stable_name: str = Field(min_length=2, max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    stable: dict


# === STABLE ===
class StableSummary(BaseModel):
    id: UUID
    name: str
    reputation: int
    fan_count: int
    balance: int
    division: Optional[dict] = None
    horse_count: int
    horses_ready: int
    next_race: Optional[dict] = None
    weekly_income: int = 0
    weekly_expenses: int = 0


class MorningReport(BaseModel):
    game_week: int
    game_day: int
    horse_statuses: list[dict]
    todos: list[dict]
    balance: int
    balance_change_24h: int = 0
    events: list[dict] = []


# === HORSE ===
class HorseListItem(BaseModel):
    id: UUID
    name: str
    gender: str
    age_years: int
    status: str
    speed: int
    endurance: int
    mentality: int
    start_ability: int
    sprint_strength: int
    balance: int
    strength: int
    condition: int
    energy: int
    health: int
    form: int
    fatigue: int
    mood: int
    current_weight: float
    total_starts: int
    total_wins: int
    total_earnings: int
    best_km_time_display: Optional[str] = None
    current_training: Optional[str] = None
    current_shoe: str
    trend: str = "stable"


class HorseDetail(HorseListItem):
    ideal_weight: float
    gallop_tendency: Optional[int] = None
    personality_primary: Optional[str] = None
    personality_secondary: Optional[str] = None
    distance_optimum: Optional[int] = None
    surface_preference: Optional[str] = None
    training_intensity: Optional[str] = None
    shoe_durability: int = 6
    total_seconds: int = 0
    total_thirds: int = 0
    total_dq: int = 0
    bloodline_name: Optional[str] = None
    sire_name: Optional[str] = None
    dam_name: Optional[str] = None
    form_last_5: list[int] = []
    compatibility_with_drivers: list[dict] = []
    feed_plan: list[dict] = []


class ChangeShoeRequest(BaseModel):
    shoe_type: str
    farrier_quality: str = "basic"


class ChangeTrainingRequest(BaseModel):
    program: str
    intensity: str = "normal"


class UpdateFeedItem(BaseModel):
    feed_type: str
    percentage: int


class UpdateFeedRequest(BaseModel):
    feeds: list[UpdateFeedItem]


class UpdateTacticsRequest(BaseModel):
    positioning: Optional[str] = None
    tempo: Optional[str] = None
    sprint_order: Optional[str] = None
    gallop_safety: Optional[str] = None
    curve_strategy: Optional[str] = None
    whip_usage: Optional[str] = None


class PressReleaseRequest(BaseModel):
    tone: str  # humble, confident, provocative
    content: str = Field(min_length=10, max_length=500)


class DriverContractRequest(BaseModel):
    contract_type: str  # permanent, guest, apprentice
    weeks: int = 16


# === DRIVER ===
class DriverItem(BaseModel):
    id: UUID
    name: str
    skill: int
    start_skill: int
    tactical_ability: int
    sprint_timing: int
    gallop_handling: int
    experience: int
    composure: int
    driving_style: str
    contract_type: Optional[str] = None
    salary_per_week: Optional[int] = None
    is_active: bool = True


class CompatibilityResult(BaseModel):
    score: int
    label: str
    performance_mod: str
    gallop_risk_mod: str
    breakdown: dict


# === RACE ===
class TacticsInput(BaseModel):
    positioning: str = "second"
    tempo: str = "balanced"
    sprint_order: str = "normal_400m"
    gallop_safety: str = "normal"
    curve_strategy: str = "middle"
    whip_usage: str = "normal"


class RaceEntryRequest(BaseModel):
    horse_id: UUID
    driver_id: UUID
    shoe: str = "normal_steel"
    tactics: TacticsInput = TacticsInput()


class RaceItem(BaseModel):
    id: UUID
    race_name: str
    race_class: str
    distance: int
    start_method: str
    prize_pool: int
    entry_fee: int
    current_entries: int = 0
    max_entries: int = 12
    your_entries: list[dict] = []
    division_level: Optional[int] = None
    surface: str = "dirt"


class RaceSessionItem(BaseModel):
    id: UUID
    scheduled_at: datetime
    track_name: str
    track_city: str
    weather: str
    temperature: int
    races: list[RaceItem]
    is_simulated: bool = False


class FinisherResult(BaseModel):
    position: int
    horse_name: str
    horse_id: UUID
    driver_name: str
    km_time: str
    prize_money: int
    energy_at_finish: int = 0
    gallop_incidents: int = 0
    driver_rating: int = 5
    compatibility: int = 50
    is_npc: bool = False
    sector_times: list[dict] = []


class RaceResultResponse(BaseModel):
    race_id: UUID
    race_name: str
    distance: int
    start_method: str
    track: str
    weather: str
    finishers: list[FinisherResult]
    disqualified: list[dict] = []
    events: list[dict] = []


# === FINANCE ===
class FinancialOverview(BaseModel):
    balance: int
    weekly_summary: dict
    trend_8_weeks: list[int] = []
    sponsors: list[dict] = []


class TransactionItem(BaseModel):
    id: UUID
    amount: int
    category: str
    description: Optional[str] = None
    game_week: int
    created_at: datetime


# === EVENT ===
class EventItem(BaseModel):
    id: UUID
    event_type: str
    title: str
    description: Optional[str] = None
    is_read: bool
    requires_action: bool
    action_data: Optional[dict] = None
    game_week: int
    created_at: datetime


# === GAME STATE ===
class GameStateResponse(BaseModel):
    current_game_week: int
    current_game_day: int
    current_season: Optional[int] = None
    season_period: Optional[str] = None
    next_race_at: Optional[datetime] = None
    total_players: int = 0
