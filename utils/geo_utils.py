from math import radians, sin, cos, sqrt, atan2

class Location:
    def __init__(self, latitude, longitude):
        self.latitude = float(latitude)
        self.longitude = float(longitude)

    def __str__(self):
        return f"Latitude: {self.latitude}, Longitude: {self.longitude}"

    @staticmethod
    def calculate_distance(start, end):
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1, lon1 = radians(start.latitude), radians(start.longitude)
        lat2, lon2 = radians(end.latitude), radians(end.longitude)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Distance in kilometers
        distance = R * c

        return distance
