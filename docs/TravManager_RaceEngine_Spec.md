# TravManager — Loppmotor & Simuleringsspecifikation
## Teknisk Design v1.0

---

## 1. Spelkalender & Loppfrekvens

### Verklig trav som referens

I svensk trav körs det lopp nästan varje dag på någon bana, men en enskild häst startar typiskt var 2–4:e vecka. V75 körs på lördagar, V86 på onsdagar. En aktiv travhäst gör 15–25 starter per år.

### Spelets tidsmodell

**1 spelvecka = 1 verklig vecka** (samma som Hattrick — realtid)

| Dag | Loppaktivitet | Typ |
|-----|--------------|-----|
| Måndag | — | Anmälningsdag (deadline tisdag 23:59) |
| Tisdag | — | Anmälningsstängning + lottning av startspår |
| **Onsdag** | **Loppkväll 1** — simuleras kl 19:30 CET | 3–4 lopp i din division |
| Torsdag | — | Analysdag, träningsjustering |
| Fredag | — | Anmälningsdag storlopp (deadline fredag 18:00) |
| **Lördag** | **V75-dag** — simuleras kl 15:00 CET | 7 lopp (V75-format, alla divisioner) |
| Söndag | — | Ekonomiavstämning, vilodag |

**Totalt: 10–11 lopp per vecka** som din division berörs av.

### Hur ofta kan en häst starta?

Här är nyckeln till strategiskt djup:

**Grundregel: Minimum 7 dagars vila mellan starter.**

Det betyder att en häst kan starta MAX 1 gång/vecka — men det är sällan optimalt.

**Återhämtningssystem (fatigue/recovery):**

```
EFTER LOPP:
  base_fatigue = 40 + (distans / 100) + (placering_stress * 5)
  
  Om hästen vann:        +10 fatigue (ansträngning)
  Om hästen galopperade:  +15 fatigue (mentalt + fysiskt)
  Om distans > 2140m:     +10 fatigue
  Om volt-start:          +5 fatigue (stressigare)

DAGLIG ÅTERHÄMTNING:
  recovery_per_day = base_recovery * condition_factor * rest_bonus * facility_bonus
  
  base_recovery = 8–12 (beroende på hästens uthållighet)
  condition_factor = horse.condition / 100
  rest_bonus = 1.3 om träning = "Vila", 1.0 annars
  facility_bonus = 1.0 + (vet_facility_level * 0.1)
```

**Praktisk effekt:**

| Scenario | Fatigue efter lopp | Dagar till redo | Kan starta nästa vecka? |
|----------|-------------------|-----------------|------------------------|
| Kort lopp (1640m), bra placering | ~45 | 4–5 dagar | ✅ Ja, men inte 100% |
| Medellopp (2140m), vinst | ~60 | 5–7 dagar | ⚠️ Möjligt men riskabelt |
| Långlopp (2640m), tung resa | ~75 | 7–9 dagar | ❌ Nej, behöver vila |
| Galoppering + DQ | ~70 | 6–8 dagar | ❌ Nej, mentalt nere |

**Strategisk konsekvens**: Du KAN starta en häst varje vecka i korta lopp, men prestandan sjunker gradvis. Optimalt är var 2–3:e vecka. Vill du pusha — riskera skada/form-dipp. Exakt som verklig trav.

**Visualisering för spelaren:**

```
BLIANSEN — Startberedskap
████████████░░░░░░ 68% (Onsdag)
██████████████████ 95% (Lördag)  ← Rekommenderad
```

---

## 2. NPC-hästar & Motståndarsystem

### Problemet

I tidigt skede (och i tunna divisioner) finns det inte tillräckligt med spelarhästar för att fylla 8–12 startande per lopp. Vi behöver NPC-hästar (AI-styrda) som fyller fältet men inte tar över spelet.

### NPC-arkitektur: "Stallmästare"-systemet

Varje division har ett antal **AI-stall** som drivs av systemet. Dessa ser ut som riktiga stall men har en (AI)-markering som syns subtilt.

**NPC-hästar genereras med:**

