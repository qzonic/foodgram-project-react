from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from recipes.models import Recipe


class FavoriteCartMixin:

    def make_response(self, request, model, serializer, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if model.objects.filter(
                    owner=request.user,
                    recipe=recipe
            ).exists():
                return Response(
                    {'errors': 'Этот объект уже есть!'},
                    status.HTTP_400_BAD_REQUEST
                )
            serializer = serializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(owner=request.user, recipe=recipe)
            return Response(serializer.data, status.HTTP_201_CREATED)
        cart = model.objects.filter(
            owner=request.user,
            recipe=recipe
        )
        if cart.exists():
            cart.delete()
            return Response(status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Этого обекта не было!'},
            status.HTTP_400_BAD_REQUEST
        )
