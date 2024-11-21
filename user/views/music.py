import math
import time
from collections import defaultdict
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from user.models import UserInfo, Music, UserMusicCount, UserSongCount, UserSimilarity, MusicSimilarity, Comment, \
    CommentLike
import json
from django.db.models import F
from user.views.tools import get_page_data
from django.http import FileResponse
from concurrent.futures import ThreadPoolExecutor


def musicmedia(request):
    url = request.GET.get('url')
    # 前端传来url，根据url找到mp3文件，返回给前端
    f = open(url, 'rb')
    response = FileResponse(f)
    return response


def listen(request):
    data = request.body.decode('utf-8')
    data = json.loads(data)
    musicName = data.get('musicName')
    userId = data.get('id')

    user_song_count, created = UserSongCount.objects.get_or_create(user_id=userId, song_name=musicName,
                                                                   defaults={'count': 1})
    if not created:
        user_song_count.count = F('count') + 1
        user_song_count.save()

    Music.objects.filter(name=musicName).update(count=F('count') + 1)

    music = Music.objects.filter(name=musicName).first()
    if music is not None:
        category = music.category
        field_name = f"{category}_count"
        if hasattr(UserMusicCount, field_name):
            UserMusicCount.objects.filter(user_id=userId).update(**{field_name: F(field_name) + 1})
        else:
            print(f"Invalid field name: {field_name}")
    else:
        print(f"Music not found: {musicName}")

    return JsonResponse({'status': 'true'})


# 根据音乐种类展示音乐
def show_music_by_category(request):
    category = request.GET.get('category')
    if category == 'all':
        music_list = Music.objects.all().order_by('-count')
    else:
        music_list = Music.objects.filter(category=category).order_by('id')
    # pattern = '|'.join(username)
    # 匹配含有username中任一子串的字符串
    # all_users = UserInfo.objects.filter(username__regex=pattern)
    page = request.GET.get('page')
    size = request.GET.get('size')
    data_list, count = get_page_data(music_list, page, size)
    return JsonResponse({'data': data_list, 'count': count}, safe=False)


def search_by_name(request):
    music_name = request.GET.get('musicName')
    category = request.GET.get('category')
    # 如果category为空，就搜索所有的
    all_musics = Music.objects.filter(name__icontains=music_name).order_by('id')
    if category != 'all':
        all_musics = all_musics.filter(category=category)
    # pattern = '|'.join(username)
    # 匹配含有username中任一子串的字符串
    # all_users = UserInfo.objects.filter(username__regex=pattern)
    page = request.GET.get('page')
    size = request.GET.get('size')
    data_list, count = get_page_data(all_musics, page, size)
    print(data_list, count)
    return JsonResponse({'data': data_list, 'count': count}, safe=False)


def recommendation(request):
    user_id = request.GET.get('id')
    way = request.GET.get('way')
    # 获取播放量最高的前500首歌曲

    if way == 'hot':
        music_list = Music.objects.all().order_by('-count')[:10]
    elif way == 'old':
        music_list = list(Music.objects.all().order_by('-count')[:500])
        music_list = sorted(music_list, key=lambda x: x.publish_date, reverse=False)[:10]
    elif way == 'new':
        # 在这500首歌曲中获取最新的10首歌曲
        music_list = Music.objects.all().order_by('-publish_date')[:10]
    elif way == 'personal':
        cal = 0
        # 获取用户听过歌曲种类的数量，与其他用户听过歌曲种类数量进行余弦相似计算，记录在相似度表中
        # 获取与当前用户最相似的用户，获取其听过的歌曲种类，推荐给当前用户
        user_music_count = UserMusicCount.objects.filter(user_id=user_id).first()
        if user_music_count is None:
            # 获取最热的三首歌曲
            music_list = Music.objects.all().order_by('-count')[:3]
            data_list, count = get_page_data(music_list, 1, 10)
            return JsonResponse({'data': data_list}, safe=False)
        similar_user_id = UserSimilarity.objects.filter(user1_id=user_id).order_by('-similarity').first().user2_id
        if similar_user_id is None:
            # 获取最热的三首歌曲

            music_list = Music.objects.all().order_by('-count')[:3]
            data_list, count = get_page_data(music_list, 1, 10)
            # 向前端返回数据
            cal = 1
            return JsonResponse({'data': data_list, 'cal': cal}, safe=False)
        music_list = UserSongCount.objects.filter(user_id=similar_user_id).order_by('-count')[:3]
        # 根据找到的音乐id，获取音乐信息
        music_list = [Music.objects.filter(name=music.song_name).first() for music in music_list]
        cal = 1
        data_list, count = get_page_data(music_list, 1, 10)
        print('123')

        return JsonResponse({'data': data_list, 'cal': cal}, safe=False)

    data_list, count = get_page_data(music_list, 1, 10)
    print(data_list)
    return JsonResponse({'data': data_list}, safe=False)


