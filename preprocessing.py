import os
import json
import tkinter as tk
from tkinter import font as tkfont

class LabelingTool:
    def __init__(self, root, image_folder, output_dir):
        self.root = root
        self.root.title("Urdu OCR Ground Truth Labeler")

        self.image_folder = image_folder
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "output_images")
        os.makedirs(self.images_dir, exist_ok=True)

        self.json_path = os.path.join(output_dir, "dataset.json")

        # Load existing records
        self.records = []
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.records = json.load(f)

        # Get already labeled image filenames
        self.labeled_files = set(
            os.path.basename(r["image_path"]) for r in self.records
        )

        # Get all images from input folder
        self.image_files = sorted([
            f for f in os.listdir(image_folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'))
            and not f.startswith("'")
        ])

        # Filter out already labeled
        self.remaining_files = [
            f for f in self.image_files
            if f"{os.path.splitext(f)[0]}.png" not in self.labeled_files
        ]

        self.current_index = 0

        self._build_ui()
        self.load_current_image()

    def _build_ui(self):
        # Status label
        self.status_label = tk.Label(self.root, text="", font=("Arial", 12), pady=5)
        self.status_label.pack()

        # Image display
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)

        # Urdu text entry (large font for readability)
        urdu_font = tkfont.Font(family="Jameel Noori Nastaleeq", size=20)
        try:
            self.text_entry = tk.Text(self.root, height=4, width=60, font=urdu_font, wrap=tk.WORD)
        except:
            self.text_entry = tk.Text(self.root, height=4, width=60, font=("Arial", 16), wrap=tk.WORD)

        self.text_entry.pack(pady=10)
        self.text_entry.focus_set()

        # Buttons frame
        self.btn_frame = tk.Frame(self.root)
        self.btn_frame.pack(pady=10)

        tk.Button(self.btn_frame, text="⏮ Skip (no text/blank)", command=self.skip_image,
                  bg="#aaaaaa", padx=15, pady=5).pack(side=tk.LEFT, padx=5)

        tk.Button(self.btn_frame, text="💾 Save & Next →", command=self.save_and_next,
                  bg="#27ae60", fg="white", padx=15, pady=5,
                  font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=5)

        # Keyboard shortcut: Ctrl+Enter to save
        self.root.bind("<Control-Return>", lambda e: self.save_and_next())

        # Info label
        self.info_label = tk.Label(self.root, text="Type the Urdu text exactly as shown, then click Save & Next (or Ctrl+Enter)",
                                   fg="#555555", pady=5)
        self.info_label.pack()

        # Completion label (hidden by default)
        self.done_label = tk.Label(self.root, text="✅ All images labeled!\n\nGreat job — your dataset is complete.",
                                    font=("Arial", 18, "bold"), fg="#27ae60", pady=40)

    def load_current_image(self):
        if self.current_index >= len(self.remaining_files):
            self.show_completion_screen()
            return

        img_name = self.remaining_files[self.current_index]
        img_path = os.path.join(self.image_folder, img_name)

        # Load and display image
        from PIL import Image, ImageTk
        img = Image.open(img_path).convert("RGB")

        # Resize if too large (max width 800px)
        max_width = 800
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)))

        self.tk_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=self.tk_img)

        # Update status
        total = len(self.image_files)
        labeled = len(self.records)
        remaining = len(self.remaining_files) - self.current_index
        self.status_label.config(
            text=f"📄 {img_name}  |  Labeled: {labeled}  |  Remaining: {remaining} / {total}"
        )

        # Clear text box
        self.text_entry.delete("1.0", tk.END)
        self.text_entry.focus_set()

    def show_completion_screen(self):
        # Hide everything else
        self.image_label.config(image="", text="")
        self.text_entry.pack_forget()
        self.btn_frame.pack_forget()
        self.info_label.pack_forget()

        # Update status
        total = len(self.image_files)
        labeled = len(self.records)
        self.status_label.config(text=f"Total labeled: {labeled} / {total}")

        # Show done message
        self.done_label.pack(pady=20)

    def save_and_next(self):
        if self.current_index >= len(self.remaining_files):
            return

        img_name = self.remaining_files[self.current_index]
        img_path = os.path.join(self.image_folder, img_name)

        text = self.text_entry.get("1.0", tk.END).strip()

        # Save image to output folder
        from PIL import Image
        img_stem = os.path.splitext(img_name)[0]
        output_filename = f"{img_stem}.png"
        output_path = os.path.join(self.images_dir, output_filename)

        if not os.path.exists(output_path):
            img = Image.open(img_path).convert("RGB")
            img.save(output_path, format="PNG")

        # Add record
        record = {
            "image_path": os.path.abspath(output_path).replace("\\", "/"),
            "ground_truth": text,
            "split": "train" if (len(self.records) % 10 != 0) else "valid"
        }
        self.records.append(record)

        # Save JSON immediately (so progress is never lost)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=4, ensure_ascii=False)

        # Move to next
        self.current_index += 1
        self.load_current_image()

    def skip_image(self):
        self.current_index += 1
        self.load_current_image()


if __name__ == "__main__":
    INPUT_IMAGE_FOLDER = r"input image"
    OUTPUT_FOLDER = r"output"

    root = tk.Tk()
    root.geometry("900x600")
    app = LabelingTool(root, INPUT_IMAGE_FOLDER, OUTPUT_FOLDER)
    root.mainloop()
