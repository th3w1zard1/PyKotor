"""NSS (NWScript) Language Server.

A language server for NSS scripts that provides diagnostics, completions,
hover information, and document symbols. Designed to run in a subprocess
to avoid blocking the UI thread and to eliminate GIL contention.

PERFORMANCE CRITICAL:
The PLY YACC parser generation takes ~900ms on first initialization.
This module caches the parser instance so this cost is paid only once
per subprocess lifetime, not on every keystroke.

Usage:
    # Start language server in subprocess
    from multiprocessing import Process, Queue
    request_queue = Queue()
    response_queue = Queue()
    server_process = Process(
        target=NSSLanguageServer.run_server,
        args=(request_queue, response_queue, is_tsl)
    )
    server_process.start()
    
    # Send requests
    request_queue.put({
        'id': 1,
        'method': 'analyze',
        'params': {'text': '...', 'filepath': '...'}
    })
    
    # Get responses
    response = response_queue.get(timeout=5.0)

References:
----------
    vendor/HoloLSP/server/src/server.ts (TypeScript NSS language server)
    vendor/HoloLSP/server/src/diagnostic-provider.ts (Diagnostic generation)
    vendor/HoloLSP/server/src/semantic-analyzer.ts (Semantic analysis)
    Language Server Protocol specification
"""
from __future__ import annotations

import re
import traceback

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ply import yacc

from pykotor.resource.formats.ncs.compiler.classes import (
    CompileError,
    FunctionDefinition,
    FunctionForwardDeclaration,
    GlobalVariableDeclaration,
    GlobalVariableInitialization,
    StructDefinition,
)
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser

if TYPE_CHECKING:
    from multiprocessing import Queue

    from pykotor.common.script import ScriptConstant, ScriptFunction
    from pykotor.resource.formats.ncs.compiler.classes import CodeRoot


class DiagnosticSeverity(IntEnum):
    """Severity levels for diagnostics (matches LSP specification)."""
    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass
class Position:
    """A position in a text document (0-indexed)."""
    line: int
    character: int


@dataclass
class Range:
    """A range in a text document."""
    start: Position
    end: Position


@dataclass
class Diagnostic:
    """A diagnostic (error, warning, etc.) in a document."""
    range: Range
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: str | None = None
    source: str = "nss"
    suggestions: list[str] = field(default_factory=list)


@dataclass
class DocumentSymbol:
    """A symbol in a document (function, struct, variable, etc.)."""
    name: str
    kind: str  # 'function', 'struct', 'variable', 'parameter'
    range: Range
    selection_range: Range
    detail: str = ""
    children: list[DocumentSymbol] = field(default_factory=list)


@dataclass
class CompletionItem:
    """An auto-completion suggestion."""
    label: str
    kind: str  # 'function', 'constant', 'keyword', 'variable'
    detail: str = ""
    documentation: str = ""
    insert_text: str = ""
    sort_text: str = ""


@dataclass
class HoverInfo:
    """Hover information for a symbol."""
    contents: str  # Markdown-formatted content
    range: Range | None = None


@dataclass
class AnalysisResult:
    """Complete analysis result for a document."""
    diagnostics: list[Diagnostic] = field(default_factory=list)
    symbols: list[DocumentSymbol] = field(default_factory=list)
    parse_successful: bool = False
    ast: CodeRoot | None = None


