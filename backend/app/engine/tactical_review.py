"""TravManager — Taktiskt facit

Efter loppet får spelaren veta VARFÖR det gick som det gick: varje
taktikval bedöms mot vad som faktiskt hände i banan, med poäng och
förslag på vad som varit bättre.

Bedömningarna speglar motorns egna mekanismer:
- Ledaren betalar ~18 % extra energi i vindmotstånd, rygg får ~15 % rabatt
- Offensiv öppning ger ×1.06 fart men ×1.35 energidränering
- Avvaktande upplägg ger ×1.10 spurt, bakifrån ×1.14 plus dynamisk bonus
  när ledarna är under 25 i energi
- Innerspår är kortast men riskerar instängdhet
"""

GOOD, OK, BAD = "good", "ok", "bad"

POSITION_LABELS = {
    "lead": "Ledning",
    "second": "Rygg (andra)",
    "outside": "Utvändigt",
    "trailing": "Bakom rygg",
    "back": "Bakifrån",
}
TEMPO_LABELS = {
    "offensive": "Offensivt",
    "balanced": "Balanserat",
    "cautious": "Avvaktande",
}
SPRINT_LABELS = {
    "early_600m": "Tidig spurt (600 m)",
    "normal_400m": "Normal spurt (400 m)",
    "late_250m": "Sen spurt (250 m)",
    "auto": "Kuskens val",
}
CURVE_LABELS = {
    "inner": "Innerspår",
    "middle": "Mittspår",
    "outer": "Ytterspår",
}
SAFETY_LABELS = {
    "safe": "Försiktig",
    "normal": "Normal",
    "risky": "Offensiv",
}


def _verdict(points: int) -> str:
    if points >= 2:
        return GOOD
    if points <= -2:
        return BAD
    return OK


