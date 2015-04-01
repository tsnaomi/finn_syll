# coding=utf-8

import jinja2

from flask import (
    flash,
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
    )
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.seasurf import SeaSurf
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.bcrypt import Bcrypt
from functools import wraps
from sqlalchemy.exc import IntegrityError
from syllabifier.phonology import get_sonorities, get_weights
from syllabifier.v2 import syllabify
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__, static_folder='_static', template_folder='_templates')
app.config.from_pyfile('finnsyll_config.py')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# To mirate database:
#     python finnsyll.py db init (only for initial migration)
#     python finnsyll.py db migrate
#     python finnsyll.py db upgrade

csrf = SeaSurf(app)
flask_bcrypt = Bcrypt(app)


# Models ----------------------------------------------------------------------

class Linguist(db.Model):
    __tablename__ = 'Mages'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = flask_bcrypt.generate_password_hash(password)

    def __repr__(self):
        return self.username

    def __unicode__(self):
        return self.__repr__()


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # the word's orthography
    orth = db.Column(db.String(40, convert_unicode=True), nullable=False)

    # the word's lemma form  (for later use)
    lemma = db.Column(db.String(40, convert_unicode=True), default='')

    # the syllabification that is estimated programmatically
    test_syll = db.Column(db.String(40, convert_unicode=True), default='')

    # a string of the rules applied in the test syllabfication
    applied_rules = db.Column(db.String(40, convert_unicode=True), default='')

    # the correct syllabification (hand-verified)
    syll = db.Column(db.String(40, convert_unicode=True), default='')

    # an alternative syllabification (hand-verified)
    alt_syll1 = db.Column(db.String(40, convert_unicode=True), default='')

    # an alternative syllabification (hand-verified)
    alt_syll2 = db.Column(db.String(40, convert_unicode=True), default='')

    # an alternative syllabification (hand-verified)
    alt_syll3 = db.Column(db.String(40, convert_unicode=True), default='')

    # the word's part-of-speech
    pos = db.Column(db.String(40, convert_unicode=True), default='')

    # the word's morpho-syntactic description
    msd = db.Column(db.String(40, convert_unicode=True), default='')

    # the word's frequency in the finnish newspaper corpus (for later use)
    freq = db.Column(db.Integer)

    # a boolean indicating if the word is a compound
    is_compound = db.Column(db.Boolean, default=False)

    # a boolean indicating if the word is a stopword -- only if the
    # word's syllabification is lexically marked
    is_stopword = db.Column(db.Boolean, default=False)

    # a boolean indicating if the algorithm has estimated correctly
    is_gold = db.Column(db.Boolean, default=None)

    # a boolean indiciating if the token is a valid token
    active = db.Column(db.Boolean, default=True)

    def __init__(self, orth, syll=None, alt_syll=None):
        self.orth = orth
        self.freq = 0

        if syll:
            self.syll = syll

        if alt_syll:
            self.alt_syll = alt_syll

        # converts all strings to Unicode prior to syllabifications
        db.session.add(self)
        db.session.commit()

        # populate self.test_syll
        self.syllabify()

    def __repr__(self):
        return '\tWord: %s\n\tEstimated syll: %s\n\tCorrect syll: %s\n\t' % (
            self.orth, self.test_syll or '', self.syll or '')

    def __unicode__(self):
        return self.__repr__()

    # Token attribute methods -------------------------------------------------

    @property
    def syllable_count(self):
        '''Return the number of syllables the word contains.'''
        if self.syll:
            return self.syll.count('.') + 1

    @property
    def syllables(self):
        '''Return a list of the word's syllables.'''
        return self.test_syll.split('.')

    @property
    def weights(self):
        '''Return the weight structure of the test syllabification.'''
        return get_weights(self.test_syll)

    @property
    def sonorities(self):
        '''Return the sonority structure of the test syllabification.'''
        return get_sonorities(self.test_syll)

    def is_lemma(self):
        return self.orth.lower() == self.lemma.lower()

    # Syllabification methods -------------------------------------------------

    def update_gold(self):
        '''Compare test syllabifcation against true syllabification.

        Token.is_gold is True if the test syllabifcation matches the true
        syllabification. Otherwise, Token.is_fold is False.
        '''
        if self.test_syll and self.syll:
            is_gold = self.test_syll == self.syll

            if not is_gold:
                is_gold = self.test_syll == self.alt_syll1

            if not is_gold:
                is_gold = self.test_syll == self.alt_syll2

            if not is_gold:
                is_gold = self.test_syll == self.alt_syll3

            self.is_gold = is_gold
            db.session.commit()

            return is_gold

        return False

    def syllabify(self):
        '''Algorithmically syllabify Token based on its orthography.'''
        # syllabifcations do not preserve capitalization
        token = self.orth.lower()
        self.test_syll, self.applied_rules = syllabify(token)

        if self.syll:
            self.update_gold()

    def correct(self, **kwargs):
        '''Save new attribute values to Token and update gold.'''
        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)

        db.session.commit()
        self.update_gold()


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # the name of the xml file in the Aamulehti-1999 corpus
    filename = db.Column(db.Text, unique=True)

    # a list of IDs for each word as they appear in the text
    tokens = db.Column(db.PickleType)

    # the text as a tokenized list, incl. Token IDs and punctuation strings
    tokenized_text = db.Column(db.PickleType)

    # a boolean indicating if all of the document's words have been reviewed
    reviewed = db.Column(db.Boolean, default=False)

    def __init__(self, filename, tokens, tokenized_text):
        self.filename = filename
        self.tokens = tokens
        self.tokenized_text = tokenized_text

    def __repr__(self):
        return self.filename

    def __unicode__(self):
        return self.__repr__()

    def query_document(self):
        '''Return a list of Tokens and puncts as they appear in the text.'''
        doc = []

        for t in self.tokenized_text:
            t = Token.query.get(t) if isinstance(t, int) else t
            doc.append(t)

        return doc

    def query_tokens(self):
        '''Return list of Tokens, ordered as they appear in the text.'''
        tokens = []

        for ID in self.tokens:
            token = Token.query.get(ID)

            if token.active:
                tokens.append(token)

        return tokens

    def verify_all_unverified_tokens(self):
        '''For all of the text's unverified Tokens, set syll equal to test_syll.

        This function is intended for when all uverified Tokens have been
        correctly syllabified in test_syll. Proceed with caution.
        '''
        tokens = self.query_tokens()

        for token in tokens:
            if token.is_gold is None:
                token.correct(syll=token.test_syll)

        self.reviewed = True
        db.session.commit()


