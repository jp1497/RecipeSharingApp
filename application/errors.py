from flask import render_template
from application import app, db

# Works same as view functions, but with the 2nd return value being the error code
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # in case of a database error, rollback the database to it's previous state
    db.session.rollback()
    return render_template('errors/500.html'), 500
