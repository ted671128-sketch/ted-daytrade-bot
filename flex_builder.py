def _row(label: str, value, color: str = "#111111") -> dict:
    return {
        "type": "box",
        "layout": "horizontal",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 2},
            {
                "type": "text", "text": str(value), "size": "sm", "weight": "bold",
                "color": color, "align": "end", "flex": 3,
            },
        ],
    }


def stock_flex(code: str, name: str, close: float, scenario: dict) -> dict:
    rr = scenario.get("risk_reward")
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": f"{code} {name}", "weight": "bold", "size": "xl"},
                {"type": "text", "text": f"參考價 {close}", "size": "sm", "color": "#888888"},
                {"type": "separator", "margin": "md"},
                _row("突破", scenario["breakout"]),
                _row("支撐", scenario["support"]),
                _row("停損", scenario["stop"], "#1B8A3A"),
                _row("目標1", scenario["target1"], "#D32F2F"),
                _row("目標2", scenario["target2"], "#D32F2F"),
                _row("風報比", rr if rr is not None else "-"),
                {"type": "separator", "margin": "md"},
                {
                    "type": "text", "text": "僅為價位試算，非投資建議",
                    "size": "xxs", "color": "#AAAAAA", "wrap": True,
                },
            ],
        },
    }


def plan_carousel(items: list[dict]) -> dict:
    """items: build_plan 的輸出；LINE carousel 最多 12 個 bubble。"""
    bubbles = [
        stock_flex(i["stock"]["code"], i["stock"].get("name", ""),
                   i["stock"]["close"], i["scenario"])
        for i in items[:12]
    ]
    return {"type": "carousel", "contents": bubbles}
