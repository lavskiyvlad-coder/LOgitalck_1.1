from customtkinter import *
from socket import *
import threading
import base64
import io
import sys
import os  # for os.path.basename

# --- Configuration ---
SERVER_HOST = 'localhost'
SERVER_PORT = 8080
USER_NAME = 'Guest'


# =========================================================================
# 1. Chat Client Logic
# =========================================================================

class ChatClient:
    """Handles the network connection and message passing."""

    def __init__(self, app_instance):
        self.app = app_instance  # Reference to the main GUI window
        self.sock = None
        self.is_connected = False

        # Start connection attempt immediately
        self.connect_to_server()

    def add_message(self, message):
        """Displays messages in the GUI (placeholder)."""
        print(f"[{'SERVER' if self.is_connected else 'SYSTEM'}] {message}")

    def recv_message(self):
        """Continuously receives messages from the server in a separate thread."""
        while self.is_connected:
            try:
                message = self.sock.recv(1024).decode()
                if not message:
                    break
                self.app.after(0, lambda m=message: self.add_message(m))
            except ConnectionResetError:
                self.add_message('З’єднання розірвано сервером.')
                self.close_connection()
                break
            except Exception as e:
                if self.is_connected:
                    self.add_message(f'Помилка при отриманні повідомлення: {e}')
                break

    def connect_to_server(self):
        """Attempts to establish a socket connection and starts the receiver thread."""
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.sock.send(USER_NAME.encode())
            self.is_connected = True
            self.add_message(f'Підключено до сервера як {USER_NAME}')

            threading.Thread(target=self.recv_message, daemon=True).start()

        except ConnectionRefusedError:
            self.add_message('Не вдалося підключитися до сервера. Переконайтеся, що сервер запущено.')
            self.is_connected = False
        except Exception as e:
            self.add_message(f'Виникла несподівана помилка підключення: {e}')
            self.is_connected = False

    def send_message(self, message):
        """Sends a message to the server."""
        if not self.is_connected:
            self.add_message('Неможливо відправити: немає підключення до сервера.')
            return

        try:
            full_message = f"{USER_NAME}: {message}"
            self.sock.send(full_message.encode())
            self.add_message(full_message)
        except Exception as e:
            self.add_message(f'Помилка при відправці повідомлення: {e}')
            self.close_connection()

    def send_image(self, file_name):
        """Optional function to send an image as Base64."""
        if not self.is_connected:
            self.add_message("Неможливо відправити зображення: немає підключення до сервера.")
            return

        if not file_name or not os.path.exists(file_name):
            self.add_message("Невірний шлях до файлу.")
            return

        try:
            with open(file_name, "rb") as f:
                raw = f.read()
                b64_data = base64.b64encode(raw).decode()
                short_name = os.path.basename(file_name)
                data = f"IMAGE@({USER_NAME})@({short_name})@({b64_data})\n"
                self.sock.sendall(data.encode())
                self.add_message(f"Зображення '{short_name}' надіслано.")
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")

    def close_connection(self):
        """Gracefully closes the connection."""
        if self.is_connected and self.sock:
            self.is_connected = False
            try:
                self.sock.shutdown(SHUT_RDWR)
                self.sock.close()
                self.add_message('Відключено від сервера.')
            except Exception as e:
                print(f"Error during socket closing: {e}")


# =========================================================================
# 2. Main GUI Window
# =========================================================================

class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('400x300')
        self.title("Simple Chat Client")

        self.chat_client = ChatClient(self)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- GUI Setup ---
        self.frame = CTkFrame(self, width=200, fg_color='gray')
        self.frame.pack_propagate(False)
        self.frame.configure(width=0)
        self.frame.place(x=0, y=0, relheight=1.0)
        self.is_show_menu = False
        self.frame_width = 0

        self.btn = CTkButton(self, text='☰', command=self.toggle_show_menu, width=30, height=30)
        self.btn.place(x=0, y=0)
        self.menu_show_speed = 20

        self.test_send_btn = CTkButton(
            self,
            text='Send Test Message',
            command=lambda: self.chat_client.send_message("Hello from GUI!"),
            width=150
        )
        self.test_send_btn.place(x=50, y=50)

    def on_closing(self):
        """Handles closing the window and shutting down the connection."""
        self.chat_client.close_connection()
        self.destroy()

    # --- Menu Animation Logic ---

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.close_menu()
        else:
            self.is_show_menu = True
            self.show_menu()

    def show_menu(self):
        if self.frame_width < 200:
            self.frame_width += self.menu_show_speed
            if self.frame_width > 200:
                self.frame_width = 200
            self.frame.configure(width=self.frame_width)
            if self.is_show_menu:
                self.after(20, self.show_menu)

    def close_menu(self):
        if self.frame_width > 0:
            self.frame_width -= self.menu_show_speed
            if self.frame_width < 0:
                self.frame_width = 0
            self.frame.configure(width=self.frame_width)
            if not self.is_show_menu:
                self.after(20, self.close_menu)


# =========================================================================
# 3. Execution
# =========================================================================

if __name__ == '__main__':
    set_appearance_mode("System")
    set_default_color_theme("blue")

    win = MainWindow()
    win.mainloop()
