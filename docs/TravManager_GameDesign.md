# TravManager — Online Travstall-simulator
## Game Design Document v1.0

---

## Koncept

**TravManager** är ett gratis, browser-baserat MMO-managerspel för travsporten — tänk Hattrick, men för svensk/nordisk trav. Du driver ett stall med travhästar, tränar dem, väljer kuskar, anmäler till lopp, hanterar ekonomi, föder upp föl och klättrar genom divisioner. Matcher (lopp) simuleras i realtid och du spelar mot andra riktiga managers.

Spelet är designat med **"20 min/vecka räcker, men det finns alltid mer att göra"**-filosofin. Varje dag bjuder på minst ett litet beslut, och varje vecka har 2–3 loppdagar som höjdpunkter.

---

## Vad vi lär av Hattrick (och vad vi gör bättre)

Från community-feedback har Hattrick dessa kända svagheter som vi kan undvika:

**Problem i Hattrick → Vår lösning:**

1. **"Spelet stagnerar — för lite att göra mellan matcherna"** → Vi har dagliga stallsysslor, foder-/hälsosystem, och marknadsaktiviteter som gör att det alltid finns mikrobeslut att ta.

2. **"Ingen spelaruthyrning/lån"** → Vi har ett lån-system för kuskar och hästar (leasing).

3. **"Matchmotorn är ogenomskinlig"** → Vår loppmotor visar detaljerade stats efteråt: sektortider, puls, energinivåer, kuskbeslut.

4. **"Nya spelare möter orimligt starka motståndare"** → Dynamisk divisionsplacering baserat på stallets sammanlagda kvalitet. Mjukstart med NPC-lopp.

5. **"Daterad grafik och UX"** → Modern, mobile-first React-app med live loppvisare.

6. **"Brist på social interaktion"** → Stallförbund, kuskagenter, auktionsplattform, V75-tippning mot andra spelare.

7. **"Achievementssystemet är tunt"** → Djupt achievement-system kopplat till meningsfulla belöningar.

---

## Spelets kärna — Veckoloop

### Veckokalender (spelets hjärtslag)

| Dag | Huvudaktivitet | Tidsåtgång |
|-----|---------------|------------|
| **Måndag** | Veckoplanering: anmäl hästar till lopp, sätt träningsschema | 5–10 min |
| **Tisdag** | Transfermarknad öppnar (auktionsdag), scoutrapporter | 5 min |
| **Onsdag** | **LOPPDAG 1** — Kvällslopp simuleras kl 19:30 | 10–15 min live |
| **Torsdag** | Analysera lopp, justera träning, pressmeddelande | 5 min |
| **Fredag** | Uppfödning (betäckningssäsong), veterinärbesök, sponsorkontakt | 5 min |
| **Lördag** | **LOPPDAG 2** — V75-simulering, storlopp | 15–20 min live |
| **Söndag** | Ekonomisk sammanställning, löneutbetalningar, vilodag | 3 min |

---

## Stallhantering (dagliga/veckovisa sysslor)

### Hästar — Egenskaper

Varje häst har:

- **Grundegenskaper**: Snabbhet, Uthållighet, Mentalitet, Startförmåga, Spurtstyrka
- **Dolda egenskaper** (avslöjas genom lopp/scouting): Banpreferens (vänster/höger), Väderrespons, Tävlingsinstinkt
- **Fysisk status**: Kondition (0–100), Skaderisk (0–100), Vikt, Hovstatus
- **Ålder**: Föl → Unghäst → Tävlingshäst → Avelssto/Avelshingst → Pensionär
- **Gångarter**: Varje häst har en risk för galopptendens som påverkas av träning och mentalitet

### Träning

Du väljer *träningsprogram* varje vecka per häst. Varje program kostar tid och pengar, och förbättrar specifika egenskaper:

- **Intervallträning** → Snabbhet + Uthållighet (hög belastning, ökad skaderisk)
- **Långdistans** → Uthållighet + Kondition (låg skaderisk)
- **Startträning** → Startförmåga (kräver startbil-investering i anläggningen)
- **Spurtträning** → Spurtstyrka (medelhög belastning)
- **Mentalträning** → Mentalitet, sänker galopptendens
- **Vila** → Återhämtning, sänker skaderisk
- **Simträning** → Kondition utan belastning (kräver poolutbyggnad)
- **Promenad** → Minimal förbättring, minimal stress

