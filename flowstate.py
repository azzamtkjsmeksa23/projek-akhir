import json
import math
import os
import time
import sys
import subprocess
import shutil

import customtkinter as ctk

ctk.set_appearance_mode("dark")

# rules
INTERVAL_PENGINGAT = 10
MINIMUM_TUGAS = 1
DURASI_PENALTI = 15
PENALTI_SAAT_DARURAT = True
FILE_STAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statistik.json")

# data
tugas = []
waktu_tersisa = 0
waktu_total = 0
waktu_berjalan = False
tick_id = None
penalti_id = None


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
    sisa = math.ceil(statisstik["penalti_sampai"] - time.time())
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
    tombol_start.configure(text="Fokus !. . ." if sesi else "Mulai")


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

    if len(tugas) == 0:
        status_label.configure(text="Tambah minimal 1 tugas kids")
        return

    total = durasi_terjemah(durasi_masuk.get())
    if total is None:
        waktu_label.configure(
            text="format waktu mu salah harusnya ini MM:SS", font=("Arial", 28, "bold")
        )
        return

    status_label.configure(text="")
    waktu_tersisa = total
    waktu_total = total
    waktu_berjalan = True
    atur_mode(True)
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


def finish_waktu():
    global waktu_berjalan
    waktu_berjalan = False
    atur_mode(False)
    selesai = sum(1 for t in tugas if t["done"])
    waktu_label.configure(text="Waktu Abis!!")
    status_label.configure(text=f"Sesi selesai: {selesai} / {len(tugas)} tugas")


def suara():
    if sys.platform.startswith("win"):
        import windsound

        windsound.MessageBeep()
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
    if tick_id is not None:
        app.after_cancel(tick_id)
    atur_mode(False)
    waktu_label.configure(text="Sesi dihentikan")
    status_label.configure(text="Sesi dihentikan lewat tombol darurat.")


def berhenti_darurat():
    if not waktu_berjalan:
        return

    dialog = ctk.CTkToplevel(app)
    dialog.title("WOI NGAPAIN")
    dialog.geometry("400x300")
    dialog.attributes("-topmost", True)
    dialog.transient(app)
    dialog.after(150, dialog.grab_set)

    ctk.CTkLabel(
        dialog, text="PERINGATAN", font=("Arial", 22, "bold"), text_color="red"
    ).pack(pady=(20, 10))

    ctk.CTkLabel(
        dialog,
        text=(
            "TOMBOL INI HANYA UNTUK DARURAT\n"
            "MENYERAH KAH??\n\n"
            "KETIK STOP UNTUK BERHENTI BERKEMBANG"
        ),
        justify="center",
    ).pack(pady=(0, 10), padx=20)

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
        if not dialog.winfo_exist():
            return
        if not waktu_berjalan:
            dialog.destroy()
            return
        dialog.after(500, cek_dialog)

    cek_dialog()


app = ctk.CTk()
app.title("FLOWSTATE")
app.geometry("500x720")

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

statistik_label = ctk.CTkLable(app, text="", text_color="gray70")
statistik_label.pack(pady=(0, 10))

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
