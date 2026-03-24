INDUSTRY_PROFILES = {
    "default": {
        "profit_margin": {"low": (0, 0, 5, 12), "medium": (8, 17, 26), "high": (20, 28, 100, 100)},
        "cost_ratio": {"low": (0, 0, 52, 64), "medium": (60, 74, 86), "high": (82, 92, 180, 180)},
        "profitability": {"low": (0, 0, 6, 12), "medium": (10, 18, 28), "high": (22, 30, 100, 100)},
        "coverage": {"low": (0, 0, 1.02, 1.08), "medium": (1.05, 1.18, 1.34), "high": (1.25, 1.45, 5, 5)},
        "growth": {"low": (-100, -100, 0, 4), "medium": (2, 8, 16), "high": (12, 20, 100, 100)},
        "liquidity": {"low": (0, 0, 0.95, 1.1), "medium": (1.05, 1.35, 1.8), "high": (1.55, 2.0, 6, 6)},
    },
    "manufacturing": {
        "profit_margin": {"low": (0, 0, 4, 10), "medium": (8, 15, 23), "high": (18, 26, 100, 100)},
        "cost_ratio": {"low": (0, 0, 56, 66), "medium": (62, 75, 86), "high": (82, 92, 180, 180)},
        "profitability": {"low": (0, 0, 5, 10), "medium": (8, 16, 24), "high": (20, 28, 100, 100)},
        "coverage": {"low": (0, 0, 1.01, 1.07), "medium": (1.04, 1.16, 1.3), "high": (1.22, 1.4, 5, 5)},
        "growth": {"low": (-100, -100, -1, 3), "medium": (1, 6, 13), "high": (10, 18, 100, 100)},
        "liquidity": {"low": (0, 0, 0.9, 1.05), "medium": (1.0, 1.25, 1.7), "high": (1.45, 1.9, 6, 6)},
    },
    "trade": {
        "profit_margin": {"low": (0, 0, 3, 8), "medium": (5, 11, 18), "high": (14, 22, 100, 100)},
        "cost_ratio": {"low": (0, 0, 46, 58), "medium": (54, 68, 80), "high": (76, 88, 180, 180)},
        "profitability": {"low": (0, 0, 4, 9), "medium": (7, 14, 22), "high": (18, 26, 100, 100)},
        "coverage": {"low": (0, 0, 1.01, 1.05), "medium": (1.03, 1.12, 1.24), "high": (1.18, 1.32, 5, 5)},
        "growth": {"low": (-100, -100, 0, 5), "medium": (3, 9, 18), "high": (14, 22, 100, 100)},
        "liquidity": {"low": (0, 0, 0.85, 1.0), "medium": (0.95, 1.15, 1.45), "high": (1.3, 1.6, 6, 6)},
    },
    "services": {
        "profit_margin": {"low": (0, 0, 6, 14), "medium": (10, 20, 30), "high": (24, 34, 100, 100)},
        "cost_ratio": {"low": (0, 0, 44, 56), "medium": (52, 66, 78), "high": (74, 86, 180, 180)},
        "profitability": {"low": (0, 0, 7, 14), "medium": (10, 20, 32), "high": (26, 36, 100, 100)},
        "coverage": {"low": (0, 0, 1.04, 1.1), "medium": (1.08, 1.22, 1.4), "high": (1.3, 1.5, 5, 5)},
        "growth": {"low": (-100, -100, 1, 6), "medium": (4, 10, 18), "high": (14, 24, 100, 100)},
        "liquidity": {"low": (0, 0, 1.0, 1.15), "medium": (1.1, 1.45, 1.95), "high": (1.7, 2.2, 6, 6)},
    },
}

PROFILE_LABELS = {
    "default": "универсальный",
    "manufacturing": "производство / машиностроение",
    "trade": "торговля",
    "services": "услуги / IT / сервис",
}
