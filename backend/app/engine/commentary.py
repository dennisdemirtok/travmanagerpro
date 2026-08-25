"""TravManager — CommentaryEngine

Översätter motorns händelser och positionsdata till levande svensk
loppkommentar. Ersätter den gamla torra loppberättelsen
("Tae Kwon Deo (3) leder i 1.13-fart").

Principer:
- Minst fyra formuleringar per händelsetyp, slumpade på loppets seed
  så samma lopp alltid låter likadant.
- Spelarens hästar nämns ungefär dubbelt så ofta som NPC-hästar.
- Dramaturgi: öppning → mittfas → sista kurvan → upplopp (var 100:e meter)
  → mållinjen → sammanfattning med vändpunkt.
- Kommentaren är tidsstämplad i meter så att uppspelningen kan synka
  raderna mot hästarnas position i banan.
"""
import random

# ── Faser ───────────────────────────────────────────────────────────
PHASE_OPENING = "opening"
PHASE_MIDDLE = "middle"
PHASE_CURVE = "curve"
PHASE_STRETCH = "stretch"
PHASE_FINISH = "finish"
PHASE_SUMMARY = "summary"

PHASE_LABELS = {
    PHASE_OPENING: "Öppning",
    PHASE_MIDDLE: "Mittfas",
    PHASE_CURVE: "Sista kurvan",
    PHASE_STRETCH: "Upploppet",
    PHASE_FINISH: "Mållinjen",
    PHASE_SUMMARY: "Efter loppet",
}


# ── Formuleringsbanker ──────────────────────────────────────────────
OPENING_LINES = [
    "{field} hästar på startlinjen över {dist} meter på {track}.",
    "Då är det dags — {dist} meter på {track}, {field} ekipage i fältet.",
    "{track}, {dist} meter. {field} hästar, och stämningen stiger.",
    "Startbilen rullar på {track}. {dist} meter framför fältet på {field} hästar.",
]

OPENING_VOLT = [
    "Voltstart — allt handlar om att komma iväg rent.",
    "Voltstart, och det är alltid en nervös historia.",
    "Voltstart: den som slarvar här får jobba hela vägen.",
    "Voltstart. Håll ögonen på galoppriskerna direkt.",
]

OPENING_AUTO = [
    "Autostart — bilen drar undan och fältet är samlat.",
    "Autostart, jämna förutsättningar för alla.",
    "Bilen släpper och det blir full fart direkt.",
    "Autostart: nu gäller det att hitta rätt position tidigt.",
]

LEADER_LINES = [
    "{horse} har tagit ledningen och håller {kmt}.",
    "Det är {horse} som styr fältet — {kmt} i tempot.",
    "{horse} leder, och farten ligger på {kmt}.",
    "Täten tillhör {horse}, som drar på i {kmt}.",
]

LEADER_HARD = [
    "{horse} drar upp tempot — {kmt} och ingen vill följa!",
    "{horse} skruvar åt: {kmt}. Det här blir tufft för fältet.",
    "Här går det undan — {horse} pressar på i {kmt}.",
    "{horse} bjuder rejält, {kmt}, och fältet töjs ut.",
]

LEADER_SLOW = [
    "{horse} håller igen — bara {kmt}. Det blir en spurtaffär.",
    "Lugnt tempo i täten, {horse} kryper fram i {kmt}.",
    "{horse} sparar krut, {kmt}. Alla är med.",
    "Ingen vill trycka på — {horse} leder i beskedliga {kmt}.",
]

TUCKED_LINES = [
    "{horse} har hittat ryggen på ledaren och åker snålskjuts.",
    "{horse} ligger perfekt i rygg och sparar krafter.",
    "{horse} sitter skyddad i andra och väntar ut det.",
    "{horse} har smugit sig in i rygg — smart körning.",
]

OUTSIDE_LINES = [
    "{horse} kör i dödens utvändigt — det kostar.",
    "{horse} tvingas gå utvändigt utan skydd.",
    "{horse} ligger i dödens och betalar för varje meter.",
    "Ingen rygg för {horse}, som får kämpa utanför.",
]

