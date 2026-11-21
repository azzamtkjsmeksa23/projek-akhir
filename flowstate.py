import json
import math
import os
import time
import sys
import subprocess
import shutil
import re

import psutil
import customtkinter as ctk

ctk.set_appearance_mode("dark")

# rules
INTERVAL_PENGINGAT = 10
MINIMUM_TUGAS = 1
DURASI_PENALTI = 15
PENALTI_SAAT_DARURAT = True
INTERVAL_BLOKIR = 2
FILE_STAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statistik.json")
FILE_BLOCKLIST = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "blocklist.json"
)
HOSTS_HELPER = "/usr/local/sbin/flowstate-hosts"


# data
tugas = []
waktu_tersisa = 0
waktu_total = 0
waktu_berjalan = False
tick_id = None
penalti_id = None
pemblokir_id = None
hosts_keepalive_id = None
website_hosts_active = False
jendela_blocklist = None


def load_statistik():
    standar = {"berhasil": 0, "gagal": 0, "streak": 0, "penalti_sampai": 0}
    try:
        with open(FILE_STAT, "r", encoding="utf-8") as f:
            data = json.load(f)
        for kunci in standar:
            if kunci in data:
                standar[kunci] = data[kunci]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return standar


def simpan_statistik():
    try:
        with open(FILE_STAT, "w", encoding="utf-8") as f:
            json.dump(statistik, f)
    except OSError:
        pass


statistik = load_statistik()


