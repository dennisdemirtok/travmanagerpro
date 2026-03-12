# TravManager — Komplett Spelmekanik-specifikation
## Alla system, alla parametrar, alla beslut
### Version 2.0

---

# DEL 1: TIDSMODELL

## Tidskomprimeringsprincip

**1 verklig vecka = 2 spelveckor**

Det betyder att allting går dubbelt så fort som verkligheten. En häst som i verkligheten behöver 3 veckors vila mellan starter behöver 10–11 verkliga dagar i spelet. En dräktighet på 11 månader i verkligheten blir ~5,5 månader i speltid.

### Spelkalender (per verklig vecka)

Varje verklig vecka innehåller **2 kompletta spelomgångar** med lopp **varje dag**:

```
MÅNDAG (Speldag 1 & 2)
  ├── 08:00  Morgonrapport: Hästhälsa, nattens händelser
  ├── 10:00  LOPP 1 — Lunchlopp (3 lopp, lägre divisioner)
  └── 19:30  LOPP 2 — Kvällslopp (4 lopp, alla divisioner)

TISDAG (Speldag 3 & 4)
  ├── 08:00  Morgonrapport
  ├── 12:00  LOPP 3 — Kvaltävling (2-3 lopp, kvallopp inför storlopp)
  └── 19:30  LOPP 4 — Kvällslopp (4 lopp)

ONSDAG (Speldag 5 & 6)
  ├── 08:00  Morgonrapport
  ├── 10:00  Transfermarknad — Ny auktionsomgång öppnar
  ├── 12:00  LOPP 5 — Lunchlopp (3 lopp)
  └── 19:30  LOPP 6 — V86-kväll (6 lopp, storformat)

TORSDAG (Speldag 7 & 8)
  ├── 08:00  Morgonrapport
  ├── 12:00  LOPP 7 — Kvaltävling (3 lopp)
  └── 19:30  LOPP 8 — Kvällslopp (4 lopp)

FREDAG (Speldag 9 & 10)
  ├── 08:00  Morgonrapport + Avelsrapport (föl-uppdatering)
  ├── 12:00  LOPP 9 — Lunchlopp (3 lopp)
  └── 19:30  LOPP 10 — Fredagsspecial (4 lopp, bonuspott)

LÖRDAG (Speldag 11 & 12)
  ├── 08:00  Morgonrapport
  ├── 13:00  LOPP 11 — V75-förmiddag (7 lopp, huvudeventet)
  └── 19:00  LOPP 12 — Kvällsgala (3 storlopp, högsta divisioner)

SÖNDAG (Speldag 13 & 14)
  ├── 08:00  Morgonrapport
  ├── 12:00  LOPP 13 — Söndagslopp (3 lopp, avslappnat)
  ├── 16:00  LOPP 14 — Veckoavslutning (2 lopp)
  └── 20:00  Ekonomisk veckosammanfattning
             Löner betalas ut
             Nästa veckas loppprogram publiceras
```

**Totalt: 14 loppomgångar per verklig vecka (~45–50 enskilda lopp)**

### Hästens startfrekvens med tidskomprimeringen

Med 2 spelveckor per verklig vecka och fatigue-systemet:

| Hästens kondition | Minimum vila (speldagar) | Verklig väntetid | Möjliga starter/vecka |
|---|---|---|---|
| Utvilad, kort lopp | 3 speldagar | ~1,5 dagar | Max 2 |
| Normal, medellopp | 5 speldagar | ~2,5 dagar | 1 |
| Trött, långlopp | 7–9 speldagar | ~3,5–4,5 dagar | 0–1 |
| Skadad | 14–56 speldagar | 1–4 veckor | 0 |

En spelare med 5 hästar kan alltså ha minst en häst i lopp nästan varje dag — men det kräver smart rotation och träningsplanering.

---

# DEL 2: HÄSTMODELLEN

## Alla egenskaper

Varje häst har tre kategorier av egenskaper:

### A. Kärnegenskaper (synliga, träningsbara)

| Egenskap | Beskrivning | Påverkar | Skala |
|----------|-------------|----------|-------|
| **Snabbhet** | Toppfart i trav | Maxhastighet i lopp | 1–100 |
| **Uthållighet** | Förmåga att hålla tempo | Energiförbrukning, långlopp | 1–100 |
| **Mentalitet** | Psykisk styrka, fokus | Galoppkontroll, stresshantering, volt-start | 1–100 |
| **Startförmåga** | Explosivitet i starten | Autostart-position, volt-reaktion | 1–100 |
| **Spurtstyrka** | Kraft i slutet | Slut-acceleration, avslutning | 1–100 |
| **Balans** | Kroppslig koordination | Kurvtagning, jämnt trav | 1–100 |
| **Styrka** | Råstyrka | Prestera i motvind, tungt underlag, drag i tredjespår | 1–100 |

### B. Fysisk status (dynamisk, förändras dagligen)

| Egenskap | Beskrivning | Påverkas av |
|----------|-------------|-------------|
| **Kondition** | Generell form | Träning, vila, ålder |
| **Energi** | Daglig energinivå | Vila, foder, senaste lopp |
| **Hälsa** | Skadebenägenhet | Träningsbelastning, ålder, vet-kvalitet |
| **Vikt** | Kroppsvikt i kg | Foder, träning (övervikt = långsammare) |
| **Form** | Aktuell tävlingsform | Senaste lopp-resultat, kurva över 5 lopp |
| **Fatigue** | Trötthet efter lopp | Sjunker med vila, ökar med lopp |
| **Humör** | Psykiskt mående | Varierar, påverkar träningseffekt |

### C. Dolda/genetiska egenskaper (avslöjas genom lopp, scouting, avel)

| Egenskap | Beskrivning |
|----------|-------------|
| **Galopptendens** | Grundläggande risk att bryta i galopp (1–40%) |
| **Banpreferens** | Vänster/Högervarv-bonus (±3%) |
| **Underlagspreferens** | Grus/Syntet/Vinterunderlag-bonus |
| **Väderkänslighet** | Presterar bättre/sämre i regn, kyla, värme |
| **Distansoptimum** | Vilken distans hästen är naturligt bäst på |
| **Mognadskurva** | Hur snabbt hästen når sin peak (tidig/sen) |
| **Tävlingsinstinkt** | Bonus när det är jämnt i sluttampen |
| **Transporttålighet** | Hur mycket lång resa påverkar prestandan |
| **Genetisk potential** | Max-tak för varje egenskap (kan aldrig tränas över) |

### Ålder och livscykel

```
Föl (0–1 spelår / 0–8 verkliga veckor)
  → Ingen träning, ingen tävling
  → Grundegenskaper avslöjas gradvis
  → Kräver: Foderkostnad, veterinärkontroll

Unghäst (1–2 spelår / 8–16 verkliga veckor)
  → Grundträning möjlig
  → Kan starta i unglopp (från 2 spelår)
  → Snabb utveckling, stor variation

Tävlingshäst (3–10 spelår / 16–80 verkliga veckor)
  → Full träning och tävling
  → Peak vid 5–7 spelår
  → Gradvis decline efter 8 spelår

Veteran (10–12 spelår)
  → Minskande stats, ökad skaderisk
  → Kan fortfarande tävla men inte på topp
  → Bra för lägre divisioner

Pension/Avel (12+ spelår, eller manuellt val)
  → Kan inte tävla
  → Avelssto/-hingst (om kvalificerad)
  → Stamtavla blir tillgänglig för avel
```

