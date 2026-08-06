"""Unit tests for app.py — executed by the CI stage of the pipeline."""
import unittest

from app import app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_returns_welcome_message(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["message"], "Hello, CI/CD!")

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_add_endpoint_returns_correct_sum(self):
        response = self.client.get("/add/4/5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["result"], 9)

    def test_add_endpoint_with_negative_style_large_numbers(self):
        response = self.client.get("/add/100/250")
        self.assertEqual(response.get_json()["result"], 350)

    def test_unknown_route_returns_404(self):
        response = self.client.get("/does-not-exist")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
