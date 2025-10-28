# Changelog

## [2.0.6] - 2025-10-28 - RELEASE BUMP
### Changed
- Version bump for distribution. No functional changes from 2.0.5.

## [2.0.5] - 2025-10-28 - STABILITY + HARDENING
### Fixed
- Correct PI30 mapping: battery discharge current at index 15
- Paho 2.x compatibility by using Callback API VERSION1 with MQTTv311
- Discovery and availability published with QoS 1 and retain
- Timestamp now timezone-aware ISO8601

### Changed
- Dockerfile: removed unnecessary build dependencies; copy only needed files
- requirements: removed unused pyserial
- Add-on config: removed SYS_ADMIN privilege and full_access

## [2.0.3] - 2025-07-20 - RELIABLE COMMUNICATION RESTORED
### 🔧 Fixed
- **Restored proven v2.0.0 communication method** that was working
- Fragment reading: 15 attempts (vs 30 in v2.0.0) for speed
- Buffer size: 500 bytes for fragments (increased from 100)
- Timeout: 1.5s for fragments (balanced)
- Complete response validation restored

### Technical Changes
- Restored robust read loop from v2.0.0
- 15 attempts instead of 30 (faster than v2.0.0)
- 500-byte fragment buffer (vs 100 in v2.0.1/2)
- Proper incomplete response handling
- Position 19 PV power reading preserved

## [2.0.2] - 2025-07-20 - COMMUNICATION FIX
### 🔧 Fixed
- **Communication issues from v2.0.1** - response fragments not being read completely
- Balanced timeouts: 3s initial, 1s for fragments (was too aggressive in v2.0.1)
- Increased read attempts to 8 (was only 3)
- Larger initial buffer (150 bytes vs 112)
- Still faster than v2.0.0 but reliable communication

### Technical Changes
- Initial timeout: 3s (balanced from 2s)
- Fragment timeout: 1s (from 0.5s)
- Read attempts: 8 (from 3)
- Fragment delay: 0.1s (from 0.05s)

## [2.0.1] - 2025-07-20 - PERFORMANCE OPTIMIZED VERSION
### 🚀 Performance Improvements
- **15-30s loading time reduced to ~2-3s**
- Removed extensive debug logging from production code
- Optimized HID communication timeouts (2s vs 5s)
- Limited read attempts to 3 (was 30)
- Reduced buffer size to 112 bytes (was 1000)
- Set debug=false by default for production use

### Technical Changes
- Streamlined read_inverter_data() function
- Removed position search debug code
- Kept only essential logging for position 19 PV power
- Faster response processing

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
