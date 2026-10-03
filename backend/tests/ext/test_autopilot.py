from tests.ext.conftest import client_for
def test_autopilot_only_approves_premium_rule():
 with client_for('autopilot') as client:
  client.put('/api/ext/autopilot/settings',json={'enabled':True,'max_order_value':50000,'max_loan_amount':50000,'critical_only':True})
  blocked=client.post('/api/ext/autopilot/run').json();assert blocked['auto_approved'] is False
  client.post('/api/demo/reset')
  client.post('/api/merchant/plan',json={'plan':'premium'})
  ok=client.post('/api/ext/autopilot/run').json()
 assert ok['auto_approved'] is True
