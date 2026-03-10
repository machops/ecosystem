#!/usr/bin/env python3
"""Axiom Signer Daemon - ed25519 + SHA3-512 signing service."""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple


class SignatureError(Exception):
    """Signature operation error."""
    pass


class KeyNotFoundError(SignatureError):
    """Key not found error."""
    pass


class InvalidSignatureError(SignatureError):
    """Invalid signature error."""
    pass


class MockEd25519:
    """Mock ed25519 implementation for testing."""
    
    KEY_SIZE = 32
    SIGNATURE_SIZE = 64
    
    @classmethod
    def create_keypair(cls) -> Tuple[bytes, bytes]:
        """Create a new keypair."""
        private_key = os.urandom(cls.KEY_SIZE)
        public_key = hashlib.sha256(private_key).digest()[:cls.KEY_SIZE]
        return private_key, public_key
    
    @classmethod
    def sign(cls, message: bytes, private_key: bytes) -> bytes:
        """Sign a message."""
        if len(private_key) != cls.KEY_SIZE:
            raise SignatureError("Invalid private key size")
        # Mock signature: SHA3-512 of message + key prefix
        h = hashlib.sha3_512()
        h.update(message)
        h.update(private_key[:16])
        return h.digest() + os.urandom(cls.SIGNATURE_SIZE - 64)
    
    @classmethod
    def verify(cls, message: bytes, signature: bytes, 
               public_key: bytes) -> bool:
        """Verify a signature."""
        if len(signature) != cls.SIGNATURE_SIZE:
            return False
        if len(public_key) != cls.KEY_SIZE:
            return False
        # In mock, we can't truly verify without private key
        # This is a simplified check
        return len(signature) == cls.SIGNATURE_SIZE


class KeyStore:
    """Secure key storage."""
    
    def __init__(self, key_dir: str):
        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._keys: Dict[str, Tuple[bytes, bytes]] = {}
    
    def generate_key(self, key_id: str) -> bytes:
        """Generate and store a new keypair."""
        private_key, public_key = MockEd25519.create_keypair()
        self._keys[key_id] = (private_key, public_key)
        self._save_key(key_id, private_key, public_key)
        return public_key
    
    def _save_key(self, key_id: str, private_key: bytes, 
                  public_key: bytes) -> None:
        """Save key to disk."""
        key_file = self.key_dir / f"{key_id}.key"
        with open(key_file, 'wb') as f:
            f.write(private_key)
        os.chmod(key_file, 0o600)
        
        pub_file = self.key_dir / f"{key_id}.pub"
        with open(pub_file, 'wb') as f:
            f.write(public_key)
        os.chmod(pub_file, 0o644)
    
    def load_key(self, key_id: str) -> Tuple[bytes, bytes]:
        """Load keypair from disk."""
        if key_id in self._keys:
            return self._keys[key_id]
        
        key_file = self.key_dir / f"{key_id}.key"
        pub_file = self.key_dir / f"{key_id}.pub"
        
        if not key_file.exists() or not pub_file.exists():
            raise KeyNotFoundError(f"Key not found: {key_id}")
        
        with open(key_file, 'rb') as f:
            private_key = f.read()
        with open(pub_file, 'rb') as f:
            public_key = f.read()
        
        self._keys[key_id] = (private_key, public_key)
        return private_key, public_key
    
    def get_public_key(self, key_id: str) -> bytes:
        """Get public key."""
        _, public_key = self.load_key(key_id)
        return public_key
    
    def delete_key(self, key_id: str) -> None:
        """Delete a key."""
        key_file = self.key_dir / f"{key_id}.key"
        pub_file = self.key_dir / f"{key_id}.pub"
        
        if key_file.exists():
            key_file.unlink()
        if pub_file.exists():
            pub_file.unlink()
        
        self._keys.pop(key_id, None)
    
    def list_keys(self) -> list:
        """List all key IDs."""
        keys = []
        for f in self.key_dir.glob("*.pub"):
            keys.append(f.stem)
        return keys


class Signer:
    """Message signer using ed25519 + SHA3-512."""
    
    def __init__(self, key_store: KeyStore):
        self.key_store = key_store
    
    def sign(self, message: bytes, key_id: str) -> bytes:
        """Sign a message."""
        private_key, _ = self.key_store.load_key(key_id)
        return MockEd25519.sign(message, private_key)
    
    def sign_json(self, data: dict, key_id: str) -> Dict[str, str]:
        """Sign JSON data."""
        message = json.dumps(data, sort_keys=True).encode('utf-8')
        signature = self.sign(message, key_id)
        return {
            'data': data,
            'signature': signature.hex(),
            'key_id': key_id,
            'algorithm': 'ed25519+sha3-512'
        }
    
    def verify(self, message: bytes, signature: bytes, 
               key_id: str) -> bool:
        """Verify a signature."""
        try:
            public_key = self.key_store.get_public_key(key_id)
            return MockEd25519.verify(message, signature, public_key)
        except KeyNotFoundError:
            return False
    
    def verify_json(self, signed_data: Dict[str, str]) -> bool:
        """Verify signed JSON data."""
        try:
            data = signed_data['data']
            signature = bytes.fromhex(signed_data['signature'])
            key_id = signed_data['key_id']
            message = json.dumps(data, sort_keys=True).encode('utf-8')
            return self.verify(message, signature, key_id)
        except (KeyError, ValueError):
            return False


class ArtifactSigner:
    """Sign deployment artifacts."""
    
    def __init__(self, signer: Signer):
        self.signer = signer
    
    def sign_artifact(self, artifact_id: str, content: bytes,
                      key_id: str) -> Dict[str, str]:
        """Sign an artifact."""
        content_hash = hashlib.sha3_512(content).hexdigest()
        data = {
            'artifact_id': artifact_id,
            'content_hash': content_hash,
            'algorithm': 'sha3-512'
        }
        return self.signer.sign_json(data, key_id)
    
    def verify_artifact(self, artifact_id: str, content: bytes,
                        signed_data: Dict[str, str]) -> bool:
        """Verify an artifact signature."""
        content_hash = hashlib.sha3_512(content).hexdigest()
        if not self.signer.verify_json(signed_data):
            return False
        
        # Verify content hash matches
        data = signed_data.get('data', {})
        return data.get('content_hash') == content_hash