*Avancerat*: Du kan schemalägga dag-för-dag träning om du vill min/maxa (premium-känsla utan pay-to-win).

### Hovvård & Skoning

- Varje 4:e vecka behöver hästar omskoning
- Val av skor påverkar grepp, vikt, och prestation: **Normalsko**, **Lättsko**, **Broddar** (vintertrav), **Barfota** (lägre vikt men sämre grepp)
- Hovslagare har kvalitetsnivåer — bättre hovslagare = bättre resultat

### Foder & Vikt

- Du sätter foderplan: Hö-andel, Kraftfoder, Tillskott, Morötter
- Överutfodring → övervikt → långsammare
- Underutfodring → tappar kondition och mentalitet
- Speciella tillskott: Elektrolyter (bra vid varmt väder), Ledtillskott (förebygger skador)

### Veterinär

- Regelbundna hälsokontroller (varannan vecka) kostar pengar men avslöjar dolda skador
- Akuta skador: Senbågsflammation, Hovspricka, Ryggproblem — kräver rehabilitering (veckor utan lopp)
- Du väljer veterinärkvalitet (Bil/Medel/Dyr) — bättre vet = snabbare diagnos

---

## Loppmekanik

### Anmälan

- Lopp har klasser/kategorier: V75-klass, Silverdivisionen, Gulddivisionen, Elitlopp, Unglopp (3–5 åring)
- Varje lopp har: Distans (1640m, 2140m, 2640m etc), Startmetod (volt/auto), Underlag, Handikapp
- Du anmäler häst + väljer kusk + taktik

### Taktik (före lopp)

Du ger kusken instruktioner:

- **Positionering**: Ledtaktik (rusa ut), Andraläge (sitta bakom ledaren), Tredjespår (chansa utanför), Död (lugnt bakifrån, spurt)
- **Tempoprofil**: Offensiv (gå hårt från start) / Balanserad / Försiktig (spara kraft)
- **Spurtorder**: Tidigt angrepp (500m kvar) / Normalt (300m) / Sent (200m)
- **Galopphantering**: Säkerhet (kusken håller tillbaka om galopprisken ökar) / Normal / Riskfylld

### Loppsimulering

- Simuleras baserat på hästens egenskaper + kuskens skicklighet + taktik + slumpfaktor
- **Live-viewer**: Textbaserad med positionsuppdateringar var 200m (likt Hattrick men för trav):
  *"500m kvar: BLIANSEN (3) leder med en längd. EXPRESSEN (7) kör tredje utifrån. DALERO (1) galopperar vid ingången till sista kurvan!"*
- **Galoppering**: Realistiskt — hästar med hög galopptendens + hög belastning = risk. Kuskens skicklighet minskar risken.
- **Diskvalifikation**: Möjlig vid galoppregler (precis som i verkligheten)

### Resultatanalys (efter lopp)

- Kilometerrapport: Tid per 500m-sektion
- Energikurva: Hur hästen hanterade sin uthållighet
- Kuskbetyg: Hur väl kusken följde taktiken
- "Vad-om"-replay: Kör simuleringsmotorn 20 gånger med samma setup (premium)

---

## Ekonomisystem

### Inkomster

- **Prispengarna** — Topp 5 i varje lopp ger pengar (1:a tar ~40%, 2:a ~20%, etc)
- **Sponsorer** — Nivån beror på stallets rykte och resultat. Sponsorkontrakt förhandlas varje säsong.
- **Hästförsäljning** — Sälj hästar på transfermarknaden eller via auktion
- **Avelsverksamhet** — Sälj betäckningstjänster (om du har en framgångsrik avelshingst)
- **Pressmeddelanden** — Skriv veckovis pressmeddelande för extra sponsorpengar + fan-engagemang
- **Stallvisning** — Öppna stallet för publik (event, ger inkomst + popularitet)
- **Login streak-bonus** — Daglig inloggning ger liten bonus (ökat fan-intresse)

