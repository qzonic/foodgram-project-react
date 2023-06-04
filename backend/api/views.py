import io

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from djoser.serializers import SetPasswordSerializer
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from . import serializers, filters
from .permissions import IsAuthorAdminOrReadPermission
from .pagination import PageLimitPagination
from recipes import models
from users.models import CustomUser, Subscribe


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.UserSerializer
        return serializers.UserCreateSerializer

    @action(
        methods=['post'],
        detail=False,
        url_path='set_password',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer_class()
        return Response(serializer(request.user).data, status.HTTP_200_OK)

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscribe(self, request, pk):
        user = get_object_or_404(CustomUser, id=pk)
        if request.method == 'POST':
            serializer = serializers.SubscribeSerializer(
                data=request.data,
                context={
                    'request': request,
                    'following': user
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user, following=user)
            return Response(serializer.data, status.HTTP_201_CREATED)
        subscribe = Subscribe.objects.filter(
            user=request.user,
            following=user
        )
        if subscribe.exists():
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на этого пользователя!'},
            status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['get'],
        detail=False,
        url_path='subscriptions',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def subscriptions(self, request):
        queryset = Subscribe.objects.filter(
            user=request.user
        )
        subscribes = self.paginate_queryset(queryset)
        serializer = serializers.SubscribeSerializer(
            subscribes,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = [filters.IngredientSearchFilter]
    search_fields = ('^name',)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = models.Recipe.objects.all()
    permission_classes = [IsAuthorAdminOrReadPermission]
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilterSet

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return serializers.RecipeReadSerializer
        return serializers.RecipeWriteSerializer

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(models.Recipe, id=pk)
        if request.method == 'POST':
            if models.Cart.objects.filter(
                owner=request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Этот рецепт уже в списке покупок!'},
                    status.HTTP_400_BAD_REQUEST
                )
            serializer = serializers.CartSerializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(owner=request.user, recipe=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        cart = models.Cart.objects.filter(
                owner=request.user,
                recipe=recipe
        )
        if cart.exists():
            cart.delete()
            return Response(status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Этого рецепта не было в списке покупок!'},
            status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        url_path='favorite',
        permission_classes=[permissions.IsAuthenticated]
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(models.Recipe, id=pk)
        if request.method == 'POST':
            if models.Favorite.objects.filter(
                    owner=request.user,
                    recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Этот рецепт уже в избранном!'},
                    status.HTTP_400_BAD_REQUEST
                )
            serializer = serializers.FavoriteSerializer(
                data=request.data
            )
            serializer.save(owner=request.user, recipe=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        cart = models.Cart.objects.filter(
            owner=request.user,
            recipe=recipe
        )
        if cart.exists():
            cart.delete()
            return Response(status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Этого рецепта не было в избранном!'},
            status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['get'],
        detail=False,
        url_path='download_shopping_cart',
        permission_classes=[permissions.IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        shopping_list = models.RecipeIngredient.objects.filter(
            recipe__cart_recipe__owner=request.user
        ).values(
            'ingredient'
        ).annotate(
            total_amount=Sum('amount')
        ).values_list(
            'ingredient__name',
            'total_amount',
            'ingredient__measurement_unit')
        ingredients = []
        for ingredient in shopping_list:
            ingredients.append('{0} - {1} {2}.'.format(
                *ingredient
            ))
        text = '\n'.join(ingredients)
        buffer = io.BytesIO()
        buffer.write(bytes(text, 'utf-8'))
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename='ShoppingList.txt')