**1 spelår = 8 verkliga veckor = 16 spelveckor**

---

# DEL 3: KUSKSYSTEMET

## Kuskegenskaper

| Egenskap | Beskrivning | Påverkar |
|----------|-------------|----------|
| **Körskicklighet** | Generell kompetens | Alla aspekter, ca 3–5% totaleffekt |
| **Startteknik** | Förmåga vid start | Volt och auto-start |
| **Taktisk förmåga** | Positionering, tempobedömning | Optimal energianvändning |
| **Spurttiming** | Tajming av slutangrepp | Spurteffektivitet, +/- 2% i sluttamp |
| **Galopphantering** | Återhämtning vid galopp | Mildrande effekt, räddning |
| **Erfarenhet** | Antal körda lopp | Bättre under press, storlopp-bonus |
| **Lugn** | Stressnivå i pressade lägen | Bättre beslut i jämna lopp |
| **Kompatibilitet** | Matchning med hästar | Se kompatibilitetssystemet nedan |

## Kontraktssystem

Kuskar anställs på kontrakt:

| Kontraktstyp | Längd | Kostnad | Regler |
|---|---|---|---|
| **Fast anställd** | 8 spelveckor (4v verklig) | Veckolön: 3 000–25 000 kr | Max 3 fasta kuskar per stall |
| **Gästkusk** | Enstaka lopp | Per lopp: 2 000–15 000 kr | Bokningsförfrågan, kan nekas |
| **Lärlingskusk** | 16 spelveckor | Veckolön: 1 500 kr | Lägre skill men billig, utvecklas snabbt |

### Kuskens schema — KRITISK REGEL

**En kusk kan bara köra ETT lopp per loppomgång.**

Om det körs 4 lopp kl 19:30 kan din fasta kusk bara sitta i ett av dem. Har du 3 hästar som ska starta samma kväll behöver du 3 olika kuskar.

```
Exempel — Onsdag kvällslopp (4 lopp kl 19:30):
  Lopp 1: Bliansen    → Erik Lindblom (fast kusk, 12 000 kr/v)
  Lopp 3: Expressen   → Anna Svensson (fast kusk, 9 500 kr/v)
  Lopp 4: Guldpilen   → Mattias Öhr (gästkusk, 8 000 kr/lopp)
```

### Kusktillgänglighet

Gästkuskar har en **bokningskö**. Populära kuskar kan vara upptagna:

```python
class DriverBookingSystem:
    def request_guest_driver(self, driver_id, race_id, stable_id):
        driver = get_driver(driver_id)
        
        # Kolla om kusken redan är bokad i denna omgång
        if driver.is_booked_for_session(race.session_id):
            return BookingResult(
                success=False,
                reason="Kusken är redan bokad i denna omgång"
            )
        
        # Populära kuskar kan neka (baserat på ditt stalls rykte)
        acceptance_chance = (
            0.5 +
            stable.reputation / 200 +     # Bra rykte = lättare att boka
            (driver.fee / driver.market_rate - 1) * 0.3  # Betala mer = högre chans
        )
        
        if random() < acceptance_chance:
            driver.book(race_id)
            return BookingResult(success=True, fee=driver.fee)
        else:
            return BookingResult(
                success=False, 
                reason="Kusken avböjde — prova en annan eller höj arvodet"
            )
```

### Kuskutveckling

Kuskar förbättras genom att köra lopp:

```
Per kört lopp:
  +0.1–0.3 erfarenhet
  +0.05–0.15 körskicklighet
  
Per vinst:
  +0.2 erfarenhet extra
  
Per galoppering (som kusken räddade):
  +0.1 galopphantering

Per galopp-DQ:
  +0.05 galopphantering (lär sig av misstag)
  -0.1 lugn (temporärt)
```

---

# DEL 4: TAKTIK FÖRE LOPP — DET TAKTISKA DJUPET

## Innan varje lopp fattar spelaren dessa beslut:

### Steg 1: Välj häst

Vilken häst ska starta? Kolla:
- Fatigue-nivå (grön/gul/röd)
- Distansoptimum vs loppets distans
- Underlagspreferens vs banans underlag
- Senaste form (uppåt/nedåt)
- Kompatibilitet med tillgänglig kusk

### Steg 2: Välj kusk

Matcha kusk med häst. Se kompatibilitetssystemet (Del 8).

### Steg 3: Skoning

Se skoningssystemet (Del 5).

### Steg 4: Taktik

| Taktiskt val | Alternativ | Effekt |
|---|---|---|
| **Positionering** | Ledtaktik / Andraläge / Tredjespår / Dödens / Bakifrån | Avgör var hästen befinner sig i fältet |
| **Tempoprofil** | Offensiv / Balanserad / Försiktig | Energifördelning under loppet |
| **Spurtorder** | Tidigt (600m) / Normalt (400m) / Sent (250m) | När slutanfallet sätts in |
| **Galopphantering** | Säkerhet / Normal / Riskfylld | Kuskens instruktion vid galoppkänsla |
| **Kurvstrategi** | Innerled / Mittled / Ytterled | Position i kurvorna (kortar/sparar energi vs utrymme) |
| **Slutkörning** | Piska-aggressiv / Normal / Skonsam | Påtryckning i slutet (prestanda vs humörpåverkan) |

### Positioneringsstrategier i detalj

```
LEDTAKTIK
  Pro:  +5% tempo-kontroll, ingen luftmotstånd-malus från andra
  Con:  Hög energiförbrukning (drar hela fältet), 
        kräver hög Snabbhet + Startförmåga
  Risk: Om hästen tröttnar → alla passerar i sluttampen
  Bäst: Hästar med hög Uthållighet + Snabbhet

ANDRALÄGE (Rygg ledaren)
  Pro:  -8% energiförbrukning (vindskydd), kontrollerad position
  Con:  Beroende av ledarens tempo, svårt att komma ut i spurt
  Risk: Kusken måste hitta lucka — kräver hög Taktisk förmåga
  Bäst: Allround-hästar med bra kusk

TREDJESPÅR
  Pro:  Fritt utrymme, ingen stängning
  Con:  +12% energiförbrukning (längre väg, ingen vindskydd)
  Risk: Extremt energikrävande, hästen kan dö i slutet
  Bäst: Hästar med extrem Uthållighet + Styrka

DÖDENS (Utvändig ledaren)
  Pro:  Pressar ledaren, kontrollerar tempo
  Con:  +15% energiförbrukning, extremt krävande
  Risk: Största risken — men om det fungerar styr du loppet
  Bäst: Mycket starka hästar med hög Styrka + Mentalitet

BAKIFRÅN
  Pro:  -15% energiförbrukning i öppningsfas, maximal spurt
  Con:  Beroende av att hitta väg genom fältet, risk att stängas
  Risk: Kusk-beroende — kräver hög Taktisk förmåga + Spurttiming
  Bäst: Hästar med extrem Spurtstyrka + bra kusk
```

