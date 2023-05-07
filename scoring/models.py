from django.db import models

# Create your models here.
class KunciJawaban(models.Model):
    nomor = models.IntegerField(primary_key=True, default=1)
    soal = models.TextField(blank=True, null=True)
    kunci = models.TextField(blank=True, null=True)
    bobot = models.IntegerField()

    def __str__(self):
        return "{}".format(self.nomor)

class Siswa(models.Model):
    nomor = models.IntegerField(primary_key=True, default=1)
    nama = models.TextField(blank=True, null=True)
    nilai = models.IntegerField(default=0)

    def __str__(self):
        return "{}. {}".format(self.nomor, self.nama)


class JawabanSiswa(models.Model):
    noSoal = models.ForeignKey(to=KunciJawaban, on_delete=models.CASCADE)
    noSiswa = models.ForeignKey(to=Siswa, on_delete=models.CASCADE)
    jawaban = models.TextField(blank=True, null=True)

    def __str__(self):
        return "{} (Soal {}, Siswa {})".format(self.id, self.noSoal, self.noSiswa)
