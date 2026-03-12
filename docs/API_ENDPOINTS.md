# TravManager — Complete API Specification
## All endpoints, request/response schemas

Base URL: `http://localhost:8000/api/v1`

---

## AUTH

### POST /auth/register
```json
Request:  { "username": "string", "email": "string", "password": "string", "stable_name": "string" }
Response: { "user_id": "uuid", "stable_id": "uuid", "token": "jwt_string" }
```
Side effects: Creates user + stable + 4 starter horses + 1 starter driver + basic facilities

### POST /auth/login
```json
Request:  { "email": "string", "password": "string" }
Response: { "access_token": "jwt", "refresh_token": "jwt", "user": {...}, "stable": {...} }
```

### POST /auth/refresh
```json
Request:  { "refresh_token": "string" }
Response: { "access_token": "jwt" }
```

---

## STABLE

### GET /stable
Returns current user's stable with summary stats.
```json
Response: {
  "id": "uuid",
  "name": "string",
  "reputation": 10,
  "fan_count": 100,
  "balance": 20000000,           // öre
  "division": { "level": 6, "name": "Bronsdivisionen", "rank": 3 },
  "horse_count": 4,
  "horses_ready": 3,
  "next_race": { "name": "...", "time": "2024-01-15T19:30:00Z" },
  "weekly_income": 6800000,
  "weekly_expenses": 5200000
}
```

### GET /stable/morning-report
Daily summary of stable status.
```json
Response: {
  "game_week": 35,
  "game_day": 3,
  "horse_statuses": [
    { "id": "uuid", "name": "Bliansen", "status": "ready", "alerts": [], "mood": 80 },
    { "id": "uuid", "name": "Expressen", "status": "ready", "alerts": ["Stel i bakbenet"], "mood": 65 }
  ],
  "todos": [
    { "type": "race_entry", "text": "Anmäl till kvällslopp (deadline 15:00)", "urgent": true },
    { "type": "vet_check", "text": "Expressens veterinärkontroll" }
  ],
  "balance": 48725000,
  "balance_change_24h": 1600000,
  "events": [...]
}
```

### POST /stable/daily-checkup
Perform daily horse checkup (required for mood).
```json
Request:  {}
Response: { "horses_checked": 5, "mood_bonus_applied": true, "issues_found": [...] }
```

### POST /stable/press-release
Write a press release for PR points and income.
```json
Request:  { "tone": "humble|confident|provocative", "content": "string (optional, auto-generated if empty)" }
Response: { "pr_points": 15, "income": 200000, "reputation_change": 2 }
```

---

## HORSES

### GET /horses
List all horses in stable.
```json
Query: ?status=ready|fatigued|injured|all&sort=speed|earnings|age
Response: { "horses": [HorseObject, ...], "total": 5 }
```

### GET /horses/{id}
Full horse detail with all visible stats.
```json
Response: {
  "id": "uuid",
  "name": "Bliansen",
  "gender": "stallion",
  "age_years": 5,
  "status": "ready",
  "stats": {
    "speed": 78, "endurance": 82, "mentality": 71,
    "start_ability": 85, "sprint_strength": 74,
    "balance": 65, "strength": 70
  },
  "physical": {
    "condition": 92, "energy": 88, "health": 88,
    "weight": 485.0, "ideal_weight": 480.0,
    "form": 65, "fatigue": 15, "mood": 80
  },
  "hidden": {
    "gallop_tendency": 12,           // Only if scouted or owned long enough
    "personality_primary": "brave",  // Only if scouted
    "personality_secondary": "responsive",
    "distance_optimum": 2140,
    "surface_preference": null
  },
  "equipment": {
    "shoe": "light_aluminum",
    "shoe_durability_remaining": 4,
    "training": "interval",
    "training_intensity": "normal"
  },
  "career": {
    "total_starts": 24, "wins": 8, "seconds": 5, "thirds": 3, "dq": 1,
    "total_earnings": 34200000,
    "best_km_time": "1.12,4",
    "win_percentage": 33.3,
    "form_last_5": [2, 1, 4, 1, 3]
  },
  "pedigree": {
    "sire": { "id": "uuid", "name": "Expressen", "best_time": "1.11,8" },
    "dam": { "id": "uuid", "name": "Guldstjärnan", "best_time": "1.13,2" },
    "bloodline": "Expressenlinjen"
  },
  "feed_plan": [...],
  "compatibility_with_drivers": [
    { "driver_id": "uuid", "driver_name": "Erik Lindblom", "score": 78, "label": "Utmärkt" },
    { "driver_id": "uuid", "driver_name": "Anna Svensson", "score": 52, "label": "Bra" }
  ],
  "fatigue_recovery": {
    "current_readiness": 85,
    "full_recovery_at": "2024-01-16T08:00:00Z",
    "can_race_today": true,
    "recommended_wait": "1 speldag"
  }
}
```