```python
class NPCHorseGenerator:
    """
    Genererar NPC-hästar kalibrerade mot divisionens nivå.
    NPC-hästar är ALLTID något svagare än genomsnittet i divisionen
    så att riktiga spelare har en naturlig fördel.
    """
    
    def generate(self, division_level: int, role: str) -> Horse:
        # Division 6 (lägst) → base_power ~45-55
        # Division 1 (högst) → base_power ~75-85
        base_power = 35 + (division_level * 8)
        
        # NPC-nerfning: alltid 5-15% under divisionssnittet
        nerf = random.uniform(0.85, 0.95)
        
        # Generera egenskaper med variation
        stats = {
            'speed':     clamp(base_power * nerf + gauss(0, 8), 20, 95),
            'endurance': clamp(base_power * nerf + gauss(0, 8), 20, 95),
            'mentality': clamp(base_power * nerf + gauss(0, 10), 20, 95),
            'start':     clamp(base_power * nerf + gauss(0, 8), 20, 95),
            'sprint':    clamp(base_power * nerf + gauss(0, 8), 20, 95),
        }
        
        # NPC-roller skapar variation i fältet
        if role == "PACEMAKER":
            stats['speed'] += 10      # Snabb ut men dör i spurten
            stats['endurance'] -= 15
        elif role == "CLOSER":
            stats['speed'] -= 8       # Kommer bakifrån
            stats['sprint'] += 12
        elif role == "STEADY":
            pass                      # Jämn, ofarlig
        elif role == "WILDCARD":
            stats['gallop_risk'] = random.randint(20, 40)  # Kan skrälla eller galoppera
            stats['speed'] += random.randint(-5, 15)
        
        return Horse(
            name=self.generate_swedish_horse_name(),
            stable=self.get_npc_stable(division_level),
            is_npc=True,
            **stats
        )
```

### Fältfyllningslogik

```python
class RaceFieldManager:
    """
    Fyller lopps-fält med rätt blandning av spelare och NPC.
    Mål: Alltid 8-12 hästar per lopp.
    """
    
    MIN_FIELD = 8
    MAX_FIELD = 12
    MIN_PLAYER_RATIO = 0.3   # Minst 30% ska vara spelar-hästar
    MAX_NPC_RATIO = 0.7       # Max 70% NPC i ett lopp
    
    def fill_race(self, race, player_entries: list) -> list:
        field = list(player_entries)  # Börja med anmälda spelar-hästar
        
        # Bestäm antal NPC som behövs
        npc_needed = max(0, self.MIN_FIELD - len(field))
        
        # Om vi har plats, lägg till NPC för att skapa intressantare fält
        if len(field) < self.MAX_FIELD:
            # Lägg alltid till minst 2 NPC (oavsett spelarantal)
            # för variation och oförutsägbarhet
            npc_needed = max(npc_needed, 2)
            npc_needed = min(npc_needed, self.MAX_FIELD - len(field))
        
        # Generera NPC med rolldistribution
        roles = self._distribute_roles(npc_needed, race)
        for role in roles:
            npc = NPCHorseGenerator().generate(
                division_level=race.division.level,
                role=role
            )
            field.append(npc)
        
        # Lottning av startspår (volt) eller startgrupper (auto)
        random.shuffle(field)
        for i, entry in enumerate(field):
            entry.post_position = i + 1
        
        return field
    
    def _distribute_roles(self, count, race):
        """
        Skapar variation i NPC-fältet.
        Varje lopp ska ha minst 1 PACEMAKER och 1 CLOSER.
        """
        roles = []
        if count >= 2:
            roles.extend(["PACEMAKER", "CLOSER"])
            count -= 2
        for _ in range(count):
            roles.append(random.choice([
                "STEADY", "STEADY", "STEADY",
                "WILDCARD",  # 25% chans för skrällhäst
            ]))
        return roles
```

### NPC-beteende över tid

**Skalning med spelarbas:**

```
Spelarantal i division   NPC per lopp (snitt)   NPC-strategi
< 20 spelare             5–7 NPC / lopp         Stort NPC-stall, 
                                                 generöst med hästar
20–50 spelare            3–5 NPC / lopp         Minskande NPC-stall
50–80 spelare            1–3 NPC / lopp         Bara fyllnad
80+ spelare              0–1 NPC / lopp         NPC fasas ut nästan helt
```

**NPC-stall har namn och identitet** (spelarupplevelse):
- "Datatraven" (AI)
- "Systemstallet" (AI)  
- "Björklunds Stall" (AI — ser mer "riktigt" ut)

