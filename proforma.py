"""FIN 43900 Lab 09: ABG five-year, three-statement pro-forma.

Python 3.9+; standard library only. USD millions except value per share.
Inputs reproduce the instructor's training case, not independently sourced
current investment research. AI assistance: OpenAI Codex; see Lab9/README.md.

Run: python proforma.py
Required refusal demonstration: python proforma.py --break-cash
Inventory-financing demonstration: python proforma.py --no-floor-plan
"""

import argparse
import math
import sys


SOURCE = (
    "https://github.com/cinderzhang/fin43900-fall2026/"
    "blob/6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f/"
    "lessons/week-05/lab-09-proforma-build.md"
)
YEARS = tuple(range(2026, 2031))
TOLERANCE = 1e-6  # USD millions: $1, far below displayed precision.

# Opening FY2025 balances and revenue, supplied by the Lab 09 instruction.
OPENING = {
    "revenue": 17999.0,
    "inventory": 2135.8,
    "ppe": 3070.4,
    "other_assets": 6371.6,
    "cash": 40.4,
    "floor_plan": 2027.0,
    "debt": 3572.0,
    "other_liabilities": 2127.5,
    "equity": 3891.7,
    "revolver": 0.0,
}

# Label and reason for every input appear in Lab9/README.md.
ASSUMPTIONS = {
    "growth": 0.018,                              # Judgment
    "gross_margin": 0.1705,                      # Judgment
    "sga_ratios": (0.665, 0.655, 0.645, 0.645, 0.645),  # Judgment
    "depreciation_ratio": 82.4 / 3070.4,          # History; do not round
    "impairment": 120.0,                         # Judgment; non-cash
    "capex": 250.0,                              # Guidance; extrapolated
    "tax_rate": 0.255,                           # Judgment
    "inventory_days": 2135.8 / (17999.0 - 3071.7) * 365,  # History
    "floor_plan_ratio": 2027.0 / 2135.8,          # History; do not round
    "other_wc_ratio": 0.008,                     # Judgment
    "minimum_cash": 25.0,                        # History, per lab
    "revolver_limit": 850.0,                     # Judgment, per lab
    "revolver_rate": 0.06,                       # Judgment
    "repayment": 150.0,                          # Judgment
    "buyback": 150.0,                            # Judgment
    "floor_plan_rate": 0.0467,                   # History
    "debt_rate": 0.0544,                         # History
    "cost_of_equity": 0.10,                      # Judgment
    "terminal_growth": 0.025,                    # Judgment
    "shares": 17.951349,                         # Fact, per assigned 10-Q
}


def balance_gap(row):
    """Recompute the accounting identity from components, never cached totals."""
    assets = row["cash"] + row["inventory"] + row["ppe"] + row["other_assets"]
    liabilities = (
        row["floor_plan"] + row["debt"] + row["revolver"]
        + row["other_liabilities"]
    )
    return assets - liabilities - row["equity"]


def validate_inputs(opening, assumptions):
    """Fail clearly on invalid inputs instead of generating a plausible price."""
    for name, value in opening.items():
        if not math.isfinite(value):
            raise ValueError(f"Opening {name} must be finite.")
    for name, value in assumptions.items():
        values = value if name == "sga_ratios" else (value,)
        if not all(math.isfinite(item) for item in values):
            raise ValueError(f"Assumption {name} must be finite.")
    if len(assumptions["sga_ratios"]) != len(YEARS):
        raise ValueError("Supply one SG&A ratio for each of the five years.")
    if assumptions["growth"] <= -1:
        raise ValueError("Revenue growth must be greater than -100%.")
    if not 0 <= assumptions["gross_margin"] <= 1:
        raise ValueError("Gross margin must lie between 0 and 1.")
    if not 0 <= assumptions["tax_rate"] <= 1:
        raise ValueError("Tax rate must lie between 0 and 1.")
    for name in (
        "depreciation_ratio", "impairment", "capex", "inventory_days",
        "floor_plan_ratio", "other_wc_ratio", "minimum_cash", "revolver_limit",
        "revolver_rate", "repayment", "buyback", "floor_plan_rate", "debt_rate",
    ):
        if assumptions[name] < 0:
            raise ValueError(f"{name} cannot be negative.")
    if any(ratio < 0 for ratio in assumptions["sga_ratios"]):
        raise ValueError("SG&A ratios cannot be negative.")
    if assumptions["shares"] <= 0:
        raise ValueError("Shares outstanding must be positive.")
    r, g = assumptions["cost_of_equity"], assumptions["terminal_growth"]
    if not -1 < g < r or r <= -1:
        raise ValueError("Require -100% < terminal growth < cost of equity.")
    gap = balance_gap(opening)
    if abs(gap) > TOLERANCE:
        raise ValueError(f"FY2025 opening balance sheet gap = {gap:+.6f}.")
    for name in ("inventory", "ppe", "other_assets", "floor_plan", "debt", "revolver"):
        if opening[name] < 0:
            raise ValueError(f"Opening {name} cannot be negative.")
    if not 0 <= opening["revolver"] <= assumptions["revolver_limit"]:
        raise ValueError("Opening revolver exceeds its facility limit.")


