from django.contrib import admin
from django.utils.safestring import mark_safe

from . import models


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


class Recipe(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'recipe_image',
        'favorites_count',
        'carts_count'
    )
    list_filter = ('author', 'tags')

    def recipe_image(self, object):
        return mark_safe(f"<img src='{object.image.url}' width=100>")

    def count_recipes(self, model, object):
        return model.objects.filter(recipe=object).count()

    def favorites_count(self, object):
        return self.count_recipes(models.Favorite, object)

    def carts_count(self, object):
        return self.count_recipes(models.Favorite, object)


admin.site.register(models.Tag, TagAdmin)
admin.site.register(models.Ingredient, IngredientAdmin)
admin.site.register(models.Recipe, Recipe)
admin.site.register(models.RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(models.Cart)
admin.site.register(models.Favorite)
