from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from .models import KunciJawaban, Siswa, JawabanSiswa
from django.templatetags.static import static
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from .forms import UploadFileForm, InputParameterForm
import time

# Import Modul used for Scroring Method
from nltk.tokenize import word_tokenize
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import pandas as pd
import json


#import stoplist dan menyimpan ke variabel stopword_list
f = default_storage.open("static/ScoringData/Modification Stoplist.txt")
stopword_list = []
for line in f:
    stripped_line = line.strip()
    line_list = stripped_line.split()
    after_decode = str(line_list[0], 'utf-8')
    stopword_list.append(after_decode)

# Memuat Kamus Sinonim dalam JSON
def load(filename):
    with default_storage.open(filename) as data_file:
        data = json.load(data_file) 
    return data

tesaurus = load("static/ScoringData/Modification Dict.json")
kataBiologi = ['populasi', 'komunitas', 'jaringan', 'individu', 'organisme']

# membuat stemmer untuk preprocessing
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Create Class for Scoring Method
class ScoringSystem:
    """docstring for ScoringSystem"""
    def __init__(self, arrKunci, arrJawaban, arrBobot, k, b, sr):
        self.arrKunci = arrKunci
        self.arrJawaban = arrJawaban
        self.arrBobot = arrBobot
        self.k = k
        self.b = b
        self.sr = sr
        self.nilaiSiswa = 0

    ### Pre-Processing
    def preprocessing(self, teks):

        # Menghapus tanda baca
        noURL = re.sub(r'http\S+', ' ', teks)
        hasilCleaning = re.sub(r'[^0-9a-zA-Z ]', ' ', noURL)

        # Case Folding
        hasilCaseFold = hasilCleaning.lower()
        
        # Tokenization
        hasilToken = word_tokenize(hasilCaseFold)
        
        # Stopwords Removal
        hasilStopword = [t for t in hasilToken if t not in stopword_list]

        # Stemming
        hasilStem = []

        for s in hasilStopword:
            hasilStem.append(stemmer.stem(s))

        return hasilStem

    def getSinonim(self, word):
        if word in tesaurus.keys():
            return tesaurus[word]['sinonim']
        else:
            return []

    def synonymExtraction(self, tokens):
        synonymDict = {}
        for token in tokens:
            if token not in synonymDict.keys() and len(self.getSinonim(token)) > 0:
                synonymDict[token] = self.getSinonim(token)
                
        return synonymDict

    def synonymRecognition(self, dict, tokens):
        for i in range(0, len(tokens)):
            if tokens[i] not in dict and tokens[i] not in kataBiologi:
                for j in dict:
                    if tokens[i] in dict[j]:
                        tokens[i] = j
                    
        
        return tokens

    def parsingKGram(self, tokens, kValue):
        hasilKGram = []
        for i in range(0, len("".join(tokens))-kValue+1):
            hasilKGram.append("".join(tokens)[i:i+kValue])
            
        return hasilKGram

    def hashFunction(self, tokens, k, b):
        # Menyimpan array Hash Value
        hashValue = []
        
        # Hashing Pertama
        hashV = 0
        for i in range(0, len(tokens[0])):
            z = ord(tokens[0][i]) * (b**(k-(i+1)))
            hashV += z
        hashValue.append(hashV)
        
        # Hashing menggunakan Rolling Hash without Modulo
        for j in range(0, len(tokens[1:])):
            z = (hashValue[j] - ord(tokens[j][0]) * b**(k-1)) * b + ord(tokens[j+1][-1:])
            hashValue.append(z)
        return hashValue

    def fingerprintExtraction(self, arr):
        return list(set(arr))

    def DiceSC(self, arr1, arr2):
        # arr1 = Kunci Jawaban
        # arr2 = Jawaban Siswa
        samePattern = []
        for i in range(0, len(arr2)):
            for j in range(0, len(arr1)):
                if arr1[j] == arr2[i]:
                    samePattern.append(arr1[j])
                        
        similarity = (2*len(samePattern))/(len(arr1) + len(arr2))
        similarity = round(similarity, 2)
        return similarity

    def penilaian(self):
        arrKunci = self.arrKunci
        arrJawaban = self.arrJawaban
        arrBobot = self.arrBobot

        k = self.k
        b = self.b
        sr = self.sr

        arrSim = []

        for i in range(0, len(arrKunci)):
            arrSim.append(self.penilaianSoal(arrKunci[i], arrJawaban[i], k, b, sr))

        self.nilaiSiswa = self.penilaianSiswa(arrSim, arrBobot)

        return arrSim, self.nilaiSiswa
        # return arrSim

    def penilaianSiswa(self, arrSim, arrBobot):
        nilaiSiswa = 0
        for i in range(0, len(arrSim)):
            nilaiSiswa += (arrSim[i]*arrBobot[i])
        nilaiSiswa = round(nilaiSiswa)
        return nilaiSiswa

    def penilaianSoal(self, kunci, jawaban, k, b, sr):
        #### Tahap preprocessingssing
        kunci = self.preprocessing(kunci)
        jawaban = self.preprocessing(jawaban)
        
        #### Tahap Synonym Recoginition
        if self.sr: #pengecekan menggunakan SR atau tidak
            kamus = self.synonymExtraction(kunci)
            jawaban = self.synonymRecognition(kamus, jawaban)
        
        #### Rabin Karp
        ## Parsing k-Gram
        kunci = self.parsingKGram(kunci, k)
        jawaban = self.parsingKGram(jawaban, k)
        
        ## Hashing
        kunci = self.hashFunction(kunci, k, b)
        jawaban = self.hashFunction(jawaban, k, b)
        
        ## Fingerptinting
        kunci = self.fingerprintExtraction(kunci)
        jawaban = self.fingerprintExtraction(jawaban)
        
        ## Dice's Similarity Coefficient
        similarity = self.DiceSC(kunci, jawaban)
        
        return similarity
       
