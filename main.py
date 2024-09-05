from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
from random import choice
import os

'''
Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///cafes.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        # Method 1.
        dictionary = {}
        # Loop through each column in the data record
        for column in self.__table__.columns:
            # Create a new dictionary entry;
            # where the key is the name of the column
            # and the value is the value of the column
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

        # Method 2. Alternatively use Dictionary Comprehension to do the same thing.
        # return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


# HTTP GET - Read Record
@app.route('/random', methods=['GET'])
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()  # return a list of rows in our db

    random_cafe = choice(all_cafes)

    return jsonify(cafe=random_cafe.to_dict())


# HTTP GET - All Record
@app.route('/all', methods=['GET'])
def get_all_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()  # return a list of rows in our database

    return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


# HTTP GET - Search a Specific Record
@app.route('/search', methods=['GET'])
def search():

    if request.method == 'GET':
        loc = request.args.get('loc')

        result = db.session.execute(db.select(Cafe).where(Cafe.location == loc))
        search_result = result.scalars().all()

        if search_result:
            return jsonify(cafes=[cafe.to_dict() for cafe in search_result])
        else:
            return {
                "error": {
                    "Not Found": "Sorry, we don't have a cafe at that location"
                }
            }
    else:
        return {
            "error": {
                "Bad Request": "Sorry, bad method request."
            }
        }


# HTTP PUT/PATCH - Update Record
@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':

        try:
            new_cafe = Cafe(
                name=request.form.get("name"),
                map_url=request.form.get("map_url"),
                img_url=request.form.get("img_url"),
                location=request.form.get("location"),
                has_sockets=bool(request.form.get("sockets")),
                has_toilet=bool(request.form.get("toilet")),
                has_wifi=bool(request.form.get("wifi")),
                can_take_calls=bool(request.form.get("calls")),
                seats=request.form.get("seats"),
                coffee_price=request.form.get("coffee_price"),
            )

            db.session.add(new_cafe)
            db.session.commit()

            return {
                "response": {
                    "success": "Successfully added the new cafe"
                }
            }, 200

        except Exception as e:
            return jsonify({"response": {"error": str(e)}}), 400

    else:
        return {
            "response": {
                "error": "Method Not Allowed"
            }
        }, 405


# HTTP PUT/PATCH - Update Record
@app.route("/update-price/<int:cafe_id>", methods=['PATCH', 'GET'])
def update_price(cafe_id):
    if request.method == "PATCH":

        try:
            # select item from db
            cafe = db.get_or_404(Cafe, cafe_id)

            # let update the column coffee_price of the selected cafe
            cafe.coffee_price = request.form.get('coffee_price')

            # commit the query
            db.session.commit()

            # return success message
            return {
                "response": {
                    "success": "Successfully updated the price."
                }
            }, 200

        except Exception as e:
            return jsonify({"response": {"error": str(e)}}), 404


# HTTP DELETE - Delete Record
@app.route("/delete/<int:cafe_id>", methods=['DELETE'])
def delete(cafe_id):
    if request.method == "DELETE":

        # check API_KEY
        if request.form.get('api_key'):

            api_key = request.form.get('api_key')
            if api_key == "TopSecretAPIKey":
                # try and catch exception
                try:
                    # select the cafe by id
                    cafe = db.get_or_404(Cafe, cafe_id)

                    # delete cafe in db
                    db.session.delete(cafe)
                    # commit the query
                    db.session.commit()

                    # return success
                    return jsonify({"response": {"success": "Successfully deleted."}})

                except Exception as e:
                    return jsonify({"response": {"error": str(e)}}), 404
            else:
                return jsonify({"response": {"error": "Wrong API KEY! Make sure you have the correct API KEY."}}), 403

        else:
            return jsonify({"response": {"error": "Sorry! An API KEY is required."}}), 403


if __name__ == '__main__':
    app.run(debug=True)