### Utgifter

- **Löner**: Kuskar (kontrakt), tränarpersonal, veterinär, hovslagare
- **Stallhyra/underhåll**: Boxhyra per häst, anläggningsuppgradering
- **Träning**: Varje träningspass kostar
- **Foder**: Veckovis foderkostnad per häst
- **Startavgifter**: Anmälningsavgift per lopp
- **Transfer/auktion**: Köp av nya hästar
- **Skoning**: Var 4:e vecka per häst
- **Vet**: Regelbundna kontroller + akutvård

### Balansering

Ekonomin är tajt i början — du måste prioritera. Har du råd att träna alla hästar hårt, eller vilar du några? Ska du satsa på en dyr kusk för finalen, eller spara pengarna till ett nytt föl?

---

## Kusk-systemet

### Anställda kuskar

- Kuskar har egenskaper: **Startskicklighet**, **Taktisk förmåga**, **Spurttiming**, **Galopphantering**, **Erfarenhet**
- Kuskar utvecklas genom att köra lopp
- Du kan ha 1–3 kuskar anställda + hyra in gästkuskar per lopp
- Kuskkontraktsförhandling varje 16 veckor
- Starkuskar kostar mer men ger bättre prestanda

### Gästkuskar

- Hyr in en starkusk för enstaka storlopp (dyrare per gång men ingen kontraktskostnad)
- Tillgänglighet varierar — populära kuskar kan vara uppbokade av andra managers

---

## Uppfödning & Avel

### Betäckningssäsong (spelets "vår")

- Välj sto + hingst
- Hingstens betäckningsavgift sätts av ägaren
- Genetik: Fölets egenskaper baseras på föräldrarnas stats + slump + dolda genetiska faktorer
- **Blodlinjer**: Vissa kombinationer ger bonusar ("nick-effekt")
- Dräktighetstid: 11 spelveckor

### Unghästutveckling

- Föl → Unghäst (1 år = ~16 spelveckor)
- Under unghästperioden: Grundträning, mentalt tålamod, hantering
- Vid 3 års ålder (speltid): Tävlingsdebut i unglopp
- Scouting avslöjar potential gradvis

### Avelsstrategi

- Framgångsrika hästar kan pensioneras till avel
- Avelshingstregister (spelare sätter pris)
- Stambokssystem med statistik per avkomma
- Mål: Skapa den perfekta blodslinjen över generationer (långsiktig hook)

---

## Facilitet & Anläggning

### Stallet (uppgraderingsbart)

| Byggnad | Effekt | Kostnad |
|---------|--------|---------|
| **Grundstall** (start) | 4 boxar | Ingår |
| **Utbyggda boxar** | +2 per nivå (max 16) | Ökande |
| **Träningsbana** | Bättre träningseffekt | Medel |
| **Startmaskin** | Möjliggör startträning | Hög |
| **Simpool** | Simträning (skonsam kondition) | Hög |
| **Veterinärklinik** | Snabbare rehab, billigare vet | Mycket hög |
| **Smedja** | Billigare skoning, bättre kvalitet | Medel |
| **Hästtransport** | Tillgång till fler banor | Medel |
| **Avelsanläggning** | Möjliggör uppfödning | Hög |
| **Fanbotik** | Extra inkomst genom merchandise | Låg |

### Anläggningsstrategi

Du kan inte bygga allt direkt — prioritering krävs. Investerar du i simpool för bättre rehabilitering, eller bygger du fler boxar för att ha fler hästar?

---

## Social & Multiplayer

### Stallförbund (Federationer)

- Gå med i eller starta ett stallförbund
- Gemensamma mål och tävlingar
- Intern transfermarknad
- Forum/chat per förbund

### V75-tippning (meta-spel)

- Varje lördag körs V75 med hästar från ALLA spelare
- Spelare tippar vilka hästar som vinner — precis som riktiga V75
- Vinster baserat på svårighetsgrad (inspirerat av verkliga travspelet)
- Tippningstävlingar mellan stallförbund

