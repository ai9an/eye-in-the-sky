from winotify import Notification

def notify_windows_toast(title, msg):
    toast = Notification(app_id="EITS", title=title, msg=msg)
    toast.show()
