import json
import requests
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth.middleware import get_user

class OPAAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.opa_url = getattr(settings, 'OPA_URL', 'http://0.0.0.0:8181/v1/data/organization/rbac/allow')

    def __call__(self, request):
        # Only process requests to opaview or projects endpoints
        path = request.path or ''
        if not (
            path.startswith('/opaview/')
            or path.startswith('/projects/')
            or path.startswith('/api/projects/')
        ):
            return self.get_response(request)

        # Skip for OPTIONS method (preflight requests)
        if request.method == 'OPTIONS':
            return self.get_response(request)

        # Check if user is authenticated by previous middlewares
        user = get_user(request)
        if not user or not user.is_authenticated:
            # Return API-shaped responses to prevent frontend crashes on unauthenticated state
            if path.startswith('/api/projects') and (request.method or '').upper() == 'GET':
                return JsonResponse({
                    "detail": "Unauthorized",
                    "results": [],
                    "count": 0,
                }, status=401)
            if path.startswith('/api/'):
                return JsonResponse({"detail": "Unauthorized"}, status=401)
            return JsonResponse({"detail": "Unauthorized"}, status=401)

        try:
            # Get request body if it exists
            if request.body:
                request_data = json.loads(request.body)
            else:
                request_data = {}
            
            username = getattr(user, 'email', None) or getattr(user, 'username', '')
            print(username)
            method = (request.method or '').upper()
            # action_map = {
            #     'GET': 'read_project',
            #     'POST': 'create_project',
            #     'PUT': 'update_project',
            #     'PATCH': 'update_project',
            #     'DELETE': 'delete_project',
            # }
      #      action = action_map.get(method, 'read_project')
            # Forward the request to OPA
            opa_payload = {
                "input": {
                    "user": username,
                    "action": "annotate_task",
                    "resource":{
                        "project_id": "project_A"
                    } # do not change this, i've hardcoded this for now
                }
            }
            # Print the exact OPA request being sent
            print(f"OPA request -> URL: {self.opa_url}, Payload: {json.dumps(opa_payload)}")
            response = requests.post(
                self.opa_url,
                json=opa_payload,
            )
            # Print response status for quick debugging
            print(f"OPA response status: {response.status_code}")
            response.raise_for_status()
            
            # Check OPA response
            opa_result = response.json()
            print(opa_result)
            if not opa_result.get('result', False):
                # Present a friendly 403 depending on API vs page request
                if path.startswith('/api/'):
                    # For list endpoints (e.g. GET /api/projects/), include results/count to avoid UI crashes
                    if path.startswith('/api/projects') and method == 'GET':
                        return JsonResponse({
                            "detail": "Forbidden",
                            "results": [],
                            "count": 0,
                        }, status=403)
                    return JsonResponse({"detail": "Forbidden"}, status=403)
                else:
                    return HttpResponseForbidden("You don't have permission to view this resource.")

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON in request body"}, 
                status=400
            )
        except requests.RequestException as e:
            return JsonResponse(
                {"error": f"Error communicating with OPA: {str(e)}"}, 
                status=502
            )

        return self.get_response(request)