### Taktikbonusar och interaktioner

Taktiken interagerar med motståndarnas taktik:

```python
def calculate_tactical_interactions(entries):
    """
    Om 3+ hästar alla kör ledtaktik → högt tempo → alla tröttnar.
    Om ingen kör ledtaktik → lågt tempo → spurthästar dominerar.
    Taktisk läsning av motståndarna är nyckeln.
    """
    leaders = [e for e in entries if e.tactics.positioning == "lead"]
    
    if len(leaders) >= 3:
        # Tempokrig! Alla som kör offensivt betalar extra energi
        for e in leaders:
            e.energy_drain_modifier *= 1.25
        
        # Men bakifrån-hästar tjänar på kaos
        closers = [e for e in entries if e.tactics.positioning == "back"]
        for e in closers:
            e.sprint_bonus *= 1.10
    
    elif len(leaders) == 0:
        # Snigellopp — alla sparar, spurten avgör allt
        for e in entries:
            e.energy_drain_modifier *= 0.85
            if e.tactics.positioning == "back":
                e.sprint_bonus *= 0.95  # Alla har energi, spurt-fördel minskar
```

---

# DEL 5: SKONINGSSYSTEM

## Skotyper

| Sko | Vikt | Grepp | Hastighetseffekt | Galopprisk | Hållbarhet | Kostnad |
|---|---|---|---|---|---|---|
| **Barfota** | 0g | Lågt | +2% snabbhet | +15% galopprisk | — | 0 kr |
| **Lättsko (aluminium)** | 120g | Medel | +1% snabbhet | +5% galopprisk | 3 lopp | 800 kr |
| **Normalsko (stål)** | 350g | Högt | Referens (0%) | Referens (0%) | 6 lopp | 1 200 kr |
| **Tungsko (stål+platta)** | 500g | Mycket högt | -2% snabbhet | -10% galopprisk | 8 lopp | 1 500 kr |
| **Broddar** | 400g | Extremt (is/snö) | -1% normalt, +3% vinter | -5% galopprisk | 4 lopp | 2 000 kr |
| **Greppskor** | 380g | Extremt (lera/regn) | -1% normalt, +4% blött | -8% galopprisk | 5 lopp | 1 800 kr |
| **Balanssko (specialtillverkad)** | 250g | Högt | +1% balans | -12% galopprisk | 4 lopp | 3 500 kr |

### Skoval-strategi

```
VÄDER IDAG: Regn + 8°C, blött underlag

Alternativ A: Normalsko
  → Standard, inga bonusar eller nackdelar
  → Grepp: Tillräckligt men inte optimalt

Alternativ B: Greppskor  
  → +4% hastighet på blött underlag
  → -8% galopprisk
  → Kostar 1 800 kr och håller 5 lopp

Alternativ C: Barfota
  → +2% snabbhet (lättvikt)
  → MEN +15% galopprisk, och blött underlag → ytterligare +10% galopprisk
  → Extremt riskabelt i regn!

→ Smart val: Greppskor (värt investeringen)
```

### Hovslagarens roll

Du anlitar hovslagare med kvalitetsnivåer:

| Hovslagare | Kvalitet | Kostnad/skoning | Effekt |
|---|---|---|---|
| Bashovslagare | Standard | 500 kr | Skor håller normalt |
| Erfaren hovslagare | Bra | 1 200 kr | +1 lopps hållbarhet per sko, -3% hovproblem |
| Elithovslagare | Excellent | 2 500 kr | +2 lopps hållbarhet, -8% hovproblem, balansoptimering |

**Omskoning behövs var 4:e spelvecka (var 2:a verklig vecka).** Missar du omskoning → hovproblem → hästen kan inte starta.

---

# DEL 6: FODERSYSTEM

## Foderplan

Varje häst har en daglig foderplan som du sätter:

### Fodertyper

| Foder | Kostnad/spelvecka | Effekt |
|---|---|---|
| **Hö (standardkvalitet)** | 200 kr | Grundfoder. Nödvändigt. |
| **Hö (premiumkvalitet)** | 450 kr | +3% konditionsåterhämtning |
| **Hö (ekologiskt elithö)** | 800 kr | +5% kondition, +2% humör |
| **Havre** | 300 kr | Energi. +snabbhet-träningseffekt |
| **Kraftfoder (standard)** | 400 kr | Muskeluppbyggnad. +styrka-träning |
| **Kraftfoder (premium)** | 750 kr | +15% all träningseffekt |
| **Morötter** | 100 kr | +humör, +mentalitet (liten effekt) |
| **Äpplen** | 120 kr | +humör |
| **Elektrolyter** | 350 kr | Bättre i varmt väder, snabbare vätskebalans |
| **Ledtillskott** | 500 kr | -10% skaderisk, viktig för äldre hästar |
| **Biotintillskott** | 400 kr | Hovkvalitet, -5% hovproblem |
| **Mineralmix** | 300 kr | Generell hälsa, förebyggande |
| **Ölmask** | 200 kr | Päls och hull. Kosmetisk + liten hälsobonus |

### Fodermixen

Du sätter procent per kategori:

```
BLIANSEN — Foderplan:
  Hö (premium):     55%    →  247 kr/v
  Havre:            20%    →   60 kr/v
  Kraftfoder (std): 15%    →   60 kr/v
  Morötter:          5%    →    5 kr/v
  Tillskott:         5%    →   25 kr/v (ledtillskott)
                   ────
  Total foderkostnad: 397 kr/spelvecka (per häst)
```

### Vikt och prestation

```python
class WeightSystem:
    """
    Varje häst har en idealvikt. Avvikelse påverkar prestation.
    """
    def calculate_weight_effect(self, horse):
        ideal = horse.ideal_weight  # Genetiskt bestämt, t.ex. 480 kg
        actual = horse.current_weight
        deviation = abs(actual - ideal) / ideal
        
        if deviation < 0.02:    # Inom 2% av ideal
            return 1.0          # Ingen påverkan
        elif deviation < 0.05:  # 2-5% avvikelse
            return 0.97         # -3% prestation
        elif deviation < 0.10:  # 5-10% avvikelse
            return 0.92         # -8% prestation
        else:                   # >10% avvikelse
            return 0.85         # -15% prestation (allvarligt)
    
    def weekly_weight_update(self, horse):
        # Foderintag vs energiförbrukning
        calorie_intake = sum(feed.calories for feed in horse.feed_plan)
        calorie_burn = horse.base_metabolism + horse.training_burn
        
        surplus = calorie_intake - calorie_burn
        # Varje 500 kcal överskott/underskott ≈ 0.5 kg vikt/spelvecka
        horse.current_weight += surplus / 1000
```

---

# DEL 7: TRÄNINGSSYSTEM

## Träningspass

Varje häst kan ha ETT aktivt träningsprogram per spelvecka. Träning sker automatiskt men du väljer program och intensitet.

### Träningsprogram

