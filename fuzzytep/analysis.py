from datetime import datetime

from .profiles import INDUSTRY_PROFILES, PROFILE_LABELS


def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, value))


def triangular(value, left, center, right):
    if value <= left or value >= right:
        return 0.0
    if value == center:
        return 1.0
    if value < center:
        return (value - left) / (center - left)
    return (right - value) / (right - center)


def trapezoidal(value, a, b, c, d):
    if value <= a or value >= d:
        return 0.0
    if b <= value <= c:
        return 1.0
    if value < b:
        return (value - a) / (b - a)
    return (d - value) / (d - c)


def fuzzy_or(*values):
    return max(values)


def fuzzy_and(*values):
    return min(values)


def normalize_enterprise_payload(payload):
    name = str(payload.get("name", "")).strip()
    profile_code = str(payload.get("profile_code", "default")).strip() or "default"
    ownership = str(payload.get("ownership", "")).strip()
    description = str(payload.get("description", "")).strip()

    if not name:
        raise ValueError("Укажите название предприятия.")
    if profile_code not in INDUSTRY_PROFILES:
        raise ValueError("Выберите корректный профиль оценки.")
    if not ownership:
        raise ValueError("Укажите форму собственности.")
    if not description:
        raise ValueError("Добавьте краткое описание предприятия.")

    return {
        "name": name[:120],
        "industry": str(payload.get("industry", "")).strip()[:120] or PROFILE_LABELS[profile_code],
        "profile_code": profile_code,
        "ownership": ownership[:120],
        "description": description[:800],
    }


def normalize_indicator_payload(payload):
    period = str(payload.get("period", "")).strip() or datetime.now().strftime("%Y-%m")
    revenue = float(payload.get("revenue"))
    profit = float(payload.get("profit"))
    costs_raw = payload.get("costs")
    profitability_raw = payload.get("profitability")
    revenue_growth = float(payload.get("revenue_growth", 0) or 0)
    liquidity_ratio = float(payload.get("liquidity_ratio", 1.2) or 1.2)

    if revenue <= 0:
        raise ValueError("Выручка должна быть больше нуля.")
    if profit >= revenue:
        raise ValueError("Для этой модели прибыль должна быть меньше выручки, чтобы затраты можно было рассчитать автоматически.")

    costs = revenue - profit if costs_raw in ("", None) else float(costs_raw)
    if costs <= 0:
        raise ValueError("Затраты должны быть больше нуля.")
    if liquidity_ratio <= 0:
        raise ValueError("Коэффициент текущей ликвидности должен быть больше нуля.")
    if revenue_growth < -100:
        raise ValueError("Темп роста выручки не может быть меньше -100%.")

    profitability = round((profit / costs) * 100, 2) if profitability_raw in ("", None) else float(profitability_raw)

    return {
        "period": period[:30],
        "revenue": round(revenue, 2),
        "profit": round(profit, 2),
        "costs": round(costs, 2),
        "profitability": round(profitability, 2),
        "revenue_growth": round(revenue_growth, 2),
        "liquidity_ratio": round(liquidity_ratio, 2),
    }


def dominant_label(values):
    return max(values.items(), key=lambda item: item[1])[0]


def score_to_efficiency(score):
    if score < 35:
        return "low", "низкая"
    if score < 60:
        return "satisfactory", "удовлетворительная"
    if score < 80:
        return "good", "хорошая"
    return "high", "высокая"


def resolve_industry_profile(industry_name):
    industry = (industry_name or "").lower()
    if any(token in industry for token in ("маш", "производ", "завод", "пром", "industrial", "manufact")):
        return "manufacturing", INDUSTRY_PROFILES["manufacturing"]
    if any(token in industry for token in ("торг", "ритейл", "магаз", "опт", "розн", "trade", "retail")):
        return "trade", INDUSTRY_PROFILES["trade"]
    if any(token in industry for token in ("услуг", "сервис", "консалт", "it", "айти", "service")):
        return "services", INDUSTRY_PROFILES["services"]
    return "default", INDUSTRY_PROFILES["default"]


