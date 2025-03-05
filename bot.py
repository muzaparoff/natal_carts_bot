from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext
from datetime import datetime
from zoneinfo import ZoneInfo
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import swisseph as swe

# Константы состояний разговора
DATE, TIME, PLACE, PREDICTION = range(4)

# Функция, запускающая разговор (стартовая точка)
def start_conv(update: Update, context: CallbackContext) -> int:
    # Приветствие и запрос даты рождения
    update.message.reply_text(
        "Здравствуйте! Давайте составим ваш гороскоп.\n"
        "Для начала, введите вашу дату рождения в формате ДД.ММ.ГГГГ.\n"
        "Вы можете в любой момент написать 'отмена' для отмены."
    )
    return DATE  # Переходим в состояние DATE

# Обработчик введенной даты рождения
def handle_date(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    date_text = update.message.text.strip()
    try:
        # Парсим дату из строки формата ДД.ММ.ГГГГ
        birth_date = datetime.strptime(date_text, "%d.%m.%Y")
        # Сохраняем дату в user_data
        user_data['birth_date'] = birth_date
    except ValueError:
        # Если парсинг не удался, просим повторить ввод
        update.message.reply_text("Пожалуйста, введите дату в правильном формате ДД.ММ.ГГГГ.")
        return DATE
    # Запрашиваем время рождения
    update.message.reply_text(
        "Спасибо. Теперь введите время рождения (часы и минуты) в формате ЧЧ:ММ (24-часовой формат)."
    )
    return TIME  # Переходим в состояние TIME

# Обработчик введенного времени рождения
def handle_time(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    time_text = update.message.text.strip()
    try:
        # Парсим время из строки формата ЧЧ:ММ
        birth_time = datetime.strptime(time_text, "%H:%M")
        # Сохраняем объект времени (часы и минуты) в user_data
        user_data['birth_time'] = birth_time
    except ValueError:
        # Если формат неверный, просим повторить
        update.message.reply_text("Время должно быть в формате ЧЧ:ММ, попробуйте еще раз.")
        return TIME
    # Запрашиваем место рождения
    update.message.reply_text("Отлично. Теперь укажите место рождения (город и страна).")
    return PLACE  # Переходим в состояние PLACE

# Обработчик введенного места рождения
def handle_place(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    place = update.message.text.strip()
    if not place:
        update.message.reply_text("Название места не распознано, попробуйте еще раз.")
        return PLACE
    # Используем геокодер для получения координат по названию места
    geolocator = Nominatim(user_agent="astro_bot")
    location = None
    try:
        location = geolocator.geocode(place)
    except Exception as e:
        location = None
    if location is None:
        # Если не удалось получить координаты, просим уточнить место
        update.message.reply_text("Не удалось найти этот населенный пункт. Пожалуйста, введите город и страну еще раз.")
        return PLACE
    # Сохраняем информацию о месте и координатах
    user_data['place'] = place
    user_data['latitude'] = location.latitude
    user_data['longitude'] = location.longitude
    # Предлагаем варианты предсказания с помощью клавиатуры быстрого выбора
    reply_keyboard = [["общий характер", "гороскоп на день"], ["совместимость", "финансовые перспективы"]]
    update.message.reply_text(
        "Принято. Что вы хотите узнать?\n"
        "Выберите один из вариантов: общий характер, гороскоп на день, совместимость, финансовые перспективы.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PREDICTION  # Переходим в состояние PREDICTION

# Обработчик выбора типа предсказания и генерации ответа
def handle_prediction(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    query_type = update.message.text.strip().lower()
    # Получаем сохраненные ранее данные
    birth_date: datetime = user_data.get('birth_date')
    birth_time: datetime = user_data.get('birth_time')
    lat = user_data.get('latitude')
    lon = user_data.get('longitude')
    place = user_data.get('place')
    # Объединяем дату и время в единый объект datetime (пока без часового пояса)
    birth_datetime_local = datetime(
        birth_date.year, birth_date.month, birth_date.day,
        birth_time.hour, birth_time.minute, tzinfo=None
    )
    # Определяем часовой пояс по координатам места рождения
    tf = TimezoneFinder()
    try:
        timezone_str = tf.timezone_at(lng=lon, lat=lat)
    except Exception as e:
        timezone_str = None
    if timezone_str is None:
        timezone_str = "UTC"
    try:
        tz = ZoneInfo(timezone_str)
    except Exception as e:
        tz = ZoneInfo("UTC")
    # Присваиваем объекту datetime найденный часовой пояс
    birth_datetime_local = birth_datetime_local.replace(tzinfo=tz)
    # Конвертируем время рождения в UTC
    birth_datetime_utc = birth_datetime_local.astimezone(ZoneInfo("UTC"))
    # Рассчитываем юлианскую дату (необходимо для вычислений Swiss Ephemeris)
    ut_hour = birth_datetime_utc.hour + birth_datetime_utc.minute/60.0 + birth_datetime_utc.second/3600.0
    jd = swe.julday(birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day, ut_hour)
    # Получаем положение планет на этой юлианской дате
    planets = [
        (swe.SUN, "Солнце"), (swe.MOON, "Луна"), (swe.MERCURY, "Меркурий"),
        (swe.VENUS, "Венера"), (swe.MARS, "Марс"), (swe.JUPITER, "Юпитер"),
        (swe.SATURN, "Сатурн"), (swe.URANUS, "Уран"), (swe.NEPTUNE, "Нептун"),
        (swe.PLUTO, "Плутон")
    ]
    positions = {}  # Словарь для долгот планет
    for planet, name in planets:
        pos, ret = swe.calc_ut(jd, planet)
        if ret != swe.ERR:
            # pos[0] содержит эклиптическую долготу планеты в градусах
            positions[name] = pos[0]
    # Определяем основные аспекты между планетами
    aspects = []  # список для хранения обнаруженных аспектов
    aspect_names = {0: "соединение", 60: "секстиль", 90: "квадрат", 120: "трин", 180: "оппозиция"}
    major_aspects = [0, 60, 90, 120, 180]
    planet_names = list(positions.keys())
    n = len(planet_names)
    for i in range(n):
        for j in range(i+1, n):
            p1 = planet_names[i]
            p2 = planet_names[j]
            # Разница в долготе между двумя планетами
            diff = abs(positions[p1] - positions[p2])
            if diff > 180:
                diff = 360 - diff
            # Проверяем, близка ли разница к одному из основных аспектов (орбус ~5°)
            for aspect_angle in major_aspects:
                if abs(diff - aspect_angle) < 5:
                    aspects.append((p1, p2, aspect_names[aspect_angle]))
                    break
    # Формируем текст предсказания в шуточной форме
    prediction_text = ""
    if "характер" in query_type:
        # Общий характер
        # Определим знаки Солнца и Луны
        sun_lon = positions.get("Солнце")
        moon_lon = positions.get("Луна")
        if sun_lon is not None and moon_lon is not None:
            sun_sign = int(sun_lon // 30)  # 0 = Овен, 1 = Телец, и т.д.
            moon_sign = int(moon_lon // 30)
            signs = ["Овне", "Тельце", "Близнецах", "Раке", "Льве", "Деве",
                     "Весах", "Скорпионе", "Стрельце", "Козероге", "Водолее", "Рыбах"]
            sun_sign_name = signs[sun_sign] if 0 <= sun_sign < 12 else "неизвестном знаке"
            moon_sign_name = signs[moon_sign] if 0 <= moon_sign < 12 else "неизвестном знаке"
            prediction_text += f"Вы родились с Солнцем в {sun_sign_name}, а Луной в {moon_sign_name}. "
            # Пара шуточных комментариев про Солнце
            if sun_sign_name == "Овне":
                prediction_text += "Вы прирожденный лидер и иногда бежите вперед паровоза. "
            elif sun_sign_name == "Тельце":
                prediction_text += "Вы упрямы как бык, но зато очень надежны и любите комфорт. "
            elif sun_sign_name == "Близнецах":
                prediction_text += "Вы любознательны и непостоянны, у вас семь пятниц на неделе. "
            # ... можно добавить описание для остальных знаков
            # Шуточный комментарий про знак Луны
            if moon_sign_name == "Рыбах":
                prediction_text += "Ваша душа поет в такт звездам, вы очень чувствительны. "
            elif moon_sign_name == "Козероге":
                prediction_text += "Внутри вы более серьезны, чем показываете окружающим. "
        # Добавим информацию об одном из аспектов, если есть
        if aspects:
            p1, p2, asp_name = aspects[0]
            prediction_text += f"Кстати, у вас {asp_name} между {p1} и {p2}, что придает вашей личности особую изюминку. "
        prediction_text += "В целом, вы уникальны - и звезды подтверждают это с улыбкой!"
    elif "день" in query_type or "гороскоп" in query_type:
        # Гороскоп на день
        if aspects:
            # Берем первый аспект для влияния дня
            p1, p2, asp_name = aspects[0]
            prediction_text += f"Сегодня {p1} и {p2} образуют аспект {asp_name}. "
            if asp_name == "оппозиция":
                prediction_text += "Это словно перетягивание каната внутри вас: возможны колебания настроения. "
            elif asp_name == "квадрат":
                prediction_text += "Угол в 90° между планетами добавляет перца в этот день: будьте готовы к неожиданностям. "
        else:
            prediction_text += "Сегодня звезды к вам милостивы и не создают особых аспектов. "
        prediction_text += "Совет дня: улыбнитесь отражению в зеркале и вперед - звезды вам подмигивают!"
    elif "совместимость" in query_type:
        # Совместимость (любовь/отношения)
        venus_lon = positions.get("Венера")
        mars_lon = positions.get("Марс")
        if venus_lon is not None:
            venus_sign = int(venus_lon // 30)
            signs_list = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
                          "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
            venus_sign_name = signs_list[venus_sign] if 0 <= venus_sign < 12 else "неизвестно"
            prediction_text += f"Ваша Венера в знаке {venus_sign_name}, "
            if venus_sign_name in ["Лев", "Овен", "Стрелец"]:
                prediction_text += "поэтому в любви вы страстны и драматичны, как в кино. "
            elif venus_sign_name in ["Телец", "Весы"]:
                prediction_text += "вы цените комфорт и гармонию в отношениях. "
            else:
                prediction_text += "ваши симпатии порой непредсказуемы. "
        if mars_lon is not None:
            mars_sign = int(mars_lon // 30)
            signs_list = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
                          "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
            mars_sign_name = signs_list[mars_sign] if 0 <= mars_sign < 12 else "неизвестно"
            prediction_text += f"Ваш Марс в знаке {mars_sign_name}, "
            if mars_sign_name in ["Скорпион", "Овен"]:
                prediction_text += "что придает вашим отношениям огня и интенсивности. "
            elif mars_sign_name in ["Рак", "Рыбы"]:
                prediction_text += "что делает вас мягким и заботливым партнером, хотя иногда вы застенчивы. "
            else:
                prediction_text += "что сильно влияет на ваш стиль общения с партнером. "
        prediction_text += "В итоге, звезды советуют искать того, кто оценит вашу уникальность и выдержит ваш характер!"
    elif "финанс" in query_type or "бюджет" in query_type or "карьер" in query_type:
        # Финансовые перспективы
        jupiter_lon = positions.get("Юпитер")
        saturn_lon = positions.get("Сатурн")
        if jupiter_lon is not None:
            jupiter_sign = int(jupiter_lon // 30)
            signs_rus = ["Овна", "Тельца", "Близнецов", "Рака", "Льва", "Девы",
                         "Весов", "Скорпиона", "Стрельца", "Козерога", "Водолея", "Рыб"]
            jupiter_sign_name = signs_rus[jupiter_sign] if 0 <= jupiter_sign < 12 else "неизвестного знака"
            prediction_text += f"Ваш Юпитер в знаке {jupiter_sign_name}. "
            if jupiter_sign_name in ["Козерога", "Девы"]:
                prediction_text += "Это указывает на серьезный подход к финансам и умение планировать бюджет. "
            elif jupiter_sign_name in ["Стрельца", "Льва"]:
                prediction_text += "Такое положение говорит о щедрости: вы то экономите, то транжирите. "
            else:
                prediction_text += "Это положение придает вашим финансам долю непредсказуемости. "
        if saturn_lon is not None:
            saturn_sign = int(saturn_lon // 30)
            signs_rus = ["Овна", "Тельца", "Близнецов", "Рака", "Льва", "Девы",
                         "Весов", "Скорпиона", "Стрельца", "Козерога", "Водолея", "Рыб"]
            saturn_sign_name = signs_rus[saturn_sign] if 0 <= saturn_sign < 12 else "неизвестного знака"
            prediction_text += f"Сатурн у вас в знаке {saturn_sign_name}. "
            if saturn_sign_name in ["Козерога", "Водолея"]:
                prediction_text += "Он дает вам дисциплину и расчетливость в денежных вопросах. "
            elif saturn_sign_name in ["Рака", "Рыб"]:
                prediction_text += "Он может вселять неуверенность в финансах, но это преодолимо. "
            else:
                prediction_text += "Он учит вас терпению на пути к материальным целям. "
        prediction_text += "В итоге, ваше финансовое будущее в ваших руках. Звезды лишь намекают на путь, а вам решать - идти по нему или протоптать свой!"
    else:
        # Если тип запроса не распознан, даем общий ответ
        prediction_text += "Звезды выстроились в необычном порядке. Просто будьте собой и помните: даже если планеты нынче капризничают, ваша улыбка способна это исправить!"
    # Отправляем текст предсказания пользователю
    update.message.reply_text(prediction_text, reply_markup=ReplyKeyboardRemove())
    # Завершаем разговор
    return ConversationHandler.END

# Обработчик команды отмены
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Запрос отменен. Если захотите попробовать снова, просто начните заново командой 'гороскоп'.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Главная функция запуска бота
def main() -> None:
    import os
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not set.")
        return
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    # Определяем ConversationHandler для последовательного диалога с пользователем
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('goroskop', start_conv),
            # Remove the problematic Cyrillic command that's causing the error
            # CommandHandler('натальная_карта', start_conv), <- This line is causing the error
            CommandHandler('natal_chart', start_conv),  # Use Latin characters only
            MessageHandler(Filters.regex('^(натальная карта|гороскоп)$'), start_conv)
        ],
        states={
            DATE: [MessageHandler(Filters.text & ~Filters.command, handle_date)],
            TIME: [MessageHandler(Filters.text & ~Filters.command, handle_time)],
            PLACE: [MessageHandler(Filters.text & ~Filters.command, handle_place)],
            PREDICTION: [MessageHandler(Filters.text & ~Filters.command, handle_prediction)]
        },
        fallbacks=[MessageHandler(Filters.regex('^(отмена|Отмена|/cancel)$'), cancel)]
    )
    dp.add_handler(conv_handler)
    # Дополнительно, перенаправляем /start на начало диалога
    dp.add_handler(CommandHandler('start', start_conv))
    # Запускаем бота
    updater.start_polling()
    print("Bot started. Press Ctrl+C to stop.")
    updater.idle()

if __name__ == '__main__':
    main()