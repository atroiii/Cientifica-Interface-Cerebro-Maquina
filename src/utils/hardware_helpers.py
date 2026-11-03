import re

import serial.tools.list_ports

try:
    import winreg
except ImportError:  # fora do Windows não há registro
    winreg = None


_CHAVE_BT = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
_MAC_RE = re.compile(r"&([0-9A-F]{12})_")


def _mac_do_hwid(hwid: str):
    """Extrai o MAC (12 dígitos hex) do hwid de uma porta Bluetooth, ex.: '...&98D331F5A1B2_C...'."""
    m = _MAC_RE.search(hwid.upper())
    return m.group(1) if m else None


def _nome_bluetooth(mac: str):
    """Lê o nome do dispositivo pareado no registro do Windows. Retorna None se não achar."""
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"{_CHAVE_BT}\{mac.lower()}") as chave:
            valor, _ = winreg.QueryValueEx(chave, "Name")
    except OSError:
        return None
    if isinstance(valor, bytes):
        valor = valor.decode("utf-8", errors="replace")
    valor = str(valor).rstrip("\x00").strip()
    return valor or None


def _nome_da_porta(porta) -> str:
    hwid = (porta.hwid or "").upper()

    # 1. Portas Bluetooth (BrainLink, HC-05, ...)
    if "BTHENUM" in hwid:
        mac = _mac_do_hwid(hwid)
        if mac == "000000000000":
            return "Bluetooth (entrada, não usar)"
        if mac:
            return _nome_bluetooth(mac) or f"Bluetooth {mac}"
        return "Bluetooth"

    # 2. Arduinos oficiais (VID 2341)
    if "2341" in hwid:
        return "Arduino (Oficial)"

    # 3. Arduinos clones/genéricos (chips CH340, CP2102 ou FTDI)
    if "1A86" in hwid:
        return "Arduino (CH340)"
    if "10C4" in hwid:
        return "Arduino / CP2102"
    if "0403" in hwid:
        return "Módulo FTDI"

    # Fallback para outros dispositivos
    return porta.description or "Dispositivo Serial"


def listar_portas() -> list[tuple[str, str]]:
    """Retorna [(porta, nome), ...], ex.: [("COM5", "HC-05"), ("COM7", "BrainLink_Pro")]."""
    return [(p.device, _nome_da_porta(p)) for p in serial.tools.list_ports.comports()]
