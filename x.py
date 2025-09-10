@dp.message(AdminStates.waiting_for_subscription_days)
async def process_subscription_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        if days <= 0:
            await message.answer("Пожалуйста, введите положительное число дней.")
            return
            
        data = await state.get_data()
        user_id = data.get('subscription_user_id')
        
        # Pass days to database function instead of end_date
        database.update_subscription(user_id, days)
        
        # Calculate end date for confirmation message
        end_date = datetime.now() + timedelta(days=days)
        await message.answer(f"✅ Подписка для пользователя {user_id} успешно добавлена на {days} дней.\nОкончание: {end_date.strftime('%Y-%m-%d %H:%M')}")
        await state.clear()
        await send_admin_panel(message.chat.id)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число дней.")