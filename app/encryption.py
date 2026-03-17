"""
encryption.py
-------------
AES-256 file encryption/decryption using the cryptography library.
Each file gets a unique random salt + IV derived from the master SECRET_KEY.

Encrypt: plaintext bytes → encrypted bytes written to disk
Decrypt: encrypted bytes from disk → plaintext bytes streamed to client
"""

import os
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

MASTER_KEY = os.getenv("SECRET_KEY", "changeme").encode()
CHUNK_SIZE = 64 * 1024  # 64KB chunks


def _derive_key(salt: bytes) -> bytes:
    """Derive a 32-byte AES key from the master key + salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return kdf.derive(MASTER_KEY)


def encrypt_file(plaintext: bytes) -> bytes:
    """
    Encrypt file bytes with AES-256-CBC.
    Output format: [16 salt][16 IV][encrypted data]
    """
    salt = os.urandom(16)
    iv   = os.urandom(16)
    key  = _derive_key(salt)

    # Pad to AES block size (16 bytes)
    pad_len = 16 - (len(plaintext) % 16)
    plaintext += bytes([pad_len] * pad_len)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(plaintext) + encryptor.finalize()

    return salt + iv + encrypted


def decrypt_file(ciphertext: bytes) -> bytes:
    """
    Decrypt file bytes encrypted by encrypt_file().
    Reads salt and IV from the first 32 bytes.
    """
    salt      = ciphertext[:16]
    iv        = ciphertext[16:32]
    encrypted = ciphertext[32:]
    key       = _derive_key(salt)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(encrypted) + decryptor.finalize()

    # Remove padding
    pad_len = plaintext[-1]
    return plaintext[:-pad_len]