def review_entry(facts: dict) -> dict:
    """Bedöm ett ekipages taktikval.

    facts:
      positioning, tempo, sprint_order, curve_strategy, gallop_safety,
      finish_position, field_size, energy_at_finish, gallop_incidents,
      boxed_steps, stretch_class, endurance, sprint_strength, start_ability,
      rank_gained (positiv = avancerade under loppet)
    """
    pos = str(facts.get("positioning", "second"))
    tempo = str(facts.get("tempo", "balanced"))
    sprint = str(facts.get("sprint_order", "normal_400m"))
    curve = str(facts.get("curve_strategy", "middle"))
    safety = str(facts.get("gallop_safety", "normal"))

    place = int(facts.get("finish_position") or 0)
    field = max(1, int(facts.get("field_size") or 10))
    energy = float(facts.get("energy_at_finish") or 0)
    gallops = int(facts.get("gallop_incidents") or 0)
    boxed = int(facts.get("boxed_steps") or 0)
    stretch = str(facts.get("stretch_class", "medium"))
    endurance = int(facts.get("endurance") or 50)
    sprint_str = int(facts.get("sprint_strength") or 50)
    start_ab = int(facts.get("start_ability") or 50)
    rank_gained = int(facts.get("rank_gained") or 0)

    won = place == 1
    top3 = 0 < place <= 3
    items = []

    # ── Position ────────────────────────────────────────────────
    p, comment, optimal = 0, "", ""
    if pos == "lead":
        if energy < 15:
            p, comment = -3, (
                f"Hästen dog i täten — bara {energy:.0f} energi kvar i mål. "
                f"Ledaren betalar 18 % extra i vindmotstånd.")
            optimal = "Rygg (andra) hade sparat krafterna till upploppet."
        elif won or (top3 and energy > 25):
            p, comment = 3, "Ledningen höll hela vägen — hästen orkade försvara den."
        elif endurance < 55:
            p, comment = -2, (
                f"Med {endurance} i uthållighet är ledning en dyr strategi.")
            optimal = "Rygg (andra) — låt någon annan ta vindmotståndet."
        else:
            p, comment = 0, "Ledningen fungerade, men kostade mer än den gav."
    elif pos in ("second", "trailing"):
        if boxed > 4:
            p, comment = -2, (
                "Hästen blev instängd i rygg och kom aldrig loss i tid.")
            optimal = "Utvändigt eller bakifrån hade gett fri väg."
        elif top3:
            p, comment = 3, "Ryggen gav 15 % energirabatt och fri väg när det gällde."
        elif energy > 45:
            p, comment = -1, (
                f"Hästen gick i mål med {energy:.0f} energi kvar — för passivt upplägg.")
            optimal = "Offensivt tempo eller tidigare spurt."
        else:
            p, comment = 1, "Solid rygg, men luckan kom lite för sent."
    elif pos == "outside":
        if won:
            p, comment = 2, "Utvändigt vann trots vindmotståndet — imponerande."
        else:
            p, comment = -2, "Dödens utvändigt kostade energi utan att ge något."
            optimal = "Rygg (andra) om spåret tillåter."
    elif pos == "back":
        if rank_gained >= 3:
            p, comment = 3, f"Bakifrån gav 14 % spurtbonus — avancerade {rank_gained} platser."
        elif energy > 40 and not top3:
            p, comment = -2, (
                f"För mycket kvar i tanken ({energy:.0f}) — spurten kom aldrig igång.")
            optimal = "Rygg (andra) för att komma närmare täten tidigare."
        else:
            p, comment = 1, "Rimligt upplägg, men fältet sprang ifrån."

    items.append(_item("Position", POSITION_LABELS.get(pos, pos), p, comment, optimal))

    # ── Tempo ───────────────────────────────────────────────────
    p, comment, optimal = 0, "", ""
    if tempo == "offensive":
        if energy < 12:
            p, comment = -3, "Offensivt tempo tömde hästen — 35 % högre energidränering."
            optimal = "Balanserat hade räckt hela vägen."
        elif top3:
            p, comment = 3, "Offensivt tempo satte press på fältet och gav utdelning."
        else:
            p, comment = -1, "Offensivt tempo kostade mer än det gav."
    elif tempo == "cautious":
        if energy > 45 and not top3:
            p, comment = -2, "Avvaktande blev för passivt — hästen fick aldrig användning för krafterna."
            optimal = "Balanserat tempo."
        elif top3:
            p, comment = 3, "Avvaktande tempo sparade krut och gav 10 % extra spurt."
        else:
            p, comment = 1, "Avvaktande var säkert men gav ingen fördel."
    else:
        p, comment = (2, "Balanserat tempo passade loppet.") if top3 else \
                     (1, "Balanserat tempo — inga misstag, inga vinster.")

    items.append(_item("Tempo", TEMPO_LABELS.get(tempo, tempo), p, comment, optimal))

    # ── Spurttiming mot upploppslängd ───────────────────────────
    p, comment, optimal = 0, "", ""
    ideal = {"short": "early_600m", "medium": "normal_400m", "long": "late_250m"}
    stretch_text = {"short": "kort", "medium": "normalt", "long": "långt"}[stretch]
    stretch_adj = {"short": "korta", "medium": "normala", "long": "långa"}[stretch]
    if sprint == ideal[stretch]:
        p, comment = 3, f"Spurttimingen matchade det {stretch_adj} upploppet."
    elif sprint == "auto":
        p, comment = 1, "Kusken fick välja — fungerade, men du styr bättre själv."
        optimal = SPRINT_LABELS[ideal[stretch]]
    else:
        p = -2 if not top3 else 0
        comment = f"Upploppet är {stretch_text} — den här timingen låg fel."
        optimal = SPRINT_LABELS[ideal[stretch]]
        if sprint_str >= 70 and stretch == "long":
            comment += " Med hästens spurtstyrka fanns mycket att hämta."

    items.append(_item("Spurttiming", SPRINT_LABELS.get(sprint, sprint), p, comment, optimal))

    # ── Kurvstrategi ────────────────────────────────────────────
    p, comment, optimal = 0, "", ""
    if curve == "inner":
        if boxed > 4:
            p, comment = -3, f"Innerspåret stängde in hästen i {boxed} lägen."
            optimal = "Mittspår ger fri väg till priset av några meter."
        else:
            p, comment = 3, "Innerspåret sparade meter utan att stänga in hästen."
    elif curve == "outer":
        p, comment = (1, "Ytterspåret gav fri väg — men kostade meter.") if top3 else \
                     (-2, "Ytterspåret kostade meter i varje kurva.")
        if not top3:
            optimal = "Mittspår."
    else:
        p, comment = 2, "Mittspåret var en trygg kompromiss."

    items.append(_item("Kurvstrategi", CURVE_LABELS.get(curve, curve), p, comment, optimal))

    # ── Galoppsäkerhet ──────────────────────────────────────────
    p, comment, optimal = 0, "", ""
    if gallops > 0:
        if safety == "risky":
            p, comment = -3, f"Offensiv galoppsäkerhet gav {gallops} galopp."
            optimal = "Försiktig inställning med den här hästen."
        elif safety == "normal":
            p, comment = -1, f"{gallops} galopp — överväg försiktig inställning."
            optimal = "Försiktig."
        else:
            p, comment = 0, f"Trots försiktig körning blev det {gallops} galopp."
    else:
        if safety == "risky":
            p, comment = 3, "Offensiv körning utan ett enda felsteg — full utdelning."
        elif safety == "safe":
            p, comment = 1, "Ren gång, men försiktigheten kostade lite fart."
        else:
            p, comment = 2, "Ren gång hela vägen."

    items.append(_item("Galoppsäkerhet", SAFETY_LABELS.get(safety, safety), p, comment, optimal))

    total = sum(i["points"] for i in items)
    max_points = len(items) * 3
    if total >= 9:
        grade, grade_text = "A", "Nära nog perfekt körning."
    elif total >= 5:
        grade, grade_text = "B", "Bra upplägg med små justeringar kvar."
    elif total >= 0:
        grade, grade_text = "C", "Fungerade, men flera val kan förbättras."
    elif total >= -5:
        grade, grade_text = "D", "Taktiken motarbetade hästen."
    else:
        grade, grade_text = "F", "Fel val rakt igenom — läs facit noga."

    return {
        "items": items,
        "total_points": total,
        "max_points": max_points,
        "grade": grade,
        "grade_text": grade_text,
        "energy_at_finish": round(energy),
        "boxed_steps": boxed,
        "gallop_incidents": gallops,
        "finish_position": place,
        "field_size": field,
    }


def _item(label, value, points, comment, optimal):
    return {
        "label": label,
        "value": value,
        "points": points,
        "verdict": _verdict(points),
        "comment": comment,
        "optimal": optimal or None,
    }
