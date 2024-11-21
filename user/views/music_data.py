from django.db.models import Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from user.models import UserInfo, Music, UserMusicCount, UserSongCount, MusicSimilarity, UserSimilarity
import httpx
import os
from . import music
import time
import requests
from django.db.models import F
import datetime
from django.utils import timezone
import csv
import random
from django.db.models import F


def get_category(tag_name):
    url = "http://localhost:3000/style/list"
    response = httpx.get(url)
    data = response.json()
    data = data['data']
    for item in data:
        if item['tagName'] == tag_name:
            print(item['tagId'])
            if 'childrenTags' in item and item['childrenTags']:
                for child in item['childrenTags']:
                    print(child['tagId'], child['tagName'])


def find():
    # 找出数据库中没有，文件夹中有的歌曲
    # 1.获取数据库中的歌曲名
    # 2.获取文件夹中的歌曲名
    # 3.找出文件夹中有，数据库中没有的歌曲
    # 4.返回结果
    musics = Music.objects.all()
    music_names = [music.name for music in musics]
    # 获取文件夹中的歌曲名

    music_dir = 'E:\\media'
    music_files = os.listdir(music_dir)
    music_files = [music_file.rsplit('.', 1)[0] for music_file in music_files]
    # 找出文件夹中有，数据库中没有的歌曲
    music_files_not_in_db = [music_file for music_file in music_files if music_file not in music_names]
    # 删除这些文件
    # for music_file in music_files_not_in_db:
    #     # os.remove(f"{music_dir}\\{music_file}.mp3")
    #     # os.remove(f"{music_dir}\\{music_file}.txt")
    #     os.remove(f"{music_dir}\\{music_file}.mp3")
    print(music_files_not_in_db)
    # 找出数据库中有，文件夹中没有的歌曲
    music_files_not_in_folder = [music_name for music_name in music_names if music_name not in music_files]
    print(music_files_not_in_folder)


def img(song_id, save_path):
    url = f"http://localhost:3000/song/detail?ids={song_id}"
    response = requests.get(url)
    data = response.json()
    pic_url = data['songs'][0]['al']['picUrl']
    print(f"Img URL: {pic_url}")
    try:
        # Check if the request was successful
        with httpx.stream("GET", pic_url) as response:
            # Open the output file in binary mode
            with open(save_path, 'wb') as file:
                # Write the response content to the file
                for chunk in response.iter_bytes():
                    file.write(chunk)

    except Exception as e:
        print(f"Error writing to file: {e}")


def lrc(song_id, save_path):
    url = f"http://localhost:3000/lyric?id={song_id}"
    print(f"Lrc URL: {url}")
    response = httpx.get(url)
    data = response.json()
    lrc = data['lrc']['lyric']
    try:
        with open(save_path, "w", encoding='utf-8') as file:
            file.write(lrc)
    except Exception as e:
        print(f"Error writing to file: {e}")

    # 现在你可以将处理后的歌词显示在网页上


# 根据获取的歌曲id下载歌曲
def download_song(song_id, save_path):
    # url = f"http://localhost:3000/song/url/v1?id={song_id}&level=standard"
    url = f"http://localhost:3000/song/url?id={song_id}"
    response = requests.get(url)
    data = response.json()
    print(data)
    song_url = data['data'][0]['url']
    print(f"download URL: {song_url}")
    # Send a GET request to the song URL with streaming enabled
    with httpx.stream("GET", song_url) as response:
        # Open the output file in binary mode
        with open(save_path, "wb") as file:
            # Write the response content to the file
            for chunk in response.iter_bytes():
                file.write(chunk)


# 寻找歌曲并下载
def fetch_data(request):
    # url = "http://localhost:3000/playlist/track/all?id=371473921&limit=100&offset=0"
    url = "http://localhost:3000/style/song?tagId=1153&size=300"
    response = httpx.get(url)
    data = response.json()
    # songs = data['songs']
    i = 0
    songs = data['data']['songs']
    for song in songs:

        try:
            print('11')
            song_name = song['name']
            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                song_name = song_name.replace(char, '')
            song_id = song['id']
            artist_name = song['ar'][0]['name']
            response = httpx.get(url)
            data = response.json()
            if Music.objects.filter(name=song_name).exists():
                continue
            print(f"Song Name: {song_name.encode('utf-8').decode('utf-8')}")
            print(f"Song ID: {song_id}")
            print(f"Artist Name: {artist_name}")

            download_song(song_id, f"E:\\media\\{song_name}.mp3")
            lrc(song_id, f"E:\\lrc\\{song_name}.txt")
            img(song_id, f"E:\\img\\{song_name}.jpg")

            Music.objects.create(name=song_name, singer=artist_name, url=f"/media/{song_name}.mp3", count=0,
                                 category='electronic', lyric_url=f"/lrc/{song_name}.txt",
                                 pic_url=f"/img/{song_name}.jpg")
            i += 1
            print(i)
        except Exception as e:
            continue
    return JsonResponse(data)


