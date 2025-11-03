"""
Cache manager untuk hasil transkripsi.
Menggunakan LRU cache in-memory untuk menghindari re-processing file yang sama.
"""
import hashlib
from functools import lru_cache
from typing import Optional
import os


class TranscriptionCache:
    """Cache untuk hasil transkripsi berdasarkan hash file."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = {}
        self._access_order = []
    
    def _compute_file_hash(self, file_path: str, chunk_size: int = 8192) -> Optional[str]:
        """
        Hitung SHA256 hash dari file untuk digunakan sebagai cache key.
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            print(f"Error computing file hash: {e}")
            return None
    
    def get(self, file_path: str, target_language: Optional[str] = None) -> Optional[dict]:
        """
        Ambil hasil transkripsi dari cache berdasarkan file hash dan target language.
        """
        file_hash = self._compute_file_hash(file_path)
        if not file_hash:
            return None
        
        cache_key = f"{file_hash}_{target_language or 'original'}"
        
        if cache_key in self._cache:
            # Update access order (LRU)
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)
            
            print(f"✅ Cache HIT for {os.path.basename(file_path)} (lang: {target_language or 'original'})")
            return self._cache[cache_key]
        
        print(f"❌ Cache MISS for {os.path.basename(file_path)} (lang: {target_language or 'original'})")
        return None
    
    def set(self, file_path: str, result: dict, target_language: Optional[str] = None):
        """
        Simpan hasil transkripsi ke cache.
        """
        file_hash = self._compute_file_hash(file_path)
        if not file_hash:
            return
        
        cache_key = f"{file_hash}_{target_language or 'original'}"
        
        # Evict LRU item jika sudah penuh
        if len(self._cache) >= self.max_size and cache_key not in self._cache:
            if self._access_order:
                lru_key = self._access_order.pop(0)
                if lru_key in self._cache:
                    del self._cache[lru_key]
                    print(f"♻️  Evicted LRU cache entry: {lru_key}")
        
        self._cache[cache_key] = result
        
        # Update access order
        if cache_key in self._access_order:
            self._access_order.remove(cache_key)
        self._access_order.append(cache_key)
        
        print(f"💾 Cached result for {os.path.basename(file_path)} (lang: {target_language or 'original'})")
    
    def clear(self):
        """
        Hapus semua cache (untuk testing/maintenance).
        """
        self._cache.clear()
        self._access_order.clear()
        print("🗑️  Cache cleared")
    
    def size(self) -> int:
        """
        Return jumlah item di cache.
        """
        return len(self._cache)


# Singleton instance
transcription_cache = TranscriptionCache(max_size=100)
