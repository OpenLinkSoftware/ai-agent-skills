# update-admin-assistant-copyright-state.md

## Status
DONE

## Step: Learn

## Goal
Update the OpenLink Admin Assistant so its displayed copyright text reads `© 1993-2026`.

## Done Looks Like
- [x] Test 1: Find the source of the user-visible copyright string in the Admin Assistant.
- [x] Test 2: Update that source so the rendered text uses the year range `1993-2026`.
- [x] Test 3: Verify the updated source contains the new year range.

## Plan
1. Locate the user-facing copyright source in the Admin Assistant tree. — needs: source search — risks: multiple copies
2. Patch the canonical string in the shared helper file. — needs: write access to the source tree — risks: editing the wrong artifact
3. Verify the new value in the updated file. — needs: file readback — risks: stale copy elsewhere
4. Record proof and close the task. — needs: verification output — risks: none

## Work Log
- Found the Admin Assistant source tree at `/Users/kidehen/Documents/Management/Development/multi-tier-stuff/wwww_sv`.
- Confirmed the UI pages render `[productname copyright]` from `include/common.tcl`.
- Updated the `productname copyright` branch in `include/common.tcl`.
- Corrected an encoding issue by using the ASCII-safe HTML entity `\&copy\;` so the UI renders `©`.

## Proof
- Test 1: PASS — `include/common.tcl` defines `productname copyright`, which is rendered by `footer`, `menu_footer`, and pages such as `html/wuab.html`.
- Test 2: PASS — the source now returns `\&copy\; 1993-2026 .` for `productname copyright`.
- Test 3: PASS — readback of `include/common.tcl` confirmed the updated line at line 33.

## Learning
For legacy Tcl/HTML output, an HTML entity is safer than inserting a raw copyright symbol into a source file with uncertain encoding.

## Files
- update-admin-assistant-copyright-state.md — task state and proof log