| Program | Primär effekt | Sekundär effekt | Belastning | Kostnad/spelvecka |
|---|---|---|---|---|
| **Intervallträning** | Snabbhet +0.4 | Uthållighet +0.2 | Hög | 4 500 kr |
| **Långdistans** | Uthållighet +0.4 | Kondition +0.3 | Låg-Medel | 3 000 kr |
| **Startträning** | Startförmåga +0.5 | Snabbhet +0.1 | Medel | 3 500 kr |
| **Spurtträning** | Spurtstyrka +0.4 | Snabbhet +0.2 | Medel | 4 000 kr |
| **Mentalträning** | Mentalitet +0.3 | Galopptendens -0.2 | Låg | 2 500 kr |
| **Styrketräning** | Styrka +0.4 | Uthållighet +0.1 | Hög | 4 000 kr |
| **Balansträning** | Balans +0.4 | Galopptendens -0.3 | Medel | 3 500 kr |
| **Simträning** | Kondition +0.5 | Uthållighet +0.2 | Mycket låg | 5 000 kr (kräver pool) |
| **Bahnträning** | Alla +0.1 | Form +0.2 | Medel | 3 000 kr |
| **Vila** | Kondition +0.2 | Fatigue -snabb | Ingen | 500 kr (bara foder) |

### Intensitetsnivå

| Intensitet | Träningseffekt | Belastning | Skaderisk |
|---|---|---|---|
| Lätt (50%) | ×0.5 | ×0.3 | Minimal |
| Normal (75%) | ×0.75 | ×0.7 | Låg |
| Hård (100%) | ×1.0 | ×1.0 | Medel |
| Maximal (120%) | ×1.15 | ×1.5 | Hög |

### Träningseffektivitet och anläggning

```python
def calculate_training_effect(horse, program, intensity, stable):
    base_gain = program.primary_effect * intensity.multiplier
    
    # Anläggningsbonus
    if program.name == "Startträning" and stable.has_start_machine:
        base_gain *= 1.25  # 25% bättre med startmaskin
    elif program.name == "Simträning" and stable.has_pool:
        base_gain *= 1.0   # Pool krävs — annars 0 effekt
    elif stable.has_training_track:
        base_gain *= 1.10  # Egen bana = generell bonus
    
    # Tränarkvalitet
    trainer_bonus = 1.0 + (stable.trainer.quality / 100) * 0.2
    base_gain *= trainer_bonus
    
    # Foderbonus (premium kraftfoder)
    if horse.has_premium_feed:
        base_gain *= 1.15
    
    # Åldersmodifierare (unga hästar lär sig snabbare)
    if horse.age < 4:
        base_gain *= 1.3
    elif horse.age > 8:
        base_gain *= 0.6  # Gamla hästar tappar träningseffekt
    
    # Genetiskt tak — kan aldrig tränas över potential
    current = getattr(horse, program.primary_stat)
    potential = horse.genetic_potential[program.primary_stat]
    ceiling_factor = max(0, 1.0 - (current / potential) ** 3)
    base_gain *= ceiling_factor
    
    # Humör påverkar träning
    if horse.mood < 30:
        base_gain *= 0.5  # Olycklig häst lär sig inte
    elif horse.mood > 80:
        base_gain *= 1.1  # Glad häst lär sig bättre
    
    return base_gain
```

### Tränare (personal)

| Tränare | Kvalitet | Lön/spelvecka | Effekt |
|---|---|---|---|
| Assisterande tränare | Basic | 2 000 kr | Referens |
| Tränare | Bra | 5 000 kr | +10% träningseffekt |
| Elittränare | Excellent | 12 000 kr | +20% träningseffekt, avslöjar dolda egenskaper snabbare |

---

# DEL 8: KOMPATIBILITETSSYSTEM

## Konceptet

Inspirerat av Xperteleven. Hästar och kuskar har **personlighetstyper** och **körstilspreferenser** som antingen matchar eller krockar. Att hitta rätt kombination kräver scouting och tid.

### Personlighetstyper (hästar)

Varje häst har 2 av 6 personlighetsdrag (primär + sekundär):

| Personlighet | Beskrivning | Effekt |
|---|---|---|
| **Lugn** | Stabil, förutsägbar | +stabil prestation, -toppresultat |
| **Het** | Ivrig, snabb men orolig | +snabbhet, +galopprisk |
| **Envis** | Stark vilja, svårstyrd | +uthållighet, -kuskrespons |
| **Lyhörd** | Svarar snabbt på kusk | +kuskeffekt, -egen initiativ |
| **Modig** | Tar strid, viker inte | +tävlingsinstinkt, klarar press |
| **Känslig** | Påverkas av omgivning | +potential, men -i oroligt fält |

### Körstilar (kuskar)

Varje kusk har en primär körstil:

| Körstil | Beskrivning | Matchning |
|---|---|---|
| **Tålmodig** | Väntar, pressar inte | ★★★ med Känslig, Het. ★☆☆ med Envis |
| **Offensiv** | Pressar, vill framåt | ★★★ med Modig, Envis. ★☆☆ med Känslig |
| **Taktisk** | Anpassar sig, läser lopp | ★★★ med Lyhörd, Lugn. ★★☆ med alla |
| **Hård** | Kräver mycket, ger resultat | ★★★ med Envis, Modig. ★☆☆ med Känslig, Lyhörd |
| **Mjuk** | Uppmuntrande, varsam | ★★★ med Känslig, Lyhörd. ★☆☆ med Envis |

### Kompatibilitetsberäkning

```python
class CompatibilityEngine:
    """
    Beräknar hur väl en häst och kusk matchar.
    Kompatibilitet: 0–100, där:
      0–30:  Dålig match (-5% prestation)
      31–50: Okej match (ingen bonus/straff)
      51–70: Bra match (+3% prestation)
      71–85: Utmärkt match (+5% prestation, -5% galopprisk)
      86–100: Perfekt match (+8% prestation, -10% galopprisk, +humör)
    """
    
    # Matchningsmatris: kusk_stil × häst_personlighet → poäng
    MATRIX = {
        ("Tålmodig", "Lugn"):     65,
        ("Tålmodig", "Het"):      85,   # Tålmodig kusk lugnar het häst
        ("Tålmodig", "Envis"):    30,   # Tålmodig orkar inte med envis
        ("Tålmodig", "Lyhörd"):   70,
        ("Tålmodig", "Modig"):    55,
        ("Tålmodig", "Känslig"):  80,
        
        ("Offensiv", "Lugn"):     45,
        ("Offensiv", "Het"):      50,   # Båda offensiva = kaos-risk
        ("Offensiv", "Envis"):    75,   # Offensiv kusk + envis häst = framåt
        ("Offensiv", "Lyhörd"):   60,
        ("Offensiv", "Modig"):    90,   # Perfekt match!
        ("Offensiv", "Känslig"):  25,   # Offensiv kusk stressar känslig häst
        
        ("Taktisk", "Lugn"):      75,
        ("Taktisk", "Het"):       65,
        ("Taktisk", "Envis"):     55,
        ("Taktisk", "Lyhörd"):    85,   # Taktisk + lyhörd = full kontroll
        ("Taktisk", "Modig"):     70,
        ("Taktisk", "Känslig"):   60,
        
        ("Hård", "Lugn"):         50,
        ("Hård", "Het"):          35,   # Hård kusk + het häst = galopp
        ("Hård", "Envis"):        80,   # Hård + envis = respekt
        ("Hård", "Lyhörd"):       30,   # Hård kusk skrämmer lyhörd häst
        ("Hård", "Modig"):        85,
        ("Hård", "Känslig"):      20,   # Värsta matchningen
        
        ("Mjuk", "Lugn"):         70,
        ("Mjuk", "Het"):          60,
        ("Mjuk", "Envis"):        25,   # Mjuk kusk = envis häst gör som den vill
        ("Mjuk", "Lyhörd"):       90,   # Perfekt match!
        ("Mjuk", "Modig"):        55,
        ("Mjuk", "Känslig"):      95,   # Allra bästa matchningen
    }
    
    def calculate(self, horse, driver):
        primary_score = self.MATRIX.get(
            (driver.driving_style, horse.personality_primary), 50
        )
        secondary_score = self.MATRIX.get(
            (driver.driving_style, horse.personality_secondary), 50
        )
        
        # Primär personlighet väger mer
        base = primary_score * 0.7 + secondary_score * 0.3
        
        # Erfarenhet av DENNA häst (ju fler lopp ihop, desto bättre)
        shared_races = get_shared_race_count(horse, driver)
        experience_bonus = min(15, shared_races * 2)
        
        # Veteranbonus (erfarna kuskar anpassar sig bättre)
        if driver.experience > 80:
            base = base * 0.7 + 50 * 0.3  # Dras mot mitten (anpassningsbar)
        
        return clamp(base + experience_bonus, 0, 100)
```