def resolve_enterprise_profile(enterprise=None):
    explicit_code = str((enterprise or {}).get("profile_code", "")).strip()
    if explicit_code in INDUSTRY_PROFILES:
        return explicit_code, INDUSTRY_PROFILES[explicit_code]
    return resolve_industry_profile((enterprise or {}).get("industry", ""))


def strength_to_impact(strength):
    if strength >= 0.7:
        return "сильное"
    if strength >= 0.35:
        return "заметное"
    return "умеренное"


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def rule_action_hint(rule_text):
    premise = (rule_text or "").lower()
    if "затрат" in premise:
        return "Проверьте, какие статьи затрат сильнее всего давят на результат."
    if "ликвидност" in premise:
        return "Посмотрите, хватает ли денежного запаса и оборотных средств на короткий период."
    if "рост" in premise:
        return "Разберите причины слабого роста или проверьте, не ухудшается ли качество роста."
    if "маржа прибыли" in premise or "прибыльност" in premise or "рентабельност" in premise:
        return "Имеет смысл проверить маржинальность по направлениям и качество прибыли."
    return "Используйте это как ориентир для следующей управленческой проверки."


def build_rule_insight(rule):
    if rule["label"] == "low":
        meaning = "Это сочетание показателей тянет оценку вниз и указывает на риск снижения устойчивости."
    elif rule["label"] == "satisfactory":
        meaning = "Это сочетание показывает пограничное состояние: бизнес работает, но запас прочности ограничен."
    elif rule["label"] == "good":
        meaning = "Это сочетание поддерживает устойчивую работу и помогает удерживать хороший уровень."
    else:
        meaning = "Это сочетание заметно усиливает итог и говорит о сильном состоянии бизнеса."

    return {
        "name": rule["name"],
        "premise": rule["text"],
        "strength": round(rule["strength"], 3),
        "label": rule["label"],
        "impact": strength_to_impact(rule["strength"]),
        "meaning": meaning,
        "action_hint": rule_action_hint(rule["text"]),
    }


