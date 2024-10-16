import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from app import create_app, init_db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        init_db(app)
    app.run(debug=True)