# Create your views here.
def Index(request):
    template = loader.get_template('index.html')

    dataKunci = KunciJawaban.objects.all()
    dataJawaban = JawabanSiswa.objects.all()
    dataSiswa = Siswa.objects.all()

    dataKunci.delete()
    dataJawaban.delete()
    dataSiswa.delete()

    print(dataKunci)
    print(dataJawaban)
    print(dataSiswa)

    context = {}
    return HttpResponse(template.render(context, request))

def InputJumlahSoal(request):
    template = loader.get_template('inputjumlahsoal.html')
    context = {}

    if 'jumlahsoal' in request.session:
        del request.session['jumlahsoal']
        
    if request.method == 'POST':
        request.session['jumlahsoal'] = int(request.POST['jumlahsoal'])
        return redirect('scoring:inputsoal')
        # InputKunci(request, int(request.POST['jumlahsoal']))

    return HttpResponse(template.render(context, request))

def InputSoal(request):
    template = loader.get_template('inputsoal.html')
    jumlahsoal = request.session['jumlahsoal']

    context = {
        'range' : range(1, int(jumlahsoal)+1)
    }

    if request.method == 'POST':

        soal_list = request.POST.getlist('soal')
        bobot_list = request.POST.getlist('bobot')
        for i in range(0, len(soal_list)):
            KunciJawaban.objects.create(
                nomor = i+1,
                soal = soal_list[i],
                kunci = "",
                bobot = bobot_list[i],
            )
        return redirect("scoring:inputkunci")
        
    return HttpResponse(template.render(context, request))

def InputKunci(request):
    template = loader.get_template('inputkunci.html')
    jumlahsoal = request.session['jumlahsoal']

    context = {
        'range' : range(1, int(jumlahsoal)+1)
    }

    if request.method == 'POST':

        kuncijawaban_list = request.POST.getlist('kuncijawaban')
        for i in range(1, len(kuncijawaban_list)+1):
            data = KunciJawaban.objects.get(nomor=i)
            data.kunci = kuncijawaban_list[(i-1)]
            data.save()
        return redirect("scoring:inputjawaban")
        
    return HttpResponse(template.render(context, request))

def InputJawaban(request):
    template = loader.get_template('inputjawaban.html')
    jumlahsoal = request.session['jumlahsoal']

    context = {
        'range' :   range(1, int(jumlahsoal)+1)
    }

    if request.method == 'POST':
        nama = request.POST.get('nama')
        jawabansiswa_list = request.POST.getlist('jawabansiswa')
        jumlahsoal = request.session['jumlahsoal']
        Siswa.objects.create(
            nama = nama,
        )
        for i in range(0, jumlahsoal):
            a = Siswa.objects.get(nomor=1)
            b = KunciJawaban.objects.get(nomor=i+1)
            JawabanSiswa.objects.create(
                noSoal = b,
                noSiswa = a,
                jawaban = jawabansiswa_list[i],
            )

        return redirect("scoring:inputparameter")


    return HttpResponse(template.render(context, request))

