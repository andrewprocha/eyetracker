"""Thread-safe ring buffer for captured frames."""

import threading
from collections import deque
from typing import Any, Optional


class RingBuffer:
    """Lock-protected ring buffer with fixed capacity."""

    def __init__(self, maxsize: int = 10):
        """
        Initialize ring buffer.

        Args:
            maxsize: Maximum number of items to store.
        """
        self._buffer: deque = deque(maxlen=maxsize)
        self._lock = threading.Lock()

    def put(self, item: Any) -> None:
        """
        Add item to buffer (oldest is dropped if full).

        Args:
            item: Item to add.
        """
        with self._lock:
            self._buffer.append(item)

    def get(self) -> Optional[Any]:
        """
        Remove and return oldest item, or None if empty.

        Returns:
            Oldest item or None.
        """
        with self._lock:
            if self._buffer:
                return self._buffer.popleft()
            return None

    def peek_all(self) -> list:
        """
        Return all items without removing them.

        Returns:
            List of all items.
        """
        with self._lock:
            return list(self._buffer)

    def clear(self) -> None:
        """Clear all items."""
        with self._lock:
            self._buffer.clear()

    def size(self) -> int:
        """
        Get current number of items.

        Returns:
            Number of items.
        """
        with self._lock:
            return len(self._buffer)

    def is_empty(self) -> bool:
        """
        Check if buffer is empty.

        Returns:
            True if empty.
        """
        with self._lock:
            return len(self._buffer) == 0