def project(opening=None, assumptions=None):
    """Link each year's income, non-cash balances, FCFE, then cash financing."""
    opening = dict(OPENING if opening is None else opening)
    a = dict(ASSUMPTIONS if assumptions is None else assumptions)
    validate_inputs(opening, a)
    previous = opening
    rows = []
    for index, year in enumerate(YEARS):
        row = {"year": year, "opening_cash": previous["cash"]}
        # 1. Income statement: all interest uses OPENING loan balances.
        row["revenue"] = previous["revenue"] * (1 + a["growth"])
        row["gross_profit"] = row["revenue"] * a["gross_margin"]
        row["cost_of_sales"] = row["revenue"] - row["gross_profit"]
        row["sga"] = row["gross_profit"] * a["sga_ratios"][index]
        row["depreciation"] = previous["ppe"] * a["depreciation_ratio"]
        row["impairment"] = a["impairment"]
        row["operating_income"] = (
            row["gross_profit"] - row["sga"]
            - row["depreciation"] - row["impairment"]
        )
        row["interest"] = (
            previous["floor_plan"] * a["floor_plan_rate"]
            + previous["debt"] * a["debt_rate"]
            + previous["revolver"] * a["revolver_rate"]
        )
        row["pretax"] = row["operating_income"] - row["interest"]
        row["tax"] = max(0.0, row["pretax"]) * a["tax_rate"]
        row["net_income"] = row["pretax"] - row["tax"]

        # 2. Balance sheet except cash; no asset or equity plug.
        row["inventory"] = row["cost_of_sales"] * a["inventory_days"] / 365
        row["floor_plan"] = row["inventory"] * a["floor_plan_ratio"]
        row["capex"] = a["capex"]
        row["ppe"] = previous["ppe"] + row["capex"] - row["depreciation"]
        row["change_other_wc"] = a["other_wc_ratio"] * (row["revenue"] - previous["revenue"])
        row["other_assets"] = previous["other_assets"] + row["change_other_wc"] - row["impairment"]
        # A loan cannot be repaid below zero; base case pays the full 150 yearly.
        row["repayment"] = min(a["repayment"], previous["debt"])
        row["debt"] = previous["debt"] - row["repayment"]
        row["other_liabilities"] = previous["other_liabilities"]
        row["buyback"] = a["buyback"]
        row["equity"] = previous["equity"] + row["net_income"] - row["buyback"]

        # 3. Owner cash flow before buybacks and the liquidity revolver.
        row["change_inventory"] = row["inventory"] - previous["inventory"]
        row["change_floor_plan"] = row["floor_plan"] - previous["floor_plan"]
        row["fcfe"] = (
            row["net_income"] + row["depreciation"] + row["impairment"]
            - row["capex"] - row["change_inventory"] - row["change_other_wc"]
            + row["change_floor_plan"] - row["repayment"]
        )
        before_revolver = previous["cash"] + row["fcfe"] - row["buyback"]
        if before_revolver < a["minimum_cash"]:
            revolver_change = min(
                a["minimum_cash"] - before_revolver,
                a["revolver_limit"] - previous["revolver"],
            )
        else:
            revolver_change = -min(
                before_revolver - a["minimum_cash"], previous["revolver"]
            )
        row["change_revolver"] = revolver_change
        row["revolver"] = previous["revolver"] + revolver_change
        row["change_cash"] = row["fcfe"] - row["buyback"] + revolver_change
        row["cf_closing_cash"] = previous["cash"] + row["change_cash"]
        row["cash"] = row["cf_closing_cash"]
        # The checks use the calculated balances; rounding is for display only.
        rows.append(row)
        previous = row
    return rows


