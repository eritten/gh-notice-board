"""
Push Notification Service using Web Push API
"""
import json
import logging
from pywebpush import webpush, WebPushException
from django.conf import settings
from .models import PushSubscription

logger = logging.getLogger(__name__)

# VAPID keys (generate with: webpush.generate_vapid_keys())
# In production, store these securely in environment variables
VAPID_PUBLIC_KEY = getattr(settings, 'VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = getattr(settings, 'VAPID_PRIVATE_KEY', '')
VAPID_CLAIMS = {
    "sub": getattr(settings, 'VAPID_ADMIN_EMAIL', 'mailto:admin@ghnoticeboard.com')
}


def send_push_notification(user, title, body, data=None, icon=None, badge=None, url=None):
    """
    Send push notification to all user's subscribed devices

    Args:
        user: User object
        title: Notification title
        body: Notification body
        data: Additional data dict
        icon: Icon URL
        badge: Badge URL
        url: URL to open when clicked
    """
    subscriptions = PushSubscription.objects.filter(
        user=user,
        is_active=True
    )

    if not subscriptions.exists():
        logger.info(f"No active push subscriptions for user {user.username}")
        return {'sent': 0, 'failed': 0}

    # Prepare notification payload
    payload = {
        'title': title,
        'body': body,
        'icon': icon or '/static/images/logo.png',
        'badge': badge or '/static/images/badge.png',
        'data': data or {},
    }

    if url:
        payload['data']['url'] = url

    sent_count = 0
    failed_count = 0
    failed_subscriptions = []

    for subscription in subscriptions:
        try:
            subscription_info = {
                'endpoint': subscription.endpoint,
                'keys': {
                    'p256dh': subscription.p256dh,
                    'auth': subscription.auth
                }
            }

            # Send push notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )

            sent_count += 1
            subscription.save(update_fields=['last_used'])
            logger.info(f"Push notification sent to {user.username} ({subscription.device_name})")

        except WebPushException as e:
            failed_count += 1
            logger.error(f"Push notification failed for {user.username}: {str(e)}")

            # If subscription is expired or invalid, mark as inactive
            if e.response and e.response.status_code in [404, 410]:
                subscription.is_active = False
                subscription.save(update_fields=['is_active'])
                failed_subscriptions.append(subscription.id)
                logger.info(f"Marked subscription {subscription.id} as inactive")

        except Exception as e:
            failed_count += 1
            logger.error(f"Unexpected error sending push notification: {str(e)}")

    return {
        'sent': sent_count,
        'failed': failed_count,
        'failed_subscriptions': failed_subscriptions
    }


def send_bulk_push_notification(users, title, body, **kwargs):
    """
    Send push notification to multiple users

    Args:
        users: QuerySet or list of User objects
        title: Notification title
        body: Notification body
        **kwargs: Additional arguments for send_push_notification
    """
    results = {
        'total_users': len(users),
        'total_sent': 0,
        'total_failed': 0
    }

    for user in users:
        result = send_push_notification(user, title, body, **kwargs)
        results['total_sent'] += result['sent']
        results['total_failed'] += result['failed']

    return results


def notify_subscribers(subscription_type, subscription_id, title, body, **kwargs):
    """
    Send push notification to all subscribers of a category/tag/subtag

    Args:
        subscription_type: 'category', 'tag', or 'subtag'
        subscription_id: ID of the category/tag/subtag
        title: Notification title
        body: Notification body
        **kwargs: Additional arguments for send_push_notification
    """
    from .models import UserSubscription

    # Build filter based on subscription type
    filter_kwargs = {
        'push_notifications': True,
        f'{subscription_type}_id': subscription_id
    }

    subscriptions = UserSubscription.objects.filter(**filter_kwargs).select_related('user')

    # Get unique users
    users = [sub.user for sub in subscriptions]

    if not users:
        logger.info(f"No subscribers with push enabled for {subscription_type} {subscription_id}")
        return {'sent': 0, 'failed': 0}

    logger.info(f"Sending notification to {len(users)} subscribers of {subscription_type} {subscription_id}")

    return send_bulk_push_notification(users, title, body, **kwargs)


def generate_vapid_keys():
    """
    Generate VAPID keys for push notifications
    Run this once and store the keys in your environment variables
    """
    from pywebpush import vapid

    vapid_data = vapid.Vapid()
    vapid_data.generate_keys()

    public_key = vapid_data.public_key.decode('utf-8')
    private_key = vapid_data.private_key.decode('utf-8')

    print("VAPID Keys Generated:")
    print(f"Public Key: {public_key}")
    print(f"Private Key: {private_key}")
    print("\nAdd these to your .env file:")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")

    return public_key, private_key