NPC-hästar KAN transfereras — spelare kan köpa NPC-hästar från transfermarknaden. När en NPC-häst köps av en spelare blir den en vanlig spelar-häst permanent.

---

## 3. Loppmotorn — Simuleringsalgoritm

### Designfilosofi

Loppmotorn ska vara:
1. **Deterministisk med seed** — samma input + seed = samma resultat (för replay, verifiering, anti-fusk)
2. **Stegbaserad** — simulerar loppet i 100m-intervall (2140m = 21 steg + start)
3. **Transparant** — spelaren ska kunna förstå VARFÖR resultatet blev som det blev
4. **Slumpmässig nog** — en sämre häst kan vinna ibland (precis som verkligheten)

### Simuleringsloop

```python
import hashlib
from dataclasses import dataclass
from typing import List

@dataclass
class RaceEntry:
    horse: Horse
    driver: Driver
    tactics: Tactics        # Spelarens valda taktik
    post_position: int      # Startspår
    
    # Runtime-state (uppdateras under simulering)
    energy: float = 100.0
    position_meters: float = 0.0
    current_speed: float = 0.0
    is_galloping: bool = False
    is_disqualified: bool = False
    mental_state: float = 1.0   # 0.5 = stressad, 1.0 = lugn, 1.2 = i zonen

@dataclass
class Tactics:
    positioning: str    # "lead", "second", "outside", "back"
    tempo: str          # "offensive", "balanced", "cautious"  
    sprint_order: str   # "early_500m", "normal_300m", "late_200m"
    gallop_safety: str  # "safe", "normal", "risky"

class RaceEngine:
    """
    Stegbaserad loppsimulering.
    Varje steg = 100 meter.
    """
    
    STEP_DISTANCE = 100  # meter
    
    def simulate(self, race, entries: List[RaceEntry], seed: int) -> RaceResult:
        self.rng = self._seeded_rng(seed)
        self.distance = race.distance        # t.ex. 2140
        self.total_steps = self.distance // self.STEP_DISTANCE
        self.events = []                     # Lopprapport
        self.step_snapshots = []             # Position per steg (för replay)
        
        # === STEG 0: START ===
        self._simulate_start(entries, race.start_method)
        
        # === STEG 1–N: LOPPET ===
        for step in range(1, self.total_steps + 1):
            meters = step * self.STEP_DISTANCE
            remaining = self.distance - meters
            
            for entry in entries:
                if entry.is_disqualified:
                    continue
                
                # 1. Beräkna målhastighet baserat på taktik & position
                target_speed = self._calc_target_speed(entry, remaining, entries)
                
                # 2. Applicera fysik (acceleration, energi, uthållighet)
                actual_speed = self._apply_physics(entry, target_speed, step)
                
                # 3. Kolla galopprisk
                galloped = self._check_gallop(entry, actual_speed, remaining)
                
                # 4. Kuskens inverkan
                actual_speed = self._apply_driver_skill(entry, actual_speed, remaining)
                
                # 5. Uppdatera position
                entry.position_meters += actual_speed
                entry.current_speed = actual_speed
            
            # Snapshot för live-viewer
            self.step_snapshots.append(self._take_snapshot(entries, meters))
        
        # === RESULTAT ===
        return self._compile_result(entries)
    
    # -------------------------------------------------------
    # STARTFAS
    # -------------------------------------------------------
    
    def _simulate_start(self, entries, start_method):
        """
        Volt-start: Hästar accelererar från gång → trav. 
        Innerspår har kortare väg men svårare att ta ledningen.
        
        Auto-start: Alla har samma förutsättning,
        startförmåga avgör vem som kommer snabbast iväg.
        """
        for entry in entries:
            horse = entry.horse
            driver = entry.driver
            
            if start_method == "auto":
                # Auto-start: ren startförmåga + lite slump
                start_power = (
                    horse.start * 0.6 +
                    driver.start_skill * 0.25 +
                    self.rng.gauss(0, 5) * 0.15
                )
                # Snabba startare får ~15m försprång
                entry.position_meters = (start_power / 100) * 15
                
            elif start_method == "volt":
                # Volt: Innerspår (1-2) har kortare väg men alla startar samtidigt
                volt_bonus = max(0, (8 - entry.post_position)) * 1.5
                start_power = (
                    horse.start * 0.5 +
                    horse.mentality * 0.2 +
                    driver.start_skill * 0.2 +
                    self.rng.gauss(0, 4) * 0.1
                )
                entry.position_meters = (start_power / 100) * 12 + volt_bonus
                
                # Volt = galopprisk i start
                gallop_chance = (
                    horse.gallop_risk * 0.4 +
                    (100 - horse.mentality) * 0.2 +
                    (100 - driver.gallop_handling) * 0.1
                ) / 100
                
                if entry.tactics.positioning == "lead":
                    gallop_chance *= 1.4  # Offensiv voltstart = högre risk
                
                if self.rng.random() < gallop_chance * 0.15:
                    self._trigger_gallop(entry, "start")
            
            self.events.append({
                'step': 0, 
                'type': 'start',
                'horse': horse.name,
                'initial_position': entry.position_meters
            })
    
    # -------------------------------------------------------
    # HASTIGHETSBERÄKNING
    # -------------------------------------------------------
    
    def _calc_target_speed(self, entry, remaining, all_entries):
        """
        Beräknar den hastighet hästen VILL hålla.
        Baseras på: taktik, position i fältet, energi, spurtzon.
        """
        horse = entry.horse
        
        # Bashastighet (beror på snabbhet + uthållighet)
        base_speed = (horse.speed * 0.6 + horse.endurance * 0.4) / 10
        # base_speed ≈ 6.0–9.0 (representerar ~m per steg-enhet)
        
        # === TAKTISK PROFIL ===
        if remaining > self.distance * 0.7:
            # Första 30% av loppet
            phase = "opening"
        elif remaining > self.distance * 0.25:
            # Mittfas
            phase = "middle"
        else:
            # Spurtfas (sista 25%)
            phase = "sprint"
        
        # Tempo-modifierare
        tempo_mod = {
            "opening": {"offensive": 1.08, "balanced": 1.00, "cautious": 0.92},
            "middle":  {"offensive": 1.04, "balanced": 1.00, "cautious": 0.97},
            "sprint":  {"offensive": 1.02, "balanced": 1.05, "cautious": 1.10},
        }
        target = base_speed * tempo_mod[phase][entry.tactics.tempo]
        
        # === POSITIONERING ===
        my_rank = self._get_rank(entry, all_entries)
        
        if entry.tactics.positioning == "lead":
            if my_rank > 1:
                target *= 1.06  # Pressa för att ta ledningen
            else:
                target *= 1.01  # Behåll ledning med minimal marginal
                
        elif entry.tactics.positioning == "second":
            leader = self._get_leader(all_entries)
            if leader:
                # Matcha ledarens tempo, ligg strax bakom
                target = min(target, leader.current_speed * 0.99)
                
        elif entry.tactics.positioning == "back":
            if phase != "sprint":
                target *= 0.94  # Spara energi
            else:
                target *= 1.12  # Full attack i spurt!
        
        # === SPURTZON ===
        sprint_trigger = {
            "early_500m": 500,
            "normal_300m": 300,
            "late_200m": 200,
        }[entry.tactics.sprint_order]
        
        if remaining <= sprint_trigger:
            sprint_power = (horse.sprint * 0.7 + horse.speed * 0.3) / 100
            target *= (1.0 + sprint_power * 0.2)
        
        # === ENERGIBEGRÄNSNING ===
        if entry.energy < 30:
            # Hästen är slut — hastigheten sjunker drastiskt
            target *= (entry.energy / 30) * 0.8 + 0.2
        elif entry.energy < 50:
            target *= 0.95
        
        return target
    
    # -------------------------------------------------------
    # FYSIKMOTOR
    # -------------------------------------------------------
    
    def _apply_physics(self, entry, target_speed, step):
        """
        Konverterar målhastighet till faktisk hastighet.
        Hanterar acceleration, energiförbrukning, och uthållighet.
        """
        horse = entry.horse
        
        # Acceleration (kan inte byta hastighet instantant)
        max_accel = 0.3 + (horse.speed / 200)
        speed_diff = target_speed - entry.current_speed
        actual_speed = entry.current_speed + clamp(speed_diff, -max_accel, max_accel)
        
        # Energiförbrukning
        speed_ratio = actual_speed / ((horse.speed * 0.6 + horse.endurance * 0.4) / 10)
        energy_cost = (
            1.0 +                                    # Baskostnad per steg
            max(0, speed_ratio - 1.0) * 4.0 +        # Överkörning kostar MYCKET
            (1.0 - horse.endurance / 100) * 0.5       # Dålig uthållighet = dyrare
        )
        
        # Mental påverkan
        if entry.mental_state < 0.8:
            energy_cost *= 1.2  # Stressad häst bränner mer energi
        
        entry.energy = max(0, entry.energy - energy_cost)
        
        # Vind & underlag (mindre slumpfaktor)
        weather_mod = 1.0 + self.rng.gauss(0, 0.01)
        actual_speed *= weather_mod
        
        return max(0, actual_speed)
    
    # -------------------------------------------------------
    # GALOPPKONTROLL
    # -------------------------------------------------------
    
    def _check_gallop(self, entry, speed, remaining):
        """
        Kontrollerar om hästen galopperar.
        Galopprisk ökar med: hög fart, dålig mentalitet, låg energi,
        trångt läge, oerfaren kusk.
        """
        horse = entry.horse
        driver = entry.driver
        
        # Basrisk per steg
        base_risk = horse.gallop_risk / 100
        
        # Hastighetsfaktor (hög fart = mer risk)
        speed_ratio = speed / ((horse.speed * 0.6 + horse.endurance * 0.4) / 10)
        if speed_ratio > 1.05:
            base_risk *= (1 + (speed_ratio - 1.05) * 3)
        
        # Mentalitetsfaktor
        mental_mod = (100 - horse.mentality) / 100 * 0.5
        base_risk += mental_mod * 0.02
        
        # Energifaktor (trött häst galopperar mer)
        if entry.energy < 20:
            base_risk *= 2.0
        elif entry.energy < 40:
            base_risk *= 1.3
        
        # Kuskens galopphantering
        driver_mod = driver.gallop_handling / 100
        
        # Taktisk säkerhetsnivå
        safety = {"safe": 0.6, "normal": 1.0, "risky": 1.5}
        base_risk *= safety[entry.tactics.gallop_safety]
        
        # Kuskens ingripande
        base_risk *= (1.0 - driver_mod * 0.4)
        
        # Slumpmässig kontroll (per 100m-steg)
        if self.rng.random() < base_risk * 0.08:
            self._trigger_gallop(entry, f"{self.distance - remaining}m")
            return True
        
        return False
    
    def _trigger_gallop(self, entry, location):
        """
        Hästen galopperar! Kuskens skicklighet avgör konsekvensen.
        """
        driver = entry.driver
        horse = entry.horse
        
        # Hur snabbt kan kusken reagera?
        recovery_skill = (driver.gallop_handling * 0.6 + driver.experience * 0.4) / 100
        
        recovery_roll = self.rng.random()
        
        if recovery_roll < recovery_skill * 0.7:
            # Snabb återhämtning — tappar 1-2 längder
            time_lost = self.rng.uniform(3, 8)
            entry.position_meters -= time_lost
            entry.mental_state *= 0.85
            severity = "minor"
            self.events.append({
                'type': 'gallop_minor',
                'horse': horse.name,
                'location': location,
                'text': f"{horse.name} galopperade kortvarigt vid {location} — "
                        f"kusken {driver.name} rättade snabbt till."
            })
            
        elif recovery_roll < recovery_skill * 0.9 + 0.3:
            # Stor galoppering — tappar 3-5 längder
            time_lost = self.rng.uniform(10, 25)
            entry.position_meters -= time_lost
            entry.energy -= 10
            entry.mental_state *= 0.6
            severity = "major"
            self.events.append({
                'type': 'gallop_major',
                'horse': horse.name,
                'location': location,
                'text': f"{horse.name} i kraftig galopp vid {location}! "
                        f"Tappar flera längder."
            })
            
        else:
            # Diskvalificering
            entry.is_disqualified = True
            severity = "dq"
            self.events.append({
                'type': 'gallop_dq',
                'horse': horse.name,
                'location': location,
                'text': f"{horse.name} DISKVALIFICERAD efter galopp vid {location}."
            })
        
        entry.is_galloping = True
        return severity
    
    # -------------------------------------------------------
    # KUSKINVERKAN
    # -------------------------------------------------------
    
    def _apply_driver_skill(self, entry, speed, remaining):
        """
        Kusken påverkar prestandan genom:
        - Taktisk körning (positionering, timing)
        - Spurtförmåga (tajming av slutangrepp)
        - Generell skicklighet (optimerar hästens kapacitet)
        """
        driver = entry.driver
        
        # Generell kompetensbonus (0-5%)
        skill_bonus = 1.0 + (driver.skill / 100) * 0.05
        
        # Taktisk bonus i mittfas (sparar energi effektivt)
        if remaining > 300 and remaining < self.distance * 0.7:
            tactical_bonus = 1.0 + (driver.tactical / 100) * 0.02
            skill_bonus *= tactical_bonus
        
        # Spurtbonus i slutet
        if remaining <= 300:
            sprint_bonus = 1.0 + (driver.sprint_timing / 100) * 0.04
            skill_bonus *= sprint_bonus
        
        return speed * skill_bonus
    
    # -------------------------------------------------------
    # HJÄLPFUNKTIONER
    # -------------------------------------------------------
    
    def _get_rank(self, entry, all_entries):
        sorted_entries = sorted(
            [e for e in all_entries if not e.is_disqualified],
            key=lambda e: e.position_meters,
            reverse=True
        )
        for i, e in enumerate(sorted_entries):
            if e == entry:
                return i + 1
        return len(sorted_entries)
    
    def _get_leader(self, all_entries):
        active = [e for e in all_entries if not e.is_disqualified]
        return max(active, key=lambda e: e.position_meters, default=None)
    
    def _take_snapshot(self, entries, meters_into_race):
        return {
            'distance': meters_into_race,
            'positions': [
                {
                    'horse': e.horse.name,
                    'horse_id': e.horse.id,
                    'position_meters': e.position_meters,
                    'energy': e.energy,
                    'speed': e.current_speed,
                    'is_galloping': e.is_galloping,
                    'is_dq': e.is_disqualified,
                }
                for e in sorted(entries, key=lambda e: e.position_meters, reverse=True)
            ]
        }
    
    def _compile_result(self, entries):
        finishers = sorted(
            [e for e in entries if not e.is_disqualified],
            key=lambda e: e.position_meters,
            reverse=True
        )
        dq = [e for e in entries if e.is_disqualified]
        
        return RaceResult(
            finishers=finishers,
            disqualified=dq,
            events=self.events,
            snapshots=self.step_snapshots,
            seed=self.seed,
        )
    
    def _seeded_rng(self, seed):
        """Deterministisk RNG baserat på race_id + timestamp."""
        import random
        rng = random.Random()
        rng.seed(seed)
        return rng


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))
```

