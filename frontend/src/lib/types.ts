export interface Horse {
  id: string;
  name: string;
  age: number;
  gender: string;
  status: string;
  speed: number;
  endurance: number;
  mentality: number;
  start_ability: number;
  sprint_strength: number;
  balance: number;
  strength: number;
  condition: number;
  form: number;
  mood: number;
  energy: number;
  weight: number;
  gallop_tendency: number;
  career_wins: number;
  career_races: number;
  career_earnings: number;
  current_shoe: string;
  training_program: string | null;
}

export interface Driver {
  id: string;
  name: string;
  skill: number;
  start_skill: number;
  tactical_ability: number;
  sprint_timing: number;
  gallop_handling: number;
  experience: number;
  composure: number;
  driving_style: string;
  contract_weeks_left: number;
  weekly_salary: number;
}

export interface Race {
  id: string;
  race_class: string;
  distance: number;
  start_method: string;
  prize_pool: number;
  max_entries: number;
  current_entries: number;
  track_name: string;
  player_entered: boolean;
}

export interface RaceSession {
  id: string;
  session_date: string;
  track_name: string;
  weather: string;
  races: Race[];
  simulated: boolean;
}

export interface FinishResult {
  position: number;
  horse_name: string;
  driver_name: string;
  km_time: string;
  prize_money: number;
  is_player: boolean;
}

export interface Event {
  id: string;
  event_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface StableSummary {
  id: string;
  name: string;
  balance: number;
  reputation: number;
  fan_count: number;
  horse_count: number;
  division_name: string;
}

export interface Transaction {
  id: string;
  category: string;
  description: string;
  amount: number;
  game_week: number;
  created_at: string;
}