def InputParameter(request):
    template = loader.get_template('inputparameter.html')
    dataKunci = KunciJawaban.objects.all()
    dataJawaban = JawabanSiswa.objects.all()
    siswa = Siswa.objects.get(nomor=1)
    data = []

    for x in range(0, len(dataKunci)):
        data.append([dataKunci[x].soal, dataKunci[x].kunci, dataJawaban[x].jawaban, dataKunci[x].bobot])

    form = InputParameterForm()
    context = {
        'data' : data,
        'nama' : siswa.nama,
        'form' : form,

    }

    if request.method == "POST":
        kValue = int(request.POST['kValue'])
        bValue = int(request.POST['bValue'])
        synonym = False
        if 'synonym' in request.POST:
            synonym = True

        request.session['bValue'] = bValue
        request.session['kValue'] = kValue
        request.session['synonym'] = synonym

        return redirect("scoring:outputhasil")

    return HttpResponse(template.render(context, request))

def OutputHasil(request):
    template = loader.get_template('outputhasil.html')
    
    jumlahsoal = request.session['jumlahsoal']
    kValue = request.session['kValue']
    bValue = request.session['bValue']
    synonym = request.session['synonym']

    kunci = KunciJawaban.objects.all()
    jawaban = JawabanSiswa.objects.all()
    siswa = Siswa.objects.get(nomor=1)

    dataKunci = []
    dataJawaban = []
    dataBobot = []

    for i in range(0, len(kunci)):
        dataKunci.append(kunci[i].kunci)
        dataJawaban.append(jawaban[i].jawaban)
        dataBobot.append(kunci[i].bobot)

    scoringSystem = ScoringSystem(dataKunci, dataJawaban, dataBobot, kValue, bValue, synonym)
    hasilPenilaian = scoringSystem.penilaian()

    dataSimilarity = hasilPenilaian[0]
 
    ### Mengisi Context dengan Kunci, Jawaban, Similarity, Bobot
    dataContext = []
    for i in range(0, len(dataKunci)):
        dataContext.append([dataJawaban[i], dataKunci[i], dataSimilarity[i], dataBobot[i]])


    context = {
        'range' : range(1, int(jumlahsoal)+1),

        'nama' : siswa.nama,
        'kValue' : kValue,
        'bValue' : bValue,
        'synonym' : synonym,
        'nilai' : hasilPenilaian[1],

        'data' : dataContext,
    }

    return HttpResponse(template.render(context, request))

def UploadKunci(request):
    template = loader.get_template('uploadfile.html')
    form  = UploadFileForm()
    context = {
        'heading' : 'Unggah Data Kunci Jawaban',
        'form': form,
        'error': False,
    }

    if request.method == "POST":
        form  = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Delete Existing File
            default_storage.delete("static/ScoringData/media_upload/DataKunci.xlsx")

            myfile = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save("static/scoringData/media_upload/DataKunci.xlsx", myfile)
            uploaded_file_url = fs.url(filename)

            dataKunci = pd.read_excel("static/scoringData/media_upload/DataKunci.xlsx")

            ### Cek Validasi Kolom
            a = dataKunci.columns
            b = ['Nomor', 'Soal', 'Kunci', 'Bobot']
            z = True
            for c in b:
                if c in a:
                    continue
                else:
                    z = False
            if not z:
                context['message'] = 'Mohon masukkan file dengan format yang benar'
                context['error'] = True

                return HttpResponse(template.render(context, request))


            ### Memasukkan data ke dalam Database
            for x,y in dataKunci.iterrows():
                KunciJawaban.objects.create(
                    nomor = y['Nomor'],
                    soal = y['Soal'],
                    kunci = y['Kunci'],
                    bobot = y['Bobot'],
                )

            return redirect("scoring:uploadjawaban")

        else:
            context['message'] = 'Mohon masukkan file dengan ekstensi .xlsx atau .xls'
            context['error'] = True
    return HttpResponse(template.render(context, request))

