"""
Configuration file for ZeroTrust Workspace Guardian
Adjust these settings for optimal accuracy in your environment
"""

# ============================================
# FACE DETECTION SETTINGS
# ============================================

# Face detection parameters (adjust for your lighting/camera)
FACE_DETECTION = {
    'scaleFactor': 1.1,       # 1.1-1.3: Lower = more sensitive but slower
    'minNeighbors': 6,        # 3-8: Higher = fewer false positives
    'minSize': (80, 80),      # Minimum face size in pixels
    'maxSize': (400, 400),    # Maximum face size in pixels
}

# Stabilization settings
STABILIZATION = {
    'face_history_length': 30,    # Number of frames to track (higher = more stable)
    'phone_history_length': 10,   # Frames for phone detection
    'consistency_threshold': 0.6,  # 0.0-1.0: Minimum consistency to trigger action
}

# ============================================
# THREAT DETECTION SETTINGS
# ============================================

# Shoulder surfing (multiple faces)
SHOULDER_SURFING = {
    'enabled': True,
    'confirmation_threshold': 4,   # Consecutive detections needed
    'cooldown_seconds': 3.0,       # Time between actions
    'action': 'minimize',          # 'minimize', 'blur', or 'lock'
}

# Camera/Phone detection
CAMERA_DETECTION = {
    'enabled': True,
    'confirmation_threshold': 3,
    'cooldown_seconds': 3.0,
    'min_area': 3000,              # Minimum object size
    'max_area': 80000,             # Maximum object size
    'aspect_ratios': {
        'portrait': (0.35, 0.75),  # Phone in portrait mode
        'landscape': (1.3, 2.2),   # Phone in landscape mode
    },
    'action': 'minimize',
}

# User absence detection
USER_ABSENCE = {
    'enabled': True,
    'threshold_seconds': 15,       # Time before auto-lock
    'action': 'lock',              # 'minimize' or 'lock'
}

# ============================================
# LOGGING & EVIDENCE
# ============================================

LOGGING = {
    'enabled': True,
    'database_path': 'security_log.db',
    'screenshot_dir': 'threat_logs',
    'capture_screenshots': True,
    'max_screenshots': 1000,       # Auto-cleanup after this many
}

# ============================================
# DISPLAY SETTINGS
# ============================================

DISPLAY = {
    'show_feed': True,
    'window_name': 'ZeroTrust Workspace Guardian - Security Feed',
    'show_face_boxes': True,
    'show_labels': True,
    'show_confidence': True,
    'show_stats': True,
}

# ============================================
# PERFORMANCE SETTINGS
# ============================================

PERFORMANCE = {
    'camera_index': 0,             # 0 = default webcam
    'frame_width': 640,            # Lower = faster processing
    'frame_height': 480,
    'fps_limit': 30,               # Maximum FPS
}

# ============================================
# ADVANCED SETTINGS
# ============================================

ADVANCED = {
    'debug_mode': False,           # Print detailed logs
    'test_mode': False,            # Don't actually minimize/lock
    'auto_start_dashboard': True,  # Launch dashboard automatically
}

# ============================================
# PRESETS
# ============================================

PRESETS = {
    'high_security': {
        'SHOULDER_SURFING': {'confirmation_threshold': 2, 'cooldown_seconds': 2.0},
        'CAMERA_DETECTION': {'confirmation_threshold': 2, 'cooldown_seconds': 2.0},
        'USER_ABSENCE': {'threshold_seconds': 10},
    },
    'balanced': {
        'SHOULDER_SURFING': {'confirmation_threshold': 3, 'cooldown_seconds': 3.0},
        'CAMERA_DETECTION': {'confirmation_threshold': 3, 'cooldown_seconds': 3.0},
        'USER_ABSENCE': {'threshold_seconds': 15},
    },
    'low_sensitivity': {
        'SHOULDER_SURFING': {'confirmation_threshold': 5, 'cooldown_seconds': 5.0},
        'CAMERA_DETECTION': {'confirmation_threshold': 5, 'cooldown_seconds': 5.0},
        'USER_ABSENCE': {'threshold_seconds': 30},
    },
}

# Select active preset
ACTIVE_PRESET = 'balanced'  # 'high_security', 'balanced', or 'low_sensitivity'

def apply_preset(preset_name):
    """Apply a preset configuration"""
    if preset_name in PRESETS:
        preset = PRESETS[preset_name]
        for category, settings in preset.items():
            globals()[category].update(settings)
        print(f"✅ Applied preset: {preset_name}")
    else:
        print(f"❌ Unknown preset: {preset_name}")

# Apply the active preset on import
if ACTIVE_PRESET:
    apply_preset(ACTIVE_PRESET)
