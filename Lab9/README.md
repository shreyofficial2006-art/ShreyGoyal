# Lab 09 — ABG Pro-Forma Build

**Shrey Goyal · FIN 43900 · Prepared September 24, 2026**

The five-year model reproduces the assigned ABG value of **$291.75 per share**. All five balance sheets balance, cash reconciles to the cash-flow statement, and cash remains above the $25 million minimum. Deliberately replacing FY2026E cash with 40.4 makes the model refuse valuation with **FY2026E: assets − liabilities − equity gap = −61.4 million**.

This is the instructor's ABG training case for **Lab 09**, using the assigned FY2025 opening balances and FY2026E–FY2030E assumptions. It is not a current ABG investment recommendation or the own-company assignment in Lab 10. All money is in **USD millions**, except value per share; shares are in millions.

## Submission files and execution evidence

| File | Purpose |
|---|---|
| [proforma.py](../proforma.py) | Standalone, standard-library-only three-statement model |
| [ABG_executed_output.txt](ABG_executed_output.txt) | Actual five-year statements, checks, and valuation |
| [broken_cash_output.txt](broken_cash_output.txt) | Actual required −61.4 rejection; no valuation printed |
| [no_floor_plan_output.txt](no_floor_plan_output.txt) | Industry-specific failure: balanced statements but insufficient cash |
| [test_proforma.py](test_proforma.py) | Published-answer comparisons, separate decimal calculations, and failure tests |
| [validation_results.txt](validation_results.txt) | Actual test log: 14 tests passed |
| [calculated_results.json](calculated_results.json) | Full-precision inputs, statements, checks, and valuation |
| [week3_preflight_output.txt](week3_preflight_output.txt) | Existing `dcf.py` still runs; the earlier lab file is unchanged |

## Reproduce

From the repository root, with Python 3.9 or later:

```text
python proforma.py
python proforma.py --break-cash
python proforma.py --no-floor-plan
python -B -m unittest discover -s Lab9 -v
```

There are no packages to install, API keys, downloads, or paid services. The two deliberate-break commands **should exit with status 1 and print no price**. The regular command exits with status 0. A break flag changes only the in-memory demonstration; run the regular command again to return to the intact base case.

For the literal swap-and-break exercise, a partner can temporarily insert `rows[0]["cash"] = OPENING["cash"]` immediately before `print_statements(rows, a)` inside `main()`, run the file, and remove that line. The `--break-cash` option performs exactly that change without editing the saved file. The saved demonstrations here are automated self-tests, **not evidence that a live partner exercise took place**.

## Define: the finance question

What are five years of a company's statements worth, given explicit assumptions, and how can the model demonstrate that those statements tie together? For this exercise, the intended user is a reviewer checking the ABG teaching model. The result is conditional on the supplied assumptions, with a large dependence on cash flows after 2030.

## Represent: opening balances and assumptions

