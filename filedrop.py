# FileDrop - single-file Android app
# Kivy version — modern UI matching the FileDrop logo
#
# Features:
#   - Send files over local Wi-Fi / hotspot
#   - Receive files from another FileDrop device
#   - Progress bar
#   - No account / database / cloud required

import os
import socket
import threading
import urllib.request
import urllib.parse

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.core.clipboard import Clipboard
from kivy.properties import NumericProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView


PORT = 8080
BUFFER_SIZE = 64 * 1024

# Brand palette, sampled directly from the FileDrop logo.
ORANGE = (1.0, 0.4588, 0.1216, 1)        # #FF751F
ORANGE_DARK = (0.851, 0.361, 0.078, 1)   # pressed state
CHARCOAL = (0.2, 0.2, 0.2, 1)            # #333333
CREAM = (0.988, 0.973, 0.953, 1)         # app background
GREY_TEXT = (0.45, 0.45, 0.45, 1)

STATUS_COLORS = {
    "ready": (0.20, 0.72, 0.38, 1),   # green
    "busy": ORANGE,
    "error": (0.86, 0.27, 0.27, 1),   # red
}


def get_local_ip():
    """Try to find the device's local Wi-Fi IP."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)

        if not ip.startswith("127."):
            return ip
    except Exception:
        pass

    return "127.0.0.1"


# ---------------------------------------------------------
# CUSTOM WIDGETS (styled to match the logo)
# ---------------------------------------------------------

class StatusDot(Widget):
    color_rgba = ListProperty(STATUS_COLORS["ready"])


class ModernProgress(Widget):
    value = NumericProperty(0)


class RoundedButton(Button):
    """Solid orange, filled, rounded-corner button."""
    bg_color = ListProperty(ORANGE)
    bg_color_down = ListProperty(ORANGE_DARK)


class OutlineButton(Button):
    """Outlined button using the orange brand color."""
    line_color = ListProperty(ORANGE)


class Card(BoxLayout):
    """White rounded card used to group content on the cream background."""
    pass


class RootWidget(BoxLayout):
    pass


KV = """
<StatusDot>:
    size_hint: None, None
    size: dp(10), dp(10)
    canvas:
        Color:
            rgba: self.color_rgba
        Ellipse:
            pos: self.pos
            size: self.size

<ModernProgress>:
    size_hint_y: None
    height: dp(10)
    canvas:
        Color:
            rgba: 0.93, 0.89, 0.85, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(5)]
        Color:
            rgba: 1, 0.4588, 0.1216, 1
        RoundedRectangle:
            pos: self.pos
            size: (self.width * (min(max(self.value, 0), 100) / 100.0), self.height)
            radius: [dp(5)]

<RoundedButton>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 1, 1, 1
    bold: True
    font_size: '16sp'
    canvas.before:
        Color:
            rgba: self.bg_color_down if self.state == 'down' else self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]

<OutlineButton>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    background_down: ''
    color: 1, 0.4588, 0.1216, 1
    bold: True
    font_size: '16sp'
    canvas.before:
        Color:
            rgba: (1, 0.4588, 0.1216, 0.12) if self.state == 'down' else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: self.line_color
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(14))
            width: dp(1.6)

<Card>:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(4)
    size_hint_y: None
    height: self.minimum_height
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]

<RootWidget>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 0.988, 0.973, 0.953, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(112)
        padding: dp(20), dp(16)
        spacing: dp(14)
        canvas.before:
            Color:
                rgba: 1, 0.4588, 0.1216, 1
            Rectangle:
                pos: self.pos
                size: self.size

        Image:
            source: 'icon.png'
            size_hint: None, None
            size: dp(52), dp(52)

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(2)

            Label:
                text: 'FileDrop'
                font_size: '26sp'
                bold: True
                color: 1, 1, 1, 1
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                size_hint_y: None
                height: dp(32)

            Label:
                text: 'Share files instantly over Wi-Fi'
                font_size: '13sp'
                color: 1, 0.93, 0.87, 1
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                size_hint_y: None
                height: dp(20)

    ScrollView:
        BoxLayout:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(16)
            size_hint_y: None
            height: self.minimum_height

            Card:
                BoxLayout:
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(24)

                    StatusDot:
                        id: status_dot

                    Label:
                        id: status_label
                        text: 'Starting...'
                        color: 0.2, 0.2, 0.2, 1
                        font_size: '15sp'
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size

            Card:
                spacing: dp(6)

                Label:
                    text: 'YOUR ADDRESS'
                    font_size: '11sp'
                    bold: True
                    color: 0.6, 0.6, 0.6, 1
                    size_hint_y: None
                    height: dp(16)
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size

                BoxLayout:
                    spacing: dp(10)
                    size_hint_y: None
                    height: dp(32)

                    Label:
                        id: address_value
                        text: 'Resolving...'
                        font_size: '15sp'
                        bold: True
                        color: 0.15, 0.15, 0.15, 1
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                        shorten: True

                    OutlineButton:
                        text: 'COPY'
                        size_hint: None, None
                        size: dp(72), dp(32)
                        font_size: '12sp'
                        on_press: root.copy_address()

            BoxLayout:
                spacing: dp(12)
                size_hint_y: None
                height: dp(54)

                RoundedButton:
                    text: 'SEND FILE'
                    on_press: root.choose_file()

                OutlineButton:
                    text: 'RECEIVE FILE'
                    on_press: root.receive_dialog()

            ModernProgress:
                id: progress

            Card:
                Label:
                    id: file_label
                    text: 'No file selected'
                    font_size: '13sp'
                    color: 0.4, 0.4, 0.4, 1
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                    size_hint_y: None
                    height: self.texture_size[1] + dp(4)
