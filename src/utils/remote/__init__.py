"""
Módulo para clientes de protocolos remotos.

Este módulo contém implementações de clientes para diversos protocolos
de acesso a arquivos remotos: SSHFS, SMB, NFS, Mounted e UNC.
"""

from .remote_protocol import RemoteProtocol
from .sshfs_client import SSHFSClient
from .smb_client import SMBClient
from .nfs_client import NFSClient
from .mounted_client import MountedClient
from .unc_client import UNCClient

__all__ = [
    'RemoteProtocol',
    'SSHFSClient',
    'SMBClient',
    'NFSClient',
    'MountedClient',
    'UNCClient'
]
