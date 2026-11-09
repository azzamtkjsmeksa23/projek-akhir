import customtkinter as ctk

tugas = []


def tambah_tugas():
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


app = ctk.CTk()
app.title("FLOWSTATE")
app.geometry("500x600")
title = ctk.CTkLabel(app, text="Flowstate", font=("Arial", 28, "bold"))
title.pack(pady=(20, 10))
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