def from_timestamp(unix_timestamp_in_seconds):
    epoch = datetime.datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = datetime.timedelta(seconds=unix_timestamp_in_seconds)
    return epoch + delta


def find_time():
    musics = Music.objects.all()
    for music in musics:
        if music.publish_date is None:
            song_name = music.name
            try:
                url = f"http://localhost:3000/search?keywords={song_name}"
                response = requests.get(url)
                data = response.json()
                publish_date = data["result"]["songs"][0]["album"]["publishTime"]
                unix_timestamp_in_seconds = publish_date / 1000

                # Convert the Unix timestamp to a timezone-aware datetime object
                datetime_obj = from_timestamp(unix_timestamp_in_seconds)
                # Format the datetime object to the desired format
                formatted_datetime = datetime_obj.strftime('%Y-%m-%d')
                print(f"Publish Date: {formatted_datetime}")
                Music.objects.filter(name=song_name).update(publish_date=formatted_datetime)
            except Exception as e:

                continue


def poem(request):
    # 删除id大于5的数据
    # UserInfo.objects.filter(id__gt=5).delete()
    # Department.objects.create(title='人事部')
    # Department.objects.create(title='财务部')
    # Department.objects.create(title='技术部')
    # Department.objects.create(title='销售部')
    # 根据用户名称  获取用户所在的部门
    # user=UserInfo.objects.filter(username='root').first()
    # 通过user中的department会自动关联到department表，直接获取里面的信息
    # print(user.department.title)
    # Department.objects.filter(id=5).delete()
    # UserSongCount.objects.filter(id__gt=1).delete()
    # Music.objects.filter(id__gt=2093).delete()
    # Music.objects.all().update(url=Concat(Value('E:\\media\\'), F('name'), Value('.mp3')))
    # find()
    # find_time()
    # change_name()
    read_csv()
    # music_data1()
    # 把UserSimilarity中的数据全部删除
    # UserSimilarity.objects.filter(id__gt=0).delete()
    # for i in range(1, 1040):
    #     print(i)
    #     if not UserInfo.objects.filter(id=i).exists():
    #         continue
    #     music.calculate_similarity(i)
    #    calculate_jaccard_similarity(i)
    # get_category('电子')
    # 把Music中id大于510的数据的类别改为rock
    # Music.objects.filter(id__gt=4756).update(category='hiphop')
    # for i in range(100):
    #     UserInfo.objects.create(username='1root' + str(i), password='123', phone='12345678901')
    #     print("注册成功")

    poem = "天生我材必有用，千金散尽还复来。"
    return JsonResponse({'poem': poem})


# 将C:\Users\admin\Desktop\VueStudy\Music-Recommendation-Using-Deep-Learning-master\Media_Spectogram_Images中文件的音乐名字改成音乐id

def change_name():
    musics = Music.objects.all()
    for music in musics:
        music_id = music.id
        # 找不到就说明改完了，就跳过
        if not os.path.exists(os.path.join(
                "C:\\Users\\admin\\Desktop\\VueStudy\\Music-Recommendation-Using-Deep-Learning-master\\Media_Spectogram_Images",
                music.name + ".jpg")):
            continue
        if music.id == 303 or music.id == 3373 or music.id == 888 or music.id == 413 or music.id == 3583 or music.id == 1667 or music.id == 3295 or music.id == 3409 or music.id == 4242 or music.id == 5537:
            continue
        old_name = os.path.join(
            "C:\\Users\\admin\\Desktop\\VueStudy\\Music-Recommendation-Using-Deep-Learning-master\\Media_Spectogram_Images",
            music.name + ".jpg")
        new_name = os.path.join(
            "C:\\Users\\admin\\Desktop\\VueStudy\\Music-Recommendation-Using-Deep-Learning-master\\Media_Spectogram_Images",
            str(music_id) + ".jpg")
        os.rename(old_name, new_name)