"""

Builder.load_string(KV)


class FileDropApp(App):

    def build(self):
        self.title = "FileDrop"
        self.icon = "icon.png"
        return FileDropRoot()

    def on_stop(self):
        if self.root:
            self.root.cleanup()


class FileDropRoot(RootWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.server_socket = None
        self.server_thread = None
        self.selected_file = None

        ip = get_local_ip()
        self.full_address = f"http://{ip}:{PORT}/"
        self.ids.address_value.text = self.full_address

        self.start_server()

    # ---------------------------------------------------------
    # STATUS HELPERS
    # ---------------------------------------------------------

    def set_status(self, text, state="ready"):
        self.ids.status_label.text = text
        self.ids.status_dot.color_rgba = STATUS_COLORS.get(
            state, STATUS_COLORS["ready"]
        )

    def update_progress(self, value):
        self.ids.progress.value = value

    def copy_address(self, *args):
        try:
            Clipboard.copy(self.full_address)
        except Exception:
            pass

        self.set_status("Address copied to clipboard", "ready")
        Clock.schedule_once(
            lambda dt: self.set_status(f"Ready • Port {PORT}", "ready"),
            1.5
        )

    # ---------------------------------------------------------
    # FILE PICKER
    # ---------------------------------------------------------

    def choose_file(self, *args):
        chooser = FileChooserListView(
            path="/storage/emulated/0",
            filters=["*.*"]
        )

        select_button = RoundedButton(
            text="SELECT",
            size_hint_y=None,
            height=dp(50)
        )

        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        layout.add_widget(chooser)
        layout.add_widget(select_button)

        popup = Popup(
            title="Choose a file",
            title_color=CHARCOAL,
            separator_color=ORANGE,
            content=layout,
            size_hint=(0.95, 0.9)
        )

        def select_file(_):
            if chooser.selection:
                self.selected_file = chooser.selection[0]
                popup.dismiss()

                name = os.path.basename(self.selected_file)

                self.ids.file_label.text = f"Selected: {name}"
                self.set_status("File selected. Waiting for receiver...", "busy")

                self.start_server()

        select_button.bind(on_press=select_file)

        popup.open()

    # ---------------------------------------------------------
    # SERVER
    # ---------------------------------------------------------

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            return

        self.server_thread = threading.Thread(
            target=self.run_server,
            daemon=True
        )
        self.server_thread.start()

    def run_server(self):
        try:
            self.server_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.server_socket.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            self.server_socket.bind(("0.0.0.0", PORT))
            self.server_socket.listen(1)

            Clock.schedule_once(
                lambda dt: self.set_status(f"Ready • Port {PORT}", "ready")
            )

            while True:

                client, address = self.server_socket.accept()

                threading.Thread(
                    target=self.handle_client,
                    args=(client, address),
                    daemon=True
                ).start()

        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.set_status(f"Server error: {e}", "error")
            )

    def handle_client(self, client, address):

        try:

            if not self.selected_file:
                self.send_http_error(client, 404, "No file selected")
                client.close()
                return

            file_path = self.selected_file

            if not os.path.isfile(file_path):
                self.send_http_error(client, 404, "File not found")
                client.close()
                return

            Clock.schedule_once(
                lambda dt: self.set_status(f"Sending to {address[0]}...", "busy")
            )

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            safe_name = urllib.parse.quote(file_name)

            headers = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/octet-stream\r\n"
                f"Content-Length: {file_size}\r\n"
                f"Content-Disposition: attachment; "
                f"filename*=UTF-8''{safe_name}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )

            client.sendall(headers.encode("utf-8"))

            sent = 0

            with open(file_path, "rb") as f:

                while True:

                    data = f.read(BUFFER_SIZE)

                    if not data:
                        break

                    client.sendall(data)

                    sent += len(data)

                    percent = (
                        sent / file_size * 100
                        if file_size > 0
                        else 100
                    )

                    Clock.schedule_once(
                        lambda dt, p=percent: self.update_progress(p)
                    )

            Clock.schedule_once(
                lambda dt: self.set_status("File sent successfully!", "ready")
            )

        except Exception as e:

            Clock.schedule_once(
                lambda dt, err=str(e): self.set_status(f"Send error: {err}", "error")
            )

        finally:

            try:
                client.close()
            except Exception:
                pass

            Clock.schedule_once(lambda dt: self.update_progress(0))

    def send_http_error(self, client, code, message):

        body = message.encode("utf-8")

        response = (
            f"HTTP/1.1 {code} Error\r\n"
            "Content-Type: text/plain\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("utf-8")

        client.sendall(response + body)

    # ---------------------------------------------------------
    # RECEIVE
    # ---------------------------------------------------------

    def receive_dialog(self, *args):

        layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        address_input = TextInput(
            hint_text="http://192.168.1.5:8080/",
            multiline=False,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(46),
            background_color=(0.96, 0.95, 0.93, 1),
            foreground_color=(0.15, 0.15, 0.15, 1),
            cursor_color=ORANGE,
            padding=[dp(12), dp(12), dp(12), dp(12)],
        )

        download_button = RoundedButton(
            text="DOWNLOAD",
            size_hint_y=None,
            height=dp(50)
        )

        layout.add_widget(
            Label(
                text="Enter the sender's address:",
                color=(0.3, 0.3, 0.3, 1),
                size_hint_y=None,
                height=dp(24)
            )
        )

        layout.add_widget(address_input)
        layout.add_widget(download_button)

        popup = Popup(
            title="Receive File",
            title_color=CHARCOAL,
            separator_color=ORANGE,
            content=layout,
            size_hint=(0.9, 0.42)
        )

        def start_download(_):

            url = address_input.text.strip()

            if not url:
                return

            popup.dismiss()

            threading.Thread(
                target=self.download_file,
                args=(url,),
                daemon=True
            ).start()

        download_button.bind(on_press=start_download)

        popup.open()

    def download_file(self, url):

        try:

            Clock.schedule_once(
                lambda dt: self.set_status("Connecting...", "busy")
            )

            request = urllib.request.Request(
                url,
                headers={"User-Agent": "FileDrop/1.0"}
            )

            response = urllib.request.urlopen(request, timeout=15)

            total = response.headers.get("Content-Length")
            total = int(total) if total else 0

            disposition = response.headers.get("Content-Disposition", "")

            file_name = self.get_filename(disposition)

            if not file_name:
                file_name = "received_file"

            save_dir = self.get_download_folder()

            os.makedirs(save_dir, exist_ok=True)

            output_path = os.path.join(save_dir, file_name)

            # Avoid overwriting existing files.
            output_path = self.unique_filename(output_path)

            received = 0

            with open(output_path, "wb") as f:

                while True:

                    data = response.read(BUFFER_SIZE)

                    if not data:
                        break

                    f.write(data)

                    received += len(data)

                    if total:

                        percent = received / total * 100

                        Clock.schedule_once(
                            lambda dt, p=percent: self.update_progress(p)
                        )

            Clock.schedule_once(
                lambda dt, path=output_path: self.receive_complete(path)
            )

        except Exception as e:

            Clock.schedule_once(
                lambda dt, err=str(e): self.set_status(f"Receive error: {err}", "error")
            )

        finally:

            Clock.schedule_once(lambda dt: self.update_progress(0))

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------

    def get_filename(self, disposition):

        if "filename*=" in disposition:

            try:
                value = disposition.split("filename*=", 1)[1]
                value = value.split(";", 1)[0].strip()

                if "''" in value:
                    value = value.split("''", 1)[1]

                return urllib.parse.unquote(value)

            except Exception:
                pass

        if "filename=" in disposition:

            try:
                value = disposition.split("filename=", 1)[1]
                value = value.split(";", 1)[0].strip()

                return value.strip('"')

            except Exception:
                pass

        return None

    def get_download_folder(self):

        # Android app-specific Downloads folder.
        try:

            from android.storage import app_storage_path

            base = app_storage_path()

            return os.path.join(base, "Downloads")

        except Exception:

            return os.path.join(os.path.expanduser("~"), "Downloads")

    def unique_filename(self, path):

        if not os.path.exists(path):
            return path

        folder = os.path.dirname(path)
        name = os.path.basename(path)

        base, ext = os.path.splitext(name)

        counter = 1

        while True:

            new_name = f"{base} ({counter}){ext}"
            new_path = os.path.join(folder, new_name)

            if not os.path.exists(new_path):
                return new_path

            counter += 1

    def receive_complete(self, path):
        self.set_status("File received successfully!", "ready")
        self.ids.file_label.text = "Saved: " + path

    def cleanup(self):
        try:
            if self.server_socket:
                self.server_socket.close()
        except Exception:
            pass


if __name__ == "__main__":
    FileDropApp().run()
