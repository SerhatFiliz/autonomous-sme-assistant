# Nexus AI Brain (Otonom KOBİ Asistanı) 🧠

**Resmi AI Hackathon Başvurusu - Yapay Zeka Katmanı**

**Nexus AI Brain**, B2B ekosistemimizin akıllı ve karar alabilen "Beyni" olarak çalışır. Hackathon'un temel gereksinimlerini eksiksiz karşılayarak tamamen yüksek performanslı **FastAPI ve Python** mimarisiyle inşa edilmiştir. Sisteme bağlı KOBİ mağazaları için merkezi bir yapay zeka mikroservisi olarak görev yapar. Otonom karar alma, Gemini destekli çift yönlü LLM asistanları ve aksiyon odaklı B2B analitikleri sunar.

---

## 🛠️ Teknoloji Yığını (Hackathon Kurallarına Tam Uyumlu)

- **Backend Çerçevesi**: FastAPI (Asenkron Python) - _Zorunlu Hackathon Gereksinimi_
- **Yapay Zeka Motoru**: Ajan (Agentic) Mimarisi ile LLM (Gemini) Entegrasyonu
- **Veri İşleme**: Gerçek Zamanlı Doğal Dil İşleme (NLP) ve Bağlama Duyarlı RAG Mekanizmaları
- **Entegrasyon**: RESTful Webhook'lar

---

## 🎯 Hackathon Kriterleri Karşılandı: Aksiyon Alan ve Otonom AI

### 1. Müşteri İletişiminin Otomasyonu (Müşteri AI Asistanı)

Geleneksel tek tip chatbot modeli yerine **Ajan tabanlı B2C Asistanı** geliştirdik. Vitrin tarafında çalışan bu asistan, doğal dil sorgularını anlar (örn: "Bana 300 TL altında dayanıklı bir hediye bul") ve _sadece_ ilgili KOBİ'nin aktif envanteri ile fiyatlarını baz alarak izole, bağlama uygun yanıtlar üretir.

### 2. Aksiyon Alabilen Sistemler (Otonom Kampanya Yöneticisi)

**Bu sadece bilgi veren, salt okunur bir bot değildir.** Yapay zeka, yavaş satan stokları ve yaklaşan pazar trendlerini proaktif olarak analiz edip KOBİ'ye spesifik kampanyalar önerir. KOBİ yöneticisi onayladığında, AI doğrudan **fiziksel aksiyon alan** bir servisi tetikler; veritabanındaki fiyat verilerini anında değiştirir ve ana uygulamada fiyat geçmişi (price history) kayıtları oluşturur.

### 3. Analitik ve İçgörü Üretimi (Yönetici AI Danışmanı ve Özet Rapor)

- **Yapay Zeka Yönetici Özeti:** Mağaza sahibi güne başladığında, FastAPI arka planı geceki satışları, bekleyen siparişleri ve acil durumları özetleyen veriye dayalı günlük bir brifing üretir.
- **B2B Stratejik Danışman:** Sanal bir veri bilimci gibi çalışan özel bir ajan. Stok tükenme hızını ve karlılığı analiz ederek mağaza sahibine doğal dil üzerinden stratejik tavsiyeler verir.

### 4. NLP Destekli Görev Yönetimi (Duygu Analizi)

Yapay zeka, webhook'lar aracılığıyla gelen müşteri mesajlarını anlık dinler. Öfke veya aciliyet durumlarını tespit etmek için gerçek zamanlı Doğal Dil İşleme (NLP) uygular ve mesajları yönetici panelinde otomatik olarak "Acil (High Priority)" olarak etiketleyerek müşteri kaybını daha yaşanmadan önler.

---

## 📡 Temel FastAPI Servisleri (Endpoints)

AI Brain, sisteme şu aksiyon odaklı uç noktaları sağlar:

- `GET /health` - Sistem durum doğrulaması.
- `GET /api/v1/manager/summary` - Tahmine dayalı sabah yönetici özeti üretimi.
- `POST /api/v1/manager-advisor/chat` - B2B stratejik danışman LLM uç noktası.
- `POST /api/v1/customer-assistant/chat` - B2C vitrin alışveriş asistanı.
- `GET /api/v1/campaigns/generate` - Algoritmik ve AI destekli indirim kampanyası üretimi.

---

## 🔗 Proje Bağlantıları (Repositories)

- **FastAPI AI Brain (Bu Repo):** [autonomous-sme-assistant](https://github.com/SerhatFiliz/autonomous-sme-assistant)
- **Django Ana Uygulama (Arayüz & DB):** [multi_tenant_shop](https://github.com/SerhatFiliz/multi_tenant_shop)