def execute_cal(request):
    user_id = request.GET.get(id)
    with ThreadPoolExecutor(max_workers=1) as executor:
        # 在后台开始计算相似度并更新数据库
        executor.submit(calculate_similarity, user_id)
    return JsonResponse({})


def calculate_similarity(user_id):
    user_music_count = UserMusicCount.objects.filter(user_id=user_id).first()
    user_music_count = model_to_dict(user_music_count)

    # 获取所有用户的音乐播放统计数据
    all_user_music_count = UserMusicCount.objects.all()

    # 计算IDF值
    total_users = UserMusicCount.objects.count()  # 用户总数
    genre_play_counts = defaultdict(int)  # 统计每个音乐种类的总播放次数

    for user_counts in all_user_music_count:
        user_counts_dict = model_to_dict(user_counts)
        for genre, count in user_counts_dict.items():
            if genre not in ['id', 'user']:
                genre_play_counts[genre] += count

    # 计算每个音乐种类的IDF值
    idf_values = {genre: math.log(total_users / (1.0 + play_count)) for genre, play_count in genre_play_counts.items()}

    # 使用字典存储每个用户的相似度
    similarity_dict = {}

    for other_user in all_user_music_count.exclude(user_id=user_id):
        other_user_dict = model_to_dict(other_user)

        # 应用TF-IDF转换
        tfidf_user = [count * idf_values.get(genre, 0) for genre, count in user_music_count.items() if
                      genre not in ['id', 'user']]
        tfidf_other = [count * idf_values.get(genre, 0) for genre, count in other_user_dict.items() if
                       genre not in ['id', 'user']]

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(tfidf_user, tfidf_other))
        magnitude_user = math.sqrt(sum(a ** 2 for a in tfidf_user))
        magnitude_other = math.sqrt(sum(b ** 2 for b in tfidf_other))
        denominator = magnitude_user * magnitude_other

        similarity = dot_product / denominator if denominator != 0 else 0
        similarity_dict[other_user_dict['user']] = similarity

    # 找到相似度最大的用户
    most_similar_user_id = max(similarity_dict, key=similarity_dict.get) if similarity_dict else None
    max_similarity = similarity_dict[most_similar_user_id] if most_similar_user_id is not None else 0

    # 更新数据库
    old_record = UserSimilarity.objects.filter(user1_id=user_id).first()
    UserSimilarity.objects.update_or_create(
        user1_id=user_id,
        defaults={
            'similarity': round(max_similarity, 5),
            'user2_id': most_similar_user_id
        }
    )

    # 如果最相似用户改变了，输出旧的和新的用户ID
    if old_record and old_record.user2_id != most_similar_user_id:
        print(
            f"User {user_id} updated: Old most similar user was {old_record.user2_id}, new is {most_similar_user_id}.")


