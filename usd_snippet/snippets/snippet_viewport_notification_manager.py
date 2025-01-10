# Viewport/Post a notification in the Viewport with omni.kit.notification_manager
from omni.kit.notification_manager import post_notification, NotificationStatus

post_notification("Notification 1, default duration")
post_notification("Notification 2, with 1 second duration", duration=1)
post_notification("Notification 4 (warning), with 4 second duration", duration=4, status=NotificationStatus.WARNING)
