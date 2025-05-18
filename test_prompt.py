#!/usr/bin/env python3
from markitdown import MarkItDown
from openai import OpenAI
import os
from dotenv import load_dotenv
import inspect

# .env dosyasından çevre değişkenlerini yükle
load_dotenv()

# OpenAI istemcisini yapılandır
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Test edilecek görüntü dosyası
image_path = "uploads/Example.png"

# MarkItDown nesnesini oluşturmadan önce kütüphaneyi analiz et
print("\nMarkItDown sınıfı parametrelerini inceliyorum...")
print(inspect.signature(MarkItDown.__init__))

# MarkItDown nesnesini özelleştirilmiş prompt ile oluştur
custom_prompt = "BU TEST PROMPTUDUR. LÜTFEN BU CÜMLEYLE BAŞLAYARAK CEVAP VER: 'Bu bir test açıklamasıdır.' Sonra resimde ne gördüğünü 5 maddede, her maddeye ★ ekleyerek listele."

print(f"\nOpenAI API Anahtarı: {'Ayarlandı' if openai_client.api_key else 'Ayarlanmadı'}")
print(f"Görüntü dosyası: {image_path}")
print(f"Özelleştirilmiş prompt: {custom_prompt}")

try:
    # Farklı parametre isimleri deneyelim
    print("\nFarklı parametre isimleri deniyorum...")

    # İlk deneme - convert metodu içinde llm_prompt parametresi geçirerek
    markitdown = MarkItDown(llm_client=openai_client, llm_model="gpt-4o")
    print("\nDeneme 1: convert metoduna llm_prompt parametresi geçiriliyor...")
    result = markitdown.convert(image_path, llm_prompt=custom_prompt)

    # Sonucu yazdır
    print("\nDÖNÜŞTÜRME SONUCU:")
    print("-" * 50)
    print(result.text_content)
    print("-" * 50)

    # Sonucu dosyaya kaydet
    output_path = "uploads/Example_test_prompt_result.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.text_content)

    print(f"\nSonuç şu dosyaya kaydedildi: {output_path}")

except Exception as e:
    print(f"HATA: {str(e)}")