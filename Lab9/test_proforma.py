"""Independent published-answer fixtures and failure-path checks for Lab 09.

Run from the repository root: python -B -m unittest discover -s Lab9 -v
Only the standard library is used. Tests do not overwrite source or artifacts.
"""

from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import proforma as model


class ProformaTests(unittest.TestCase):
    def setUp(self):
        self.a = deepcopy(model.ASSUMPTIONS)
        self.rows = model.project()

    def test_all_published_lab_endpoint_answers(self):
        # Fixed fixtures transcribed from the lab, not calculated by the model.
        expected = {
            "revenue": ("18323.0", "19678.3"),
            "operating_income": ("844.2", "971.4"),
            "net_income": ("413.6", "527.5"),
            "fcfe": ("211.4", "342.3"),
            "cash": ("101.8", "719.8"),
        }
        for key, endpoints in expected.items():
            for index, target in zip((0, -1), endpoints):
                with self.subTest(line=key, year=self.rows[index]["year"]):
                    self.assertEqual(f"{self.rows[index][key]:.1f}", target)
        result = model.value_equity(self.rows)
        self.assertEqual(f"{result['value_per_share']:.2f}", "291.75")
        self.assertEqual(f"{result['terminal_share']:.1%}", "79.8%")

    def test_intermediate_years_against_tutorial(self):
        for row, fcfe, cash in zip(
            self.rows,
            ("211.4", "255.1", "299.7", "320.9", "342.3"),
            ("101.8", "206.9", "356.6", "527.5", "719.8"),
        ):
            self.assertEqual(f"{row['fcfe']:.1f}", fcfe)
            self.assertEqual(f"{row['cash']:.1f}", cash)

    def test_first_year_with_separate_decimal_arithmetic(self):
        # A separate one-year calculation using exact decimal source inputs.
        sales = D("17999.0") * D("1.018")
        gp = sales * D("0.1705")
        op_income = gp * (1 - D("0.665")) - D("82.4") - D("120")
        interest = D("2027") * D("0.0467") + D("3572") * D("0.0544")
        net_income = (op_income - interest) * D("0.745")
        inventory = (sales - gp) * D("2135.8") / (D("17999") - D("3071.7"))
        floor_plan = inventory * D("2027") / D("2135.8")
        fcfe = (net_income + D("82.4") + D("120") - D("250")
                - (inventory - D("2135.8")) - D("0.008") * (sales - D("17999"))
                + (floor_plan - D("2027")) - D("150"))
        self.assertAlmostEqual(self.rows[0]["fcfe"], float(fcfe), places=8)
        self.assertAlmostEqual(self.rows[0]["cash"], float(D("40.4") + fcfe - D("150")), places=8)

    def test_all_years_balance_link_cash_and_meet_floor(self):
        model.assert_balanced(self.rows)
        for row in self.rows:
            self.assertLess(abs(model.balance_gap(row)), model.TOLERANCE)
            self.assertEqual(row["cash"], row["cf_closing_cash"])
            self.assertGreaterEqual(row["cash"], 25)
            self.assertEqual(row["revolver"], 0)

    def test_required_cash_break_blocks_valuation(self):
        self.rows[0]["cash"] = 40.4
        with self.assertRaisesRegex(ValueError, r"FY2026E.*gap = -61\.4.*valuation refused"):
            model.value_equity(self.rows)

    def test_offsetting_equity_cannot_hide_broken_cash_link(self):
        self.rows[0]["cash"] -= 1
        self.rows[0]["equity"] -= 1
        self.assertAlmostEqual(model.balance_gap(self.rows[0]), 0)
        with self.assertRaisesRegex(ValueError, "cash-flow cash gap"):
            model.value_equity(self.rows)

    def test_no_floor_plan_can_balance_but_is_not_liquid(self):
        self.a["floor_plan_ratio"] = 0
        rows = model.project(assumptions=self.a)
        self.assertAlmostEqual(model.balance_gap(rows[0]), 0)
        self.assertEqual(rows[0]["revolver"], 850)
        self.assertLess(rows[0]["cash"], -1000)
        with self.assertRaisesRegex(ValueError, r"FY2026E.*cash-floor gap"):
            model.value_equity(rows, self.a)

    def test_revolver_draw_then_repay_and_charge_opening_interest(self):
        self.a["sga_ratios"] = (0.75, 0.655, 0.645, 0.645, 0.645)
        rows = model.project(assumptions=self.a)
        model.assert_balanced(rows, self.a)
        self.assertAlmostEqual(rows[0]["cash"], 25)
        self.assertGreater(rows[0]["revolver"], 0)
        self.assertLess(rows[1]["revolver"], rows[0]["revolver"])
        self.assertEqual(rows[-1]["revolver"], 0)
        first_interest = 2027 * 0.0467 + 3572 * 0.0544
        self.assertAlmostEqual(rows[0]["interest"], first_interest)
        second_interest = (rows[0]["floor_plan"] * 0.0467
                           + rows[0]["debt"] * 0.0544
                           + rows[0]["revolver"] * 0.06)
        self.assertAlmostEqual(rows[1]["interest"], second_interest)

    def test_no_automatic_tax_credit_on_loss(self):
        self.a["gross_margin"] = 0.01
        rows = model.project(assumptions=self.a)
        self.assertLess(rows[0]["pretax"], 0)
        self.assertEqual(rows[0]["tax"], 0)

    def test_terminal_growth_at_or_above_discount_rate_refused(self):
        for growth in (0.10, 0.11):
            with self.subTest(growth=growth):
                self.a["terminal_growth"] = growth
                with self.assertRaisesRegex(ValueError, "terminal growth < cost of equity"):
                    model.value_equity(self.rows, self.a)

    def test_terminal_repays_no_further_debt_and_discounts_five_years(self):
        result = model.value_equity(self.rows)
        # Decimal arithmetic starts with generated cash flows, checking valuation separately.
        f = [D(str(row["fcfe"])) for row in self.rows]
        explicit = sum(cf / D("1.10") ** t for t, cf in enumerate(f, 1))
        terminal = (f[-1] + D("150")) * D("1.025") / D("0.075") / D("1.10") ** 5
        self.assertAlmostEqual(result["pv_explicit"], float(explicit), places=8)
        self.assertAlmostEqual(result["pv_terminal"], float(terminal), places=8)
        self.assertAlmostEqual(result["value_per_share"], float((explicit + terminal) / D("17.951349")), places=8)

    def test_invalid_opening_shares_and_nonfinite_inputs(self):
        opening = dict(model.OPENING, cash=39.4)
        with self.assertRaisesRegex(ValueError, "FY2025 opening balance sheet gap"):
            model.project(opening=opening)
        with self.assertRaisesRegex(ValueError, "Shares outstanding must be positive"):
            model.project(assumptions=dict(self.a, shares=0))
        with self.assertRaisesRegex(ValueError, "must be finite"):
            model.project(assumptions=dict(self.a, growth=float("nan")))
        self.rows[0]["cash"] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite statement value"):
            model.value_equity(self.rows)

    def test_incomplete_forecast_refused(self):
        with self.assertRaisesRegex(ValueError, "all five forecast years"):
            model.value_equity(self.rows[:-1])

    def test_command_line_refusals_emit_no_price_and_base_case_recovers(self):
        for flag, message in (("--break-cash", "gap = -61.4"), ("--no-floor-plan", "cash-floor gap")):
            with self.subTest(flag=flag):
                run = subprocess.run([sys.executable, "-B", str(ROOT / "proforma.py"), flag], capture_output=True, text=True)
                self.assertEqual(run.returncode, 1)
                self.assertIn(message, run.stdout)
                self.assertNotIn("Value per share:", run.stdout)
        run = subprocess.run([sys.executable, "-B", str(ROOT / "proforma.py")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        self.assertIn("Value per share: $291.75", run.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