The source of every number below is the [assigned Lab 09 input table and opening balance sheet](https://github.com/cinderzhang/fin43900-fall2026/blob/6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f/lessons/week-05/lab-09-proforma-build.md). The reasons summarize the instructor's [Part 1 explanations](https://cinderzhang.github.io/FIN43900-Fall2026/lessons/week-05/pro-forma-abg-tutorial/video-1-build-the-base-case-slides.html), particularly slides 5–14. Labels such as “history,” “guidance,” and “fact” preserve the lab's attribution; the underlying issuer filings were not independently re-audited for this replication.

| FY2025 opening item | USD millions |
|---|---:|
| Revenue | 17,999.0 |
| Cash | 40.4 |
| Inventory | 2,135.8 |
| PP&E | 3,070.4 |
| Other assets | 6,371.6 |
| Floor-plan loans | 2,027.0 |
| Term debt | 3,572.0 |
| Other liabilities | 2,127.5 |
| Equity | 3,891.7 |
| Revolver | 0.0 |

Opening assets and liabilities plus equity both equal **11,618.2**. No balancing adjustment is added to the lab's opening numbers.

| Assumption | Exact model input | Label | Rationale / interpretation |
|---|---|---|---|
| Organic revenue growth | 1.8% yearly | Judgment | A modest organic-growth assumption above the tutorial's 1.2% same-store observation; it does not compound acquisition-driven reported growth. |
| Gross margin | 17.05% | Judgment | Holds a normalized margin near the assigned 2025 level after the vehicle-shortage premium subsides. Holding it flat is a choice. |
| SG&A / gross profit | 66.5%, 65.5%, 64.5%, 64.5%, 64.5% | Judgment | Costs rise initially during integration, then improve toward the earlier operating range without assuming a full return to unusually low 2023 costs. |
| Depreciation / opening PP&E | `82.4 / 3070.4` | History | Carries the specified FY2025 ratio at full precision; depreciation uses each forecast year's opening PP&E. |
| Non-cash impairment | 120 yearly | Judgment | Recognizes recurring asset write-downs rather than treating them as permanently absent. |
| Capital spending | 250 yearly | Guidance | The lab labels the 2026 amount as management guidance; extending it through 2030 is a judgment. The tutorial notes that interim spending challenges this assumption. |
| Tax rate | 25.5% | Judgment | Sits between the tutorial's recent average and latest annual effective tax rate; losses receive no automatic tax credit. |
| Inventory days | `2135.8 / (17999.0 - 3071.7) * 365` | History | Uses FY2025 inventory divided by cost of sales; do not substitute rounded days. |
| Floor-plan loans / inventory | `2027.0 / 2135.8` | History | Preserves the assigned inventory financing ratio rather than rounding it to 95%. |
| Other working capital | 0.8% of change in revenue | Judgment | A small incremental cash investment as sales grow, also recorded in other assets. |
| Minimum cash | 25 | History, per lab | The stipulated liquidity floor for a dealer operating with relatively little cash. |
| Revolver limit | 850 | Judgment, per lab | A finite liquidity facility; the model may not borrow past it. |
| Revolver rate | 6% | Judgment | Charges the opening drawn balance, avoiding a circular same-year interest calculation. |
| Term-debt repayment | 150 yearly | Judgment | A scheduled five-year reduction in term debt. Repayment ends in the terminal calculation; it cannot exceed debt outstanding. |
| Share buyback | 150 yearly | Judgment | A distribution choice; reduces equity and cash after FCFE, rather than being deducted from FCFE twice. |
| Floor-plan interest rate | 4.67% | History | Applied to opening floor-plan loans, including the existing balance in 2026. |
| Term-debt interest rate | 5.44% | History | Applied to opening term debt, before the current-year repayment. |
| Cost of equity | 10% | Judgment | The assigned required return for equity cash flows. This is a starting assumption, not an estimated ABG beta. |
| Terminal growth | 2.5% | Judgment | The assigned perpetual growth rate; valuation requires it to be below the cost of equity. |
| Shares outstanding | 17.951349 million | Fact, per lab's June 30, 2026 10-Q attribution | Fixed denominator required to reproduce the known answer. Future buybacks are not used to invent a forecast repurchase price or new share count. |

The three main **operating judgments** are organic growth, gross margin, and the SG&A recovery path. Growth determines the sales base, margin determines gross profit, and the SG&A path determines how much gross profit reaches operating earnings. The tutorial identifies the pace of SG&A recovery as especially consequential. The cost of equity and terminal growth are also material valuation judgments because approximately 80% of value lies beyond the explicit forecast.

## Implement: how the statements connect

The engine computes revenue, gross profit, SG&A, depreciation, impairment, operating income, interest, tax, and net income first. It then projects the non-cash balance-sheet lines. Inventory follows cost of sales and inventory days; inventory loans follow inventory; PP&E increases with capital spending and decreases with depreciation. Other assets increase with incremental working capital and decrease with impairment. Equity increases with net income and decreases with buybacks.

The cash-flow bridge is:

```text
FCFE = net income + depreciation + impairment
       - capital spending - increase in inventory - increase in other working capital
       + increase in floor-plan loans - term-debt repayment

Cash before revolver = opening cash + FCFE - buyback
Closing cash = cash before revolver + revolver draw - revolver repayment
```

Cash is calculated **last** because it is the result of these operating, investment, borrowing, repayment, and distribution decisions. If cash were entered independently, the cash-flow statement and balance sheet could disagree. It is not a plug used to force the accounting identity to hold. The revolver only fills a cash shortfall up to its limit, and surplus cash repays any outstanding revolver first. The base case never needs the revolver.

Non-cash impairment reduces earnings and other assets, then is added back in the cash-flow bridge. Depreciation similarly reduces earnings and PP&E and is added back in cash flow. This treatment links the statements without double-counting non-cash expenses.

## Validate: known answers and deliberate failures

| Published check | FY2026E expected | FY2026E actual | FY2030E expected | FY2030E actual |
|---|---:|---:|---:|---:|
| Revenue | 18,323.0 | 18,323.0 | 19,678.3 | 19,678.3 |
| Operating income | 844.2 | 844.2 | 971.4 | 971.4 |
| Net income | 413.6 | 413.6 | 527.5 | 527.5 |
| FCFE | 211.4 | 211.4 | 342.3 | 342.3 |
| Closing cash | 101.8 | 101.8 | 719.8 | 719.8 |
| Assets − liabilities − equity | 0.0 | 0.0 | 0.0 | 0.0 |

| Valuation component | Model result |
|---|---:|
| PV of FY2026E–FY2030E FCFE | $1,059.87 million |
| 2031 normalized FCFE | $504.59 million |
| Terminal value at end-2030 | $6,727.85 million |
| PV of terminal value | $4,177.46 million |
| Equity value | **$5,237.34 million** |
| Share of value after 2030 | **79.76%** |
| Value per share | **$291.75** |

Displayed components are rounded separately; calculations retain full precision. FCFE is already a cash flow to equity, so the discount rate is the cost of equity and term debt is not subtracted again. The required terminal formula is:

```text
2031 FCFE = (2030 FCFE + 2030 debt repayment) × 1.025
Terminal value at end-2030 = 2031 FCFE / (0.10 - 0.025)
Equity value = sum(FCFE[t] / 1.10^t, t=1..5) + terminal value / 1.10^5
Value per share = equity value / 17.951349
```

The 150 repayment is added back because the assigned explicit repayment schedule ends after 2030. The remaining term debt is not assumed to vanish; this is the course's terminal normalization, which would need further justification in a company-specific valuation.

**Required cash break.** FY2026E normally produces 211.4 of FCFE and spends 150.0 on buybacks, increasing cash by 61.4. Replacing computed closing cash of 101.8 with opening cash of 40.4 removes that increase from assets while leaving liabilities and equity unchanged. Therefore the gap is **−61.4**. Its size and sign point directly to a stale, unlinked cash line. The executable demonstration calls the same valuation function as the base case; `assert_balanced` raises before any price is printed. The intact base case is rerun successfully in the automated command-line test.

**What floor plan means.** Dealers finance vehicles using inventory-secured loans from manufacturers' finance companies and banks. The forecast ties those loans to inventory, charges interest on the opening balance, and includes the change in inventory financing inside the FCFE bridge. Financing covers most of the cash needed for the additional vehicles.

**Why deleting floor plan causes roughly −$1.1 billion of cash.** Setting the projected financing ratio to zero while retaining the existing opening liability forces repayment of the entire 2,027.0 opening loan and removes replacement funding. The revolver reaches its 850.0 limit but cannot fill the hole. FY2026E ending cash becomes approximately **−1,112.0 million**. The accounting identity still balances: repaying a liability reduces cash and liabilities together. The separate cash-floor check refuses valuation. Balanced accounts alone do not establish financial viability.

The [14-test log](validation_results.txt) covers published first/last-year answers, intermediate-year tutorial values, a separate first-year Decimal calculation, accounting and cash linkage in every year, required cash rejection, offsetting errors that leave a balance sheet apparently balanced, loss of floor-plan financing, revolver draw and repayment, opening-balance interest, losses without tax credits, invalid terminal growth, separate terminal-value arithmetic, invalid inputs, incomplete forecasts, and command-line failure/recovery.

## Reflection and preparation for the partner exercise

- **Why cash last?** Cash must follow actual sources and uses; entering it first would break its connection to earnings, reinvestment, financing, and distributions.
- **What does −61.4 tell me?** The model omitted the 61.4 increase in cash. The balance-sheet cash line likely still points at the opening balance.
- **Why keep floor plan?** Inventory loans fund the dealer's vehicles. Removing them while leaving inventory intact turns a funded operating asset into an enormous cash need.
- **What needs the most judgment?** The SG&A recovery path determines how much gross profit becomes earnings. The terminal growth and equity discount rate then carry most of the valuation weight.

These AI-assisted explanations prepare the student to explain the model in their own words. They do not claim video attendance, a no-screen explanation, or a completed live partner review. The assigned [Part 1 video](https://youtu.be/O4PeC2PqwRY) and actual partner explanation/swap-and-break remain distinct activities.

## AI assistance, checks, and limitations

**Tool: OpenAI Codex.** Codex read the current Lab 09 instructions and relevant tutorial material, wrote the model and tests, ran them, and drafted this report. The checks compare model output with the instructor's published numerical fixtures and use separate Decimal arithmetic and deliberately corrupted cases. Agreement between AI-generated code and AI-generated tests alone is not the basis for accepting the result; the external known-answer table is the main benchmark. No student-only or partner activity is represented as completed by the assistant.

This package uses the course case as assigned. It does not assert independent verification of the underlying SEC filings, estimate a current market price, forecast future acquisitions, or establish that the base-case assumptions will occur. Capital-spending extrapolation, stable gross margin, SG&A improvement, fixed share count, and terminal normalization are limitations. The substantial terminal-value contribution makes the point estimate sensitive to long-run assumptions.

The original Week 3 `dcf.py` was executed without modification; its saved output is linked above. Lab 10's own-company history, assumption defense, and partner challenge are separate work and are not substituted into this ABG replication.

## Course references and requirement coverage

Reviewed course snapshot: **`6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f`**.

- [Lab 09 instructions, input table, known answers, and checkout](https://github.com/cinderzhang/fin43900-fall2026/blob/6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f/lessons/week-05/lab-09-proforma-build.md)
- [Week 5 overview and prework](https://github.com/cinderzhang/fin43900-fall2026/blob/6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f/lessons/week-05/README.md)
- [Week 5 worked numerical handout](https://github.com/cinderzhang/fin43900-fall2026/blob/6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f/lessons/week-05/student-handout.md)
- [Part 1 slides and spoken notes](https://cinderzhang.github.io/FIN43900-Fall2026/lessons/week-05/pro-forma-abg-tutorial/video-1-build-the-base-case-slides.html), especially slides 10–14, 17–19, 25, 27, and 35–38
- [Tutorial context](https://github.com/cinderzhang/fin43900-fall2026/blob/6bcbc3c929de59c547b2e421fe0f4ef2dc5d564f/lessons/week-05/pro-forma-abg-tutorial.md)

| Lab requirement | Evidence / status |
|---|---|
| Single Python file; standard library only | `../proforma.py`; no installation required |
| Five years of income statement, balance sheet, and cash flow | `ABG_executed_output.txt` |
| Exact ratios and labelled assumptions | Input block plus this report's assumption table |
| Cash computed last; minimum and revolver respected | `project`, output checks, and financing tests |
| Printed annual checks; `assert_balanced` before valuation | Output check block and `value_equity` gate |
| Published ABG answers and $291.75 | Known-answer comparison and executed output |
| Broken cash must fail at FY2026E, −61.4 | `broken_cash_output.txt` and command-line test |
| Floor-plan explanation and reflection | Sections above plus `no_floor_plan_output.txt` |
| Video/prework and live partner exercise | Student activities; not claimed by automated evidence |
| Individual GitHub checkout | This report, source file, and linked execution evidence |

The course describes Lab 09 as a **25-or-0 completion checkout**. Brightspace governs deadlines and submission; publishing these files does not itself submit them to Brightspace.
