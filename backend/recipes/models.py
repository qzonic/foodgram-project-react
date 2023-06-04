from django.core.validators import MinValueValidator
from colorfield.fields import ColorField
from django.db import models

from users.models import CustomUser, Subscribe


class Tag(models.Model):
    name = models.CharField(max_length=200)
    color = ColorField(default='#FF0000')
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredients'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} | {self.ingredient} | {self.amount}'


class Recipe(models.Model):
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through=RecipeIngredient,
        through_fields=('recipe', 'ingredient')
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to='recipes/'
    )
    text = models.TextField()
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return self.name


class Cart(models.Model):
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart_recipe'
    )

    def __str__(self):
        return f'{self.owner.username}|{self.recipe.name}'


class Favorite(models.Model):
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe'
    )

    def __str__(self):
        return f'{self.owner.username}|{self.recipe.name}'
