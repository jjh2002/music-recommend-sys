"""
URL configuration for Django_music project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views. Home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from user.views import music, music_data, user_method

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', user_method.login),
    path('api/poem/', music_data.poem),
    path('api/poem1/', user_method.poem1),
    path('api/register/', user_method.register),
    path('api/show/', user_method.show),
    path('api/search/', user_method.search),
    path('api/update/', user_method.update),
    path('api/delete/', user_method.delete),
    path('api/add/', user_method.add),
    path('api/searchById/', user_method.search_by_id),
    path('api/listen/', music.listen),
    path('api/showByCategory/', music.show_music_by_category),
    path('api/fetch1/', music_data.fetch_data),
    path('api/lrc/', music_data.lrc),
    path('api/media/', music.musicmedia),
    path('api/searchByName/', music.search_by_name),
    path('api/recommendation/', music.recommendation),
    path('api/similar_music/', music.similar_music),
    path('api/cal', music.execute_cal),
    path('api/comment/', music.to_comment),
    path('api/showComment/', music.show_comment),
    path('api/deleteComment/', music.delete_comment),
    path('api/myMusic/', music.my_music),
    path('api/commentLike/', music.like_comment),
]
