from django.core.paginator import Paginator
from django.forms import model_to_dict


def get_page_data(queryset, page, size):
    paginator = Paginator(queryset, size)
    count = paginator.count
    data = paginator.get_page(page)
    data_list = [model_to_dict(item) for item in data]
    return data_list, count


class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response[
            "Access-Control-Allow-Headers"] = "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range"
        response["Access-Control-Expose-Headers"] = "Content-Length,Content-Range"
        return response