class NSSLanguageServer:
    """Language server for NSS scripts.
    
    Provides diagnostics, completions, hover, and document symbols.
    Designed to be instantiated once per subprocess and reused for
    multiple analysis requests.
    
    Attributes:
        functions: List of built-in script functions
        constants: List of built-in script constants
        library: Dictionary of script library contents
        is_tsl: Whether this is for TSL (True) or K1 (False)
    """
    
    # Singleton parser and lexer - created once, reused forever
    _parser: NssParser | None = None
    _lexer: NssLexer | None = None
    _initialized_for_tsl: bool | None = None
    
    def __init__(
        self,
        functions: list[ScriptFunction] | None = None,
        constants: list[ScriptConstant] | None = None,
        library: dict[str, bytes] | None = None,
        is_tsl: bool = False,
    ):
        """Initialize the language server.
        
        Args:
            functions: Built-in script functions
            constants: Built-in script constants  
            library: Script library for includes
            is_tsl: Whether this is for TSL (K2) or K1
        """
        self.functions = functions or []
        self.constants = constants or []
        self.library = library or {}
        self.is_tsl = is_tsl
        self._current_filepath: Path | None = None
        
        # Initialize parser on first use (expensive, ~900ms)
        self._ensure_parser_initialized()
    
    def _ensure_parser_initialized(self):
        """Ensure parser is initialized (only once per process)."""
        if (
            NSSLanguageServer._parser is None 
            or NSSLanguageServer._initialized_for_tsl != self.is_tsl
        ):
            # Create parser with error suppression
            NSSLanguageServer._parser = NssParser(
                functions=self.functions,
                constants=self.constants,
                library=self.library,
                library_lookup=None,
                errorlog=yacc.NullLogger(),
            )
            NSSLanguageServer._lexer = NssLexer()
            NSSLanguageServer._initialized_for_tsl = self.is_tsl
    
    def _get_parser(self) -> NssParser:
        """Get the cached parser, updating its functions/constants if needed."""
        assert NSSLanguageServer._parser is not None
        parser = NSSLanguageServer._parser
        
        # Update parser references (cheap operation, no table regeneration)
        parser.functions = self.functions
        parser.constants = self.constants
        parser.library = self.library
        if self._current_filepath is not None:
            parser.library_lookup = [self._current_filepath.parent]
        else:
            parser.library_lookup = []
        
        return parser
    
    def _create_lexer(self) -> NssLexer:
        """Create a fresh lexer for each parse (lexer state needs reset)."""
        return NssLexer()
    
    def analyze(
        self,
        text: str,
        filepath: str | Path | None = None,
    ) -> AnalysisResult:
        """Analyze NSS source code and return diagnostics and symbols.
        
        This is the main entry point for document analysis. It parses the
        source code and extracts diagnostics (errors/warnings) and document
        symbols (functions, structs, variables).
        
        Args:
            text: NSS source code to analyze
            filepath: Optional file path for include resolution
            
        Returns:
            AnalysisResult with diagnostics and symbols
        """
        self._current_filepath = Path(filepath) if filepath else None
        result = AnalysisResult()
        
        if not text.strip():
            return result
        
        # Parse the document
        try:
            parser = self._get_parser()
            lexer = self._create_lexer()
            ast = parser.parser.parse(text, lexer=lexer.lexer)
            result.parse_successful = True
            result.ast = ast
            
            # Extract symbols from AST
            result.symbols = self._extract_symbols(ast, text)
            
            # Perform semantic analysis
            semantic_diagnostics = self._semantic_analysis(ast, text)
            result.diagnostics.extend(semantic_diagnostics)
            
        except CompileError as e:
            # Extract line number from error
            diagnostic = self._compile_error_to_diagnostic(e, text)
            result.diagnostics.append(diagnostic)
            
        except Exception as e:
            # Generic parse error
            diagnostic = self._exception_to_diagnostic(e, text)
            result.diagnostics.append(diagnostic)
        
        # Add syntax-based diagnostics (fast, regex-based)
        syntax_diagnostics = self._syntax_diagnostics(text)
        result.diagnostics.extend(syntax_diagnostics)
        
        return result
    
    def _compile_error_to_diagnostic(
        self,
        error: CompileError,
        text: str,
    ) -> Diagnostic:
        """Convert a CompileError to a Diagnostic."""
        # Try to extract line number
        line = 0
        col = 0
        
        if hasattr(error, 'line_num') and error.line_num is not None:
            line = error.line_num - 1  # Convert to 0-indexed
        else:
            # Try to extract from message
            match = re.search(r'line (\d+)', str(error), re.IGNORECASE)
            if match:
                line = int(match.group(1)) - 1
        
        # Get line content for range calculation
        lines = text.split('\n')
        if 0 <= line < len(lines):
            col = 0
            end_col = len(lines[line])
        else:
            end_col = 0
        
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=col),
                end=Position(line=line, character=end_col),
            ),
            message=str(error),
            severity=DiagnosticSeverity.ERROR,
            code="compile-error",
            source="nss",
        )
    
    def _exception_to_diagnostic(
        self,
        error: Exception,
        text: str,
    ) -> Diagnostic:
        """Convert a generic exception to a Diagnostic."""
        # Try to extract line number from traceback or message
        line = 0
        
        error_str = str(error)
        match = re.search(r'line (\d+)', error_str, re.IGNORECASE)
        if match:
            line = int(match.group(1)) - 1
        
        # Also check for "position" or "lineno" in the error
        pos_match = re.search(r'position (\d+)', error_str, re.IGNORECASE)
        if pos_match and line == 0:
            # Convert character position to line number
            pos = int(pos_match.group(1))
            current_pos = 0
            for i, content in enumerate(text.split('\n')):
                if current_pos + len(content) + 1 >= pos:
                    line = i
                    break
                current_pos += len(content) + 1
        
        lines = text.split('\n')
        if 0 <= line < len(lines):
            end_col = len(lines[line])
        else:
            end_col = 0
        
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=0),
                end=Position(line=line, character=end_col),
            ),
            message=f"Parse error: {error}",
            severity=DiagnosticSeverity.ERROR,
            code="parse-error",
            source="nss",
        )
    
    def _syntax_diagnostics(self, text: str) -> list[Diagnostic]:
        """Quick syntax-based diagnostics (no parsing required)."""
        diagnostics: list[Diagnostic] = []
        lines = text.split('\n')
        
        # Track brace balance
        brace_balance = 0
        paren_balance = 0
        
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments
            if stripped.startswith('//'):
                continue
            
            # Remove string literals for analysis
            line_no_strings = re.sub(r'"[^"\\]*(\\.[^"\\]*)*"', '""', stripped)
            
            # Track balance
            brace_balance += line_no_strings.count('{') - line_no_strings.count('}')
            paren_balance += line_no_strings.count('(') - line_no_strings.count(')')
            
            # Check for double semicolons
            if ';;' in line_no_strings:
                diagnostics.append(Diagnostic(
                    range=Range(
                        start=Position(line=line_num, character=line.find(';;')),
                        end=Position(line=line_num, character=line.find(';;') + 2),
                    ),
                    message="Redundant semicolon",
                    severity=DiagnosticSeverity.WARNING,
                    code="redundant-semicolon",
                ))
            
            # Check for common typos
            if re.search(r'\bvodi\b', stripped, re.IGNORECASE):
                match = re.search(r'\bvodi\b', stripped, re.IGNORECASE)
                if match:
                    diagnostics.append(Diagnostic(
                        range=Range(
                            start=Position(line=line_num, character=match.start()),
                            end=Position(line=line_num, character=match.end()),
                        ),
                        message="Did you mean 'void'?",
                        severity=DiagnosticSeverity.ERROR,
                        code="unknown-type",
                        suggestions=["void"],
                    ))
        
        # Check for unbalanced braces
        if brace_balance > 0:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=len(lines) - 1, character=0),
                    end=Position(line=len(lines) - 1, character=0),
                ),
                message=f"Missing {brace_balance} closing brace(s) '}}'",
                severity=DiagnosticSeverity.ERROR,
                code="unbalanced-braces",
            ))
        elif brace_balance < 0:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=0),
                ),
                message=f"Extra {-brace_balance} closing brace(s) '}}'",
                severity=DiagnosticSeverity.ERROR,
                code="unbalanced-braces",
            ))
        
        return diagnostics
    
    def _semantic_analysis(
        self,
        ast: CodeRoot,
        text: str,
    ) -> list[Diagnostic]:
        """Perform semantic analysis on the AST."""
        diagnostics: list[Diagnostic] = []
        
        # Check for entry point
        has_main = False
        has_starting_conditional = False
        
        for obj in ast.objects:
            if isinstance(obj, FunctionDefinition):
                if obj.identifier.identifier == "main":
                    has_main = True
                elif obj.identifier.identifier == "StartingConditional":
                    has_starting_conditional = True
        
        # Only warn about missing entry point if there are no forward declarations
        # (which would indicate this is an include file)
        has_forward_decl = any(
            isinstance(obj, FunctionForwardDeclaration)
            for obj in ast.objects
        )
        
        if not has_main and not has_starting_conditional and not has_forward_decl:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=0),
                ),
                message="Script has no entry point (main() or StartingConditional()). "
                        "This is normal for include files.",
                severity=DiagnosticSeverity.INFORMATION,
                code="no-entry-point",
                suggestions=[
                    "Add void main() { } for executable scripts",
                    "Add int StartingConditional() { return TRUE; } for conditional scripts",
                ],
            ))
        
        return diagnostics
    
    def _extract_symbols(
        self,
        ast: CodeRoot,
        text: str,
    ) -> list[DocumentSymbol]:
        """Extract document symbols from the AST."""
        symbols: list[DocumentSymbol] = []
        lines = text.split('\n')
        
        for obj in ast.objects:
            line_num = getattr(obj, 'line_num', 1) - 1  # Convert to 0-indexed
            if line_num < 0:
                line_num = 0
            
            if isinstance(obj, FunctionDefinition):
                # Get function details
                return_type = str(getattr(obj.return_type, 'builtin', 'void')).split('.')[-1]
                params = getattr(obj, 'parameters', [])
                param_str = ', '.join(
                    f"{getattr(p.datatype, 'builtin', '?').name if hasattr(getattr(p.datatype, 'builtin', '?'), 'name') else str(getattr(p.datatype, 'builtin', '?')).split('.')[-1]} {p.identifier}"
                    for p in params
                )
                
                # Calculate range
                end_line = line_num
                # Find the closing brace
                brace_count = 0
                for i in range(line_num, len(lines)):
                    brace_count += lines[i].count('{') - lines[i].count('}')
                    if brace_count == 0 and '{' in ''.join(lines[line_num:i+1]):
                        end_line = i
                        break
                
                # Create symbol with children for parameters
                func_symbol = DocumentSymbol(
                    name=obj.identifier.identifier,
                    kind='function',
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=end_line, character=len(lines[end_line]) if end_line < len(lines) else 0),
                    ),
                    selection_range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=len(lines[line_num]) if line_num < len(lines) else 0),
                    ),
                    detail=f"{return_type} {obj.identifier.identifier}({param_str})",
                    children=[],
                )
                
                # Add parameters as children
                for param in params:
                    param_type = str(getattr(param.datatype, 'builtin', '?'))
                    if '.' in param_type:
                        param_type = param_type.split('.')[-1]
                    func_symbol.children.append(DocumentSymbol(
                        name=param.identifier.identifier,
                        kind='parameter',
                        range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=0),
                        ),
                        selection_range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=0),
                        ),
                        detail=param_type,
                    ))
                
                symbols.append(func_symbol)
            
            elif isinstance(obj, StructDefinition):
                members = getattr(obj, 'members', [])
                
                struct_symbol = DocumentSymbol(
                    name=obj.identifier.identifier,
                    kind='struct',
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=0),
                    ),
                    selection_range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=0),
                    ),
                    detail=f"struct ({len(members)} members)",
                    children=[],
                )
                
                # Add members
                for member in members:
                    member_type = str(getattr(member.datatype, 'builtin', '?'))
                    if '.' in member_type:
                        member_type = member_type.split('.')[-1]
                    struct_symbol.children.append(DocumentSymbol(
                        name=member.identifier.identifier,
                        kind='variable',
                        range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=0),
                        ),
                        selection_range=Range(
                            start=Position(line=line_num, character=0),
                            end=Position(line=line_num, character=0),
                        ),
                        detail=member_type,
                    ))
                
                symbols.append(struct_symbol)
            
            elif isinstance(obj, (GlobalVariableDeclaration, GlobalVariableInitialization)):
                var_type = str(getattr(obj.data_type, 'builtin', '?'))
                if '.' in var_type:
                    var_type = var_type.split('.')[-1]
                
                symbols.append(DocumentSymbol(
                    name=obj.identifier.identifier,
                    kind='variable',
                    range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=0),
                    ),
                    selection_range=Range(
                        start=Position(line=line_num, character=0),
                        end=Position(line=line_num, character=0),
                    ),
                    detail=var_type,
                ))
        
        return symbols
    
    def get_completions(
        self,
        text: str,
        line: int,
        character: int,
    ) -> list[CompletionItem]:
        """Get completion suggestions at a position.
        
        Args:
            text: Document text
            line: 0-indexed line number
            character: 0-indexed character position
            
        Returns:
            List of completion items
        """
        completions: list[CompletionItem] = []
        
        # Get the word being typed
        lines = text.split('\n')
        if line >= len(lines):
            return completions
        
        current_line = lines[line]
        # Find word start
        word_start = character
        while word_start > 0 and (current_line[word_start - 1].isalnum() or current_line[word_start - 1] == '_'):
            word_start -= 1
        
        prefix = current_line[word_start:character].lower() if character > word_start else ""
        
        # Add functions
        for func in self.functions:
            if not prefix or func.name.lower().startswith(prefix):
                return_type = getattr(func, 'return_type', 'void')
                params = getattr(func, 'parameters', [])
                param_str = ', '.join(
                    f"{getattr(p, 'type', '?')} {getattr(p, 'name', 'arg')}"
                    for p in params[:3]
                )
                if len(params) > 3:
                    param_str += ", ..."
                
                completions.append(CompletionItem(
                    label=func.name,
                    kind='function',
                    detail=f"{return_type} {func.name}({param_str})",
                    documentation=getattr(func, 'description', '') or "",
                    insert_text=f"{func.name}($0)",
                    sort_text=f"0_{func.name}",  # Functions first
                ))
        
        # Add constants
        for const in self.constants:
            if not prefix or const.name.lower().startswith(prefix):
                const_type = getattr(const, 'type', '')
                const_value = getattr(const, 'value', '')
                
                completions.append(CompletionItem(
                    label=const.name,
                    kind='constant',
                    detail=f"{const_type} = {const_value}" if const_value else const_type,
                    documentation=getattr(const, 'description', '') or "",
                    insert_text=const.name,
                    sort_text=f"1_{const.name}",  # Constants second
                ))
        
        # Add keywords
        keywords = [
            "void", "int", "float", "string", "object", "vector", "location",
            "effect", "event", "itemproperty", "talent", "action",
            "if", "else", "for", "while", "do", "switch", "case", "default",
            "break", "continue", "return", "struct", "const", "include",
            "TRUE", "FALSE", "OBJECT_SELF", "OBJECT_INVALID",
        ]
        for kw in keywords:
            if not prefix or kw.lower().startswith(prefix):
                completions.append(CompletionItem(
                    label=kw,
                    kind='keyword',
                    detail="keyword",
                    insert_text=kw,
                    sort_text=f"2_{kw}",  # Keywords last
                ))
        
        return completions
    
    def get_hover(
        self,
        text: str,
        line: int,
        character: int,
    ) -> HoverInfo | None:
        """Get hover information at a position.
        
        Args:
            text: Document text
            line: 0-indexed line number
            character: 0-indexed character position
            
        Returns:
            HoverInfo or None if nothing to show
        """
        lines = text.split('\n')
        if line >= len(lines):
            return None
        
        current_line = lines[line]
        
        # Find word at position
        word_start = character
        word_end = character
        
        while word_start > 0 and (current_line[word_start - 1].isalnum() or current_line[word_start - 1] == '_'):
            word_start -= 1
        while word_end < len(current_line) and (current_line[word_end].isalnum() or current_line[word_end] == '_'):
            word_end += 1
        
        word = current_line[word_start:word_end]
        if not word:
            return None
        
        word_lower = word.lower()
        
        # Search functions
        for func in self.functions:
            if func.name.lower() == word_lower:
                return_type = getattr(func, 'return_type', 'void')
                params = getattr(func, 'parameters', [])
                param_str = ', '.join(
                    f"{getattr(p, 'type', '?')} {getattr(p, 'name', 'arg')}"
                    for p in params
                )
                description = getattr(func, 'description', '') or ""
                
                content = f"```nwscript\n{return_type} {func.name}({param_str})\n```"
                if description:
                    content += f"\n\n{description}"
                
                return HoverInfo(
                    contents=content,
                    range=Range(
                        start=Position(line=line, character=word_start),
                        end=Position(line=line, character=word_end),
                    ),
                )
        
        # Search constants
        for const in self.constants:
            if const.name.lower() == word_lower:
                const_type = getattr(const, 'type', '')
                const_value = getattr(const, 'value', '')
                description = getattr(const, 'description', '') or ""
                
                if const_type and const_value:
                    content = f"```nwscript\nconst {const_type} {const.name} = {const_value}\n```"
                elif const_value:
                    content = f"```nwscript\n{const.name} = {const_value}\n```"
                else:
                    content = f"```nwscript\n{const.name}\n```"
                
                if description:
                    content += f"\n\n{description}"
                
                return HoverInfo(
                    contents=content,
                    range=Range(
                        start=Position(line=line, character=word_start),
                        end=Position(line=line, character=word_end),
                    ),
                )
        
        return None
    
    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a language server request.
        
        Request format:
        {
            'id': <unique request id>,
            'method': 'analyze' | 'completions' | 'hover' | 'shutdown',
            'params': {...}  # method-specific parameters
        }
        
        Response format:
        {
            'id': <same as request>,
            'result': {...} | None,
            'error': {'code': int, 'message': str} | None
        }
        """
        request_id = request.get('id')
        method = request.get('method', '')
        params = request.get('params', {})
        
        try:
            if method == 'analyze':
                result = self.analyze(
                    text=params.get('text', ''),
                    filepath=params.get('filepath'),
                )
                return {
                    'id': request_id,
                    'result': self._analysis_result_to_dict(result),
                    'error': None,
                }
            
            elif method == 'completions':
                completions = self.get_completions(
                    text=params.get('text', ''),
                    line=params.get('line', 0),
                    character=params.get('character', 0),
                )
                return {
                    'id': request_id,
                    'result': [self._completion_to_dict(c) for c in completions],
                    'error': None,
                }
            
            elif method == 'hover':
                hover = self.get_hover(
                    text=params.get('text', ''),
                    line=params.get('line', 0),
                    character=params.get('character', 0),
                )
                return {
                    'id': request_id,
                    'result': self._hover_to_dict(hover) if hover else None,
                    'error': None,
                }
            
            elif method == 'shutdown':
                return {
                    'id': request_id,
                    'result': {'status': 'shutdown'},
                    'error': None,
                }
            
            elif method == 'update_config':
                # Update functions/constants/library
                if 'functions' in params:
                    self.functions = params['functions']
                if 'constants' in params:
                    self.constants = params['constants']
                if 'library' in params:
                    self.library = params['library']
                if 'is_tsl' in params:
                    self.is_tsl = params['is_tsl']
                    # May need to reinitialize parser if game type changed
                    self._ensure_parser_initialized()
                
                return {
                    'id': request_id,
                    'result': {'status': 'updated'},
                    'error': None,
                }
            
            else:
                return {
                    'id': request_id,
                    'result': None,
                    'error': {'code': -32601, 'message': f'Unknown method: {method}'},
                }
        
        except Exception as e:
            return {
                'id': request_id,
                'result': None,
                'error': {'code': -32603, 'message': str(e), 'traceback': traceback.format_exc()},
            }
    
    def _analysis_result_to_dict(self, result: AnalysisResult) -> dict[str, Any]:
        """Convert AnalysisResult to dictionary for JSON serialization."""
        return {
            'diagnostics': [self._diagnostic_to_dict(d) for d in result.diagnostics],
            'symbols': [self._symbol_to_dict(s) for s in result.symbols],
            'parse_successful': result.parse_successful,
        }
    
    def _diagnostic_to_dict(self, diagnostic: Diagnostic) -> dict[str, Any]:
        """Convert Diagnostic to dictionary."""
        return {
            'range': {
                'start': {'line': diagnostic.range.start.line, 'character': diagnostic.range.start.character},
                'end': {'line': diagnostic.range.end.line, 'character': diagnostic.range.end.character},
            },
            'message': diagnostic.message,
            'severity': int(diagnostic.severity),
            'code': diagnostic.code,
            'source': diagnostic.source,
            'suggestions': diagnostic.suggestions,
        }
    
    def _symbol_to_dict(self, symbol: DocumentSymbol) -> dict[str, Any]:
        """Convert DocumentSymbol to dictionary."""
        return {
            'name': symbol.name,
            'kind': symbol.kind,
            'range': {
                'start': {'line': symbol.range.start.line, 'character': symbol.range.start.character},
                'end': {'line': symbol.range.end.line, 'character': symbol.range.end.character},
            },
            'selection_range': {
                'start': {'line': symbol.selection_range.start.line, 'character': symbol.selection_range.start.character},
                'end': {'line': symbol.selection_range.end.line, 'character': symbol.selection_range.end.character},
            },
            'detail': symbol.detail,
            'children': [self._symbol_to_dict(c) for c in symbol.children],
        }
    
    def _completion_to_dict(self, completion: CompletionItem) -> dict[str, Any]:
        """Convert CompletionItem to dictionary."""
        return {
            'label': completion.label,
            'kind': completion.kind,
            'detail': completion.detail,
            'documentation': completion.documentation,
            'insert_text': completion.insert_text,
            'sort_text': completion.sort_text,
        }
    
    def _hover_to_dict(self, hover: HoverInfo) -> dict[str, Any]:
        """Convert HoverInfo to dictionary."""
        result: dict[str, Any] = {'contents': hover.contents}
        if hover.range:
            result['range'] = {
                'start': {'line': hover.range.start.line, 'character': hover.range.start.character},
                'end': {'line': hover.range.end.line, 'character': hover.range.end.character},
            }
        return result
    
    @staticmethod
    def run_server(
        request_queue: Queue,
        response_queue: Queue,
        is_tsl: bool = False,
        functions: list[ScriptFunction] | None = None,
        constants: list[ScriptConstant] | None = None,
        library: dict[str, bytes] | None = None,
    ):
        """Run the language server in a subprocess.
        
        This is the entry point for the subprocess. It creates a language
        server instance and processes requests from the queue until shutdown.
        
        Args:
            request_queue: Queue to receive requests from
            response_queue: Queue to send responses to
            is_tsl: Whether this is for TSL (K2) or K1
            functions: Built-in script functions
            constants: Built-in script constants
            library: Script library for includes
        """
        # Load default functions/constants if not provided
        if functions is None or constants is None or library is None:
            # Import here to avoid circular imports and speed up initial import
            from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS
            from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
            
            if is_tsl:
                functions = list(TSL_FUNCTIONS) if functions is None else functions
                constants = list(TSL_CONSTANTS) if constants is None else constants
                library = dict(TSL_LIBRARY) if library is None else library
            else:
                functions = list(KOTOR_FUNCTIONS) if functions is None else functions
                constants = list(KOTOR_CONSTANTS) if constants is None else constants
                library = dict(KOTOR_LIBRARY) if library is None else library
        
        # Create server instance (this initializes the parser - ~900ms one-time cost)
        server = NSSLanguageServer(
            functions=functions,
            constants=constants,
            library=library,
            is_tsl=is_tsl,
        )
        
        # Signal that server is ready
        response_queue.put({
            'id': None,
            'result': {'status': 'ready'},
            'error': None,
        })
        
        # Process requests
        while True:
            try:
                request = request_queue.get(timeout=1.0)
            except Exception:
                # Timeout - check if parent process is still alive
                continue
            
            if request is None:
                # Shutdown signal
                break
            
            response = server.handle_request(request)
            response_queue.put(response)
            
            if request.get('method') == 'shutdown':
                break

