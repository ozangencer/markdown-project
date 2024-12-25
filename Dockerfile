FROM python:3.13-slim

# Çalışma dizini oluştur
WORKDIR /app

# Proje dosyalarını konteynıra kopyala
COPY . /app

# Gerekli bağımlılıkları yükle
RUN pip install -r requirements.txt

# Uygulamayı başlat
CMD ["python", "app.py"]