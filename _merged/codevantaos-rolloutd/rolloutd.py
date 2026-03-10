#!/usr/bin/env python3
"""Axiom Rollout Daemon - Canary deployment controller."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum, auto


class RolloutPhase(Enum):
    """Canary rollout phases."""
    PENDING = auto()
    CANARY = auto()
    ANALYSIS = auto()
    PROMOTION = auto()
    ROLLOUT = auto()
    COMPLETED = auto()
    ABORTED = auto()


class RolloutStrategy(Enum):
    """Rollout strategies."""
    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    RECREATE = "recreate"


@dataclass
class CanaryConfig:
    """Canary rollout configuration."""
    canary_percentage: int = 10
    canary_duration: float = 300  # seconds
    analysis_threshold: float = 0.99  # success rate
    max_analysis_failures: int = 3
    promotion_percentage: int = 50
    promotion_duration: float = 600


@dataclass
class RolloutStatus:
    """Current rollout status."""
    phase: RolloutPhase
    current_percentage: int
    start_time: float
    last_update: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class RolloutController:
    """Canary deployment controller."""
    
    def __init__(self, config: CanaryConfig):
        self.config = config
        self._status: Optional[RolloutStatus] = None
        self._handlers: Dict[RolloutPhase, List[Callable]] = {}
        self._abort_requested = False
    
    def start_rollout(self, deployment_id: str) -> RolloutStatus:
        """Start a new rollout."""
        now = time.time()
        self._status = RolloutStatus(
            phase=RolloutPhase.PENDING,
            current_percentage=0,
            start_time=now,
            last_update=now
        )
        self._abort_requested = False
        return self._status
    
    def advance_phase(self) -> RolloutStatus:
        """Advance to next phase."""
        if not self._status:
            raise RuntimeError("No active rollout")
        
        if self._abort_requested:
            self._status.phase = RolloutPhase.ABORTED
            return self._status
        
        phase_order = [
            RolloutPhase.PENDING,
            RolloutPhase.CANARY,
            RolloutPhase.ANALYSIS,
            RolloutPhase.PROMOTION,
            RolloutPhase.ROLLOUT,
            RolloutPhase.COMPLETED
        ]
        
        current_idx = phase_order.index(self._status.phase)
        if current_idx < len(phase_order) - 1:
            self._status.phase = phase_order[current_idx + 1]
            self._status.last_update = time.time()
            
            # Update percentage based on phase
            if self._status.phase == RolloutPhase.CANARY:
                self._status.current_percentage = self.config.canary_percentage
            elif self._status.phase == RolloutPhase.PROMOTION:
                self._status.current_percentage = self.config.promotion_percentage
            elif self._status.phase == RolloutPhase.ROLLOUT:
                self._status.current_percentage = 100
        
        return self._status
    
    def analyze_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Analyze canary metrics."""
        if not self._status:
            return False
        
        self._status.metrics = metrics
        
        # Check success rate
        success_rate = metrics.get('success_rate', 1.0)
        if success_rate < self.config.analysis_threshold:
            self._status.errors.append(
                f"Success rate {success_rate} below threshold {self.config.analysis_threshold}"
            )
            if len(self._status.errors) >= self.config.max_analysis_failures:
                self.abort("Too many analysis failures")
                return False
        
        # Check error rate
        error_rate = metrics.get('error_rate', 0.0)
        if error_rate > 0.01:  # 1% error rate threshold
            self._status.errors.append(f"Error rate {error_rate} too high")
        
        return len(self._status.errors) < self.config.max_analysis_failures
    
    def abort(self, reason: str) -> RolloutStatus:
        """Abort the rollout."""
        self._abort_requested = True
        if self._status:
            self._status.phase = RolloutPhase.ABORTED
            self._status.errors.append(f"Aborted: {reason}")
            self._status.last_update = time.time()
        return self._status
    
    def get_status(self) -> Optional[RolloutStatus]:
        """Get current rollout status."""
        return self._status
    
    def is_complete(self) -> bool:
        """Check if rollout is complete."""
        if not self._status:
            return False
        return self._status.phase in (RolloutPhase.COMPLETED, RolloutPhase.ABORTED)
    
    def can_promote(self) -> bool:
        """Check if can promote to next phase."""
        if not self._status:
            return False
        if self._status.phase != RolloutPhase.ANALYSIS:
            return False
        return len(self._status.errors) == 0


class RolloutManager:
    """Manage multiple rollouts."""
    
    def __init__(self):
        self._rollouts: Dict[str, RolloutController] = {}
    
    def create_rollout(self, deployment_id: str, 
                       config: CanaryConfig) -> RolloutController:
        """Create a new rollout."""
        controller = RolloutController(config)
        controller.start_rollout(deployment_id)
        self._rollouts[deployment_id] = controller
        return controller
    
    def get_rollout(self, deployment_id: str) -> Optional[RolloutController]:
        """Get rollout controller."""
        return self._rollouts.get(deployment_id)
    
    def list_rollouts(self) -> List[str]:
        """List all rollout IDs."""
        return list(self._rollouts.keys())
    
    def cleanup_completed(self, max_age: float = 86400) -> int:
        """Remove completed rollouts older than max_age."""
        now = time.time()
        to_remove = []
        
        for deployment_id, controller in self._rollouts.items():
            status = controller.get_status()
            if status and controller.is_complete():
                age = now - status.last_update
                if age > max_age:
                    to_remove.append(deployment_id)
        
        for deployment_id in to_remove:
            del self._rollouts[deployment_id]
        
        return len(to_remove)
