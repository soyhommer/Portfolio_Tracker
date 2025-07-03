# 🗺️ FX Module - Detailed Roadmap

## ✅ Phase 1: Data Acquisition
- Research and select ECB historical data source (XML or CSV endpoint).
- Define target currencies (USD, GBP, CHF, JPY) to extract.
- Write robust parser to handle CSV lines, manage N/A values, normalize dates.
- Implement logging for parsing errors or missing data.

## ✅ Phase 2: Storage Format
- Define schema for euro_forex.json with currency ➜ date ➜ rate mapping.
- Ensure JSON format supports easy lookup and minimal size.
- Write JSON export function from parsed data.
- Include optional metadata (e.g., last updated date).

## ✅ Phase 3: Loader Module
- Create fx_loader.py.
- Implement load_euro_forex_json() with caching to avoid repeated disk reads.
- Build get_eur_rate(currency, date) with forward/backward date fallback.
- Implement get_cross_rate(source_currency, target_currency, date) using EUR pivot.
- Design error handling for missing rates.

## ✅ Phase 4: Auto-Update System
- Implement check_and_update_fx_data() to verify latest date in JSON.
- Auto-trigger ECB download and parse if data is stale or missing.
- Build CLI script fx_updater.py to refresh euro_forex.json on demand or via cron.
- Add logging of update success/failure.

## ✅ Phase 5: UI Integration
- Add manual refresh button in Streamlit NAV module.
- Hook button to fx_updater or parser call.
- Show confirmation on success or detailed error on failure.
- Display last updated date from JSON in UI for transparency.

## ✅ Phase 6: Testing & Validation
- Unit test ECB parser with real ECB sample files.
- Test get_eur_rate and get_cross_rate with synthetic and real data.
- Validate fallback behavior when dates are missing.
- Include regression tests for JSON format changes.

## ✅ Phase 7: Deployment Considerations
- Document setup of daily cron job for server deployments.
- Handle permissions for data/fx_rates folder.
- Provide manual uploader in UI for admins to recover from corruption.
- Ensure data is shared and consistent across all users.

## ✅ Optional Enhancements
- Add metadata with updated_at in JSON for UI display.
- Allow selective currency parsing in CLI with flags.
- Add CLI verbose logging option.
- Implement backup/restore for euro_forex.json.

