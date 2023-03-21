from django.http import HttpResponsePermanentRedirect
import logging


class RedirectToHttpMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.is_secure():
            url = request.build_absolute_uri(request.get_full_path())
            url = url.replace("https://", "http://")
            return HttpResponsePermanentRedirect(url)

        response = self.get_response(request)
        return response


import logging

class DisableLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.count = 0

    def __call__(self, request):
        self.count += 1
        if request.path == '/cr' and request.method == 'GET':
            logging.disable(logging.CRITICAL)  # Set the logger level to ERROR to disable logging

        if self.count % 10 == 0:
            print(f"TV Reload check Succes| Device : {request.META.get('REMOTE_ADDR')}")
        response = self.get_response(request)
        return response

