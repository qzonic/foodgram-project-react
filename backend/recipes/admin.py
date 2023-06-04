from django.contrib import admin

from . import models

admin.site.register(models.Tag)
admin.site.register(models.Ingredient)
admin.site.register(models.Recipe)
admin.site.register(models.RecipeIngredient)
admin.site.register(models.Cart)
admin.site.register(models.Favorite)