def load_blocklist():
    standar = {"aplikasi": [], "website": []}
    try:
        with open(FILE_BLOCKLIST, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for kunci in standar:
                if isinstance(data.get(kunci), list):
                    standar[kunci] = [item for item in data[kunci] if isinstance(item, str)]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return standar


def simpan_blocklist():
    try:
        with open(FILE_BLOCKLIST, "w", encoding="utf-8") as f:
            json.dump(blocklist, f, indent=2)
    except OSError:
        pass


blocklist = load_blocklist()


def update_statistik_label():
    statistik_label.configure(
        text=(
            f"Berhasil: {statistik['berhasil']} "
            f"Gagal: {statistik['gagal']} "
            f"Streak: {statistik['streak']}"
        )
    )


def penalti_aktif():
    return time.time() < statistik["penalti_sampai"]


def mulai_penalti():
    statistik["penalti_sampai"] = time.time() + DURASI_PENALTI
    simpan_statistik()
    hitung_penalti()


def hitung_penalti():
    global penalti_id
    sisa = math.ceil(statistik["penalti_sampai"] - time.time())
    if sisa <= 0:
        penalti_id = None
        tombol_start.configure(text="Mulai")
        status_label.configure(text="Penalti selesai. Siap fokus lagi.")
        return
    tombol_start.configure(text=f"Penalti {format_waktu(sisa)}")
    penalti_id = app.after(500, hitung_penalti)


def tambah_tugas():
    if waktu_berjalan:
        return
    text = tugas_input.get().strip()
    if text == "":
        return
    tugas.append({"text": text, "done": False})
    tugas_input.delete(0, "end")
    update_tugas_list()


def cek_tugas(urutan, box):
    tugas[urutan]["done"] = bool(box.get())
    update_penghitung()


def update_tugas_list():
    for widget in tugas_frame.winfo_children():
        widget.destroy()
    for urutan, tugs in enumerate(tugas):
        box = ctk.CTkCheckBox(tugas_frame, text=tugs["text"])
        box.configure(command=lambda u=urutan, b=box: cek_tugas(u, b))
        if tugs["done"]:
            box.select()
        box.pack(fill="x", padx=10, pady=5)
    update_penghitung()


def update_penghitung():
    selesai = sum(1 for t in tugas if t["done"])
    penghitung.configure(text=f"Selesai: {selesai} / {len(tugas)}")


def format_waktu(total_detiks):
    menits = total_detiks // 60
    detiks = total_detiks % 60
    return f"{menits:02d}:{detiks:02d}"


def durasi_terjemah(text):
    text = text.strip()
    try:
        if ":" in text:
            menits_text, detiks_text = text.split(":")
            menits = int(menits_text)
            detiks = int(detiks_text)
            if not 0 <= detiks < 60:
                return None
        else:
            menits = int(text)
            detiks = 0
    except ValueError:
        return None

    total = menits * 60 + detiks
    if menits < 0 or total <= 0:
        return None
    return total


def atur_mode(sesi):
    status = "disabled" if sesi else "normal"
    tugas_input.configure(state=status)
    tombol_tambah.configure(state=status)
    durasi_masuk.configure(state=status)
    tombol_blocklist.configure(state=status)
    if sesi and jendela_blocklist_hidup():
        jendela_blocklist.destroy()
    tombol_start.configure(text="Fokus !. . ." if sesi else "Mulai")


def bersihkan_website(text):
    """Ambil hostname dari URL atau domain yang dimasukkan pengguna."""
    from urllib.parse import urlsplit

    text = text.strip().lower()
    if not text:
        return ""
    if "://" not in text:
        text = "https://" + text
    try:
        hostname = urlsplit(text).hostname or ""
    except ValueError:
        return ""
    hostname = hostname.rstrip(".").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    # Hanya domain DNS biasa; jangan menerima path, spasi, atau alamat IP.
    pola_domain = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    if not re.fullmatch(pola_domain, hostname):
        return ""
    return hostname



def nama_aplikasi_normal(text):
    """Normalize executable names; matching below is exact, never substring."""
    nama = os.path.basename((text or "").strip()).lower()
    if nama.endswith(".exe"):
        nama = nama[:-4]
    return nama


def cek_aplikasi_blokir():
    """Terminate ONLY processes whose exact process/executable name is listed."""
    if not waktu_berjalan:
        return

    daftar_blokir = {
        nama_aplikasi_normal(item)
        for item in blocklist["aplikasi"]
        if item.strip()
    }
    daftar_blokir.discard("")
    if not daftar_blokir:
        return

    for proses in psutil.process_iter(["pid", "name", "exe"]):
        try:
            if proses.info["pid"] == os.getpid():
                continue

            nama_proses = nama_aplikasi_normal(proses.info.get("name"))
            nama_exe = nama_aplikasi_normal(proses.info.get("exe"))

            # Exact set membership: "firefox" does NOT match "firefox-bin-extra".
            if nama_proses not in daftar_blokir and nama_exe not in daftar_blokir:
                continue

            nama_tampil = proses.info.get("name") or nama_exe or "unknown"
            proses.terminate()
            try:
                proses.wait(timeout=1.0)
            except psutil.TimeoutExpired:
                proses.kill()
                proses.wait(timeout=1.0)
            status_label.configure(text=f"Aplikasi di blocklist ditutup: {nama_tampil}")

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def mulai_pemblokir():
    """Check only listed application names every INTERVAL_BLOKIR seconds."""
    global pemblokir_id
    if not waktu_berjalan:
        pemblokir_id = None
        return
    cek_aplikasi_blokir()
    pemblokir_id = app.after(INTERVAL_BLOKIR * 1000, mulai_pemblokir)


def hentikan_pemblokir():
    global pemblokir_id
    if pemblokir_id is not None:
        try:
            app.after_cancel(pemblokir_id)
        except Exception:
            pass
        pemblokir_id = None


def jalankan_hosts_helper(aksi, domains=None, butuh_prompt=False):
    """Call the separately installed, root-owned helper for listed domains only."""
    if not os.path.isfile(HOSTS_HELPER):
        raise FileNotFoundError(
            f"Helper tidak ditemukan: {HOSTS_HELPER}. Ikuti langkah instalasi helper."
        )
    perintah = ["sudo"]
    if not butuh_prompt:
        perintah.append("-n")
    perintah.extend([HOSTS_HELPER, aksi])
    if domains:
        perintah.extend(domains)
    subprocess.run(perintah, check=True, timeout=30)


def keep_sudo_alive():
    """Keep the user's sudo ticket fresh so cleanup can run when focus ends."""
    global hosts_keepalive_id
    if not website_hosts_active or not waktu_berjalan:
        hosts_keepalive_id = None
        return
    try:
        subprocess.run(["sudo", "-n", "-v"], check=True, timeout=5)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        status_label.configure(
            text="Izin sudo habis. Jika website belum terbuka setelah sesi, jalankan perintah pemulihan."
        )
    hosts_keepalive_id = app.after(60_000, keep_sudo_alive)


def mulai_blokir_website():
    """Block only domains explicitly listed in blocklist.json / tab Website."""
    global website_hosts_active, hosts_keepalive_id
    domains = sorted({bersihkan_website(x) for x in blocklist["website"]})
    domains = [domain for domain in domains if domain]
    if not domains:
        return
    try:
        # Ask for sudo once; app itself must NOT be run as root.
        subprocess.run(["sudo", "-v"], check=True, timeout=60)
        jalankan_hosts_helper("block", domains, butuh_prompt=False)
        website_hosts_active = True
        hosts_keepalive_id = app.after(60_000, keep_sudo_alive)
        status_label.configure(text="Website di tab blocklist sedang diblokir.")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as error:
        website_hosts_active = False
        status_label.configure(
            text=f"Website tidak diblokir (izin/helper gagal). Blocker aplikasi tetap aktif. {error}"
        )


def hentikan_blokir_website():
    """Remove only Flowstate's marked /etc/hosts entries."""
    global website_hosts_active, hosts_keepalive_id
    if hosts_keepalive_id is not None:
        try:
            app.after_cancel(hosts_keepalive_id)
        except Exception:
            pass
        hosts_keepalive_id = None
    if not website_hosts_active:
        return
    try:
        jalankan_hosts_helper("unblock", butuh_prompt=False)
        website_hosts_active = False
        status_label.configure(text="Blockir website dinonaktifkan.")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        status_label.configure(
            text="Gagal membuka blokir otomatis. Jalankan: sudo /usr/local/sbin/flowstate-hosts unblock"
        )


def jendela_blocklist_hidup():
    try:
        return jendela_blocklist is not None and jendela_blocklist.winfo_exists()
    except Exception:
        return False


def isi_daftar(jenis, frame):
    for widget in frame.winfo_children():
        widget.destroy()
    for item in blocklist[jenis]:
        baris = ctk.CTkFrame(frame, fg_color="transparent")
        baris.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(baris, text=item, anchor="w").pack(
            side="left", fill="x", expand=True
        )
        ctk.CTkButton(
            baris,
            text="Hapus",
            width=60,
            fg_color="#b00020",
            hover_color="#800018",
            command=lambda i=item: hapus_item(jenis, i, frame),
        ).pack(side="right")


def tambah_item(jenis, entry, pesan, frame):
    if waktu_berjalan:
        return
    text = entry.get().strip().lower()
    if jenis == "website":
        text = bersihkan_website(text)
        if "." not in text or " " in text:
            pesan.configure(text="Masukkan domain valid, contoh: youtube.com")
            return
    if text == "":
        return
    if text in blocklist[jenis]:
        pesan.configure(text="Sudah ada di daftar.")
        return
    blocklist[jenis].append(text)
    simpan_blocklist()
    entry.delete(0, "end")
    pesan.configure(text="")
    isi_daftar(jenis, frame)


def hapus_item(jenis, item, frame):
    if waktu_berjalan:
        return
    if item in blocklist[jenis]:
        blocklist[jenis].remove(item)
        simpan_blocklist()
    isi_daftar(jenis, frame)


def buat_tab(tab, jenis, petunjuk):
    baris_input = ctk.CTkFrame(tab, fg_color="transparent")
    baris_input.pack(fill="x", pady=(5, 0))

    entry = ctk.CTkEntry(baris_input, placeholder_text=petunjuk)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

    petunjuk_label = ctk.CTkLabel(
        tab,
        text=("Nama proses harus persis, contoh: firefox / discord" if jenis == "aplikasi"
              else "Hanya domain yang ditambahkan yang diblokir, contoh: youtube.com"),
        text_color="gray65",
        wraplength=360,
    )
    petunjuk_label.pack(pady=(4, 0))

    pesan = ctk.CTkLabel(tab, text="", text_color="orange")
    pesan.pack(pady=(5, 0))

    frame = ctk.CTkScrollableFrame(tab)
    frame.pack(fill="both", expand=True, pady=10)

    ctk.CTkButton(
        baris_input,
        text="Tambah",
        width=80,
        command=lambda: tambah_item(jenis, entry, pesan, frame),
    ).pack(side="right")
    entry.bind("<Return>", lambda event: tambah_item(jenis, entry, pesan, frame))
    isi_daftar(jenis, frame)


def buka_blocklist():
    global jendela_blocklist
    if waktu_berjalan:
        return
    if jendela_blocklist_hidup():
        jendela_blocklist.focus()
        return

    jendela_blocklist = ctk.CTkToplevel(app)
    jendela_blocklist.title("Blocklist")
    jendela_blocklist.geometry("420x480")
    jendela_blocklist.transient(app)

    tabs = ctk.CTkTabview(jendela_blocklist)
    tabs.pack(fill="both", expand=True, padx=15, pady=15)
    tabs.add("Aplikasi")
    tabs.add("Website")

    buat_tab(tabs.tab("Aplikasi"), "aplikasi", "Nama aplikasi, mis. discord")
    buat_tab(tabs.tab("Website"), "website", "Alamat web, mis. youtube.com")


def tampil_pengingat():
    sisa = sum(1 for t in tugas if not t["done"])
    suara()

    popup = ctk.CTkToplevel(app)
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)

    lebar, tinggi = 300, 90
    x = app.winfo_screenwidth() - lebar - 20
    popup.geometry(f"{lebar}x{tinggi}+{x}+20")

    ctk.CTkLabel(popup, text="Tetap fokus!", font=("Arial", 18, "bold")).pack(
        pady=(15, 2)
    )
    ctk.CTkLabel(popup, text=f"Tugas tersisa: {sisa}").pack()
    popup.after(4000, popup.destroy)


