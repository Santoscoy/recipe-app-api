"""
Test for ingredients API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe,
)

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Create and return an ingredient detail URL."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="test@example.com", password="Test123"):
    """Create and return a new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientAPITests(TestCase):
    """Test unauthenticated API requests."""
    def setUp(self):
        self.client = APIClient()

    def test_authentication_required(self):
        """Test auth is required for retrieving ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITest(TestCase):
    """Test authenticated API requests."""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients."""
        Ingredient.objects.create(user=self.user, name="Ingredient1")
        Ingredient.objects.create(user=self.user, name="Ingredient2")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_limited_to_user(self):
        """Test list of ingredients is limited to authenticated user."""
        user2 = create_user(email="user2@example.com")
        Ingredient.objects.create(user=user2, name="Ingredient1")
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient2"
        )

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """Test updating an ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient 1"
        )
        payload = {"name": "New ingredient name"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredients"""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient 1"
        )

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes."""
        in1 = Ingredient.objects.create(user=self.user, name="Ingredient 1")
        in2 = Ingredient.objects.create(user=self.user, name="Ingredient 2")
        recipe = Recipe.objects.create(
            title="Simple Title Test",
            time_minutes=5,
            pirce=Decimal("4.22"),
            user=self.user,
        )
        recipe.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_unique(self):
        """test filter ingredients returns a unique list."""
        ing = Ingredient.objects.create(user=self.user, name="Ingredient 1")
        Ingredient.objects.create(user=self.user, name="Ingredient 2")
        r1 = Recipe.objects.create(
            title="Simple Title Test 1",
            time_minutes=5,
            pirce=Decimal("4.22"),
            user=self.user,
        )
        r2 = Recipe.objects.create(
            title="Simple Title Test 2",
            time_minutes=10,
            pirce=Decimal("4.32"),
            user=self.user,
        )
        r1.ingredients.add(ing)
        r2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
