import flet as ft

try:
    print(f"Version: {ft.version.version}")
except:
    pass

print("\n--- Tab ---")
print(dir(ft.Tab))
import inspect

print(inspect.signature(ft.Tab.__init__))

print("\n--- Tabs ---")
print(inspect.signature(ft.Tabs.__init__))