def build_business_takeaways(memberships, efficiency_label):
    dominant = {key: dominant_label(values) for key, values in memberships.items()}
    strengths = []
    risks = []
    actions = []

    if dominant["profit_margin"] == "high":
        strengths.append("Маржа прибыли дает хороший запас по доходности.")
    elif dominant["profit_margin"] == "low":
        risks.append("Маржа прибыли низкая, поэтому запас прочности по прибыли ограничен.")
        actions.append("Проверьте маржу по продуктам, ценам и скидкам.")
    if dominant["cost_ratio"] == "low":
        strengths.append("Доля затрат выглядит управляемой и не съедает большую часть выручки.")
    elif dominant["cost_ratio"] == "high":
        risks.append("Доля затрат слишком высокая и заметно давит на итоговую оценку.")
        actions.append("Разберите структуру затрат и найдите статьи с наибольшим давлением.")
    if dominant["profitability"] == "high":
        strengths.append("Рентабельность показывает, что выручка превращается в прибыль на хорошем уровне.")
    elif dominant["profitability"] == "low":
        risks.append("Рентабельность низкая, поэтому результат бизнеса окупается слабо.")
        actions.append("Проверьте, где теряется прибыльность: в цене, объеме или расходах.")
    if dominant["coverage"] == "high":
        strengths.append("Выручка уверенно покрывает затраты и поддерживает операционную устойчивость.")
    elif dominant["coverage"] == "low":
        risks.append("Покрытие затрат слабое, поэтому выручки недостаточно для комфортной работы.")
        actions.append("Сравните темп роста выручки и затрат, чтобы понять источник просадки.")
    if dominant["growth"] == "high":
        strengths.append("Темп роста выручки поддерживает развитие бизнеса.")
    elif dominant["growth"] == "low":
        risks.append("Рост выручки слабый, поэтому запас для развития ограничен.")
        actions.append("Разберите причины замедления роста выручки и точки восстановления спроса.")
    if dominant["liquidity"] == "high":
        strengths.append("Ликвидность дает запас для работы без лишнего финансового напряжения.")
    elif dominant["liquidity"] == "low":
        risks.append("Ликвидность слабая, поэтому компании может не хватать финансовой подушки.")
        actions.append("Проверьте денежный запас, дебиторку и краткосрочные обязательства.")

    strengths = dedupe(strengths)[:3]
    risks = dedupe(risks)[:3]
    actions = dedupe(actions)[:3]

    if not strengths:
        fallback_strength = "Критичных перекосов по ключевым показателям сейчас не видно." if efficiency_label in ("хорошая", "высокая") else "У предприятия есть рабочая база, но она пока не дает сильного преимущества."
        strengths.append(fallback_strength)
    if not risks:
        fallback_risk = "Явно проблемных зон сейчас не видно, но важно не потерять дисциплину по затратам и ликвидности." if efficiency_label == "высокая" else "Сильных провалов нет, но часть показателей находится близко к пограничным значениям."
        risks.append(fallback_risk)
    if not actions:
        if efficiency_label in ("хорошая", "высокая"):
            actions.append("Сохраняйте текущую финансовую дисциплину и сравнивайте динамику по периодам.")
        elif efficiency_label == "удовлетворительная":
            actions.append("Сначала проверьте показатели, которые ближе всего к зоне риска, и зафиксируйте план улучшений.")
        else:
            actions.append("Начните с показателей, которые давят на устойчивость сильнее всего, и отдельно проверьте платежную способность.")

    if efficiency_label == "низкая":
        main_takeaway = "Сейчас у предприятия выраженные признаки слабой устойчивости. Без корректирующих действий результат может ухудшаться дальше."
    elif efficiency_label == "удовлетворительная":
        main_takeaway = "Предприятие работает приемлемо, но запас устойчивости ограничен. Один-два слабых показателя уже заметно тянут оценку вниз."
    elif efficiency_label == "хорошая":
        main_takeaway = "Предприятие выглядит устойчивым, но итог все еще зависит от нескольких чувствительных зон, которые важно контролировать."
    else:
        main_takeaway = "Предприятие показывает сильное и устойчивое состояние. Ключевые показатели сейчас поддерживают хороший запас прочности."

    return {
        "dominant_zones": dominant,
        "strengths": strengths,
        "risks": risks,
        "actions": actions,
        "main_takeaway": main_takeaway,
    }


def calculate_memberships(metrics, profile):
    return {
        "profit_margin": {
            "low": round(trapezoidal(metrics["profit_margin"], *profile["profit_margin"]["low"]), 3),
            "medium": round(triangular(metrics["profit_margin"], *profile["profit_margin"]["medium"]), 3),
            "high": round(trapezoidal(metrics["profit_margin"], *profile["profit_margin"]["high"]), 3),
        },
        "cost_ratio": {
            "low": round(trapezoidal(metrics["cost_ratio"], *profile["cost_ratio"]["low"]), 3),
            "medium": round(triangular(metrics["cost_ratio"], *profile["cost_ratio"]["medium"]), 3),
            "high": round(trapezoidal(metrics["cost_ratio"], *profile["cost_ratio"]["high"]), 3),
        },
        "profitability": {
            "low": round(trapezoidal(metrics["profitability"], *profile["profitability"]["low"]), 3),
            "medium": round(triangular(metrics["profitability"], *profile["profitability"]["medium"]), 3),
            "high": round(trapezoidal(metrics["profitability"], *profile["profitability"]["high"]), 3),
        },
        "coverage": {
            "low": round(trapezoidal(metrics["coverage_ratio"], *profile["coverage"]["low"]), 3),
            "medium": round(triangular(metrics["coverage_ratio"], *profile["coverage"]["medium"]), 3),
            "high": round(trapezoidal(metrics["coverage_ratio"], *profile["coverage"]["high"]), 3),
        },
        "growth": {
            "low": round(trapezoidal(metrics["revenue_growth"], *profile["growth"]["low"]), 3),
            "medium": round(triangular(metrics["revenue_growth"], *profile["growth"]["medium"]), 3),
            "high": round(trapezoidal(metrics["revenue_growth"], *profile["growth"]["high"]), 3),
        },
        "liquidity": {
            "low": round(trapezoidal(metrics["liquidity_ratio"], *profile["liquidity"]["low"]), 3),
            "medium": round(triangular(metrics["liquidity_ratio"], *profile["liquidity"]["medium"]), 3),
            "high": round(trapezoidal(metrics["liquidity_ratio"], *profile["liquidity"]["high"]), 3),
        },
    }


