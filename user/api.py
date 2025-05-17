from rest_framework import viewsets, permissions

from user.models import User
from user.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permissions_classes = [permissions.AllowAny]
    serializer_class = UserSerializer
