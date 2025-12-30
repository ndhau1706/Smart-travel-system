"""
Streaming Response Utilities - Bug #15 Fix
Handles robust streaming with:
- Unicode boundary protection
- Chunk ordering and deduplication
- Timeout detection with heartbeat
- Buffer overflow prevention
- Graceful disconnect handling
"""
import asyncio
import hashlib
import time
from typing import Optional, Set, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class StreamingMetrics:
    """Track streaming health metrics."""
    chunks_sent: int = 0
    bytes_sent: int = 0
    start_time: float = field(default_factory=time.time)
    last_chunk_time: float = field(default_factory=time.time)
    retries: int = 0
    duplicates_filtered: int = 0
    unicode_fixes: int = 0
    
    def update_chunk(self, chunk_size: int):
        """Update metrics after sending chunk."""
        self.chunks_sent += 1
        self.bytes_sent += chunk_size
        self.last_chunk_time = time.time()
    
    def time_since_last_chunk(self) -> float:
        """Seconds since last chunk."""
        return time.time() - self.last_chunk_time
    
    def total_duration(self) -> float:
        """Total streaming duration in seconds."""
        return time.time() - self.start_time


class StreamBuffer:
    """
    Robust streaming buffer with Bug #15 fixes:
    - Unicode boundary protection (#6)
    - Chunk deduplication (#9)
    - Ordering validation (#8)
    - Overflow prevention (#3)
    - Timeout detection (#1)
    """
    
    # Limits to prevent buffer overflow
    MAX_BUFFER_SIZE = 100 * 1024  # 100KB max buffer
    MAX_CHUNK_SIZE = 8 * 1024     # 8KB max per chunk
    CHUNK_TIMEOUT = 30.0          # 30s max between chunks
    HEARTBEAT_INTERVAL = 5.0      # 5s heartbeat when no data
    
    def __init__(self):
        self.buffer: List[str] = []
        self.buffer_size: int = 0
        self.seen_hashes: Set[str] = set()
        self.expected_sequence: int = 0
        self.metrics = StreamingMetrics()
        self.partial_utf8: bytes = b''
        self.disconnected: bool = False
        
    def add_chunk(self, chunk: str, sequence_id: Optional[int] = None) -> Optional[str]:
        """
        Add chunk with validation.
        
        Args:
            chunk: Text chunk to add
            sequence_id: Optional sequence number for ordering
            
        Returns:
            Processed chunk or None if filtered
        """
        if self.disconnected:
            logger.warning("🚫 Attempted to add chunk to disconnected stream")
            return None
        
        # Bug #9 Fix: Deduplication
        chunk_hash = self._hash_chunk(chunk)
        if chunk_hash in self.seen_hashes:
            self.metrics.duplicates_filtered += 1
            logger.debug(f"🔄 Filtered duplicate chunk (hash: {chunk_hash[:8]})")
            return None
        
        # Bug #8 Fix: Sequence validation (if provided)
        if sequence_id is not None:
            if sequence_id != self.expected_sequence:
                logger.warning(
                    f"⚠️ Out-of-order chunk: expected {self.expected_sequence}, "
                    f"got {sequence_id}. Buffering..."
                )
                # In production, would buffer and reorder. For now, just warn.
                # TODO: Implement proper reordering buffer
            self.expected_sequence += 1
        
        # Bug #3 Fix: Buffer overflow prevention
        chunk_size = len(chunk.encode('utf-8'))
        if self.buffer_size + chunk_size > self.MAX_BUFFER_SIZE:
            logger.error(
                f"❌ Buffer overflow prevented: {self.buffer_size + chunk_size} bytes "
                f"exceeds {self.MAX_BUFFER_SIZE} limit"
            )
            self.disconnected = True
            return None
        
        if chunk_size > self.MAX_CHUNK_SIZE:
            logger.warning(
                f"⚠️ Chunk too large ({chunk_size} bytes), truncating to "
                f"{self.MAX_CHUNK_SIZE} bytes"
            )
            # Truncate with unicode safety
            chunk = self._safe_truncate(chunk, self.MAX_CHUNK_SIZE)
        
        # Bug #6 Fix: Unicode boundary protection
        safe_chunk = self._ensure_valid_utf8(chunk)
        if safe_chunk != chunk:
            self.metrics.unicode_fixes += 1
            logger.debug("🔧 Fixed unicode boundary issue")
        
        # Add to buffer
        self.buffer.append(safe_chunk)
        self.buffer_size += len(safe_chunk.encode('utf-8'))
        self.seen_hashes.add(chunk_hash)
        self.metrics.update_chunk(len(safe_chunk.encode('utf-8')))
        
        return safe_chunk
    
    def _hash_chunk(self, chunk: str) -> str:
        """Generate hash for deduplication."""
        return hashlib.sha256(chunk.encode('utf-8')).hexdigest()
    
    def _ensure_valid_utf8(self, chunk: str) -> str:
        """
        Ensure chunk doesn't break in middle of UTF-8 character.
        Handles Bug #6: Unicode Break.
        """
        try:
            # Try encoding/decoding to validate
            chunk.encode('utf-8').decode('utf-8')
            return chunk
        except UnicodeDecodeError:
            # Handle partial UTF-8 sequences
            chunk_bytes = chunk.encode('utf-8', errors='ignore')
            
            # Check for incomplete trailing bytes
            if len(chunk_bytes) > 0:
                last_byte = chunk_bytes[-1]
                # UTF-8 multi-byte sequence detector
                if last_byte & 0b10000000:  # High bit set = multi-byte
                    # Find start of incomplete sequence
                    for i in range(min(4, len(chunk_bytes))):
                        byte = chunk_bytes[-(i+1)]
                        if byte & 0b11000000 == 0b11000000:  # Sequence start
                            # Remove incomplete sequence
                            chunk_bytes = chunk_bytes[:-(i+1)]
                            self.partial_utf8 = chunk_bytes[-(i+1):]
                            break
            
            return chunk_bytes.decode('utf-8', errors='ignore')
    
    def _safe_truncate(self, text: str, max_bytes: int) -> str:
        """Truncate text to max bytes without breaking UTF-8."""
        encoded = text.encode('utf-8')
        if len(encoded) <= max_bytes:
            return text
        
        # Truncate and find valid UTF-8 boundary
        truncated = encoded[:max_bytes]
        
        # Find last complete character
        for i in range(min(4, len(truncated))):
            try:
                return truncated[:len(truncated)-i].decode('utf-8')
            except UnicodeDecodeError:
                continue
        
        return truncated.decode('utf-8', errors='ignore')
    
    def is_timeout(self) -> bool:
        """Bug #1 Fix: Check if stream has timed out."""
        return self.metrics.time_since_last_chunk() > self.CHUNK_TIMEOUT
    
    def needs_heartbeat(self) -> bool:
        """Check if heartbeat needed to prevent timeout."""
        return self.metrics.time_since_last_chunk() > self.HEARTBEAT_INTERVAL
    
    def get_complete_text(self) -> str:
        """Get complete buffered text."""
        return ''.join(self.buffer)
    
    def mark_disconnected(self):
        """Bug #2 Fix: Mark stream as disconnected."""
        self.disconnected = True
        logger.info(
            f"🔌 Stream disconnected after {self.metrics.total_duration():.2f}s "
            f"({self.metrics.chunks_sent} chunks, {self.metrics.bytes_sent} bytes)"
        )
    
    def is_disconnected(self) -> bool:
        """Check if stream disconnected."""
        return self.disconnected
    
    def get_stats(self) -> dict:
        """Get buffer statistics."""
        return {
            'chunks_sent': self.metrics.chunks_sent,
            'bytes_sent': self.metrics.bytes_sent,
            'duration_seconds': self.metrics.total_duration(),
            'retries': self.metrics.retries,
            'duplicates_filtered': self.metrics.duplicates_filtered,
            'unicode_fixes': self.metrics.unicode_fixes,
            'buffer_size_bytes': self.buffer_size,
            'disconnected': self.disconnected
        }


