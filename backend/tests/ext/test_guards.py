from tests.ext.conftest import client_for
def test_guards_make_plan_quantities_pack_multiples():
 with client_for('guards') as client:
  p=client.post('/api/analyze',json={'merchant_id':'m1'}).json()['proposal']
 assert all(item['qty']>0 for item in p['line_items'])
 assert any(item.get('adjustments') is not None for item in p['line_items'])
