from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from .models import User, Category, Post, Setting
from .serializers import UserSerializer, CategorySerializer, PostSerializer, SettingSerializer

def format_response(success, data=None, message=None, count=None):
    res = {'success': success}
    if count is not None:
        res['count'] = count
    if data is not None:
        # map 'id' to '_id' for frontend compatibility if it's a dict
        if isinstance(data, dict) and 'id' in data:
            data['_id'] = data['id']
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'id' in item:
                    item['_id'] = item['id']
        res['data'] = data
    if message is not None:
        res['message'] = message
    return res

# --- Auth ---
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    try:
        email = request.data.get('email')
        if User.objects.filter(email=email).exists():
            return Response(format_response(False, message='User already exists'), status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            data = serializer.data
            data['_id'] = user.id
            data['token'] = str(refresh.access_token)
            return Response(format_response(True, data=data), status=status.HTTP_201_CREATED)
        return Response(format_response(False, message='Invalid user data'), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email=email).first()
        
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            serializer = UserSerializer(user)
            data = serializer.data
            data['_id'] = user.id
            data['token'] = str(refresh.access_token)
            return Response(format_response(True, data=data))
        return Response(format_response(False, message='Invalid email or password'), status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    try:
        serializer = UserSerializer(request.user)
        return Response(format_response(True, data=serializer.data))
    except Exception as e:
        return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Posts ---
class PostListCreateView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        try:
            category = request.GET.get('category')
            status_filter = request.GET.get('status')
            search = request.GET.get('search')
            
            posts = Post.objects.all().order_by('-created_at')
            if category:
                posts = posts.filter(category_id=category)
            if status_filter:
                posts = posts.filter(status=status_filter)
            if search:
                posts = posts.filter(title__icontains=search)
                
            serializer = PostSerializer(posts, many=True)
            return Response(format_response(True, count=posts.count(), data=serializer.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            data = request.data.copy()
            data['author'] = request.user.id
            serializer = PostSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(format_response(True, data=serializer.data), status=status.HTTP_201_CREATED)
            return Response(format_response(False, message='Validation error'), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PostDetailView(views.APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, pk):
        try:
            post = Post.objects.filter(pk=pk).first()
            if not post:
                return Response(format_response(False, message='Post not found'), status=status.HTTP_404_NOT_FOUND)
            serializer = PostSerializer(post)
            return Response(format_response(True, data=serializer.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            post = Post.objects.filter(pk=pk).first()
            if not post:
                return Response(format_response(False, message='Post not found'), status=status.HTTP_404_NOT_FOUND)
            serializer = PostSerializer(post, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(format_response(True, data=serializer.data))
            return Response(format_response(False, message='Validation error'), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            post = Post.objects.filter(pk=pk).first()
            if not post:
                return Response(format_response(False, message='Post not found'), status=status.HTTP_404_NOT_FOUND)
            post.delete()
            return Response(format_response(True, data={}))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_post_by_slug(request, slug):
    try:
        post = Post.objects.filter(slug=slug).first()
        if not post:
            return Response(format_response(False, message='Post not found'), status=status.HTTP_404_NOT_FOUND)
        post.views += 1
        post.save()
        serializer = PostSerializer(post)
        return Response(format_response(True, data=serializer.data))
    except Exception as e:
        return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Categories ---
class CategoryListCreateView(views.APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        try:
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(format_response(True, data=serializer.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = CategorySerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(format_response(True, data=serializer.data), status=status.HTTP_201_CREATED)
            return Response(format_response(False, message='Validation error'), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryDetailView(views.APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, pk):
        try:
            category = Category.objects.filter(pk=pk).first()
            if not category:
                return Response(format_response(False, message='Category not found'), status=status.HTTP_404_NOT_FOUND)
            serializer = CategorySerializer(category)
            return Response(format_response(True, data=serializer.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            category = Category.objects.filter(pk=pk).first()
            if not category:
                return Response(format_response(False, message='Category not found'), status=status.HTTP_404_NOT_FOUND)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(format_response(True, data=serializer.data))
            return Response(format_response(False, message='Validation error'), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            category = Category.objects.filter(pk=pk).first()
            if not category:
                return Response(format_response(False, message='Category not found'), status=status.HTTP_404_NOT_FOUND)
            category.delete()
            return Response(format_response(True, data={}))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Users ---
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

class UserListView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not is_admin(request.user):
            return Response(format_response(False, message='Not authorized as admin'), status=status.HTTP_401_UNAUTHORIZED)
        try:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response(format_response(True, data=serializer.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDetailView(views.APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request, pk):
        if not is_admin(request.user):
            return Response(format_response(False, message='Not authorized as admin'), status=status.HTTP_401_UNAUTHORIZED)
        try:
            user = User.objects.filter(pk=pk).first()
            if not user:
                return Response(format_response(False, message='User not found'), status=status.HTTP_404_NOT_FOUND)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(format_response(True, data=serializer.data))
            return Response(format_response(False, message='Validation error'), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        if not is_admin(request.user):
            return Response(format_response(False, message='Not authorized as admin'), status=status.HTTP_401_UNAUTHORIZED)
        try:
            user = User.objects.filter(pk=pk).first()
            if not user:
                return Response(format_response(False, message='User not found'), status=status.HTTP_404_NOT_FOUND)
            user.delete()
            return Response(format_response(True, data={}))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Settings ---
class SettingListCreateView(views.APIView):
    def get(self, request):
        try:
            settings = Setting.objects.all()
            serializer = SettingSerializer(settings, many=True)
            return Response(format_response(True, data=serializer.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        if not is_admin(request.user):
            return Response(format_response(False, message='Not authorized as admin'), status=status.HTTP_401_UNAUTHORIZED)
        try:
            for item in request.data:
                Setting.objects.update_or_create(key=item['key'], defaults={'value': item['value']})
            return Response(format_response(True, data=request.data))
        except Exception as e:
            return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Dashboard ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard_stats(request):
    try:
        total_posts = Post.objects.count()
        total_categories = Category.objects.count()
        total_users = User.objects.count()
        total_views = sum([p.views for p in Post.objects.all()])
        
        return Response(format_response(True, data={
            'totalPosts': total_posts,
            'totalCategories': total_categories,
            'totalUsers': total_users,
            'totalViews': total_views
        }))
    except Exception as e:
        return Response(format_response(False, message=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
