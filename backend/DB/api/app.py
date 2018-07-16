from flask import render_template, request, url_for
from werkzeug.utils import redirect
from api import tables
from api import *

from api import queries


@app.route('/')
def display_db():
    return render_template(
        'display_db.html',
        users=queries.get_all_users(),
        pizza_pairs=queries.get_pair_since_last_reward('pizza'),
        cake_pairs=queries.get_pair_since_last_reward('cake'),
    )


#        pairs=Pair.query.all(),
#        thresholds=Threshold.query.all(),
#        rewards=Reward.query.all())


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        user = tables.User(request.form['username'], request.form['firstname'], request.form['lastname'])
        queries.add_user(user)
        return redirect(url_for('display_db'))
    return render_template('add_user.html')


@app.route('/add_pair', methods=['GET', 'POST'])
def add_pair():
    if request.method == 'POST':
        pair = tables.Pair(request.form['person1'], request.form['person2'])
        db.session.add(pair)
        db.session.commit()
        return redirect(url_for('display_db'))
    return render_template('add_pair.html')


@app.route('/edit_user/<string:username>', methods=['GET', 'POST'])
def edit_user(username):
    if request.method == 'POST':
        user = tables.User(username, request.form['firstname'], request.form['lastname'])
        queries.update_user(user)
        return redirect(url_for('display_db'))
    return render_template('edit_user.html', user=queries.get_user_by_username(username))


@app.route('/delete_user/<string:username>', methods=['GET', 'POST'])
def delete_user(username):
    queries.disable_user(username)
    return redirect(url_for('display_db'))


@app.route("/add_reward/<string:reward_type>", methods=['GET', 'POST'])
def add_reward(reward_type):
    reward = tables.Reward(reward_type)
    queries.add_reward(reward)
    return redirect(url_for('display_db'))


if __name__ == '__main__':
    db.create_all()
    db.init_app(app)
    app.run(debug=True)
