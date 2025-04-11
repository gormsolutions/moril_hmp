from frappe.desk.doctype.notification_log.notification_log import NotificationLog

class CustomNotificationLog(NotificationLog):
    @staticmethod
    def get_permission_query_conditions(for_user):
        # Remove restriction and allow all users to see all logs
        return None
