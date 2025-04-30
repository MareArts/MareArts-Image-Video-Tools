import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import shutil
from typing import List, Dict, Tuple, Optional


class MosaicRegion:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)


class ImageViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Main window configuration
        self.title("Image Viewer")
        self.geometry("1200x800")
        self.minsize(800, 600)
        
        # Application state
        self.current_folder = None
        self.image_files = []
        self.current_image_index = -1
        self.current_image_path = None
        self.original_image = None
        self.displayed_image = None
        self.tk_image = None
        self.mosaic_regions = []
        self.is_selecting = False
        self.selection_start = None
        self.selection_rectangle = None
        self.mosaic_rectangles = []
        self.modified = False
        self.resize_timer_id = None
        
        # Create UI components
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()
        self._create_statusbar()
        
        # Bind keyboard shortcuts
        self.bind("<Prior>", lambda e: self.previous_image())  # Page Up
        self.bind("<Next>", lambda e: self.next_image())       # Page Down
        self.bind("<Control-s>", lambda e: self.save_image())
        self.bind("<Command-s>", lambda e: self.save_image())  # For macOS
        self.bind("<Delete>", lambda e: self.delete_image())
        self.bind("a", lambda e: self.move_to_subfolder("a"))
        self.bind("f", lambda e: self.move_to_subfolder("f"))
        
        # Bind window resize event
        self.bind("<Configure>", self.on_window_resize)
        
        # Focus the window
        self.focus_force()
    
    # Simple method to regain focus after dialog boxes
    def regain_focus(self):
        """Regain focus to the main window after dialogs"""
        self.after(100, lambda: [self.focus_force(), self.lift()])
    
    def on_window_resize(self, event):
        """Handle window resize event with debouncing"""
        # Only respond to root window's resize events, not child widgets
        if event.widget != self:
            return
            
        # Cancel any existing timer
        if self.resize_timer_id:
            self.after_cancel(self.resize_timer_id)
            
        # Set a new timer
        self.resize_timer_id = self.after(100, self._handle_resize)
    
    def _handle_resize(self):
        """Resize and redisplay the image after resize is complete"""
        self.resize_timer_id = None
        
        # Only redisplay if we have an image
        if self.displayed_image:
            self._resize_and_display_image()
    
    def navigate_file_list(self, event):
        """Handle up/down arrow key navigation in the file list"""
        if not self.image_files:
            return "break"
            
        current_selection = self.file_listbox.curselection()
        
        if not current_selection:
            # If nothing is selected, select the first item
            if event.keysym == "Down" and self.file_listbox.size() > 0:
                self.file_listbox.selection_set(0)
                self.file_listbox.see(0)
                self.load_image(0)
            return "break"
            
        current_index = current_selection[0]
        
        if event.keysym == "Up" and current_index > 0:
            new_index = current_index - 1
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(new_index)
            self.file_listbox.see(new_index)
            self.load_image(new_index)
        elif event.keysym == "Down" and current_index < self.file_listbox.size() - 1:
            new_index = current_index + 1
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(new_index)
            self.file_listbox.see(new_index)
            self.load_image(new_index)
            
        # Prevent the event from propagating further
        return "break"
    
    def _create_menu(self):
        """Create the application menu"""
        menu_bar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open Folder", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_command(label="Move To 'a' Folder", command=lambda: self.move_to_subfolder("a"), accelerator="a")
        file_menu.add_command(label="Move To 'f' Folder", command=lambda: self.move_to_subfolder("f"), accelerator="f")
        file_menu.add_command(label="Move To...", command=self.move_image)
        file_menu.add_command(label="Delete", command=self.delete_image, accelerator="Delete")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Toggle Selection Tool", command=self.toggle_selection)
        edit_menu.add_command(label="Clear Mosaic Regions", command=self.clear_mosaic_regions)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        
        # Navigation menu
        nav_menu = tk.Menu(menu_bar, tearoff=0)
        nav_menu.add_command(label="Previous Image", command=self.previous_image, accelerator="Page Up")
        nav_menu.add_command(label="Next Image", command=self.next_image, accelerator="Page Down")
        menu_bar.add_cascade(label="Navigation", menu=nav_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.config(menu=menu_bar)
    
    def _create_toolbar(self):
        """Create the toolbar with buttons"""
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Toolbar buttons
        ttk.Button(toolbar_frame, text="Open Folder", command=self.open_folder).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, pady=2, fill=tk.Y)
        
        ttk.Button(toolbar_frame, text="Previous", command=self.previous_image).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar_frame, text="Next", command=self.next_image).pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, pady=2, fill=tk.Y)
        
        self.selection_button = ttk.Button(toolbar_frame, text="Selection Tool", command=self.toggle_selection)
        self.selection_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        ttk.Button(toolbar_frame, text="Save", command=self.save_image).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar_frame, text="Move To...", command=self.move_image).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(toolbar_frame, text="Delete", command=self.delete_image).pack(side=tk.LEFT, padx=2, pady=2)
    
    def _create_main_area(self):
        """Create the main content area (file list and image view)"""
        # Main container with resizable panels
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - File list
        self.file_list_frame = ttk.Frame(paned_window, width=200)
        paned_window.add(self.file_list_frame, weight=1)
        
        # File list with scrollbar
        file_list_label = ttk.Label(self.file_list_frame, text="Files")
        file_list_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        file_list_container = ttk.Frame(self.file_list_frame)
        file_list_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(file_list_container)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        
        # Add keyboard navigation for the file list
        self.file_listbox.bind("<Up>", self.navigate_file_list)
        self.file_listbox.bind("<Down>", self.navigate_file_list)
        self.file_listbox.bind("<Return>", lambda e: self.on_file_select(None))
        
        file_scrollbar = ttk.Scrollbar(file_list_container, orient=tk.VERTICAL, command=self.file_listbox.yview)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)
        
        # Right panel - Image view
        self.image_frame = ttk.Frame(paned_window)
        paned_window.add(self.image_frame, weight=3)
        
        # Canvas for image display
        self.canvas = tk.Canvas(self.image_frame, bg="gray90")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind canvas events for selection
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
    
    def _create_statusbar(self):
        """Create the status bar at the bottom"""
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")
    
    def open_folder(self):
        """Open a folder and load image files"""
        folder_path = filedialog.askdirectory(title="Select Image Folder")
        self.regain_focus()
        
        if not folder_path:
            return
        
        self.current_folder = folder_path
        self.image_files = []
        self.file_listbox.delete(0, tk.END)
        
        # Find image files in the folder
        valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(valid_extensions):
                self.image_files.append(filename)
                self.file_listbox.insert(tk.END, filename)
        
        # Update status bar
        self.status_var.set(f"Loaded {len(self.image_files)} images from {os.path.basename(folder_path)}")
        
        # Load first image if available
        if self.image_files:
            self.file_listbox.selection_set(0)
            self.load_image(0)
    
    def on_file_select(self, event):
        """Handle file selection from the list"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.image_files):
                self.load_image(index)
    
    def load_image(self, index):
        """Load and display the image at the given index"""
        if not self.image_files or index < 0 or index >= len(self.image_files):
            return
        
        # Check for unsaved changes
        if self.modified and self.current_image_path:
            if not messagebox.askyesno("Unsaved Changes", 
                                      "You have unsaved changes. Continue without saving?"):
                self.regain_focus()
                return
            self.regain_focus()
        
        # Reset state
        self.current_image_index = index
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(index)
        self.file_listbox.see(index)
        self.mosaic_regions = []
        self.modified = False
        
        # Load the image
        filename = self.image_files[index]
        self.current_image_path = os.path.join(self.current_folder, filename)
        try:
            self.original_image = Image.open(self.current_image_path)
            self.display_image()
            self.status_var.set(f"Loaded: {filename} ({self.original_image.width}x{self.original_image.height})")
        except Exception as e:
            self.status_var.set(f"Error loading image: {str(e)}")
            messagebox.showerror("Error", f"Could not load image: {str(e)}")
            self.regain_focus()
    
    def display_image(self):
        """Display the current image on the canvas"""
        if self.original_image is None:
            return
        
        # Clear the canvas
        self.canvas.delete("all")
        
        # Copy the original to avoid modifying it
        self.displayed_image = self.original_image.copy()
        
        # Apply mosaic effect to regions
        if self.mosaic_regions:
            try:
                # Create a draw object
                draw = ImageDraw.Draw(self.displayed_image)
                
                # Calculate base mosaic pixel size based on overall image dimensions
                img_width, img_height = self.original_image.size
                base_pixel_size = max(10, min(img_width, img_height) // 50)
                
                for region in self.mosaic_regions:
                    # Extract the region, ensure coordinates are within image bounds
                    x1 = max(0, min(region.x1, self.original_image.width - 1))
                    y1 = max(0, min(region.y1, self.original_image.height - 1))
                    x2 = max(0, min(region.x2, self.original_image.width))
                    y2 = max(0, min(region.y2, self.original_image.height))
                    
                    # Skip invalid regions
                    if x2 <= x1 or y2 <= y1:
                        continue
                    
                    # Extract the region
                    region_img = self.original_image.crop((x1, y1, x2, y2))
                    
                    # Apply mosaic effect (pixelate) - use base size
                    # Adjust pixel size based on region size and base size
                    region_width = x2 - x1
                    region_height = y2 - y1
                    
                    # For small regions, use smaller pixel size
                    if region_width < img_width * 0.1 or region_height < img_height * 0.1:
                        pixel_size = max(5, min(region_width, region_height) // 5)
                    else:
                        # For larger regions, use base pixel size
                        pixel_size = base_pixel_size
                    
                    pixel_size = max(1, pixel_size)  # Ensure it's at least 1
                    
                    # Ensure region is large enough to resize
                    if region_img.width > 0 and region_img.height > 0:
                        small_width = max(1, region_img.width // pixel_size)
                        small_height = max(1, region_img.height // pixel_size)
                        
                        small_img = region_img.resize(
                            (small_width, small_height),
                            resample=Image.NEAREST
                        )
                        result = small_img.resize(region_img.size, Image.NEAREST)
                        
                        # Paste back
                        self.displayed_image.paste(result, (x1, y1))
                    
                    # Draw rectangle borders
                    draw.rectangle([x1, y1, x2, y2], outline="blue", width=2)
            except Exception as e:
                print(f"Error applying mosaic: {e}")
                messagebox.showerror("Error", f"Error applying mosaic effect: {str(e)}")
                self.regain_focus()
        
        self._resize_and_display_image()
    
    def _resize_and_display_image(self):
        """Resize and display the image based on current canvas size"""
        if self.displayed_image is None:
            return
            
        # Get current canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Ensure we have valid dimensions (when canvas is not yet fully created)
        if canvas_width <= 1:
            canvas_width = 800
        if canvas_height <= 1:
            canvas_height = 600
        
        img_width, img_height = self.displayed_image.size
        
        # Calculate the scaling factor to fit the image
        scale_width = canvas_width / img_width if img_width > 0 else 1.0
        scale_height = canvas_height / img_height if img_height > 0 else 1.0
        scale = min(scale_width, scale_height, 1.0)  # Don't enlarge images
        
        new_width = max(1, int(img_width * scale))
        new_height = max(1, int(img_height * scale))
        
        try:
            if scale < 1.0:
                resized_img = self.displayed_image.resize((new_width, new_height), Image.LANCZOS)
            else:
                resized_img = self.displayed_image
            
            # Create Tkinter compatible image
            self.tk_image = ImageTk.PhotoImage(resized_img)
            
            # Display the image centered on the canvas
            x = max(0, (canvas_width - new_width) // 2)
            y = max(0, (canvas_height - new_height) // 2)
            
            self.canvas_image = self.canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image)
            
            # Update canvas scrollregion
            self.canvas.config(scrollregion=(0, 0, max(canvas_width, new_width), max(canvas_height, new_height)))
        except Exception as e:
            print(f"Error displaying image: {e}")
            messagebox.showerror("Error", f"Error displaying image: {str(e)}")
            self.regain_focus()
    
    def previous_image(self):
        """Navigate to the previous image"""
        if self.current_image_index > 0:
            self.load_image(self.current_image_index - 1)
    
    def next_image(self):
        """Navigate to the next image"""
        if self.current_image_index < len(self.image_files) - 1:
            self.load_image(self.current_image_index + 1)
    
    def toggle_selection(self):
        """Toggle the selection tool on/off"""
        self.is_selecting = not self.is_selecting
        if self.is_selecting:
            self.selection_button.config(text="Selection Tool (On)")
            self.canvas.config(cursor="crosshair")
            self.status_var.set("Selection tool active: Click and drag to select an area for mosaic effect")
        else:
            self.selection_button.config(text="Selection Tool")
            self.canvas.config(cursor="")
            self.status_var.set("Selection tool disabled")
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        if not self.is_selecting or self.original_image is None:
            return
        
        # Get canvas-relative coordinates
        self.selection_start = (event.x, event.y)
        
        # Create a new selection rectangle
        if hasattr(self, 'selection_rectangle') and self.selection_rectangle:
            self.canvas.delete(self.selection_rectangle)
        
        self.selection_rectangle = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y, 
            outline="blue", width=2, dash=(5, 5)
        )
    
    def on_mouse_drag(self, event):
        """Handle mouse drag"""
        if not self.is_selecting or not self.selection_start or not hasattr(self, 'selection_rectangle') or not self.selection_rectangle:
            return
        
        # Update the selection rectangle
        x1, y1 = self.selection_start
        x2, y2 = event.x, event.y
        
        self.canvas.coords(self.selection_rectangle, x1, y1, x2, y2)
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if not self.is_selecting or not self.selection_start or not hasattr(self, 'selection_rectangle') or not self.selection_rectangle:
            return
        
        # Get the final selection coordinates
        x1, y1 = self.selection_start
        x2, y2 = event.x, event.y
        
        # Ensure minimum size
        if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
            self.canvas.delete(self.selection_rectangle)
            self.selection_rectangle = None
            self.selection_start = None
            return
        
        # Convert canvas coordinates to image coordinates
        # This is a simplified version - in a real app you'd need to account for scaling and scrolling
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = self.original_image.size
        
        # Calculate the scaling factor used in display_image
        scale_width = canvas_width / img_width
        scale_height = canvas_height / img_height
        scale = min(scale_width, scale_height, 1.0)
        
        # Calculate the offset for centering
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        x_offset = max(0, (canvas_width - new_width) // 2)
        y_offset = max(0, (canvas_height - new_height) // 2)
        
        # Adjust coordinates
        x1 = max(0, min(img_width, int((x1 - x_offset) / scale)))
        y1 = max(0, min(img_height, int((y1 - y_offset) / scale)))
        x2 = max(0, min(img_width, int((x2 - x_offset) / scale)))
        y2 = max(0, min(img_height, int((y2 - y_offset) / scale)))
        
        # Add the region to the list
        self.mosaic_regions.append(MosaicRegion(x1, y1, x2, y2))
        
        # Update the display
        self.display_image()
        self.modified = True
        
        # Reset selection
        self.selection_rectangle = None
        self.selection_start = None
    
    def clear_mosaic_regions(self):
        """Clear all mosaic regions"""
        if self.mosaic_regions:
            self.mosaic_regions = []
            self.display_image()
            self.modified = True
            self.status_var.set("Cleared all mosaic regions")
    
    def save_image(self):
        """Save the image with applied effects"""
        if not self.current_image_path or not self.displayed_image:
            return
        
        if not self.modified:
            self.status_var.set("No changes to save")
            return
        
        try:
            # Get file extension
            _, ext = os.path.splitext(self.current_image_path)
            
            # Set up file types based on the platform
            filetypes = []
            if ext.lower() in ('.jpg', '.jpeg'):
                filetypes.append(("JPEG files", "*.jpg"))
            elif ext.lower() == '.png':
                filetypes.append(("PNG files", "*.png"))
            else:
                filetypes.append(("Image files", f"*{ext}"))
            
            # Add a generic option at the end
            filetypes.append(("All files", "*.*"))
            
            # Ask for save location - using a simpler approach that's more compatible
            initialdir = os.path.dirname(self.current_image_path)
            initialfile = os.path.basename(self.current_image_path)
            
            # Store current focus to restore it after dialog
            save_path = filedialog.asksaveasfilename(
                initialdir=initialdir,
                initialfile=initialfile,
                filetypes=filetypes
            )
            
            # Restore focus to main window
            self.regain_focus()
            
            if not save_path:
                return
                
            # Ensure the extension is present
            if not os.path.splitext(save_path)[1]:
                save_path = save_path + ext
            
            # Create a clean copy of the display image without the border lines
            save_image = self.original_image.copy()
            
            # Apply mosaic effect to regions without drawing borders
            if self.mosaic_regions:
                try:
                    # Calculate base mosaic pixel size based on overall image dimensions
                    img_width, img_height = self.original_image.size
                    base_pixel_size = max(10, min(img_width, img_height) // 50)
                    
                    for region in self.mosaic_regions:
                        # Extract the region - ensure coordinates are within bounds
                        x1 = max(0, min(region.x1, self.original_image.width - 1))
                        y1 = max(0, min(region.y1, self.original_image.height - 1))
                        x2 = max(0, min(region.x2, self.original_image.width))
                        y2 = max(0, min(region.y2, self.original_image.height))
                        
                        # Skip invalid regions
                        if x2 <= x1 or y2 <= y1:
                            continue
                        
                        # Extract the region
                        region_img = self.original_image.crop((x1, y1, x2, y2))
                        
                        # Apply mosaic effect with adaptive pixel size
                        region_width = x2 - x1
                        region_height = y2 - y1
                        
                        # For small regions, use smaller pixel size
                        if region_width < img_width * 0.1 or region_height < img_height * 0.1:
                            pixel_size = max(5, min(region_width, region_height) // 5)
                        else:
                            # For larger regions, use base pixel size
                            pixel_size = base_pixel_size
                            
                        pixel_size = max(1, pixel_size)  # Ensure it's at least 1
                        
                        # Ensure region is large enough to resize
                        if region_img.width > 0 and region_img.height > 0:
                            small_width = max(1, region_img.width // pixel_size)
                            small_height = max(1, region_img.height // pixel_size)
                            
                            small_img = region_img.resize(
                                (small_width, small_height),
                                resample=Image.NEAREST
                            )
                            result = small_img.resize(region_img.size, Image.NEAREST)
                            
                            # Paste back
                            save_image.paste(result, (x1, y1))
                except Exception as e:
                    print(f"Error processing region: {e}")
            
            # Save the image
            try:
                save_image.save(save_path)
                self.modified = False
                self.status_var.set(f"Image saved to {os.path.basename(save_path)}")
            except Exception as e:
                print(f"Error saving to {save_path}: {e}")
                # Try with a simple name in the current directory as fallback
                fallback_path = f"./saved_image{ext}"
                save_image.save(fallback_path)
                self.status_var.set(f"Image saved to {fallback_path}")
                self.modified = False
                messagebox.showinfo("Save Info", f"Saved to fallback location: {fallback_path}")
                self.regain_focus()
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(f"Error details: {traceback_str}")
            self.status_var.set(f"Error saving image: {str(e)}")
            messagebox.showerror("Error", f"Could not save image: {str(e)}")
            self.regain_focus()
    
    def delete_image(self):
        """Delete the current image"""
        if not self.current_image_path:
            return
        
        if messagebox.askyesno("Confirm Delete", 
                             f"Are you sure you want to delete {os.path.basename(self.current_image_path)}?"):
            self.regain_focus()
            try:
                # Delete the file
                os.remove(self.current_image_path)
                
                # Update the list
                del_index = self.current_image_index
                self.file_listbox.delete(del_index)
                self.image_files.pop(del_index)
                
                # Update status
                self.status_var.set(f"Deleted {os.path.basename(self.current_image_path)}")
                
                # Load next image if available
                if self.image_files:
                    new_index = min(del_index, len(self.image_files) - 1)
                    self.load_image(new_index)
                else:
                    # No more images
                    self.current_image_index = -1
                    self.current_image_path = None
                    self.original_image = None
                    self.displayed_image = None
                    self.canvas.delete("all")
                    self.status_var.set("No images to display")
            except Exception as e:
                self.status_var.set(f"Error deleting image: {str(e)}")
                messagebox.showerror("Error", f"Could not delete image: {str(e)}")
                self.regain_focus()
        else:
            self.regain_focus()
    
    def move_image(self):
        """Move the current image to another folder"""
        if not self.current_image_path:
            return
        
        # Ask for destination folder
        dest_folder = filedialog.askdirectory(title="Select Destination Folder")
        self.regain_focus()
        
        if not dest_folder:
            return
        
        try:
            # Generate destination path
            filename = os.path.basename(self.current_image_path)
            dest_path = os.path.join(dest_folder, filename)
            
            # Check if file already exists
            if os.path.exists(dest_path):
                if not messagebox.askyesno("File Exists", 
                                        f"{filename} already exists in the destination folder. Overwrite?"):
                    self.regain_focus()
                    return
                self.regain_focus()
            
            # Move the file
            shutil.move(self.current_image_path, dest_path)
            
            # Update the list
            del_index = self.current_image_index
            self.file_listbox.delete(del_index)
            self.image_files.pop(del_index)
            
            # Update status
            self.status_var.set(f"Moved {filename} to {os.path.basename(dest_folder)}")
            
            # Load next image if available
            if self.image_files:
                new_index = min(del_index, len(self.image_files) - 1)
                self.load_image(new_index)
            else:
                # No more images
                self.current_image_index = -1
                self.current_image_path = None
                self.original_image = None
                self.displayed_image = None
                self.canvas.delete("all")
                self.status_var.set("No images to display")
        except Exception as e:
            self.status_var.set(f"Error moving image: {str(e)}")
            messagebox.showerror("Error", f"Could not move image: {str(e)}")
            self.regain_focus()
    
    def move_to_subfolder(self, folder_name):
        """Move the current image to a subfolder with the given name"""
        if not self.current_image_path:
            return
            
        # Check for unsaved changes
        if self.modified:
            if messagebox.askyesno("Unsaved Changes", 
                                "You have unsaved changes. Save before moving?"):
                self.regain_focus()
                self.save_image()
            else:
                self.regain_focus()
        
        try:
            # Create the subfolder if it doesn't exist
            parent_dir = os.path.dirname(self.current_image_path)
            subfolder_path = os.path.join(parent_dir, folder_name)
            
            if not os.path.exists(subfolder_path):
                os.makedirs(subfolder_path)
                self.status_var.set(f"Created subfolder: {folder_name}")
            
            # Generate destination path
            filename = os.path.basename(self.current_image_path)
            dest_path = os.path.join(subfolder_path, filename)
            
            # Check if file already exists
            if os.path.exists(dest_path):
                if not messagebox.askyesno("File Exists", 
                                        f"{filename} already exists in {folder_name} folder. Overwrite?"):
                    self.regain_focus()
                    return
                self.regain_focus()
            
            # Move the file
            shutil.move(self.current_image_path, dest_path)
            
            # Update the list
            del_index = self.current_image_index
            self.file_listbox.delete(del_index)
            self.image_files.pop(del_index)
            
            # Update status
            self.status_var.set(f"Moved {filename} to {folder_name}/ folder")
            
            # Load next image if available
            if self.image_files:
                new_index = min(del_index, len(self.image_files) - 1)
                self.load_image(new_index)
            else:
                # No more images
                self.current_image_index = -1
                self.current_image_path = None
                self.original_image = None
                self.displayed_image = None
                self.canvas.delete("all")
                self.status_var.set("No images to display")
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(f"Error moving to subfolder: {traceback_str}")
            self.status_var.set(f"Error moving image: {str(e)}")
            messagebox.showerror("Error", f"Could not move image: {str(e)}")
            self.regain_focus()
    
    def show_shortcuts(self):
        """Show keyboard shortcuts help dialog"""
        messagebox.showinfo(
            "Keyboard Shortcuts",
            "Keyboard Shortcuts:\n\n"
            "Navigation:\n"
            "- Page Up: Previous image\n"
            "- Page Down: Next image\n"
            "- Up/Down Arrows: Navigate file list\n\n"
            "File Operations:\n"
            "- Ctrl+S or Command+S: Save image\n"
            "- Delete: Delete current image\n"
            "- 'a': Move to 'a' subfolder\n"
            "- 'f': Move to 'f' subfolder\n\n"
            "Selection:\n"
            "- Click and drag: Create selection for mosaic"
        )
        self.regain_focus()
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Image Viewer",
            "Image Viewer 1.0\n\n"
            "A simple image viewer with mosaic functionality.\n\n"
            "Features:\n"
            "- Browse image folders\n"
            "- Navigate with keyboard shortcuts (Page Up/Down)\n"
            "- Apply mosaic effect to selected regions\n"
            "- Save, move, and delete images\n"
            "- Quick folder organization with 'a' and 'f' keys\n\n"
            "Save shortcut: Ctrl+S (Windows/Linux) or Command+S (macOS)"
        )
        self.regain_focus()


if __name__ == "__main__":
    app = ImageViewer()
    app.mainloop()