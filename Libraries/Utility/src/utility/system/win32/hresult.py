from __future__ import annotations

from ctypes import HRESULT

FACILITY_CODES = {
    0: "FACILITY_NULL",
    1: "FACILITY_RPC",
    2: "FACILITY_DISPATCH",
    3: "FACILITY_STORAGE",
    4: "FACILITY_ITF",
    7: "FACILITY_WIN32",
    8: "FACILITY_WINDOWS",
    9: "FACILITY_SECURITY",
    10: "FACILITY_CONTROL",
    11: "FACILITY_CERT",
    12: "FACILITY_INTERNET",
    13: "FACILITY_MEDIASERVER",
    14: "FACILITY_MSMQ",
    15: "FACILITY_SETUPAPI",
    16: "FACILITY_SCARD",
    17: "FACILITY_COMPLUS",
    18: "FACILITY_AAF",
    19: "FACILITY_URT",
    20: "FACILITY_ACS",
    21: "FACILITY_DPLAY",
    22: "FACILITY_UMI",
    23: "FACILITY_SXS",
    24: "FACILITY_WINDOWS_CE",
    25: "FACILITY_HTTP",
    26: "FACILITY_USERMODE_COMMONLOG",
    27: "FACILITY_WER",
    28: "FACILITY_USERMODE_FILTER_MANAGER",
    29: "FACILITY_BACKGROUNDCOPY",
    30: "FACILITY_CONFIGURATION",
    31: "FACILITY_STATE_MANAGEMENT",
    32: "FACILITY_METADIRECTORY",
    33: "FACILITY_SYSTEM_INTEGRITY",
    34: "FACILITY_VIRTUALIZATION",
    35: "FACILITY_VOLMGR",
    36: "FACILITY_BCD",
    37: "FACILITY_USERMODE_VHD",
    38: "FACILITY_USERMODE_HYPERVISOR",
    39: "FACILITY_USERMODE_VM",
    40: "FACILITY_USERMODE_VOLSNAP",
    41: "FACILITY_USERMODE_STORLIB",
    42: "FACILITY_USERMODE_LICENSING",
    43: "FACILITY_USERMODE_SMB",
    44: "FACILITY_USERMODE_VSS",
    45: "FACILITY_USERMODE_FILE_REPLICATION",
    46: "FACILITY_USERMODE_NDIS",
    47: "FACILITY_USERMODE_TPM",
    48: "FACILITY_USERMODE_NT",
    49: "FACILITY_USERMODE_USB",
    50: "FACILITY_USERMODE_NTOS",
    51: "FACILITY_USERMODE_COMPLUS",
    52: "FACILITY_USERMODE_NET",
    53: "FACILITY_USERMODE_CONFIGURATION_MANAGER",
    54: "FACILITY_USERMODE_COM",
    55: "FACILITY_USERMODE_DIRECTORY_SERVICE",
    56: "FACILITY_USERMODE_CMI",
    57: "FACILITY_USERMODE_LSA",
    58: "FACILITY_USERMODE_RPC",
    59: "FACILITY_USERMODE_IPSECVPN",
    60: "FACILITY_USERMODE_NETWORK_POLICY",
    61: "FACILITY_USERMODE_DNS_SERVER",
    62: "FACILITY_USERMODE_DNS_SERVER_ADMIN",
    63: "FACILITY_USERMODE_DNS_SERVER_CONFIGURATION",
    64: "FACILITY_USERMODE_DNS_SERVER_TUNING",
    65: "FACILITY_USERMODE_DNS_SERVER_ZONE",
    66: "FACILITY_USERMODE_DNS_SERVER_FORWARDER",
    67: "FACILITY_USERMODE_DNS_SERVER_REPLICATION",
    68: "FACILITY_USERMODE_DNS_SERVER_NDNC",
    69: "FACILITY_USERMODE_DNS_SERVER_FORWARDS",
    70: "FACILITY_USERMODE_DNS_SERVER_DS",
    71: "FACILITY_USERMODE_DNS_SERVER_ROOT_HINTS",
    72: "FACILITY_USERMODE_DNS_SERVER_ZONE_SOURCE",
    73: "FACILITY_USERMODE_DNS_SERVER_DATABASE",
    74: "FACILITY_USERMODE_DNS_SERVER_PROTOCOL",
    75: "FACILITY_USERMODE_DNS_SERVER_SERVICED",
    76: "FACILITY_USERMODE_DNS_SERVER_SOCKETS",
    77: "FACILITY_USERMODE_DNS_SERVER_SERVER_ADMIN",
    78: "FACILITY_USERMODE_DNS_SERVER_SOAP",
    79: "FACILITY_USERMODE_DNS_SERVER_ISAPI",
    80: "FACILITY_USERMODE_DNS_SERVER_WEB",
    81: "FACILITY_USERMODE_DNS_SERVER_SERVER",
    82: "FACILITY_USERMODE_DNS_SERVER_ADMIN_R2",
    83: "FACILITY_USERMODE_DNS_SERVER_ISAPI_FILTER",
    84: "FACILITY_USERMODE_DNS_SERVER_NDNC2",
    85: "FACILITY_USERMODE_DNS_SERVER_EVENTLOG",
    86: "FACILITY_USERMODE_DNS_SERVER_ADMIN2",
    87: "FACILITY_USERMODE_DNS_SERVER_ZONE2",
    88: "FACILITY_USERMODE_DNS_SERVER_NDNC3",
    89: "FACILITY_USERMODE_DNS_SERVER_SOCKETS2",
    90: "FACILITY_USERMODE_DNS_SERVER_ADMIN3",
    91: "FACILITY_USERMODE_DNS_SERVER_WEB2",
    92: "FACILITY_USERMODE_DNS_SERVER_ADMIN4",
    93: "FACILITY_USERMODE_DNS_SERVER_SERVER3",
    94: "FACILITY_USERMODE_DNS_SERVER_SOCKETS3",
    95: "FACILITY_USERMODE_DNS_SERVER_ADMIN5",
    96: "FACILITY_USERMODE_DNS_SERVER_SERVER4",
    97: "FACILITY_USERMODE_DNS_SERVER_ADMIN6",
    98: "FACILITY_USERMODE_DNS_SERVER_SOCKETS4",
    99: "FACILITY_USERMODE_DNS_SERVER_WEB3",
}

def decode_hresult(hresult: HRESULT | int) -> str:
    if isinstance(hresult, HRESULT):
        hresult = hresult.value
    severity: int = (hresult >> 31) & 1
    facility: int = (hresult >> 16) & 0x1FFF
    code: int = hresult & 0xFFFF

    severity_str = "Success" if severity == 0 else "Failure"
    facility_str = FACILITY_CODES.get(facility, "Unknown Facility")

    return (
        f"HRESULT: 0x{hresult:08X}\n"
        f"Severity: {severity_str}\n"
        f"Facility: {facility_str} ({facility})\n"
        f"Code: 0x{code:04X} ({code})"
    )


def print_hresult(hresult: HRESULT | int) -> None:
    print(decode_hresult(hresult))