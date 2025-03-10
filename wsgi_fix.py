from app import create_app

# Создаем экземпляр приложения
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) 