# 获取相似音乐
def similar_music(request):
    music_id = request.GET.get('musicId')
    print(music_id, 'music_id')
    similar_musics = MusicSimilarity.objects.filter(music_id=music_id).order_by('-similarity')
    similar_musics = [Music.objects.filter(id=similar_music.similar_music_id).first() for similar_music in
                      similar_musics]
    data_list = [model_to_dict(similar_music) for similar_music in similar_musics]
    print(data_list, 'similar_musics')
    return JsonResponse({'data': data_list}, safe=False)


def to_comment(requset):
    data = requset.body.decode('utf-8')
    data = json.loads(data)
    musicId = data.get('musicId')
    comment = data.get('comment')
    userId = data.get('userId')
    print(musicId, comment, userId)
    Comment.objects.create(user_id=userId, music_id=musicId, content=comment)
    return JsonResponse({'status': 'success'})


def show_comment(request):
    musicId = request.GET.get('musicId')
    userId = request.GET.get('userId')
    comments = Comment.objects.filter(music_id=musicId).select_related('user')
    data_list = []

    for comment in comments:
        comment_like_query = CommentLike.objects.filter(user_id=userId, comment_id=comment.id)
        is_liked = comment_like_query.first().is_liked if comment_like_query.exists() else None
        data_list.append({
            'id': comment.id,
            'content': comment.content,
            'username': comment.user.username,
            'music': comment.music_id,
            'user': comment.user_id,
            'time': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'count': comment.like_count,
            'is_liked': is_liked,
        })
    print(data_list)
    return JsonResponse({'data': data_list}, safe=False)


def delete_comment(request):
    data = request.body.decode('utf-8')
    data = json.loads(data)
    id = data.get('commentId')
    Comment.objects.filter(id=id).delete()
    return JsonResponse({'status': 'success'})


def my_music(request):
    user_id = request.GET.get('id')
    # 当前页和页大小
    page = request.GET.get('page')
    size = request.GET.get('size')
    print(user_id)
    count_list = UserSongCount.objects.filter(user_id=user_id).order_by('-count')
    # 查询用户听歌次数，同时获取关联的音乐信息
    music_list = []
    # 构建要返回的音乐列表及其听歌次数
    count_list, count = get_page_data(count_list, page, size)
    # 对于UserSongCount中每条记录，根据song_name查找对应的Music记录
    for user_song_count in count_list:
        try:
            # 尝试根据音乐名获取Music对象
            print(user_song_count)
            music = Music.objects.get(name=user_song_count['song_name'])
            music_list.append({
                'name': music.name,
                'singer': music.singer,
                'category': music.category,
                'count': user_song_count['count'],
                'url': music.url,
                'pic_url': music.pic_url,
                'lyric_url': music.lyric_url,
                'id': music.id
                # 可根据需要添加其他相关字段信息
            })
        except Music.DoesNotExist:
            # 如果没有找到相应的Music记录，这里可以选择如何处理
            # 例如可以跳过，或添加一个包含错误信息的字典
            continue
    return JsonResponse({'data': music_list, 'count': count}, safe=False)


def like_comment(request):
    # 从POST数据中获取用户ID和评论ID
    user_id = request.POST.get('userId')
    comment_id = request.POST.get('commentId')

    # 获取用户和评论或返回错误
    user = get_object_or_404(UserInfo, id=user_id)
    comment = get_object_or_404(Comment, id=comment_id)

    # 获取或创建点赞对象
    comment_like, created = CommentLike.objects.get_or_create(user=user, comment=comment)

    # 如果点赞已经存在，则改变状态并更新计数
    if not created:
        comment_like.is_liked = not comment_like.is_liked
        comment_like.save()
        comment.like_count = (comment.like_count + 1) if comment_like.is_liked else (comment.like_count - 1)
        comment.save()
    else:
        # 新点赞
        comment.like_count += 1
        comment.save()

    return JsonResponse({'status': 'liked' if comment_like.is_liked else 'unliked'})

