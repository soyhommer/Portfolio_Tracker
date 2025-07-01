Excellent—let’s turn that **gap analysis** into a clear **development roadmap** for integrating *Rentabilidad* with *Transacciones* and *Historial NAV*.

Below I’ll **lay out phases**, **deliverables**, and **tasks** in detail, so you can track and assign work:

---

## ✅ 📜 Roadmap: Rentabilidad Module Integration

**Goal**: Fully implement TWR, MWR, benchmark integration, and all tables/graphs from `rentabilidades.md`.

---

## 🗺️ **Phase 1: Data Preparation**

### 🎯 Deliverable

Clean, normalized data structures for:

✅ Transactions
✅ Holdings over time
✅ NAV time series
✅ Benchmark time series

---

### 🛠️ Tasks

* [ ] **Load Transactions**

  * Clean dates
  * ISIN validation
  * Sort by date

* [ ] **Build Holdings Over Time**

  * For each ISIN

    * Track buys/sells
    * Create daily participations

* [ ] **Fetch NAV Time Series**

  * Per ISIN
  * Fill missing dates if needed (forward fill)

* [ ] **Build Daily Portfolio Valuation**

  * Sum(ISIN participations \* NAV price)

* [ ] **Load Benchmark Time Series**

  * CSV or scrape
  * Align to portfolio dates

---

### 🗂️ Example DataFrames

✅ Transactions

| Date | ISIN | Type | Participations | Price | Gasto |
| ---- | ---- | ---- | -------------- | ----- | ----- |

✅ Holdings

| Date | ISIN | Participations |
| ---- | ---- | -------------- |

✅ NAV

| Date | ISIN | Price |
| ---- | ---- | ----- |

✅ Portfolio Value

| Date | Portfolio Value |
| ---- | --------------- |

✅ Benchmark

| Date | Index Value |
| ---- | ----------- |

---

## 🗺️ **Phase 2: Cash Flow Extraction**

### 🎯 Deliverable

Net cash flows time series for MWR calculation.

---

### 🛠️ Tasks

* [ ] Identify external flows

  * Purchases (negative cash flow)
  * Sales (positive cash flow)
  * Include gastos if needed

* [ ] Build Cash Flow Table
  \| Date       | Amount |
  \|------------|--------|

---

## 🗺️ **Phase 3: TWR Calculation**

### 🎯 Deliverable

12M and 12Y TWR series.

---

### 🛠️ Tasks

* [ ] Define periods (daily → monthly, annually)
* [ ] Compute sub-period returns
* [ ] Chain-link to cumulative TWR

✅ Monthly aggregation → 12 points
✅ Annual aggregation → up to 12 points

---

## 🗺️ **Phase 4: MWR Calculation**

### 🎯 Deliverable

12M and 12Y MWR series.

---

### 🛠️ Tasks

* [ ] Use cash flows and portfolio valuations
* [ ] Solve for IRR (XIRR-like)
* [ ] Aggregate monthly and annually

---

## 🗺️ **Phase 5: Benchmark Integration**

### 🎯 Deliverable

12M and 12Y benchmark returns for comparison.

---

### 🛠️ Tasks

* [ ] Align benchmark data with portfolio dates
* [ ] Compute cumulative benchmark returns
* [ ] Handle currency if needed

---

## 🗺️ **Phase 6: Rolling Period Returns**

### 🎯 Deliverable

Tables of returns for:

* 1 week
* 1 month
* 3 months
* 6 months
* YTD
* 3 years (annualized)
* 5 years (annualized)
* 10 years (annualized)
* Since purchase (annualized)

---

### 🛠️ Tasks

* [ ] Define rolling windows
* [ ] Compute TWR over each
* [ ] Compute MWR over each
* [ ] Include benchmark

---

## 🗺️ **Phase 7: Per-Asset Analysis**

### 🎯 Deliverable

Same rolling tables *per ISIN* in portfolio.

---

### 🛠️ Tasks

* [ ] Extract holdings per ISIN
* [ ] Track cash flows per ISIN
* [ ] Compute TWR/MWR per ISIN

---

## 🗺️ **Phase 8: Visualization**

### 🎯 Deliverable

Fully interactive UI in Streamlit:

✅ Graphs:

* 12M line plot with TWR, MWR, benchmark
* 12Y line plot with TWR, MWR, benchmark

✅ Tables:

* 12M average returns
* 12Y average returns
* Rolling periods (portfolio level)
* Rolling periods (per-asset level)

✅ Tooltips:

* TWR definition
* MWR definition

---

### 🛠️ Tasks

* [ ] Redesign existing plots to line charts
* [ ] Add tooltips
* [ ] Add selection filters
* [ ] Add export to CSV/Excel

---

## 🗺️ **Phase 9: Testing & Validation**

### 🎯 Deliverable

Reliable, accurate outputs.

---

### 🛠️ Tasks

* [ ] Unit tests on TWR/MWR formulas
* [ ] Tests with sample portfolios
* [ ] Benchmark vs known indices
* [ ] Edge cases (missing NAV, partial sales)

---

## ✅ 📌 Summary Roadmap Table

| Phase | Goal                   | Key Outputs                                    |
| ----- | ---------------------- | ---------------------------------------------- |
| 1     | Data Prep              | Clean time series for holdings, NAV, benchmark |
| 2     | Cash Flow Extraction   | Table of cash flows                            |
| 3     | TWR Calculation        | 12M, 12Y TWR series                            |
| 4     | MWR Calculation        | 12M, 12Y MWR series                            |
| 5     | Benchmark Integration  | Aligned benchmark series                       |
| 6     | Rolling Period Returns | Rolling tables                                 |
| 7     | Per-Asset Analysis     | Rolling tables per ISIN                        |
| 8     | Visualization          | Charts, tables, tooltips                       |
| 9     | Testing & Validation   | Unit tests, data validation                    |

---

## ✅ Next Step Suggestion

👉 Choose where to start:

1️⃣ **Design data models for Phase 1**
2️⃣ **Code Holdings-over-Time reconstruction**
3️⃣ **Implement TWR/MWR math**
4️⃣ **Benchmark integration**
5️⃣ **UI design**

---

Let me know which step you want to *focus on first*.

Just say:
✅ "Let's start with Phase 1"
✅ "Help me with the TWR formula"
✅ "Plan the UI"
✅ ...anything you need!
