from rest_framework import serializers
from .models import User, Category, Post, Setting, ContactMessage, Subscriber, Video, EPaper

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'role', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            role=validated_data.get('role', 'editor')
        )
        return user

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    # To mimic Mongoose populate, we can return the nested object on GET, 
    # but accept ID on POST/PUT. For simplicity and exact Node.js match:
    class Meta:
        model = Post
        fields = '__all__'

    def to_representation(self, instance):
        # Match Mongoose populate behavior
        representation = super().to_representation(instance)
        representation['category'] = CategorySerializer(instance.category).data if instance.category else None
        
        # User details without password
        if instance.author:
            representation['author'] = {
                'id': instance.author.id,
                'name': instance.author.name,
                'email': instance.author.email,
                'role': instance.author.role
            }
        else:
            representation['author'] = None
            
        return representation

class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = '__all__'

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'

class SubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscriber
        fields = '__all__'

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'

class EPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = EPaper
        fields = '__all__'
