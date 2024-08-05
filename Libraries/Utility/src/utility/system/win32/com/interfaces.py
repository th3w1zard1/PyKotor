from __future__ import annotations

from ctypes import POINTER, POINTER as C_POINTER, Structure, c_char_p, c_int, c_uint, c_ulong, c_void_p, c_wchar_p, windll
from ctypes.wintypes import BOOL, DWORD, HWND, LPCWSTR, LPWSTR, ULONG
from typing import TYPE_CHECKING, Callable, ClassVar, Sequence

import comtypes  # pyright: ignore[reportMissingTypeStubs]

from comtypes import COMMETHOD  # pyright: ignore[reportMissingTypeStubs]

from utility.system.win32.com.com_types import GUID
from utility.system.win32.hresult import HRESULT, S_OK  # pyright: ignore[reportMissingTypeStubs]

if TYPE_CHECKING:
    import os

    from ctypes import Array, _CData, _FuncPointer, _Pointer

    from comtypes._memberspec import _ComMemberSpec  # pyright: ignore[reportMissingTypeStubs]
    from typing_extensions import Self

# GUID Definitions
IID_IUnknown = GUID("{00000000-0000-0000-C000-000000000046}")
IID_IDispatch = GUID("{00020400-0000-0000-C000-000000000046}")
IID_IClassFactory = GUID("{00000001-0000-0000-C000-000000000046}")
IID_IStream = GUID("{0000000c-0000-0000-C000-000000000046}")
IID_IStorage = GUID("{0000000b-0000-0000-C000-000000000046}")
IID_IBindCtx = GUID("{0000000e-0000-0000-C000-000000000046}")
IID_IEnumShellItems = GUID("{70629033-E363-4A28-A567-0DB78006E6D7}")
IID_IContextMenu = GUID("{000214e4-0000-0000-c000-000000000046}")
IID_IContextMenu2 = GUID("{000214f4-0000-0000-c000-000000000046}")
IID_IContextMenu3 = GUID("{bcfce0a0-ec17-11d0-8d10-00a0c90f2719}")
IID_IShellFolder = GUID("{000214E6-0000-0000-C000-000000000046}")
IID_IShellFolder2 = GUID("{93F2F68C-1D1B-11D3-A30E-00C04F79ABD1}")
IID_IShellItem = GUID("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
IID_IShellItem2 = GUID("{7E9FB0D3-919F-4307-AB2E-9B1860310C93}")
IID_IShellLibrary = GUID("{11A66EFA-382E-451A-9234-1E0E12EF3085}")
IID_IShellItemArray = GUID("{B63EA76D-1F85-456F-A19C-48159EFA858B}")
IID_IShellItemFilter = GUID("{2659B475-EEB8-48B7-8F07-B378810F48CF}")
IID_IShellView = GUID("{000214e3-0000-0000-c000-000000000046}")
IID_IModalWindow = GUID("{B4DB1657-70D7-485E-8E3E-6FCB5A5C1802}")
IID_IFileDialog = GUID("{42F85136-DB7E-439C-85F1-E4075D135FC8}")
IID_IFileDialog2 = GUID("{61744FC7-85B5-4791-A9B0-272276309B13}")
IID_IFileSaveDialog = GUID("{84BCCD23-5FDE-4CDB-AEA4-AF64B83D78AB}")
IID_IFileSaveDialogOld = GUID("{2804B74C-AC16-4398-9DC0-DB83F5B7ED14}")
IID_IFileSaveDialogPrivate = GUID("{6CB95A6A-88B6-4DC4-B3EA-3A776D1E8EFF}")
IID_IFileOpenDialog = GUID("{D57C7288-D4AD-4768-BE02-9D969532D960}")
IID_IFileDialogEvents = GUID("{973510DB-7D7F-452B-8975-74A85828D354}")
IID_FileDialogPermissionAttribute = GUID("{0CCCA629-440F-313E-96CD-BA1B4B4997F7}")
IID_FileDialogPermission = GUID("{A8B7138C-8932-3D78-A585-A91569C743AC}")
IID_IFileDialogPrivate = GUID("{9EA5491C-89C8-4BEF-93D3-7F665FB82A33}")
IID_IFileDialogCustomize = GUID("{E6FDD21A-163F-4975-9C8C-A69F1BA37034}")
IID_IFileDialogEventsPrivate = GUID("{050E9E69-BAEA-4C08-AD6A-61666DD32E96}")
IID_IFileDialogControlEvents = GUID("{36116642-D713-4B97-9B83-7484A9D00433}")
IID_IFileDialogControlEvents = GUID("{36116642-D713-4B97-9B83-7484A9D00433}")
IID_IFileDialogResultHandler = GUID("{42841501-194F-478F-9B4C-78985419DA53}")
IID_IShellLink = GUID("{000214f9-0000-0000-c000-000000000046}")
IID_IShellLinkDataList = GUID("{45E2B4AE-B1C3-11D0-BA91-00C04FD7A083}")
IID_IPropertyStore = GUID("{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}")
IID_IFileOperationProgressSink = GUID("{04B0F1A7-9490-44BC-96E1-4296A31252E2}")
CLSID_FileDialog = GUID("{3D9C8F03-50D4-4E40-BB11-70E74D3F10F3}")
CLSID_FileOpenDialog = GUID("{DC1C5A9C-E88A-4dde-A5A1-60F82A20AEF7}")
CLSID_FileOpenDialogLegacy = GUID("{725F645B-EAED-4fc5-B1C5-D9AD0ACCBA5E}")
CLSID_FileSaveDialog = GUID("{C0B4E2F3-BA21-4773-8DBA-335EC946EB8B}")
CLSID_FileSaveDialogLegacy = GUID("{AF02484C-A0A9-4669-9051-058AB12B9195}")
CLSID_ShellItemArrayShellNamespacehelper = GUID("{26671179-2ec2-42bf-93d3-64108589cad5}")
CLSID_ShellItemArrayShellNamespacehelper = GUID("{b77b1cbf-e827-44a9-a33a-6ccfeeaa142a}")  # redef??
CLSID_ShellItemArrayShellNamespacehelper = GUID("{CDC82860-468D-4d4e-B7E7-C298FF23AB2C}")  # redef??
CLSID_ShellItemArrayShellNamespacehelper = GUID("{F6166DAD-D3BE-4ebd-8419-9B5EAD8D0EC7}")  # redef??
CLSID_ShellLibraryAPI = GUID("{d9b3211d-e57f-4426-aaef-30a806add397}")
CLSID_ShellFileSystemFolder = GUID("{F3364BA0-65B9-11CE-A9BA-00AA004AE837}")
CLSID_ShellBindStatusCallbackProxy = GUID("{2B4F54B1-3D6D-11d0-8258-00C04FD5AE38}")
CLSID_ShellURL = GUID("{4bec2015-bfa1-42fa-9c0c-59431bbe880e}")
CLSID_ShellDropTarget = GUID("{4bf684f8-3d29-4403-810d-494e72c4291b}")
CLSID_ShellNameSpace = GUID("{55136805-B2DE-11D1-B9F2-00A0C98BC547}")

# Constants
CLSCTX_INPROC_SERVER = 1
FOS_OVERWRITEPROMPT = 0x00000002
FOS_STRICTFILETYPES = 0x00000004
FOS_NOCHANGEDIR = 0x00000008
FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
FOS_ALLNONSTORAGEITEMS = 0x00000080
FOS_NOVALIDATE = 0x00000100
FOS_ALLOWMULTISELECT = 0x00000200
FOS_PATHMUSTEXIST = 0x00000800
FOS_FILEMUSTEXIST = 0x00001000
FOS_CREATEPROMPT = 0x00002000
FOS_SHAREAWARE = 0x00004000
FOS_NOREADONLYRETURN = 0x00008000
FOS_NOTESTFILECREATE = 0x00010000
FOS_HIDEMRUPLACES = 0x00020000
FOS_HIDEPINNEDPLACES = 0x00040000
FOS_NODEREFERENCELINKS = 0x00100000
FOS_DONTADDTORECENT = 0x02000000
FOS_FORCESHOWHIDDEN = 0x10000000
FOS_DEFAULTNOMINIMODE = 0x20000000
FOS_FORCEPREVIEWPANEON = 0x40000000

SFGAOF = c_ulong
SFGAO_FILESYSTEM = 0x40000000
SFGAO_FOLDER = 0x20000000
class SIGDN(c_int):
    SIGDN_NORMALDISPLAY = 0x00000000
    SIGDN_PARENTRELATIVEPARSING = 0x80018001
    SIGDN_PARENTRELATIVEFORADDRESSBAR = 0x8001C001
    SIGDN_DESKTOPABSOLUTEPARSING = 0x80028000
    SIGDN_PARENTRELATIVEEDITING = 0x80031001
    SIGDN_DESKTOPABSOLUTEEDITING = 0x8004C000
    SIGDN_FILESYSPATH = 0x80058000
    SIGDN_URL = 0x80068000


class FDAP(c_int):
    FDAP_BOTTOM = 0x00000000
    FDAP_TOP = 0x00000001


class FDE_SHAREVIOLATION_RESPONSE(c_int):  # noqa: N801
    FDESVR_DEFAULT = 0x00000000
    FDESVR_ACCEPT = 0x00000001
    FDESVR_REFUSE = 0x00000002


FDE_OVERWRITE_RESPONSE = FDE_SHAREVIOLATION_RESPONSE


class COMFunctionPointers:
    def __init__(self):
        self.hOle32: _FuncPointer
        self.hShell32: _FuncPointer
        self.pCoInitialize: _FuncPointer
        self.pCoUninitialize: _FuncPointer
        self.pCoCreateInstance: _FuncPointer
        self.pCoTaskMemFree: _FuncPointer
        self.pSHCreateItemFromParsingName: _FuncPointer

    @staticmethod
    def load_library(dll_name: str) -> _FuncPointer:
        windll.kernel32.LoadLibraryW.argtypes = [LPCWSTR]
        windll.kernel32.LoadLibraryW.restype = c_void_p
        handle = windll.kernel32.LoadLibraryW(dll_name)
        if not handle:
            raise ValueError(f"Unable to load library: {dll_name}")
        return handle

    @staticmethod
    def resolve_function(handle: _FuncPointer, func: bytes, func_type: type[_FuncPointer]) -> _FuncPointer:
        windll.kernel32.GetProcAddress.argtypes = [c_void_p, c_char_p]
        windll.kernel32.GetProcAddress.restype = c_void_p
        address = windll.kernel32.GetProcAddress(handle, func)
        assert address is not None
        return func_type(address)


class COMDLG_FILTERSPEC(Structure):  # noqa: N801
    _fields_: Sequence[tuple[str, type[_CData]] | tuple[str, type[_CData], int]] = [
        ("pszName", LPCWSTR),
        ("pszSpec", LPCWSTR)
    ]


class IUnknown(comtypes.IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IUnknown
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        # implicitly defined in comtypes
        #COMMETHOD([], HRESULT, "QueryInterface",
        #          (["in"], POINTER(GUID), "riid"),
        #          (["out"], POINTER(POINTER(comtypes.IUnknown)), "ppvObject")),
        #COMMETHOD([], ULONG, "AddRef"),
        #COMMETHOD([], ULONG, "Release")
    ]
    QueryInterface: Callable[[GUID, _Pointer[_Pointer[IUnknown]]], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
class Unknown(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IUnknown]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)


class IModalWindow(comtypes.IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IModalWindow
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "Show",
                  (["in"], HWND, "hwndParent"))
    ]
    QueryInterface: Callable[[GUID, _Pointer[_Pointer[IUnknown]]], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    Show: Callable[[HWND | int], HRESULT]
class ModalWindow(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IModalWindow]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def Show(self, hwndParent: HWND | int) -> HRESULT:
        return S_OK


class IShellItem(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IShellItem
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "BindToHandler",
                  (["in"], POINTER(IUnknown), "pbc"),
                  (["in"], POINTER(GUID), "bhid"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "GetParent",
                  (["out"], POINTER(POINTER(IUnknown)), "ppsi")),
        COMMETHOD([], HRESULT, "GetDisplayName",
                  (["in"], c_ulong, "sigdnName"),
                  (["out"], POINTER(LPWSTR), "ppszName")),
        COMMETHOD([], HRESULT, "GetAttributes",
                  (["in"], c_ulong, "sfgaoMask"),
                  (["out"], POINTER(c_ulong), "psfgaoAttribs")),
        COMMETHOD([], HRESULT, "Compare",
                  (["in"], POINTER(IUnknown), "psi"),
                  (["in"], c_ulong, "hint"),
                  (["out"], POINTER(c_int), "piOrder"))
    ]
    QueryInterface: Callable[[GUID, _Pointer[_Pointer[IUnknown]]], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    BindToHandler: Callable[[_Pointer[IUnknown], GUID, GUID, _Pointer[c_void_p]], HRESULT]
    GetParent: Callable[[], IUnknown]
    GetDisplayName: Callable[[c_ulong | int], str]
    GetAttributes: Callable[[c_ulong | int], c_ulong]
    Compare: Callable[[_Pointer[IUnknown], c_ulong, c_int], HRESULT]
    @classmethod
    def from_path(cls, path: os.PathLike | str) -> _Pointer[Self]:
        pShellItem = POINTER(cls)()
        hr = SHCreateItemFromParsingName(c_wchar_p(str(path)), None, comtypes.byref(pShellItem))
        if hr != 0:
            raise OSError(f"Failed to create IShellItem from path. HRESULT: {hr}")
        return pShellItem

class ShellItem(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IShellItem]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def BindToHandler(self, pbc: _Pointer[comtypes.IUnknown], bhid: GUID, riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def GetParent(self, ppsi: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def GetDisplayName(self, sigdnName: c_ulong | int, ppszName: _Pointer[c_wchar_p]) -> HRESULT:
        return S_OK
    def GetAttributes(self, sfgaoMask: c_ulong | int, psfgaoAttribs: _Pointer[c_ulong]) -> HRESULT:
        return S_OK
    def Compare(self, psi: _Pointer[comtypes.IUnknown], hint: c_ulong | int, piOrder: c_int) -> HRESULT:
        return S_OK


SHCreateItemFromParsingName = windll.shell32.SHCreateItemFromParsingName
SHCreateItemFromParsingName.argtypes = [LPCWSTR, comtypes.POINTER(comtypes.IUnknown), comtypes.POINTER(POINTER(IShellItem))]
SHCreateItemFromParsingName.restype = HRESULT


class IContextMenu(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IContextMenu
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "QueryContextMenu",
                  (["in"], c_void_p, "hmenu"),
                  (["in"], c_uint, "indexMenu"),
                  (["in"], c_uint, "idCmdFirst"),
                  (["in"], c_uint, "idCmdLast"),
                  (["in"], c_uint, "uFlags")),
        COMMETHOD([], HRESULT, "InvokeCommand",
                  (["in"], c_void_p, "pici")),
        COMMETHOD([], HRESULT, "GetCommandString",
                  (["in"], c_uint, "idCmd"),
                  (["in"], c_uint, "uType"),
                  (["in"], c_void_p, "pReserved"),
                  (["out"], c_wchar_p, "pszName"),
                  (["in"], c_uint, "cchMax"))
    ]
    QueryInterface: Callable[[GUID, _Pointer[_Pointer[IUnknown]]], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    QueryContextMenu: Callable[[c_void_p, c_uint, c_uint, c_uint, c_uint], HRESULT]
    InvokeCommand: Callable[[c_void_p], HRESULT]
    GetCommandString: Callable[[c_uint, c_uint, c_void_p, _Pointer[c_wchar_p], c_uint], HRESULT]
class ContextMenu(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IContextMenu]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def QueryContextMenu(self, hmenu: c_void_p, indexMenu: c_uint | int, idCmdFirst: c_uint | int, idCmdLast: c_uint | int, uFlags: c_uint | int) -> HRESULT:
        return S_OK
    def InvokeCommand(self, pici: c_void_p) -> HRESULT:
        return S_OK
    def GetCommandString(self, idCmd: c_uint | int, uType: c_uint | int, pReserved: c_void_p, pszName: c_wchar_p, cchMax: c_uint | int) -> HRESULT:
        return S_OK


class IShellFolder(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IShellFolder
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "ParseDisplayName",
                  (["in"], HWND, "hwnd"),
                  (["in"], POINTER(IUnknown), "pbc"),
                  (["in"], LPCWSTR, "pszDisplayName"),
                  (["out"], POINTER(ULONG), "pchEaten"),
                  (["out"], POINTER(c_void_p), "ppidl"),
                  (["in"], POINTER(ULONG), "pdwAttributes")),
        COMMETHOD([], HRESULT, "EnumObjects",
                  (["in"], HWND, "hwnd"),
                  (["in"], c_ulong, "grfFlags"),
                  (["out"], POINTER(POINTER(IUnknown)), "ppenumIDList")),
        COMMETHOD([], HRESULT, "BindToObject",
                  (["in"], c_void_p, "pidl"),
                  (["in"], POINTER(IUnknown), "pbc"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "BindToStorage",
                  (["in"], c_void_p, "pidl"),
                  (["in"], POINTER(IUnknown), "pbc"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "CompareIDs",
                  (["in"], c_void_p, "lParam"),
                  (["in"], c_void_p, "pidl1"),
                  (["in"], c_void_p, "pidl2")),
        COMMETHOD([], HRESULT, "CreateViewObject",
                  (["in"], HWND, "hwndOwner"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "GetAttributesOf",
                  (["in"], c_uint, "cidl"),
                  (["in"], C_POINTER(c_void_p), "apidl"),
                  (["out"], POINTER(c_ulong), "rgfInOut")),
        COMMETHOD([], HRESULT, "GetUIObjectOf",
                  (["in"], HWND, "hwndOwner"),
                  (["in"], c_uint, "cidl"),
                  (["in"], C_POINTER(c_void_p), "apidl"),
                  (["in"], POINTER(GUID), "riid"),
                  (["in"], POINTER(c_uint), "rgfReserved"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "GetDisplayNameOf",
                  (["in"], c_void_p, "pidl"),
                  (["in"], c_ulong, "uFlags"),
                  (["out"], POINTER(c_wchar_p), "pName")),
        COMMETHOD([], HRESULT, "SetNameOf",
                  (["in"], HWND, "hwnd"),
                  (["in"], c_void_p, "pidl"),
                  (["in"], LPCWSTR, "pszName"),
                  (["in"], c_ulong, "uFlags"),
                  (["out"], POINTER(c_void_p), "ppidlOut"))
    ]
    QueryInterface: Callable[[GUID, _Pointer[_Pointer[IUnknown]]], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    ParseDisplayName: Callable[[HWND, _Pointer[IUnknown], LPCWSTR, _Pointer[ULONG], _Pointer[c_void_p], _Pointer[ULONG]], HRESULT]
    EnumObjects: Callable[[HWND, c_ulong, _Pointer[_Pointer[IUnknown]]], HRESULT]
    BindToObject: Callable[[c_void_p, _Pointer[IUnknown], GUID, _Pointer[c_void_p]], HRESULT]
    BindToStorage: Callable[[c_void_p, _Pointer[IUnknown], GUID, _Pointer[c_void_p]], HRESULT]
    CompareIDs: Callable[[c_void_p, c_void_p, c_void_p], HRESULT]
    CreateViewObject: Callable[[HWND, GUID, _Pointer[c_void_p]], HRESULT]
    GetAttributesOf: Callable[[c_uint, _Pointer[c_void_p], _Pointer[c_ulong]], HRESULT]
    GetUIObjectOf: Callable[[HWND, c_uint, _Pointer[c_void_p], GUID, _Pointer[c_uint], _Pointer[c_void_p]], HRESULT]
    GetDisplayNameOf: Callable[[c_void_p, c_ulong, _Pointer[c_wchar_p]], HRESULT]
    SetNameOf: Callable[[HWND, c_void_p, LPCWSTR, c_ulong, _Pointer[c_void_p]], HRESULT]
class ShellFolder(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IShellFolder]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def ParseDisplayName(self, hwnd: HWND | int, pbc: _Pointer[comtypes.IUnknown], pszDisplayName: LPCWSTR | str, pchEaten: _Pointer[ULONG], ppidl: _Pointer[c_void_p], pdwAttributes: _Pointer[ULONG]) -> HRESULT:
        return S_OK
    def EnumObjects(self, hwnd: HWND | int, grfFlags: c_ulong | int, ppenumIDList: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def BindToObject(self, pidl: c_void_p, pbc: _Pointer[comtypes.IUnknown], riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def BindToStorage(self, pidl: c_void_p, pbc: _Pointer[comtypes.IUnknown], riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def CompareIDs(self, lParam: c_void_p, pidl1: c_void_p, pidl2: c_void_p) -> HRESULT:
        return S_OK
    def CreateViewObject(self, hwndOwner: HWND | int, riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def GetAttributesOf(self, cidl: c_uint | int, apidl: _Pointer[c_void_p], rgfInOut: _Pointer[c_ulong]) -> HRESULT:
        return S_OK
    def GetUIObjectOf(self, hwndOwner: HWND | int, cidl: c_uint | int, apidl: _Pointer[c_void_p], riid: GUID, rgfReserved: _Pointer[c_uint], ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def GetDisplayNameOf(self, pidl: c_void_p, uFlags: c_ulong | int, pName: _Pointer[c_wchar_p]) -> HRESULT:
        return S_OK
    def SetNameOf(self, hwnd: HWND | int, pidl: c_void_p, pszName: LPCWSTR | str, uFlags: c_ulong | int, ppidlOut: _Pointer[c_void_p]) -> HRESULT:
        return S_OK


class IShellItemArray(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IShellItemArray
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "BindToHandler",
                  (["in"], POINTER(IUnknown), "pbc"),
                  (["in"], POINTER(GUID), "bhid"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "GetPropertyStore",
                  (["in"], c_ulong, "flags"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "GetPropertyDescriptionList",
                  (["in"], POINTER(GUID), "keyType"),
                  (["in"], POINTER(GUID), "riid"),
                  (["out"], POINTER(c_void_p), "ppv")),
        COMMETHOD([], HRESULT, "GetAttributes",
                  (["in"], c_ulong, "attribFlags"),
                  (["in"], c_ulong, "sfgaoMask"),
                  (["out"], POINTER(c_ulong), "psfgaoAttribs")),
        COMMETHOD([], HRESULT, "GetCount",
                  (["out"], POINTER(c_uint), "pdwNumItems")),
        COMMETHOD([], HRESULT, "GetItemAt",
                  (["in"], c_uint, "dwIndex"),
                  (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
        COMMETHOD([], HRESULT, "EnumItems",
                  (["out"], POINTER(POINTER(IUnknown)), "ppenumShellItems"))
    ]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    BindToHandler: Callable[[_Pointer[IUnknown], GUID, GUID], int]
    GetPropertyStore: Callable[[c_ulong, GUID], c_void_p]
    GetPropertyDescriptionList: Callable[[GUID, GUID], c_void_p]
    GetAttributes: Callable[[c_ulong, c_ulong], _Pointer[c_ulong]]
    GetCount: Callable[[], int]
    GetItemAt: Callable[[c_uint | int], IShellItem]
    EnumItems: Callable[[], comtypes.IUnknown]
class ShellItemArray(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IShellItemArray]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def BindToHandler(self, pbc: _Pointer[comtypes.IUnknown], bhid: GUID, riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def GetPropertyStore(self, flags: c_ulong | int, riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def GetPropertyDescriptionList(self, keyType: GUID, riid: GUID, ppv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def GetAttributes(self, attribFlags: c_ulong | int, sfgaoMask: c_ulong | int, psfgaoAttribs: _Pointer[c_ulong]) -> HRESULT:
        return S_OK
    def GetCount(self, pdwNumItems: _Pointer[c_uint]) -> HRESULT:
        return S_OK
    def GetItemAt(self, dwIndex: c_uint | int, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def EnumItems(self, ppenumShellItems: comtypes.IUnknown) -> HRESULT:
        return S_OK


class IShellItemFilter(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IShellItemFilter
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "IncludeItem",
                  (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "GetEnumFlagsForItem",
                  (["in"], POINTER(IShellItem), "psi"),
                  (["out"], POINTER(c_ulong), "pgrfFlags"))
    ]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    IncludeItem: Callable[[IShellItem], c_ulong]
    GetEnumFlagsForItem: Callable[[], HRESULT]
class ShellItemFilter(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IShellItemFilter]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def IncludeItem(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def GetEnumFlagsForItem(self, psi: IShellItem, pgrfFlags: _Pointer[c_ulong]) -> HRESULT:
        return S_OK


class IEnumShellItems(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IEnumShellItems
    _methods_: ClassVar[list[_ComMemberSpec]]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    Next: Callable[[_Pointer[IEnumShellItems], c_ulong, IShellItem, _Pointer[c_ulong]], HRESULT]
    Skip: Callable[[_Pointer[IEnumShellItems], c_ulong], HRESULT]
    Reset: Callable[[_Pointer[IEnumShellItems]], HRESULT]
    Clone: Callable[[_Pointer[IEnumShellItems], _Pointer[_Pointer[IEnumShellItems]]], HRESULT]
IEnumShellItems._methods_ = [  # noqa: SLF001
    COMMETHOD([], HRESULT, "Next",
                (["in"], c_ulong, "celt"),
                (["out"], POINTER(POINTER(IShellItem)), "rgelt"),
                (["out"], POINTER(c_ulong), "pceltFetched")),
    COMMETHOD([], HRESULT, "Skip",
                (["in"], c_ulong, "celt")),
    COMMETHOD([], HRESULT, "Reset"),
    COMMETHOD([], HRESULT, "Clone",
                (["out"], POINTER(POINTER(IEnumShellItems)), "ppenum"))
]
class EnumShellItems(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IEnumShellItems]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def Next(self, celt: c_ulong | int, rgelt: IShellItem, pceltFetched: _Pointer[c_ulong]) -> HRESULT:
        return S_OK
    def Skip(self, celt: c_ulong | int) -> HRESULT:
        return S_OK
    def Reset(self) -> HRESULT:
        return S_OK
    def Clone(self, ppenum: _Pointer[_Pointer[IEnumShellItems]]) -> HRESULT:
        return S_OK


class IPropertyStore(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IPropertyStore
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "GetCount",
                (["out"], POINTER(c_ulong), "count")),
        COMMETHOD([], HRESULT, "GetAt",
                (["in"], c_ulong, "index"),
                (["out"], POINTER(GUID), "key")),
        COMMETHOD([], HRESULT, "GetValue",
                (["in"], POINTER(GUID), "key"),
                (["out"], POINTER(c_void_p), "pv")),
        COMMETHOD([], HRESULT, "SetValue",
                (["in"], POINTER(GUID), "key"),
                (["in"], POINTER(c_void_p), "propvar")),
        COMMETHOD([], HRESULT, "Commit")
    ]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    GetCount: Callable[[_Pointer[IPropertyStore], _Pointer[c_ulong]], HRESULT]
    GetAt: Callable[[_Pointer[IPropertyStore], c_ulong, GUID], HRESULT]
    GetValue: Callable[[_Pointer[IPropertyStore], GUID, _Pointer[c_void_p]], HRESULT]
    SetValue: Callable[[_Pointer[IPropertyStore], GUID, _Pointer[c_void_p]], HRESULT]
    Commit: Callable[[_Pointer[IPropertyStore]], HRESULT]
class PropertyStore(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IPropertyStore]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def GetCount(self, count: _Pointer[c_ulong]) -> HRESULT:
        return S_OK
    def GetAt(self, index: c_ulong | int, key: GUID) -> HRESULT:
        return S_OK
    def GetValue(self, key: GUID, pv: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def SetValue(self, key: GUID, propvar: _Pointer[c_void_p]) -> HRESULT:
        return S_OK
    def Commit(self) -> HRESULT:
        return S_OK

class IFileOperationProgressSink(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IFileOperationProgressSink
    _methods_: ClassVar[list[_ComMemberSpec]] = [
    COMMETHOD([], HRESULT, "StartOperations"),
    COMMETHOD([], HRESULT, "FinishOperations",
              (["in"], HRESULT, "hr")),
    COMMETHOD([], HRESULT, "PreRenameItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], c_wchar_p, "pszNewName")),
    COMMETHOD([], HRESULT, "PostRenameItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], c_wchar_p, "pszNewName"),
              (["in"], HRESULT, "hrRename"),
              (["in"], POINTER(IShellItem), "psiNewlyCreated")),
    COMMETHOD([], HRESULT, "PreMoveItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], POINTER(IShellItem), "psiDestinationFolder"),
              (["in"], c_wchar_p, "pszNewName")),
    COMMETHOD([], HRESULT, "PostMoveItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], POINTER(IShellItem), "psiDestinationFolder"),
              (["in"], c_wchar_p, "pszNewName"),
              (["in"], HRESULT, "hrMove"),
              (["in"], POINTER(IShellItem), "psiNewlyCreated")),
    COMMETHOD([], HRESULT, "PreCopyItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], POINTER(IShellItem), "psiDestinationFolder"),
              (["in"], c_wchar_p, "pszNewName")),
    COMMETHOD([], HRESULT, "PostCopyItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], POINTER(IShellItem), "psiDestinationFolder"),
              (["in"], c_wchar_p, "pszNewName"),
              (["in"], HRESULT, "hrCopy"),
              (["in"], POINTER(IShellItem), "psiNewlyCreated")),
    COMMETHOD([], HRESULT, "PreDeleteItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem")),
    COMMETHOD([], HRESULT, "PostDeleteItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiItem"),
              (["in"], HRESULT, "hrDelete"),
              (["in"], POINTER(IShellItem), "psiNewlyCreated")),
    COMMETHOD([], HRESULT, "PreNewItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiDestinationFolder"),
              (["in"], c_wchar_p, "pszNewName")),
    COMMETHOD([], HRESULT, "PostNewItem",
              (["in"], c_ulong, "dwFlags"),
              (["in"], POINTER(IShellItem), "psiDestinationFolder"),
              (["in"], c_wchar_p, "pszNewName"),
              (["in"], c_wchar_p, "pszTemplateName"),
              (["in"], c_ulong, "dwFileAttributes"),
              (["in"], HRESULT, "hrNew"),
              (["in"], POINTER(IShellItem), "psiNewItem")),
    COMMETHOD([], HRESULT, "UpdateProgress",
              (["in"], c_ulong, "iWorkTotal"),
              (["in"], c_ulong, "iWorkSoFar")),
    COMMETHOD([], HRESULT, "ResetTimer"),
    COMMETHOD([], HRESULT, "PauseTimer"),
    COMMETHOD([], HRESULT, "ResumeTimer")
]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    StartOperations: Callable[[], HRESULT]
    FinishOperations: Callable[[HRESULT], HRESULT]
    PreRenameItem: Callable[[c_ulong, IShellItem, c_wchar_p], HRESULT]
    PostRenameItem: Callable[[c_ulong, IShellItem, c_wchar_p, HRESULT, IShellItem], HRESULT]
    PreMoveItem: Callable[[c_ulong, IShellItem, IShellItem, c_wchar_p], HRESULT]
    PostMoveItem: Callable[[c_ulong, IShellItem, IShellItem, c_wchar_p, HRESULT, IShellItem], HRESULT]
    PreCopyItem: Callable[[c_ulong, IShellItem, IShellItem, c_wchar_p], HRESULT]
    PostCopyItem: Callable[[c_ulong, IShellItem, IShellItem, c_wchar_p, HRESULT, IShellItem], HRESULT]
    PreDeleteItem: Callable[[c_ulong, IShellItem], HRESULT]
    PostDeleteItem: Callable[[c_ulong, IShellItem, HRESULT, IShellItem], HRESULT]
    PreNewItem: Callable[[c_ulong, IShellItem, c_wchar_p], HRESULT]
    PostNewItem: Callable[[c_ulong, IShellItem, c_wchar_p, c_wchar_p, c_ulong, HRESULT, IShellItem], HRESULT]
    UpdateProgress: Callable[[c_ulong, c_ulong], HRESULT]
    ResetTimer: Callable[[], HRESULT]
    PauseTimer: Callable[[], HRESULT]
    ResumeTimer: Callable[[], HRESULT]
class FileOperationProgressSink(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileOperationProgressSink]
    def StartOperations(self) -> HRESULT:
        return S_OK
    def FinishOperations(self, hr: HRESULT) -> HRESULT:
        return S_OK
    def PreRenameItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, pszNewName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def PostRenameItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, pszNewName: LPCWSTR | str, hrRename: HRESULT, psiNewlyCreated: IShellItem) -> HRESULT:
        return S_OK
    def PreMoveItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, psiDestinationFolder: IShellItem, pszNewName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def PostMoveItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, psiDestinationFolder: IShellItem, pszNewName: LPCWSTR | str, hrMove: HRESULT, psiNewlyCreated: IShellItem) -> HRESULT:
        return S_OK
    def PreCopyItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, psiDestinationFolder: IShellItem, pszNewName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def PostCopyItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, psiDestinationFolder: IShellItem, pszNewName: LPCWSTR | str, hrCopy: HRESULT, psiNewlyCreated: IShellItem) -> HRESULT:
        return S_OK
    def PreDeleteItem(self, dwFlags: c_ulong | int, psiItem: IShellItem) -> HRESULT:
        return S_OK
    def PostDeleteItem(self, dwFlags: c_ulong | int, psiItem: IShellItem, hrDelete: HRESULT, psiNewlyCreated: IShellItem) -> HRESULT:
        return S_OK
    def PreNewItem(self, dwFlags: c_ulong | int, psiDestinationFolder: IShellItem, pszNewName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def PostNewItem(self, dwFlags: c_ulong | int, psiDestinationFolder: IShellItem, pszNewName: LPCWSTR | str, pszTemplateName: LPCWSTR | str, dwFileAttributes: c_ulong | int, hrNew: HRESULT, psiNewItem: IShellItem) -> HRESULT:
        return S_OK
    def UpdateProgress(self, iWorkTotal: c_ulong | int, iWorkSoFar: c_ulong | int) -> HRESULT:
        return S_OK
    def ResetTimer(self) -> HRESULT:
        return S_OK
    def PauseTimer(self) -> HRESULT:
        return S_OK
    def ResumeTimer(self) -> HRESULT:
        return S_OK


class IFileDialogEvents(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IFileDialogEvents
    _methods_: ClassVar[list[_ComMemberSpec]]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    OnFileOk: Callable[[IFileDialog], HRESULT]
    OnFolderChanging: Callable[[IFileDialog, IShellItem], HRESULT]
    OnFolderChange: Callable[[IFileDialog], HRESULT]
    OnSelectionChange: Callable[[IFileDialog], HRESULT]
    OnShareViolation: Callable[[IFileDialog, IShellItem, c_int], HRESULT]
    OnTypeChange: Callable[[IFileDialog], HRESULT]
    OnOverwrite: Callable[[IFileDialog, IShellItem, c_int], HRESULT]
class IFileDialog(IModalWindow):
    _iid_: GUID = IID_IFileDialog
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "SetFileTypes",
                  (["in"], c_uint, "cFileTypes"),
                  (["in"], POINTER(c_void_p), "rgFilterSpec")),
        COMMETHOD([], HRESULT, "SetFileTypeIndex",
                  (["in"], c_uint, "iFileType")),
        COMMETHOD([], HRESULT, "GetFileTypeIndex",
                  (["out"], POINTER(c_uint), "piFileType")),
        COMMETHOD([], HRESULT, "Advise",
                  (["in"], POINTER(IUnknown), "pfde"),
                  (["out"], POINTER(DWORD), "pdwCookie")),
        COMMETHOD([], HRESULT, "Unadvise",
                  (["in"], DWORD, "dwCookie")),
        COMMETHOD([], HRESULT, "SetOptions",
                  (["in"], c_uint, "fos")),
        COMMETHOD([], HRESULT, "GetOptions",
                  (["out"], POINTER(DWORD), "pfos")),
        COMMETHOD([], HRESULT, "SetDefaultFolder",
                  (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "SetFolder",
                  (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "GetFolder",
                  (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
        COMMETHOD([], HRESULT, "GetCurrentSelection",
                  (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
        COMMETHOD([], HRESULT, "SetFileName",
                  (["in"], LPCWSTR, "pszName")),
        COMMETHOD([], HRESULT, "GetFileName",
                  (["out"], POINTER(LPWSTR), "pszName")),
        COMMETHOD([], HRESULT, "SetTitle",
                  (["in"], LPCWSTR, "pszTitle")),
        COMMETHOD([], HRESULT, "SetOkButtonLabel",
                  (["in"], LPCWSTR, "pszText")),
        COMMETHOD([], HRESULT, "SetFileNameLabel",
                  (["in"], LPCWSTR, "pszLabel")),
        COMMETHOD([], HRESULT, "GetResult",
                  (["out"], POINTER(POINTER(IShellItem)), "ppsi")),
        COMMETHOD([], HRESULT, "AddPlace",
                  (["in"], POINTER(IShellItem), "psi"),
                  (["in"], c_int, "fdap")),
        COMMETHOD([], HRESULT, "SetDefaultExtension",
                  (["in"], LPCWSTR, "pszDefaultExtension")),
        COMMETHOD([], HRESULT, "Close",
                  (["in"], HRESULT, "hr")),
        COMMETHOD([], HRESULT, "SetClientGuid",
                  (["in"], POINTER(GUID), "guid")),
        COMMETHOD([], HRESULT, "ClearClientData"),
        COMMETHOD([], HRESULT, "SetFilter",
                  (["in"], POINTER(IShellItemFilter), "pFilter"))
    ]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    Show: Callable[[int | HWND], HRESULT]
    SetFileTypes: Callable[[c_uint | int, _Pointer[c_void_p]], HRESULT]
    SetFileTypeIndex: Callable[[c_uint], HRESULT]
    GetFileTypeIndex: Callable[[], _Pointer[c_uint]]
    Advise: Callable[[IUnknown | comtypes.COMObject], int]
    Unadvise: Callable[[int], HRESULT]
    SetOptions: Callable[[DWORD | int], HRESULT]
    GetOptions: Callable[[], int]
    SetDefaultFolder: Callable[[_Pointer[IShellItem]], HRESULT]
    SetFolder: Callable[[_Pointer[IShellItem]], HRESULT]
    GetFolder: Callable[[], IShellItem]
    GetCurrentSelection: Callable[[], IShellItem]
    SetFileName: Callable[[str], HRESULT]
    GetFileName: Callable[[], _Pointer[LPWSTR]]
    SetTitle: Callable[[str], HRESULT]
    SetOkButtonLabel: Callable[[str], HRESULT]
    SetFileNameLabel: Callable[[str], HRESULT]
    GetResult: Callable[[], IShellItem]
    AddPlace: Callable[[IShellItem, c_int], HRESULT]
    SetDefaultExtension: Callable[[str], HRESULT]
    Close: Callable[[HRESULT], HRESULT]
    SetClientGuid: Callable[[GUID], HRESULT]
    ClearClientData: Callable[[], HRESULT]
    SetFilter: Callable[[IShellItemFilter], HRESULT]
IFileDialogEvents._methods_ = [  # noqa: SLF001
        COMMETHOD([], HRESULT, "OnFileOk",
                  (["in"], POINTER(IFileDialog), "pfd")),
        COMMETHOD([], HRESULT, "OnFolderChanging",
                  (["in"], POINTER(IFileDialog), "pfd"),
                  (["in"], POINTER(IShellItem), "psiFolder")),
        COMMETHOD([], HRESULT, "OnFolderChange",
                  (["in"], POINTER(IFileDialog), "pfd")),
        COMMETHOD([], HRESULT, "OnSelectionChange",
                  (["in"], POINTER(IFileDialog), "pfd")),
        COMMETHOD([], HRESULT, "OnShareViolation",
                  (["in"], POINTER(IFileDialog), "pfd"),
                  (["in"], POINTER(IShellItem), "psi"),
                  (["out"], POINTER(c_int), "pResponse")),
        COMMETHOD([], HRESULT, "OnTypeChange",
                  (["in"], POINTER(IFileDialog), "pfd")),
        COMMETHOD([], HRESULT, "OnOverwrite",
                  (["in"], POINTER(IFileDialog), "pfd"),
                  (["in"], POINTER(IShellItem), "psi"),
                  (["out"], POINTER(c_int), "pResponse"))
    ]
class FileDialogEvents(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileDialogEvents]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def OnFileOk(self, ifd: IFileDialog) -> HRESULT:
        return S_OK
    def OnFolderChanging(self, ifd: IFileDialog, isiFolder: IShellItem) -> HRESULT:
        return S_OK
    def OnFolderChange(self, ifd: IFileDialog) -> HRESULT:
        return S_OK
    def OnSelectionChange(self, ifd: IFileDialog) -> HRESULT:
        return S_OK
    def OnShareViolation(self, ifd: IFileDialog, psi: IShellItem, response: c_int) -> HRESULT:
        return S_OK
    def OnTypeChange(self, ifd: IFileDialog) -> HRESULT:
        return S_OK
    def OnOverwrite(self, ifd: IFileDialog, psi: IShellItem, response: c_int) -> HRESULT:
        return S_OK
class FileDialog(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileDialog]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def Show(self, hwndOwner: HWND | int) -> HRESULT:
        return S_OK
    def SetFileTypes(self, cFileTypes: c_uint | int, rgFilterSpec: Array[COMDLG_FILTERSPEC]) -> HRESULT:
        return S_OK
    def SetFileTypeIndex(self, iFileType: c_uint | int) -> HRESULT:
        return S_OK
    def GetFileTypeIndex(self, piFileType: _Pointer[c_uint]) -> HRESULT:
        return S_OK
    def Advise(self, pfde: _Pointer[IUnknown], pdwCookie: _Pointer[DWORD]) -> HRESULT:
        return S_OK
    def Unadvise(self, dwCookie: int) -> HRESULT:
        return S_OK
    def SetOptions(self, fos: int) -> HRESULT:
        return S_OK
    def GetOptions(self, pfos: _Pointer[DWORD]) -> HRESULT:
        return S_OK
    def SetDefaultFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def SetFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def GetFolder(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def GetCurrentSelection(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def SetFileName(self, pszName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def GetFileName(self, pszName: _Pointer[LPWSTR]) -> HRESULT:
        return S_OK
    def SetTitle(self, pszTitle: LPCWSTR | str) -> HRESULT:
        return S_OK
    def SetOkButtonLabel(self, pszText: LPCWSTR | str) -> HRESULT:
        return S_OK
    def SetFileNameLabel(self, pszLabel: LPCWSTR | str) -> HRESULT:
        return S_OK
    def GetResult(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def AddPlace(self, psi: IShellItem, fdap: c_int) -> HRESULT:
        return S_OK
    def SetDefaultExtension(self, pszDefaultExtension: LPCWSTR | str) -> HRESULT:
        return S_OK
    def Close(self, hr: HRESULT | int) -> HRESULT:
        return S_OK
    def SetClientGuid(self, guid: GUID) -> HRESULT:
        return S_OK
    def ClearClientData(self) -> HRESULT:
        return S_OK
    def SetFilter(self, pFilter: IShellItemFilter) -> HRESULT:
        return S_OK


class IShellLibrary(IUnknown):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IShellLibrary
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "LoadLibraryFromItem",
                (["in"], POINTER(IShellItem), "psi"),
                (["in"], c_ulong, "grfMode")),
        COMMETHOD([], HRESULT, "LoadLibraryFromKnownFolder",
                (["in"], POINTER(GUID), "kfidLibrary"),
                (["in"], c_ulong, "grfMode")),
        COMMETHOD([], HRESULT, "AddFolder",
                (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "RemoveFolder",
                (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "GetFolders",
                (["in"], c_int, "lff"),
                (["in"], POINTER(GUID), "riid"),
                (["out"], POINTER(POINTER(c_void_p)), "ppv")),
        COMMETHOD([], HRESULT, "ResolveFolder",
                (["in"], POINTER(IShellItem), "psi"),
                (["in"], c_ulong, "grfMode"),
                (["in"], POINTER(GUID), "riid"),
                (["out"], POINTER(POINTER(c_void_p)), "ppv")),
        COMMETHOD([], HRESULT, "GetDefaultSaveFolder",
                (["in"], c_int, "dsft"),
                (["in"], POINTER(GUID), "riid"),
                (["out"], POINTER(POINTER(c_void_p)), "ppv")),
        COMMETHOD([], HRESULT, "SetDefaultSaveFolder",
                (["in"], c_int, "dsft"),
                (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "GetOptions",
                (["out"], POINTER(c_uint), "pOptions")),
        COMMETHOD([], HRESULT, "SetOptions",
                (["in"], c_ulong, "stfOptions"),
                (["in"], c_ulong, "stfMask")),
        COMMETHOD([], HRESULT, "GetFolderType",
                (["out"], POINTER(GUID), "pftid")),
        COMMETHOD([], HRESULT, "SetFolderType",
                (["in"], POINTER(GUID), "ftid")),
        COMMETHOD([], HRESULT, "GetIcon",
                (["out"], POINTER(LPWSTR), "ppszIcon")),
        COMMETHOD([], HRESULT, "SetIcon",
                (["in"], LPCWSTR, "pszIcon")),
        COMMETHOD([], HRESULT, "Commit"),
        COMMETHOD([], HRESULT, "Save",
                (["in"], POINTER(IShellItem), "psiFolderToSaveIn"),
                (["in"], LPCWSTR, "pszLibraryName"),
                (["in"], c_ulong, "lrf"),
                (["out"], POINTER(POINTER(IShellItem)), "ppsiNewItem")),
        COMMETHOD([], HRESULT, "SaveInKnownFolder",
                (["in"], POINTER(GUID), "kfid"),
                (["in"], LPCWSTR, "pszLibraryName"),
                (["in"], c_ulong, "lrf"),
                (["out"], POINTER(POINTER(IShellItem)), "ppsiNewItem"))
    ]
    QueryInterface: Callable[[GUID, comtypes.IUnknown], HRESULT]
    AddRef: Callable[[], ULONG]
    Release: Callable[[], ULONG]
    LoadLibraryFromItem: Callable[[_Pointer[IShellLibrary], IShellItem, c_ulong], HRESULT]
    LoadLibraryFromKnownFolder: Callable[[_Pointer[IShellLibrary], GUID, c_ulong], HRESULT]
    AddFolder: Callable[[_Pointer[IShellLibrary], IShellItem], HRESULT]
    RemoveFolder: Callable[[_Pointer[IShellLibrary], IShellItem], HRESULT]
    GetFolders: Callable[[_Pointer[IShellLibrary], c_int, GUID, _Pointer[_Pointer[c_void_p]]], HRESULT]
    ResolveFolder: Callable[[_Pointer[IShellLibrary], IShellItem, c_ulong, GUID, _Pointer[_Pointer[c_void_p]]], HRESULT]
    GetDefaultSaveFolder: Callable[[_Pointer[IShellLibrary], c_int, GUID, _Pointer[_Pointer[c_void_p]]], HRESULT]
    SetDefaultSaveFolder: Callable[[_Pointer[IShellLibrary], c_int, IShellItem], HRESULT]
    GetOptions: Callable[[_Pointer[IShellLibrary], _Pointer[c_uint]], HRESULT]
    SetOptions: Callable[[_Pointer[IShellLibrary], c_ulong, c_ulong], HRESULT]
    GetFolderType: Callable[[_Pointer[IShellLibrary], GUID], HRESULT]
    SetFolderType: Callable[[_Pointer[IShellLibrary], GUID], HRESULT]
    GetIcon: Callable[[_Pointer[IShellLibrary], _Pointer[LPWSTR]], HRESULT]
    SetIcon: Callable[[_Pointer[IShellLibrary], LPCWSTR], HRESULT]
    Commit: Callable[[_Pointer[IShellLibrary]], HRESULT]
    Save: Callable[[_Pointer[IShellLibrary], IShellItem, LPCWSTR, c_ulong, IShellItem], HRESULT]
    SaveInKnownFolder: Callable[[_Pointer[IShellLibrary], GUID, LPCWSTR, c_ulong, IShellItem], HRESULT]
class ShellLibrary(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IShellLibrary]
    def LoadLibraryFromItem(self, psi: IShellItem, grfMode: c_ulong | int) -> HRESULT:
        return S_OK
    def LoadLibraryFromKnownFolder(self, kfidLibrary: GUID, grfMode: c_ulong | int) -> HRESULT:
        return S_OK
    def AddFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def RemoveFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def GetFolders(self, lff: c_int | int, riid: GUID, ppv: _Pointer[_Pointer[c_void_p]]) -> HRESULT:
        return S_OK
    def ResolveFolder(self, psi: IShellItem, grfMode: c_ulong | int, riid: GUID, ppv: _Pointer[_Pointer[c_void_p]]) -> HRESULT:
        return S_OK
    def GetDefaultSaveFolder(self, dsft: c_int | int, riid: GUID, ppv: _Pointer[_Pointer[c_void_p]]) -> HRESULT:
        return S_OK
    def SetDefaultSaveFolder(self, dsft: c_int | int, psi: IShellItem) -> HRESULT:
        return S_OK
    def GetOptions(self, pOptions: _Pointer[c_uint]) -> HRESULT:
        return S_OK
    def SetOptions(self, stfOptions: c_ulong | int, stfMask: c_ulong | int) -> HRESULT:
        return S_OK
    def GetFolderType(self, pftid: GUID) -> HRESULT:
        return S_OK
    def SetFolderType(self, ftid: GUID) -> HRESULT:
        return S_OK
    def GetIcon(self, ppszIcon: _Pointer[LPWSTR]) -> HRESULT:
        return S_OK
    def SetIcon(self, pszIcon: LPCWSTR | str) -> HRESULT:
        return S_OK
    def Commit(self) -> HRESULT:
        return S_OK
    def Save(self, psiFolderToSaveIn: IShellItem, pszLibraryName: LPCWSTR | str, lrf: c_ulong | int, ppsiNewItem: IShellItem) -> HRESULT:
        return S_OK
    def SaveInKnownFolder(self, kfid: GUID, pszLibraryName: LPCWSTR | str, lrf: c_ulong | int, ppsiNewItem: IShellItem) -> HRESULT:
        return S_OK


class IFileOpenDialog(IFileDialog):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IFileOpenDialog
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "GetResults",
                  (["out"], POINTER(POINTER(IShellItemArray)), "ppenum")),
        COMMETHOD([], HRESULT, "GetSelectedItems",
                  (["out"], POINTER(POINTER(IShellItemArray)), "ppsai"))
    ]
    GetResults: Callable[[], IShellItemArray]
    GetSelectedItems: Callable[[], IShellItemArray]
class FileOpenDialog(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileOpenDialog]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def Show(self, hwndParent: HWND | int) -> HRESULT:
        return S_OK
    def SetFileTypes(self, cFileTypes: c_uint | int, rgFilterSpec: Array[COMDLG_FILTERSPEC]) -> HRESULT:
        return S_OK
    def SetFileTypeIndex(self, iFileType: c_uint | int) -> HRESULT:
        return S_OK
    def GetFileTypeIndex(self, piFileType: _Pointer[c_uint]) -> HRESULT:
        return S_OK
    def Advise(self, pfde: _Pointer[comtypes.IUnknown], pdwCookie: _Pointer[DWORD]) -> HRESULT:
        return S_OK
    def Unadvise(self, dwCookie: int) -> HRESULT:
        return S_OK
    def SetOptions(self, fos: int) -> HRESULT:
        return S_OK
    def GetOptions(self, pfos: _Pointer[DWORD]) -> HRESULT:
        return S_OK
    def SetDefaultFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def SetFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def GetFolder(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def GetCurrentSelection(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def SetFileName(self, pszName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def GetFileName(self, pszName: _Pointer[LPWSTR]) -> HRESULT:
        return S_OK
    def SetTitle(self, pszTitle: LPCWSTR | str) -> HRESULT:
        return S_OK
    def SetOkButtonLabel(self, pszText: LPCWSTR | str) -> HRESULT:
        return S_OK
    def SetFileNameLabel(self, pszLabel: LPCWSTR | str) -> HRESULT:
        return S_OK
    def GetResult(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def AddPlace(self, psi: IShellItem, fdap: c_int) -> HRESULT:
        return S_OK
    def SetDefaultExtension(self, pszDefaultExtension: LPCWSTR | str) -> HRESULT:
        return S_OK
    def Close(self, hr: HRESULT | int) -> HRESULT:
        return S_OK
    def SetClientGuid(self, guid: GUID) -> HRESULT:
        return S_OK
    def ClearClientData(self) -> HRESULT:
        return S_OK
    def SetFilter(self, isFilter: IShellItemFilter) -> HRESULT:
        return S_OK
    def GetResults(self, isArray: IShellItemArray) -> HRESULT:
        return S_OK
    def GetSelectedItems(self, ppsai: IShellItemArray) -> HRESULT:
        return S_OK


class IFileSaveDialog(IFileDialog):
    _case_insensitive_: bool = True
    _iid_: GUID = IID_IFileSaveDialog
    _methods_: ClassVar[list[_ComMemberSpec]] = [
        COMMETHOD([], HRESULT, "SetSaveAsItem",
                  (["in"], POINTER(IShellItem), "psi")),
        COMMETHOD([], HRESULT, "SetProperties",
                  (["in"], POINTER(IUnknown), "pStore")),
        COMMETHOD([], HRESULT, "SetCollectedProperties",
                  (["in"], POINTER(IUnknown), "pList"),
                  (["in"], BOOL, "fAppendDefault")),
        COMMETHOD([], HRESULT, "GetProperties",
                  (["out"], POINTER(POINTER(IUnknown)), "ppStore")),
        COMMETHOD([], HRESULT, "ApplyProperties",
                  (["in"], POINTER(IShellItem), "psi"),
                  (["in"], POINTER(IUnknown), "pStore"),
                  (["in"], HWND, "hwnd"),
                  (["in"], POINTER(IUnknown), "pSink"))
    ]
    SetSaveAsItem: Callable[[IShellItem], HRESULT]
    SetProperties: Callable[[_Pointer[IUnknown]], HRESULT]
    SetCollectedProperties: Callable[[_Pointer[IUnknown], BOOL], HRESULT]
    GetProperties: Callable[[_Pointer[_Pointer[IUnknown]]], HRESULT]
    ApplyProperties: Callable[[IShellItem, _Pointer[IUnknown], HWND, _Pointer[IUnknown]], HRESULT]
class FileSaveDialog(comtypes.COMObject):
    _com_interfaces_: Sequence[type[comtypes.IUnknown]] = [IFileSaveDialog]
    def QueryInterface(self, riid: GUID, ppvObject: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def AddRef(self) -> ULONG:
        return ULONG(-1)
    def Release(self) -> ULONG:
        return ULONG(-1)
    def Show(self, hwndParent: HWND | int) -> HRESULT:
        return S_OK
    def SetFileTypes(self, cFileTypes: c_uint | int, rgFilterSpec: _Pointer[COMDLG_FILTERSPEC]) -> HRESULT:
        return S_OK
    def SetFileTypeIndex(self, iFileType: c_uint | int) -> HRESULT:
        return S_OK
    def GetFileTypeIndex(self, piFileType: _Pointer[c_uint]) -> HRESULT:
        return S_OK
    def Advise(self, pfde: _Pointer[IUnknown], pdwCookie: _Pointer[DWORD]) -> HRESULT:
        return S_OK
    def Unadvise(self, dwCookie: int) -> HRESULT:
        return S_OK
    def SetOptions(self, fos: int) -> HRESULT:
        return S_OK
    def GetOptions(self, pfos: _Pointer[DWORD]) -> HRESULT:
        return S_OK
    def SetDefaultFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def SetFolder(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def GetFolder(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def GetCurrentSelection(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def SetFileName(self, pszName: LPCWSTR | str) -> HRESULT:
        return S_OK
    def GetFileName(self, pszName: _Pointer[LPWSTR]) -> HRESULT:
        return S_OK
    def SetTitle(self, pszTitle: LPCWSTR | str) -> HRESULT:
        return S_OK
    def SetOkButtonLabel(self, pszText: LPCWSTR | str) -> HRESULT:
        return S_OK
    def SetFileNameLabel(self, pszLabel: LPCWSTR | str) -> HRESULT:
        return S_OK
    def GetResult(self, ppsi: IShellItem) -> HRESULT:
        return S_OK
    def AddPlace(self, psi: IShellItem, fdap: c_int) -> HRESULT:
        return S_OK
    def SetDefaultExtension(self, pszDefaultExtension: LPCWSTR | str) -> HRESULT:
        return S_OK
    def Close(self, hr: HRESULT | int) -> HRESULT:
        return S_OK
    def SetClientGuid(self, guid: GUID) -> HRESULT:
        return S_OK
    def ClearClientData(self) -> HRESULT:
        return S_OK
    def SetFilter(self, pFilter: IShellItemFilter) -> HRESULT:
        return S_OK
    def SetSaveAsItem(self, psi: IShellItem) -> HRESULT:
        return S_OK
    def SetProperties(self, pStore: _Pointer[comtypes.IUnknown]) -> HRESULT:
        return S_OK
    def SetCollectedProperties(self, pList: _Pointer[comtypes.IUnknown], fAppendDefault: BOOL | int) -> HRESULT:
        return S_OK
    def GetProperties(self, ppStore: comtypes.IUnknown) -> HRESULT:
        return S_OK
    def ApplyProperties(self, psi: IShellItem, pStore: _Pointer[comtypes.IUnknown], hwnd: HWND | int, pSink: _Pointer[comtypes.IUnknown]) -> HRESULT:
        return S_OK


if __name__ == "__main__":
    assert Unknown()
    assert ModalWindow()
    assert ShellItem()
    assert ContextMenu()
    assert ShellFolder()
    assert ShellItemArray()
    assert ShellItemFilter()
    assert EnumShellItems()
    assert PropertyStore()
    assert FileOperationProgressSink()
    assert FileDialogEvents()
    assert FileDialog()
    assert ShellLibrary()
    assert FileOpenDialog()
    assert FileSaveDialog()