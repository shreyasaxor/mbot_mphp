from django.urls import path
from .views import *

urlpatterns = [
   path('dsvalue/',dsvalue_cosine,name='FileUpload'),
   path('config/',recommend_config,name='recommend_config'),
   path('testcase/',recommend_test,name='recommend_test'),
   path('index/',Index.as_view(),name='index'),

   path('values/',exc_values)
]