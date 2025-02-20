from django.db.models import F, Value, FloatField
from django.db.models.functions import Power, Sqrt, Sin, Cos, Radians, ATan2

def annotate_with_distance(queryset, user_latitude, user_longitude):
    R = 6371

    return queryset.annotate(
        lat_rad=Radians(F('address__latitude')),
        lon_rad=Radians(F('address__longitude')),
        user_lat_rad=Radians(Value(user_latitude)),
        user_lon_rad=Radians(Value(user_longitude)),

        delta_lat=Radians(F('address__latitude')) - Radians(Value(user_latitude)),
        delta_lon=Radians(F('address__longitude')) - Radians(Value(user_longitude)),

        a=Power(Sin(F('delta_lat') / 2), 2) +
          Cos(F('user_lat_rad')) * Cos(F('lat_rad')) *
          Power(Sin(F('delta_lon') / 2), 2),

        c=2 * ATan2(Sqrt(F('a')), Sqrt(1 - F('a'))),

        distance=R * F('c')
    )
