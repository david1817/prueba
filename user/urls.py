from django.urls import path, include
from rest_framework import routers

from user.api import UserViewSet
from .views import ask, create_user, insurance, insurance_delete, insurance_list, report, update_user, find_user, login, recovery_user, recovery_token_user, \
    recovery_user_with_login, comments_phone, comments_ask, frequent_questions_list, frequent_questions_create_update, \
    feed_back_create, notification_create, notification_list, notification_disabling, notification_disabling_unique, \
    comments_all, comments_modify, color_web

router = routers.DefaultRouter()

router.register('api/user', UserViewSet, 'user')

urlpatterns = [
    path('', include(router.urls)),  # Incluye las rutas del router
    path('api/ask', ask, name='chatgpt'),
    path('api/user/create', create_user, name='create_user'),
    path('api/user/find', find_user, name='find_user'),
    path('api/user/update', update_user, name='update_user'),
    path('api/user/recovery', recovery_user, name='recovery_user'),
    path('api/login', login, name='login'),
    path('api/user/recovery/password', recovery_token_user, name='recovery_token_user'),
    path('api/user/recovery/password/authenticated', recovery_user_with_login, name='recovery_user_with_login'),
    path('api/user/comments/email', comments_ask, name='comments_email'),
    path('api/user/comments/phone', comments_phone, name='comments_phone'),
    path('api/frequent/questions/list', frequent_questions_list, name='frequent_questions_list'),
    path('api/frequent/questions/create/update', frequent_questions_create_update,
         name='frequent_questions_create_update'),
    path('api/feedback/create', feed_back_create, name='feed_back_create'),
    path('api/notification/create', notification_create, name='notification_create'),
    path('api/notification/list', notification_list, name='notification_create'),
    path('api/notification/disabling/user', notification_disabling, name='notification_create'),
    path('api/notification/seen-at', notification_disabling_unique, name='notification_create'),
    path('api/comments/list', comments_all, name='notification_create'),
    path('api/comments/modify', comments_modify, name='notification_create'),
    path('api/color/web', color_web, name='change_color_web'),
    path('api/document/insurance/create', insurance, name='insurance'),
    path('api/document/insurance/list', insurance_list, name='insurance'),
    path('api/document/insurance/delete', insurance_delete, name='insurance'),
    path('api/report', report, name='insurance')
]
