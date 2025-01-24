# scrollable_frame.py

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create a canvas
        canvas = tk.Canvas(self, borderwidth=0, background="#f0f0f0")
        self.canvas = canvas

        # Add a vertical scrollbar to the canvas
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scrollbar.set)

        # Add a horizontal scrollbar to the canvas
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=canvas.xview)
        canvas.configure(xscrollcommand=h_scrollbar.set)

        # Position the scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        # Create an internal frame to hold widgets
        self.scrollable_frame = ttk.Frame(canvas, padding=(10, 10, 10, 10))

        # Bind the frame to the canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Create a window inside the canvas
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