### Scouting — Att avslöja kompatibilitet

**Personlighet är INTE synlig direkt.** Du ser bara:
- Grundstats (snabbhet, uthållighet etc) — alltid synligt
- Personlighet — kräver scouting (se nedan)
- Dolda egenskaper — kräver avancerad scouting eller lopp

```python
class ScoutingSystem:
    """
    Scouting kostar tid och pengar.
    Ju mer du scouter, desto mer avslöjas.
    """
    
    def scout_horse(self, horse, scout_level, stable):
        result = ScoutReport()
        
        # Nivå 1: Grundscouting (gratis, alla kan se)
        result.visible_stats = horse.get_basic_stats()
        result.age = horse.age
        result.race_record = horse.get_record()
        
        if scout_level >= 1:
            # Nivå 2: Standardscouting (1 500 kr, 1 speldag)
            result.personality_primary = horse.personality_primary
            result.estimated_potential = horse.potential + gauss(0, 10)
            result.gallop_tendency = "Låg/Medel/Hög"  # Ungefärlig
        
        if scout_level >= 2:
            # Nivå 3: Djupscouting (4 000 kr, 3 speldagar)
            result.personality_secondary = horse.personality_secondary
            result.hidden_preferences = {
                'distance_optimum': horse.distance_optimum,
                'surface_preference': horse.surface_preference,
            }
            result.potential_exact = horse.potential  # ±5 poäng
            result.injury_history_analysis = True
        
        if scout_level >= 3:
            # Nivå 4: Elitscouting (10 000 kr, 5 speldagar)
            result.genetic_profile = horse.get_genetic_data()
            result.compatibility_estimate = True
            result.all_hidden_traits = True
        
        return result
```

### Kompatibilitet vid hästköp (Transfer)

När du kollar en häst på transfermarknaden:

```
STORMKUNGEN — Till salu: 180 000 kr
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Grundstats:       Synliga ✓
Personlighet:     ??? (kräver scouting nivå 2)
Dold potential:   ??? (kräver scouting nivå 3)

[Scouta — 1 500 kr, klar om 1 speldag]

---

(Efter scouting nivå 2):

STORMKUNGEN — Till salu: 180 000 kr
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Grundstats:       Synliga ✓
Personlighet:     Het (primär), Modig (sekundär)
Potentialbedömning: Hög (±10)

Kompatibilitet med dina kuskar:
  Erik Lindblom (Taktisk):  ★★★☆☆  65/100  "Bra match"
  Anna Svensson (Mjuk):     ★★☆☆☆  48/100  "Okej match"

→ Het + Modig häst passar bäst med Offensiv kusk!
  Du har ingen offensiv kusk — överväg att rekrytera en.
```

---

# DEL 9: AVELSYSTEM

## Grundprocess

```
1. VÄLJ STO (din häst, minst 4 spelår)
   └── Sto måste vara i god hälsa, inte tävla under dräktighet

2. VÄLJ HINGST (från avelsregistret)
   └── Hingstägare sätter betäckningsavgift (5 000–200 000 kr)
   └── Du kan se hingstens:
       - Tävlingsrekord
       - Stamtavla (3 generationer)
       - Avkommor och deras prestationer
       - Genetisk profil (om scouted)

3. BETÄCKNING
   └── Kostar: Betäckningsavgift + 2 000 kr veterinär
   └── Lyckas med 70% sannolikhet (bättre vet → högre chans)
   └── Om misslyckad: Kan försöka igen nästa spelvecka

4. DRÄKTIGHET
   └── 22 spelveckor (11 verkliga veckor)
   └── Sto kan inte tävla under dräktigheten
   └── Foderkostnad ökar +30%
   └── Veterinärkontroller rekommenderas (2 under dräktigheten)

5. FÖLNING
   └── Fölet föds med basegenskaper bestämda av genetik
   └── Grundegenskaper synliga efter 2 spelveckor
   └── Kön bestäms slumpmässigt (50/50)

6. UPPFÖDNING (0–2 spelår)
   └── Grundhantering och socialisering
   └── Kostnader: Foder + stallplats + veterinär
   └── Inga lopp, ingen riktig träning

7. UNGHÄSTTRÄNING (2–3 spelår)
   └── Grundträning börjar
   └── Debuttid: 3 spelår
```

## Genetiksystem

### Arvsprincipen

