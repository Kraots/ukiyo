from disnake.ui import View, Button

__all__ = ('UrlButton',)


class UrlButton(View):
    def __init__(self, label: str, url: str):
        super().__init__()
        self.add_item(Button(label=label, url=url))