from tests.ext.conftest import client_for
def test_hardening_rate_limit_and_audit():
 with client_for('hardening') as client:
  p=None
  for _ in range(10):
   response=client.post('/api/analyze',json={'merchant_id':'m1'});assert response.status_code==200;p=response.json()['proposal']
  assert client.post('/api/analyze',json={'merchant_id':'m1'}).status_code==429
  client.post(f"/api/proposals/{p['id']}/approve")
  assert len(client.get('/api/ext/hardening/audit').json()['events'])==1
