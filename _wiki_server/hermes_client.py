#!/usr/bin/env python3
"""Hermes Portal – Abstraktion über lokale vs. SSH-Verbindung zum Hermes-Agenten.

Das Portal soll wahlweise IN derselben VM/Container laufen wie der Hermes-Agent (Mode
``local``) ODER über das Netzwerk auf einen entfernten Agent zugreifen (Mode ``ssh``).
Alle Dateioperationen und CLI-Aufrufe gehen durch diese Schicht, sodass der restliche
Code beide Modi gleich behandelt.

SSH-Mode ist optional und nur aktiv, wenn ``paramiko`` installiert ist. Andernfalls
fällt das Portal auf den lokalen Modus zurück und protokolliert eine Warnung.
"""
from __future__ import annotations

import os
import shlex
import subprocess
import time
import fnmatch
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Iterable, Iterator, List, Optional, Tuple

try:
    import paramiko  # type: ignore
    HAS_PARAMIKO = True
except Exception:  # pragma: no cover - optional dependency
    paramiko = None  # type: ignore
    HAS_PARAMIKO = False

from config import AppConfig, get_config


@dataclass
class CmdResult:
    """Vereinheitlichtes Ergebnis eines Befehls (lokal oder remote)."""
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class DirEntry:
    name: str
    is_dir: bool
    size: int
    modified: float  # unix timestamp


@dataclass
class FileStat:
    exists: bool
    is_dir: bool
    size: int
    modified: float


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------