def mulai_waktu():
    global waktu_tersisa, waktu_berjalan, waktu_total
    if waktu_berjalan:
        return

    if penalti_aktif():
        status_label.configure(text="Masih dalam penalti. Tunggu sampai habis.")
        return

    if len(tugas) == 0:
        status_label.configure(text="Tambah minimal 1 tugas kids")
        return

    total = durasi_terjemah(durasi_masuk.get())
    if total is None:
        status_label.configure(text="Format waktu salah. Pake MM:SS")
        return

    status_label.configure(text="")
    waktu_tersisa = total
    waktu_total = total
    waktu_berjalan = True
    atur_mode(True)
    mulai_blokir_website()
    mulai_pemblokir()
    tick()


def tick():
    global waktu_tersisa, tick_id
    if not waktu_berjalan:
        return
    waktu_label.configure(text=format_waktu(waktu_tersisa))
    if waktu_tersisa <= 0:
        finish_waktu()
        return

    berlalu = waktu_total - waktu_tersisa
    waktu_tersisa -= 1
    tick_id = app.after(1000, tick)

    if berlalu > 0 and berlalu % INTERVAL_PENGINGAT == 0:
        tampil_pengingat()


def evaluasi_sesi(darurat=False):
    selesai = sum(1 for t in tugas if t["done"])
    total = len(tugas)
    penalti = False

    if darurat:
        if PENALTI_SAAT_DARURAT:
            statistik["gagal"] += 1
            statistik["streak"] = 0
            penalti = True
            pesan = f"Sesi dihentikan. Penalti {DURASI_PENALTI} detik"
        else:
            pesan = "Sesi dihentikan. Tidak ada Penalti"
    elif selesai >= MINIMUM_TUGAS:
        statistik["berhasil"] += 1
        statistik["streak"] += 1
        pesan = f"Berhasil! {selesai} / {total} tugas selesai!"
    else:
        statistik["gagal"] += 1
        statistik["streak"] = 0
        penalti = True
        pesan = f"Gagal: {selesai} / {total} tugas. Penalti {DURASI_PENALTI} detik."

    tugas[:] = [t for t in tugas if not t["done"]]
    update_tugas_list()

    simpan_statistik()
    update_statistik_label()
    status_label.configure(text=pesan)
    if penalti:
        mulai_penalti()