### PUT /horses/{id}/training
Change training program.
```json
Request:  { "program": "interval|long_distance|start_training|sprint_training|mental_training|strength_training|balance_training|swim_training|track_training|rest", "intensity": "light|normal|hard|maximum" }
Response: { "success": true, "weekly_cost": 450000, "expected_gains": { "speed": 0.4, "endurance": 0.2 } }
```

### PUT /horses/{id}/feed
Update feed plan.
```json
Request:  { "feeds": [ { "type": "hay_premium", "percentage": 55 }, { "type": "oats", "percentage": 20 }, ... ] }
Response: { "success": true, "weekly_cost": 39700, "weight_trend": "stable" }
```

### PUT /horses/{id}/shoe
Change shoeing.
```json
Request:  { "shoe_type": "light_aluminum|normal_steel|...", "farrier_quality": "basic|experienced|elite" }
Response: { "success": true, "cost": 180000, "durability": 4, "effects": { "speed_mod": 1.01, "gallop_risk_mod": 1.05 } }
```

---

## DRIVERS

### GET /drivers
List contracted drivers + available guest drivers.
```json
Response: {
  "contracted": [DriverObject, ...],
  "available_guests": [DriverObject, ...],
  "market": [DriverObject, ...]
}
```

### GET /drivers/{id}/compatibility/{horse_id}
Calculate compatibility between driver and horse.
```json
Response: {
  "score": 78,
  "label": "Utmärkt",
  "performance_mod": "+5%",
  "gallop_risk_mod": "-5%",
  "breakdown": {
    "style_match": 72,
    "experience_bonus": 6,
    "shared_races": 8
  }
}
```

### POST /drivers/{id}/contract
Offer contract to a driver.
```json
Request:  { "contract_type": "permanent|apprentice", "duration_weeks": 8, "salary_per_week": 1200000 }
Response: { "accepted": true, "contract_id": "uuid" }
```

### POST /drivers/{id}/book-guest
Book a guest driver for a specific race.
```json
Request:  { "race_id": "uuid", "offered_fee": 800000 }
Response: { "accepted": true, "fee": 800000 } | { "accepted": false, "reason": "Kusken avböjde" }
```

---

## RACES

### GET /races/schedule
Upcoming race schedule.
```json
Query: ?days=7&division=all|3|4
Response: {
  "sessions": [
    {
      "id": "uuid",
      "scheduled_at": "2024-01-15T19:30:00Z",
      "track": "Solvalla",
      "weather": "clear",
      "temperature": 14,
      "races": [
        {
          "id": "uuid",
          "name": "Silverdivisionen Omg 8",
          "class": "silver",
          "distance": 2140,
          "start_method": "volt",
          "prize_pool": 15000000,
          "entry_fee": 200000,
          "current_entries": 7,
          "max_entries": 12,
          "entry_deadline": "2024-01-15T15:00:00Z",
          "your_entries": []
        }
      ]
    }
  ]
}
```

### POST /races/{id}/enter
Enter a horse in a race.
```json
Request: {
  "horse_id": "uuid",
  "driver_id": "uuid",
  "shoe": "light_aluminum",
  "tactics": {
    "positioning": "second",
    "tempo": "balanced",
    "sprint_order": "normal_400m",
    "gallop_safety": "normal",
    "curve_strategy": "middle",
    "whip_usage": "normal"
  }
}
Response: {
  "entry_id": "uuid",
  "post_position": null,      // Assigned after deadline
  "entry_fee_charged": 200000,
  "compatibility_score": 78,
  "warnings": ["Hästen är på 72% readiness — risk för sämre prestation"]
}
```

### PUT /races/entries/{id}/tactics
Update tactics for an existing entry (before deadline).
```json
Request:  { "positioning": "lead", "tempo": "offensive", ... }
Response: { "success": true }
```

### DELETE /races/entries/{id}
Scratch (withdraw) entry. Entry fee not refunded.

