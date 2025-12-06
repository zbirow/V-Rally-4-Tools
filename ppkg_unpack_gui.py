import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import struct
import os
import threading

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VRallyUnpackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("V-Rally 4 / PKG Unpacker")
        self.geometry("700x550")
        self.resizable(False, False)

        self.file_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to work.")
        self.is_running = False

        self.frame_file = ctk.CTkFrame(self)
        self.frame_file.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame_file, text=".PKG File:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.entry_file = ctk.CTkEntry(self.frame_file, textvariable=self.file_path_var, width=500)
        self.entry_file.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        
        self.btn_file = ctk.CTkButton(self.frame_file, text="Browse", width=100, command=self.browse_file)
        self.btn_file.pack(side="right", padx=10, pady=10)

        self.frame_out = ctk.CTkFrame(self)
        self.frame_out.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame_out, text="Output Folder:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.entry_out = ctk.CTkEntry(self.frame_out, textvariable=self.output_path_var, width=500)
        self.entry_out.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        
        self.btn_out = ctk.CTkButton(self.frame_out, text="Browse", width=100, command=self.browse_folder)
        self.btn_out.pack(side="right", padx=10, pady=10)

        self.label_status = ctk.CTkLabel(self, textvariable=self.status_var, text_color="cyan")
        self.label_status.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=650)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.log_box = ctk.CTkTextbox(self, width=660, height=200)
        self.log_box.pack(pady=10)
        self.log_box.insert("0.0", "--- APPLICATION LOG ---\n")
        self.log_box.configure(state="disabled")

        self.btn_start = ctk.CTkButton(self, text="START UNPACKING", height=40, font=("Arial", 14, "bold"), command=self.start_thread)
        self.btn_start.pack(pady=10, padx=20, fill="x")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("PKG Files", "*.PKG"), ("All Files", "*.*")])
        if filename:
            self.file_path_var.set(filename)
            if not self.output_path_var.get():
                suggested_dir = os.path.join(os.path.dirname(filename), "EXTRACTED")
                self.output_path_var.set(suggested_dir)

    def browse_folder(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_path_var.set(dirname)

    def start_thread(self):
        if self.is_running:
            return
        
        input_path = self.file_path_var.get()
        output_path = self.output_path_var.get()

        if not os.path.exists(input_path):
            messagebox.showerror("Error", "Input file path is invalid.")
            return

        if not output_path:
            messagebox.showerror("Error", "Select an output folder.")
            return

        self.is_running = True
        self.btn_start.configure(state="disabled", text="WORKING...")
        self.log("-" * 40)
        self.log(f"Starting file analysis: {os.path.basename(input_path)}")
        
        thread = threading.Thread(target=self.run_extraction_logic, args=(input_path, output_path))
        thread.start()

    def run_extraction_logic(self, file_path, output_dir):
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                if magic != b'PPKG':
                    self.log(f"ERROR: Invalid file header! Expected PPKG, got: {magic}")
                    self.finish_process()
                    return

                version = struct.unpack('<I', f.read(4))[0]
                file_count = struct.unpack('<I', f.read(4))[0]
                index_offset = struct.unpack('<I', f.read(4))[0]
                
                f.read(32)

                self.log(f"Header OK. Version: {version}")
                self.log(f"Number of files to extract: {file_count}")
                self.status_var.set(f"Analyzing index ({file_count} files)...")

                files_toc = []
                
                for i in range(file_count):
                    name_len_bytes = f.read(4)
                    if not name_len_bytes: break
                    name_len = struct.unpack('<I', name_len_bytes)[0]

                    name_bytes = f.read(name_len)
                    try:
                        rel_path = name_bytes.decode('utf-8', errors='replace').strip('\x00')
                    except:
                        rel_path = f"UNKNOWN/file_{i}.dat"

                    meta_block = f.read(80)
                    
                    data_offset = struct.unpack('<I', meta_block[4:8])[0]
                    data_size = struct.unpack('<I', meta_block[20:24])[0]

                    files_toc.append({
                        'path': rel_path,
                        'offset': data_offset,
                        'size': data_size
                    })

                self.log(f"Index loaded. Starting disk write...")
                
                for idx, entry in enumerate(files_toc):
                    if idx % 10 == 0:
                        progress = (idx + 1) / file_count
                        self.progress_bar.set(progress)
                        self.status_var.set(f"Extracting: {idx + 1}/{file_count}")

                    safe_path = entry['path'].replace('\\', os.sep)
                    full_out_path = os.path.join(output_dir, safe_path)
                    
                    os.makedirs(os.path.dirname(full_out_path), exist_ok=True)

                    f.seek(entry['offset'])

                    check_magic = f.read(4)
                    
                    if check_magic != b'PKGB':
                        self.log(f"[WARN] Missing PKGB in {entry['path']} (Offset: {hex(entry['offset'])})")
                        pass
                    
                    bytes_to_read = entry['size'] - 4
                    if bytes_to_read < 0: bytes_to_read = 0

                    data = f.read(bytes_to_read)

                    with open(full_out_path, 'wb') as out_file:
                        out_file.write(data)

                self.log("COMPLETED SUCCESSFULLY.")
                messagebox.showinfo("Success", f"Extracted {len(files_toc)} files!")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", str(e))
        
        finally:
            self.finish_process()

    def finish_process(self):
        self.is_running = False
        self.btn_start.configure(state="normal", text="START UNPACKING")
        self.status_var.set("Ready.")
        self.progress_bar.set(0)

if __name__ == "__main__":
    app = VRallyUnpackerApp()
    app.mainloop()