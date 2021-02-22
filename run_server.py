from flask_server import create_app
import os
import os.path as op
app = create_app()

# Build a sample db on the fly, if one does not exist yet.
app_dir = op.join(op.realpath(os.path.dirname(__file__)))
print("app_dir = " , app_dir)
database_path = op.join(app_dir, app.config['DATABASE_FILE'])
print("database_path = " , database_path)


if __name__ == '__main__':
    app.run(debug=True,port=5111)

    