---

## 4. Tidsberäkning & Kilometer-tid

### Hur konverteras simulering → visningstid?

Simuleringen räknar i abstrakta "speed-units". Vi konverterar till visningstid i efterhand:

```python
class TimeConverter:
    """
    Konverterar simuleringsresultat till realistiska tider.
    
    Referenstider (verklig trav):
    - 1640m auto, bra häst: ~1.11-1.13 (km-tid)
    - 2140m volt, bra häst: ~1.12-1.14  
    - 2640m volt, bra häst: ~1.13-1.16
    """
    
    # Kilometer-tid i sekunder (per 1000m)
    BASE_KM_TIMES = {
        # division_level: (snabbast_möjlig, genomsnitt, långsammast)
        6: (77.0, 80.0, 85.0),    # ~1.17 - 1.25
        5: (75.0, 78.0, 82.0),    # ~1.15 - 1.22
        4: (73.0, 76.0, 80.0),    # ~1.13 - 1.20
        3: (71.5, 74.0, 78.0),    # ~1.11.5 - 1.18
        2: (70.0, 72.5, 76.0),    # ~1.10 - 1.16
        1: (68.5, 71.0, 74.0),    # ~1.08.5 - 1.14
    }
    
    def convert(self, result, race):
        """Sätter realistiska tider baserat på placering."""
        div = race.division.level
        fastest, avg, slowest = self.BASE_KM_TIMES[div]
        
        finishers = result.finishers
        if not finishers:
            return
        
        # Vinnartid (baserat på hur starkt loppet kördes)
        winner = finishers[0]
        winner_power = (winner.horse.speed + winner.horse.endurance) / 2
        
        # Normalisera: 50-power = genomsnitt, 90-power = snabbast
        power_pct = (winner_power - 40) / 50  # 0.0 = svag, 1.0 = stark
        winner_km_time = avg - (avg - fastest) * power_pct
        
        # Total tid
        winner_total = winner_km_time * (race.distance / 1000)
        
        # Auto-start = lite snabbare (ingen volt-fördröjning)
        if race.start_method == "auto":
            winner_total -= 1.5
        
        # Övriga hästar: tid baserad på avstånd till vinnaren
        winner_pos = winner.position_meters
        for entry in finishers:
            distance_behind = winner_pos - entry.position_meters
            # 1 "meter" i simulering ≈ 0.3-0.5 sekunder
            time_behind = distance_behind * 0.35
            entry.finish_time = winner_total + time_behind
            
            # Formatera som t.ex. "1.12,4"
            total_secs = entry.finish_time
            km_secs = total_secs / (race.distance / 1000)
            mins = int(km_secs // 60)
            secs = km_secs % 60
            entry.km_time_display = f"{mins}.{secs:04.1f}".replace(".", ",", 1)
```

