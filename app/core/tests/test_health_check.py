"""
Test for the healt check API.
"""
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    """Test the healt check API."""

    def test_health_check(self):
        """Test health chech API."""
        client = APIClient()
        url = reverse("health-check")
        res = client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
