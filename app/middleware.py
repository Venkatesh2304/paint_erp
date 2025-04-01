import time

class DelayResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "PUT" : 
            time.sleep(0)  # Adjust this time as needed
        # Call the next middleware or view
        response = self.get_response(request)
        
        return response