```python
class GeneticEngine:
    """
    Varje egenskap har ett genetiskt värde från varje förälder.
    Fölet ärver en blandning + mutation.
    
    Genetisk potential = max-tak som egenskapen kan nå genom träning.
    Startegenskaper = var hästen börjar (lägre än potential).
    """
    
    def breed(self, mare, stallion):
        foal = Horse()
        
        for stat in CORE_STATS:
            # Genetisk potential från föräldrar
            mare_gene = mare.genetic_potential[stat]
            stallion_gene = stallion.genetic_potential[stat]
            
            # Arv: 40% från varje förälder + 20% slump
            inherited = (
                mare_gene * 0.40 +
                stallion_gene * 0.40 +
                gauss(50, 15) * 0.20  # Slumpfaktor
            )
            
            # Nick-effekt: Vissa blodlinjer kombinerar bättre
            nick = self.calculate_nick(mare.bloodline, stallion.bloodline, stat)
            inherited *= nick  # 0.9 = dålig nick, 1.0 = neutral, 1.15 = bra nick
            
            # Mutation: Liten chans till exceptionellt föl
            mutation_roll = random()
            if mutation_roll < 0.02:      # 2% chans
                inherited *= 1.20         # Stjärna! +20% potential
            elif mutation_roll < 0.05:    # 3% chans
                inherited *= 1.10         # Talang
            elif mutation_roll > 0.98:    # 2% chans
                inherited *= 0.85         # Sämre än förväntat
            
            foal.genetic_potential[stat] = clamp(inherited, 20, 99)
            
            # Startegenskaper = 30-50% av potential
            foal.current_stats[stat] = foal.genetic_potential[stat] * uniform(0.3, 0.5)
        
        # Personlighet: Ärv från föräldrar eller mutation
        foal.personality_primary = self.inherit_personality(mare, stallion)
        foal.personality_secondary = self.inherit_personality(mare, stallion, secondary=True)
        
        # Galopptendens (starkt ärftlig)
        foal.gallop_tendency = (
            mare.gallop_tendency * 0.45 +
            stallion.gallop_tendency * 0.45 +
            gauss(15, 5) * 0.10
        )
        
        # Idealvikt (ärftlig)
        foal.ideal_weight = (mare.ideal_weight + stallion.ideal_weight) / 2 + gauss(0, 8)
        
        return foal
    
    def calculate_nick(self, mare_bloodline, stallion_bloodline, stat):
        """
        Nick-effekten: Vissa blodlinjekombinationer ger bonusar.
        Spelaren kan se nick-statistik i avelsregistret.
        
        Baserat på historisk data i spelet:
        Om avkommor från denna korsning har presterat bra → bra nick.
        """
        key = frozenset([mare_bloodline.id, stallion_bloodline.id])
        
        if key in self.nick_registry:
            return self.nick_registry[key][stat]
        
        # Okänd kombination — neutral med viss variation
        return 1.0 + gauss(0, 0.05)
```

### Stamtavla och blodlinjer

```
STORMKUNGEN (hingst, 6 spelår)
├── Far: EXPRESSEN (snabbhet 85, spurt 88)
│   ├── Farfar: BLIXTEN (snabbhet 90)
│   └── Farmor: SOLSTRÅLEN (uthållighet 82)
└── Mor: GULDSTJÄRNAN (uthållighet 87, mentalitet 85)
    ├── Morfar: JÄRNMANNEN (uthållighet 92, styrka 88)
    └── Mormor: NATTFJÄRILEN (snabbhet 78, balans 84)

NICK-ANALYS:
  Expressen-linjen × Järnmannen-linjen:
    Kända avkommor: 12
    Genomsnittlig prestation: +8% över förväntat
    Starkast i: Snabbhet, Uthållighet
    Nick-rating: ★★★★☆ (BRA)
```

### Avelsregistret (spelargenererat)

Andra spelare registrerar sina hingstar:

```
AVELSREGISTER — Säsong 2024
━━━━━━━━━━━━━━━━━━━━━━━━━━

EXPRESSEN (ägare: DennisStall)
  Avgift: 35 000 kr
  Rekord: 24 starter, 5 vinster, km-tid 1.12,4
  Avkommor i spel: 8 st, varav 3 vinnare
  Blodlinje: Expressen-linjen
  [Boka betäckning]

DALERO (ägare: SundsvallsTrav)  
  Avgift: 18 000 kr
  Rekord: 52 starter, 15 vinster, km-tid 1.13,0
  Avkommor i spel: 14 st, varav 7 vinnare
  Blodlinje: Järnmannen-linjen
  [Boka betäckning]
```

---

# DEL 10: DAGLIGA AKTIVITETER & ENGAGEMANG

## Morgonrapport (varje dag, 08:00)

Automatisk notifikation med:

```
╔══════════════════════════════════════╗
║  MORGONRAPPORT — Tisdag, Vecka 35   ║
╠══════════════════════════════════════╣
║                                      ║
║  🐴 HÄSTSTATUS                       ║
║  Bliansen:    Pigg, redo ✅          ║
║  Expressen:   Lite stel i bakbenet ⚠️║
║  Dalero:      Vila (skadad) ❌       ║
║  Nattsvansen: Bra humör ✅           ║
║  Guldpilen:   Övervikt +3 kg ⚠️     ║
║                                      ║
║  📋 ATT GÖRA IDAG                    ║
║  • Anmäl till kvällslopp (deadline 15:00) ║
║  • Expressens veterinärkontroll      ║
║  • Guldpilens foder behöver justeras ║
║  • Ny auktion: Häst i din prisklass  ║
║                                      ║
║  💰 EKONOMI                          ║
║  Saldo: 487 250 kr (+16 000 igår)    ║
║                                      ║
╚══════════════════════════════════════╝
```

## Dagliga beslut och aktiviteter

### Varje dag finns dessa att göra:

**1. Hästtillsyn (30 sek — obligatoriskt för att inte tappa humör)**
- Kolla varje hästs status
- Klicka "Tillsyn utförd" — hästen får +1 humör
- Missar du 3 dagar i rad → humör sjunker, tränare klagar

**2. Foderrevidering (1–2 min när det behövs)**
- Häst gått upp i vikt? → Justera fodermix
- Häst verkar trött? → Lägg till elektrolyter
- Ny säsong (vinter)? → Byt till vinterfoder

**3. Träningsjustering (1 min)**
- Hästen har nått platå i snabbhet → Byt till uthållighetsträning
- Hästen startar i lopp om 2 dagar → Sätt på lätt träning
- Unghäst visar talang i spurt → Fokusera spurtträning

**4. Loppanmälan (2–5 min på loppdagar)**
- Granska tillgängliga lopp
- Kolla distans, underlag, väder, fält
- Välj häst → kusk → sko → taktik
- Bekräfta anmälan

**5. Scoutinguppdrag (1 min att starta, vänta på resultat)**
- Scouta motståndarhästar inför lopp
- Scouta hästar på transfermarknaden
- Scouta unghästar i eget stall (avslöja potential)

**6. Pressmeddelande (2 min, max 1/speldag)**
- Skriv om senaste vinst/förlust
- Ger: PR-poäng → sponsorintresse → pengar
- Välj ton: Ödmjuk / Självsäker / Provocerande
  - Ödmjuk: +PR, +sponsorer (säkert)
  - Självsäker: +PR om du sedan vinner, -PR om du förlorar
  - Provocerande: Mycket +PR men -relation med andra spelare

**7. Sponsorkontakt (event, 1–2 ggr/spelvecka)**
- Nya sponsorerbjudanden dyker upp
- Förhandla villkor (bonusar vid vinst, grundbelopp)
- Bättre rykte = bättre sponsorer

**8. Stallunderhåll (event, slumpmässigt)**
- "Taket läcker i stallet — reparera nu (5 000 kr) eller vänta?"
  - Vänta → risk att häst blir sjuk
- "Hästtransporten behöver service"
  - Ignorera → kan inte köra till borta-banor

**9. Personalsamtal (event, slumpmässigt)**
- "Din tränare vill ha löneökning — 3 000 kr/v mer"
  - Acceptera → behåll bra tränare
  - Neka → tränare kan säga upp sig om 4 veckor
