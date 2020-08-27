# Connect to the database
database_name = "trivia"
SQLALCHEMY_DATABASE_URI = "postgresql://{}/{}".format('localhost:5432', database_name)

# Track modifications
SQLALCHEMY_TRACK_MODIFICATIONS = False