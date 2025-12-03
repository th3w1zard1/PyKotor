from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import markdown

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QTextBrowser, QVBoxLayout

from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.error_handling import universal_simplify_exception
from utility.system.os_helper import is_frozen

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


def get_wiki_path() -> Path:
    """Get the path to the wiki directory.
    
    Returns:
        Path to wiki directory, checking both frozen and development locations.
    """
    if is_frozen():
        # When frozen, wiki should be bundled in the same directory as the executable
        import sys
        exe_path = Path(sys.executable).parent
        wiki_path = exe_path / "wiki"
        if wiki_path.exists():
            return wiki_path
    
    # Development mode: check toolset/wiki first, then root wiki
    toolset_wiki = Path(__file__).parent.parent.parent.parent.parent / "wiki"
    if toolset_wiki.exists():
        return toolset_wiki
    
    root_wiki = Path(__file__).parent.parent.parent.parent.parent.parent / "wiki"
    if root_wiki.exists():
        return root_wiki
    
    # Fallback
    return Path("./wiki")


class EditorHelpDialog(QDialog):
    """Non-blocking dialog for displaying editor help documentation from wiki markdown files."""
    
    def __init__(self, parent: QWidget | None, wiki_filename: str):
        """Initialize the help dialog.
        
        Args:
            parent: Parent widget
            wiki_filename: Name of the markdown file in the wiki directory (e.g., "GFF-File-Format.md")
        """
        super().__init__(parent)
        from toolset.gui.common.localization import trf
        self.setWindowTitle(trf("Help - {filename}", filename=wiki_filename))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinMaxButtonsHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self.resize(900, 700)
        
        # Setup UI
        layout = QVBoxLayout(self)
        self.text_browser = QTextBrowser(self)
        layout.addWidget(self.text_browser)
        
        # Set search paths for relative links
        wiki_path = get_wiki_path()
        self.text_browser.setSearchPaths([str(wiki_path)])
        
        # Load and display the markdown file
        self.load_wiki_file(wiki_filename)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

    def _wrap_html_with_styles(self, html_body: str) -> str:
        """Wrap HTML body with modern CSS styling for better readability."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 24px;
            background-color: #ffffff;
        }}

        h1 {{
            font-size: 2em;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e1e4e8;
            color: #24292e;
        }}

        h2 {{
            font-size: 1.5em;
            font-weight: 600;
            margin-top: 32px;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e1e4e8;
            color: #24292e;
        }}

        h3 {{
            font-size: 1.25em;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 12px;
            color: #24292e;
        }}

        h4, h5, h6 {{
            font-size: 1.1em;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
            color: #24292e;
        }}

        p {{
            margin-top: 0;
            margin-bottom: 16px;
        }}

        ul, ol {{
            margin-top: 0;
            margin-bottom: 16px;
            padding-left: 32px;
        }}

        li {{
            margin-bottom: 8px;
        }}

        li > p {{
            margin-bottom: 8px;
        }}

        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 24px 0;
            display: block;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}

        table thead {{
            background-color: #f6f8fa;
        }}

        table th {{
            font-weight: 600;
            text-align: left;
            padding: 12px 16px;
            border: 1px solid #d1d5da;
            background-color: #f6f8fa;
            color: #24292e;
        }}

        table td {{
            padding: 12px 16px;
            border: 1px solid #d1d5da;
            vertical-align: top;
        }}

        table tbody tr:nth-child(even) {{
            background-color: #f9fafb;
        }}

        table tbody tr:hover {{
            background-color: #f1f3f5;
        }}

        code {{
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', monospace;
            font-size: 0.9em;
            padding: 2px 6px;
            background-color: #f6f8fa;
            border-radius: 3px;
            color: #e83e8c;
        }}

        pre {{
            font-family: 'SFMono-Regular', 'Consolas', 'Liberation Mono', 'Menlo', 'Courier', monospace;
            font-size: 0.9em;
            padding: 16px;
            background-color: #f6f8fa;
            border-radius: 6px;
            overflow-x: auto;
            margin: 16px 0;
            border: 1px solid #e1e4e8;
        }}

        pre code {{
            padding: 0;
            background-color: transparent;
            color: #24292e;
            border-radius: 0;
        }}

        a {{
            color: #0366d6;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        hr {{
            height: 0;
            margin: 24px 0;
            background: transparent;
            border: 0;
            border-top: 1px solid #e1e4e8;
        }}

        blockquote {{
            margin: 16px 0;
            padding: 0 16px;
            color: #6a737d;
            border-left: 4px solid #dfe2e5;
        }}

        strong {{
            font-weight: 600;
            color: #24292e;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""

    def load_wiki_file(self, wiki_filename: str) -> None:
        """Load and render a markdown file from the wiki directory.

        Args:
            wiki_filename: Name of the markdown file (e.g., "GFF-File-Format.md")
        """
        wiki_path = get_wiki_path()
        file_path = wiki_path / wiki_filename
        
        if not file_path.exists():
            from toolset.gui.common.localization import translate as tr, trf
            error_html = f"""
            <html>
            <body>
            <h1>{tr("Help File Not Found")}</h1>
            <p>{trf("Could not find help file: <code>{filename}</code>", filename=wiki_filename)}</p>
            <p>{trf("Expected location: <code>{path}</code>", path=str(file_path))}</p>
            <p>{trf("Wiki path: <code>{path}</code>", path=str(wiki_path))}</p>
            </body>
            </html>
            """
            self.text_browser.setHtml(error_html)
            return

        try:
            text: str = decode_bytes_with_fallbacks(file_path.read_bytes())
            html_body: str = markdown.markdown(
                text,
                extensions=["tables", "fenced_code", "codehilite", "toc"]
            )
            html: str = self._wrap_html_with_styles(html_body)
            self.text_browser.setHtml(html)
        except Exception as e:
            error_html = f"""
            <html>
            <body>
            <h1>Error Loading Help File</h1>
            <p>Could not load help file: <code>{wiki_filename}</code></p>
            <p>Error: {universal_simplify_exception(e)}</p>
            </body>
            </html>
            """
            self.text_browser.setHtml(error_html)