BOXED_LINES = [
    "{horse} sitter FAST i {rank}:e inner... hittar den en lucka?!",
    "{horse} är instängd — behöver att det öppnar sig snart.",
    "{horse} har hästar runt om sig och kommer ingenstans.",
    "Trångt för {horse}, som väntar på en lucka som inte kommer.",
]

GAP_FOUND_LINES = [
    "NU släpper det! {horse} ut i banan — vilken acceleration!",
    "Där kom luckan — {horse} tar den direkt!",
    "{horse} hittar öppningen och skjuter fart!",
    "Luckan öppnar sig och {horse} är blixtsnabb genom den!",
]

GALLOP_MINOR_LINES = [
    "{horse} hoppar till men fångar upp det snabbt.",
    "Ett litet felsteg av {horse} — kusken räddar situationen.",
    "{horse} tappar takten ett ögonblick, men är på gång igen.",
    "Där skar sig {horse} lite grann. Snyggt fångat av kusken.",
]

GALLOP_MAJOR_LINES = [
    "{horse} galopperar! Massor av mark förlorad.",
    "Nej! {horse} går upp i galopp och tappar hela positionen.",
    "{horse} tappar balansen totalt — det där kostar loppet.",
    "Galopp för {horse}! Kusken får kämpa för att få ner den.",
]

GALLOP_DQ_LINES = [
    "{horse} bryter — det blir diskvalifikation.",
    "Slutet för {horse}, som galopperar bort alla chanser.",
    "{horse} kommer aldrig ner i takt igen. Diskad.",
    "Där gick det illa för {horse} — diskvalificerad.",
]

HIDDEN_GEAR_LINES = [
    "{horse} hittar en växel ingen visste fanns!",
    "Vad är det här? {horse} lägger in en extra växel!",
    "{horse} accelererar på ett sätt vi inte sett tidigare!",
    "Plötsligt ökar {horse} — den hade mer kvar!",
]

INSTINCT_LINES = [
    "{horse} vaknar till liv när målet kommer i sikte!",
    "Tävlingsinstinkten slår till — {horse} rycker!",
    "{horse} känner vittring på seger och sätter in en spurt!",
    "Nu tänder {horse} till — den vill verkligen ha det här!",
]

TACTICAL_LINES = [
    "Kusken på {horse} tar ett initiativ — smart drag.",
    "{horse} flyttas fram av en kusk som ser något ingen annan ser.",
    "Där kommer ett taktiskt drag från {horse}s kusk.",
    "{horse} styrs ut i rätt ögonblick — erfarenhet syns.",
]

FADING_LINES = [
    "{horse} börjar ta slut — energin är nere på {energy}.",
    "Krafterna sinar för {horse}, bara {energy} kvar i tanken.",
    "{horse} går tomt. {energy} energi återstår.",
    "Det tar emot för {horse} nu — {energy} kvar.",
]

CLOSING_LINES = [
    "{horse} kommer med fart bakifrån!",
    "{horse} avancerar snabbt i fältet!",
    "Håll ögonen på {horse} — den äter sig framåt!",
    "{horse} sätter in en attack utifrån!",
]

STRETCH_TIGHT = [
    "{first} och {second} sida vid sida — det här avgörs på målfoto!",
    "Omöjligt att skilja {first} och {second} åt!",
    "{first} håller undan, men {second} är där hela tiden!",
    "Nacke mot nacke mellan {first} och {second}!",
]

STRETCH_CLEAR = [
    "{horse} har ryckt ifrån och ser ohotad ut!",
    "{horse} går undan — det här är avgjort!",
    "Ingen når {horse}, som drar iväg mot mål!",
    "{horse} har öppnat en lucka som ingen täpper till!",
]

REMAINING_LINES = [
    "{m} kvar.",
    "{m} meter till mål.",
    "Ner till {m} kvar.",
    "{m} meter återstår.",
]

