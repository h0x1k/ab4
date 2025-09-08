from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel_keyboard(is_parsing_active):
    buttons = [
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_menu")],
        [InlineKeyboardButton(text="👥 Управление подписками", callback_data="subscriptions_menu")],
        [InlineKeyboardButton(text="📊 Управление БК", callback_data="bookmakers_menu")],
        [InlineKeyboardButton(text="📢 Управление каналами", callback_data="channel_settings_menu")],
        [InlineKeyboardButton(text="📈 Статус бота", callback_data="bot_status")],
        [InlineKeyboardButton(text="🔍 Отладка", callback_data="debug_info")],
        [InlineKeyboardButton(text=f"{'⏸️ Приостановить парсинг' if is_parsing_active else '▶️ Возобновить парсинг'}", callback_data="toggle_parsing")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def settings_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="🔑 Логин/пароль Sportschecker", callback_data="set_credentials")],
        [InlineKeyboardButton(text="⏰ Интервал парсинга", callback_data="set_parsing_interval")],
        [InlineKeyboardButton(text="🕒 Время работы бота", callback_data="set_working_time")],
        [InlineKeyboardButton(text="🌐 Часовой пояс", callback_data="set_timezone")],
        [InlineKeyboardButton(text="📊 Лимиты сигналов", callback_data="set_signal_limits")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subscriptions_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="add_subscription")],
        [InlineKeyboardButton(text="⏸️ Приостановить подписку", callback_data="pause_subscription")],
        [InlineKeyboardButton(text="▶️ Возобновить подписку", callback_data="unpause_subscription")],
        [InlineKeyboardButton(text="❌ Отменить подписку", callback_data="cancel_subscription")],
        [InlineKeyboardButton(text="👥 Список пользователей", callback_data="user_list_from_subs")],
        [InlineKeyboardButton(text="👑 Назначить админа", callback_data="set_admin_user_list")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def user_actions_keyboard(user_id):
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data=f"add_subscription:{user_id}")],
        [InlineKeyboardButton(text="⏸️ Приостановить подписку", callback_data=f"pause_subscription:{user_id}")],
        [InlineKeyboardButton(text="▶️ Возобновить подписку", callback_data=f"unpause_subscription:{user_id}")],
        [InlineKeyboardButton(text="❌ Отменить подписку", callback_data=f"cancel_subscription:{user_id}")],
        [InlineKeyboardButton(text="📊 Управление БК", callback_data=f"select_user_for_bk:{user_id}")],
        [InlineKeyboardButton(text="👑 Сделать админом", callback_data=f"set_admin_user_list:{user_id}")],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="user_list_from_subs")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def bookmakers_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="👤 Для пользователей", callback_data="user_bk_management")],
        [InlineKeyboardButton(text="⚙️ Для системы", callback_data="admin_bk_management")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def users_list_keyboard(users, action_prefix):
    """Create keyboard for user list with specified action prefix"""
    keyboard = []
    
    for user in users:
        username = user['username'] or f"User {user['user_id']}"
        button_text = f"👤 {username} (ID: {user['user_id']})"
        callback_data = f"{action_prefix}:{user['user_id']}"
        keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def user_bookmakers_keyboard(user_id, bookmakers, selected_ids):
    buttons = []
    
    # Add toggle all button
    buttons.append([InlineKeyboardButton(
        text="✅ Выбрать все БК" if not selected_ids or len(selected_ids) == len([b for b in bookmakers if b['is_active']]) else "☑️ Выбрать все БК",
        callback_data=f"toggle_all_bk:{user_id}"
    )])
    
    # Add bookmaker buttons
    for bookmaker in bookmakers:
        if not bookmaker['is_active']:
            continue
            
        is_selected = bookmaker['id'] in selected_ids
        emoji = "✅" if is_selected else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {bookmaker['name']}",
            callback_data=f"toggle_bk:{bookmaker['id']}"
        )])
    
    # Add save and back buttons
    buttons.append([InlineKeyboardButton(text="💾 Сохранить", callback_data=f"save_bk:{user_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="user_bk_management")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_bookmakers_management_keyboard(bookmakers):
    buttons = []
    for bookmaker in bookmakers:
        status = "✅" if bookmaker['is_active'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {bookmaker['name']}",
            callback_data=f"admin_toggle_bk:{bookmaker['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="➕ Добавить БК", callback_data="add_new_bk")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="bookmakers_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_admin_panel_keyboard():
    buttons = [[InlineKeyboardButton(text="◀️ Назад в админ-панель", callback_data="back_to_admin_panel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def channel_management_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📋 Список каналов", callback_data="channel_list")],
        [InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")],
        [InlineKeyboardButton(text="⚙️ Управление БК каналов", callback_data="manage_channel_bk")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def channels_list_keyboard(channels, action_prefix):
    buttons = []
    for channel in channels:
        status = "✅" if channel['is_active'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{status} {channel['name']}",
            callback_data=f"{action_prefix}:{channel['channel_id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="channel_settings_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def channel_bookmakers_management_keyboard(channel_id, bookmakers):
    buttons = []
    
    # Add toggle all button
    all_selected = all(bk['is_selected'] for bk in bookmakers)
    buttons.append([InlineKeyboardButton(
        text="✅ Выбрать все БК" if all_selected else "☑️ Выбрать все БК",
        callback_data=f"channel_toggle_all_bk:{channel_id}"
    )])
    
    # Add bookmaker buttons
    for bookmaker in bookmakers:
        emoji = "✅" if bookmaker['is_selected'] else "❌"
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {bookmaker['name']}",
            callback_data=f"channel_toggle_bk:{channel_id}:{bookmaker['id']}"
        )])
    
    # Add channel management buttons
    buttons.append([InlineKeyboardButton(text="🔄 Активировать/деактивировать", callback_data=f"toggle_channel_status:{channel_id}")])
    buttons.append([InlineKeyboardButton(text="🗑️ Удалить канал", callback_data=f"delete_channel:{channel_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="manage_channel_bk")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)