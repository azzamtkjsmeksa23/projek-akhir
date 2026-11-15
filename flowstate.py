import customtkinter as ctk
import subprocess
import shutil

ctk.set_appearance_mode("dark")

INTERVAL_PENGINGAT = 10
tugas = []
waktu_tersisa = 0
waktu_total = 0
waktu_berjalan = False


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
    global waktu_tersisa
    if not waktu_berjalan:
        return
    waktu_label.configure(text=format_waktu(waktu_tersisa))
    if waktu_tersisa <= 0:
        finish_waktu()
        return

    berlalu = waktu_total - waktu_tersisa
    waktu_tersisa -= 1
    app.after(1000, tick)

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
    file_suara = "/usr/share/sounds/freedesktop/stereo/message.oga"
    for pemutar in ("pw-play", "paplay"):
        if shutil.which(pemutar):
            subprocess.Popen([pemutar, file_suara])
            return
    app.bell()


app = ctk.CTk()
app.title("FLOWSTATE")
app.geometry("500x600")

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
    waktu_controls, text="Mulai", width=100, command=mulai_waktu
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
penghitung.pack(pady=(0, 20))

app.mainloop()
