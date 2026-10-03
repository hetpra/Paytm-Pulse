from tests.ext.conftest import client_for
def test_demo_status_matches_health():
 with client_for('demo') as client:
  health=client.get('/health').json();status=client.get('/status').json()
 assert status['db_mode']==health['db_mode'] and status['forecasts_ready']==health['forecasts_ready']
