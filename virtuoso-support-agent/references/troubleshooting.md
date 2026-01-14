# Troubleshooting Guide - Virtuoso Support Agent

Common issues, error codes, and resolution procedures.

---

## RDF Views Generation Issues

### Error: Table Not Found

**Symptoms:**
- "Table [name] does not exist"
- "No such table: [name]"

**Causes:**
1. Incorrect table name
2. Wrong schema specified
3. Insufficient permissions
4. Table in different catalog

**Resolution:**
```
1. Re-run table discovery:
   {Server}:execute_sql_query({
     sql: "SELECT name_part(KEY_TABLE, 0) AS catalog, name_part(KEY_TABLE, 1) AS schema, name_part(KEY_TABLE, 2) AS table_name FROM DB.DBA.SYS_KEYS WHERE KEY_IS_MAIN = 1 ORDER BY catalog, schema, table_name",
     format: "markdown"
   })

2. Verify exact spelling and case sensitivity

3. Check permissions:
   SELECT * FROM [catalog].[schema].[table] LIMIT 1;

4. Use full catalog.schema.table format
```

---

### Error: Graph IRI Already Exists

**Symptoms:**
- "Quad map [name] already exists"
- "Graph IRI [iri] is already in use"
- Duplicate key violation

**Causes:**
1. Previous RDF View not cleaned up
2. Graph IRI conflict
3. Incomplete deletion

**Resolution:**
```
1. List existing quad maps:
   {Server}:sparqlQuery({
     query: "PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#> SELECT ?qm WHERE { ?qm a virtrdf:QuadMap } ORDER BY ?qm"
   })

2. Generate drop script:
   {Server}:RDFVIEW_DROP_SCRIPT({
     graph_iri: "http://conflicting.iri/graph"
   })

3. Execute drop script:
   {Server}:EXECUTE_SQL_SCRIPT({
     sql_script: "[generated drop script]"
   })

4. Clear the graph:
   {Server}:sparqlQuery({
     query: "CLEAR GRAPH <http://conflicting.iri/graph>"
   })

5. Retry RDF View creation
```

---

### Error: SQL Script Execution Failure

**Symptoms:**
- "Error executing statement [N]"
- "SR171: Transaction aborted"
- Script stops mid-execution

**Causes:**
1. Resource constraints
2. Lock timeouts
3. Permission issues
4. Malformed IRI

**Resolution:**
```
1. Check specific error:
   Look at statement number and error code

2. Verify resources:
   {Server}:execute_sql_query({
     sql: "SELECT * FROM SYS_STAT WHERE STAT_NAME LIKE '%Locks%'",
     format: "markdown"
   })

3. Check locks:
   {Server}:execute_sql_query({
     sql: "SELECT * FROM DB.DBA.SYS_L_STAT",
     format: "markdown"
   })

4. Restart transaction:
   - Stop other operations
   - Retry script execution

5. If persistent, break script into smaller chunks
```

---

## Metadata Audit Failures

### Error: Metadata Inconsistency

**Symptoms:**
- Audit Level 1 reports errors
- Missing RDF metadata
- Orphaned quad maps

**Causes:**
1. Incomplete operations
2. Aborted transactions
3. System crash during RDF operation

**Resolution:**
```
1. Run Level 2 audit (auto-repair):
   {Server}:RDF_AUDIT_METADATA({
     audit_level: 2,
     format: "json"
   })

2. Review results:
   - Check "repaired" count
   - Note any unresolved issues

3. If issues remain, run Level 3:
   {Server}:RDF_AUDIT_METADATA({
     audit_level: 3,
     format: "json"
   })

4. Manual verification:
   SELECT * FROM DB.DBA.RDF_QUAD 
   WHERE G = iri_to_id('[graph_iri]')
   LIMIT 100;

5. If still broken, consider:
   - Backup database
   - Drop and recreate RDF Views
   - Restore from backup if needed
```

---

## Query Execution Issues

### Error: Query Timeout

**Symptoms:**
- "Timeout expired"
- "Query execution took too long"
- No response after [timeout] seconds

