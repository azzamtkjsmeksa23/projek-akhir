import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FlowstateApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FLOWSTATE !")
        self.geometry("900x600")
        self.minsize(700, 500)
        self.tasks = []

        self.title_label = ctk.CTkLabel(
            self,
            text="Flowstate",
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        self.title_label.pack(pady=(30, 10))

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=30, pady=10)

        self.add_button = ctk.CTkButton(
            self.input_frame,
            text="Add Task",
            height=40,
            command=self.add_task,
        )
        self.add_button.pack(side="right")

        self.task_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="ketik tugasnya, trus enter",
            height=40,
        )
        self.task_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.task_entry.bind("<Return>", self.add_task)
        self.task_list_frame = ctk.CTkScrollableFrame(self,label_text="tugas hari ini.")
        self.task_list_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="Stay Focused. Finish what matters.",
            font=ctk.CTkFont(size=16),
        )
        self.subtitle_label.pack()

    def add_task(self, event=None):
        text = self.task_entry.get().strip()
        if text == "":
            return

        self.tasks.append(text)
        self.task_entry.delete(0, "end")
        self.refresh_task_list()

    def refresh_task_list(self):
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        for number, task in enumerate(self.tasks, start=1):
            label = ctk.CTkLabel(
                self.task_list_frame,
                text=f"{number}. {task}",
                anchor="w",
                font=ctk.CTkFont(size=16),
            )
            label.pack(fill="x", padx=10, pady=4)

if __name__ == "__main__":
    app = FlowstateApp()
    app.mainloop()
