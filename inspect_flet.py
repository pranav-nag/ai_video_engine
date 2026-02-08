import flet as ft

print(f"Flet Version: {ft.version}")
print("Args for ft.Tab.__init__:")
import inspect

print(inspect.signature(ft.Tab.__init__))