---

## 5. Seedning & Replay-system

### Varför deterministisk simulering?

1. **Anti-fusk**: Servern kan verifiera att resultatet stämmer
2. **Replay**: Spelare kan se loppet igen (eller i slow-motion)
3. **"Vad-om"**: Premium-feature — kör loppet 20x med samma grundförutsättningar men olika seeds

### Seed-generering

```python
def generate_race_seed(race_id: int, scheduled_time: datetime) -> int:
    """
    Seed genereras av race_id + exakt tid.
    Kan inte förutsägas av spelare, men kan reproduceras av servern.
    """
    raw = f"{race_id}:{scheduled_time.isoformat()}:TravManager_v1"
    hash_bytes = hashlib.sha256(raw.encode()).digest()
    return int.from_bytes(hash_bytes[:8], 'big')
```

### Replay-data (skickas till frontend)

```json
{
  "race_id": 4521,
  "distance": 2140,
  "start_method": "volt",
  "seed": 8827364519,
  "snapshots": [
    {
      "distance": 0,
      "positions": [
        {"horse_id": 1, "name": "Bliansen", "pos_m": 8.2, "energy": 100, "speed": 0},
        {"horse_id": 7, "name": "Expressen", "pos_m": 6.1, "energy": 100, "speed": 0}
      ]
    },
    {
      "distance": 100,
      "positions": [
        {"horse_id": 1, "name": "Bliansen", "pos_m": 112.5, "energy": 97, "speed": 8.1},
        {"horse_id": 7, "name": "Expressen", "pos_m": 108.2, "energy": 98, "speed": 7.9}
      ]
    }
  ],
  "events": [
    {"step": 18, "type": "gallop_minor", "horse": "Nattsvansen", "location": "1800m"}
  ],
  "results": {
    "finishers": [
      {"horse": "Expressen", "km_time": "1.12,4", "position": 1, "prize": 60000}
    ],
    "disqualified": [
      {"horse": "Nattsvansen", "reason": "Galopp vid 1800m"}
    ]
  }
}
```