def finish_waktu():
    global waktu_berjalan
    waktu_berjalan = False
    hentikan_pemblokir()
    hentikan_blokir_website()
    atur_mode(False)
    waktu_label.configure(text="Waktu Abis!!")
    evaluasi_sesi()


def suara():
    if sys.platform.startswith("win"):
        import winsound

        winsound.MessageBeep()
    elif sys.platform.startswith("linux"):
        file_suara = "/usr/share/sounds/freedesktop/stereo/message.oga"
        for pemutar in ("pw-play", "paplay"):
            if shutil.which(pemutar):
                subprocess.Popen([pemutar, file_suara])
                return
        app.bell()
    else:
        app.bell()


def hentikan_sesi():
    global waktu_berjalan
    if not waktu_berjalan:
        return
    waktu_berjalan = False
    hentikan_pemblokir()
    hentikan_blokir_website()
    if tick_id is not None:
        app.after_cancel(tick_id)
    atur_mode(False)
    waktu_label.configure(text="Sesi dihentikan")
    evaluasi_sesi(darurat=True)


def berhenti_darurat():
    if not waktu_berjalan:
        return

    dialog = ctk.CTkToplevel(app)
    dialog.title("WOI NGAPAIN")
    dialog.geometry("400x320")
    dialog.attributes("-topmost", True)
    dialog.transient(app)
    dialog.after(150, dialog.grab_set)

    ctk.CTkLabel(
        dialog, text="PERINGATAN", font=("Arial", 22, "bold"), text_color="red"
    ).pack(pady=(20, 10))

    peringatan = "Tombol ini Untuk keadaan darurat kids\nMenyerah kah?? \n"
    if PENALTI_SAAT_DARURAT:
        peringatan += (
            "Menghentikan sesi akan dihitung malas, GAGAL dan akan kena penalti\n"
        )
    peringatan += "\nKetik STOP, menyerah untuk berkembang."

    ctk.CTkLabel(dialog, text=peringatan, justify="center").pack(pady=(0, 10), padx=20)

    konfirmasi = ctk.CTkEntry(dialog, justify="center", placeholder_text="STOP")
    konfirmasi.pack(pady=5)

    pesan = ctk.CTkLabel(dialog, text="", text_color="orange")
    pesan.pack()

    def real_berhenti():
        if konfirmasi.get().strip().upper() != "STOP":
            pesan.configure(text="KETIK STOP DENGAN BENAR DEKS")
            return
        dialog.destroy()
        hentikan_sesi()

    tombol_row = ctk.CTkFrame(dialog, fg_color="transparent")
    tombol_row.pack(pady=15)

    ctk.CTkButton(
        tombol_row,
        text="Hentikan Sesi",
        fg_color="#2e7d32",
        hover_color="#1b5e20",
        command=real_berhenti,
    ).pack(side="left", padx=8)

    ctk.CTkButton(
        tombol_row,
        text="Lanjut FOKUS",
        fg_color="#b00020",
        hover_color="#800018",
        command=dialog.destroy,
    ).pack(side="left", padx=8)

    def cek_dialog():
        if not dialog.winfo_exists():
            return
        if not waktu_berjalan:
            dialog.destroy()
            return
        dialog.after(500, cek_dialog)

    cek_dialog()


