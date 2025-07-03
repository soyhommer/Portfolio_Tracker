```markdown
# 📈 FX Module - Functional Specification

## 🎯 Objective
Enable **multi-currency portfolio valuation** by providing historical FX rates to convert any asset currency to the **base currency of the portfolio**.

The FX system will:
✅ Store daily ECB reference rates in EUR base.  
✅ Serve any needed conversion via EUR as the pivot currency.  
✅ Stay automatically up to date with ECB data.  
✅ Be shared and consistent across all users.

---

## ⚙️ Data Model

### 1️⃣ Storage File

**Path:**
```

/data/fx\_rates/euro\_forex.json

````

**Format:**
```json
{
  "USD": {
    "2025-07-02": 1.1755,
    "2025-07-01": 1.181,
    ...
  },
  "GBP": {
    "2025-07-02": 0.8605,
    ...
  },
  "CHF": {
    "2025-07-02": 0.933,
    ...
  },
  "JPY": {
    "2025-07-02": 169.45,
    ...
  }
}
````

✅ EUR is the **pivot currency**.
✅ Rates are ECB **end-of-day** official reference rates.
✅ N/A or missing values are excluded during parsing.

---

## 2️⃣ Cross-rate Formula

All conversions will use EUR as pivot:

```
Amount_in_target = Amount_in_source × (EUR→target) / (EUR→source)
```

✅ Direct rates for EUR→Currency: stored in JSON.
✅ Cross-rates for Currency1→Currency2: calculated dynamically.

**Example:**

```
USD/GBP = (EUR→USD) / (EUR→GBP)
```

---

## 3️⃣ File Structure

```
/data/
  /fx_rates/
    euro_forex.json
  /nav_historico/
  /transacciones/
```

---

## 🔗 Source of Data

✅ ECB historical reference rates:

* XML: [https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml)
* CSV-like daily updates also available.

✅ Rates always EUR-based:

* "1 EUR = X Currency"

---

## 🛠️ Update Strategy

### ✅ A. Automatic Refresh on App Load

On startup:

```
check_and_update_fx_data()
```

* Load existing JSON.
* Check latest date.
* If outdated → download ECB, reparse, save new JSON.

✅ Ensures fresh data with no manual steps.
✅ Works offline after first sync.

---

### ✅ B. Scheduled Server Job

Optional for production:

* Daily cron job or Windows task.

```
python utils/fx_updater.py
```

✅ Fully automatic, no frontend dependency.

---

### ✅ C. Manual Fallback in UI

Optional Streamlit button:

> "⚠️ Refresh FX Rates Now"

* Calls the same download and parse function.
* For corrupted or missing JSON recovery.

---

## 📂 Recommended Modules

### 1️⃣ `/utils/fx_loader.py`

Provides:

```python
get_eur_rate(currency, date)
get_cross_rate(source_currency, target_currency, date)
check_and_update_fx_data()
```

* Loads euro\_forex.json into memory cache.
* Serves FX rates with fallback search if date missing.
* Calculates cross rates via EUR.

---

### 2️⃣ `/utils/fx_updater.py`

Provides:

```bash
python fx_updater.py
```

* CLI script.
* Downloads ECB historical file.
* Parses relevant currencies (USD, GBP, CHF, JPY).
* Writes `/data/fx_rates/euro_forex.json`.

---

## ✅ Example API Usage

**EUR portfolio base:**

```python
rate = get_eur_rate("USD", "2025-07-02")
```

**Non-EUR base:**

```python
usd_to_gbp = get_cross_rate("USD", "GBP", "2025-07-02")
```

---

## ✅ Automatic Maintenance

* App initialization triggers `check_and_update_fx_data()`.
* Ensures `euro_forex.json` is always up to date.
* Supports manual Streamlit upload as fallback.

---

## ✅ Benefits

✔️ Single authoritative FX dataset.
✔️ Shared across all users.
✔️ Works offline once populated.
✔️ Fully local, no vendor lock-in.
✔️ ECB official, reliable and free.

---

## 🚀 Optional Enhancements

* Add metadata:

```json
{
  "updated_at": "2025-07-02",
  "rates": { ... }
}
```

* CLI flags for selective currency parsing.
* UI notification of last update date.
* Backfilling historical gaps.

---

## 📌 TL;DR

✅ Store ECB historical FX rates in `euro_forex.json`.
✅ Always EUR-based.
✅ Serve any currency pair via cross-rate formula.
✅ Keep it updated automatically.
✅ Allow manual fallback.
✅ Integrate seamlessly with all valuation modules.

---

```

I've put the complete FX module specification in Markdown above. If you want, I can help you next to:

✅ Turn it into a real `README_FX.md` file  
✅ Write the actual `fx_loader.py` module code skeleton  
✅ Write the ECB parsing / updating script skeleton  

Just tell me what you want next!
```