---

## 6. Arkitektur — Hur motorn körs

### Serverarkitektur

```
┌─────────────────────────────────────────────────┐
│                  SCHEDULER                       │
│  Cron: Onsdag 19:30, Lördag 15:00               │
│  Triggar loppsimulering för alla lopp i omgången │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              RACE ENGINE SERVICE                 │
│  Python-mikrotjänst (FastAPI)                    │
│                                                  │
│  POST /simulate                                  │
│  Body: { race_id, entries[], conditions, seed }  │
│  Response: { result, snapshots[], events[] }     │
│                                                  │
│  Kör ALLA lopp i omgången parallellt             │
│  (~10 lopp × ~0.5s simulering = ~5s total)       │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│              MAIN API (NestJS/FastAPI)            │
│                                                  │
│  1. Sparar resultat i PostgreSQL                 │
│  2. Uppdaterar ekonomi (prispengar)              │
│  3. Uppdaterar häst-fatigue                      │
│  4. Pushar via WebSocket till live-viewer        │
│  5. Genererar lopprapport                        │
└──────────────────────┬──────────────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
     ┌──────────────┐  ┌──────────────┐
     │  WebSocket   │  │  PostgreSQL  │
     │  Live-viewer │  │  Permanent   │
     │  (Socket.io) │  │  storage     │
     └──────────────┘  └──────────────┘
```