**Causes:**
1. Complex query
2. Large dataset
3. Missing indexes
4. Resource constraints

**Resolution:**
```
1. Increase timeout:
   {Server}:execute_spasql_query({
     sql: "[query]",
     timeout: 60000  // Try 60 seconds
   })

2. Optimize query:
   - Add LIMIT clause
   - Use more specific filters
   - Break into smaller queries

3. Check indexes:
   {Server}:execute_sql_query({
     sql: "SELECT * FROM SYS_KEYS WHERE KEY_TABLE = 'Demo.demo.Customers'",
     format: "markdown"
   })

4. Monitor resources:
   {Server}:execute_sql_query({
     sql: "status()",
     format: "markdown"
   })
```

---

### Error: Empty Result Set

**Symptoms:**
- Query returns no results
- "0 rows returned"
- Expected data missing

**Causes:**
1. Wrong graph IRI
2. Data not loaded
3. Incorrect SPARQL syntax
4. Filters too restrictive

**Resolution:**
```
1. Verify graph exists:
   {Server}:sparqlQuery({
     query: "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g",
     format: "markdown"
   })

2. Count triples:
   {Server}:sparqlQuery({
     query: "SELECT COUNT(*) as ?count FROM <[graph_iri]> WHERE { ?s ?p ?o }",
     format: "markdown"
   })

3. Test basic query:
   {Server}:sparqlQuery({
     query: "SELECT * FROM <[graph_iri]> WHERE { ?s ?p ?o } LIMIT 10",
     format: "markdown"
   })

4. Check quad map:
   {Server}:sparqlQuery({
     query: "PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#> SELECT ?qm WHERE { ?qm a virtrdf:QuadMap } ORDER BY ?qm",
     format: "markdown"
   })
```

---

## VAD Package Issues

### Error: VAD Installation Failed

**Symptoms:**
- "VAD install failed"
- "Package [name] installation error"
- Application not accessible

**Resolution:**
```
1. Start in debug mode:
   virtuoso-t -df

2. Enable error tracing:
   {Server}:execute_sql_query({
     sql: "trace_on('errors')"
   })

3. Check VAD status:
   {Server}:execute_sql_query({
     sql: "SELECT * FROM DB.DBA.VAD_REGISTRY",
     format: "markdown"
   })

4. Check for conflicts:
   {Server}:execute_sql_query({
     sql: "SELECT * FROM DB.DBA.SYS_PROCEDURES WHERE P_NAME LIKE '[VadName]%'",
     format: "markdown"
   })

5. Reinstall VAD:
   - Uninstall: vad_uninstall('[package]')
   - Reinstall: vad_install('[package].vad')
```

---

## Performance Issues

### Slow Query Execution

**Symptoms:**
- Queries take longer than expected
- System unresponsive
- High CPU usage

**Resolution:**
```
1. Check server statistics:
   {Server}:execute_sql_query({
     sql: "status()",
     format: "markdown"
   })

2. Analyze query plan:
   {Server}:execute_sql_query({
     sql: "EXPLAIN([your_query])",
     format: "markdown"
   })

3. Check locks:
   {Server}:execute_sql_query({
     sql: "SELECT * FROM SYS_L_STAT",
     format: "markdown"
   })

4. Optimize configuration:
   - Increase NumberOfBuffers
   - Adjust MaxCheckpointRemap
   - Enable parallel query execution

5. Add indexes if needed:
   CREATE INDEX [name] ON [table]([column])
```

---

### Memory Issues

**Symptoms:**
- "Out of memory" errors
- Server crashes
- Slow performance

**Resolution:**
```
1. Check memory usage:
   {Server}:execute_sql_query({
     sql: "status('c')",
     format: "markdown"
   })

2. Review configuration:
   - NumberOfBuffers (increase if possible)
   - MaxDirtyBuffers
   - ThreadsPerQuery

3. Clear caches:
   {Server}:execute_sql_query({
     sql: "__dbf_set('dc_batch_sz', 1)"
   })

4. Checkpoint database:
   {Server}:execute_sql_query({
     sql: "checkpoint"
   })

5. Consider:
   - Upgrading hardware
   - Optimizing queries
   - Archiving old data
```

