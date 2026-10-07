"""Tkinter interface for the progressive image drawing project."""

import argparse
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk

from drawing_engine import DrawingEngine
from image_processor import DRAW_SIZE, prepare_image


PROJECT_FOLDER = Path(__file__).resolve().parent
DEFAULT_IMAGE = PROJECT_FOLDER / "input" / "ganesh09_logo.webp"
CANVAS_SIZE = 700
TICK_MS = 30

COLORS = {
    "background": "#071416",
    "panel": "#0d2022",
    "canvas": "#030d0f",
    "text": "#e4f2ef",
    "muted": "#91aaa6",
    "accent": "#36d9c2",
    "button": "#173638",
    "button_hover": "#205154",
}


class DrawingApp:
    def __init__(self, root: tk.Tk, image_path: Path | None = None) -> None:
        self.root = root
        self.root.title("Progressive Image Drawing Animation")
        self.root.configure(bg=COLORS["background"])
        self.root.geometry("1120x850")
        self.root.minsize(1060, 810)

        self.engine: DrawingEngine | None = None
        self.photo = None
        self.running = False
        self.animation_job: str | None = None
        self.image_path: Path | None = None
        self.speed = tk.IntVar(value=1)

        self._build_interface()

        if image_path is not None:
            self.load_image(image_path)
        elif DEFAULT_IMAGE.exists():
            self.load_image(DEFAULT_IMAGE)
        else:
            self._set_stage("Choose an image to begin")
            self._show_blank_canvas()

    def _build_interface(self) -> None:
        header = tk.Frame(self.root, bg=COLORS["background"])
        header.pack(fill="x", padx=28, pady=(22, 14))

        tk.Label(
            header,
            text="Progressive Image Drawing",
            font=("Segoe UI", 23, "bold"),
            fg=COLORS["text"],
            bg=COLORS["background"],
        ).pack(anchor="w")
        tk.Label(
            header,
            text="A picture rebuilt one point at a time",
            font=("Segoe UI", 10),
            fg=COLORS["muted"],
            bg=COLORS["background"],
        ).pack(anchor="w", pady=(2, 0))

        content = tk.Frame(self.root, bg=COLORS["background"])
        content.pack(fill="both", expand=True, padx=24, pady=(0, 22))

        self.canvas = tk.Canvas(
            content,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg=COLORS["canvas"],
            highlightthickness=1,
            highlightbackground="#244447",
        )
        self.canvas.pack(side="left", padx=(0, 22))
        self.canvas_image = self.canvas.create_image(
            CANVAS_SIZE // 2,
            CANVAS_SIZE // 2,
            anchor="center",
        )

        controls = tk.Frame(content, bg=COLORS["panel"], padx=18, pady=18, width=300)
        controls.pack(side="left", fill="y")
        controls.pack_propagate(False)

        tk.Label(
            controls,
            text="ANIMATION CONTROLS",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["panel"],
        ).pack(anchor="w", pady=(0, 14))

        self._make_button(controls, "Choose image…", self.choose_image).pack(fill="x", pady=(0, 12))
        self.image_name = tk.Label(
            controls,
            text="No image selected",
            font=("Segoe UI", 9),
            fg=COLORS["muted"],
            bg=COLORS["panel"],
            wraplength=260,
            justify="left",
        )
        self.image_name.pack(anchor="w", pady=(0, 18))

        button_row = tk.Frame(controls, bg=COLORS["panel"])
        button_row.pack(fill="x", pady=(0, 8))
        self._make_button(button_row, "Start", self.start).pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._make_button(button_row, "Pause", self.pause).pack(side="left", fill="x", expand=True, padx=(4, 0))

        button_row = tk.Frame(controls, bg=COLORS["panel"])
        button_row.pack(fill="x", pady=(0, 16))
        self._make_button(button_row, "Resume", self.resume).pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._make_button(button_row, "Restart", self.restart).pack(side="left", fill="x", expand=True, padx=(4, 0))

        self._make_button(controls, "Skip to final image", self.skip_to_final).pack(fill="x", pady=(0, 22))

        tk.Label(
            controls,
            text="DRAWING SPEED",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel"],
        ).pack(anchor="w")
        tk.Scale(
            controls,
            from_=1,
            to=5,
            orient="horizontal",
            variable=self.speed,
            showvalue=True,
            resolution=1,
            length=250,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            troughcolor="#214345",
            activebackground=COLORS["accent"],
            highlightthickness=0,
            bd=0,
        ).pack(fill="x", pady=(3, 18))

        tk.Label(
            controls,
            text="CURRENT STAGE",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["text"],
            bg=COLORS["panel"],
        ).pack(anchor="w")
        self.stage_label = tk.Label(
            controls,
            text="READY TO DRAW",
            font=("Segoe UI", 10, "bold"),
            fg=COLORS["accent"],
            bg=COLORS["panel"],
            wraplength=260,
            justify="left",
        )
        self.stage_label.pack(anchor="w", pady=(5, 8))

        self.progress_canvas = tk.Canvas(
            controls,
            width=260,
            height=7,
            bg="#203537",
            highlightthickness=0,
        )
        self.progress_canvas.pack(fill="x", pady=(0, 14))
        self.progress_bar = self.progress_canvas.create_rectangle(0, 0, 0, 7, fill=COLORS["accent"], outline="")

        tk.Label(
            controls,
            text="POINTS  →  SHAPES  →  OUTLINES  →  DETAILS",
            font=("Segoe UI", 8),
            fg=COLORS["muted"],
            bg=COLORS["panel"],
            wraplength=260,
            justify="left",
        ).pack(anchor="w", side="bottom")

    @staticmethod
    def _make_button(parent: tk.Widget, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["text"],
            bg=COLORS["button"],
            activeforeground=COLORS["text"],
            activebackground=COLORS["button_hover"],
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            cursor="hand2",
        )

    def _set_stage(self, text: str) -> None:
        self.stage_label.configure(text=text)

    def _show_blank_canvas(self) -> None:
        blank = ImageTk.PhotoImage(Image.new("RGB", (DRAW_SIZE, DRAW_SIZE), (3, 13, 15)))
        self.photo = blank
        self.canvas.itemconfigure(self.canvas_image, image=self.photo)

    def choose_image(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose an image to draw",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("All files", "*.*")],
        )
        if selected:
            self.load_image(Path(selected))

    def load_image(self, image_path: Path) -> None:
        self._cancel_animation()
        self.running = False
        try:
            image, edge_map = prepare_image(image_path)
            self.engine = DrawingEngine(image, edge_map)
        except (OSError, ValueError) as error:
            messagebox.showerror("Could not open image", str(error), parent=self.root)
            return

        self.image_path = image_path
        self.image_name.configure(text=image_path.name)
        self._show_blank_canvas()
        self._update_progress()
        self._set_stage("READY TO DRAW")

    def start(self) -> None:
        if self.engine is None:
            self.choose_image()
            return
        if self.engine.index >= self.engine.total_dots:
            return
        self.running = True
        self._schedule_animation(0)

    def pause(self) -> None:
        if self.engine is None or self.engine.index >= self.engine.total_dots:
            return
        self.running = False
        self._cancel_animation()
        self._set_stage("PAUSED")

    def resume(self) -> None:
        self.start()

    def restart(self) -> None:
        if self.engine is None:
            return
        self.engine.reset()
        self.running = True
        self._show_blank_canvas()
        self._update_progress()
        self._schedule_animation(0)

    def skip_to_final(self) -> None:
        if self.engine is None:
            return
        self.running = False
        self._cancel_animation()
        self.engine.draw_batch(self.engine.total_dots)
        self._show_drawing()
        self._update_progress()
        self._set_stage("DRAWING COMPLETE")

    def _schedule_animation(self, delay: int) -> None:
        self._cancel_animation()
        self.animation_job = self.root.after(delay, self._animate)

    def _cancel_animation(self) -> None:
        if self.animation_job is not None:
            try:
                self.root.after_cancel(self.animation_job)
            except tk.TclError:
                pass
            self.animation_job = None

    def _animate(self) -> None:
        self.animation_job = None
        if not self.running or self.engine is None:
            return

        speed = self.speed.get()
        if self.engine.index < self.engine.seed_end:
            batch_size = 4 * speed
        elif self.engine.index < self.engine.shape_end:
            batch_size = 16 * speed
        elif self.engine.index < self.engine.edge_end:
            batch_size = 65 * speed
        else:
            batch_size = 260 * speed

        complete = self.engine.draw_batch(batch_size)
        self._show_drawing()
        self._update_progress()

        if complete:
            self.running = False
            self._set_stage("DRAWING COMPLETE")
        else:
            self._set_stage(self.engine.stage)
            self.animation_job = self.root.after(TICK_MS, self._animate)

    def _show_drawing(self) -> None:
        if self.engine is None:
            self._show_blank_canvas()
            return
        self.photo = ImageTk.PhotoImage(self.engine.image)
        self.canvas.itemconfigure(self.canvas_image, image=self.photo)

    def _update_progress(self) -> None:
        progress = self.engine.progress if self.engine else 0.0
        width = max(1, self.progress_canvas.winfo_width())
        self.progress_canvas.coords(self.progress_bar, 0, 0, round(width * progress), 7)


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw an image gradually using colored dots.")
    parser.add_argument("--image", type=Path, help="Image file to reconstruct (PNG, JPG, WebP, or BMP).")
    args = parser.parse_args()

    root = tk.Tk()
    DrawingApp(root, args.image)
    root.mainloop()


if __name__ == "__main__":
    main()
