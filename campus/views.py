from rest_framework import generics
from .models import Building
from .serializers import BuildingSerializer
from django.shortcuts import render                   
import requests 
from unimap_project import settings
from django.core.cache import cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from openrouteservice import convert # to convert the polyline geometry return by openroutesevices

ORS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"

class BuildingList(generics.ListAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    
#rendering our html file 
def campus_map_page(request):
    return render(request, "campus_map.html")


@api_view(["GET"])
def get_route(request):
    """
    handle route request between two points on the map.
    it accepts GET parameters from the front end 
    Returns:
        decodedd route coordinates
        distance in metress and 
        the time taken in min if >=60sec
    """
    start = request.GET.get("start")  # "lat,lng"
    end = request.GET.get("end")      # "lat,lng"

    if not start or not end:
        return Response({"error": "start and end parameters required"}, status=400)

    # Uses Caching to speed up repeated requests
    cache_key = f"route_{start}_{end}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    try:
        # convert incomng lat,lng to str
        start_lat, start_lng = map(float, start.split(","))
        end_lat, end_lng = map(float, end.split(","))

        payload = {
            "coordinates": [
                [start_lng, start_lat],  # ORS uses [lng, lat]
                [end_lng, end_lat]
            ]
        }

        headers = {
            "Authorization": settings.ORS_KEY,
            "Content-Type": "application/json"
        }

        ors_response = requests.post(ORS_URL, json=payload, headers=headers)

        if ors_response.status_code != 200:
            return Response({
                "error": "ORS API error",
                "details": ors_response.text
            }, status=500)

        data = ors_response.json()

        
        if "routes" not in data:
            return Response({
                "error": "Invalid ORS response",
                "details": data
            }, status=500)

        route = data["routes"][0]

        # Decode encoded polyline
        encoded = route["geometry"]
        decoded = convert.decode_polyline(encoded)  # uses openrouteservice package

        #extract distance and duration
        geometry = decoded["coordinates"]
        summary = route["summary"]
        raw_duration = summary["duration"]  
        formated = format_duration(raw_duration) #formating the duration

        result = {
            "coordinates": geometry,
            "distance": summary["distance"],
            "duration": formated
        }
    

        cache.set(cache_key, result, timeout=600) #keep the routes for 10 min

        return Response(result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


def format_duration(seconds:str):
    """ 
    convert duration in seconds into a reable format
    - 20 sec
    - 3 min 50 sec
    - 2 min
    """ 
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} sec"
    
    minutes = seconds // 60
    remaining = seconds % 60
     
    if remaining == 0:
        return f"{minutes} min"
    return f"{minutes} min {remaining} sec"