WIN_LINES = [
    "{horse} vinner {race}!",
    "Segern går till {horse} i {race}!",
    "{horse} först över mållinjen i {race}!",
    "Det blir {horse} som tar hem {race}!",
]


def format_km_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    rest = seconds % 60
    whole = int(rest)
    tenths = int(round((rest - whole) * 10))
    if tenths == 10:
        whole += 1
        tenths = 0
    return f"{minutes}.{whole:02d},{tenths}"


# Motorns interna fart är inte m/s, så km-tider kan inte räknas rakt av.
# Vi ankrar i stället mot vinnarens FAKTISKA km-tid och skalar med
# fartförhållandet, så siffrorna alltid hamnar i ett trovärdigt travspann.
KM_TIME_MIN = 62.0   # 1.02,0
KM_TIME_MAX = 95.0   # 1.35,0


class CommentaryEngine:
    """Bygger en tidsstämplad kommentarsström för ett kört lopp."""

    def __init__(self, *, distance, snapshots, events, finishers, disqualified,
                 player_horse_ids=None, race_name="", track_name="", start_method="auto",
                 seed=0, winner_km_time=None):
        self.distance = max(1, int(distance))
        self.snapshots = snapshots or []
        self.events = events or []
        self.finishers = finishers or []
        self.disqualified = disqualified or []
        self.player_ids = set(player_horse_ids or [])
        self.race_name = race_name
        self.track_name = track_name or "banan"
        self.start_method = start_method
        self.rng = random.Random(seed or 1)
        self.lines: list[dict] = []
        self._used_texts: set[str] = set()

        # Referens för km-tider: vinnarens verkliga tid och fältets medelfart
        self.ref_km_time = float(winner_km_time) if winner_km_time else 74.0
        leader_speeds = []
        total = len(self.snapshots)
        lo, hi = int(total * 0.2), max(1, int(total * 0.8))
        for snap in self.snapshots[lo:hi] or self.snapshots:
            ranked = self._ranked(snap)
            if ranked:
                sp = self._speed(ranked[0])
                if sp > 0:
                    leader_speeds.append(sp)
        self.ref_speed = (sum(leader_speeds) / len(leader_speeds)) if leader_speeds else 1.0
        self._leader_speeds = sorted(leader_speeds)

    def tempo_pool(self, speed: float):
        """Hårt/lugnt/neutralt tempo relativt loppets egen fart."""
        if self.ref_speed <= 0.01:
            return LEADER_LINES
        ratio = speed / self.ref_speed
        if ratio >= 1.04:
            return LEADER_HARD
        if ratio <= 0.96:
            return LEADER_SLOW
        return LEADER_LINES

    def km_time(self, speed: float) -> str:
        """Km-tid vid given fart, skalad mot vinnarens verkliga tid."""
        if speed <= 0.01 or self.ref_speed <= 0.01:
            return format_km_time(self.ref_km_time)
        scaled = self.ref_km_time * (self.ref_speed / speed)
        return format_km_time(max(KM_TIME_MIN, min(KM_TIME_MAX, scaled)))

    # ── Hjälpare ────────────────────────────────────────────────
    def _pick(self, pool: list[str]) -> str:
        """Slumpa formulering, undvik att upprepa samma två gånger."""
        candidates = [p for p in pool if p not in self._used_texts] or list(pool)
        choice = self.rng.choice(candidates)
        self._used_texts.add(choice)
        if len(self._used_texts) > 24:
            self._used_texts.clear()
        return choice

    def _add(self, d: int, phase: str, text: str, horse_id=None, tone="neutral"):
        self.lines.append({
            "d": int(max(0, min(self.distance, d))),
            "phase": phase,
            "text": text,
            "horse_id": horse_id,
            "tone": "player" if horse_id in self.player_ids else tone,
        })

    def _snap_at(self, meters: float):
        """Närmaste snapshot vid eller före angiven distans."""
        if not self.snapshots:
            return None
        best = self.snapshots[0]
        for snap in self.snapshots:
            if self._snap_d(snap) <= meters:
                best = snap
            else:
                break
        return best

    @staticmethod
    def _snap_d(snap):
        return snap.distance if hasattr(snap, "distance") else snap.get("d", 0)

    @staticmethod
    def _snap_p(snap):
        return snap.positions if hasattr(snap, "positions") else snap.get("p", [])

    @staticmethod
    def _field(p, *names, default=None):
        for n in names:
            if hasattr(p, n):
                return getattr(p, n)
            if isinstance(p, dict) and n in p:
                return p[n]
        return default

    def _ranked(self, snap):
        pos = [p for p in self._snap_p(snap)
               if not self._field(p, "is_disqualified", "dq", default=False)]
        return sorted(pos, key=lambda p: self._field(p, "rank", "r", default=99))

    def _name(self, p):
        return self._field(p, "horse_name", "n", default="Hästen")

    def _hid(self, p):
        return self._field(p, "horse_id", "id")

    def _pos_m(self, p):
        return float(self._field(p, "position_meters", "pos", default=0) or 0)

    def _energy(self, p):
        return float(self._field(p, "energy", "e", default=100) or 0)

    def _speed(self, p):
        return float(self._field(p, "speed", "spd", default=0) or 0)

    def _is_player(self, p):
        return self._hid(p) in self.player_ids

    def _prefer_player(self, ranked, limit=6):
        """Välj en häst att kommentera — spelarens hästar väger dubbelt."""
        pool = []
        for p in ranked[:limit]:
            pool.append(p)
            if self._is_player(p):
                pool.append(p)  # dubbel vikt
        return self.rng.choice(pool) if pool else None

    # ── Faser ───────────────────────────────────────────────────
    def _opening(self):
        first = self.snapshots[0] if self.snapshots else None
        field_size = len(self._snap_p(first)) if first else len(self.finishers)
        self._add(0, PHASE_OPENING, self._pick(OPENING_LINES).format(
            field=field_size, dist=self.distance, track=self.track_name))
        self._add(0, PHASE_OPENING, self._pick(
            OPENING_VOLT if str(self.start_method).lower().endswith("volt") else OPENING_AUTO))

        mark = int(self.distance * 0.12)
        snap = self._snap_at(mark)
        if not snap:
            return
        ranked = self._ranked(snap)
        if not ranked:
            return
        leader = ranked[0]
        kmt = self.km_time(self._speed(leader))
        self._add(mark, PHASE_OPENING, self._pick(LEADER_LINES).format(
            horse=self._name(leader), kmt=kmt), self._hid(leader))

        if len(ranked) > 1:
            second = ranked[1]
            gap = self._pos_m(leader) - self._pos_m(second)
            pool = TUCKED_LINES if gap < 6 else OUTSIDE_LINES
            self._add(mark, PHASE_OPENING, self._pick(pool).format(
                horse=self._name(second)), self._hid(second))

    def _middle(self):
        for frac in (0.35, 0.5):
            mark = int(self.distance * frac)
            snap = self._snap_at(mark)
            if not snap:
                continue
            ranked = self._ranked(snap)
            if not ranked:
                continue
            leader = ranked[0]
            speed = self._speed(leader)
            kmt = self.km_time(speed)
            pool = self.tempo_pool(speed)
            self._add(mark, PHASE_MIDDLE, self._pick(pool).format(
                horse=self._name(leader), kmt=kmt), self._hid(leader))

            subject = self._prefer_player(ranked[1:], limit=6)
            if subject is not None:
                boxed = self._field(subject, "boxed_in", default=False)
                rank = self._field(subject, "rank", "r", default=2)
                if boxed:
                    self._add(mark, PHASE_MIDDLE, self._pick(BOXED_LINES).format(
                        horse=self._name(subject), rank=rank), self._hid(subject), "drama")
                elif self._energy(subject) < 35:
                    self._add(mark, PHASE_MIDDLE, self._pick(FADING_LINES).format(
                        horse=self._name(subject), energy=int(self._energy(subject))),
                        self._hid(subject))
                else:
                    self._add(mark, PHASE_MIDDLE, self._pick(TUCKED_LINES).format(
                        horse=self._name(subject)), self._hid(subject))

    def _curve(self):
        mark = int(self.distance * 0.72)
        snap = self._snap_at(mark)
        if not snap:
            return
        ranked = self._ranked(snap)
        if not ranked:
            return
        leader = ranked[0]
        remaining = self.distance - mark
        self._add(mark, PHASE_CURVE, self._pick(REMAINING_LINES).format(m=remaining))

        if self._energy(leader) < 40:
            self._add(mark, PHASE_CURVE, self._pick(FADING_LINES).format(
                horse=self._name(leader), energy=int(self._energy(leader))),
                self._hid(leader), "drama")

        # Vem avancerar? Jämför mot läget i mittfasen.
        earlier = self._snap_at(int(self.distance * 0.5))
        if earlier:
            before = {self._hid(p): self._field(p, "rank", "r", default=99)
                      for p in self._ranked(earlier)}
            movers = [
                p for p in ranked[1:8]
                if before.get(self._hid(p), 99) - self._field(p, "rank", "r", default=99) >= 2
            ]
            if movers:
                mover = self._prefer_player(movers, limit=len(movers))
                self._add(mark, PHASE_CURVE, self._pick(CLOSING_LINES).format(
                    horse=self._name(mover)), self._hid(mover), "drama")

    def _stretch(self):
        start = int(self.distance * 0.82)
        marks = list(range(start, self.distance, 100)) or [start]
        for mark in marks:
            snap = self._snap_at(mark)
            if not snap:
                continue
            ranked = self._ranked(snap)
            if len(ranked) < 2:
                continue
            first, second = ranked[0], ranked[1]
            gap = self._pos_m(first) - self._pos_m(second)
            remaining = self.distance - mark

            self._add(mark, PHASE_STRETCH, self._pick(REMAINING_LINES).format(m=remaining))
            if gap < 3:
                self._add(mark, PHASE_STRETCH, self._pick(STRETCH_TIGHT).format(
                    first=self._name(first), second=self._name(second)),
                    self._hid(first), "drama")
            elif gap > 12:
                self._add(mark, PHASE_STRETCH, self._pick(STRETCH_CLEAR).format(
                    horse=self._name(first)), self._hid(first))
            else:
                # Bara hästar BAKOM ledaren kan "komma bakifrån"
                chasers = ranked[1:5]
                if chasers:
                    subject = self._prefer_player(chasers, limit=len(chasers))
                    self._add(mark, PHASE_STRETCH, self._pick(CLOSING_LINES).format(
                        horse=self._name(subject)), self._hid(subject), "drama")

    def _weave_events(self):
        """Väv in motorns händelser på rätt distans."""
        pools = {
            "gallop_minor": GALLOP_MINOR_LINES,
            "gallop_major": GALLOP_MAJOR_LINES,
            "gallop_dq": GALLOP_DQ_LINES,
            "hidden_gear": HIDDEN_GEAR_LINES,
            "instinct_surge": INSTINCT_LINES,
            "driver_tactical_move": TACTICAL_LINES,
        }
        for ev in self.events:
            etype = ev.event_type if hasattr(ev, "event_type") else ev.get("type")
            pool = pools.get(etype)
            if not pool:
                continue
            d = ev.distance if hasattr(ev, "distance") else ev.get("distance", 0)
            name = ev.horse_name if hasattr(ev, "horse_name") else ev.get("horse", "Hästen")
            hid = ev.horse_id if hasattr(ev, "horse_id") else ev.get("horse_id")
            frac = d / self.distance
            phase = (PHASE_OPENING if frac < 0.15 else PHASE_MIDDLE if frac < 0.55
                     else PHASE_CURVE if frac < 0.82 else PHASE_STRETCH)
            tone = "drama" if etype.startswith("gallop") else "neutral"
            self._add(d, phase, self._pick(pool).format(horse=name), hid, tone)

    def _finish_and_summary(self):
        if not self.finishers:
            return
        winner = self.finishers[0]
        w_name = self._field(winner, "horse_name", "horse_name", default="Vinnaren")
        w_id = self._field(winner, "horse_id")
        w_time = self._field(winner, "km_time_display", "km_time", default="")

        self._add(self.distance, PHASE_FINISH, self._pick(WIN_LINES).format(
            horse=w_name, race=self.race_name or "loppet"), w_id, "drama")
        if w_time:
            self._add(self.distance, PHASE_FINISH,
                      f"Vinnartid {w_time} över {self.distance} meter.", w_id)

        # Sammanfattning
        top = self.finishers[:3]
        if len(top) >= 3:
            names = ", ".join(self._field(f, "horse_name", default="?") for f in top)
            self._add(self.distance, PHASE_SUMMARY, f"Trippeln: {names}.")

        for f in self.finishers:
            if self._field(f, "horse_id") in self.player_ids:
                pos = self._field(f, "finish_position", default=0)
                nm = self._field(f, "horse_name", default="Din häst")
                if pos == 1:
                    self._add(self.distance, PHASE_SUMMARY, f"{nm} vann — en perfekt dag.",
                              self._field(f, "horse_id"))
                elif pos <= 3:
                    self._add(self.distance, PHASE_SUMMARY,
                              f"{nm} till pallplats som {pos}:a.", self._field(f, "horse_id"))
                else:
                    self._add(self.distance, PHASE_SUMMARY,
                              f"{nm} slutade {pos}:a.", self._field(f, "horse_id"))
                break

        turning = self._turning_point()
        if turning:
            self._add(self.distance, PHASE_SUMMARY, f"Vändpunkten: {turning}")

    def _turning_point(self) -> str:
        """Den händelse som avgjorde loppet."""
        priority = ["gallop_dq", "gallop_major", "instinct_surge", "hidden_gear",
                    "driver_tactical_move", "gallop_minor"]
        best = None
        best_rank = len(priority)
        for ev in self.events:
            etype = ev.event_type if hasattr(ev, "event_type") else ev.get("type")
            if etype in priority:
                r = priority.index(etype)
                if r < best_rank:
                    best_rank, best = r, ev
        if best is None:
            # Ingen dramatisk händelse — avgjordes på upploppet
            if len(self.finishers) >= 2:
                w = self._field(self.finishers[0], "horse_name", default="vinnaren")
                s = self._field(self.finishers[1], "horse_name", default="tvåan")
                return f"{w} höll undan för {s} i en rak uppgörelse på upploppet."
            return ""
        name = best.horse_name if hasattr(best, "horse_name") else best.get("horse", "hästen")
        d = best.distance if hasattr(best, "distance") else best.get("distance", 0)
        etype = best.event_type if hasattr(best, "event_type") else best.get("type")
        described = {
            "gallop_dq": f"{name} galopperade bort loppet vid {d} meter.",
            "gallop_major": f"{name}s galopp vid {d} meter kostade hela positionen.",
            "instinct_surge": f"{name}s ryck vid {d} meter avgjorde.",
            "hidden_gear": f"{name} hittade en extra växel vid {d} meter.",
            "driver_tactical_move": f"Kuskens drag med {name} vid {d} meter blev avgörande.",
            "gallop_minor": f"{name}s felsteg vid {d} meter bröt rytmen.",
        }
        return described.get(etype, "")

    # ── Publikt API ─────────────────────────────────────────────
    def build(self) -> list[dict]:
        self._opening()
        self._middle()
        self._curve()
        self._stretch()
        self._weave_events()
        self._finish_and_summary()

        phase_order = {
            PHASE_OPENING: 0, PHASE_MIDDLE: 1, PHASE_CURVE: 2,
            PHASE_STRETCH: 3, PHASE_FINISH: 4, PHASE_SUMMARY: 5,
        }
        self.lines.sort(key=lambda l: (l["d"], phase_order.get(l["phase"], 9)))
        return self.lines


def build_commentary(**kwargs) -> list[dict]:
    return CommentaryEngine(**kwargs).build()
