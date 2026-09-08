"""Five-year FCFF discounted cash flow model for Lab 05.

All monetary inputs and outputs are in USD millions except value per share.
Edit only the input block for a different scenario or company.
"""

# ----------------------------- INPUTS -----------------------------
starting_fcff = 100.0
growth_rates = [0.08, 0.06, 0.05, 0.04, 0.03]
wacc = 0.10
terminal_growth = 0.03
non_operating_cash = 50.0
debt = 300.0
diluted_shares = 50.0
# ------------------------------------------------------------------

if terminal_growth >= wacc:
    raise SystemExit("Error: terminal growth must be less than WACC.")

fcff_by_year = []
fcff = starting_fcff

for growth_rate in growth_rates:
    fcff *= 1.0 + growth_rate
    fcff_by_year.append(fcff)

present_value_explicit_fcff = sum(
    yearly_fcff / (1.0 + wacc) ** year
    for year, yearly_fcff in enumerate(fcff_by_year, start=1)
)

terminal_value_year_5 = (
    fcff_by_year[-1] * (1.0 + terminal_growth) / (wacc - terminal_growth)
)

present_value_terminal_value = terminal_value_year_5 / (1.0 + wacc) ** 5
enterprise_value = present_value_explicit_fcff + present_value_terminal_value
equity_value = enterprise_value + non_operating_cash - debt
value_per_diluted_share = equity_value / diluted_shares
terminal_value_share = present_value_terminal_value / enterprise_value

for year, yearly_fcff in enumerate(fcff_by_year, start=1):
    print(f"FCFF Year {year}: {yearly_fcff:.4f}")

print(f"Present value of the explicit FCFF: {present_value_explicit_fcff:.4f}")
print(f"Terminal value at Year 5: {terminal_value_year_5:.4f}")
print(f"Present value of the terminal value: {present_value_terminal_value:.4f}")
print(f"Enterprise value: {enterprise_value:.4f}")
print(f"Equity value: {equity_value:.4f}")
print(f"Value per diluted share: {value_per_diluted_share:.4f}")
print(
    "Present value of the terminal value as a share of enterprise value: "
    f"{terminal_value_share:.4f}"
)