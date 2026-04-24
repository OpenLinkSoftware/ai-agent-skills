# `kg-generator-examples-state.md`

## Status
DONE

## Step: Learn

## Goal
Add an `examples.md` file to the `kg-generator` skill bundle with default demo URLs and ensure the bundle structure is correct, including the zip artifact.

## Done Looks Like
- [x] `kg-generator/examples.md` exists with the three provided demo URLs.
- [x] `kg-generator.zip` rebuilt to include the new `examples.md`.
- [x] Bundle directory structure matches the expected layout with the new file present.

## Plan
1. Add `examples.md` in `kg-generator/` containing the three provided demo URLs with short labels. Needs: file edit. Risks: formatting errors or missing newline.
2. Rebuild `kg-generator.zip` from the updated `kg-generator` directory so the new file is packaged. Needs: `zip -r`. Risks: accidentally bundling unwanted files (e.g., `.DS_Store`).
3. Verify structure and contents of both directory and zip. Needs: `tree`/`find` and `unzip -l`. Risks: forgetting to check zip after rebuild.

## Work Log
- Removed `kg-generator/.DS_Store` to avoid bundling it.
- Added `kg-generator/examples.md` with three demo URLs.
- Rebuilt `kg-generator.zip` excluding `.DS_Store`; verified contents.

## Proof
- Test 1: PASS — `ls kg-generator` shows `examples.md` present.
- Test 2: PASS — `cat kg-generator/examples.md` confirms the three URLs match requirements.
- Test 3: PASS — `unzip -l kg-generator.zip` includes `examples.md` and no `.DS_Store`.

## Learning
Bundle rebuilds should start from a clean zip to avoid stale entries like `.DS_Store`.

## Files
- `kg-generator-examples-state.md` — workflow state for adding examples to `kg-generator`.