def build_rules(memberships):
    pm = memberships["profit_margin"]
    cr = memberships["cost_ratio"]
    pr = memberships["profitability"]
    cv = memberships["coverage"]
    gr = memberships["growth"]
    liq = memberships["liquidity"]
    return [
        {"name": "Лидерская эффективность", "text": "маржа прибыли высокая, рентабельность высокая, покрытие затрат высокое и ликвидность не ниже средней", "strength": fuzzy_and(pm["high"], pr["high"], cv["high"], fuzzy_or(liq["medium"], liq["high"])), "label": "high"},
        {"name": "Высокая прибыль при контролируемых затратах", "text": "маржа прибыли высокая, доля затрат низкая и ликвидность высокая", "strength": fuzzy_and(pm["high"], cr["low"], liq["high"]), "label": "high"},
        {"name": "Сильный рост без потери устойчивости", "text": "темп роста высокий, рентабельность высокая и ликвидность не проседает", "strength": fuzzy_and(gr["high"], pr["high"], fuzzy_or(liq["medium"], liq["high"])), "label": "high"},
        {"name": "Рост подкреплен хорошим запасом ликвидности", "text": "темп роста высокий и ликвидность высокая", "strength": fuzzy_and(gr["high"], liq["high"]), "label": "high"},
        {"name": "Устойчивая хорошая работа", "text": "маржа прибыли средняя, рентабельность высокая, затраты низкие", "strength": fuzzy_and(pm["medium"], pr["high"], cr["low"]), "label": "good"},
        {"name": "Хорошая экономика предприятия", "text": "маржа прибыли высокая и рентабельность не ниже средней", "strength": fuzzy_and(pm["high"], fuzzy_or(pr["medium"], pr["high"])), "label": "good"},
        {"name": "Сильная операционная устойчивость", "text": "покрытие затрат высокое и ликвидность высокая", "strength": fuzzy_and(cv["high"], liq["high"]), "label": "good"},
        {"name": "Рост поддерживает развитие предприятия", "text": "темп роста средний или высокий, а маржа прибыли не ниже средней", "strength": fuzzy_and(fuzzy_or(gr["medium"], gr["high"]), fuzzy_or(pm["medium"], pm["high"])), "label": "good"},
        {"name": "Сильная рентабельность при хорошей окупаемости", "text": "рентабельность высокая и покрытие затрат высокое", "strength": fuzzy_and(pr["high"], cv["high"]), "label": "good"},
        {"name": "Сбалансированное состояние", "text": "маржа прибыли средняя, затраты средние, рентабельность средняя, ликвидность средняя", "strength": fuzzy_and(pm["medium"], cr["medium"], pr["medium"], liq["medium"]), "label": "satisfactory"},
        {"name": "Приемлемая эффективность при умеренной нагрузке", "text": "покрытие затрат среднее и рентабельность средняя", "strength": fuzzy_and(cv["medium"], pr["medium"]), "label": "satisfactory"},
        {"name": "Граница устойчивости", "text": "маржа прибыли средняя, но темп роста низкий или затраты высокие", "strength": fuzzy_and(pm["medium"], fuzzy_or(gr["low"], cr["high"])), "label": "satisfactory"},
        {"name": "Нормальная прибыльность без роста", "text": "рентабельность средняя, ликвидность средняя, но роста почти нет", "strength": fuzzy_and(pr["medium"], liq["medium"], gr["low"]), "label": "satisfactory"},
        {"name": "Переходное состояние", "text": "показатели распределены между средними и низкими зонами", "strength": fuzzy_and(fuzzy_or(pm["low"], pm["medium"]), fuzzy_or(pr["low"], pr["medium"]), cr["medium"]), "label": "satisfactory"},
        {"name": "Риск снижения эффективности", "text": "рентабельность низкая и покрытие затрат среднее", "strength": fuzzy_and(pr["low"], cv["medium"]), "label": "low"},
        {"name": "Высокая затратность", "text": "затраты высокие и маржа прибыли низкая", "strength": fuzzy_and(cr["high"], pm["low"]), "label": "low"},
        {"name": "Недостаточная окупаемость", "text": "покрытие затрат низкое и рентабельность низкая", "strength": fuzzy_and(cv["low"], pr["low"]), "label": "low"},
        {"name": "Слабая прибыльность", "text": "маржа прибыли низкая и рентабельность низкая", "strength": fuzzy_and(pm["low"], pr["low"]), "label": "low"},
        {"name": "Резерв для роста", "text": "затраты низкие, но прибыльность только средняя", "strength": fuzzy_and(cr["low"], pr["medium"], pm["medium"]), "label": "good"},
        {"name": "Неустойчивая модель расходов", "text": "затраты высокие даже при средней рентабельности", "strength": fuzzy_and(cr["high"], pr["medium"]), "label": "low"},
        {"name": "Скрытая сила предприятия", "text": "покрытие затрат высокое, маржа прибыли средняя и ликвидность не ниже средней", "strength": fuzzy_and(cv["high"], pm["medium"], fuzzy_or(liq["medium"], liq["high"])), "label": "good"},
        {"name": "Снижение спроса и финансовой подушки", "text": "темп роста низкий и ликвидность низкая", "strength": fuzzy_and(gr["low"], liq["low"]), "label": "low"},
        {"name": "Рост есть, но деньги зажаты", "text": "темп роста высокий, но ликвидность низкая", "strength": fuzzy_and(gr["high"], liq["low"]), "label": "satisfactory"},
        {"name": "Финансовая напряженность", "text": "ликвидность низкая и доля затрат высокая", "strength": fuzzy_and(liq["low"], cr["high"]), "label": "low"},
        {"name": "Рост без прибыли не спасает", "text": "темп роста высокий, но маржа прибыли низкая", "strength": fuzzy_and(gr["high"], pm["low"]), "label": "satisfactory"},
        {"name": "Медленный, но устойчивый бизнес", "text": "рост низкий, но ликвидность высокая и покрытие затрат высокое", "strength": fuzzy_and(gr["low"], liq["high"], cv["high"]), "label": "good"},
        {"name": "Нехватка финансового запаса", "text": "ликвидность низкая даже при средней прибыльности", "strength": fuzzy_and(liq["low"], pr["medium"]), "label": "low"},
        {"name": "Растущий, но пока средний уровень", "text": "темп роста средний и прибыльность средняя", "strength": fuzzy_and(gr["medium"], pr["medium"]), "label": "satisfactory"},
    ]