### Live-upplevelse (frontend)

```
19:29:30  "Loppet startar om 30 sekunder..."
19:30:00  Servern kör simuleringen (tar <1 sekund)
19:30:01  Servern börjar STREAMA snapshots med delay:
          
          Snapshot 0 (START)  → skickas direkt
          Snapshot 1 (100m)   → skickas efter 3 sekunder
          Snapshot 2 (200m)   → skickas efter 6 sekunder
          ...
          Snapshot 21 (MÅL)   → skickas efter ~65 sekunder

Totalt: Loppet "pågår" i ~65 sekunder för spelaren,
även om simuleringen var klar på <1 sekund.
```

Loppet spelas alltså upp i "fake realtime" — det simuleras omedelbart men visas uppgradvis via tidsfördröjda WebSocket-events. Exakt samma teknik som Hattrick använder för sina matcher.

---

## 7. Lopptyper & Variationer

### Startmetoder

| Metod | Mekanik | Effekt |
|-------|---------|--------|
| **Volt** | Hästar startar i rörelse från volt. Innerspår = kortare väg | Startförmåga + mentalitet avgör. Galopprisk i start. |
| **Auto** | Startbil, alla har samma utgångsläge | Renare start, startförmåga dominerar. Snabbare lopp. |

### Distanser

