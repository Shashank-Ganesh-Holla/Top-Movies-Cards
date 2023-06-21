from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, InputRequired, NumberRange
from imdb import Cinemagoer, IMDbError
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Whatever key you like to keep in order to secure the request from CSRF'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie_list.db"
Bootstrap(app)
db = SQLAlchemy(app)

movie_list = []
ia = Cinemagoer()


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f"Movie Name: {self.title}"


class RateMovieForm(FlaskForm):
    rating = StringField(label="Your Rating Out of 10 e.g. 7.5", render_kw={"autocomplete": "off"})
    review = StringField(label="Your Review", render_kw={"autocomplete": "off"})
    submit = SubmitField(label="Done")


class AddMovie(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[InputRequired()])
    submit = SubmitField(label="Add Movie")


@app.route("/")
def home():
    global movie_list

    if not os.path.exists("movie_list.db"):
        # Create the database file
        db.create_all()
    movie_list = Movie.query.order_by(Movie.rating).all()
    # sorted_list = db.session.query(Movie).order_by(Movie.rating.asc())
    # print(movie_list)
    i = len(movie_list)
    for movie in movie_list:
        # print(movie)
        movie.ranking = i
        i -= 1
    return render_template("index.html", movie=movie_list)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    id_movie = request.args.get('id')
    form = RateMovieForm()
    movie = db.session.get(Movie, id_movie)
    if form.validate_on_submit():
        if form.rating.data:  movie.rating = form.rating.data

        if form.review.data: movie.review = form.review.data
        # movie.rating = request.form.get('rating')
        # movie.review = request.form.get('review')
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', movie=movie, form=form)


@app.route('/delete')
def delete():
    # print(request.args.get('id'))
    delete_id = request.args.get('id')
    movie_delete = db.session.get(Movie, delete_id)
    db.session.delete(movie_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = AddMovie()
    if add_form.validate_on_submit():
        movie_title = add_form.movie_title.data

        try:
            ia = Cinemagoer()
            list_movie = ia.search_movie(movie_title)
        except IMDbError as e:
            print(e)
            list_movie = []
        return render_template('select.html', movies=list_movie)

    return render_template('add.html', form=add_form)


@app.route('/select', methods=['GET', 'POST'])
def select():
    movie_id = request.args['id']

    try:
        ia = Cinemagoer()
        movie_data = ia.get_movie(movie_id)
        existing_list = db.session.query(Movie).all()
        existing_list = Movie.query.all()
        for movies in existing_list:
            if movies.title == movie_data.get('title'):
                return render_template('Error_select.html', movie=movies)

        new_movie = Movie(title=movie_data.get('title'), year=movie_data.get('year'),
                          description=movie_data.get('plot outline', "No description"),
                          rating=movie_data.get('rating'), ranking=movie_data.get('ranking', 'None'),
                          review=movie_data.get('review', "None"),
                          img_url=movie_data.get('cover url'))

        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))
    except IMDbError as e:
        print(e)

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)