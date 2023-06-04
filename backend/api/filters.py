from django_filters import filterset
from rest_framework.filters import SearchFilter

from recipes.models import Favorite, Recipe, Tag
from users.models import Subscribe, CustomUser


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilterSet(filterset.FilterSet):
    tags = filterset.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = filterset.ModelChoiceFilter(
        queryset=CustomUser.objects.all()
    )
    is_favorited = filterset.NumberFilter(method='get_is_favorited')
    is_in_shopping_cart = filterset.NumberFilter(method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and int(value) == 1:
            return queryset.filter(favorite_recipe__owner=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(cart_recipe__owner=self.request.user)
        return queryset
