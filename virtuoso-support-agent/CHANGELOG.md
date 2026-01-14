# Virtuoso Support Agent Skill - Changelog

## v1.4.1 - Corrected Workflow

**Release Date:** November 12, 2025

### Corrections from v1.4.0

**Issue:** Initial v1.4.0 incorrectly positioned remote DSN handling as a mandatory Step 0 in the main workflow, instead of error recovery.

**Solution:** 
- Returned to **9-step core workflow** (not 12-step)
- Remote DSN verification moved to **error recovery only** (Step 2 fallback)
- Uses **high-level RDF Views tools** exclusively (not low-level SQL tools)
- **Assumes database and schema already exist** in Virtuoso

### Workflow Changes

#### Before (Incorrect v1.4.0)
```
Step 0: Remote Data Source Initialization (mandatory, always executed first)
Step 1-12: Main workflow
Total: 13 steps including optional paths
```

#### After (Correct v1.4.1)
```
Step 1: Confirm Target Instance
Step 2: Table Discovery (using database_schema_objects with qualified names)
Step 3: Graph IRI Assignments
Step 4: Pre-audit
Step 5: Generate RDF Views + Ontology + Data Rules (all high-level tools)
Step 6: Execute All Scripts
Step 7: Post-audit
Step 8: Verify Quad Maps & Ontology
Step 9: Validate Knowledge Graph
Total: 9 steps (clean, linear workflow)
```

**Note:** If table discovery fails in Step 2, remote DSN verification is attempted as error recovery.

### Key Corrections

1. ✅ **Correct Tool Abstraction Level**
   - Uses `RDFVIEW_FROM_TABLES`, `RDFVIEW_ONTOLOGY_FROM_TABLES`, `RDFVIEW_GENERATE_DATA_RULES`
   - NOT low-level SQL query tools
   - Tools handle remote database complexity internally

2. ✅ **Correct Assumptions**
   - Database and schema assumed to exist
   - Qualified table names used: `sqlserver.northwind.Customers`
   - Remote DSN only checked if discovery fails

3. ✅ **Correct Step Sequence**
   - No conditional Step 0
   - All tools use high-level generation functions
   - Consolidated ontology + data rules into Step 5 generation, Step 6 execution

4. ✅ **Correct Error Recovery**
   - Remote DSN handling moved to "Error Recovery Procedures"
   - Only triggered if `database_schema_objects` fails
   - Not part of standard workflow

### Files Updated

- `SKILL.md`: Updated workflow description (9 steps, not 12)
- `references/workflow-details.md`: Completely rewritten for correct 9-step workflow
- `CHANGELOG.md`: This file

### Impact

- **Simpler, cleaner workflow** (9 steps instead of 13)
- **Better tool abstraction** (high-level RDF Views tools)
- **Correct assumptions documented** (database/schema exist)
- **Proper error recovery** (remote DSN as fallback)
- **More maintainable** (linear flow, no conditional branches)

### Backward Compatibility

- ✅ Existing RDF Views knowledge base still applies
- ✅ All tool names unchanged
- ✅ All functionality preserved
- ⚠️ Workflow diagram changed (users should review)
- ⚠️ Step numbering corrected (was 12 steps, now 9)

### For SQL Server Northwind Use Case

The corrected workflow now properly handles your scenario:

1. **Step 1:** Confirm Demo/URIBurner instance
2. **Step 2:** Discover tables via `database_schema_objects` with `sqlserver` qualifier and `northwind` schema filter
3. **Step 3:** Assign IRIs for data/ontology/schema graphs
4. **Step 4-5:** Generate all artifacts (RDF Views + Ontology + Data Rules)
5. **Step 6:** Execute scripts in sequence
6. **Step 7-9:** Verify and validate

**Result:** Clean Knowledge Graph workflow using proper tool abstraction.

---

## v1.4.0 - Initial Enhancement (Superseded by v1.4.1)

*This version had incorrect workflow structure and has been corrected.*

---

## v1.3.05 - Previous Release

**Release Date:** (Earlier)

- Token-optimized references architecture
- 9-step RDF Views workflow
- Optional ontology and data rules generation