class _LocalBackend:
    """Direkter Zugriff aufs lokale Dateisystem + ``subprocess``."""

    def read_text(self, path: str) -> Optional[str]:
        try:
            return Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    def write_text(self, path: str, content: str) -> bool:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return True
        except OSError:
            return False

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_dir(self, path: str) -> bool:
        return Path(path).is_dir()

    def list_dir(self, path: str) -> List[DirEntry]:
        p = Path(path)
        if not p.is_dir():
            return []
        out: List[DirEntry] = []
        for child in sorted(p.iterdir(), key=lambda c: c.name.lower()):
            try:
                st = child.stat()
                out.append(DirEntry(
                    name=child.name,
                    is_dir=child.is_dir(),
                    size=0 if child.is_dir() else st.st_size,
                    modified=st.st_mtime,
                ))
            except OSError:
                continue
        return out

    def mkdir(self, path: str) -> bool:
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except OSError:
            return False

    def remove(self, path: str) -> bool:
        try:
            p = Path(path)
            if p.is_dir():
                # rekursiv, aber bewusst restriktiv – nur leere Ordner
                for child in p.iterdir():
                    if child.is_dir():
                        return False
                    child.unlink()
                p.rmdir()
            else:
                p.unlink()
            return True
        except OSError:
            return False

    def run(self, argv: List[str], *, timeout: int = 120, cwd: Optional[str] = None,
            env: Optional[dict] = None) -> CmdResult:
        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env or {**os.environ},
            )
            return CmdResult(result.returncode, result.stdout or "", result.stderr or "")
        except subprocess.TimeoutExpired as ex:
            return CmdResult(-1, "", f"Timeout nach {ex.timeout}s")
        except FileNotFoundError as ex:
            return CmdResult(127, "", f"Befehl nicht gefunden: {ex}")
        except Exception as ex:  # pragma: no cover
            return CmdResult(-1, "", f"Fehler: {ex}")

    def statvfs(self, path: str) -> Optional[Tuple[int, int]]:
        try:
            s = os.statvfs(path)
            return s.f_blocks * s.f_frsize, s.f_bavail * s.f_frsize
        except OSError:
            return None

    def mtime(self, path: str) -> Optional[float]:
        try:
            return Path(path).stat().st_mtime
        except OSError:
            return None

    def stat(self, path: str) -> Optional["FileStat"]:
        try:
            st = Path(path).stat()
            return FileStat(
                exists=True,
                is_dir=Path(path).is_dir(),
                size=st.st_size,
                modified=st.st_mtime,
            )
        except OSError:
            return None

    def read_bytes(self, path: str) -> Optional[bytes]:
        try:
            return Path(path).read_bytes()
        except OSError:
            return None

    def write_bytes(self, path: str, data: bytes) -> bool:
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return True
        except OSError:
            return False

    def glob(self, dir_path: str, pattern: str) -> List[str]:
        """Liste der Dateinamen (ohne Pfad) im Verzeichnis, die zum Glob-Pattern passen."""
        try:
            return sorted(p.name for p in Path(dir_path).glob(pattern) if p.is_file())
        except OSError:
            return []

    def walk(self, path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
        """Wie ``os.walk``. Lokale Variante delegiert direkt."""
        try:
            yield from os.walk(path)
        except OSError:
            return

    def rmtree(self, path: str) -> bool:
        try:
            p = Path(path)
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
            return True
        except OSError:
            return False

    def tail(self, path: str, n: int = 200) -> List[str]:
        """Liest die letzten n Zeilen einer Datei (effizient via seek)."""
        try:
            p = Path(path)
            size = p.stat().st_size
            if size == 0:
                return []
            block = min(size, max(64 * 1024, n * 300))
            with open(p, "rb") as f:
                if size > block:
                    # Nur Block-Ende lesen
                    f.seek(-block, 2)
                # else: Datei ist kleiner als block → von Anfang lesen
                data = f.read()
            return data.decode("utf-8", errors="replace").splitlines()[-n:]
        except OSError:
            return []


class _SSHBackend:
    """Über ``paramiko`` ausgeführter Remote-Zugriff."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self._client: Optional["paramiko.SSHClient"] = None
        self._sftp: Optional["paramiko.SFTPClient"] = None
        self._lock = RLock()
        self._last_connect_error: str = ""

    # --- Verbindung ----------------------------------------------------
    def _ensure_connected(self) -> bool:
        if not HAS_PARAMIKO:
            self._last_connect_error = "paramiko ist nicht installiert"
            return False
        with self._lock:
            if self._client is not None:
                transport = self._client.get_transport()
                if transport and transport.is_active():
                    return True
                self._client = None
                self._sftp = None
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                kwargs = {
                    "hostname": self.cfg.agent_host,
                    "port": self.cfg.ssh_port,
                    "username": self.cfg.ssh_user,
                    "timeout": 8,
                    "allow_agent": True,
                    "look_for_keys": True,
                }
                key_path = self.cfg.ssh_key_path
                if key_path and Path(key_path).exists():
                    kwargs["key_filename"] = key_path
                if self.cfg.ssh_password:
                    kwargs["password"] = self.cfg.ssh_password
                client.connect(**kwargs)
                self._client = client
                self._sftp = client.open_sftp()
                self._last_connect_error = ""
                return True
            except Exception as ex:  # pragma: no cover - network
                self._last_connect_error = str(ex)
                self._client = None
                self._sftp = None
                return False

    def last_error(self) -> str:
        return self._last_connect_error

    def close(self) -> None:
        """Schließt SFTP- und SSH-Channel sauber. Idempotent."""
        with self._lock:
            try:
                if self._sftp is not None:
                    self._sftp.close()
            except Exception:
                pass
            self._sftp = None
            try:
                if self._client is not None:
                    self._client.close()
            except Exception:
                pass
            self._client = None

    # --- Dateioperationen ---------------------------------------------
    # Wichtig: paramiko.SFTPClient ist NICHT thread-safe (eine einzige Channel-
    # Session pro SFTP-Instanz). Bei Flask mit ``threaded=True`` feuern Browser
    # parallele XHRs ab; ohne Lock kommt es zu Deadlocks auf dem SFTP-Channel.
    # Wir serialisieren daher jeden Aufruf via ``self._lock`` (RLock, also
    # reentrant für rekursive Operationen wie ``walk``).
    def read_text(self, path: str) -> Optional[str]:
        if not self._ensure_connected() or self._sftp is None:
            return None
        with self._lock:
            try:
                with self._sftp.open(path, "r") as f:
                    data = f.read()
                if isinstance(data, bytes):
                    return data.decode("utf-8", errors="replace")
                return str(data)
            except Exception:
                return None

    def write_text(self, path: str, content: str) -> bool:
        if not self._ensure_connected() or self._sftp is None:
            return False
        with self._lock:
            try:
                # Parent-Pfad ggf. anlegen
                parent = "/".join(path.rstrip("/").split("/")[:-1])
                if parent:
                    self._mkdir_p_unlocked(parent)
                with self._sftp.open(path, "w") as f:
                    f.write(content)
                return True
            except Exception:
                return False

    def _mkdir_p_unlocked(self, path: str) -> None:
        """Caller muss ``self._lock`` halten."""
        assert self._sftp is not None
        parts = path.strip("/").split("/")
        cur = ""
        for part in parts:
            cur = f"{cur}/{part}" if cur else f"/{part}"
            try:
                self._sftp.stat(cur)
            except IOError:
                try:
                    self._sftp.mkdir(cur)
                except Exception:
                    pass

    def exists(self, path: str) -> bool:
        if not self._ensure_connected() or self._sftp is None:
            return False
        with self._lock:
            try:
                self._sftp.stat(path)
                return True
            except Exception:
                return False

    def is_dir(self, path: str) -> bool:
        if not self._ensure_connected() or self._sftp is None:
            return False
        with self._lock:
            try:
                import stat as _stat
                attr = self._sftp.stat(path)
                return bool(attr.st_mode and _stat.S_ISDIR(attr.st_mode))
            except Exception:
                return False

    def list_dir(self, path: str) -> List[DirEntry]:
        if not self._ensure_connected() or self._sftp is None:
            return []
        with self._lock:
            try:
                import stat as _stat
                out: List[DirEntry] = []
                for attr in self._sftp.listdir_attr(path):
                    is_dir = bool(attr.st_mode and _stat.S_ISDIR(attr.st_mode))
                    out.append(DirEntry(
                        name=attr.filename,
                        is_dir=is_dir,
                        size=0 if is_dir else int(attr.st_size or 0),
                        modified=float(attr.st_mtime or 0),
                    ))
                out.sort(key=lambda e: e.name.lower())
                return out
            except Exception:
                return []

    def mkdir(self, path: str) -> bool:
        if not self._ensure_connected() or self._sftp is None:
            return False
        with self._lock:
            try:
                self._mkdir_p_unlocked(path)
                return True
            except Exception:
                return False

    def remove(self, path: str) -> bool:
        if not self._ensure_connected() or self._sftp is None:
            return False
        with self._lock:
            try:
                self._sftp.remove(path)
                return True
            except Exception:
                try:
                    self._sftp.rmdir(path)
                    return True
                except Exception:
                    return False

    # --- Befehlsausführung --------------------------------------------
    def run(self, argv: List[str], *, timeout: int = 120, cwd: Optional[str] = None,
            env: Optional[dict] = None) -> CmdResult:
        if not self._ensure_connected() or self._client is None:
            return CmdResult(-1, "", f"SSH nicht verbunden: {self._last_connect_error}")
        cmd = " ".join(shlex.quote(a) for a in argv)
        if cwd:
            cmd = f"cd {shlex.quote(cwd)} && {cmd}"
        with self._lock:
            try:
                transport = self._client.get_transport()
                assert transport is not None
                chan = transport.open_session()
                chan.settimeout(timeout)
                if env:
                    # Nur einfache String-Envs senden
                    for k, v in env.items():
                        try:
                            chan.update_environment({k: str(v)})  # type: ignore[attr-defined]
                        except Exception:
                            pass
                chan.exec_command(cmd)
                start = time.time()
                stdout = b""
                stderr = b""
                while True:
                    if chan.recv_ready():
                        stdout += chan.recv(65536)
                    if chan.recv_stderr_ready():
                        stderr += chan.recv_stderr(65536)
                    if chan.exit_status_ready():
                        # Reste lesen
                        while chan.recv_ready():
                            stdout += chan.recv(65536)
                        while chan.recv_stderr_ready():
                            stderr += chan.recv_stderr(65536)
                        rc = chan.recv_exit_status()
                        return CmdResult(rc,
                                         stdout.decode("utf-8", errors="replace"),
                                         stderr.decode("utf-8", errors="replace"))
                    if time.time() - start > timeout:
                        chan.close()
                        return CmdResult(-1, stdout.decode("utf-8", errors="replace"),
                                         stderr.decode("utf-8", errors="replace") + f"\nTimeout nach {timeout}s")
                    time.sleep(0.05)
            except Exception as ex:
                return CmdResult(-1, "", f"SSH-Fehler: {ex}")

    def statvfs(self, path: str) -> Optional[Tuple[int, int]]:
        # Über df ausführen
        result = self.run(["df", "-Pk", path], timeout=10)
        if not result.ok:
            return None
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    total_kb = int(parts[1])
                    avail_kb = int(parts[3])
                    return total_kb * 1024, avail_kb * 1024
                except ValueError:
                    pass
        return None

    def mtime(self, path: str) -> Optional[float]:
        if not self._ensure_connected() or self._sftp is None:
            return None
        with self._lock:
            try:
                attr = self._sftp.stat(path)
                return float(attr.st_mtime) if attr.st_mtime is not None else None
            except Exception:
                return None

    def stat(self, path: str) -> Optional["FileStat"]:
        if not self._ensure_connected() or self._sftp is None:
            return None
        with self._lock:
            try:
                import stat as _stat
                attr = self._sftp.stat(path)
                return FileStat(
                    exists=True,
                    is_dir=bool(attr.st_mode and _stat.S_ISDIR(attr.st_mode)),
                    size=int(attr.st_size or 0),
                    modified=float(attr.st_mtime or 0),
                )
            except Exception:
                return None

    def read_bytes(self, path: str) -> Optional[bytes]:
        if not self._ensure_connected() or self._sftp is None:
            return None
        with self._lock:
            try:
                with self._sftp.open(path, "rb") as f:
                    return f.read()
            except Exception:
                return None

    def write_bytes(self, path: str, data: bytes) -> bool:
        if not self._ensure_connected() or self._sftp is None:
            return False
        with self._lock:
            try:
                parent = "/".join(path.rstrip("/").split("/")[:-1])
                if parent:
                    self._mkdir_p_unlocked(parent)
                with self._sftp.open(path, "wb") as f:
                    f.write(data)
                return True
            except Exception:
                return False

    def glob(self, dir_path: str, pattern: str) -> List[str]:
        """Ein-Ebenen Glob – filtert die ``list_dir``-Ausgabe nach Pattern.
        Lock kommt von list_dir (RLock erlaubt Reentry)."""
        entries = self.list_dir(dir_path)
        return sorted(e.name for e in entries if not e.is_dir and fnmatch.fnmatch(e.name, pattern))

    def walk(self, path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
        """Rekursiv über SFTP. Jeder Schritt kostet einen SFTP-Round-Trip."""
        try:
            entries = self.list_dir(path)
        except Exception:
            return
        dirs, files = [], []
        for e in entries:
            (dirs if e.is_dir else files).append(e.name)
        yield path, dirs, files
        for d in dirs:
            sub = f"{path.rstrip('/')}/{d}"
            yield from self.walk(sub)

    def rmtree(self, path: str) -> bool:
        """Rekursives Löschen via ``rm -rf`` über SSH (schneller als viele SFTP-Calls)."""
        if not path or path in ("/", ""):
            return False
        result = self.run(["rm", "-rf", "--", path], timeout=30)
        return result.ok

    def tail(self, path: str, n: int = 200) -> List[str]:
        """Remote-effizient via `tail -n` – kein Streamen der ganzen Datei."""
        result = self.run(["tail", "-n", str(n), path], timeout=15)
        if not result.ok:
            return []
        return result.stdout.splitlines()


# ---------------------------------------------------------------------------
# Public Facade
# ---------------------------------------------------------------------------


class HermesClient:
    """Top-Level Facade – wählt automatisch local oder ssh."""

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        self._local = _LocalBackend()
        self._ssh: Optional[_SSHBackend] = None
        # Cache für VM-Zeit-Offset (VM-naive wall clock minus lokale wall clock,
        # in Sekunden). Wird per `time_offset_seconds()` lazy ermittelt.
        self._time_offset: Optional[float] = None
        self._time_offset_at: float = 0.0
        if cfg.connection_mode == "ssh":
            if HAS_PARAMIKO:
                self._ssh = _SSHBackend(cfg)
            else:
                # Silentes Fallback. Wird in /api/status sichtbar gemacht.
                pass

    # --- Mode-Helfer ---------------------------------------------------
    @property
    def mode(self) -> str:
        return "ssh" if self._ssh is not None else "local"

    def status(self) -> dict:
        info = {"mode": self.mode, "paramiko": HAS_PARAMIKO}
        if self._ssh is not None:
            connected = self._ssh._ensure_connected()
            info["connected"] = connected
            info["host"] = self.cfg.agent_host
            if not connected:
                info["error"] = self._ssh.last_error() or "unbekannt"
        else:
            info["connected"] = True  # local ist immer verfügbar
        return info

    def _backend(self):
        return self._ssh if self._ssh is not None else self._local

    def close(self) -> None:
        """Räumt evtl. offene SSH-Verbindung auf."""
        if self._ssh is not None:
            self._ssh.close()

    # --- Delegations ---------------------------------------------------
    def read_text(self, path: str) -> Optional[str]:                    return self._backend().read_text(path)
    def write_text(self, path: str, content: str) -> bool:              return self._backend().write_text(path, content)
    def exists(self, path: str) -> bool:                                return self._backend().exists(path)
    def is_dir(self, path: str) -> bool:                                return self._backend().is_dir(path)
    def list_dir(self, path: str) -> List[DirEntry]:                    return self._backend().list_dir(path)
    def mkdir(self, path: str) -> bool:                                 return self._backend().mkdir(path)
    def remove(self, path: str) -> bool:                                return self._backend().remove(path)
    def statvfs(self, path: str) -> Optional[Tuple[int, int]]:          return self._backend().statvfs(path)
    def mtime(self, path: str) -> Optional[float]:                      return self._backend().mtime(path)
    def stat(self, path: str) -> Optional[FileStat]:                    return self._backend().stat(path)
    def tail(self, path: str, n: int = 200) -> List[str]:               return self._backend().tail(path, n)
    def read_bytes(self, path: str) -> Optional[bytes]:                 return self._backend().read_bytes(path)
    def write_bytes(self, path: str, data: bytes) -> bool:              return self._backend().write_bytes(path, data)
    def glob(self, dir_path: str, pattern: str) -> List[str]:           return self._backend().glob(dir_path, pattern)
    def walk(self, path: str) -> Iterator[Tuple[str, List[str], List[str]]]:
        return self._backend().walk(path)
    def rmtree(self, path: str) -> bool:                                return self._backend().rmtree(path)

    def run(self, argv: List[str], *, timeout: int = 120, cwd: Optional[str] = None,
            env: Optional[dict] = None) -> CmdResult:
        return self._backend().run(argv, timeout=timeout, cwd=cwd, env=env)

    # --- JSON-Convenience ---------------------------------------------
    def read_json(self, path: str, default: Any = None) -> Any:
        """Liest JSON. Bei Fehler wird ``default`` zurückgegeben."""
        raw = self.read_text(path)
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return default

    def write_json(self, path: str, data: Any, *, indent: int = 2) -> bool:
        return self.write_text(path, json.dumps(data, indent=indent, ensure_ascii=False))

    # --- Hermes-spezifische Convenience -------------------------------
    def hermes(self, args: Iterable[str], *, timeout: int = 120) -> CmdResult:
        """Ruft ``hermes <args>`` auf dem Agent-Host auf."""
        return self.run([self.cfg.hermes_bin, *list(args)], timeout=timeout)

    # --- Zeit-Offset (VM-Wall-Clock minus lokale Wall-Clock) ----------
    def time_offset_seconds(self, cache_ttl: int = 60) -> float:
        """Differenz zwischen ``datetime.now()`` der VM und der lokalen Maschine.

        Wichtig im SSH-Mode, wenn die VM (z.B. in UTC) andere Wall-Clock-Zeit
        hat als das Portal-Host (z.B. CEST). Vergleiche zwischen naiven
        Timestamps aus jobs.json/Logs und ``datetime.now()`` auf dem Portal
        sind sonst um den TZ-Offset verschoben.

        Liefert ``0.0`` im local-Mode. Bei Fehler ebenfalls ``0`` (graceful).
        Wert wird ``cache_ttl`` Sekunden lang gecached.
        """
        import time as _time
        if self.mode != "ssh":
            return 0.0
        now = _time.time()
        if self._time_offset is not None and (now - self._time_offset_at) < cache_ttl:
            return self._time_offset
        result = self.run(["date", "+%Y-%m-%dT%H:%M:%S"], timeout=5)
        offset = 0.0
        try:
            from datetime import datetime as _dt
            vm_naive = _dt.fromisoformat(result.stdout.strip())
            mac_naive = _dt.now()
            offset = (vm_naive - mac_naive).total_seconds()
        except Exception:
            offset = 0.0
        self._time_offset = offset
        self._time_offset_at = now
        return offset

    def first_existing(self, paths: Iterable[str]) -> Optional[str]:
        """Erstes ``path`` aus der Liste, das existiert (für Log-Kandidaten)."""
        for p in paths:
            if p and self.exists(p):
                return p
        return None


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_CLIENT: Optional[HermesClient] = None
_CLIENT_LOCK = RLock()


def get_client() -> HermesClient:
    global _CLIENT
    with _CLIENT_LOCK:
        if _CLIENT is None:
            _CLIENT = HermesClient(get_config())
        return _CLIENT


def reset_client() -> HermesClient:
    """Re-instanziiert den Client – nach Settings-Änderungen aufrufen.

    Schließt eine vorhandene SSH-Verbindung sauber, bevor ein neuer Client
    aufgebaut wird, damit keine verwaisten paramiko-Channels zurückbleiben.
    """
    global _CLIENT
    with _CLIENT_LOCK:
        old = _CLIENT
        if old is not None:
            try:
                old.close()
            except Exception:
                pass
        _CLIENT = HermesClient(get_config())
        return _CLIENT