### GET /races/{id}/result
Race results with full detail.
```json
Response: {
  "race_id": "uuid",
  "name": "Silverdivisionen Omg 8",
  "distance": 2140,
  "start_method": "auto",
  "track": "Solvalla",
  "weather": "clear",
  "finishers": [
    {
      "position": 1,
      "horse": { "id": "uuid", "name": "Expressen", "is_npc": false },
      "driver": "Erik Lindblom",
      "km_time": "1.12,4",
      "prize_money": 6000000,
      "energy_at_finish": 31,
      "gallop_incidents": 0,
      "driver_rating": 8,
      "compatibility": 78,
      "sector_times": [
        { "sector": 1, "distance": 500, "km_time": "1.16,2" },
        { "sector": 2, "distance": 1000, "km_time": "1.13,5" },
        { "sector": 3, "distance": 1500, "km_time": "1.12,0" },
        { "sector": 4, "distance": 2140, "km_time": "1.10,8" }
      ]
    }, ...
  ],
  "disqualified": [...],
  "events": [
    { "type": "gallop_minor", "horse": "Nattsvansen", "location": "1400m", "text": "..." }
  ]
}
```

### GET /races/{id}/replay
Full replay data for live viewer.
```json
Response: {
  "seed": 8827364519,
  "snapshots": [
    { "distance": 0, "positions": [...] },
    { "distance": 100, "positions": [...] },
    ...
  ],
  "events": [...],
  "total_steps": 21,
  "playback_interval_ms": 3000   // 3 seconds between steps for ~65s total
}
```

### WebSocket: /ws/race/{session_id}
Live race feed. Server pushes snapshots with delay after simulation.
```json
Events:
  { "type": "race_starting", "race_id": "uuid", "countdown": 30 }
  { "type": "snapshot", "race_id": "uuid", "data": PositionSnapshot }
  { "type": "event", "race_id": "uuid", "data": RaceEvent }
  { "type": "race_finished", "race_id": "uuid", "results": [...] }
```

---

## TRANSFER

### GET /transfer/auctions
Active auctions.
```json
Query: ?min_speed=60&max_price=300000&sort=ending_soon|price|speed
Response: { "auctions": [AuctionObject, ...], "total": 23 }
```

### POST /transfer/auctions/{id}/bid
Place a bid.
```json
Request:  { "amount": 19500000 }
Response: { "success": true, "new_highest": true, "your_bid": 19500000 }
```

### POST /transfer/auctions/create
List a horse for sale.
```json
Request:  { "horse_id": "uuid", "starting_price": 10000000, "duration_hours": 48 }
Response: { "auction_id": "uuid" }
```

### POST /transfer/scout/{horse_id}
Request scouting report on a horse.
```json
Request:  { "level": 2 }    // 1=basic, 2=standard, 3=deep, 4=elite
Response: {
  "report_id": "uuid",
  "cost": 400000,
  "completion_time": "2024-01-16T08:00:00Z",    // Takes game time
  "level": 2
}
```

### GET /transfer/scout/{report_id}
Get completed scouting report.
```json
Response: {
  "horse_id": "uuid",
  "level": 2,
  "revealed": {
    "personality_primary": "hot",
    "personality_secondary": "brave",
    "estimated_potential": 75,
    "gallop_tendency": "Medel (15-25%)",
    "compatibility_with_your_drivers": [
      { "driver": "Erik Lindblom", "score": 65, "label": "Bra" }
    ]
  }
}
```

---

## BREEDING

### GET /breeding/stallion-registry
Available stallions for breeding.
```json
Response: {
  "stallions": [
    {
      "horse_id": "uuid",
      "name": "Expressen",
      "owner": "DennisStall",
      "stud_fee": 3500000,
      "career": { "starts": 24, "wins": 5, "best_time": "1.12,4" },
      "offspring": { "total": 8, "winners": 3 },
      "bloodline": "Expressenlinjen",
      "nick_data": [
        { "with_bloodline": "Järnmannenlinjen", "rating": "Bra", "sample": 12 }
      ]
    }
  ]
}
```

### POST /breeding/breed
Request breeding.
```json
Request:  { "mare_id": "uuid", "stallion_id": "uuid" }
Response: {
  "breeding_id": "uuid",
  "cost": { "stud_fee": 3500000, "vet_fee": 200000 },
  "success_chance": 70,
  "expected_birth_week": 57,
  "nick_rating": "Bra (+8% potential)"
}
```

