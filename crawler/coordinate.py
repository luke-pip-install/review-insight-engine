from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="geo_app")
location = geolocator.geocode("Sydney Opera House")

if __name__ == "__main__":
    print(location.latitude, location.longitude)