def assert_balanced(rows, assumptions=None):
    """Enforce accounting, cash linkage, cash floor and financing capacity."""
    a = ASSUMPTIONS if assumptions is None else assumptions
    if [row["year"] for row in rows] != list(YEARS):
        raise ValueError("Require all five forecast years, FY2026E through FY2030E.")
    for row in rows:
        year = f"FY{row['year']}E"
        if not all(math.isfinite(value) for value in row.values()):
            raise ValueError(f"{year}: non-finite statement value; valuation refused.")
        gap = balance_gap(row)
        if abs(gap) > TOLERANCE:
            raise ValueError(
                f"{year}: assets - liabilities - equity gap = {gap:+.1f} "
                "USD million; valuation refused."
            )
        cash_gap = row["cash"] - row["cf_closing_cash"]
        if abs(cash_gap) > TOLERANCE:
            raise ValueError(f"{year}: balance-sheet / cash-flow cash gap = {cash_gap:+.1f}; valuation refused.")
        floor_gap = row["cash"] - a["minimum_cash"]
        if floor_gap < -TOLERANCE:
            raise ValueError(
                f"{year}: cash-floor gap = {floor_gap:+.1f} USD million "
                f"(cash {row['cash']:.1f}, minimum {a['minimum_cash']:.1f}); valuation refused."
            )
        if not -TOLERANCE <= row["revolver"] <= a["revolver_limit"] + TOLERANCE:
            raise ValueError(f"{year}: revolver outside 0 to {a['revolver_limit']:.1f}; valuation refused.")
        for name in ("inventory", "ppe", "other_assets", "floor_plan", "debt"):
            if row[name] < -TOLERANCE:
                raise ValueError(f"{year}: negative {name}; valuation refused.")


def value_equity(rows, assumptions=None):
    """Value FCFE directly; do not subtract debt a second time."""
    a = ASSUMPTIONS if assumptions is None else assumptions
    assert_balanced(rows, a)  # Mandatory gate, even when called outside main().
    r, g, shares = a["cost_of_equity"], a["terminal_growth"], a["shares"]
    if not all(math.isfinite(number) for number in (r, g, shares)):
        raise ValueError("Valuation inputs must be finite.")
    if not -1 < g < r or shares <= 0:
        raise ValueError("Require -100% < terminal growth < cost of equity and positive shares.")
    present_values = [row["fcfe"] / (1 + r) ** t for t, row in enumerate(rows, 1)]
    # Scheduled repayment ends after 2030, exactly as required by the lab.
    terminal_cash_flow = (rows[-1]["fcfe"] + rows[-1]["repayment"]) * (1 + g)
    if terminal_cash_flow <= 0:
        raise ValueError("Nonpositive terminal FCFE requires a different terminal model.")
    terminal_value = terminal_cash_flow / (r - g)
    pv_terminal = terminal_value / (1 + r) ** len(rows)
    pv_explicit = sum(present_values)
    equity_value = pv_explicit + pv_terminal
    if equity_value <= 0:
        raise ValueError("Nonpositive equity value; terminal-value share is not meaningful.")
    return {
        "pv_explicit": pv_explicit,
        "terminal_cash_flow": terminal_cash_flow,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "equity_value": equity_value,
        "terminal_share": pv_terminal / equity_value,
        "value_per_share": equity_value / shares,
    }


def print_table(title, rows, lines):
    print(f"\n{title} (USD millions)")
    print(f"{'Line':<39}" + "".join(f"{('FY' + str(row['year']) + 'E'):>13}" for row in rows))
    print("-" * (39 + 13 * len(rows)))
    for label, value in lines:
        numbers = [value(row) if callable(value) else row[value] for row in rows]
        print(f"{label:<39}" + "".join(f"{(0.0 if abs(n) < TOLERANCE else n):>13,.1f}" for n in numbers))


