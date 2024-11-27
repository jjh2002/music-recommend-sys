from django.forms import model_to_dict
from django.http import JsonResponse
from user.models import UserInfo, Music, UserMusicCount, UserSongCount
from user.views.tools import get_page_data
import json


def add(request):
    # 1.获取前端传递过来的数据
    data = request.body.decode('utf-8')
    user = json.loads(data)
    print(user)
    username = user.get('username')
    password = user.get('password')
    phone = user.get('phone')
    # 2.根据用户名查询用户是否存在
    user = UserInfo.objects.filter(username=username).first()
    # 3.如果用户存在，返回错误信息
    if user:
        return JsonResponse({'status': 'error', 'error': '用户名已存在'})
    # 4.如果用户不存在，添加用户
    UserInfo.objects.create(username=username, password=password, phone=phone)
    # 5.返回结果
    return JsonResponse({'status': 'success'})


# 删除用户
# 1.获取前端传递过来的数据
# 2.根据用户id删除用户
# 3.返回结果
def delete(request):
    # 1.获取前端传递过来的数据
    data = request.body.decode('utf-8')
    user = json.loads(data)
    id = user.get('id')
    # 2.根据用户id删除用户
    UserInfo.objects.filter(id=id).delete()
    # 3.返回结果
    return JsonResponse({'status': 'success'})


# 修改用户信息
# 1.获取前端传递过来的数据
# 2.根据用id获取用户信息
def update(request):
    # 1.获取前端传递过来的数据
    data = request.body.decode('utf-8')
    user = json.loads(data)
    id = user.get('id')
    username = user.get('username')
    password = user.get('password')
    phone = user.get('phone')
    # 2.根据用id获取用户信息
    user = UserInfo.objects.filter(id=id).first()
    # 3.修改用户信息
    user.username = username
    user.password = password
    user.phone = phone
    user.save()
    return JsonResponse({'status': 'success'})


def show(request):
    data_qs = UserInfo.objects.all().order_by('id')
    page = request.GET.get('page')
    size = request.GET.get('size')
    data_list, count = get_page_data(data_qs, page, size)
    return JsonResponse({'data': data_list, 'count': count}, safe=False)


def search(request):
    username = request.GET.get('username')
    # 匹配含有username的字符串，不区分大小写
    all_users = UserInfo.objects.filter(username__icontains=username).order_by('id')
    # pattern = '|'.join(username)
    # 匹配含有username中任一子串的字符串
    # all_users = UserInfo.objects.filter(username__regex=pattern)
    page = request.GET.get('page')
    size = request.GET.get('size')
    data_list, count = get_page_data(all_users, page, size)
    return JsonResponse({'data': data_list, 'count': count}, safe=False)


def login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'invalid json'}, status=400)
    username = data.get('userName')
    password = data.get('password')
    print(username, password)
    user = UserInfo.objects.filter(username=username, password=password).first()
    print(user)
    if user:
        user_dict = model_to_dict(user)  # 将 UserInfo 对象转换为字典
        return JsonResponse({'status': 'success', 'user': user_dict})
    print("用户名或密码错误")
    return JsonResponse({'status': 'failed'})


def search_by_id(request):
    userid = request.GET.get('id')
    print(userid)
    user = UserInfo.objects.filter(id=userid).first()
    if user:
        user_dict = model_to_dict(user)  # 将 UserInfo 对象转换为字典
        return JsonResponse({'status': 'success', 'user': user_dict})
    print("用户名或密码错误1")
    return JsonResponse({'status': 'failed'})


def poem1(request):
    global APoem
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            APoem = data.get('APoem')
            # 在这里，你可以处理诗句
            print(APoem)
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'invalid json'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)
    elif request.method == 'GET':
        return JsonResponse({'APoem': APoem})
    else:
        return JsonResponse({'status': 'invalid request method'}, status=405)


def register(request):
    # 前端获取用户名密码和手机号，实现注册功能  保存到数据库中
    # 获取前端传递过来的数据
    data = request.body.decode('utf-8')
    user = json.loads(data)
    username = user.get('username')
    password = user.get('password')
    phone = user.get('phone')
    print(username, password, phone)
    if UserInfo.objects.filter(username=username).first():
        return JsonResponse({'status': 'false'})
    else:
        UserInfo.objects.create(username=username, password=password, phone=phone)
        print("注册成功")
        return JsonResponse({'status': 'true'})

    # 新建数据
    # Department.objects.create(title='人事部')
    # Department.objects.create(title='财务部')
    # Department.objects.create(title='技术部')
    # Department.objects.create(title='销售部')
    # UserInfo.objects.create(username='root', password='123', phone='12345678901')
    # UserInfo.objects.create(username='admin', password='123', phone='12345678902')
    # UserInfo.objects.create(username='user', password='123', phone='12345678903')
    # 删除数据把名字为root的数据删除
    # UserInfo.objects.filter(username='root').delete()
    # 把Department表中的所有数据都删除
    # Department.objects.all().delete()
    # 获取所有的数据
    # all_data = UserInfo.objects.all()
    # for data in all_data:
    #     print(data.username, data.password, data.phone)
    # 获取用户名为root的数据
    # user_data = UserInfo.objects.filter(username='user').first()
    # print(user_data.username, user_data.password, user_data.phone)
    # 更新数据  把用户名为root的数据的密码改为456
    # UserInfo.objects.filter(username='user').update(password='456')
