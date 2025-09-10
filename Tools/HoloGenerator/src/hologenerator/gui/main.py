"""
HoloGenerator GUI Interface

Tkinter-based graphical interface for the configuration generator.
All tkinter imports are protected with try-catch blocks.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Protected tkinter imports
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    ttk = None
    filedialog = None
    messagebox = None
    scrolledtext = None

if TKINTER_AVAILABLE:
    from hologenerator.core.generator import ConfigurationGenerator


class HoloGeneratorGUI:
    """Main GUI application for the HoloGenerator."""
    
    def __init__(self, root: tk.Tk):
        if not TKINTER_AVAILABLE:
            raise ImportError("tkinter is not available")
            
        self.root = root
        self.root.title("HoloGenerator - KOTOR Configuration Generator")
        self.root.geometry("800x600")
        
        # Variables for paths
        self.path1_var = tk.StringVar()
        self.path2_var = tk.StringVar()
        self.output_var = tk.StringVar(value="changes.ini")
        self.file_mode_var = tk.BooleanVar()
        
        # Configuration generator
        self.generator = ConfigurationGenerator()
        
        # Create the UI
        self.create_widgets()
    
    def create_widgets(self):
        """Create and layout all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="HoloGenerator", 
            font=("Arial", 18, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Mode selection
        mode_frame = ttk.LabelFrame(main_frame, text="Comparison Mode", padding="5")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Radiobutton(
            mode_frame, 
            text="Installation Mode (compare full KOTOR installations)",
            variable=self.file_mode_var,
            value=False
        ).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="File Mode (compare individual files)",
            variable=self.file_mode_var,
            value=True
        ).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Path 1 selection
        ttk.Label(main_frame, text="Original Path:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.path1_var, width=60).grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_path1).grid(
            row=2, column=2, padx=5, pady=5
        )
        
        # Path 2 selection
        ttk.Label(main_frame, text="Modified Path:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.path2_var, width=60).grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_path2).grid(
            row=3, column=2, padx=5, pady=5
        )
        
        # Output file selection
        ttk.Label(main_frame, text="Output changes.ini:").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        ttk.Entry(main_frame, textvariable=self.output_var, width=60).grid(
            row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(
            row=4, column=2, padx=5, pady=5
        )
        
        # Generate button
        self.generate_button = ttk.Button(
            main_frame, 
            text="Generate Configuration", 
            command=self.generate_config
        )
        self.generate_button.grid(row=5, column=0, columnspan=3, pady=20)
        
        # Output text area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, 
            height=15, 
            width=80,
            wrap=tk.WORD
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def browse_path1(self):
        """Browse for the first path."""
        if self.file_mode_var.get():
            path = filedialog.askopenfilename(
                title="Select Original File"
            )
        else:
            path = filedialog.askdirectory(
                title="Select Original KOTOR Installation Directory"
            )
        if path:
            self.path1_var.set(path)
    
    def browse_path2(self):
        """Browse for the second path."""
        if self.file_mode_var.get():
            path = filedialog.askopenfilename(
                title="Select Modified File"
            )
        else:
            path = filedialog.askdirectory(
                title="Select Modified KOTOR Installation Directory"
            )
        if path:
            self.path2_var.set(path)
    
    def browse_output(self):
        """Browse for the output file path."""
        path = filedialog.asksaveasfilename(
            title="Save changes.ini file as",
            defaultextension=".ini",
            filetypes=[("INI files", "*.ini"), ("All files", "*.*")]
        )
        if path:
            self.output_var.set(path)
    
    def generate_config(self):
        """Generate the configuration file."""
        path1 = Path(self.path1_var.get().strip())
        path2 = Path(self.path2_var.get().strip())
        output_path = Path(self.output_var.get().strip())
        
        if not path1.exists():
            messagebox.showerror("Error", f"Path '{path1}' does not exist")
            return
        
        if not path2.exists():
            messagebox.showerror("Error", f"Path '{path2}' does not exist")
            return
        
        try:
            self.output_text.delete(1.0, tk.END)
            self.output_text.insert(tk.END, "Generating configuration...\n")
            self.root.update()
            
            if self.file_mode_var.get():
                result = self.generator.generate_from_files(path1, path2)
                # Save result if we have an output path
                if result and output_path:
                    output_path.write_text(result, encoding='utf-8')
            else:
                result = self.generator.generate_config(path1, path2, output_path)
            
            if result:
                self.output_text.insert(tk.END, f"Configuration generated successfully!\n")
                self.output_text.insert(tk.END, f"Output saved to: {output_path}\n\n")
                self.output_text.insert(tk.END, "Generated configuration:\n")
                self.output_text.insert(tk.END, "-" * 40 + "\n")
                self.output_text.insert(tk.END, result)
                messagebox.showinfo("Success", "Configuration generated successfully!")
            else:
                self.output_text.insert(tk.END, "No differences found.\n")
                messagebox.showinfo("No Changes", "No differences found between the selected paths.")
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.output_text.insert(tk.END, f"{error_msg}\n")
            messagebox.showerror("Error", error_msg)


def main():
    """Main function to run the GUI application."""
    if not TKINTER_AVAILABLE:
        print("Error: tkinter is not available. Please install tkinter to use the GUI.")
        sys.exit(1)
    
    try:
        root = tk.Tk()
        app = HoloGeneratorGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Failed to start GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()