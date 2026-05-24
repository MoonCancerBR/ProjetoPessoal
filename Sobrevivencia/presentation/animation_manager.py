try:
    import pytweening
except ImportError:
    if __package__:
        from ..config.runtime import TweeningFallback as pytweening
    else:
        from Sobrevivencia.config.runtime import TweeningFallback as pytweening

class TweenValue:
    """
    A value that smoothly transitions towards a target using an easing function.
    Useful for health bars, XP bars, and UI element positions.
    """
    def __init__(self, initial_value, duration=0.5, easing_func=pytweening.easeOutQuad):
        self.current = float(initial_value)
        self.target = float(initial_value)
        self.start_val = float(initial_value)
        self.duration = duration
        self.elapsed = 0.0
        self.easing_func = easing_func
        self.is_animating = False

    def set_target(self, new_target):
        if new_target == self.target:
            return
        self.start_val = self.current
        self.target = float(new_target)
        self.elapsed = 0.0
        self.is_animating = True

    def update(self, dt):
        if not self.is_animating:
            return self.current
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.current = self.target
            self.elapsed = self.duration
            self.is_animating = False
            return self.current
        
        progress = self.elapsed / self.duration
        eased_progress = self.easing_func(progress)
        self.current = self.start_val + (self.target - self.start_val) * eased_progress
        return self.current

class OneShotAnimation:
    """
    An animation that runs once from 0.0 to 1.0 over a duration.
    Useful for popups, damage numbers, and screen effects.
    """
    def __init__(self, duration, easing_func=pytweening.easeOutQuad, on_complete=None):
        self.duration = duration
        self.elapsed = 0.0
        self.easing_func = easing_func
        self.on_complete = on_complete
        self.progress = 0.0  # Linear progress 0->1
        self.value = 0.0     # Eased progress 0->1
        self.done = False

    def update(self, dt):
        if self.done:
            return
        
        self.elapsed += dt
        self.progress = min(1.0, self.elapsed / self.duration)
        self.value = self.easing_func(self.progress)
        
        if self.progress >= 1.0:
            self.done = True
            if self.on_complete:
                self.on_complete()

class AnimationManager:
    """
    Central manager for UI animations and smoothing.
    """
    def __init__(self):
        self.persistent_tweens = {}
        self.one_shots = []

    def get_tween(self, key, initial_value=0.0, duration=0.5, easing=pytweening.easeOutQuad):
        if key not in self.persistent_tweens:
            self.persistent_tweens[key] = TweenValue(initial_value, duration, easing)
        return self.persistent_tweens[key]

    def set_target(self, key, target_value):
        if key in self.persistent_tweens:
            self.persistent_tweens[key].set_target(target_value)

    def play_one_shot(self, duration, easing=pytweening.easeOutQuad, on_complete=None):
        anim = OneShotAnimation(duration, easing, on_complete)
        self.one_shots.append(anim)
        return anim

    def update(self, dt):
        # Update persistent tweens
        for tween in self.persistent_tweens.values():
            tween.update(dt)
            
        # Update one-shots and remove completed ones
        for anim in self.one_shots[:]:
            anim.update(dt)
            if anim.done:
                self.one_shots.remove(anim)