- "Din hovslagare erbjuder rabatt om du binder dig 8 veckor"

**10. Transferbevakning**
- Bevakade hästar: Notis om ny budgivning
- Bevakade kuskar: Notis om kontrakt löper ut
- Bevakade hingstar: Notis om betäckningstid

## Veckoaktiviteter

### Varje spelvecka (= var 3,5:e verklig dag):

**Löneutbetalning** — Alla löner dras automatiskt
**Hovkontroll** — Var 4:e spelvecka: Omskoning krävs
**Veterinärkontroll** — Var 4:e spelvecka: Rekommenderad
**Säsongsavslutning** — Var 16:e spelvecka: Prisutdelning, kontraktsomgång
**Avelsperiod** — Var 32:e spelvecka: Betäckningssäsong öppnar

---

# DEL 11: LOPPDETALJER — VERKLIGA DISTANSER

## Distanser som förekommer i spelet

Baserat på svensk trav:

| Distans | Startmetod | Typ | Vanlighet | Karaktär |
|---|---|---|---|---|
| **1609m** | Auto | Sprint | Vanlig | Snabbhet + start avgör |
| **1640m** | Auto/Volt | Sprint | Mycket vanlig | Standard kort-lopp |
| **1700m** | Volt | Sprint+ | Ovanlig | Specialbanor |
| **2140m** | Auto/Volt | Medel | Mycket vanlig | Standard-distans (vanligast) |
| **2160m** | Volt | Medel | Vanlig | Standard volt |
| **2640m** | Volt | Stayer | Vanlig | Uthållighetslopp |
| **2680m** | Volt | Stayer | Ganska vanlig | Lång volt |
| **3140m** | Volt | Marathon | Ovanlig | Speciallopp, extremt uthållighet |
| **3200m** | Volt | Marathon | Sällsynt | Elitlopp lång distans |
| **1000m** | Auto | Sprintjakt | Sällsynt | Event/speciallopp |
| **1800m** | Auto | Mellansprint | Ganska vanlig | Montélopp |

## Loppklasser och prispengar

| Klass | Division | Prispott | Anmälningsavgift |
|---|---|---|---|
| **V75-lopp** | Alla | 150 000–500 000 kr | 3 000 kr |
| **Gulddivisionen** | Div 1 | 200 000–400 000 kr | 5 000 kr |
| **Silverdivisionen** | Div 2–3 | 80 000–200 000 kr | 2 000 kr |
| **Bronsdivisionen** | Div 4–5 | 30 000–80 000 kr | 1 000 kr |
| **Vardagslopp** | Div 6 | 15 000–40 000 kr | 500 kr |
| **Unglopp** | Öppen (3–4 år) | 40 000–100 000 kr | 1 500 kr |
| **Stolopp** | Bara ston | 50 000–150 000 kr | 2 000 kr |
| **Amatörlopp** | Lägre | 10 000–25 000 kr | 300 kr |
| **Kvallopp** | Alla | 0 kr (kvalificering) | 800 kr |

### Prispengsdistribution

| Placering | Andel av prispott |
|---|---|
| 1:a | 40% |
| 2:a | 20% |
| 3:a | 12% |
| 4:a | 8% |
| 5:a | 6% |
| 6:a–8:a | 4% vardera (resterande) |
| DQ | 0% |

### Kilometertider per division

| Division | Vinnartid (km-tid, 2140m) | Genomsnitt | Långsammast |
|---|---|---|---|
| Div 1 (Elit) | 1.09,0–1.11,0 | 1.11,5 | 1.13,0 |
| Div 2 | 1.11,0–1.13,0 | 1.13,0 | 1.15,0 |
| Div 3 | 1.13,0–1.15,0 | 1.15,0 | 1.17,0 |
| Div 4 | 1.15,0–1.17,0 | 1.17,0 | 1.19,0 |
| Div 5 | 1.17,0–1.19,0 | 1.19,0 | 1.21,0 |
| Div 6 | 1.19,0–1.22,0 | 1.21,0 | 1.24,0 |
| Unglopp | 1.14,0–1.18,0 | 1.16,0 | 1.20,0 |

---

# DEL 12: RESULTAT OCH HÄSTLOGG

## Resultatkortet (efter varje lopp)

```
╔═══════════════════════════════════════════════════════════╗
║  LOPP 6 — V86 Silverdivisionen, 2140m Volt               ║
║  Solvalla • Onsdag 19:30 • Grus • Uppehåll 12°C          ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Plac  Häst          Kusk             Km-tid  Pris       ║
║  ────  ────          ────             ──────  ────       ║
║  1.    EXPRESSEN     Erik Lindblom    1.12,4a  60 000 kr ║
║  2.    BLIANSEN      Anna Svensson    1.12,8a  30 000 kr ║
║  3.    GULDPILEN     Mattias Öhr      1.13,1a  18 000 kr ║
║  4.    DALERO (AI)   System-kusk      1.13,6a   9 000 kr ║
║  5.    STORMVIND(AI) System-kusk      1.14,0a   6 000 kr ║
║  6.    BLIXTRA       Per Eriksson     1.14,3a   4 000 kr ║
║  7.    VINTERNATT    Lisa Berg        1.15,1a   3 000 kr ║
║  DQ    NATTSVANSEN   Erik Lindblom    galp.1800m    0 kr ║
║                                                           ║
║  (a = autostart)                                          ║
╠═══════════════════════════════════════════════════════════╣
║  DETALJERAT — EXPRESSEN                                   ║
║                                                           ║
║  Sektortider:  0–500m:  1.16,2 (medel)                   ║
║                500–1000m: 1.13,5 (snabb)                  ║
║                1000–1500m: 1.12,0 (snabb)                 ║
║                1500–2140m: 1.10,8 (mycket snabb)          ║
║                                                           ║
║  Energikurva:  Start 100% → 500m 91% → 1000m 78%         ║
║                → 1500m 62% → Mål 31%                      ║
║                                                           ║
║  Taktik:       Andraläge → Spurt 400m kvar                ║
║  Kuskbetyg:    8/10 (utmärkt tajming)                     ║
║  Kompatibilitet: 78/100 (Utmärkt match)                   ║
║  Skor:         Lättsko (bra val — torrt underlag)         ║
║                                                           ║
║  Galoppnotering: Inga galopperingar                       ║
╚═══════════════════════════════════════════════════════════╝
```

## Hästens meritlista

```
BLIANSEN — Karriärstatistik
━━━━━━━━━━━━━━━━━━━━━━━━━━

Starter: 24 | Vinster: 8 | Tvåa: 5 | Trea: 3 | DQ: 1
Vinstprocent: 33%   Plocka-procent: 67%
Totalt intjänat: 342 000 kr
Bästa km-tid: 1.12,4a (2140m, Solvalla)

Per distans:
  1640m auto:  6 starter, 3 vinster, bäst 1.11,8
  2140m volt:  14 starter, 4 vinster, bäst 1.12,4
  2640m volt:  4 starter, 1 vinst, bäst 1.14,2

Per underlag:
  Grus:    18 starter, 7 vinster (39%)
  Syntet:  6 starter, 1 vinst (17%)  ← Gillar inte syntet

Per väder:
  Uppehåll: 15 starter, 7 vinster (47%)
  Regn:     9 starter, 1 vinst (11%)  ← Dålig i regn

Senaste 5 lopp: 2-1-4-1-3 (form: ↗ uppåt)
```