### Transfermarknad

- Öppen auktionsmarknad (Hattrick-stil)
- "Claiming"-system: I vissa lopp kan du "claima" en häst som tävlat (betala fast pris)
- Direktaffärer mellan managers (förhandling)
- Leasing: Hyr ut/hyr in hästar för en säsong

### Kommunikation

- Pressmeddelanden (synliga för alla, ger PR-poäng)
- Trash talk inför storlopp (socialt drag)
- Manager-till-manager meddelanden
- Förbundsforum

---

## Progressionssystem

### Divisioner

- **Div 6** (start) → Div 5 → Div 4 → Div 3 → Div 2 → **Div 1 (Eliten)**
- Uppflyttning baserat på säsongspoäng (prispengar + loppvinster)
- Varje division har 8–12 stall som tävlar på samma banor
- Toppdivisionen ger tillgång till: Elitloppet, Kriteriet, Hugo Åbergs Memorial

### Achievements

- **Första vinsten** — Vinn ditt första lopp
- **Uppfödarmästare** — Vinn med en egenuppfödd häst
- **Ekonomisk stabilitet** — Ha positiv budget 10 veckor i rad
- **Kuskflörtare** — Anlita 10 olika gästkuskar
- **Galoppfri säsong** — Kör en hel säsong utan galopperingar
- **V75-kung** — Vinn V75-tippningen 3 gånger
- **Blodlinjearkitekt** — Föd upp 3 generationer av vinnare
- **Stallets ansikte** — Skriv 50 pressmeddelanden
- **Alla distanser** — Vinn på 1640m, 2140m och 2640m
- **Veteranstall** — Spela aktivt i 1 år

### Säsongsstruktur

- 1 säsong = 16 spelveckor
- Varje säsong: Liga-tävling + Cupsystem + Finaler
- Mellan säsonger: Avelssäsong, transferfönster, stalluppgradering
- Årsavslutning: Hästgala med priser (Årets Häst, Årets Uppfödare, etc)

---

## Dagliga Mikrobeslut (det som gör spelet "kladdigt")

Här är nyckeln — det ska alltid finnas *något* att göra:

1. **Morgon**: Kolla hästhälsa (notifikation om någon är halt/orolig)
2. **Träningsjustering**: Byt träning om en häst visar tecken på överbelastning
3. **Foderoptimering**: En häst har gått upp — sänk kraftfodret
4. **Transferbevakning**: Notis om en häst du bevakat går ut på auktion
5. **Sponsorerbjudande**: Nytt sponsoravtal att ta ställning till
6. **Kuskscout**: En ny lovande kusk finns tillgänglig
7. **Väderkoll**: Lördag blir regnigt — byt skor på din häst
8. **Pressmeddelande**: Skriv om dina framgångar (eller bortförklara dina förluster)
9. **Stallvisning**: Arrangera öppet hus (kräver planering, ger inkomst)
10. **Unglopp**: Ditt nyaste föl kan göra kvaltidsstest — vill du riskera det?

---

## Tech Stack — Rekommendation

### Frontend
- **React (Next.js)** — SSR för SEO, App Router
- **Tailwind CSS** — Snabb styling, mobile-first
- **React Native** (eller PWA) — Mobilapp
- **Framer Motion** — Animationer för loppvisaren

### Backend
- **Node.js (NestJS)** eller **Python (FastAPI)** — API-server
- **PostgreSQL** — Huvuddatabas (relationer: hästar, stall, lopp, transaktioner)
- **Redis** — Caching, realtidssessioner, leaderboards
- **Bull/BullMQ** — Jobbkö för loppsimulering, träningsberäkningar

### Loppmotor
- **Separat mikrotjänst** (Python rekommenderat för simuleringen)
- Deterministisk med seed — samma input = samma resultat (för replay/verifiering)
- Beräknar: positioner var 100m, energiförbrukning, galopprisker, kuskbeslut
- Output: Komplett loppdata (JSON) som frontend renderar som live-feed

### Realtid
- **WebSockets (Socket.io)** — Live loppvisare, liveuppdateringar
- **Server-Sent Events** — Notifikationer, auktionsuppdateringar

