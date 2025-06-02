from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


class Base(DeclarativeBase):
    pass


TMDB_API_KEY = 'fc0467256273eef3d3c6e6acba62495e'
TMDB_API_READ_TOKEN = ('eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJmYzA0NjcyNTYyNzNlZWYzZDNjNmU2YWNiYTYyNDk1ZSIsIm5iZiI6MTc'
                       'yOTE3NDI0MC4wODcyOTksInN1YiI6IjY3MTExOThmZGI3OWM5Y2VhZTBmMGFkZiIsInNjb3BlcyI6WyJhcGlfcmV'
                       'hZCJdLCJ2ZXJzaW9uIjoxfQ.n8tYKGedTSFqevUIc05slWyeeQsKHrL6ZFVDYcghapM')

TMDB_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
TMDB_MOVIE_FIND_URL = 'https://api.themoviedb.org/3/movie'
TMDB_IMG_URL = 'https://image.tmdb.org/t/p/original/'

headers = {'Authorization': 'Bearer ' + TMDB_API_READ_TOKEN}

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
Bootstrap5(app)

db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating out 10')
    review = StringField('Review')
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    title = StringField('Movie Title')
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    rank = 1
    for movie in all_movies:
        movie.ranking = rank
        rank += 1
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        Movie_name = form.title.data
        response = requests.get(TMDB_SEARCH_URL, params={'api_key': TMDB_API_KEY, "query": Movie_name})
        results = response.json()["results"]
        return render_template("select.html", results=results)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{TMDB_MOVIE_FIND_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={'api_key': TMDB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data['original_title'],
            year=data['release_date'].split("-")[0],
            img_url=f"{TMDB_IMG_URL}{data['poster_path']}",
            description=data['overview']
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


@app.route("/edit", methods=['GET', 'POST'])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    print(f"Deleted {movie.title}")
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)

