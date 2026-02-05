import ctypes
import ctypes.util

try:
    carbon_path = ctypes.util.find_library('Carbon')
    print(f"Carbon Path: {carbon_path}")
    
    if not carbon_path:
        # Fallback to absolute path
        carbon_path = '/System/Library/Frameworks/Carbon.framework/Versions/Current/Carbon'
        
    carbon = ctypes.cdll.LoadLibrary(carbon_path)
    print("Carbon Framework Loaded Successfully")
    
    # Check if RegisterEventHotKey exists
    if hasattr(carbon, 'RegisterEventHotKey'):
        print("RegisterEventHotKey found")
    else:
        print("RegisterEventHotKey NOT found")

except OSError as e:
    print(f"OS Error loading Carbon: {e}")
except Exception as e:
    print(f"Error: {e}")
