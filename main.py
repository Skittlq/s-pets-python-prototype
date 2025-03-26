import pygame
import sys
import win32api
import win32con
import win32gui
from dotenv import load_dotenv
import os
from character import Character
import json


load_dotenv()
application_name = os.getenv("APPLICATION_NAME")
icon_path = os.getenv("ICON_PATH")

# Initialize Pygame
pygame.init()

# Set up display (borderless full-screen simulation)
display_info = pygame.display.Info()
width, height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.SRCALPHA, display=0)
pygame.display.set_caption(application_name)

# Set up the clock for a decent framerate
clock = pygame.time.Clock()

# Get the window handle
hwnd = pygame.display.get_wm_info()["window"]

# Set up layered window and transparency
win32gui.SetWindowLong(
    hwnd,
    win32con.GWL_EXSTYLE,
    win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    | win32con.WS_EX_LAYERED
    | win32con.WS_EX_NOACTIVATE
)

transparent_color = (255, 0, 255)  # Magenta
win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*transparent_color), 0, win32con.LWA_COLORKEY)

# Set window to always be on top
win32gui.SetWindowPos(
    hwnd,
    win32con.HWND_TOPMOST,
    0, 0, 0, 0,
    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
)

# Modify extended style to hide from Alt-Tab and the taskbar
exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
exstyle = (exstyle | win32con.WS_EX_TOOLWINDOW) & ~win32con.WS_EX_APPWINDOW
win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exstyle)

original_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
oldWndProc = None

def wnd_proc(hwnd, msg, wparam, lparam):
    if msg == win32con.WM_COMMAND:
        cmd = win32api.LOWORD(wparam)
        if cmd == 1023:  # ID for our "Exit" menu item
            pygame.event.post(pygame.event.Event(pygame.QUIT))
        return 0
    elif msg == win32con.WM_USER + 20:  # Tray icon callback message
        if lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "Exit")
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, hwnd, None)
            win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        elif lparam == win32con.WM_LBUTTONDBLCLK:
            if win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        return 0
    return win32gui.CallWindowProc(oldWndProc, hwnd, msg, wparam, lparam)

oldWndProc = win32gui.SetWindowLong(hwnd, win32con.GWL_WNDPROC, wnd_proc)

# Load a custom icon from an .ico file and create a system tray icon using Shell_NotifyIcon.
hicon = win32gui.LoadImage(
    None, icon_path, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
)
nid = (
    hwnd, 0,
    win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
    win32con.WM_USER + 20,
    hicon,
    application_name
)
win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

boundaries = screen.get_rect()

# Variables to track whether the ball is grabbed
last_mouse_pos = pygame.math.Vector2(0, 0)

characters = {}
character_positions = {}

# Iterate through each folder in the "characters/" directory
characters_dir = "characters/"
for folder_name in os.listdir(characters_dir):
    folder_path = os.path.join(characters_dir, folder_name)
    if os.path.isdir(folder_path):
        # Check for character.json and required sprite directories
        character_json_path = os.path.join(folder_path, "character.json")
        required_dirs = ["sprites/dragged", "sprites/fall", "sprites/idle", "sprites/run", "sprites/walk"]
        if os.path.exists(character_json_path) and all(os.path.exists(os.path.join(folder_path, d)) for d in required_dirs):
            # Initialize the character
            characters[folder_name] = Character(folder_path)
            character_positions[folder_name] = pygame.Vector2(100, 100)  # Default position

running = True
# Main loop
while running:
    dt = clock.tick(60) / 1000  # Convert milliseconds to seconds
    for event in pygame.event.get():
        if event.type == pygame.WINDOWFOCUSLOST:
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, original_exstyle)
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()

    for character_name, character in characters.items():
        character.update()
        character.apply_physics(dt, screen.get_height())
        character_positions[character_name] = character.pos

    # Drawing
    screen.fill(transparent_color)
    for character_name, character in characters.items():
        position = character_positions[character_name]
        character.draw(screen, position)
    pygame.display.flip()

win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 0))
pygame.quit()
sys.exit()
