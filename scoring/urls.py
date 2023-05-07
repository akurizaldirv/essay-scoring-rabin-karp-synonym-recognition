from django.urls import path
from .views import *

app_name = 'scoring'

urlpatterns = [
    path('', Index, name='home'),
    path('scoring/', InputJumlahSoal, name='inputjumlahsoal'),
    path('scoring/inputsoal/', InputSoal, name='inputsoal'),
    path('scoring/inputkunci/', InputKunci, name='inputkunci'),
    path('scoring/inputjawaban/', InputJawaban, name="inputjawaban"),
    path('scoring/inputparameter/', InputParameter, name="inputparameter"),
    path('scoring/outputhasil/', OutputHasil, name="outputhasil"),
    path('multiscoring/', UploadKunci, name='uploadkunci'),
    path('multiscoring/uploadjawaban/', UploadJawaban, name='uploadjawaban'),
    path('multiscoring/inputparameter/', MultiInputParameter, name='multiinputparameter'),
    path('multiscoring/outputhasil/', MultiOutputHasil, name='multioutputhasil'),
]