import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FlowstateApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLOWSTATE !")
        self.geometry("900x600")
        self.minsize(700, 500)

        self.title_label = ctk.CTkLabel(
            self,
            text="Flowstate",
            font=ctk.CTkFont(size=32, weight="Bold"),
        )
        self.title_label.pack(pady=40)

        self.subtitle_label = ctk.CTklabel(
            self,
            text="Stay Focused. Finish what matters.",
            font=ctk.CTkLabel(size=16),
        )
        self.subtitle_label.pack()

if __name__ == "__main__":
    app = FlowstateApp()
    app.mainloop()