### Infrastruktur
- **Docker + Kubernetes** — Containerisering
- **AWS/Hetzner** — Hosting (Hetzner för kostnadseffektivitet i tidigt skede)
- **CloudFlare** — CDN + DDoS-skydd
- **GitHub Actions** — CI/CD

### Datamodell (kärna)

```
Stable (stall)
├── horses[] (hästar)
│   ├── attributes (snabbhet, uthållighet etc)
│   ├── health_status
│   ├── training_schedule
│   ├── feed_plan
│   ├── shoe_config
│   └── pedigree (blodlinje)
├── drivers[] (kuskar)
│   ├── skills
│   └── contract
├── staff[] (personal)
│   ├── vet, farrier, trainer
│   └── quality_level
├── facilities (anläggning)
│   └── buildings[]
├── finances
│   ├── balance
│   ├── income_sources[]
│   └── expenses[]
└── achievements[]

Race (lopp)
├── entries[] (anmälda hästar + taktik)
├── conditions (distans, underlag, väder)
├── simulation_result
│   ├── positions_over_time[]
│   ├── sector_times[]
│   ├── incidents[] (galopperingar, etc)
│   └── prize_distribution
└── division / competition

Transfer Market
├── auctions[]
├── claims[]
├── leases[]
└── direct_deals[]

Breeding
├── stallion_registry[]
├── mating_pairs[]
├── pregnancies[]
└── foal_development[]
```

---

## MVP-plan (Fas 1 — 3 månader)

**Mål**: Spelbar kärna med 50 beta-testare

1. ✅ Stall med 4 hästar (fördefinierade)
2. ✅ Grundträning (3 träningstyper)
3. ✅ Loppmotor (grundversion, text-simulering)
4. ✅ 1 loppdag/vecka
5. ✅ Enkel ekonomi (inkomst från lopp, utgift för träning/foder)
6. ✅ Transfermarknad (grundversion)
7. ✅ Divisioner (3 nivåer)
8. ✅ Mobilanpassad webgränssnitt

**Fas 2** (3–6 mån): Avel, kusk-systemet, V75-tippning, achievements
**Fas 3** (6–12 mån): Stallförbund, live-viewer, premium-features, mobilapp

---

## Monetarisering (ej pay-to-win)

Precis som Hattrick — aldrig betala för fördel:

- **TravManager Supporter** (månadsprenumeration): Extra statistik, detaljerad loppanalys, fler scouting-rapporter, kosmetik (stalldrakter, kuskfärger)
- **"Vad-om" Replay**: Kör simuleringsmotorn 20x för ett lopp (som Hattrick Gears)
- **Kosmetik**: Stallemblem, unika kuskdräkter, namnbelysning
- **Extra anläggningsdesign**: Ren kosmetik — hur ditt stall ser ut

---

## Unik hook vs. alla andra hästspel

| Existerande spel | Deras fokus | Vår differentiering |
|---|---|---|
| iHorse Racing | 3D-grafik, casual mobile | Vi: Djup strategi, PvP, community |
| HarnessNation | Multiplayer standardbred | Vi: Skandinavisk trav, V75-metagame |
| Horse Racing Manager (Steam) | Singleplayer, galopp | Vi: Multiplayer, realtid, travspecifikt |
| Sulky Manager | 3D sulky | Vi: Browser-based, community-first |

**Vår nisch**: Det enda seriösa, community-drivna, browser-baserade travmanagerspelet med skandinavisk travkultur, V75-tippning, och Hattrick-djup.

---

## Sammanfattning

TravManager tar det bästa från Hattrick (långsiktig strategi, community, fair play) och kombinerar det med den rika världen av travsporten. Dagliga mikrobeslut (foder, hälsa, träning) håller spelare engagerade mellan loppdagarna, medan avel och generationsspel ger den långsiktiga hooken. V75-tippningen skapar ett unikt meta-game som inget annat managerspel har.

Målgrupp: Travintresserade 25–55 år, skandinavisk marknad initialt, med expansion till Frankrike (världens största travmarknad) och USA (standardbred).