---

## Connection Issues

### Cannot Connect to Instance

**Symptoms:**
- "Connection refused"
- "No route to host"
- Timeout on connection

**Resolution:**
```
1. Verify instance is running:
   - Check process: ps aux | grep virtuoso
   - Check port: netstat -an | grep 1111

2. Test connectivity:
   - Demo: telnet demo.host 1111
   - URIBurner: telnet uriburner.host 1111

3. Check firewall:
   - Ensure port 1111 (SQL) open
   - Ensure port 8890 (HTTP) open

4. Verify credentials:
   - Default: dba/dba
   - Check if password changed

5. Check virtuoso.ini:
   - ServerPort setting
   - Listen address (0.0.0.0 vs localhost)
```

---

## Data Integrity Issues

### Missing Triples After Sync

**Symptoms:**
- Physical graph incomplete
- Some data missing after sync
- Count mismatch between virtual and physical

**Resolution:**
```
1. Compare counts:
   -- Virtual
   {Server}:sparqlQuery({
     query: "SELECT COUNT(*) FROM <virtual_graph> WHERE { ?s ?p ?o }"
   })
   
   -- Physical  
   {Server}:sparqlQuery({
     query: "SELECT COUNT(*) FROM <physical_graph> WHERE { ?s ?p ?o }"
   })

2. Re-sync with load_data=1:
   {Server}:RDFVIEW_SYNC_TO_PHYSICAL_STORE({
     source_virtual_graph_iri: "virtual_graph",
     target_physical_graph_iri: "physical_graph",
     load_data: 1
   })

3. Check for errors during sync

4. Verify source data:
   {Server}:execute_sql_query({
     sql: "SELECT COUNT(*) FROM [source_table]"
   })
```

---

## Diagnostic Commands

### System Health Check

```sql
-- Server status
status();

-- Check disk usage
SELECT * FROM SYS_STAT WHERE STAT_NAME LIKE '%disk%';

-- Check memory
SELECT * FROM SYS_STAT WHERE STAT_NAME LIKE '%memory%';

-- Check threads
SELECT * FROM SYS_STAT WHERE STAT_NAME LIKE '%thread%';

-- Check locks
SELECT * FROM SYS_L_STAT;

-- Check transactions
SELECT * FROM SYS_STAT WHERE STAT_NAME LIKE '%transaction%';
```

### RDF-Specific Diagnostics

```sql
-- List all graphs
SPARQL SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } };

-- Count triples per graph
SPARQL SELECT ?g COUNT(*) as ?count 
WHERE { GRAPH ?g { ?s ?p ?o } }
GROUP BY ?g
ORDER BY DESC(?count);

-- List quad maps
SPARQL 
PREFIX virtrdf: <http://www.openlinksw.com/schemas/virtrdf#>
SELECT ?qm ?table 
WHERE { 
  ?qm a virtrdf:QuadMap . 
  ?qm virtrdf:qmTableName ?table 
};

-- Check RDF metadata
SELECT * FROM DB.DBA.RDF_QUAD LIMIT 100;
```

---

## Getting Additional Help

### Information to Collect

Before escalating to human support:

1. **Error messages** - Exact text
2. **Virtuoso version** - Run: `status();`
3. **Operation being performed** - RDF Views, query, etc.
4. **Instance** - Demo or URIBurner
5. **Reproducible steps** - How to recreate issue
6. **Logs** - Server log excerpts
7. **Configuration** - Relevant INI settings

### Support Resources

- OpenLink Support: https://www.openlinksw.com/contact
- Documentation: Indexed knowledge base
- Community: OpenLink forums

---

## Prevention Best Practices

1. **Always run metadata audits** before and after operations
2. **Test with small datasets** before production
3. **Backup regularly** before major changes
4. **Monitor resources** during operations
5. **Use timeouts** appropriate for operation
6. **Verify results** after each step
7. **Keep logs** for troubleshooting
8. **Document IRIs** and configurations