### POST /breeding/register-stallion
Register your stallion for breeding.
```json
Request:  { "horse_id": "uuid", "stud_fee": 3500000 }
Response: { "registry_id": "uuid" }
```

---

## FINANCES

### GET /finances/overview
Financial summary.
```json
Response: {
  "balance": 48725000,
  "weekly_summary": {
    "income": { "prize_money": 4200000, "sponsors": 2500000, "press": 100000, "total": 6800000 },
    "expenses": { "salaries": 2250000, "feed": 350000, "training": 900000, "stable": 250000, "total": 5200000 },
    "net": 1600000
  },
  "trend_8_weeks": [42000000, 43500000, 44800000, 46000000, 45500000, 47200000, 48700000, 48725000],
  "sponsors": [
    { "name": "Betsafe", "weekly_payment": 2500000, "expires_week": 48 }
  ]
}
```

### GET /finances/transactions
Transaction history.
```json
Query: ?category=prize_money|salary|feed&game_week=35&limit=50
Response: { "transactions": [...], "total": 234 }
```

---

## V75 (META-GAME)

### GET /v75/current
Current V75 round.
```json
Response: {
  "round_id": "uuid",
  "races": [
    { "race_id": "uuid", "name": "...", "horses": [{ "id": "uuid", "name": "...", "stats_preview": {...} }] }
  ],
  "deadline": "2024-01-20T12:00:00Z",
  "pool_amount": 50000000
}
```

### POST /v75/submit-coupon
Submit V75 picks.
```json
Request: {
  "picks": {
    "race_1": ["horse_uuid_1"],                    // Spik (1 horse)
    "race_2": ["horse_uuid_3", "horse_uuid_5"],    // 2 horses
    "race_3": ["horse_uuid_2", "horse_uuid_4", "horse_uuid_7"],  // 3 horses
    ...
  }
}
Response: {
  "coupon_id": "uuid",
  "cost": 500000,
  "total_rows": 72
}
```

---

## EVENTS

### GET /events
Stable events/news feed.
```json
Query: ?unread=true&type=injury|transfer|race|sponsor|achievement|stable_maintenance
Response: {
  "events": [
    {
      "id": "uuid",
      "type": "injury",
      "title": "Dalero halt efter gårdagens träning",
      "description": "Veterinär tillkallad — beräknad rehabilitering: 2 spelveckor",
      "requires_action": true,
      "action_data": { "type": "vet_decision", "options": ["Akutvård (5000 kr)", "Avvakta"] },
      "created_at": "2024-01-15T08:00:00Z"
    }
  ]
}
```

### POST /events/{id}/action
Respond to an actionable event.
```json
Request:  { "choice": "option_1" }
Response: { "result": "Akutvård utförd. Beräknad återhämtning: 10 speldagar.", "cost": 500000 }
```

---

## GAME STATE (Admin/System)

### GET /game/state
Current game time and status.
```json
Response: {
  "current_game_week": 35,
  "current_game_day": 7,
  "current_season": 3,
  "season_period": "regular",
  "next_race_at": "2024-01-15T19:30:00Z",
  "total_players": 234,
  "npc_scaling": 0.45
}
```

---

## SCHEDULED TASKS (Celery)

These run automatically:

| Task | Schedule | Description |
|------|----------|-------------|
| `simulate_race_session` | At each race time | Runs race engine for all races in session |
| `morning_report` | 08:00 CET daily | Generates morning reports for all stables |
| `daily_horse_update` | 06:00 CET daily | Updates health, energy, fatigue, weight, mood |
| `weekly_training_effect` | Every 3.5 days | Applies training gains to horse stats |
| `weekly_finances` | Every 3.5 days | Deducts salaries, feed, facility costs |
| `check_shoe_durability` | After each race | Decrements shoe durability, notifies if worn |
| `process_auctions` | Every 5 min | Checks expired auctions, finalizes sales |
| `npc_race_entries` | 2h before race | NPC stables enter horses in upcoming races |
| `breeding_progress` | Daily | Updates pregnancy, handles foal births |
| `generate_events` | Daily | Random stable events (maintenance, staff, etc.) |
| `season_transition` | Per schedule | Handles promotion/relegation, new season setup |
| `achievement_check` | After race results | Checks all achievement conditions |
