# Terminator plugin: right-click capture of full scrollback for reports.
# Places a "Capture for Report..." item in the terminal context menu.

import os
import subprocess
import tempfile
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte
import terminatorlib.plugin as plugin
from terminatorlib.translation import _

AVAILABLE = ['ReportShot']

class ReportShot(plugin.MenuItem):
    capabilities = ['terminal_menu']

    def callback(self, menuitems, menu, terminal):
        entry = Gtk.MenuItem.new_with_mnemonic(_('Capture for _Report...'))
        entry.connect("activate", self.on_capture, terminal)
        menuitems.append(entry)

    def extract_scrollback(self, terminal):
        vte = terminal.get_vte()
        col, row = vte.get_cursor_position()
        try:
            result = vte.get_text_range_format(Vte.Format.TEXT, 0, 0, row, col)
            text = result[0] if result else ""
        except Exception:
            try:
                result = vte.get_text_range(0, 0, row, col, None)
                text = result[0] if result else ""
            except Exception:
                text = ""
        return text or ""

    def on_capture(self, _widget, terminal):
        dialog = Gtk.Dialog(
            title="Capture for Report",
            transient_for=_widget.get_toplevel() if _widget else None,
            modal=True
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button("Capture", Gtk.ResponseType.OK)

        content = dialog.get_content_area()
        content.set_spacing(8)
        content.set_border_width(12)

        lbl = Gtk.Label(label="Tool / category name (used for folder organization):")
        lbl.set_halign(Gtk.Align.START)
        content.pack_start(lbl, False, False, 0)

        tool_entry = Gtk.Entry()
        tool_entry.set_placeholder_text("e.g. nmap, sqlmap, gobuster, bloodhound")
        content.pack_start(tool_entry, False, False, 0)

        title_lbl = Gtk.Label(label="Optional title shown on the image:")
        title_lbl.set_halign(Gtk.Align.START)
        content.pack_start(title_lbl, False, False, 0)

        title_entry = Gtk.Entry()
        title_entry.set_placeholder_text("Optional custom title")
        content.pack_start(title_entry, False, False, 0)

        dialog.show_all()
        response = dialog.run()

        tool = tool_entry.get_text().strip()
        title = title_entry.get_text().strip()
        dialog.destroy()

        if response != Gtk.ResponseType.OK or not tool:
            return

        text = self.extract_scrollback(terminal)
        if not text.strip():
            self.notify("No scrollback content found.", error=True)
            return

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as tmp:
            tmp.write(text)
            tmp_path = tmp.name

        candidates = [
            os.path.expanduser("~/.local/bin/termreport.py"),
            os.path.expanduser("~/termreport.py"),
            "/usr/local/bin/termreport.py",
            os.path.join(os.path.dirname(__file__), "termreport.py"),
        ]
        script = next((p for p in candidates if os.path.isfile(p)), None)

        if not script:
            self.notify(
                "termreport.py not found.\n"
                "Place it in ~/.local/bin/ or next to this plugin.",
                error=True
            )
            os.unlink(tmp_path)
            return

        cmd = ["python3", script, "-t", tool, "-f", tmp_path]
        if title:
            cmd.extend(["--title", title])

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                msg = proc.stdout.strip() or "Screenshot saved successfully."
                self.notify(msg)
            else:
                self.notify(
                    f"Renderer failed:\n{proc.stderr or proc.stdout}",
                    error=True
                )
        except Exception as exc:
            self.notify(f"Error running renderer: {exc}", error=True)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def notify(self, message, error=False):
        kind = Gtk.MessageType.ERROR if error else Gtk.MessageType.INFO
        dialog = Gtk.MessageDialog(None, 0, kind, Gtk.ButtonsType.OK, message)
        dialog.run()
        dialog.destroy()