# Database functions ----------------------------------------------------------

def delete_token(id):
    '''Delete token (e.g., if the orthopgraphy is a misspelling).'''
    try:
        token = Token.query.get(id)
        token.is_gold = None
        token.active = False
        db.session.commit()

    except KeyError:
        pass


def find_token(orth):
    '''Retrieve token by its ID.'''
    try:
        # ilike queries are case insensitive
        token = Token.query.filter(Token.orth.ilike(orth)).first()
        return token

    except KeyError:
        return None


def get_bad_tokens():
    '''Return all of the Tokens that are incorrectly syllabified.'''
    return Token.query.filter_by(is_gold=False).order_by(Token.orth)


def get_good_tokens():
    '''Return all of the Tokens that are correctly syllabified.'''
    return Token.query.filter_by(is_gold=True).order_by(Token.orth)


def get_unverified_tokens():
    '''Return Tokens with uncertain syllabifications.'''
    return Token.query.filter_by(is_gold=None).filter_by(active=True)


def review_tokens():
    '''Compare test_syll and syll for all Tokens; update is_gold.'''
    tokens = Token.query.all()

    for token in tokens:
        token.update_gold()


def syllabify_tokens():
    '''Algorithmically syllabify all Tokens.

    This is done anytime a Token is instantiated. It *should* also be done
    anytime the syllabifying algorithm is updated.'''
    tokens = Token.query.all()

    for token in tokens:
        token.syllabify()


def add_doc(filename):
    if filename.endswith('.txt'):

        try:
            doc = Document(filename)
            db.session.add(doc)
            db.session.commit()

            return doc

        except IntegrityError:
            db.session.rollback()
            flash('This file was previously uploaded')

    else:
        flash('Plese input a text (.txt) file. Thank you!')


def get_unreviewed_documents():
    return Document.query.filter_by(reviewed=False)


def get_numbers():
    total = Token.query.filter(Token.is_gold.isnot(None)).count()
    gold = Token.query.filter_by(is_gold=True).count()
    accuracy = (float(gold) / total) * 100.0 if gold and total else 0
    accuracy = round(accuracy, 2)

    return gold, total, accuracy


# View helpers ----------------------------------------------------------------

@app.before_request
def renew_session():
    # Forgot why I did this... but I think it's important
    session.modified = True


def login_required(x):
    # View decorator requiring users to be authenticated to access the view
    @wraps(x)
    def decorator(*args, **kwargs):
        if session.get('current_user'):
            return x(*args, **kwargs)

        return redirect(url_for('login_view'))

    return decorator


