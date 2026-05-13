# Nexus AI Brain (Otonom KOBİ Asistanı) 🧠

**Nexus AI Brain**, çok kiracılı (multi-tenant) B2B e-ticaret platformları için geliştirilmiş, yüksek performanslı ve otonom bir yapay zeka mikroservisidir. Asenkron **FastAPI** mimarisi üzerine inşa edilen bu katman, KOBİ'ler (SME) için 7/24 arka planda çalışan, veri analizi yapan ve doğrudan aksiyon alabilen zeki ajanlar (agents) barındırır.

⚠️ **ÖNEMLİ NOT:** Bu proje, sistemin "Zeka ve Analitik" katmanıdır. Uçtan uca çalışabilmesi için veritabanı ve arayüzü barındıran [NexusCommerce Django Ana Uygulaması](https://github.com/SerhatFiliz/multi_tenant_shop) ile birlikte çalıştırılması gerekmektedir.

---

## 📋 Ön Koşullar (Prerequisites)

Projeyi yerel ortamınızda çalıştırmak için aşağıdaki araçların kurulu olması gerekmektedir:

- **Python 3.9+**
- **Git**
- Geçerli bir **Gemini API Key** (veya desteklenen diğer LLM sağlayıcıları)
- Ana uygulamanın (Django) http://127.0.0.1:8001 portunda aktif olarak çalışıyor olması.

---

## 🚀 Adım Adım Kurulum ve Çalıştırma

### 1. Depoyu Klonlayın

Öncelikle projeyi bilgisayarınıza indirin ve proje dizinine girin:

git clone https://github.com/SerhatFiliz/autonomous-sme-assistant.git
cd autonomous-sme-assistant

### 2. Sanal Ortam (Virtual Environment) Oluşturun

Proje bağımlılıklarının sisteminizle çakışmaması için izole bir ortam oluşturun:

**Windows için:**
python -m venv venv
.\venv\Scripts\activate

**macOS/Linux için:**
python3 -m venv venv
source venv/bin/activate

### 3. Gerekli Paketleri Yükleyin

Sanal ortam aktifken requirements.txt dosyasındaki tüm kütüphaneleri kurun:

pip install -r requirements.txt

### 4. Çevresel Değişkenleri (.env) Ayarlayın

Ana dizinde .env adında bir dosya oluşturun ve içerisine yapay zeka ve haberleşme için gerekli parametreleri ekleyin:

# AI Model Configuration

GEMINI_API_KEY=sizin_api_anahtariniz_buraya

# Django Core Connection

DJANGO_API_URL=http://127.0.0.1:8001

# Application Settings

DEBUG=True
ENVIRONMENT=development

### 5. FastAPI Sunucusunu Başlatın

Tüm ayarlar tamamlandıktan sonra, sunucuyu **8002** portunda (Django ile çakışmaması için) başlatın:

uvicorn main:app --host 127.0.0.1 --port 8002 --reload

---

## 🧪 Sistemin Test Edilmesi

Sunucu başarıyla ayağa kalktığında terminalde "Application startup complete" mesajını göreceksiniz. Sistemi test etmek için:

1. **Health Check (Sistem Durumu):** Tarayıcınızdan http://127.0.0.1:8002/health adresine giderek AI beyninin canlı olup olmadığını kontrol edebilirsiniz.
2. **Swagger UI (API Dokümantasyonu):** FastAPI'nin otomatik oluşturduğu test arayüzüne ulaşmak için http://127.0.0.1:8002/docs adresine gidin. Buradan tüm endpointleri (Chat, Summary, Campaigns) doğrudan test edebilirsiniz.

---

## ✨ Temel API Uç Noktaları (Endpoints)

| HTTP Metodu | Endpoint                        | Açıklama                                                            |
| :---------- | :------------------------------ | :------------------------------------------------------------------ |
| GET         | /health                         | Mikroservisin ayakta olup olmadığını doğrular.                      |
| GET         | /api/v1/manager/summary         | Mağaza sahibine sabahları sunulacak otonom günlük özeti üretir.     |
| POST        | /api/v1/manager-advisor/chat    | B2B Yönetici Danışmanı ile doğal dilde stratejik sohbet uç noktası. |
| POST        | /api/v1/customer-assistant/chat | B2C Müşteri vitrin alışveriş asistanı sorgu noktası.                |
| GET         | /api/v1/campaigns/generate      | Veri analizi yaparak otonom indirim kampanyaları önerir.            |

---

## 📂 Proje Mimarisi

app/
├── agents/ # Otonom LLM ajanları (Fiyatlandırma, Müşteri Asistanı)
├── routers/ # API Uç Noktaları ve Yönlendirmeler
├── services/ # İş mantığı, Django köprüsü ve LLM entegrasyonları
└── main.py # FastAPI uygulama örneği (Entrypoint)
core/ # Güvenlik, CORS ve yapılandırma dosyaları
requirements.txt # Bağımlılık listesi
main.py # Uvicorn sunucu başlatıcı
