from django.db.transaction import atomic
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status

from recipes import models
from users.models import CustomUser, Subscribe


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Subscribe.objects.filter(user=user, following=obj).exists()
        return False


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    @atomic
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class SubscribeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='following.email', read_only=True)
    id = serializers.IntegerField(source='following.id', read_only=True)
    username = serializers.CharField(source='following.username', read_only=True)
    first_name = serializers.CharField(source='following.first_name', read_only=True)
    last_name = serializers.CharField(source='following.last_name', read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        read_only_fields = (
            'email',
            'username',
            'first_name',
            'last_name'
        )

    def validate(self, attrs):
        user = self.context.get('request').user
        following = self.context.get('following')
        if user == following:
            raise serializers.ValidationError(
                {'errors': 'Вы не можете подписаться на себя!'},
                status.HTTP_400_BAD_REQUEST
            )
        if Subscribe.objects.filter(
                user=user,
                following=following
        ).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого пользователя!'},
                status.HTTP_400_BAD_REQUEST
            )
        return attrs

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Subscribe.objects.filter(user=user, following=obj.following).exists()
        return False

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = obj.following.recipes.all()
        if recipes_limit:
            return RecipeShortSerializer(
                recipes[:int(recipes_limit)],
                many=True,
                context={'request': request}).data
        return RecipeShortSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Ingredient
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = models.RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=models.Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = models.RecipeIngredient
        fields = ('id', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    author = UserSerializer(
        read_only=True
    )
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        read_only=True,
        source='recipe.ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = models.Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return models.Favorite.objects.filter(recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return models.Cart.objects.filter(recipe=obj).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=models.Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientWriteSerializer(
        many=True,
        write_only=True,
    )
    image = Base64ImageField()

    class Meta:
        model = models.Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author'
        )

    def validate(self, obj):
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )
        for field in fields:
            if not obj.get(field):
                raise serializers.ValidationError(
                    {field: 'Обязательное поле!'}
                )
        return obj

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте ингредиенты!')
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Добавьте теги!')
        return value

    @atomic
    def tags_and_ingredients(self, recipe, ingredients, tags):
        recipe.tags.set(tags)
        for ingredient in ingredients:
            models.RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    @atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.tags_and_ingredients(recipe, ingredients, tags)
        return recipe

    @atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.tags_and_ingredients(instance, ingredients, tags)
        return super().update(instance, validated_data)


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class BaseCartFavoriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(source='recipe.cooking_time', read_only=True)


class CartSerializer(BaseCartFavoriteSerializer):

    class Meta:
        model = models.Cart
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class FavoriteSerializer(BaseCartFavoriteSerializer):

    class Meta:
        model = models.Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

