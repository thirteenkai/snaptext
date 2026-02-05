import Cocoa
import sys
import os

def convert_svg_to_png(svg_path, png_path, size=(32, 32)):
    try:
        # Load SVG data
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # 1. Thicken stroke
        # Lucide usually has stroke-width="2". We replace it.
        if 'stroke-width="2"' in svg_content:
            svg_content = svg_content.replace('stroke-width="2"', 'stroke-width="2.5"')
        
        data = svg_content.encode('utf-8')
        ns_data = Cocoa.NSData.dataWithBytes_length_(data, len(data))
        
        # NSImage from SVG data
        image = Cocoa.NSImage.alloc().initWithData_(ns_data)
        
        if not image:
            print(f"Failed to load SVG: {svg_path}")
            return
            
        # 2. Resize with padding (Tighter look)
        # Target size is 32x32 (16pt @2x), but we want the icon visual to be smaller (e.g. 24x24 or 22x22)
        # standard menu icon is usually around 18-20px visual weight in 32px box.
        # Let's try 22x22 visual centered in 32x32.
        
        canvas_size = Cocoa.NSSize(size[0], size[1])
        target_image = Cocoa.NSImage.alloc().initWithSize_(canvas_size)
        
        visual_size = 22.0
        padding = (32.0 - visual_size) / 2.0 # 5.0
        
        target_image.lockFocus()
        image.drawInRect_fromRect_operation_fraction_(
            Cocoa.NSMakeRect(padding, padding, visual_size, visual_size),
            Cocoa.NSZeroRect,
            Cocoa.NSCompositeSourceOver,
            1.0
        )
        target_image.unlockFocus()
        
        # 3. Save as PNG (Template format usually just needs name, but we ensure simple black)
        # AppKit rendering from black SVG should result in black PNG with alpha.
        
        tiff_data = target_image.TIFFRepresentation()
        bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(tiff_data)
        png_data = bitmap.representationUsingType_properties_(Cocoa.NSBitmapImageFileTypePNG, None)
        
        png_data.writeToFile_atomically_(png_path, True)
        print(f"Converted: {svg_path} -> {png_path}")
        
    except Exception as e:
        print(f"Error converting {svg_path}: {e}")

if __name__ == "__main__":
    icon_dir = "/Users/macbookpro/Desktop/Code File/snaptext/LocalOCR/resources/icons"
    icons = [
        "scan-text.svg",
        "settings.svg",
        "rotate-cw.svg",
        "info.svg",
        "log-out.svg"
    ]
    
    for icon in icons:
        svg = os.path.join(icon_dir, icon)
        # Output as Template.png
        png = os.path.join(icon_dir, icon.replace(".svg", "Template.png"))
        if os.path.exists(svg):
            convert_svg_to_png(svg, png, size=(32, 32))
