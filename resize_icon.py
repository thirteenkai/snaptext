import Cocoa
import sys
import os

def add_padding_to_png(input_path, output_path, padding_percent=0.1):
    """
    Reads a PNG, adds padding around it (transparent), and saves it.
    This creates an icon that doesn't touch the edges of the squircle, typical for macOS apps.
    """
    try:
        if not os.path.exists(input_path):
            print(f"Error: {input_path} does not exist.")
            return

        # Load image
        image = Cocoa.NSImage.alloc().initWithContentsOfFile_(input_path)
        if not image:
            print("Failed to load image.")
            return

        w = image.size().width
        h = image.size().height
        
        # New size is same as old, but we draw smaller inside
        new_size = Cocoa.NSSize(w, h)
        target_image = Cocoa.NSImage.alloc().initWithSize_(new_size)
        
        # Calculate rect
        # e.g., for 10% padding on each side, the content is 80% of dimension
        scale_factor = 1.0 - (padding_percent * 2)
        new_w = w * scale_factor
        new_h = h * scale_factor
        x = (w - new_w) / 2.0
        y = (h - new_h) / 2.0
        
        target_image.lockFocus()
        image.drawInRect_fromRect_operation_fraction_(
            Cocoa.NSMakeRect(x, y, new_w, new_h),
            Cocoa.NSZeroRect,
            Cocoa.NSCompositeSourceOver,
            1.0
        )
        target_image.unlockFocus()
        
        # Save
        tiff_data = target_image.TIFFRepresentation()
        bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(tiff_data)
        png_data = bitmap.representationUsingType_properties_(Cocoa.NSBitmapImageFileTypePNG, None)
        
        png_data.writeToFile_atomically_(output_path, True)
        print(f"Padded image saved to: {output_path}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    src = "LocalOCR/resources/icon.png"
    dst = "LocalOCR/resources/icon_padded.png"
    add_padding_to_png(src, dst, padding_percent=0.1)