# 读取csv文件，将音乐id，相似音乐id，相似度存入数据库
def read_csv():
    with open(
            'E:\\vue_django\\Django_music\\user\\views\\recommendations11.csv',
            'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            music_id = row[0]
            similar_music_id1 = row[1]
            similarity1 = row[2]
            similar_music_id2 = row[3]
            similarity2 = row[4]
            MusicSimilarity.objects.update_or_create(music_id=music_id, rank=1,
                                                     defaults={'similar_music_id': similar_music_id1, 'similarity': similarity1})
            MusicSimilarity.objects.update_or_create(music_id=music_id, rank=2,
                                                     defaults={'similar_music_id': similar_music_id2, 'similarity': similarity2})


def music_data():
    # 假设你的用户 ID 从 1 到 100
    user_ids = range(829, 1040)

    # 获取所有的音乐种类
    music_categories = [choice[0] for choice in Music.CATEGORY_CHOICES]

    # 对每个用户，随机选择三到四个偏好的音乐种类
    user_preferences = {user_id: random.sample(music_categories, k=random.randint(3, 4)) for user_id in user_ids}

    # 对每个用户，随机选择一些歌曲并模拟听歌的行为
    for user_id in user_ids:
        if not UserInfo.objects.filter(id=user_id).exists():
            continue
        preferred_categories = user_preferences[user_id]
        for _ in range(random.randint(50, 80)):  # 每个用户随机听 30 到 50 首歌
            # 从偏好的音乐种类中随机选择一个种类
            category = random.choice(preferred_categories)
            # 从这个种类中随机选择一首歌
            music = Music.objects.filter(category=category).order_by('?').first()

            # 更新 UserSongCount
            user_song_count, created = UserSongCount.objects.get_or_create(user_id=user_id, song_name=music.name,
                                                                           defaults={'count': 1})
            if not created:
                user_song_count.count = F('count') + 1
                user_song_count.save()

            # 更新 Music
            Music.objects.filter(name=music.name).update(count=F('count') + 1)

            # 更新 UserMusicCount
            field_name = f"{music.category}_count"
            if hasattr(UserMusicCount, field_name):
                user_music_count, created = UserMusicCount.objects.get_or_create(user_id=user_id)
                if created:
                    setattr(user_music_count, field_name, 1)
                else:
                    setattr(user_music_count, field_name, F(field_name) + 1)
                user_music_count.save()


def music_data1():
    # 假设你的用户 ID 从 1 到 100
    user_ids = range(1040, 2300)

    # 从 UserMusic 模型中获取所有的音乐名称
    music_names = Music.objects.values_list('name', flat=True)

    # 对每个用户，随机选择一些歌曲并模拟听歌的行为
    for user_id in user_ids:
        print(user_id)
        # 如果没有这个id就跳过
        if not UserInfo.objects.filter(id=user_id).exists():
            continue

        for _ in range(random.randint(10, 20)):  # 每个用户随机听 30 到 50 首歌
            music_name = random.choice(music_names)  # 随机选择一首歌

            # 更新 UserSongCount
            user_song_count, created = UserSongCount.objects.get_or_create(user_id=user_id, song_name=music_name,
                                                                           defaults={'count': 1})
            if not created:
                user_song_count.count = F('count') + 1
                user_song_count.save()

            # 更新 Music
            Music.objects.filter(name=music_name).update(count=F('count') + 1)

            # 更新 UserMusicCount
            music = Music.objects.filter(name=music_name).first()
            if music is not None:
                category = music.category
                field_name = f"{category}_count"
                if hasattr(UserMusicCount, field_name):
                    user_music_count, created = UserMusicCount.objects.get_or_create(user_id=user_id)
                    if created:
                        setattr(user_music_count, field_name, 1)
                    else:
                        setattr(user_music_count, field_name, F(field_name) + 1)
                    user_music_count.save()


def calculate_jaccard_similarity(user_id):
    # 获取当前用户播放过的音乐名称
    user_songs = set(UserSongCount.objects.filter(user_id=user_id)
                     .values_list('song_name', flat=True))

    # 获取所有其他用户
    all_users = UserSongCount.objects.values('user')
    jaccard_similarity_dict = {}

    # 对每个其他用户计算杰卡德相似度
    for other_user in all_users:
        other_user_id = other_user['user']
        if other_user_id != user_id:
            other_user_songs = set(UserSongCount.objects.filter(user_id=other_user_id)
                                   .values_list('song_name', flat=True))

            # 计算交集和并集
            intersection = len(user_songs.intersection(other_user_songs))
            union = len(user_songs.union(other_user_songs))

            # 计算杰卡德相似度
            jaccard_similarity = intersection / union if union else 0
            jaccard_similarity_dict[other_user_id] = jaccard_similarity

    # 找到相似度最大的用户
    most_similar_user_id, max_similarity = max(jaccard_similarity_dict.items(), key=lambda x: x[1], default=(None, 0))

    # 存在就更新，不存在就创建相似度记录
    if most_similar_user_id:
        UserSimilarity.objects.update_or_create(
            user1_id=user_id,
            defaults={'similarity': max_similarity, 'user2_id': most_similar_user_id}
        )

    return most_similar_user_id, max_similarity
