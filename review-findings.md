# truthcert-meta2-prototype — Code Review Findings

**Reviewer:** Claude Opus 4.6 (1M context)
**Date:** 2026-04-03
**Files:** index.html (43 lines, landing page), sim/ (21 Python modules)

## P0 — Critical (must fix)

None found.

## P1 — Important

### P1-1: SE approximation from CrI uses /3.92 (correct)
**File:** sim/witness_panel.py, line 66
**Issue:** SE estimated as (CrI_high - CrI_low) / 3.92. This is correct for a 95% CrI under normality (3.92 = 2 * 1.96). Comment correctly notes this is only for reporting.
**Status:** PASS.

### P1-2: Arbitration can only inflate, never shrink
**File:** sim/arbitration.py, lines 1-9, implemented throughout
**Status:** PASS — the conservative invariant is maintained. `inflation_factor >= 1.0` always.

### P1-3: Disagreement metric uses std of witness means
**File:** sim/arbitration.py, line 76
**Issue:** `np.std(mus)` with default ddof=0 (population std). For 3 witnesses, this is reasonable and consistent.
**Status:** PASS.

## P2 — Minor

### P2-1: `index.html` has `</html>` closing tag
**Line:** 44
**Status:** PASS.

### P2-2: No security concerns — Python simulation code only
**Status:** No user-facing input, no web interface, no CSV export with user data.

### P2-3: `_safe()` function handles None correctly
**File:** sim/witness_panel.py, line 43-45
**Status:** PASS — returns default when value is None.

## Summary

| Severity | Count |
|----------|-------|
| P0       | 0     |
| P1       | 3     |
| P2       | 3     |
