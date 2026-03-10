#!/usr/bin/env python3
"""Axiom Event Bus - Internal event distribution."""

import asyncio
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
import time


class EventPriority(Enum):
    """Event priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Event:
    """Event instance."""
    id: str
    type: str
    source: str
    payload: Dict[str, Any]
    priority: EventPriority
    timestamp: float
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'source': self.source,
            'payload': self.payload,
            'priority': self.priority.value,
            'timestamp': self.timestamp,
            'correlation_id': self.correlation_id
        }


class EventBus:
    """In-memory event bus with pub/sub."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._wildcards: List[Callable[[Event], None]] = []
        self._event_counter = 0
        self._history: List[Event] = []
        self._max_history = 1000
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        self._event_counter += 1
        return f"EVT-{int(time.time())}-{self._event_counter}"
    
    def subscribe(self, event_type: str, 
                  handler: Callable[[Event], None]) -> None:
        """Subscribe to event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events."""
        self._wildcards.append(handler)
    
    def unsubscribe(self, event_type: str,
                    handler: Callable[[Event], None]) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
    
    def publish(self, event_type: str, source: str,
                payload: Dict[str, Any],
                priority: EventPriority = EventPriority.NORMAL,
                correlation_id: Optional[str] = None) -> Event:
        """Publish an event."""
        event = Event(
            id=self._generate_event_id(),
            type=event_type,
            source=source,
            payload=payload,
            priority=priority,
            timestamp=time.time(),
            correlation_id=correlation_id
        )
        
        # Store in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)
        
        # Notify subscribers
        self._notify(event)
        return event
    
    def _notify(self, event: Event) -> None:
        """Notify all subscribers."""
        # Type-specific subscribers
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Don't let handler errors break event flow
        
        # Wildcard subscribers
        for handler in self._wildcards:
            try:
                handler(event)
            except Exception:
                pass
    
    def get_history(self, event_type: Optional[str] = None,
                    limit: int = 100) -> List[Event]:
        """Get event history."""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._history.clear()


class EventRouter:
    """Route events to different handlers based on rules."""
    
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self._routes: List[tuple] = []  # (condition, handler)
    
    def add_route(self, condition: Callable[[Event], bool],
                  handler: Callable[[Event], None]) -> None:
        """Add a routing rule."""
        self._routes.append((condition, handler))
        self.bus.subscribe_all(self._route_event)
    
    def _route_event(self, event: Event) -> None:
        """Route event based on rules."""
        for condition, handler in self._routes:
            try:
                if condition(event):
                    handler(event)
            except Exception:
                pass


class AsyncEventBus(EventBus):
    """Async-enabled event bus."""
    
    def __init__(self):
        super().__init__()
        self._async_subscribers: Dict[str, List[Callable[[Event], asyncio.Future]]] = {}
        self._pending: Set[asyncio.Future] = set()
    
    async def publish_async(self, event_type: str, source: str,
                           payload: Dict[str, Any],
                           priority: EventPriority = EventPriority.NORMAL,
                           correlation_id: Optional[str] = None) -> Event:
        """Publish event asynchronously."""
        event = self.publish(event_type, source, payload, priority, correlation_id)
        await self._notify_async(event)
        return event
    
    async def _notify_async(self, event: Event) -> None:
        """Notify async subscribers."""
        handlers = self._async_subscribers.get(event.type, [])
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                else:
                    handler(event)
            except Exception:
                pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
