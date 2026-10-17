import unittest
import json
from app import app, init_db, get_db

class TestHiddenGems(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret'
        self.client = app.test_client()

    def test_routes_get(self):
        routes = ['/', '/login', '/signup', '/forgot-password', '/discover', '/map', '/finder', '/api/places']
        for r in routes:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")

    def test_auth_and_protected_routes(self):
        # Protected redirects
        for r in ['/dashboard', '/planner', '/profile', '/api/itineraries']:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 302, f"Route {r} should redirect to login")

        import time
        email = f'tester_{int(time.time())}@example.com'

        # Signup test user
        res = self.client.post('/signup', data={
            'name': 'Test User',
            'email': email,
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Now dashboard, planner, profile should work
        for r in ['/dashboard', '/planner', '/profile', '/api/itineraries']:
            res = self.client.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed when logged in: {res.status_code}")

        # Test creating a trip in planner
        res = self.client.post('/planner', data={
            'title': 'Test Mumbai Day',
            'trip_date': '2026-10-20',
            'group_size': '2',
            'budget': '1500',
            'start_location': 'Bandra',
            'notes': 'Test notes',
            'stop_name[]': ['Sewri Fort', 'Bandra Fort'],
            'stop_date[]': ['2026-10-20', '2026-10-20'],
            'start_time[]': ['07:00', '18:00'],
            'end_time[]': ['08:30', '19:30'],
            'transport[]': ['taxi', 'auto'],
            'cost[]': ['200', '150'],
            'entry_cost[]': ['0', '0'],
            'stop_notes[]': ['Flamingos', 'Sunset']
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Test Mumbai Day', res.data)

        # Test saving place
        res = self.client.post('/save-place/Sewri Fort', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Test profile post
        res = self.client.post('/profile', data={
            'name': 'Updated Tester',
            'home_location': 'Bandra West'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