def print_statements(rows, a):
    print_table("INCOME STATEMENT", rows, [
        ("Revenue", "revenue"), ("Cost of sales", "cost_of_sales"),
        ("Gross profit", "gross_profit"), ("SG&A", "sga"),
        ("Depreciation", "depreciation"), ("Impairment (non-cash)", "impairment"),
        ("Operating income", "operating_income"), ("Interest expense", "interest"),
        ("Pretax income", "pretax"), ("Tax expense", "tax"), ("Net income", "net_income"),
    ])
    print_table("BALANCE SHEET", rows, [
        ("Cash", "cash"), ("Inventory", "inventory"), ("PP&E", "ppe"),
        ("Other assets", "other_assets"),
        ("Total assets", lambda y: y["cash"] + y["inventory"] + y["ppe"] + y["other_assets"]),
        ("Floor plan inventory loans", "floor_plan"), ("Term debt", "debt"),
        ("Revolver", "revolver"), ("Other liabilities", "other_liabilities"),
        ("Equity", "equity"),
        ("Total liabilities and equity", lambda y: y["floor_plan"] + y["debt"] + y["revolver"] + y["other_liabilities"] + y["equity"]),
    ])
    print_table("CASH FLOW / FCFE BRIDGE", rows, [
        ("Net income", "net_income"), ("+ Depreciation", "depreciation"),
        ("+ Impairment", "impairment"), ("- Capital spending", lambda y: -y["capex"]),
        ("- Change in inventory", lambda y: -y["change_inventory"]),
        ("- Change in other working capital", lambda y: -y["change_other_wc"]),
        ("+ Change in floor plan", "change_floor_plan"),
        ("- Term debt repayment", lambda y: -y["repayment"]),
        ("Free cash flow to equity", "fcfe"), ("- Buyback", lambda y: -y["buyback"]),
        ("+ Revolver draw / (-) repayment", "change_revolver"),
        ("Change in cash", "change_cash"), ("Opening cash", "opening_cash"),
        ("Closing cash from cash flow", "cf_closing_cash"),
    ])
    print_table("CHECKS BEFORE VALUATION", rows, [
        ("Assets - liabilities - equity", balance_gap),
        ("Balance-sheet cash - cash-flow cash", lambda y: y["cash"] - y["cf_closing_cash"]),
        (f"Cash above minimum of {a['minimum_cash']:.1f}", lambda y: y["cash"] - a["minimum_cash"]),
        ("Revolver capacity remaining", lambda y: a["revolver_limit"] - y["revolver"]),
    ])
    for row in rows:
        failures = []
        if abs(balance_gap(row)) > TOLERANCE:
            failures.append("balance")
        if abs(row["cash"] - row["cf_closing_cash"]) > TOLERANCE:
            failures.append("cash linkage")
        if row["cash"] < a["minimum_cash"] - TOLERANCE:
            failures.append("cash floor")
        print(f"FY{row['year']}E: " + ("FAIL: " + ", ".join(failures) if failures else "PASS"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    demos = parser.add_mutually_exclusive_group()
    demos.add_argument("--break-cash", action="store_true", help="Set FY2026E cash to 40.4; must refuse valuation.")
    demos.add_argument("--no-floor-plan", action="store_true", help="Remove projected floor-plan funding; must fail cash floor.")
    args = parser.parse_args()
    a = dict(ASSUMPTIONS)
    if args.no_floor_plan:
        a["floor_plan_ratio"] = 0.0
    print("FIN 43900 LAB 09 - ASBURY AUTOMOTIVE GROUP (ABG)")
    print("Assigned FY2025 opening data; forecasts FY2026E-FY2030E. Teaching case.")
    print("Full precision internally; USD millions; fixed shares: 17.951349 million.")
    print("Source: " + SOURCE)
    try:
        rows = project(assumptions=a)
        if args.break_cash:
            rows[0]["cash"] = OPENING["cash"]
            print("DELIBERATE BREAK: FY2026E balance-sheet cash overwritten with 40.4.")
        if args.no_floor_plan:
            print("DELIBERATE BREAK: floor-plan funding removed; opening loans still repaid.")
        print_statements(rows, a)
        result = value_equity(rows, a)
    except ValueError as error:
        print(f"\nERROR: {error}")
        return 1
    print("\nVALUATION - all five years passed assert_balanced")
    print(f"Cost of equity: {a['cost_of_equity']:.2%}; terminal growth: {a['terminal_growth']:.2%}")
    for label, key in [
        ("PV of 2026-2030 FCFE", "pv_explicit"), ("2031 terminal FCFE", "terminal_cash_flow"),
        ("Terminal value at end-2030", "terminal_value"), ("PV of terminal value", "pv_terminal"),
        ("Equity value", "equity_value"),
    ]:
        print(f"{label}: ${result[key]:,.2f} million")
    print(f"Share of value after 2030: {result['terminal_share']:.2%}")
    print(f"Value per share: ${result['value_per_share']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
