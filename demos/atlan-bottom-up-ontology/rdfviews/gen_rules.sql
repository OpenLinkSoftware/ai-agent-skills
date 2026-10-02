DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_rule2',
1,
'(/[^#]*)',
vector('path'),
1,
'/sparql?query=DESCRIBE+%%3Chttp%%3A//^{URIQADefaultHost}^%U%%23this%%3E+FROM+%%3Chttp%%3A//^{URIQADefaultHost}^/DB%%23%%3E&format=%U',
vector('path', '*accept*'),
null,
'(text/rdf.n3)|(application/rdf.xml)|(text/n3)|(application/json)|(text/turtle)',
2,
null
);
DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_rule4',
1,
'/DB/stat([^#]*)',
vector('path'),
1,
'/sparql?query=DESCRIBE+%%3Chttp%%3A//^{URIQADefaultHost}^/DB/stat%%23%%3E+%%3Fo+FROM+%%3Chttp%%3A//^{URIQADefaultHost}^/DB%%23%%3E+WHERE+{+%%3Chttp%%3A//^{URIQADefaultHost}^/DB/stat%%23%%3E+%%3Fp+%%3Fo+}&format=%U',
vector('*accept*'),
null,
'(text/rdf.n3)|(application/rdf.xml)|(text/n3)|(application/json)|(text/turtle)',
2,
null
);
DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_rule6',
1,
'/DB/objects/([^#]*)',
vector('path'),
1,
'/sparql?query=DESCRIBE+%%3Chttp%%3A//^{URIQADefaultHost}^/DB/objects/%U%%3E+FROM+%%3Chttp%%3A//^{URIQADefaultHost}^/DB%%23%%3E&format=%U',
vector('path', '*accept*'),
null,
'(text/rdf.n3)|(application/rdf.xml)|(text/n3)|(application/json)|(text/turtle)',
2,
null
);
DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_rule1',
1,
'([^#]*)',
vector('path'),
1,
'/describe/?url=http%%3A//^{URIQADefaultHost}^%U%%23this&graph=http%%3A//^{URIQADefaultHost}^/DB%%23&distinct=0',
vector('path'),
null,
null,
2,
303
);
DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_rule7',
1,
'/DB/stat([^#]*)',
vector('path'),
1,
'/describe/?url=http%%3A//^{URIQADefaultHost}^/DB/stat%%23&graph=http%%3A//^{URIQADefaultHost}^/DB%%23',
vector('path'),
null,
null,
2,
303
);
DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_rule5',
1,
'/DB/objects/(.*)',
vector('path'),
1,
'/services/rdf/object.binary?path=%%2FDB%%2Fobjects%%2F%U&accept=%U',
vector('path', '*accept*'),
null,
null,
2,
null
);
DB.DBA.URLREWRITE_CREATE_RULELIST ( 'db_rule_list1', 1, vector ( 'db_rule1', 'db_rule7', 'db_rule5', 'db_rule2', 'db_rule4', 'db_rule6'));
DB.DBA.VHOST_REMOVE (lpath=>'/DB');
DB.DBA.VHOST_DEFINE (lpath=>'/DB', ppath=>'/', vsp_user=>'dba', is_dav=>0,
is_brws=>0, opts=>vector ('url_rewrite', 'db_rule_list1')
);DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_owl_rule2',
1,
'(/[^#]*)',
vector('path'),
1,
'/sparql?query=DESCRIBE+%%3Chttp%%3A//^{URIQADefaultHost}^%U%%3E+FROM+%%3Chttp%%3A//^{URIQADefaultHost}^/schemas/DB%%23%%3E&format=%U',
vector('path', '*accept*'),
null,
'(text/rdf.n3)|(application/rdf.xml)|(text/n3)|(application/json)|(text/turtle)',
2,
null
);
DB.DBA.URLREWRITE_CREATE_REGEX_RULE (
'db_owl_rule1',
1,
'([^#]*)',
vector('path'),
1,
'/describe/?url=http://^{URIQADefaultHost}^%U',
vector('path'),
null,
null,
2,
303
);
DB.DBA.URLREWRITE_CREATE_RULELIST ( 'db_owl_rule_list1', 1, vector ( 'db_owl_rule1', 'db_owl_rule2'));
DB.DBA.VHOST_REMOVE (lpath=>'/schemas/DB');
DB.DBA.VHOST_DEFINE (lpath=>'/schemas/DB', ppath=>'/', vsp_user=>'dba', is_dav=>0,
is_brws=>0, opts=>vector ('url_rewrite', 'db_owl_rule_list1')
);