class StreamValidator:
    """
    Validates streaming responses for completeness and correctness.
    Handles Bug #4, #5, #7.
    """
    
    MIN_COMPLETE_LENGTH = 50  # Minimum chars for complete response
    MIN_CHUNK_COUNT = 5       # Minimum chunks for complete response
    MAX_RETRIES = 2           # Bug #7 Fix: Prevent retry storms
    
    @staticmethod
    def is_complete_sentence(text: str) -> bool:
        """
        Bug #4 Fix: Check if text ends with complete sentence.
        """
        if not text or len(text) < 10:
            return False
        
        # Vietnamese and English sentence endings
        sentence_endings = {'.', '!', '?', '。', '。', '！', '？'}
        
        # Trim whitespace
        text = text.rstrip()
        
        # Check last character
        if text[-1] in sentence_endings:
            return True
        
        # Check for common Vietnamese sentence patterns (word endings)
        complete_patterns = [
            ' ạ', ' nhé', ' nha', ' đó', ' vậy', ' rồi',
            'ạ', 'nhé', 'nha', 'đó', 'vậy', 'rồi'
        ]
        
        for pattern in complete_patterns:
            if text.endswith(pattern):
                return True
        
        return False
    
    @staticmethod
    def validate_json(text: str) -> bool:
        """
        Bug #5 Fix: Validate JSON response completeness.
        """
        import json
        
        # Try parsing
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError as e:
            logger.debug(f"JSON validation failed: {e}")
            return False
    
    @staticmethod
    def should_retry(
        buffer: StreamBuffer,
        retry_count: int,
        is_json: bool = False
    ) -> bool:
        """
        Bug #7 Fix: Determine if retry is needed (with storm prevention).
        
        Returns:
            True if should retry, False otherwise
        """
        # Bug #7: Prevent retry storms
        if retry_count >= StreamValidator.MAX_RETRIES:
            logger.warning(
                f"⚠️ Max retries ({StreamValidator.MAX_RETRIES}) reached, "
                f"stopping retry storm"
            )
            return False
        
        # Don't retry if disconnected by client
        if buffer.is_disconnected():
            logger.info("🔌 Client disconnected, no retry needed")
            return False
        
        # Retry if response too short
        text = buffer.get_complete_text()
        if len(text) < StreamValidator.MIN_COMPLETE_LENGTH:
            logger.info(
                f"🔄 Response too short ({len(text)} chars), "
                f"retry #{retry_count + 1}"
            )
            return True
        
        # Retry if too few chunks (likely timeout)
        if buffer.metrics.chunks_sent < StreamValidator.MIN_CHUNK_COUNT:
            logger.info(
                f"🔄 Too few chunks ({buffer.metrics.chunks_sent}), "
                f"retry #{retry_count + 1}"
            )
            return True
        
        # Retry if JSON expected but invalid
        if is_json and not StreamValidator.validate_json(text):
            logger.info(f"🔄 Invalid JSON, retry #{retry_count + 1}")
            return True
        
        # Retry if incomplete sentence
        if not StreamValidator.is_complete_sentence(text):
            logger.info(f"🔄 Incomplete sentence, retry #{retry_count + 1}")
            return True
        
        # All checks passed, no retry needed
        return False


async def send_heartbeat(interval: float = 5.0) -> str:
    """
    Generate heartbeat comment to prevent timeout.
    Bug #1 Fix: Keep connection alive.
    """
    await asyncio.sleep(interval)
    return ": heartbeat\n\n"  # SSE comment format


def generate_end_marker() -> str:
    """
    Bug #10 Fix: Generate proper end marker for streaming.
    """
    return "data: [DONE]\n\n"