def UploadJawaban(request):
    template = loader.get_template('uploadfile.html')
    form  = UploadFileForm()
    context = {
        'heading' : 'Unggah Data Jawaban Siswa',
        'form': form,
        'error': False,
    }

    if request.method == "POST":
        form  = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():

            # Delete Existing File
            default_storage.delete("static/ScoringData/media_upload/DataJawaban.xlsx")

            myfile = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save("static/scoringData/media_upload/DataJawaban.xlsx", myfile)
            uploaded_file_url = fs.url(filename)

            dataJawaban = pd.read_excel("static/scoringData/media_upload/DataJawaban.xlsx")

            ### Cek Validasi Kolom
            a = dataJawaban.columns
            b = ['Soal 1', 'Soal 2', 'Soal 3', 'Soal 4', 'Soal 5', 'Soal 6', 'Soal 7', 'Soal 8', 'Soal 9', 'Soal 10']
            z = True
            for c in b:
                if c in a:
                    continue
                else:
                    z = False
            if not z:
                context['message'] = 'Mohon masukkan file dengan format yang benar'
                context['error'] = True

                return HttpResponse(template.render(context, request))


            ### Memasukkan data ke dalam Database
            for x,y in dataJawaban.iterrows():
                Siswa.objects.create(
                        nomor = y['No.'],
                        nama = y['Nama'],
                    )

                for i in range(1, 11):
                    a = Siswa.objects.get(nomor=y['No.'])
                    b = KunciJawaban.objects.get(nomor=i)
                    soalKe = "Soal "+ str(i)
                    JawabanSiswa.objects.create(
                            noSoal = b,
                            noSiswa = a,
                            jawaban = y[soalKe],
                        )    

            return redirect("scoring:multiinputparameter")

        else:
            context['message'] = 'Mohon masukkan file dengan ekstensi .xlsx atau .xls'
            context['error'] = True
    return HttpResponse(template.render(context, request))    

def MultiInputParameter(request):
    template = loader.get_template('multiinputparameter.html')
    dataKunci = KunciJawaban.objects.all()
    dataJawaban = JawabanSiswa.objects.all()
    siswa = Siswa.objects.all()
    data = []

    for x in range(0, len(siswa)):
        data.append(siswa[x].nama)

    form = InputParameterForm()
    context = {
        'data' : data,
        'form' : form,
    }

    if request.method == "POST":
        kValue = int(request.POST['kValue'])
        bValue = int(request.POST['bValue'])
        synonym = False
        if 'synonym' in request.POST:
            synonym = True


        request.session['bValue'] = bValue
        request.session['kValue'] = kValue
        request.session['synonym'] = synonym

        return redirect("scoring:multioutputhasil")

    return HttpResponse(template.render(context, request))

def MultiOutputHasil(request):
    template = loader.get_template('multioutputhasil.html')
    dataContext = []

    kValue = request.session['kValue']
    bValue = request.session['bValue']
    synonym = request.session['synonym']

    # start timer
    t0 = time.time()
    
    kunci = KunciJawaban.objects.all()
    jawaban = JawabanSiswa.objects.all()
    siswa = Siswa.objects.all()

    for i in range(1, len(siswa)+1):
        noSiswa = i
        namaSiswa = siswa.filter(nomor=i)[0].nama
        jawabanSiswa = jawaban.filter(noSiswa = noSiswa)

        dataKunci = []
        dataJawaban = []
        dataBobot = []


        for j in range(0, len(kunci)):
            dataKunci.append(kunci[j].kunci)
            dataJawaban.append(jawabanSiswa[j].jawaban)
            dataBobot.append(kunci[j].bobot)

        scoringSystem = ScoringSystem(dataKunci, dataJawaban, dataBobot, kValue, bValue, synonym)
        hasilPenilaian = scoringSystem.penilaian()

        dataContext.append([namaSiswa, hasilPenilaian[1]])


    # end timer
    t1 = time.time() - t0

    print(dataContext[0])
    context = {
        'range' : range(1, len(siswa)+1),

        'kValue' : kValue,
        'bValue' : bValue,
        'synonym' : synonym,
        'timer': t1,
        'data' : dataContext,
    }

    return HttpResponse(template.render(context, request))
