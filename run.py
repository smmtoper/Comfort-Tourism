from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("СЕРВЕР ЗАПУЩЕН!")
    print("Откройте в браузере: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)