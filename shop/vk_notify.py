"""
Отправка уведомления о новом заказе администратору ВКонтакте
через messages.send (токен сообщества).

Настройки VK_BOT_TOKEN и VK_ADMIN_ID лежат в settings.py,
куда попадают из .env (VK_BOT_TOKEN, VK_ADMIN_ID).
"""
import logging
import random

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_order_to_vk(order) -> bool:
    """
    Отправляет администратору в личные сообщения ВК детали заказа.

    :param order: объект Order (уже сохранённый в БД)
    :return: True при успехе, False при любой ошибке (в т.ч. отсутствии настроек)
    """
    # Если токен/ID не заданы — просто пишем в лог и не ломаем заказ
    if not getattr(settings, 'VK_BOT_TOKEN', '') or not getattr(settings, 'VK_ADMIN_ID', 0):
        logger.warning(
            'VK_BOT_TOKEN или VK_ADMIN_ID не заданы — уведомление пропущено.'
        )
        return False

    text = (
        f'🔥 Новый заказ №{order.pk}!\n\n'
        f'👤 Имя: {order.customer_name}\n'
        f'📞 Телефон: {order.phone}\n'
        f'📍 Адрес: {order.address}\n'
        f'💬 Связь: {order.get_contact_method_display()}\n'
        f'📦 Состав:\n{order.items_summary or "—"}\n'
        f'💰 Сумма: {order.total_price} ₽\n'
        f'🕒 {order.created_at:%d.%m.%Y %H:%M}'
    )

    payload = {
        'access_token': settings.VK_BOT_TOKEN,
        'v': getattr(settings, 'VK_API_VERSION', '5.199'),
        'user_id': settings.VK_ADMIN_ID,
        'peer_id': settings.VK_ADMIN_ID,
        'message': text,
        'random_id': random.randint(1, 2_147_483_647),  # обязательный параметр VK API
    }

    try:
        response = requests.post(
            'https://api.vk.com/method/messages.send',
            data=payload,
            timeout=10,
        )
        data = response.json()
        if 'error' in data:
            logger.error('VK API error: %s', data['error'])
            return False
        return True
    except requests.RequestException as exc:
        logger.exception('Не удалось отправить уведомление в VK: %s', exc)
        return False