def output_membership(label, score):
    if label == "low":
        return trapezoidal(score, 0, 0, 22, 42)
    if label == "satisfactory":
        return triangular(score, 32, 50, 68)
    if label == "good":
        return triangular(score, 58, 74, 88)
    return trapezoidal(score, 78, 90, 100, 100)


def defuzzify(rules):
    universe = list(range(0, 101))
    aggregated = []
    for score in universe:
        level = 0.0
        for rule in rules:
            level = max(level, min(rule["strength"], output_membership(rule["label"], score)))
        aggregated.append(level)
    area = sum(aggregated)
    if area == 0:
        return 0.0
    return round(sum(score * level for score, level in zip(universe, aggregated)) / area, 1)


def analyse_indicators(payload, enterprise=None):
    indicators = normalize_indicator_payload(payload)
    revenue = indicators["revenue"]
    profit = indicators["profit"]
    costs = indicators["costs"]
    profitability = indicators["profitability"]
    revenue_growth = indicators["revenue_growth"]
    liquidity_ratio = indicators["liquidity_ratio"]

    profit_margin = round((profit / revenue) * 100, 2)
    cost_ratio = round((costs / revenue) * 100, 2)
    coverage_ratio = round(revenue / max(costs, 1), 3)
    industry_key, profile = resolve_enterprise_profile(enterprise)

    metrics = {
        "profit_margin": profit_margin,
        "cost_ratio": cost_ratio,
        "profitability": profitability,
        "coverage_ratio": coverage_ratio,
        "revenue_growth": revenue_growth,
        "liquidity_ratio": liquidity_ratio,
    }
    memberships = calculate_memberships(metrics, profile)
    active_rules = [rule for rule in build_rules(memberships) if rule["strength"] > 0.05]
    final_score = defuzzify(active_rules)

    if final_score == 0.0:
        final_score = round(
            (
                clamp((profit_margin / 30) * 100)
                + clamp(((105 - cost_ratio) / 55) * 100)
                + clamp((profitability / 30) * 100)
                + clamp(((coverage_ratio - 0.95) / 0.55) * 100)
                + clamp(((revenue_growth + 10) / 30) * 100)
                + clamp(((liquidity_ratio - 0.8) / 1.2) * 100)
            )
            / 6,
            1,
        )

    efficiency_code, efficiency_label = score_to_efficiency(final_score)
    takeaways = build_business_takeaways(memberships, efficiency_label)
    top_rules = sorted(active_rules, key=lambda item: item["strength"], reverse=True)[:2]
    reasons = "; ".join(rule["name"].lower() for rule in top_rules) if top_rules else "сработал базовый интегральный расчет без доминирующего правила"
    explanation = (
        f"Система сопоставила шесть показателей между собой: маржу прибыли {profit_margin:.2f}%, "
        f"долю затрат {cost_ratio:.2f}%, рентабельность {profitability:.2f}%, покрытие затрат {coverage_ratio:.2f}, "
        f"темп роста выручки {revenue_growth:.2f}% и текущую ликвидность {liquidity_ratio:.2f}. "
        f"Использован профиль оценки: {PROFILE_LABELS.get(industry_key, industry_key)}. Сильнее всего на итог повлияли: {reasons}. "
        f"Следующий разумный шаг: {takeaways['actions'][0]}"
    )

    return {
        "period": indicators["period"],
        "revenue": revenue,
        "profit": profit,
        "costs": costs,
        "profitability": profitability,
        "revenue_growth": revenue_growth,
        "liquidity_ratio": liquidity_ratio,
        "profit_margin": round(profit_margin, 2),
        "cost_ratio": round(cost_ratio, 2),
        "coverage_ratio": round(coverage_ratio, 3),
        "industry_profile": industry_key,
        "efficiency_code": efficiency_code,
        "efficiency_label": efficiency_label,
        "numeric_score": final_score,
        "comment": f"{takeaways['main_takeaway']} Главный позитивный сигнал: {takeaways['strengths'][0]} Основной риск: {takeaways['risks'][0]}",
        "explanation": explanation,
        "main_takeaway": takeaways["main_takeaway"],
        "strengths": takeaways["strengths"],
        "risks": takeaways["risks"],
        "actions": takeaways["actions"],
        "memberships": memberships,
        "triggered_rules": [build_rule_insight(rule) for rule in sorted(active_rules, key=lambda item: item["strength"], reverse=True)],
    }
