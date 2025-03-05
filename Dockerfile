# Базовый образ с Python (slim-версия для меньшего размера)
FROM python:3.10-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код бота
COPY bot.py .

# Устанавливаем временную зону контейнера (опционально, например, на UTC)
ENV TZ=UTC

# Определяем команду запуска контейнера: запуск бота
CMD ["python", "bot.py"]