def tutup_aplikasi():
    """Stop timers and remove Flowstate website rules before closing the GUI."""
    global waktu_berjalan
    waktu_berjalan = False
    hentikan_pemblokir()
    hentikan_blokir_website()
    if tick_id is not None:
        try:
            app.after_cancel(tick_id)
        except Exception:
            pass
    if penalti_id is not None:
        try:
            app.after_cancel(penalti_id)
        except Exception:
            pass
    app.destroy()


app = ctk.CTk()
app.title("FLOWSTATE")
app.geometry("520x790")
app.minsize(480, 650)
app.protocol("WM_DELETE_WINDOW", tutup_aplikasi)

title = ctk.CTkLabel(app, text="Flowstate", font=("Arial", 28, "bold"))
title.pack(pady=(20, 10))

waktu_label = ctk.CTkLabel(app, text="25:00", font=("Arial", 36, "bold"))
waktu_label.pack(pady=(10, 10))

waktu_controls = ctk.CTkFrame(app, fg_color="transparent")
waktu_controls.pack(pady=(0, 20))

durasi_label = ctk.CTkLabel(waktu_controls, text="Waktu (MM:SS):")
durasi_label.pack(side="left", padx=(0, 8))

durasi_masuk = ctk.CTkEntry(waktu_controls, width=60, justify="center")
durasi_masuk.insert(0, "25:00")
durasi_masuk.pack(side="left", padx=(0, 15))

tombol_start = ctk.CTkButton(
    waktu_controls, text="Mulai", width=130, command=mulai_waktu
)
tombol_start.pack(side="left")

status_label = ctk.CTkLabel(app, text="", text_color="orange")
status_label.pack(pady=(0, 10))

subtitle = ctk.CTkLabel(app, text="tambah tugas untuk hari ini")
subtitle.pack(pady=(20, 10))

frame_input = ctk.CTkFrame(app, fg_color="transparent")
frame_input.pack(fill="x", padx=20)

tugas_input = ctk.CTkEntry(frame_input, placeholder_text="Tulis tugas")
tugas_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
tugas_input.bind("<Return>", lambda event: tambah_tugas())

tombol_tambah = ctk.CTkButton(
    frame_input, text="TAMBAH", width=100, command=tambah_tugas
)
tombol_tambah.pack(side="right")

tugas_frame = ctk.CTkScrollableFrame(app, label_text="Tugas Hari ini : ")
tugas_frame.pack(fill="both", expand=True, padx=20, pady=20)

penghitung = ctk.CTkLabel(app, text="SELESAI: 0 / 0", font=("Arial", 16))
penghitung.pack(pady=(0, 5))

statistik_label = ctk.CTkLabel(app, text="", text_color="gray70")
statistik_label.pack(pady=(0, 10))

tombol_blocklist = ctk.CTkButton(
    app, text="Blocklist", fg_color="#37474f", command=buka_blocklist
)
tombol_blocklist.pack(pady=(0, 10))

tombol_darurat = ctk.CTkButton(
    app,
    text="DARURAT: STOP",
    fg_color="#b00020",
    hover_color="#800018",
    command=berhenti_darurat,
)
tombol_darurat.pack(pady=(0, 20))

update_statistik_label()
if penalti_aktif():
    hitung_penalti()
app.mainloop()