"""
PC Analyst Pro v3 — Advanced System Diagnostic & Maintenance Suite
===================================================================
pip install psutil pywin32 speedtest-cli
pip install pynvml          # optional – NVIDIA GPU temperature

Run as Administrator for full functionality.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os, re, glob, struct, threading, subprocess, time, ctypes, platform
from datetime import datetime
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

# ── psutil ────────────────────────────────────────────────────────────────────
try:    import psutil;          PSUTIL_OK = True
except ImportError:             PSUTIL_OK = False

# ── pywin32 ───────────────────────────────────────────────────────────────────
WIN32_OK = False
try:
    import win32evtlog, win32evtlogutil, win32api, win32con, win32process
    import winreg
    WIN32_OK = True
except ImportError:
    pass

# ── pynvml ────────────────────────────────────────────────────────────────────
GPU_OK = False
try:
    import pynvml; pynvml.nvmlInit(); GPU_OK = True
except Exception:
    pass

# ── speedtest-cli ─────────────────────────────────────────────────────────────
SPEED_OK = False
try:    import speedtest as _st; SPEED_OK = True
except ImportError:              pass


# ════════════════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (GitHub Dark)
# ════════════════════════════════════════════════════════════════════════════════
C = dict(bg="#0d1117", surface="#161b22", surface2="#1c2128", border="#30363d",
         blue="#58a6ff", green="#3fb950", red="#f85149",
         yellow="#e3b341", purple="#bc8cff", orange="#f0883e",
         teal="#39d353", muted="#8b949e", text="#e6edf3", white="#ffffff")

FONT_UI    = ("Segoe UI",  10, "bold")
FONT_SMALL = ("Segoe UI",   9, "bold")
FONT_MONO  = ("Consolas",   9)
FONT_H1    = ("Segoe UI",  18, "bold")
FONT_H2    = ("Segoe UI",  14, "bold")
FONT_H3    = ("Segoe UI",  11, "bold")
FONT_TINY  = ("Segoe UI",   8, "italic")


# ════════════════════════════════════════════════════════════════════════════════
#  LOCALISATION
# ════════════════════════════════════════════════════════════════════════════════
S = {
    "app_title":        {"en": "PC Analyst Pro v3 · System Engineering Suite",
                         "tr": "PC Analyst Pro v3 · Sistem Mühendisliği Paketi"},
    "header_title":     {"en": "⚙  PC ANALYST PRO",     "tr": "⚙  PC ANALİST PRO"},
    # ── tabs ─────────────────────────────────────────────────────────────────
    "tab_dash":         {"en": "  📊  Dashboard  ",      "tr": "  📊  Gösterge  "},
    "tab_analysis":     {"en": "  🔍  Analysis  ",       "tr": "  🔍  Analiz  "},
    "tab_cleanup":      {"en": "  🧹  Cleanup  ",        "tr": "  🧹  Temizlik  "},
    "tab_network":      {"en": "  🌐  Network  ",        "tr": "  🌐  Ağ  "},
    "tab_sysinfo":      {"en": "  💻  System Info  ",    "tr": "  💻  Sistem Bilgisi  "},
    "tab_startup":      {"en": "  🚀  Startup  ",        "tr": "  🚀  Başlangıç  "},
    "tab_thermal":      {"en": "  🌡  Thermal  ",        "tr": "  🌡  Isı İzleme  "},
    "tab_language":     {"en": "  🌍  Language  ",       "tr": "  🌍  Dil  "},
    # ── dashboard ─────────────────────────────────────────────────────────────
    "m_cpu":            {"en": "CPU",                    "tr": "İŞLEMCİ"},
    "m_ram":            {"en": "RAM",                    "tr": "BELLEK"},
    "m_gpu":            {"en": "GPU",                    "tr": "EKRAN KARTI"},
    "m_disk":           {"en": "DISK",                   "tr": "DİSK"},
    # ── analysis ──────────────────────────────────────────────────────────────
    "btn_quick_scan":   {"en": "⚡  Quick Scan",          "tr": "⚡  Hızlı Tarama"},
    "btn_deep_scan":    {"en": "🔬  Deep Scan",           "tr": "🔬  Derin Tarama"},
    "btn_quick_fix":    {"en": "🛠  Quick Fix Pro",        "tr": "🛠  Hızlı Düzeltme Pro"},
    "crash_history":    {"en": "Crash Report History",    "tr": "Çökme Raporu Geçmişi"},
    "crash_hint":       {"en": "Double-click a row to view diagnosis",
                         "tr": "Teşhis için satıra çift tıklayın"},
    "col_time":         {"en": "Timestamp",               "tr": "Zaman Damgası"},
    "col_code":         {"en": "Error Code",              "tr": "Hata Kodu"},
    "col_cat":          {"en": "Category",                "tr": "Kategori"},
    "col_src":          {"en": "Source",                  "tr": "Kaynak"},
    # ── cleanup ───────────────────────────────────────────────────────────────
    "cleanup_title":    {"en": "Select areas to clean:",  "tr": "Temizlenecek alanlar:"},
    "opt_temp":         {"en": "System Temp Folders",     "tr": "Sistem Geçici Klasörleri"},
    "opt_prefetch":     {"en": "Windows Prefetch",        "tr": "Windows Prefetch"},
    "opt_updates":      {"en": "Old Windows Update Cache","tr": "Eski Windows Güncelleme Önbelleği"},
    "opt_browser":      {"en": "Browser Caches (Chrome, Edge, Firefox)",
                         "tr": "Tarayıcı Önbellekleri (Chrome, Edge, Firefox)"},
    "btn_cleanup":      {"en": "🧹  Start Cleanup",       "tr": "🧹  Temizliği Başlat"},
    "btn_opt_ram":      {"en": "🚀  Optimize RAM",        "tr": "🚀  RAM'i Optimize Et"},
    # ── network ───────────────────────────────────────────────────────────────
    "btn_net_diag":     {"en": "🌐  Run Diagnostics",     "tr": "🌐  Teşhis Çalıştır"},
    "btn_speed":        {"en": "⚡  Speed Test",           "tr": "⚡  Hız Testi"},
    "net_health":       {"en": "Network Health",           "tr": "Ağ Sağlığı"},
    "net_status":       {"en": "Connection Status",        "tr": "Bağlantı Durumu"},
    "net_ping":         {"en": "Ping Latency",             "tr": "Ping Gecikmesi"},
    "net_dl":           {"en": "Download Speed",           "tr": "İndirme Hızı"},
    "net_ul":           {"en": "Upload Speed",             "tr": "Yükleme Hızı"},
    "net_dns":          {"en": "DNS Status",               "tr": "DNS Durumu"},
    # ── sysinfo ───────────────────────────────────────────────────────────────
    "si_title":         {"en": "Hardware & System Summary","tr": "Donanım & Sistem Özeti"},
    "si_os":            {"en": "Operating System",         "tr": "İşletim Sistemi"},
    "si_cpu":           {"en": "Processor",                "tr": "İşlemci"},
    "si_cores":         {"en": "Cores / Threads",          "tr": "Çekirdek / İş Parçacığı"},
    "si_ram_total":     {"en": "Total RAM",                "tr": "Toplam RAM"},
    "si_ram_avail":     {"en": "Available RAM",            "tr": "Kullanılabilir RAM"},
    "si_disk_model":    {"en": "Primary Disk",             "tr": "Birincil Disk"},
    "si_gpu":           {"en": "GPU",                      "tr": "Ekran Kartı"},
    "si_bios":          {"en": "BIOS Version",             "tr": "BIOS Sürümü"},
    "si_uptime":        {"en": "System Uptime",            "tr": "Sistem Çalışma Süresi"},
    "si_arch":          {"en": "Architecture",             "tr": "Mimari"},
    "btn_refresh_si":   {"en": "🔄  Refresh",              "tr": "🔄  Yenile"},
    # ── startup manager ───────────────────────────────────────────────────────
    "sm_title":         {"en": "Startup Applications",     "tr": "Başlangıç Uygulamaları"},
    "sm_hint":          {"en": "Select an entry and click Disable/Enable to toggle it",
                         "tr": "Bir girdi seçip Devre Dışı/Etkinleştir butonuna tıklayın"},
    "sm_col_name":      {"en": "Application Name",         "tr": "Uygulama Adı"},
    "sm_col_path":      {"en": "Executable Path",          "tr": "Çalıştırılabilir Yol"},
    "sm_col_hive":      {"en": "Registry Hive",            "tr": "Kayıt Hive"},
    "sm_col_state":     {"en": "State",                    "tr": "Durum"},
    "sm_enabled":       {"en": "✅  Enabled",               "tr": "✅  Etkin"},
    "sm_disabled":      {"en": "⛔  Disabled",              "tr": "⛔  Devre Dışı"},
    "btn_sm_refresh":   {"en": "🔄  Refresh List",          "tr": "🔄  Listeyi Yenile"},
    "btn_sm_disable":   {"en": "⛔  Disable Selected",      "tr": "⛔  Seçiliyi Devre Dışı Bırak"},
    "btn_sm_enable":    {"en": "✅  Enable Selected",        "tr": "✅  Seçiliyi Etkinleştir"},
    "sm_no_sel":        {"en": "No entry selected.",        "tr": "Seçili giriş yok."},
    "sm_no_win32":      {"en": "pywin32 required for Registry access.",
                         "tr": "Kayıt defteri erişimi için pywin32 gereklidir."},
    # ── thermal ───────────────────────────────────────────────────────────────
    "th_title":         {"en": "Thermal Monitoring",        "tr": "Isı İzleme"},
    "th_cpu_temp":      {"en": "CPU Temperature",           "tr": "İşlemci Sıcaklığı"},
    "th_gpu_temp":      {"en": "GPU Temperature",           "tr": "GPU Sıcaklığı"},
    "th_cpu_fan":       {"en": "CPU Fan Speed",             "tr": "İşlemci Fan Hızı"},
    "th_status":        {"en": "Thermal Status",            "tr": "Isıl Durum"},
    "th_normal":        {"en": "Normal 🟢",                 "tr": "Normal 🟢"},
    "th_warm":          {"en": "Warm 🟡",                   "tr": "Ilık 🟡"},
    "th_hot":           {"en": "Hot 🔴",                    "tr": "Sıcak 🔴"},
    "th_na":            {"en": "N/A — sensor not found",    "tr": "Yok — sensör bulunamadı"},
    "btn_th_refresh":   {"en": "🔄  Refresh",               "tr": "🔄  Yenile"},
    "th_hint":          {"en": "pynvml required for NVIDIA GPU temp. CPU via WMI/PowerShell.",
                         "tr": "NVIDIA GPU için pynvml gerekli. CPU sıcaklığı WMI/PowerShell."},
    # ── language ──────────────────────────────────────────────────────────────
    "lang_title":       {"en": "Interface Language",        "tr": "Arayüz Dili"},
    "lang_sub":         {"en": "Select the display language. UI updates instantly.",
                         "tr": "Görüntüleme dilini seçin. Arayüz anında güncellenir."},
    "lang_note":        {"en": "⚠  Runtime log messages appear in the language active at that moment.",
                         "tr": "⚠  Log mesajları o andaki aktif dilde görünür."},
    # ── console / export ──────────────────────────────────────────────────────
    "op_log":           {"en": "Operation Log",             "tr": "Operasyon Günlüğü"},
    "btn_export":       {"en": "📄  Export Report",         "tr": "📄  Raporu Dışa Aktar"},
    "export_title":     {"en": "Save System Report",        "tr": "Sistem Raporunu Kaydet"},
    "export_ok":        {"en": "Report Saved",              "tr": "Rapor Kaydedildi"},
    "export_ok_msg":    {"en": "Saved to:\n{}",             "tr": "Kaydedildi:\n{}"},
    "export_err":       {"en": "Export Failed",             "tr": "Dışa Aktarma Başarısız"},
    # ── crash modal ───────────────────────────────────────────────────────────
    "modal_title":      {"en": "Crash Analysis",            "tr": "Çökme Analizi"},
    "modal_code":       {"en": "Stop Code:",                "tr": "Durdurma Kodu:"},
    "modal_cat":        {"en": "Category:",                 "tr": "Kategori:"},
    "modal_time":       {"en": "Occurred:",                 "tr": "Zaman:"},
    "modal_what":       {"en": "What happened:",            "tr": "Ne oldu:"},
    "modal_fix":        {"en": "Recommended fix:",          "tr": "Önerilen çözüm:"},
    "btn_close":        {"en": "  Close  ",                 "tr": "  Kapat  "},
    # ── log messages ──────────────────────────────────────────────────────────
    "log_qs_start":     {"en": "━━━  QUICK SCAN STARTED  ━━━",     "tr": "━━━  HIZLI TARAMA BAŞLADI  ━━━"},
    "log_qs_done":      {"en": "━━━  QUICK SCAN COMPLETE  ━━━",    "tr": "━━━  HIZLI TARAMA TAMAMLANDI  ━━━"},
    "log_ds_start":     {"en": "━━━  DEEP SCAN STARTED  ━━━",      "tr": "━━━  DERİN TARAMA BAŞLADI  ━━━"},
    "log_ds_done":      {"en": "━━━  DEEP SCAN COMPLETE  ━━━",     "tr": "━━━  DERİN TARAMA TAMAMLANDI  ━━━"},
    "log_svc_check":    {"en": "Checking core services …",          "tr": "Temel servisler kontrol ediliyor …"},
    "log_running":      {"en": "running",                            "tr": "çalışıyor"},
    "log_missing":      {"en": "NOT FOUND (run as admin?)",          "tr": "BULUNAMADI (yönetici olarak mı çalıştırın?)"},
    "log_disk_u":       {"en": "Disk usage",                         "tr": "Disk kullanımı"},
    "log_used":         {"en": "used",                               "tr": "kullanılıyor"},
    "log_total":        {"en": "total",                              "tr": "toplam"},
    "log_ram_free":     {"en": "free",                               "tr": "boş"},
    "log_evtlog":       {"en": "Scanning Windows Event Logs …",      "tr": "Windows Olay Günlükleri taranıyor …"},
    "log_no_pywin32":   {"en": "  ⚠  pywin32 missing — Minidump fallback",
                         "tr": "  ⚠  pywin32 yok — Minidump taramasına geçiliyor"},
    "log_smart":        {"en": "\nQuerying disk health …",           "tr": "\nDisk sağlığı sorgulanıyor …"},
    "log_bg_proc":      {"en": "\nScanning background processes …",  "tr": "\nArka plan süreçleri taranıyor …"},
    "log_top_cpu":      {"en": "\nTop CPU-consuming processes:",     "tr": "\nEn yüksek CPU kullanan süreçler:"},
    "log_no_crash":     {"en": "No crash events — system stable.",   "tr": "Çökme olayı yok — sistem kararlı."},
    "log_evtlog_err":   {"en": "  Event log error: ",               "tr": "  Olay günlüğü hatası: "},
    "log_no_mini_dir":  {"en": "  No Minidump directory.",          "tr": "  Minidump dizini bulunamadı."},
    "log_no_dmp":       {"en": "  No .dmp files.",                  "tr": "  .dmp dosyası yok."},
    "log_perm":         {"en": "  PermissionError: run as Admin.",  "tr": "  İzin Hatası: Yönetici olarak çalıştırın."},
    "log_smart_err":    {"en": "  Disk health query failed: ",      "tr": "  Disk sağlık sorgusu başarısız: "},
    "log_disk_lbl":     {"en": "  Disk:",                           "tr": "  Disk:"},
    "log_no_susp":      {"en": "  No suspicious processes.",        "tr": "  Şüpheli süreç yok."},
    "log_susp":         {"en": "  ⚠  Suspicious process:",         "tr": "  ⚠  Şüpheli süreç:"},
    "log_cl_start":     {"en": "━━━  CLEANUP STARTED  ━━━",         "tr": "━━━  TEMİZLİK BAŞLADI  ━━━"},
    "log_cl_done":      {"en": "━━━  CLEANUP COMPLETE  ━━━",        "tr": "━━━  TEMİZLİK TAMAMLANDI  ━━━"},
    "log_freed":        {"en": "MB freed",                           "tr": "MB temizlendi"},
    "log_total_freed":  {"en": "\n  TOTAL FREED:",                  "tr": "\n  TOPLAM TEMİZLENEN:"},
    "log_pf_nf":        {"en": "  Prefetch: no access.",            "tr": "  Prefetch: erişim yok."},
    "log_wu_nf":        {"en": "  WU cache: not accessible.",       "tr": "  WU önbelleği: erişilemiyor."},
    "log_net_start":    {"en": "━━━  NETWORK DIAGNOSTICS  ━━━",     "tr": "━━━  AĞ TEŞHİSİ  ━━━"},
    "log_net_done":     {"en": "━━━  DIAGNOSTICS COMPLETE  ━━━",    "tr": "━━━  TEŞHİS TAMAMLANDI  ━━━"},
    "log_dns_ok":       {"en": "  DNS cache flushed.",              "tr": "  DNS önbelleği temizlendi."},
    "log_dns_err":      {"en": "  DNS flush failed: ",              "tr": "  DNS temizleme başarısız: "},
    "log_reach":        {"en": "reachable — avg",                   "tr": "erişilebilir — ort."},
    "log_unreach":      {"en": "unreachable",                       "tr": "erişilemiyor"},
    "log_ping_err":     {"en": "  Ping error: ",                    "tr": "  Ping hatası: "},
    "log_sp_start":     {"en": "━━━  SPEED TEST (may take 30s)  ━━━","tr": "━━━  HIZ TESTİ (30s)  ━━━"},
    "log_sp_done":      {"en": "━━━  SPEED TEST COMPLETE  ━━━",     "tr": "━━━  HIZ TESTİ TAMAMLANDI  ━━━"},
    "log_testing":      {"en": "Testing …",                          "tr": "Test ediliyor …"},
    "log_sp_err":       {"en": "  Speed test error: ",              "tr": "  Hız testi hatası: "},
    "log_dl":           {"en": "  ↓ Download :",                    "tr": "  ↓ İndirme  :"},
    "log_ul":           {"en": "  ↑ Upload   :",                    "tr": "  ↑ Yükleme  :"},
    "log_ping_r":       {"en": "  ◌ Ping     :",                    "tr": "  ◌ Ping     :"},
    "log_exported":     {"en": "Report exported →",                  "tr": "Rapor dışa aktarıldı →"},
    "log_ram_opt":      {"en": "━━━  RAM OPTIMISATION  ━━━",        "tr": "━━━  RAM OPTİMİZASYONU  ━━━"},
    "log_ram_before":   {"en": "  RAM before:",                     "tr": "  RAM öncesi:"},
    "log_ram_after":    {"en": "  RAM after: ",                     "tr": "  RAM sonrası:"},
    "log_ram_saved":    {"en": "  Freed:   ",                       "tr": "  Kurtarıldı:"},
    "log_qf_start":     {"en": "━━━  QUICK FIX PRO STARTED  ━━━",  "tr": "━━━  HIZLI DÜZELTME PRO BAŞLADI  ━━━"},
    "log_qf_done":      {"en": "━━━  QUICK FIX COMPLETE  ━━━",     "tr": "━━━  HIZLI DÜZELTME TAMAMLANDI  ━━━"},
    "log_qf_sfc":       {"en": "  [1/3] Running SFC /scannow …",   "tr": "  [1/3] SFC /scannow çalıştırılıyor …"},
    "log_qf_dism":      {"en": "  [2/3] DISM /RestoreHealth …",    "tr": "  [2/3] DISM /RestoreHealth …"},
    "log_qf_dns":       {"en": "  [3/3] Flushing DNS …",           "tr": "  [3/3] DNS temizleniyor …"},
    "log_qf_ok":        {"en": "       ✓ Done",                     "tr": "       ✓ Tamamlandı"},
    "log_qf_err":       {"en": "       ✗ Error: ",                  "tr": "       ✗ Hata: "},
    "net_ok":           {"en": "Connected ✓",                       "tr": "Bağlı ✓"},
    "net_fail":         {"en": "No internet",                       "tr": "İnternet yok"},
    "net_flushed":      {"en": "Flushed ✓",                         "tr": "Temizlendi ✓"},
    "sp_miss_title":    {"en": "Missing Library",                   "tr": "Eksik Kütüphane"},
    "sp_miss_msg":      {"en": "speedtest-cli not installed.\npip install speedtest-cli",
                         "tr": "speedtest-cli kurulu değil.\npip install speedtest-cli"},
    "rep_header":       {"en": "  PC ANALYST PRO v3  —  SYSTEM REPORT",
                         "tr": "  PC ANALİST PRO v3  —  SİSTEM RAPORU"},
    "rep_gen":          {"en": "Generated",                         "tr": "Oluşturuldu"},
    "rep_summary":      {"en": "SYSTEM SUMMARY",                    "tr": "SİSTEM ÖZETİ"},
    "rep_cores":        {"en": "CPU Cores  :",                      "tr": "CPU Çekirdek :"},
    "rep_ram":          {"en": "Total RAM  :",                      "tr": "Toplam RAM  :"},
    "rep_disk_tot":     {"en": "Disk Total :",                      "tr": "Disk Toplam :"},
    "rep_disk_free":    {"en": "Disk Free  :",                      "tr": "Disk Boş    :"},
    "rep_crashes":      {"en": "CRASH REPORT HISTORY",              "tr": "ÇÖKME RAPORU GEÇMİŞİ"},
    "rep_oplog":        {"en": "OPERATION LOG",                     "tr": "OPERASYON GÜNLÜĞÜ"},
    # ── diagnosis / driver-aging ─────────────────────────────────────────────────
    "diag_likely":      {"en": "Likely Culprit:",                   "tr": "Muhtemel Sorunlu:"},
    "diag_recommend":   {"en": "Recommendation:",                   "tr": "Öneri:"},
    "diag_overheat":    {"en": "Your PC crashed due to overheating (Max temp: {} °C).",
                         "tr": "PC'niz aşırı ısınma nedeniyle çöktü (Maks sıcaklık: {} °C)."},
    "drv_risk":         {"en": "Potential Stability Risk",         "tr": "Olası Kararlılık Riski"},
    "drv_age_old":      {"en": "Driver older than 2 years: {}",    "tr": "2 yıldan eski sürücü: {}"},
    "drv_age_none":     {"en": "No outdated drivers found.",      "tr": "Eski sürücü bulunamadı."},
}

_LANG = "en"
def set_lang(code: str): global _LANG; _LANG = code
def T(k: str) -> str:
    e = S.get(k)
    return (e.get(_LANG) or e.get("en", f"[{k}]")) if e else f"[{k}]"


# ════════════════════════════════════════════════════════════════════════════════
#  BSOD KNOWLEDGE BASE  (bilingual)
# ════════════════════════════════════════════════════════════════════════════════
def _bsod(name, cat_en, cat_tr, plain_en, plain_tr, fix_en, fix_tr):
    return {"name": name,
            "category": {"en": cat_en, "tr": cat_tr},
            "plain":    {"en": plain_en, "tr": plain_tr},
            "fix":      {"en": fix_en,   "tr": fix_tr}}

BSOD_DB = {
    "0x0000000A": _bsod("IRQL_NOT_LESS_OR_EQUAL","Memory / Driver","Bellek / Sürücü",
        "A driver accessed memory it shouldn't. Usually a faulty/outdated driver.",
        "Bir sürücü izinsiz belleğe erişti. Genellikle hatalı/eski sürücü.",
        "Update all drivers — chipset, network, display. Run Memory Diagnostic.",
        "Tüm sürücüleri güncelleyin — yonga seti, ağ, ekran. Bellek Tanılama çalıştırın."),
    "0x0000001E": _bsod("KMODE_EXCEPTION_NOT_HANDLED","Driver / Software","Sürücü / Yazılım",
        "A kernel-mode program generated an unhandled error.",
        "Çekirdek modundaki program işlenemeyen hata üretti.",
        "Check recently installed software/drivers. Boot Safe Mode.",
        "Son yüklenen yazılım/sürücüleri kontrol edin. Güvenli Mod."),
    "0x00000050": _bsod("PAGE_FAULT_IN_NONPAGED_AREA","Memory Corruption","Bellek Bozulması",
        "System read a non-existent memory page — bad RAM or corrupt driver.",
        "Sistem var olmayan bellek sayfasını okudu — hatalı RAM veya bozuk sürücü.",
        "Run Windows Memory Diagnostic. Update/rollback recent drivers.",
        "Windows Bellek Tanılama çalıştırın. Son sürücüleri güncelleyin/geri alın."),
    "0x00000074": _bsod("BAD_SYSTEM_CONFIG_INFO","Registry / Boot","Kayıt Defteri / Önyükleme",
        "System registry damaged — often after a failed update.",
        "Kayıt defteri hasarlı — genellikle başarısız güncelleme sonrası.",
        "Boot Windows media → Startup Repair.",
        "Windows medyasından başlatın → Başlangıç Onarımı."),
    "0x0000007E": _bsod("SYSTEM_THREAD_EXCEPTION_NOT_HANDLED","Driver Failure","Sürücü Arızası",
        "System thread threw an uncaught exception — almost always a driver bug.",
        "Sistem iş parçacığı yakalanmayan istisna fırlattı — sürücü hatası.",
        "Safe Mode → update or remove the latest driver.",
        "Güvenli Mod → son sürücüyü güncelleyin veya kaldırın."),
    "0x0000007F": _bsod("UNEXPECTED_KERNEL_MODE_TRAP","Hardware / Overheating","Donanım / Aşırı Isınma",
        "CPU hit a fatal condition — overheating, bad RAM, or overclocking.",
        "İşlemci kritik durumla karşılaştı — aşırı ısınma, hatalı RAM veya hız aşırtma.",
        "Check CPU temps. Remove OC. Test RAM with MemTest86.",
        "İşlemci sıcaklıklarını kontrol edin. OC kaldırın. MemTest86 ile RAM testi."),
    "0x0000009F": _bsod("DRIVER_POWER_STATE_FAILURE","Power / Driver","Güç / Sürücü",
        "Driver didn't respond during sleep/wake transition.",
        "Uyku/uyanma geçişinde sürücü yanıt vermedi.",
        "Update USB, network, display drivers. Disable fast startup.",
        "USB, ağ, ekran sürücülerini güncelleyin. Hızlı başlatmayı kapatın."),
    "0x000000EF": _bsod("CRITICAL_PROCESS_DIED","Critical System Process","Kritik Sistem Süreci",
        "Core Windows process (lsass.exe / winlogon.exe) crashed.",
        "Temel Windows süreci (lsass.exe / winlogon.exe) çöktü.",
        "Run SFC /scannow as Administrator.",
        "Yönetici olarak SFC /scannow çalıştırın."),
    "0x0000003B": _bsod("SYSTEM_SERVICE_EXCEPTION","Driver / Software","Sürücü / Yazılım",
        "Exception during user→kernel mode transition.",
        "Kullanıcı→çekirdek modu geçişi sırasında istisna.",
        "Update Windows and all drivers. Run SFC /scannow.",
        "Windows ve tüm sürücüleri güncelleyin. SFC /scannow."),
    "0x00000116": _bsod("VIDEO_TDR_FAILURE","GPU Driver Failure","GPU Sürücü Arızası",
        "GPU driver stopped responding — GPU overload/OC.",
        "GPU sürücüsü yanıt vermeyi bıraktı — GPU aşırı yükü.",
        "Clean-install GPU drivers. Check GPU temps.",
        "GPU sürücülerini temiz kurun. GPU sıcaklıklarını kontrol edin."),
    "0x000000D1": _bsod("DRIVER_IRQL_NOT_LESS_OR_EQUAL","Driver / Memory","Sürücü / Bellek",
        "Network/hardware driver accessed paged memory at too high an IRQL.",
        "Ağ/donanım sürücüsü çok yüksek IRQL'de sayfalanmış belleğe erişti.",
        "Update network adapter and chipset drivers.",
        "Ağ adaptörü ve yonga seti sürücülerini güncelleyin."),
    "UNKNOWN": _bsod("Unknown Error Code","Unclassified","Sınıflandırılmamış",
        "Error code not in local database.",
        "Hata kodu yerel veritabanında yok.",
        "Search the code on Microsoft's BSOD documentation.",
        "Microsoft BSOD belgelerinde kodu arayın."),
}

def BF(entry, field):
    v = entry.get(field, "")
    return (v.get(_LANG) or v.get("en", "")) if isinstance(v, dict) else v

# Mapping driver filenames to friendly names (bilingual via S keys used in UI)
DRIVER_MAP = {
    "nvlddmkm.sys": "NVIDIA Graphics Driver",
    "igdkmd64.sys": "Intel Graphics Driver",
    "rtwlane.sys":  "Realtek Wi-Fi Driver",
    "ntfs.sys":     "Windows File System",
}

# Precompile regex to search for known drivers in text/binary dumps
_DRIVER_RE = re.compile(r"\b(nvlddmkm|igdkmd64|rtwlane|ntfs)\.sys\b", re.IGNORECASE)

def _find_driver_in_text(text: str):
    """Return (filename, friendly_name) or (None, None)."""
    if not text: return (None, None)
    m = _DRIVER_RE.search(text)
    if not m: return (None, None)
    fn = m.group(0).lower()
    friendly = DRIVER_MAP.get(fn, fn)
    return (fn, friendly)

# Recommendations per friendly culprit (bilingual text will be generated via S)
RECOMM_MAP = {
    "NVIDIA Graphics Driver": {
        "en": [
            "1. Update GPU drivers from NVIDIA's website.",
            "2. Perform a clean driver install using DDU in Safe Mode.",
            "3. Monitor GPU temps; reseat GPU if necessary."],
        "tr": [
            "1. NVIDIA web sitesinden GPU sürücülerini güncelleyin.",
            "2. Safe Mode'da DDU ile temiz sürücü kurulumu yapın.",
            "3. GPU sıcaklıklarını izleyin; gerekirse GPU'yu yeniden takın."]
    },
    "Intel Graphics Driver": {
        "en": [
            "1. Update Intel graphics drivers via Intel Driver & Support Assistant.",
            "2. Check for Windows optional updates and chipset drivers.",
            "3. If recent update caused issues, rollback the driver."],
        "tr": [
            "1. Intel Driver & Support Assistant ile Intel grafik sürücülerini güncelleyin.",
            "2. Windows isteğe bağlı güncellemelerini ve chipset sürücülerini kontrol edin.",
            "3. Sorun güncellemeden sonra başladıysa sürücüyü geri alın."]
    },
    "Realtek Wi-Fi Driver": {
        "en": [
            "1. Update Realtek Wi-Fi drivers from vendor.",
            "2. Reinstall the wireless adapter and check antenna connections.",
            "3. Rollback if the problem started after a recent update."],
        "tr": [
            "1. Realtek sürücülerini üreticiden güncelleyin.",
            "2. Kablosuz adaptörü yeniden yükleyin ve anten bağlantılarını kontrol edin.",
            "3. Sorun yakın zamanda bir güncelleme sonrası başladıysa geri alın."]
    },
    "Windows File System": {
        "en": [
            "1. Run CHKDSK /F on affected volumes.",
            "2. Check disk SMART with CrystalDisk or similar.",
            "3. Update storage/NVMe controller drivers and firmware."],
        "tr": [
            "1. Etkilenen sürücülerde CHKDSK /F çalıştırın.",
            "2. CrystalDisk veya benzeri ile disk SMART'ını kontrol edin.",
            "3. Depolama/NVMe denetleyici sürücülerini ve firmware'i güncelleyin."]
    },
}


# ════════════════════════════════════════════════════════════════════════════════
#  HELPER WIDGETS  (DRY)
# ════════════════════════════════════════════════════════════════════════════════
def make_btn(parent, text, cmd, color, small=False):
    f, p = (FONT_SMALL, (8, 4)) if small else (FONT_UI, (14, 8))
    return tk.Button(parent, text=text, command=cmd, font=f,
                     padx=p[0], pady=p[1], bg=color, fg=C["bg"],
                     activebackground=C["text"], activeforeground=C["bg"],
                     relief="flat", cursor="hand2", bd=0)

def make_sep(parent): return tk.Frame(parent, bg=C["border"], height=1)

def lbl(parent, text, font=FONT_UI, fg=None, bg=None, **kw):
    return tk.Label(parent, text=text, font=font,
                    bg=bg or C["bg"], fg=fg or C["text"], **kw)

def slbl(parent, text, font=FONT_UI, fg=None, **kw):
    return tk.Label(parent, text=text, font=font,
                    bg=C["surface"], fg=fg or C["text"], **kw)

def progressbar(parent, color, key):
    sn = f"{key}.Horizontal.TProgressbar"
    st = ttk.Style()
    try: st.layout(sn, st.layout("Horizontal.TProgressbar"))
    except Exception: pass
    st.configure(sn, background=color, troughcolor=C["surface"], thickness=18)
    return ttk.Progressbar(parent, mode="determinate", style=sn)

def ps_query(script: str, timeout: int = 15) -> str:
    try:
        # Run powershell and try robust decoding (UTF-8, UTF-16LE, fallback)
        r = subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script
        ], capture_output=True, timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        out_b = r.stdout
        if isinstance(out_b, str):
            # Python may already return str on some platforms
            return out_b.strip()
        try:
            return out_b.decode("utf-8").strip()
        except Exception:
            try:
                return out_b.decode("utf-16le").strip()
            except Exception:
                try:
                    return out_b.decode("latin-1").strip()
                except Exception:
                    return ""
    except Exception:
        return ""


# ════════════════════════════════════════════════════════════════════════════════
#  SYSTEM INFO  (platform + PowerShell / Get-CimInstance)
# ════════════════════════════════════════════════════════════════════════════════
def collect_sysinfo() -> dict:
    info = {}
    
    # OS Bilgisi (Platform + PS)
    try:
        info["os"] = ps_query("(Get-CimInstance Win32_OperatingSystem).Caption") or platform.system()
    except: info["os"] = "Windows"

    # Mimari
    info["arch"] = platform.machine()

    # CPU Bilgisi
    try:
        cpu_name = ps_query("(Get-CimInstance Win32_Processor).Name")
        info["cpu"] = cpu_name or platform.processor()
        info["cores"] = f"{psutil.cpu_count(logical=False)} Cores / {psutil.cpu_count(logical=True)} Threads"
    except: info["cpu"] = "N/A"

    # RAM
    if PSUTIL_OK:
        vm = psutil.virtual_memory()
        info["ram_total"] = f"{vm.total // (1024**3)} GB"
        info["ram_avail"] = f"{vm.available // (1024**3)} GB ({100 - vm.percent:.0f}% free)"

    # BIOS
    info["bios"] = ps_query("(Get-CimInstance Win32_BIOS).SMBIOSBIOSVersion") or "N/A"

    # Disk Modeli (Garantili yol)
    try:
        info["disk"] = ps_query("(Get-CimInstance Win32_DiskDrive | Select-Object -First 1).Model") or "N/A"
    except: info["disk"] = "N/A"

    # GPU
    try:
        if GPU_OK:
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            info["gpu"] = pynvml.nvmlDeviceGetName(h).decode()
        else:
            info["gpu"] = ps_query("(Get-CimInstance Win32_VideoController | Select-Object -First 1).Name") or "N/A"
    except: info["gpu"] = "N/A"

    # Uptime
    if PSUTIL_OK:
        up = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        info["uptime"] = f"{int(up.total_seconds() // 3600)}h {int((up.total_seconds() % 3600) // 60)}m"

    return info

# ════════════════════════════════════════════════════════════════════════════════
#  THERMAL MONITORING  (pynvml GPU  +  PowerShell WMI CPU)
# ════════════════════════════════════════════════════════════════════════════════
def collect_thermal() -> dict:
    t = {}

    # ── CPU temperature (WMI MSAcpi_ThermalZoneTemperature → Kelvin × 10) ────
    try:
        raw = ps_query(
            "(Get-CimInstance -Namespace root/wmi MSAcpi_ThermalZoneTemperature "
            "| Select-Object -First 1 CurrentTemperature).CurrentTemperature")
        if raw:
            celsius = (int(raw) / 10) - 273.15
            t["cpu_temp"] = f"{celsius:.1f} °C"
            t["cpu_status"] = ("hot" if celsius > 85
                               else "warm" if celsius > 70 else "normal")
        else:
            t["cpu_temp"] = None
    except Exception:
        t["cpu_temp"] = None

    # ── GPU temperature via pynvml ─────────────────────────────────────────────
    if GPU_OK:
        try:
            h = pynvml.nvmlDeviceGetHandleByIndex(0)
            temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            t["gpu_temp"] = f"{temp} °C"
            t["gpu_status"] = ("hot" if temp > 90
                               else "warm" if temp > 75 else "normal")
        except Exception:
            t["gpu_temp"] = None
    else:
        t["gpu_temp"] = None

    # ── CPU fan speed via WMI ──────────────────────────────────────────────────
    try:
        fan = ps_query(
            "(Get-CimInstance -Namespace root/wmi MSAcpi_ThermalZoneTemperature "
            "| Select-Object -First 1).ThermalZone")
        fan_raw = ps_query(
            "(Get-CimInstance Win32_Fan | Select-Object -First 1).DesiredSpeed")
        t["cpu_fan"] = f"{fan_raw} RPM" if fan_raw else None
    except Exception:
        t["cpu_fan"] = None

    return t


# ════════════════════════════════════════════════════════════════════════════════
#  STARTUP MANAGER  (Registry HKLM + HKCU)
# ════════════════════════════════════════════════════════════════════════════════
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_DISABLED_PREFIX = "HKEY_DISABLED_"

def get_startup_entries() -> list:
    """Return list of dicts: {name, path, hive, disabled}."""
    entries = []
    if not WIN32_OK:
        return entries
    hives = [
        ("HKLM", winreg.HKEY_LOCAL_MACHINE),
        ("HKCU", winreg.HKEY_CURRENT_USER),
    ]
    for hive_name, hive in hives:
        for key_path in [_RUN_KEY]:
            try:
                key = winreg.OpenKey(hive, key_path,
                                     0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, data, _ = winreg.EnumValue(key, i)
                        entries.append({"name": name, "path": data,
                                        "hive": hive_name, "disabled": False,
                                        "_hive": hive, "_key": key_path})
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except Exception:
                pass
        # Check disabled entries (stored under Run\Disabled)
        disabled_path = _RUN_KEY + r"\Disabled"
        try:
            key = winreg.OpenKey(hive, disabled_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, data, _ = winreg.EnumValue(key, i)
                    entries.append({"name": name, "path": data,
                                    "hive": hive_name, "disabled": True,
                                    "_hive": hive, "_key": key_path})
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception:
            pass
    return entries

def toggle_startup_entry(entry: dict, disable: bool) -> bool:
    """Disable by moving to Run\\Disabled, enable by moving back."""
    if not WIN32_OK:
        return False
    try:
        hive     = entry["_hive"]
        src_path = (_RUN_KEY if not disable else _RUN_KEY) if not entry["disabled"] else _RUN_KEY + r"\Disabled"
        dst_path = _RUN_KEY + r"\Disabled" if disable else _RUN_KEY

        src_key = winreg.OpenKey(hive, src_path, 0,
                                 winreg.KEY_READ | winreg.KEY_WRITE)
        try:
            dst_key = winreg.CreateKey(hive, dst_path)
        except Exception:
            dst_key = winreg.OpenKey(hive, dst_path, 0, winreg.KEY_WRITE)

        winreg.SetValueEx(dst_key, entry["name"], 0,
                          winreg.REG_SZ, entry["path"])
        winreg.DeleteValue(src_key, entry["name"])
        winreg.CloseKey(src_key)
        winreg.CloseKey(dst_key)
        return True
    except Exception:
        return False


# ════════════════════════════════════════════════════════════════════════════════
#  RAM OPTIMISER
# ════════════════════════════════════════════════════════════════════════════════
def optimise_ram() -> tuple:
    if not PSUTIL_OK: return 0, 0
    before = psutil.virtual_memory().used
    PROCESS_ALL_ACCESS = 0x1F0FFF
    if WIN32_OK:
        for proc in psutil.process_iter(["pid"]):
            try:
                h = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,
                                         False, proc.info["pid"])
                win32process.SetProcessWorkingSetSize(h, -1, -1)
                win32api.CloseHandle(h)
            except Exception: pass
    else:
        try:
            k32 = ctypes.windll.kernel32
            for proc in psutil.process_iter(["pid"]):
                try:
                    h = k32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.info["pid"])
                    if h: k32.SetProcessWorkingSetSize(h, -1, -1); k32.CloseHandle(h)
                except Exception: pass
        except Exception: pass
    return before, psutil.virtual_memory().used


# ════════════════════════════════════════════════════════════════════════════════
#  APPLICATION
# ════════════════════════════════════════════════════════════════════════════════
class PCAnalystPro:

    def __init__(self, root: tk.Tk):
        self.root    = root
        self.running = True
        self.scan_results: list = []
        self._startup_entries: list = []
        self.report_dir = os.path.join(
            os.path.expanduser("~"), "Documents", "PC Analyst Reports")
        os.makedirs(self.report_dir, exist_ok=True)
        self._build_ui()
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    # ════════════════════════════════════════════════════════════════════════
    #  UI CONSTRUCTION
    # ════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self.root.configure(bg=C["bg"])
        self.root.geometry("1160x880")
        self.root.minsize(960, 740)
        self._build_header()
        self._build_notebook()
        self._build_console()
        self.root.title(T("app_title"))

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["surface"], height=64)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        self.hdr_lbl = tk.Label(hdr, text=T("header_title"),
                                 font=FONT_H1, bg=C["surface"], fg=C["blue"])
        self.hdr_lbl.pack(side="left", padx=24, pady=16)

        lf = tk.Frame(hdr, bg=C["surface"]); lf.pack(side="right", padx=16)
        self._lang_btns = {}
        for code, flag in [("en", "🇬🇧"), ("tr", "🇹🇷")]:
            b = tk.Button(lf, text=flag, font=("Segoe UI", 14),
                          bg=C["blue"] if code == _LANG else C["surface"],
                          fg=C["bg"]   if code == _LANG else C["muted"],
                          activebackground=C["text"], activeforeground=C["bg"],
                          relief="flat", cursor="hand2", bd=0, padx=6, pady=4,
                          command=lambda c=code: self._change_lang(c))
            b.pack(side="left", padx=2); self._lang_btns[code] = b

        self.clock_lbl = tk.Label(hdr, font=FONT_MONO,
                                   bg=C["surface"], fg=C["muted"])
        self.clock_lbl.pack(side="right", padx=12)
        self._tick()

    def _tick(self):
        self.clock_lbl.config(text=datetime.now().strftime("%d %b %Y  %H:%M:%S"))
        self.root.after(1000, self._tick)

    # ── Notebook ──────────────────────────────────────────────────────────────

    def _build_notebook(self):
        st = ttk.Style(); st.theme_use("default")
        st.configure("Dark.TNotebook", background=C["bg"], borderwidth=0)
        st.configure("Dark.TNotebook.Tab",
                     background=C["surface"], foreground=C["muted"],
                     font=FONT_UI, padding=[14, 8], borderwidth=0)
        st.map("Dark.TNotebook.Tab",
               background=[("selected", C["blue"])],
               foreground=[("selected", C["white"])])

        self.nb = ttk.Notebook(self.root, style="Dark.TNotebook")
        self.nb.pack(fill="x", padx=16, pady=(12, 0))

        defs = [("tab_dash",     self._tab_dashboard),
                ("tab_analysis", self._tab_analysis),
                ("tab_cleanup",  self._tab_cleanup),
                ("tab_network",  self._tab_network),
                ("tab_sysinfo",  self._tab_sysinfo),
                ("tab_startup",  self._tab_startup),
                ("tab_thermal",  self._tab_thermal),
                ("tab_language", self._tab_language)]

        self._tab_ids = []
        for key, builder in defs:
            f = tk.Frame(self.nb, bg=C["bg"])
            self.nb.add(f, text=T(key))
            self._tab_ids.append((self.nb.tabs()[-1], key))
            builder(f)

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def _tab_dashboard(self, p):
        outer = tk.Frame(p, bg=C["bg"]); outer.pack(fill="x", padx=24, pady=16)
        self.bars = {}
        for mkey, color in [("m_cpu", C["blue"]), ("m_ram", C["green"]),
                             ("m_gpu", C["purple"]), ("m_disk", C["yellow"])]:
            row = tk.Frame(outer, bg=C["bg"]); row.pack(fill="x", pady=5)
            l = tk.Label(row, text=f"{T(mkey)}:  0%", font=FONT_UI,
                         width=20, anchor="w", bg=C["bg"], fg=C["text"])
            l.pack(side="left")
            bar = progressbar(row, color, mkey.replace("m_", "").upper())
            bar.pack(side="left", fill="x", expand=True, padx=10)
            vl = tk.Label(row, text="", width=6, font=FONT_MONO, anchor="e",
                          bg=C["bg"], fg=color)
            vl.pack(side="left")
            self.bars[mkey] = (bar, l, vl)

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _tab_analysis(self, p):
        bf = tk.Frame(p, bg=C["bg"]); bf.pack(pady=16, padx=24, anchor="w")
        self.btn_qs = make_btn(bf, T("btn_quick_scan"), self._run_quick_scan, C["green"])
        self.btn_qs.pack(side="left", padx=6)
        self.btn_ds = make_btn(bf, T("btn_deep_scan"), self._run_deep_scan, C["blue"])
        self.btn_ds.pack(side="left", padx=6)
        self.btn_qf = make_btn(bf, T("btn_quick_fix"), self._run_quick_fix, C["orange"])
        self.btn_qf.pack(side="left", padx=6)

        lf = tk.Frame(p, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        lf.pack(fill="x", padx=24, pady=(0, 8))
        self.crash_h_lbl = slbl(lf, T("crash_history"), font=FONT_H3)
        self.crash_h_lbl.pack(anchor="w", padx=12, pady=(10, 4))

        self.crash_tree = ttk.Treeview(lf,
                                        columns=("time","code","category","file"),
                                        show="headings", height=6)
        ts = ttk.Style()
        ts.configure("Treeview", background=C["bg"], fieldbackground=C["bg"],
                     foreground=C["text"], rowheight=24, font=FONT_MONO)
        ts.configure("Treeview.Heading", background=C["surface"],
                     foreground=C["muted"], font=FONT_SMALL)
        ts.map("Treeview", background=[("selected", C["blue"])])
        self._tree_cols = [("time","col_time",160),("code","col_code",130),
                           ("category","col_cat",180),("file","col_src",290)]
        for col, key, w in self._tree_cols:
            self.crash_tree.heading(col, text=T(key))
            self.crash_tree.column(col, width=w, anchor="w")
        self.crash_tree.pack(fill="x", padx=12, pady=(0, 4))
        self.crash_tree.bind("<Double-1>", self._on_crash_click)
        self.crash_hint_lbl = slbl(lf, T("crash_hint"),
                                    font=FONT_TINY, fg=C["muted"])
        self.crash_hint_lbl.pack(anchor="w", padx=12, pady=(0, 8))

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def _tab_cleanup(self, p):
        of = tk.Frame(p, bg=C["bg"]); of.pack(fill="x", padx=24, pady=16)
        self.cl_title_lbl = lbl(of, T("cleanup_title"), font=FONT_H3)
        self.cl_title_lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))
        self.clean_opts, self._cl_cbs = {}, {}
        for i, (k, sk) in enumerate([("temp","opt_temp"),("prefetch","opt_prefetch"),
                                      ("updates","opt_updates"),("browser","opt_browser")]):
            var = tk.BooleanVar(value=True); self.clean_opts[k] = var
            cb = tk.Checkbutton(of, text=T(sk), variable=var, font=FONT_UI,
                                bg=C["bg"], fg=C["text"], selectcolor=C["surface"],
                                activebackground=C["bg"], activeforeground=C["text"])
            cb.grid(row=i+1, column=0, sticky="w", padx=8, pady=3)
            self._cl_cbs[k] = (cb, sk)
        br = tk.Frame(of, bg=C["bg"]); br.grid(row=5, column=0, sticky="w", padx=8, pady=12)
        self.btn_cl  = make_btn(br, T("btn_cleanup"), self._run_cleanup, C["yellow"])
        self.btn_cl.pack(side="left", padx=(0,10))
        self.btn_ram = make_btn(br, T("btn_opt_ram"), self._run_ram_opt, C["purple"])
        self.btn_ram.pack(side="left")
        self.cl_prog = ttk.Progressbar(of, mode="indeterminate", length=440)
        self.cl_prog.grid(row=6, column=0, sticky="w", padx=8)

    # ── Network ───────────────────────────────────────────────────────────────

    def _tab_network(self, p):
        br = tk.Frame(p, bg=C["bg"]); br.pack(pady=16, padx=24, anchor="w")
        self.btn_nd = make_btn(br, T("btn_net_diag"), self._run_net_diag, C["blue"])
        self.btn_nd.pack(side="left", padx=6)
        self.btn_sp = make_btn(br, T("btn_speed"), self._run_speed_test, C["green"])
        self.btn_sp.pack(side="left", padx=6)
        mf = tk.Frame(p, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        mf.pack(fill="x", padx=24, pady=(0,12))
        self.net_h_lbl = slbl(mf, T("net_health"), font=FONT_H3)
        self.net_h_lbl.pack(anchor="w", padx=12, pady=(10,6))
        inner = tk.Frame(mf, bg=C["surface"]); inner.pack(fill="x", padx=12, pady=(0,12))
        self._net_rows, self.net_vals = {}, {}
        for i, (k, sk) in enumerate([("status","net_status"),("ping","net_ping"),
                                       ("download","net_dl"),("upload","net_ul"),
                                       ("dns","net_dns")]):
            rl = slbl(inner, f"{T(sk)}:", width=24, anchor="w", fg=C["muted"])
            rl.grid(row=i, column=0, sticky="w", pady=3)
            self._net_rows[k] = (rl, sk)
            vl = slbl(inner, "—", font=FONT_MONO)
            vl.grid(row=i, column=1, sticky="w", padx=12, pady=3)
            self.net_vals[k] = vl

    # ── System Info ───────────────────────────────────────────────────────────

    def _tab_sysinfo(self, p):
        hrow = tk.Frame(p, bg=C["bg"]); hrow.pack(fill="x", padx=24, pady=(16,8))
        self.si_title_lbl = lbl(hrow, T("si_title"), font=FONT_H3)
        self.si_title_lbl.pack(side="left")
        self.btn_si_ref = make_btn(hrow, T("btn_refresh_si"),
                                    self._refresh_sysinfo, C["muted"], small=True)
        self.btn_si_ref.pack(side="right")
        tf = tk.Frame(p, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill="x", padx=24, pady=(0,12))
        self._si_rows = {}
        fields = [("si_os","os"),("si_arch","arch"),("si_cpu","cpu"),
                  ("si_cores","cores"),("si_ram_total","ram_total"),
                  ("si_ram_avail","ram_avail"),("si_disk_model","disk"),
                  ("si_gpu","gpu"),("si_bios","bios"),("si_uptime","uptime")]
        for i, (sk, dk) in enumerate(fields):
            bg = C["surface"] if i % 2 == 0 else C["surface2"]
            row = tk.Frame(tf, bg=bg); row.pack(fill="x")
            tk.Label(row, text=T(sk), font=FONT_SMALL, width=28,
                     anchor="w", bg=bg, fg=C["muted"],
                     padx=14, pady=8).pack(side="left")
            vl = tk.Label(row, text="…", font=FONT_MONO,
                          anchor="w", bg=bg, fg=C["blue"], padx=8, pady=8)
            vl.pack(side="left", fill="x", expand=True)
            self._si_rows[dk] = (vl, sk, bg)
        self._refresh_sysinfo()

    def _refresh_sysinfo(self):
        def _work():
            d = collect_sysinfo()
            def _apply():
                for k, (vl, sk, bg) in self._si_rows.items():
                    vl.config(text=d.get(k, "N/A"))
                    vl.master.winfo_children()[0].config(text=T(sk))
            self.root.after(0, _apply)
        threading.Thread(target=_work, daemon=True).start()

    # ── Startup Manager ───────────────────────────────────────────────────────

    def _tab_startup(self, p):
        hrow = tk.Frame(p, bg=C["bg"]); hrow.pack(fill="x", padx=24, pady=(16,8))
        self.sm_title_lbl = lbl(hrow, T("sm_title"), font=FONT_H3)
        self.sm_title_lbl.pack(side="left")

        br = tk.Frame(p, bg=C["bg"]); br.pack(fill="x", padx=24, anchor="w", pady=(0,8))
        self.btn_sm_ref = make_btn(br, T("btn_sm_refresh"),
                                    self._refresh_startup, C["muted"], small=True)
        self.btn_sm_ref.pack(side="left", padx=(0,8))
        self.btn_sm_dis = make_btn(br, T("btn_sm_disable"),
                                    self._startup_disable, C["red"], small=True)
        self.btn_sm_dis.pack(side="left", padx=(0,8))
        self.btn_sm_en = make_btn(br, T("btn_sm_enable"),
                                   self._startup_enable, C["green"], small=True)
        self.btn_sm_en.pack(side="left")

        tf = tk.Frame(p, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill="both", expand=True, padx=24, pady=(0,8))

        self.sm_tree = ttk.Treeview(tf,
            columns=("name","path","hive","state"),
            show="headings", height=10)
        self._sm_cols = [("name","sm_col_name",200),("path","sm_col_path",400),
                         ("hive","sm_col_hive",70),("state","sm_col_state",100)]
        for col, key, w in self._sm_cols:
            self.sm_tree.heading(col, text=T(key))
            self.sm_tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.sm_tree.yview)
        self.sm_tree.configure(yscrollcommand=sb.set)
        self.sm_tree.pack(side="left", fill="both", expand=True, padx=12, pady=8)
        sb.pack(side="right", fill="y", pady=8)

        self.sm_hint_lbl = lbl(p, T("sm_hint"), font=FONT_TINY, fg=C["muted"])
        self.sm_hint_lbl.pack(anchor="w", padx=24, pady=(0,4))

        self._refresh_startup()

    def _refresh_startup(self):
        def _work():
            entries = get_startup_entries()
            def _apply():
                self.sm_tree.delete(*self.sm_tree.get_children())
                self._startup_entries = entries
                for e in entries:
                    state = T("sm_disabled") if e["disabled"] else T("sm_enabled")
                    self.sm_tree.insert("", "end",
                        values=(e["name"], e["path"], e["hive"], state))
            self.root.after(0, _apply)
        threading.Thread(target=_work, daemon=True).start()

    def _startup_toggle(self, disable: bool):
        if not WIN32_OK:
            self.log(T("sm_no_win32"), "yellow"); return
        sel = self.sm_tree.selection()
        if not sel: self.log(T("sm_no_sel"), "muted"); return
        idx = self.sm_tree.index(sel[0])
        if idx >= len(self._startup_entries): return
        entry = self._startup_entries[idx]
        ok = toggle_startup_entry(entry, disable)
        action = "Disabled" if disable else "Enabled"
        color  = "yellow" if disable else "green"
        self.log(f"  {action}: {entry['name']} — {'OK' if ok else 'FAILED'}", color)
        self._refresh_startup()

    def _startup_disable(self): self._startup_toggle(True)
    def _startup_enable(self):  self._startup_toggle(False)

    # ── Thermal Monitoring ────────────────────────────────────────────────────

    def _tab_thermal(self, p):
        hrow = tk.Frame(p, bg=C["bg"]); hrow.pack(fill="x", padx=24, pady=(16,8))
        self.th_title_lbl = lbl(hrow, T("th_title"), font=FONT_H3)
        self.th_title_lbl.pack(side="left")
        self.btn_th_ref = make_btn(hrow, T("btn_th_refresh"),
                                    self._refresh_thermal, C["muted"], small=True)
        self.btn_th_ref.pack(side="right")

        tf = tk.Frame(p, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        tf.pack(fill="x", padx=24, pady=(0,12))

        self._th_labels = {}
        fields = [("th_cpu_temp","cpu_temp"),("th_gpu_temp","gpu_temp"),
                  ("th_cpu_fan","cpu_fan"),("th_status","status")]
        for i, (sk, dk) in enumerate(fields):
            bg = C["surface"] if i % 2 == 0 else C["surface2"]
            row = tk.Frame(tf, bg=bg); row.pack(fill="x")
            tk.Label(row, text=T(sk), font=FONT_SMALL, width=28,
                     anchor="w", bg=bg, fg=C["muted"],
                     padx=14, pady=10).pack(side="left")
            vl = tk.Label(row, text="…", font=FONT_H3,
                          anchor="w", bg=bg, fg=C["teal"], padx=8)
            vl.pack(side="left", fill="x", expand=True)
            self._th_labels[dk] = (vl, sk, bg)

        self.th_hint_lbl = lbl(p, T("th_hint"), font=FONT_TINY, fg=C["muted"])
        self.th_hint_lbl.pack(anchor="w", padx=24, pady=(0,4))

        self._refresh_thermal()

    def _refresh_thermal(self):
        def _work():
            d = collect_thermal()
            def _apply():
                # CPU temp
                ct = d.get("cpu_temp")
                cpu_lbl = self._th_labels["cpu_temp"][0]
                if ct:
                    st = d.get("cpu_status","normal")
                    cpu_lbl.config(text=ct,
                                   fg=(C["red"] if st=="hot"
                                       else C["yellow"] if st=="warm"
                                       else C["teal"]))
                else:
                    cpu_lbl.config(text=T("th_na"), fg=C["muted"])

                # GPU temp
                gt = d.get("gpu_temp")
                gpu_lbl = self._th_labels["gpu_temp"][0]
                if gt:
                    st = d.get("gpu_status","normal")
                    gpu_lbl.config(text=gt,
                                   fg=(C["red"] if st=="hot"
                                       else C["yellow"] if st=="warm"
                                       else C["teal"]))
                else:
                    gpu_lbl.config(text=T("th_na"), fg=C["muted"])

                # Fan
                fan = d.get("cpu_fan")
                self._th_labels["cpu_fan"][0].config(
                    text=fan or T("th_na"),
                    fg=C["teal"] if fan else C["muted"])

                # Overall status
                cpu_s = d.get("cpu_status","")
                gpu_s = d.get("gpu_status","")
                worst = ("hot"  if "hot"  in (cpu_s, gpu_s) else
                         "warm" if "warm" in (cpu_s, gpu_s) else "normal")
                self._th_labels["status"][0].config(
                    text=T(f"th_{worst}"),
                    fg=(C["red"] if worst=="hot"
                        else C["yellow"] if worst=="warm"
                        else C["teal"]))

                # Retranslate row labels
                for dk, (vl, sk, _) in self._th_labels.items():
                    vl.master.winfo_children()[0].config(text=T(sk))
            self.root.after(0, _apply)
        threading.Thread(target=_work, daemon=True).start()

    # ── Language Tab ──────────────────────────────────────────────────────────

    def _tab_language(self, p):
        f = tk.Frame(p, bg=C["bg"]); f.pack(padx=40, pady=30, anchor="nw")
        self.lang_t_lbl = lbl(f, T("lang_title"), font=FONT_H2)
        self.lang_t_lbl.pack(anchor="w", pady=(0,6))
        self.lang_s_lbl = lbl(f, T("lang_sub"), fg=C["muted"])
        self.lang_s_lbl.pack(anchor="w", pady=(0,20))
        br = tk.Frame(f, bg=C["bg"]); br.pack(anchor="w")
        self._lang_tab_btns = {}
        for code, label in [("en","🇬🇧  English"),("tr","🇹🇷  Türkçe")]:
            active = (code == _LANG)
            b = tk.Button(br, text=label, font=("Segoe UI",11,"bold"),
                          padx=20, pady=10,
                          bg=C["blue"] if active else C["surface"],
                          fg=C["bg"]   if active else C["text"],
                          activebackground=C["text"], activeforeground=C["bg"],
                          relief="flat", cursor="hand2", bd=0,
                          command=lambda c=code: self._change_lang(c))
            b.pack(side="left", padx=(0,12)); self._lang_tab_btns[code] = b
        make_sep(f).pack(fill="x", pady=20)
        self.lang_n_lbl = lbl(f, T("lang_note"), fg=C["yellow"],
                               font=("Segoe UI",9,"italic"), justify="left")
        self.lang_n_lbl.pack(anchor="w")

    # ── Console ───────────────────────────────────────────────────────────────

    def _build_console(self):
        ch = tk.Frame(self.root, bg=C["bg"]); ch.pack(fill="x", padx=20, pady=(8,0))
        self.op_lbl = tk.Label(ch, text=T("op_log"), font=FONT_SMALL,
                                bg=C["bg"], fg=C["muted"])
        self.op_lbl.pack(side="left")
        self.btn_exp = make_btn(ch, T("btn_export"), self._export, C["muted"], small=True)
        self.btn_exp.pack(side="right", padx=4)
        self.console = tk.Text(self.root, bg=C["surface"], fg=C["text"],
                                font=FONT_MONO, padx=12, pady=10,
                                borderwidth=1, relief="flat",
                                state="disabled", height=9)
        self.console.pack(fill="both", expand=True, padx=20, pady=(4,16))
        for tag, col in [("blue",C["blue"]),("green",C["green"]),("red",C["red"]),
                          ("yellow",C["yellow"]),("purple",C["purple"]),
                          ("orange",C["orange"]),("teal",C["teal"]),("muted",C["muted"])]:
            self.console.tag_configure(tag, foreground=col)

    # ════════════════════════════════════════════════════════════════════════
    #  LANGUAGE
    # ════════════════════════════════════════════════════════════════════════

    def _change_lang(self, code: str): set_lang(code); self._retranslate()

    def _retranslate(self):
        self.root.title(T("app_title"))
        self.hdr_lbl.config(text=T("header_title"))
        for tid, key in self._tab_ids: self.nb.tab(tid, text=T(key))

        for code, btn in self._lang_btns.items():
            a = (code == _LANG)
            btn.config(bg=C["blue"] if a else C["surface"],
                       fg=C["bg"]   if a else C["muted"])
        for code, btn in self._lang_tab_btns.items():
            a = (code == _LANG)
            btn.config(bg=C["blue"] if a else C["surface"],
                       fg=C["bg"]   if a else C["text"])

        for mkey, (bar, l, vl) in self.bars.items():
            pct = l.cget("text").split(":")[1].strip() if ":" in l.cget("text") else "0%"
            l.config(text=f"{T(mkey)}:  {pct}")

        self.btn_qs.config(text=T("btn_quick_scan"))
        self.btn_ds.config(text=T("btn_deep_scan"))
        self.btn_qf.config(text=T("btn_quick_fix"))
        self.crash_h_lbl.config(text=T("crash_history"))
        self.crash_hint_lbl.config(text=T("crash_hint"))
        for col, key, _ in self._tree_cols: self.crash_tree.heading(col, text=T(key))

        self.cl_title_lbl.config(text=T("cleanup_title"))
        for _, (cb, sk) in self._cl_cbs.items(): cb.config(text=T(sk))
        self.btn_cl.config(text=T("btn_cleanup"))
        self.btn_ram.config(text=T("btn_opt_ram"))

        self.btn_nd.config(text=T("btn_net_diag"))
        self.btn_sp.config(text=T("btn_speed"))
        self.net_h_lbl.config(text=T("net_health"))
        for k, (rl, sk) in self._net_rows.items(): rl.config(text=f"{T(sk)}:")

        self.si_title_lbl.config(text=T("si_title"))
        self.btn_si_ref.config(text=T("btn_refresh_si"))
        for _, (vl, sk, _) in self._si_rows.items():
            vl.master.winfo_children()[0].config(text=T(sk))

        self.sm_title_lbl.config(text=T("sm_title"))
        self.btn_sm_ref.config(text=T("btn_sm_refresh"))
        self.btn_sm_dis.config(text=T("btn_sm_disable"))
        self.btn_sm_en.config(text=T("btn_sm_enable"))
        self.sm_hint_lbl.config(text=T("sm_hint"))
        for col, key, _ in self._sm_cols: self.sm_tree.heading(col, text=T(key))
        # Re-render state column translations
        for i, item in enumerate(self.sm_tree.get_children()):
            vals = list(self.sm_tree.item(item, "values"))
            if i < len(self._startup_entries):
                d = self._startup_entries[i]["disabled"]
                vals[3] = T("sm_disabled") if d else T("sm_enabled")
            self.sm_tree.item(item, values=vals)

        self.th_title_lbl.config(text=T("th_title"))
        self.btn_th_ref.config(text=T("btn_th_refresh"))
        self.th_hint_lbl.config(text=T("th_hint"))
        for _, (vl, sk, _) in self._th_labels.items():
            vl.master.winfo_children()[0].config(text=T(sk))

        self.lang_t_lbl.config(text=T("lang_title"))
        self.lang_s_lbl.config(text=T("lang_sub"))
        self.lang_n_lbl.config(text=T("lang_note"))
        self.op_lbl.config(text=T("op_log"))
        self.btn_exp.config(text=T("btn_export"))

    # ════════════════════════════════════════════════════════════════════════
    #  LOGGING
    # ════════════════════════════════════════════════════════════════════════

    def log(self, text: str, color: str = ""):
        def _do():
            self.console.config(state="normal")
            ts = datetime.now().strftime("[%H:%M:%S]")
            self.console.insert("end", f"{ts}  {text}\n", color or "")
            self.console.see("end")
            self.console.config(state="disabled")
        self.root.after(0, _do)

    # ════════════════════════════════════════════════════════════════════════
    #  LIVE MONITOR
    # ════════════════════════════════════════════════════════════════════════

    def _monitor_loop(self):
        while self.running:
            try:
                cpu  = psutil.cpu_percent(interval=1) if PSUTIL_OK else 0
                ram  = psutil.virtual_memory().percent if PSUTIL_OK else 0
                disk = psutil.disk_usage("/").percent  if PSUTIL_OK else 0
                gpu  = 0
                if GPU_OK:
                    try:
                        h = pynvml.nvmlDeviceGetHandleByIndex(0)
                        gpu = pynvml.nvmlDeviceGetUtilizationRates(h).gpu
                    except Exception: pass
                for k, v in [("m_cpu",cpu),("m_ram",ram),
                               ("m_gpu",gpu),("m_disk",disk)]:
                    self.root.after(0, lambda k=k, v=v: self._set_bar(k, v))
            except Exception as e:
                print(f"Monitor: {e}")
            time.sleep(2)

    def _set_bar(self, mkey: str, value: float):
        bar, l, vl = self.bars[mkey]
        bar["value"] = value
        l.config(text=f"{T(mkey)}:  {value:.0f}%")
        vl.config(text=f"{value:.0f}%")

    # ════════════════════════════════════════════════════════════════════════
    #  QUICK SCAN
    # ════════════════════════════════════════════════════════════════════════

    def _run_quick_scan(self):
        threading.Thread(target=self._quick_scan, daemon=True).start()

    def _quick_scan(self):
        self.log(T("log_qs_start"), "blue")
        self.log(T("log_svc_check"), "muted")
        critical = ["lsass.exe","csrss.exe","winlogon.exe","svchost.exe"]
        found = ({p.info["name"].lower()
                  for p in psutil.process_iter(["name"])}
                 if PSUTIL_OK else set())
        for svc in critical:
            if svc in found: self.log(f"  ✓  {svc} — {T('log_running')}", "green")
            else:             self.log(f"  ✗  {svc} — {T('log_missing')}", "red")
        if PSUTIL_OK:
            u = psutil.disk_usage("/")
            col = "red" if u.percent>90 else ("yellow" if u.percent>75 else "green")
            self.log(f"{T('log_disk_u')}: {u.percent:.1f}%  "
                     f"({u.used//(1024**3)} GB {T('log_used')} / "
                     f"{u.total//(1024**3)} GB {T('log_total')})", col)
            vm = psutil.virtual_memory()
            self.log(f"RAM: {vm.percent:.1f}% {T('log_used')}  "
                     f"({vm.available//(1024**2)} MB {T('log_ram_free')})",
                     "green" if vm.percent<80 else "red")
        self.log(T("log_qs_done"), "blue")

    # ════════════════════════════════════════════════════════════════════════
    #  DEEP SCAN
    # ════════════════════════════════════════════════════════════════════════

    def _run_deep_scan(self):
        threading.Thread(target=self._deep_scan, daemon=True).start()

    def _deep_scan(self):
        self.log(T("log_ds_start"), "blue")
        self.scan_results.clear()
        self.root.after(0, lambda: self.crash_tree.delete(
            *self.crash_tree.get_children()))
        self.log(T("log_evtlog"), "muted")
        if WIN32_OK: self._parse_event_logs()
        else: self.log(T("log_no_pywin32"),"yellow"); self._parse_minidumps()
        self.log(T("log_smart"), "muted"); self._smart_check()
        # Driver aging scan: highlight drivers older than 2 years
        self.log(T("drv_risk"), "muted"); self._driver_aging()
        self.log(T("log_bg_proc"), "muted"); self._process_audit()
        self.log(T("log_top_cpu"), "muted")
        if PSUTIL_OK:
            procs = sorted(psutil.process_iter(["name","cpu_percent"]),
                           key=lambda p: p.info.get("cpu_percent") or 0,
                           reverse=True)[:5]
            for pr in procs:
                cpu = pr.info.get("cpu_percent") or 0
                col = "red" if cpu>30 else ("yellow" if cpu>10 else "green")
                self.log(f"  {pr.info['name']:<30} {cpu:>6.1f}% CPU", col)
        self.log(T("log_ds_done"), "blue")
        if not self.scan_results: self.log(T("log_no_crash"), "green")

    def _parse_event_logs(self):
        try:
            h = win32evtlog.OpenEventLog(None, "System")
            flags = (win32evtlog.EVENTLOG_BACKWARDS_READ |
                     win32evtlog.EVENTLOG_SEQUENTIAL_READ)
            count = 0
            while count < 500:
                recs = win32evtlog.ReadEventLog(h, flags, 0)
                if not recs: break
                for rec in recs:
                    count += 1
                    if rec.EventID & 0xFFFF == 1001:
                        msg  = win32evtlogutil.SafeFormatMessage(rec, "System")
                        code = self._extract_code(msg)
                        fn, friendly = _find_driver_in_text(msg)
                        culprit = friendly if friendly else None
                        self._add_crash(rec.TimeGenerated.Format(), code, "Event Log", culprit=culprit)
                    if count >= 500: break
            win32evtlog.CloseEventLog(h)
        except Exception as ex:
            self.log(T("log_evtlog_err") + str(ex), "yellow")

    def _parse_minidumps(self):
        mini = r"C:\Windows\Minidump"
        if not os.path.isdir(mini): self.log(T("log_no_mini_dir"), "muted"); return
        try:
            files = sorted(glob.glob(os.path.join(mini,"*.dmp")),
                           key=os.path.getmtime, reverse=True)[:10]
            if not files: self.log(T("log_no_dmp"), "muted"); return
            for path in files:
                mtime = datetime.fromtimestamp(
                    os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                code = self._read_dump(path)
                # Attempt to scan binary dump for known driver filenames
                try:
                    fn, friendly = self._scan_dump_for_driver(path)
                except Exception:
                    fn, friendly = (None, None)
                culprit = friendly if friendly else None
                self._add_crash(mtime, code, os.path.basename(path), culprit=culprit)
        except PermissionError:
            self.log(T("log_perm"), "yellow")

    def _scan_dump_for_driver(self, path: str):
        """Read initial bytes of dump and look for known driver filenames."""
        try:
            with open(path, "rb") as f:
                data = f.read(0x4000)
            # decode as latin1 to preserve byte values for ascii matches
            txt = data.decode("latin-1", errors="ignore")
            return _find_driver_in_text(txt)
        except Exception:
            return (None, None)

    def _read_dump(self, path: str) -> str:
        try:
            with open(path, "rb") as f: data = f.read(0x1000)
            if data[:4] != b"MDMP": return "UNKNOWN"
            ns = struct.unpack_from("<I", data, 0x10)[0]
            rva = struct.unpack_from("<I", data, 0x1C)[0]
            for i in range(min(ns, 32)):
                off = rva + i * 12
                if off + 12 > len(data): break
                stype = struct.unpack_from("<I", data, off)[0]
                s_rva = struct.unpack_from("<I", data, off + 8)[0]
                if stype == 6 and s_rva + 4 <= len(data):
                    return f"0x{struct.unpack_from('<I', data, s_rva)[0]:08X}"
            return "UNKNOWN"
        except Exception: return "UNKNOWN"

    @staticmethod
    def _extract_code(msg: str) -> str:
        m = re.search(r"0x[0-9A-Fa-f]{8}", msg)
        return m.group(0).upper() if m else "UNKNOWN"

    def _add_crash(self, ts, code, src, culprit: str = None):
        entry = BSOD_DB.get(code.upper(), BSOD_DB["UNKNOWN"])
        cat = BF(entry, "category")
        rec = {"time": ts, "code": code, "category": cat, "file": src, "culprit": culprit}
        self.scan_results.append(rec)
        # Log with culprit if found
        if culprit:
            self.log(f"  🔴  {ts}  |  {code}  |  {cat}  |  {culprit}", "red")
        else:
            self.log(f"  🔴  {ts}  |  {code}  |  {cat}", "red")
        self.root.after(0, lambda: self.crash_tree.insert(
            "", "end", values=(ts, code, cat, src)))

    def _smart_check(self):
        try:
            out = ps_query(
                "Get-CimInstance Win32_DiskDrive | "
                "Select-Object Model,Size,Status | "
                "ConvertTo-Csv -NoTypeInformation", timeout=12)
            for line in out.splitlines()[1:]:
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= 3:
                    model, size_b, status = parts[0], parts[1], parts[2]
                    gb = int(size_b) // 1024**3 if size_b.isdigit() else 0
                    self.log(f"{T('log_disk_lbl')} {model}  —  {gb} GB  —  {status}",
                             "green" if status.lower()=="ok" else "red")
        except Exception as e:
            self.log(T("log_smart_err") + str(e), "yellow")

    def _driver_aging(self):
        """Scan installed signed drivers and flag ones older than 2 years."""
        def _work():
            try:
                ps = (
                    "Get-CimInstance Win32_PnPSignedDriver | Select-Object DeviceName,Manufacturer,DriverVersion,"
                    "@{n='DriverDate';e={if ($_.DriverDate) {$_.DriverDate.ToString('s')} else {''}}} | ConvertTo-Csv -NoTypeInformation"
                )
                out = ps_query(ps, timeout=20)
                if not out:
                    self.log(T("drv_age_none"), "green")
                    return
                outdated = []
                for line in out.splitlines()[1:]:
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) < 4: continue
                    name = parts[0]; date_s = parts[3]
                    if not date_s: continue
                    try:
                        dt = datetime.fromisoformat(date_s)
                        age_days = (datetime.now() - dt).days
                        if age_days > 365 * 2:
                            outdated.append(name)
                            self.log(T("drv_age_old").format(name), "yellow")
                    except Exception:
                        continue
                if not outdated:
                    self.log(T("drv_age_none"), "green")
            except Exception as e:
                self.log("Driver aging scan failed: " + str(e), "yellow")
        threading.Thread(target=_work, daemon=True).start()

    def _process_audit(self):
        if not PSUTIL_OK: return
        bad = {"cryptominer","xmrig","minerd","nssm","mimikatz","rat.exe"}
        found = False
        for pr in psutil.process_iter(["name","pid"]):
            if pr.info["name"].lower() in bad:
                self.log(f"{T('log_susp')} {pr.info['name']} "
                         f"(PID {pr.info['pid']})", "red")
                found = True
        if not found: self.log(T("log_no_susp"), "green")

    # ════════════════════════════════════════════════════════════════════════
    #  QUICK FIX PRO
    # ════════════════════════════════════════════════════════════════════════

    def _run_quick_fix(self):
        threading.Thread(target=self._quick_fix, daemon=True).start()

    def _quick_fix(self):
        self.log(T("log_qf_start"), "orange")
        steps = [
            ("log_qf_dns",  ["ipconfig", "/flushdns"]),
            ("log_qf_dism", ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"]),
            ("log_qf_sfc",  ["sfc", "/scannow"]),
        ]
        for lkey, cmd in steps:
            self.log(T(lkey), "muted")
            try:
                subprocess.run(cmd, capture_output=True, timeout=360,
                               creationflags=subprocess.CREATE_NO_WINDOW)
                self.log(T("log_qf_ok"), "green")
            except Exception as e:
                self.log(T("log_qf_err") + str(e), "red")
        self.log(T("log_qf_done"), "orange")

    # ════════════════════════════════════════════════════════════════════════
    #  CRASH MODAL
    # ════════════════════════════════════════════════════════════════════════

    def _on_crash_click(self, _):
        sel = self.crash_tree.selection()
        if not sel: return
        ts, code = self.crash_tree.item(sel[0], "values")[:2]
        entry = BSOD_DB.get(code.upper(), BSOD_DB["UNKNOWN"])
        # try find culprit from scan_results matching timestamp+code
        culprit = None
        for r in self.scan_results:
            if r.get("time") == ts and r.get("code") == code:
                culprit = r.get("culprit")
                break
        m = tk.Toplevel(self.root)
        m.title(f"{T('modal_title')} — {code}")
        m.configure(bg=C["bg"]); m.resizable(False,False); m.grab_set()
        def row(label, value, vc=C["text"]):
            f = tk.Frame(m, bg=C["bg"]); f.pack(fill="x", padx=20, pady=4)
            tk.Label(f, text=label, width=18, anchor="w",
                     font=FONT_SMALL, bg=C["bg"], fg=C["muted"]).pack(side="left")
            tk.Label(f, text=value, font=FONT_UI, bg=C["bg"], fg=vc,
                     wraplength=400, justify="left").pack(side="left",fill="x",expand=True)
        tk.Label(m, text=f"🔴  {entry['name']}", font=FONT_H2,
                 bg=C["bg"], fg=C["red"]).pack(pady=(20,4))
        make_sep(m).pack(fill="x", padx=20, pady=8)
        row(T("modal_code"), code, C["yellow"])
        row(T("modal_cat"),  BF(entry,"category"), C["blue"])
        row(T("modal_time"), ts)
        # Likely culprit (if detected)
        if culprit:
            row(T("diag_likely"), culprit, C["orange"])
        make_sep(m).pack(fill="x", padx=20, pady=8)
        tk.Label(m, text=T("modal_what"), font=FONT_SMALL,
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", padx=20)
        tk.Label(m, text=BF(entry,"plain"), font=FONT_UI,
                 bg=C["bg"], fg=C["text"], wraplength=440,
                 justify="left").pack(anchor="w", padx=20, pady=(4,12))
        tk.Label(m, text=T("modal_fix"), font=FONT_SMALL,
                 bg=C["bg"], fg=C["muted"]).pack(anchor="w", padx=20)
        # Recommendations: prefer culprit-specific bilingual recommendations
        rec_frame = tk.Frame(m, bg=C["bg"])
        rec_frame.pack(fill="x", padx=20, pady=(4,8))
        recs = None
        if culprit and culprit in RECOMM_MAP:
            recs = RECOMM_MAP[culprit].get(_LANG, RECOMM_MAP[culprit].get("en"))
        else:
            # fallback to BSOD_DB fix text (may be a single string)
            fix_text = BF(entry, "fix")
            if isinstance(fix_text, str):
                # attempt to split into up to 3 steps by sentences
                parts = [p.strip() for p in re.split(r"[\n\.]{1,}", fix_text) if p.strip()]
                recs = parts[:3] if parts else [fix_text]
        if recs:
            for rtxt in recs:
                tk.Label(rec_frame, text=rtxt, font=FONT_UI,
                         bg=C["bg"], fg=C["green"], wraplength=440,
                         justify="left").pack(anchor="w")
        else:
            tk.Label(rec_frame, text=T("drv_age_none"), font=FONT_UI,
                     bg=C["bg"], fg=C["green"]).pack(anchor="w")

        # Thermal correlation: if category suggests Hardware/CPU, check temps
        cat_en = entry.get("category", {}).get("en", "").lower() if isinstance(entry.get("category"), dict) else ""
        if any(k in cat_en for k in ("hardware", "cpu")):
            # run in background to avoid UI freeze
            warn_lbl = tk.Label(m, text="", font=FONT_SMALL, bg=C["bg"], fg=C["red"], wraplength=440, justify="left")
            warn_lbl.pack(fill="x", padx=20, pady=(8,4))
            def _check_thermal():
                d = collect_thermal()
                ct = d.get("cpu_temp")
                maxtemp = None
                if ct:
                    m = re.search(r"([0-9]+(\.[0-9]+)?)", ct)
                    if m:
                        try: maxtemp = float(m.group(1))
                        except Exception: maxtemp = None
                if maxtemp and maxtemp > 85:
                    txt = T("diag_overheat").format(int(maxtemp))
                    self.root.after(0, lambda: warn_lbl.config(text=txt))
            threading.Thread(target=_check_thermal, daemon=True).start()
        make_btn(m, T("btn_close"), m.destroy, C["blue"]).pack(pady=(0,16))

    # ════════════════════════════════════════════════════════════════════════
    #  RAM OPTIMISER
    # ════════════════════════════════════════════════════════════════════════

    def _run_ram_opt(self):
        threading.Thread(target=self._ram_opt, daemon=True).start()

    def _ram_opt(self):
        self.log(T("log_ram_opt"), "purple")
        before, after = optimise_ram()
        if before == 0 == after: return
        freed = (before - after) / 1024**2
        self.log(f"{T('log_ram_before')} {before/1024**3:.2f} GB", "muted")
        self.log(f"{T('log_ram_after')}  {after /1024**3:.2f} GB", "muted")
        self.log(f"{T('log_ram_saved')}  {freed:.0f} MB",
                 "green" if freed > 0 else "yellow")

    # ════════════════════════════════════════════════════════════════════════
    #  CLEANUP
    # ════════════════════════════════════════════════════════════════════════

    def _run_cleanup(self):
        threading.Thread(target=self._cleanup, daemon=True).start()

    def _cleanup(self):
        self.root.after(0, self.cl_prog.start)
        self.log(T("log_cl_start"), "yellow")
        total = 0
        def clean(folder, ext=""):
            freed = 0
            for rd, _, files in os.walk(folder):
                for fn in files:
                    if ext and not fn.endswith(ext): continue
                    fp = os.path.join(rd, fn)
                    try: freed += os.path.getsize(fp); os.remove(fp)
                    except (PermissionError, FileNotFoundError, OSError): pass
            return freed
        if self.clean_opts["temp"].get():
            for f in [os.environ.get("TEMP",""), os.environ.get("TMP",""),
                      r"C:\Windows\Temp"]:
                if f and os.path.isdir(f):
                    n = clean(f); total += n
                    self.log(f"  Temp [{f}]: {n/1024**2:.2f} {T('log_freed')}", "green")
        if self.clean_opts["prefetch"].get():
            pf = r"C:\Windows\Prefetch"
            if os.path.isdir(pf):
                n = clean(pf,".pf"); total += n
                self.log(f"  Prefetch: {n/1024**2:.2f} {T('log_freed')}", "green")
            else: self.log(T("log_pf_nf"), "muted")
        if self.clean_opts["updates"].get():
            wu = r"C:\Windows\SoftwareDistribution\Download"
            if os.path.isdir(wu):
                n = clean(wu); total += n
                self.log(f"  WU Cache: {n/1024**2:.2f} {T('log_freed')}", "green")
            else: self.log(T("log_wu_nf"), "muted")
        if self.clean_opts["browser"].get():
            la = os.environ.get("LOCALAPPDATA","")
            for br, p in {
                "Chrome":  os.path.join(la,"Google","Chrome","User Data","Default","Cache"),
                "Edge":    os.path.join(la,"Microsoft","Edge","User Data","Default","Cache"),
                "Firefox": self._ff_cache(),
            }.items():
                if p and os.path.isdir(p):
                    n = clean(p); total += n
                    self.log(f"  {br}: {n/1024**2:.2f} {T('log_freed')}", "green")
        self.log(f"{T('log_total_freed')} {total/1024**2:.2f} MB", "yellow")
        self.log(T("log_cl_done"), "yellow")
        self.root.after(0, self.cl_prog.stop)

    @staticmethod
    def _ff_cache() -> str:
        base = os.path.join(os.environ.get("LOCALAPPDATA",""),
                            "Mozilla","Firefox","Profiles")
        if not os.path.isdir(base): return ""
        for pr in os.listdir(base):
            c = os.path.join(base, pr, "cache2")
            if os.path.isdir(c): return c
        return ""

    # ════════════════════════════════════════════════════════════════════════
    #  NETWORK
    # ════════════════════════════════════════════════════════════════════════

    def _run_net_diag(self):
        threading.Thread(target=self._net_diag, daemon=True).start()

    def _net_diag(self):
        self.log(T("log_net_start"), "blue")
        try:
            subprocess.run(["ipconfig","/flushdns"], capture_output=True,
                           timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
            self.log(T("log_dns_ok"), "green")
            self._nv("dns", T("net_flushed"), C["green"])
        except Exception as e:
            self.log(T("log_dns_err")+str(e), "yellow")
            self._nv("dns", str(e), C["yellow"])
        connected = False
        for ip, name in [("8.8.8.8","Google DNS"),("1.1.1.1","Cloudflare DNS")]:
            try:
                r = subprocess.run(["ping","-n","4",ip], capture_output=True,
                                   text=True, timeout=15,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                if "TTL=" in r.stdout:
                    m   = re.search(r"Average = (\d+)ms", r.stdout)
                    avg = (m.group(1)+" ms") if m else "OK"
                    self.log(f"  {name} ({ip}): {T('log_reach')} {avg}", "green")
                    self._nv("ping",   avg,          C["green"])
                    self._nv("status", T("net_ok"),  C["green"])
                    connected = True; break
                else:
                    self.log(f"  {name} ({ip}): {T('log_unreach')}", "red")
            except Exception as ex:
                self.log(T("log_ping_err")+str(ex), "red")
        if not connected:
            self._nv("status", T("net_fail"), C["red"])
            self._nv("ping",   "—",           C["muted"])
        self.log(T("log_net_done"), "blue")

    def _run_speed_test(self):
        if not SPEED_OK:
            messagebox.showwarning(T("sp_miss_title"), T("sp_miss_msg")); return
        threading.Thread(target=self._speed_test, daemon=True).start()

    def _speed_test(self):
        self.log(T("log_sp_start"), "blue")
        for k in ("download","upload","ping"):
            self._nv(k, T("log_testing"), C["yellow"])
        try:
            st = _st.Speedtest(secure=True); st.get_best_server()
            dl = st.download()/1e6; ul = st.upload()/1e6; pm = st.results.ping
            self._nv("download", f"{dl:.2f}  Mbps", C["green"])
            self._nv("upload",   f"{ul:.2f}  Mbps", C["green"])
            self._nv("ping",     f"{pm:.0f} ms",
                     C["green"] if pm<80 else C["yellow"])
            self.log(f"{T('log_dl')} {dl:.2f} Mbps",  "green")
            self.log(f"{T('log_ul')}   {ul:.2f} Mbps","green")
            self.log(f"{T('log_ping_r')} {pm:.0f} ms",
                     "green" if pm<80 else "yellow")
        except Exception as e:
            self.log(T("log_sp_err")+str(e), "red")
            self._nv("download","Error",C["red"]); self._nv("upload","Error",C["red"])
        self.log(T("log_sp_done"), "blue")

    def _nv(self, key: str, text: str, color: str):
        self.root.after(0, lambda: self.net_vals[key].config(text=text, fg=color)
                        if key in self.net_vals else None)

    # ════════════════════════════════════════════════════════════════════════
    #  EXPORT
    # ════════════════════════════════════════════════════════════════════════

    def _export(self):
        name = f"Report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        path = filedialog.asksaveasfilename(
            initialdir=self.report_dir, initialfile=name,
            defaultextension=".txt",
            filetypes=[("Text","*.txt"),("All","*.*")],
            title=T("export_title"))
        if not path: return
        try:
            txt = self.console.get("1.0","end")
            with open(path, "w", encoding="utf-8") as f:
                f.write("="*60+"\n")
                f.write(T("rep_header")+"\n")
                f.write(f"  {T('rep_gen')}: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}\n")
                f.write("="*60+"\n\n")
                if PSUTIL_OK:
                    vm = psutil.virtual_memory(); dk = psutil.disk_usage("/")
                    f.write(T("rep_summary")+"\n"+"-"*40+"\n")
                    f.write(f"{T('rep_cores')} {psutil.cpu_count()}\n")
                    f.write(f"{T('rep_ram')}   {vm.total//(1024**3)} GB\n")
                    f.write(f"{T('rep_disk_tot')} {dk.total//(1024**3)} GB\n")
                    f.write(f"{T('rep_disk_free')} {dk.free//(1024**3)} GB\n\n")
                if self.scan_results:
                    f.write(T("rep_crashes")+"\n"+"-"*40+"\n")
                    for r in self.scan_results:
                        f.write(f"  [{r['time']}]  {r['code']}  |  "
                                f"{r['category']}  |  {r['file']}\n")
                    f.write("\n")
                f.write(T("rep_oplog")+"\n"+"-"*40+"\n"+txt)
            messagebox.showinfo(T("export_ok"), T("export_ok_msg").format(path))
            self.log(f"{T('log_exported')} {os.path.basename(path)}", "green")
        except Exception as e:
            messagebox.showerror(T("export_err"), str(e))

    # ════════════════════════════════════════════════════════════════════════
    #  SHUTDOWN
    # ════════════════════════════════════════════════════════════════════════

    def on_close(self):
        self.running = False
        self.root.destroy()


# ════════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = PCAnalystPro(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
