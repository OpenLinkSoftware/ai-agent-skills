#!/usr/bin/env python3
import importlib.util, pathlib
from rdflib import Graph

p = pathlib.Path(__file__).with_name('ucp_resource_client.py')
spec = importlib.util.spec_from_file_location('client', p)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

ttl = '''@prefix schema: <https://schema.org/> .
<https://shop.example/offers/r1> a schema:Offer ;
 schema:itemOffered <https://shop.example/DAV/r1.pdf> ;
 schema:price "5.00" ; schema:priceCurrency "USD" .
<https://shop.example/DAV/r1.pdf> schema:sku "r1" .
'''
g = Graph().parse(data=ttl, format='turtle')
o = m.find_offer(g, 'https://shop.example/DAV/r1.pdf')
r = m.offer_to_record(g, o, 'https://shop.example/DAV/r1.pdf')
assert r['offer_iri'] == 'https://shop.example/offers/r1'
assert r['ucp_item_id'] == 'r1'
assert r['rdf_price'] == '5.00'
assert r['rdf_currency'] == 'USD'

direct_ttl = '''@prefix schema: <http://schema.org/> .
<https://shop.example/offers/direct> a schema:Offer ;
 schema:url <https://shop.example/DAV/direct.pdf> ; schema:sku "direct-item" .
'''
dg = Graph().parse(data=direct_ttl, format='turtle')
do = m.find_offer(dg, 'https://shop.example/DAV/direct.pdf')
dr = m.offer_to_record(dg, do, 'https://shop.example/DAV/direct.pdf')
assert dr['item_offered'] == 'https://shop.example/DAV/direct.pdf'
assert dr['ucp_item_id'] == 'direct-item'

hotpot_ttl = '''@prefix schema: <http://schema.org/> .
@prefix opllic: <http://www.openlinksw.com/ontology/licenses#> .
@prefix oplofr: <http://www.openlinksw.com/ontology/offers#> .
<http://data.example/offer/hotpot> a schema:Offer ;
 schema:itemOffered <http://data.example/license/hotpot> ;
 schema:priceSpecification <http://data.example/price/hotpot> ;
 oplofr:offerNumber "ODSQA-FA-HOTPOT-0001" .
<http://data.example/license/hotpot>
 opllic:uriParameter <https://shop.example/DAV/Proper%20Lancashire%20Hotpot.pdf> .
<http://data.example/price/hotpot>
 schema:price "2.99" ; schema:priceCurrency "USD" .
'''
hg = Graph().parse(data=hotpot_ttl, format='turtle')
ho = m.find_offer(hg, 'https://shop.example/DAV/Proper%20Lancashire%20Hotpot.pdf')
hr = m.offer_to_record(hg, ho, 'https://shop.example/DAV/Proper%20Lancashire%20Hotpot.pdf')
assert hr['offer_iri'] == 'http://data.example/offer/hotpot'
assert hr['ucp_item_id'] == 'ODSQA-FA-HOTPOT-0001'
assert hr['ucp_item_id_source'] == str(m.OPLOFR_OFFER_NUMBER)
assert hr['rdf_price'] == '2.99' and hr['rdf_currency'] == 'USD'
assert hr['price_specification'] == 'http://data.example/price/hotpot'

action_ttl = '''@prefix schema: <https://schema.org/> .
<https://shop.example/offers/action> a schema:Offer ;
 schema:itemOffered <https://shop.example/DAV/action.pdf> ;
 schema:potentialAction <https://shop.example/cart?item=https%3A%2F%2Fshop.example%2Foffers%2Faction> .
'''
ag = Graph().parse(data=action_ttl, format='turtle')
ao = m.find_offer(ag, 'https://shop.example/DAV/action.pdf')
try:
    m.offer_to_record(ag, ao, 'https://shop.example/DAV/action.pdf')
    raise AssertionError('potentialAction must remain opt-in')
except RuntimeError:
    pass
ar = m.offer_to_record(ag, ao, 'https://shop.example/DAV/action.pdf', allow_action_item_id=True)
assert ar['ucp_item_id'] == 'https://shop.example/offers/action'

class HeaderList:
    def __init__(self, values): self.values = values
    def getlist(self, name): return self.values.get(name.lower(), [])

class RawHeaders:
    def __init__(self, values): self.headers = HeaderList(values)

class AccessResponse:
    def __init__(self, status, headers=None, header_lists=None):
        self.status_code = status
        self.headers = headers or {}
        self.raw = RawHeaders(header_lists or {})

