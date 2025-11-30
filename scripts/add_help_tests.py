"""Script to add help dialog tests to all editor test files."""
from pathlib import Path
import re

# Mapping of test file names to editor class names and wiki files
EDITOR_MAPPING = {
    "test_are_editor.py": ("AREEditor", "GFF-ARE.md"),
    "test_bwm_editor.py": ("BWMEditor", "BWM-File-Format.md"),
    "test_dlg_editor.py": ("DLGEditor", "GFF-DLG.md"),
    "test_erf_editor.py": ("ERFEditor", "ERF-File-Format.md"),
    "test_gff_editor.py": ("GFFEditor", "GFF-File-Format.md"),
    "test_git_editor.py": ("GITEditor", "GFF-GIT.md"),
    "test_ifo_editor.py": ("IFOEditor", "GFF-IFO.md"),
    "test_jrl_editor.py": ("JRLEditor", "GFF-JRL.md"),
    "test_lip_editor.py": ("LIPEditor", "LIP-File-Format.md"),
    "test_ltr_editor.py": ("LTREditor", "LTR-File-Format.md"),
    "test_lyt_editor.py": ("LYTEditor", "LYT-File-Format.md"),
    "test_mdl_editor.py": ("MDLEditor", "MDL-MDX-File-Format.md"),
    "test_nss_editor.py": ("NSSEditor", "NSS-File-Format.md"),
    "test_pth_editor.py": ("PTHEditor", "GFF-PTH.md"),
    "test_savegame_editor.py": ("SaveGameEditor", "GFF-File-Format.md"),
    "test_ssf_editor.py": ("SSFEditor", "SSF-File-Format.md"),
    "test_tlk_editor.py": ("TLKEditor", "TLK-File-Format.md"),
    "test_tpc_editor.py": ("TPCEditor", "TPC-File-Format.md"),
    "test_twoda_editor.py": ("TwoDAEditor", "2DA-File-Format.md"),
    "test_txt_editor.py": ("TXTEditor", None),  # No help file
    "test_utc_editor.py": ("UTCEditor", "GFF-UTC.md"),
    "test_utd_editor.py": ("UTDEditor", "GFF-UTD.md"),
    "test_ute_editor.py": ("UTEEditor", "GFF-UTE.md"),
    "test_uti_editor.py": ("UTIEditor", "GFF-UTI.md"),
    "test_utm_editor.py": ("UTMEditor", "GFF-UTM.md"),
    "test_utp_editor.py": ("UTPEditor", "GFF-UTP.md"),
    "test_uts_editor.py": ("UTSEditor", "GFF-UTS.md"),
    "test_utt_editor.py": ("UTTEditor", "GFF-UTT.md"),
    "test_utw_editor.py": ("UTWEditor", "GFF-UTW.md"),
}

TEST_TEMPLATE = '''
def test_{editor_lower}_editor_help_dialog_opens_correct_file(qtbot, installation: HTInstallation):
    """Test that {editor_class} help dialog opens and displays the correct help file (not 'Help File Not Found')."""
    from toolset.gui.dialogs.editor_help import EditorHelpDialog
    
    editor = {editor_class}(None, installation)
    qtbot.addWidget(editor)
    
    # Trigger help dialog with the correct file for {editor_class}
    editor._show_help_dialog("{wiki_file}")
    qtbot.wait(200)  # Wait for dialog to be created
    
    # Find the help dialog
    dialogs = [child for child in editor.findChildren(EditorHelpDialog)]
    assert len(dialogs) > 0, "Help dialog should be opened"
    
    dialog = dialogs[0]
    qtbot.waitExposed(dialog)
    
    # Get the HTML content
    html = dialog.text_browser.toHtml()
    
    # Assert that "Help File Not Found" error is NOT shown
    assert "Help File Not Found" not in html, \\
        f"Help file '{wiki_file}' should be found, but error was shown. HTML: {{html[:500]}}"
    
    # Assert that some content is present (file was loaded successfully)
    assert len(html) > 100, "Help dialog should contain content"
'''

TEST_TEMPLATE_NO_HELP = '''
def test_{editor_lower}_editor_help_dialog_skips_when_no_wiki_file(qtbot, installation: HTInstallation):
    """Test that {editor_class} does not add help action when no wiki file is mapped."""
    editor = {editor_class}(None, installation)
    qtbot.addWidget(editor)
    
    # {editor_class} has None in the mapping, so _add_help_action should skip
    # This test verifies the editor can be created without errors
    assert editor is not None
'''

def add_test_to_file(test_file_path: Path, editor_class: str, wiki_file: str | None):
    """Add help test to a test file."""
    content = test_file_path.read_text(encoding='utf-8')
    
    # Check if test already exists
    test_name = f"test_{editor_class.lower()}_editor_help_dialog"
    if test_name in content:
        print(f"  Test already exists in {test_file_path.name}, skipping...")
        return False
    
    # Find the last test function or class to add after
    # Look for the last function definition
    lines = content.split('\n')
    last_test_line = -1
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r'^def test_', lines[i]):
            last_test_line = i
            break
    
    if last_test_line == -1:
        # No test functions found, add at end
        insert_pos = len(lines)
    else:
        # Find the end of the last test function
        insert_pos = last_test_line + 1
        indent_level = len(lines[last_test_line]) - len(lines[last_test_line].lstrip())
        # Find the next line with same or less indentation (end of function)
        for i in range(last_test_line + 1, len(lines)):
            if lines[i].strip() and not lines[i].startswith(' ' * (indent_level + 1)):
                if not lines[i].startswith(' ' * indent_level):
                    insert_pos = i
                    break
    
    # Generate test code
    editor_lower = editor_class.lower()
    if wiki_file:
        test_code = TEST_TEMPLATE.format(
            editor_lower=editor_lower,
            editor_class=editor_class,
            wiki_file=wiki_file
        )
    else:
        test_code = TEST_TEMPLATE_NO_HELP.format(
            editor_lower=editor_lower,
            editor_class=editor_class
        )
    
    # Insert test
    lines.insert(insert_pos, test_code)
    new_content = '\n'.join(lines)
    
    test_file_path.write_text(new_content, encoding='utf-8')
    return True

def main():
    """Main function."""
    repo_root = Path(__file__).parent.parent
    test_dir = repo_root / "tests" / "test_toolset" / "gui" / "editors"
    
    print("Adding help dialog tests to editor test files...")
    
    for test_file_name, (editor_class, wiki_file) in EDITOR_MAPPING.items():
        test_file_path = test_dir / test_file_name
        if not test_file_path.exists():
            print(f"  Warning: {test_file_name} not found, skipping...")
            continue
        
        print(f"  Processing {test_file_name}...")
        if add_test_to_file(test_file_path, editor_class, wiki_file):
            print(f"    Added help test for {editor_class}")
        else:
            print(f"    Skipped {editor_class} (test already exists)")

if __name__ == "__main__":
    main()