| Distans | Typ | Karaktär |
|---------|-----|----------|
| **1640m** | Sprint | Snabbhet + start dominerar. Kort, intensivt. |
| **2140m** | Medel | Balanserat. Standard-distansen. |
| **2640m** | Stayer | Uthållighet avgör. Taktik viktigare. |
| **3140m** | Maratonlopp | Sällsynta speciallopp. Extremt uthållighetsberoende. |

### Handikapp

Starkare hästar startar 20m eller 40m bakom i volt-lopp. Skapar jämnare lopp och strategiska val: "Ska jag anmäla till ett lopp där jag startar 20m back, eller vänta på ett svagare fält?"

---

## 8. Post-race — Analys & Effekter

### Vad händer efter loppet?

```python
def post_race_effects(entry, race, result):
    horse = entry.horse
    
    # 1. FATIGUE (se sektion 1)
    horse.fatigue += calculate_fatigue(entry, race)
    
    # 2. ERFARENHET
    horse.experience += race_experience(result.position, race.level)
    
    # 3. FORM-KURVA (dold egenskap som påverkar nästa lopp)
    if result.position <= 3:
        horse.form += 3  # Vinst/placering höjer formen
    elif result.position > 6:
        horse.form -= 2  # Dåligt lopp sänker formen
    
    # 4. MENTALITET (långsiktig effekt)
    if entry.is_disqualified:
        horse.mentality -= 1  # Galoppering sänker mentalitet över tid
    if result.position == 1:
        horse.mentality += 0.5  # Vinst stärker självförtroendet
    
    # 5. SKADERISK
    injury_roll = random.random()
    injury_threshold = (
        horse.fatigue / 100 * 0.1 +
        (100 - horse.health) / 100 * 0.05
    )
    if injury_roll < injury_threshold:
        horse.injury = generate_injury()
        # Skador: 1-8 veckors rehabilitering
    
    # 6. PRISPENGAR
    prize = race.prize_pool * PRIZE_DISTRIBUTION[result.position]
    horse.stable.balance += prize
```

---

## Sammanfattning

| Aspekt | Design |
|--------|--------|
| Loppfrekvens | 2 loppdagar/vecka (onsdag + lördag) |
| Häst startfrekvens | Max 1/vecka, optimalt var 2-3:e vecka |
| Fältstorlek | 8–12 hästar per lopp |
| NPC-andel | 70% tidigt → 0% vid full spelarbas |
| Simulering | Deterministisk, stegbaserad (100m-steg) |
| Parametrar | Snabbhet, uthållighet, mentalitet, start, spurt, energi, galopprisk |
| Kuskeffekt | 5–10% påverkan (strategi, inte avgörande) |
| Live-upplevelse | Fake-realtime via WebSocket (65s lopp) |
| Replay | Full data sparas, kan återspelas med seed |
