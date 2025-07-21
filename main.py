from app import create_app
from datetime import timedelta
from flask import Flask, session

app = create_app()
app.secret_key = 'No-secret-key'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)  # 30 minutes

@app.before_request
def before_request():
    if 'user_id' in session:
        session.permanent = True
        session.modified = True

if __name__ == '__main__':
    app.run(debug=True)