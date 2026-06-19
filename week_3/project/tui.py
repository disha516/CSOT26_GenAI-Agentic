"""
TUIAgent — full-screen Textual UI inheriting from Agent.

Usage:
  python agent.py --tui

Tasks:
  1. class TUIAgent(Agent) — override _emit() for tool log panel
  2. class ResearchDeskApp(App) — layout, input, key bindings
  3. on_input_submitted -> worker -> self.chat() (inherited from Agent)
  4. Ctrl+L / Ctrl+K / Ctrl+Q from Week 2
"""
import sys
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input, RichLog
from agent import Agent
from textual import work
import threading


class TUIAgent(Agent):
    """TUIAgent inherits from Agent but overrides _emit to write to the Textual log."""
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            self.log_widget.write(f"[bold yellow]  🔧 Tool Running: {data.get('name')}[/bold yellow]")

class TUIAgentApp(App):
    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear Display"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(id="log", highlight=True, wrap=True)
        yield Input(placeholder="Ask Research Desk...")
        yield Footer()

    def on_mount(self):
        log = self.query_one("#log", RichLog)
        self.agent = TUIAgent(log_widget=log)
        log.write(f"[bold green]Research Desk Started! (Session: {self.agent.session_id})[/bold green]\nType '/quit' or press Ctrl+Q to exit.")

    def on_input_submitted(self, event):
        user_text = event.value
        self.query_one("Input").value = ""
        log = self.query_one("#log", RichLog)
        log.write(f"\n[bold cyan][You][/bold cyan] {user_text}")

        threading.Thread(target=self.process_chat, args=(user_text,)).start()

    def process_chat(self, text):
        reply = self.agent.chat(text)
        self.call_from_thread(self.query_one("#log", RichLog).write, f"\n[bold magenta][Agent][/bold magenta] {reply}")

    def action_clear_display(self):
        self.query_one("#log", RichLog).clear()

if __name__ == "__main__":
    TUIAgentApp().run()