@app.context_processor
def serve_docs():
    docs = get_unreviewed_documents()

    return dict(docs=docs)


def redirect_url(default='main_view'):
    # Redirect page to previous url or to main_view
    return request.referrer or url_for(default)


def apply_form(http_form):
    # Apply changes to Token instance based on POST request
    try:
        orth = http_form['orth']
        syll = http_form['syll'] or http_form['test_syll']
        alt_syll1 = http_form['alt_syll1'] or ''
        alt_syll2 = http_form['alt_syll2'] or ''
        alt_syll3 = http_form['alt_syll3'] or ''
        is_compound = bool(http_form.getlist('is_compound'))
        is_stopword = bool(http_form.getlist('is_stopword'))
        active = bool(int(http_form['active']))
        token = find_token(orth)

        if not active:
            delete_token(token.id)

        else:
            token.correct(
                orth=orth,
                syll=syll,
                alt_syll1=alt_syll1,
                alt_syll2=alt_syll2,
                alt_syll3=alt_syll3,
                is_compound=is_compound,
                is_stopword=is_stopword,
                )

    except (AttributeError, KeyError, LookupError):
        pass


# Views -----------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
@login_required
def main_view():
    '''List links to unverified texts (think: Table of Contents).'''
    if request.method == 'POST':

        try:
            f = request.form['file']
            doc = add_doc(f)

            if doc:
                return redirect(url_for('doc_view', id=doc.id))

        except BadRequestKeyError:
            flash('No file was selected.')

    stats = (
        '<b>%s</b>/<b>%s</b> correctly syllabified<br><b>%s</b>%% accuracy'
        ) % get_numbers()

    # return render_template('main.html', docs=docs, stats=stats, kw='main')
    return render_template('main.html', stats=stats, kw='main')


@app.route('/doc/<id>', methods=['GET', 'POST'])
@login_required
def doc_view(id):
    '''Present detail view of specified doc, composed of editable Tokens.'''
    if request.method == 'POST':
        apply_form(request.form)

    doc = Document.query.get_or_404(id)
    TEXT = doc.query_document()

    return render_template('doc.html', doc=doc, TEXT=TEXT, kw='doc')


@app.route('/approve/approve/approve/doc/<id>', methods=['POST', ])
@login_required
def approve_doc_view(id):
    '''For all of the doc's unverified Tokens, set syll equal to test_syll.'''
    doc = Document.query.get_or_404(id)
    doc.verify_all_unverified_tokens()

    return redirect(url_for('doc_view', id=id))


@app.route('/unverified', methods=['GET', 'POST'])
@login_required
def unverified_view():
    '''List all unverified Tokens and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_unverified_tokens()

    return render_template('tokens.html', tokens=tokens, kw='unverified')


@app.route('/bad', methods=['GET', 'POST'])
@login_required
def bad_view():
    '''List all incorrectly syllabified Tokens and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_bad_tokens()

    return render_template('tokens.html', tokens=tokens, kw='bad')


@app.route('/good', methods=['GET', 'POST'])
@login_required
def good_view():
    '''List all correctly syllabified Tokens and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_good_tokens()

    return render_template('tokens.html', tokens=tokens, kw='good')


@app.route('/delete/delete/delete/token/<id>', methods=['POST', ])
@login_required
def delete_token_view(id):
    '''Delete the specified token.'''
    delete_token(id)

    return redirect(redirect_url())


@app.route('/enter', methods=['GET', 'POST'])
def login_view():
    '''Sign in current user.'''
    if session.get('current_user'):
        return redirect(url_for('main_view'))

    if request.method == 'POST':
        username = request.form['username']
        linguist = Linguist.query.filter_by(username=username).first()

        if linguist is None or not flask_bcrypt.check_password_hash(
                linguist.password,
                request.form['password']
                ):
            flash('Invalid username and/or password.')

        else:
            session['current_user'] = linguist.username
            return redirect(url_for('main_view'))

    return render_template('enter.html')


@app.route('/leave')
def logout_view():
    '''Sign out current user.'''
    session.pop('current_user', None)

    return redirect(url_for('main_view'))


# Jinja2 ----------------------------------------------------------------------

def gold_class(t):
    # Return an is_gold css class for a given token.is_gold value
    gold = t.is_gold
    return 'good' if gold else 'unverified' if gold is None else 'bad'


def istoken(t):
    # Return True if the t is a Token object, else False
    return hasattr(t, 'syll')

jinja2.filters.FILTERS['gold_class'] = gold_class
jinja2.filters.FILTERS['istoken'] = istoken

# -----------------------------------------------------------------------------


if __name__ == '__main__':
    manager.run()
