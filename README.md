⚙️ PC Analyst Pro v4
Intelligent Diagnosis & System Maintenance Suite
🇹🇷 Türkçe
PC Analyst Pro v4, Windows sistemleri için geliştirilmiş, akıllı analiz yeteneklerine sahip çift dilli (TR/EN) bir teşhis ve bakım aracıdır. Standart sistem araçlarının aksine, sadece veri göstermekle kalmaz; çökmeleri analiz eder, donanım sıcaklıklarıyla ilişkilendirir ve teknik bilgisi olmayan kullanıcılar için anlamlı çözüm yolları sunar.

🚀 Öne Çıkan Özellikler
Akıllı Teşhis Sistemi (Intelligent Diagnosis): Mavi ekran (BSOD) raporlarını ve Event Logları analiz eder. Karmaşık hata kodlarını (0x0...) insan diline çevirir.

Sürücü Dedektifi: Çökmeye neden olan .sys veya .dll dosyalarını (örn: nvlddmkm.sys) tespit eder ve hangi donanıma (NVIDIA) ait olduğunu söyler.

Termal Korelasyon: Donanım kaynaklı çökmeleri anlık sıcaklık verileriyle karşılaştırır. Eğer işlemci >85°C ise kullanıcıyı aşırı ısınma konusunda uyarır.

Sürücü Yaşlandırma Analizi: Sistemdeki sürücülerin tarihlerini kontrol eder; 2 yıldan eski sürücüleri "Potansiyel Risk" olarak işaretler.

Bakım Araçları: Tek tıkla RAM optimizasyonu (Working Set clearing), geçici dosya temizliği ve ağ teşhisi.

Gelişmiş Arayüz: GitHub Dark temasıyla modern görünüm ve anlık dil değiştirme desteği.

🛠 Kurulum ve Çalıştırma
Gereksinimler: Python 3.10 veya üzeri gereklidir.

Kütüphaneleri Yükleyin:

PowerShell

pip install psutil pywin32 speedtest-cli pynvml
Çalıştır: Uygulamanın tüm özelliklerine (Minidump erişimi, Kayıt defteri vb.) erişebilmesi için Yönetici Olarak çalıştırılması gerekir.

PowerShell

python analyst_gui.py

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
🇺🇸 English
PC Analyst Pro v4 is a bilingual (TR/EN) Windows system diagnostic and maintenance suite equipped with intelligent analysis capabilities. Unlike standard tools, it doesn't just display raw data—it analyzes crashes, correlates them with hardware thermals, and provides meaningful remediation steps for non-technical users.

🚀 Key Features
Intelligent Diagnosis: Analyzes Blue Screen (BSOD) reports and Event Logs. Translates cryptic hex codes (0x0...) into plain English/Turkish.

Driver Detective: Identifies the specific .sys or .dll files (e.g., nvlddmkm.sys) responsible for crashes and maps them to their respective hardware (e.g., NVIDIA).

Thermal Correlation: Cross-references hardware crashes with real-time temperature logs. If CPU >85°C, it alerts the user about overheating.

Driver Aging Scan: Scans installed drivers and flags those older than 2 years as "Potential Stability Risks."

Maintenance Suite: One-click RAM optimization (Working Set clearing), temporary file cleanup, and network diagnostics.

Advanced UI: Sleek GitHub Dark themed interface with instant language switching support.

🛠 Installation & Usage
Prerequisites: Python 3.10+ is recommended.

Install Dependencies:

PowerShell

pip install psutil pywin32 speedtest-cli pynvml
Run: Must be executed As Administrator for full functionality (Access to Minidumps, Registry, and Event Logs).

PowerShell

python analyst_gui.py
📋 Dependencies / Bağımlılıklar
psutil: System utilization & process scanning.

pywin32: Accessing Windows Event Logs & Registry.

pynvml: NVIDIA GPU telemetry.

speedtest-cli: Network performance testing.

Harika bir fikir. Roadmap kısmını hem geçmiş başarılarını (versiyon gelişimini) hem de gelecekteki vizyonunu gösterecek şekilde, profesyonel bir Markdown formatında hazırladım.

Bunu doğrudan README.md dosyanın en sonuna yapıştırabilirsin:

🗺 Roadmap & Evolution / Yol Haritası ve Gelişim
📅 Version History / Versiyon Geçmişi
v1.0 — Foundation (Temeller)
EN: Basic system monitoring (CPU, RAM, Disk) using psutil. Original white Tkinter UI.

TR: psutil kullanarak temel sistem izleme (CPU, RAM, Disk). Orijinal beyaz Tkinter arayüzü.

v2.0 — Maintenance (Bakım)
EN: Added temporary file cleanup, basic ping testing, and initial BSOD code reader. Transitioned to GitHub Dark theme.

TR: Geçici dosya temizliği, temel ping testi ve ilk BSOD kod okuyucu eklendi. GitHub Dark temasına geçiş yapıldı.

v3.0 — System Engineering (Sistem Mühendisliği)
EN: Multilingual support (TR/EN). Registry-based Startup management. Windows API RAM optimization. PowerShell CIM queries integration.

TR: Çok dilli destek (TR/EN). Kayıt defteri tabanlı Başlangıç yönetimi. Windows API ile RAM optimizasyonu. PowerShell CIM sorguları entegrasyonu.

v4.0 — Intelligent Diagnosis (Mevcut Versiyon)
EN: Diagnosis Cards: Translates hex codes to plain language. Driver Detective: Regex-based .sys file identification. Thermal Correlation: Logic to link crashes with high heat. Driver Aging: Identifies drivers older than 2 years.

TR: Teşhis Kartları: Hex kodlarını halk diline çevirir. Sürücü Dedektifi: Regex ile .sys dosyası tespiti. Termal Korelasyon: Çökmeleri yüksek ısı ile ilişkilendirme. Sürücü Yaşlandırma: 2 yıldan eski sürücülerin tespiti.