auth_401 = AccessResponse(401, {'WWW-Authenticate': 'Digest realm="dav", nonce="abc"'})
assert m.resource_access_metadata(auth_401, 'https://shop.example/DAV/r1.pdf')['state'] == 'authentication_required'
assert m.resource_access_metadata(auth_401, 'https://shop.example/DAV/r1.pdf', True)['state'] == 'authentication_failed'

granted = AccessResponse(200, {'Content-Type': 'application/pdf'})
assert m.resource_access_metadata(granted, 'https://shop.example/DAV/r1.pdf', True)['state'] == 'access_granted'

payment_header = ('Payment id="challenge-1", realm="dav", method="stripe", '
                  'intent="charge", request="eyJhbW91bnQiOiIyOTkifQ"')
payment_402 = AccessResponse(402, {
    'WWW-Authenticate': payment_header,
    'Link': '<https://shop.example/offers/r1.ttl>; rel="describedby"; type="text/turtle"',
})
payment_meta = m.resource_access_metadata(payment_402, 'https://shop.example/DAV/r1.pdf', True)
assert payment_meta['state'] == 'payment_required'
assert payment_meta['payment_challenges'][0]['method'] == 'stripe'
assert payment_meta['payment_challenges'][0]['intent'] == 'charge'
assert payment_meta['links'][0]['rels'] == ('describedby',)
assert m.resource_access_metadata(payment_402, 'https://shop.example/DAV/r1.pdf')['state'] == 'protocol_error'

bare_402 = AccessResponse(402, {})
bare_meta = m.resource_access_metadata(bare_402, 'https://shop.example/DAV/r1.pdf', True)
assert bare_meta['state'] == 'protocol_error'
assert 'lacks WWW-Authenticate' in bare_meta['protocol_errors'][0]

denied_403 = AccessResponse(403, {})
assert m.resource_access_metadata(denied_403, 'https://shop.example/DAV/r1.pdf', True)['state'] == 'access_denied'

class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): pass
    def json(self): return self.payload

class FakeSession:
    def __init__(self): self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url.endswith('/sparql'):
            return FakeResponse({'results': {'bindings': [{
                'offer': {'type': 'uri', 'value': 'https://shop.example/offers/r1'},
                'item': {'type': 'uri', 'value': 'https://shop.example/DAV/r1.pdf'},
                'itemSku': {'type': 'literal', 'value': 'r1'},
                'price': {'type': 'literal', 'value': '5.00'},
                'currency': {'type': 'literal', 'value': 'USD'},
            }]}})
        raise AssertionError('RDF dereference should not run after SPARQL match')

fs = FakeSession()
sg, so, meta = m.discover_offer(fs, 'https://shop.example/DAV/r1.pdf', rdf_url='https://shop.example/offers/r1.ttl')
assert meta['method'] == 'sparql'
assert m.offer_to_record(sg, so, 'https://shop.example/DAV/r1.pdf')['ucp_item_id'] == 'r1'
assert len(fs.calls) == 1 and fs.calls[0][0] == 'https://shop.example/sparql'

legacy_profile = {'ucp': {
    'services': {'dev.ucp.shopping': [
        {'transport': 'rest', 'endpoint': 'https://shop.example/ucp', 'version': 'v1'}]},
    'capabilities': {'dev.ucp.shopping.checkout': [{}]}}}
current_profile = {
    'ucp': {
        'version': '2026-01-11',
        'services': {'dev.ucp.shopping': {
            'version': '2026-01-11',
            'rest': {'endpoint': 'https://shop.example/ucp'}}},
        'capabilities': [{'name': 'dev.ucp.shopping.checkout', 'version': '2026-01-11'}]},
    'payment': {'handlers': [{'id': 'mock_payment_handler'}]}}

class ProfileSession:
    def __init__(self, profile): self.profile = profile
    def get(self, url, **kwargs): return FakeResponse(self.profile)

lu = m.discover_ucp(ProfileSession(legacy_profile), 'https://shop.example')
assert lu['endpoint'] == 'https://shop.example/ucp' and lu['version'] == 'v1'
cu = m.discover_ucp(ProfileSession(current_profile), 'https://shop.example')
assert cu['endpoint'] == 'https://shop.example/ucp'
assert cu['version'] == '2026-01-11'
assert cu['payment_handlers'][0]['id'] == 'mock_payment_handler'
print('ok')