---

# DEL 13: EKONOMISK MODELL

## Kostnadsöversikt per spelvecka (1 häst)

| Post | Min | Normal | Max |
|---|---|---|---|
| Foder | 200 kr | 400 kr | 800 kr |
| Träning | 500 kr | 3 500 kr | 5 000 kr |
| Stallplats | 500 kr | 500 kr | 500 kr |
| Omskoning (snittat) | 200 kr | 350 kr | 650 kr |
| Veterinär (snittat) | 100 kr | 300 kr | 800 kr |
| **TOTALT per häst** | **1 500 kr** | **5 050 kr** | **7 750 kr** |

## Driftskostnad för helt stall (5 hästar + personal)

| Post | Kostnad/spelvecka |
|---|---|
| 5 hästar × 5 050 kr snitt | 25 250 kr |
| 2 fasta kuskar | 10 750 kr |
| Tränare | 5 000 kr |
| Stallhyra (5 boxar) | 2 500 kr |
| Diverse (reparationer, transport) | 2 000 kr |
| **TOTAL DRIFT** | **~45 500 kr/spelvecka** |

## Break-even-analys

Med 5 hästar behöver du tjäna ~45 500 kr/spelvecka.

Om varje häst startar varannan spelvecka (7 starter per 2-veckorsperiod):
- Behövs snittinkomst: ~6 500 kr per start
- Vinst i Bronsdivisionen (Div 4–5): 30 000–80 000 kr pott
  - 1:a plats: 12 000–32 000 kr
  - 3:a plats: 3 600–9 600 kr
  - 6:a plats: 1 200–3 200 kr

**Slutsats**: Du behöver placera dig bra regelbundet. Ekonomin är tight i början, precis som Hattrick, vilket skapar meningsfulla beslut.

### Inkomstkällor utöver lopp

| Källa | Belopp/spelvecka | Villkor |
|---|---|---|
| Sponsorer | 5 000–50 000 kr | Beror på rykte/division |
| Pressmeddelanden | 500–3 000 kr | 1 per speldag max |
| Stallvisning | 2 000–8 000 kr | 1 per spelvecka, tar tid |
| Hästförsäljning | Engångsbelopp | Transfermarknad |
| Avelstjänst (hingst) | Per betäckning | Kräver framgångsrik hingst |
| Login streak | 200–1 000 kr | Daglig inloggning |
| V75-tippning (vinst) | 5 000–50 000 kr | Om du tippar rätt |
| Achievements | Engångsbelöningar | Vid milestone |

---

# DEL 14: STORLOPP & SÄSONGSSTRUKTUR

## Säsongskalender

**1 säsong = 16 spelveckor = 8 verkliga veckor**

```
Spelvecka 1–2:    Säsongsstart, nya kontrakt, förberedelse
Spelvecka 3–6:    Seriespel (ligalopp i din division)
Spelvecka 7:      Kval till storlopp
Spelvecka 8:      STORLOPP 1 — Kriteriet (3-åriga unghästar)
Spelvecka 9–12:   Seriespel fortsätter
Spelvecka 13:     Kval till finaler
Spelvecka 14:     STORLOPP 2 — Elitloppet (alla divisioner)
Spelvecka 15:     Finaler + Cupfinaler
Spelvecka 16:     Säsongsavslutning — Priser, upp/nedflyttning

MELLAN SÄSONGER (spelvecka 16–1):
  → Kontraktsförhandlingar
  → Transferfönster EXTRA aktivt
  → Betäckningssäsong (avel)
  → Stalluppgraderingar
  → Prisceremoni: Årets Häst, Årets Stall, Årets Uppfödare etc
```

---

# DEL 15: NPC-SYSTEMET KOMPLETT

## NPC-stall per division

| Division | Antal NPC-stall | Hästar per NPC-stall | Nedtrappning |
|---|---|---|---|
| Div 6 (start) | 6 | 3–4 | Fasas ut sist |
| Div 5 | 5 | 3–4 | Vid 40+ spelare |
| Div 4 | 4 | 3–4 | Vid 50+ spelare |
| Div 3 | 3 | 2–3 | Vid 60+ spelare |
| Div 2 | 2 | 2–3 | Vid 70+ spelare |
| Div 1 | 1 | 2 | Vid 80+ spelare |

## NPC-namnsgenerator

```python
PREFIXES = [
    "Storm", "Guld", "Silver", "Blixt", "Natt", "Sol", "Vinter", "Järn",
    "Kung", "Dröm", "Stjärn", "Eld", "Is", "Nord", "Snabb", "Stark",
    "Mörk", "Ljus", "Vind", "Åsk", "Lyn", "Kraft", "Ädel", "Fri",
]

SUFFIXES = [
    "pilen", "svansen", "fansen", "stegen", "bollen", "blansen",
    "pransen", "dansen", "kransen", "bransen", "tansen", "ransen",
    "en", "ansen", "aren", "ansen", "anden", "ansen",
    "ansen", "ansen", "ansen", "ansen", "ansen", "ansen",
]

# Kombineras: "Stormpilen", "Guldsvansen", "Nattdansen" etc.
```

## NPC-beteende

NPC-hästar:
- Anmäler sig automatiskt till lopp i sin division
- Väljer taktik baserat på sina stats (hög snabbhet → ledtaktik)
- Kan säljas på transfermarknaden (spelaren köper)
- Kan INTE köpa spelarens hästar
- Har realistiska resultat men vinner sällan mot bra spelare
- Kuskar: Systemkuskar (gratis, medelhög skill)

---

# DEL 16: TECH STACK SAMMANFATTNING

```
FRONTEND
  ├── Next.js 14+ (App Router, SSR)
  ├── React + TypeScript
  ├── Tailwind CSS
  ├── Framer Motion (animationer)
  ├── Socket.io-client (live lopp)
  └── PWA-stöd (installbar på mobil)

BACKEND
  ├── Python FastAPI (huvud-API)
  ├── PostgreSQL (all data)
  ├── Redis (sessions, cache, leaderboards, realtid)
  ├── Celery + Redis (bakgrundsjobb: träning, simulering)
  └── Socket.io (WebSocket-server för live)

LOPPMOTOR
  ├── Python (separat modul)
  ├── Deterministisk simulering (seed-baserad)
  ├── Anropas via Celery-task eller direkt API
  └── Output: JSON (snapshots + events + resultat)

INFRASTRUKTUR
  ├── Docker Compose (utveckling)
  ├── Hetzner Cloud (produktion, börja billigt)
  ├── CloudFlare (CDN + DNS)
  ├── GitHub Actions (CI/CD)
  └── Sentry (error tracking)

SCHEDULER
  ├── Celery Beat (tidsstyrda tasks)
  ├── Lopp simuleras vid exakta tider
  ├── Dagliga: morgonrapport, hälsouppdatering
  └── Veckovisa: löner, omskoning-påminnelse
```
