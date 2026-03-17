"""
Signals are handled directly in admin.save_model() for order status changes,
because we need access to the old status to detect changes.

This module is kept as a hook point for future signal-based integrations.
"""
