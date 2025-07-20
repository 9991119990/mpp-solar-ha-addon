# Changelog

## [2.0.0] - 2025-07-20 - FINAL PRODUCTION VERSION
### 🎯 MAJOR BREAKTHROUGH
- **FOUND IT!** PV power is stored directly in QPIGS position 19
- Same as EASUN inverters - no calculations needed
- 98.2% accuracy (444W display shows as 436W in position 19)
- Removed ALL correction factors and calculations

### Changed
- Complete rewrite of PV power reading logic
- Direct reading from `values[19]` - no math involved
- Extended response reading to capture all positions

### Technical Details
- Position 19 contains actual PV power in watts
- No conversion or scaling needed
- Matches display values with 98%+ accuracy

## [1.0.12] - 2025-07-19
### Added
- Extended diagnostics to search for direct value
- Complete HEX dump of responses
- Search for values matching display

## [1.0.11] - 2025-07-19
### Changed
- Attempted formula: (Bus voltage + PV voltage) × 2
- Still not accurate enough

## [1.0.10] - 2025-07-19
### Added
- Deep search mode for exact display values
- Fractional value checking

## [1.0.9] - 2025-07-19
### Changed
- Adaptive correction factors based on power levels
- Better but still calculated, not direct

## [1.0.8] - 2025-07-19
### Changed
- Fixed factor of 4 for position 5
- Only accurate at low power levels

## [1.0.0-1.0.7] - 2025-07-18
### Initial Development
- Various attempts at calculating PV power
- Correction factors and formulas
- None matched display accurately

---

**Note:** Version 2.0.0 is the FINAL version with direct display value reading.