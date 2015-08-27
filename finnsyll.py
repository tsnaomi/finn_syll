# coding=utf-8

from datetime import datetime
from flask import (
    abort,
    flash,
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
    )
from flaskext.markdown import Markdown
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.seasurf import SeaSurf
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.bcrypt import Bcrypt
from functools import wraps
from math import ceil
from sqlalchemy import or_, and_  # func
from sqlalchemy.ext.hybrid import hybrid_property
from syllabifier.compound import detect, split
from syllabifier.phonology import replace_umlauts
from syllabifier.v8 import syllabify
from werkzeug.exceptions import BadRequestKeyError

app = Flask(__name__, static_folder='_static', template_folder='_templates')
app.config.from_pyfile('finnsyll_config.py')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# To mirate database:
#     python finnsyll.py db migrate
#     python finnsyll.py db upgrade

csrf = SeaSurf(app)
flask_bcrypt = Bcrypt(app)
markdown = Markdown(app)


# Models ----------------------------------------------------------------------

class Linguist(db.Model):
    __tablename__ = 'Linguist'
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
    __tablename__ = 'Token'
    id = db.Column(db.Integer, primary_key=True)

    # a boolean indicating if this word appears in the Aamulehti newspaper
    # corpus
    is_aamulehti = db.Column(db.Boolean, default=False)

    # a boolean indicating if this word appears in the Gutenberg poetry
    is_gutenberg = db.Column(db.Boolean, default=False)

    # the word's orthography
    orth = db.Column(db.String(80, convert_unicode=True), nullable=False)

    # the word's orthography in lowercase, with umlauts replaced and compound
    # boundaries delimited; the syllabifier takes in Token.base
    base = db.Column(db.String(80, convert_unicode=True), nullable=True)

    # the word's lemma/citation form
    lemma = db.Column(db.String(80, convert_unicode=True), default='')

    # rules applied in test syllabifications ----------------------------------

    rules1 = db.Column(db.String(80, convert_unicode=True), default='')

    rules2 = db.Column(db.String(80, convert_unicode=True), default='')

    rules3 = db.Column(db.String(80, convert_unicode=True), default='')

    rules4 = db.Column(db.String(80, convert_unicode=True), default='')

    rules5 = db.Column(db.String(80, convert_unicode=True), default='')

    rules6 = db.Column(db.String(80, convert_unicode=True), default='')

    rules7 = db.Column(db.String(80, convert_unicode=True), default='')

    rules8 = db.Column(db.String(80, convert_unicode=True), default='')

    rules9 = db.Column(db.String(80, convert_unicode=True), default='')

    rules10 = db.Column(db.String(80, convert_unicode=True), default='')

    rules11 = db.Column(db.String(80, convert_unicode=True), default='')

    rules12 = db.Column(db.String(80, convert_unicode=True), default='')

    rules13 = db.Column(db.String(80, convert_unicode=True), default='')

    rules14 = db.Column(db.String(80, convert_unicode=True), default='')

    rules15 = db.Column(db.String(80, convert_unicode=True), default='')

    rules16 = db.Column(db.String(80, convert_unicode=True), default='')

    # test syllabifications ---------------------------------------------------

    test_syll1 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll2 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll3 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll4 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll5 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll6 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll7 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll8 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll9 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll10 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll11 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll12 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll13 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll14 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll15 = db.Column(db.String(80, convert_unicode=True), default='')

    test_syll16 = db.Column(db.String(80, convert_unicode=True), default='')

    # correct syllabifications (hand-verified) --------------------------------

    syll1 = db.Column(db.String(80, convert_unicode=True), default='')

    syll2 = db.Column(db.String(80, convert_unicode=True), default='')

    syll3 = db.Column(db.String(80, convert_unicode=True), default='')

    syll4 = db.Column(db.String(80, convert_unicode=True), default='')

    syll5 = db.Column(db.String(80, convert_unicode=True), default='')

    syll6 = db.Column(db.String(80, convert_unicode=True), default='')

    syll7 = db.Column(db.String(80, convert_unicode=True), default='')

    syll8 = db.Column(db.String(80, convert_unicode=True), default='')

    syll9 = db.Column(db.String(80, convert_unicode=True), default='')

    syll10 = db.Column(db.String(80, convert_unicode=True), default='')

    syll11 = db.Column(db.String(80, convert_unicode=True), default='')

    syll12 = db.Column(db.String(80, convert_unicode=True), default='')

    syll13 = db.Column(db.String(80, convert_unicode=True), default='')

    syll14 = db.Column(db.String(80, convert_unicode=True), default='')

    syll15 = db.Column(db.String(80, convert_unicode=True), default='')

    syll16 = db.Column(db.String(80, convert_unicode=True), default='')

    # -------------------------------------------------------------------------

    # the word's part-of-speech
    pos = db.Column(db.String(80, convert_unicode=True), default='')

    # the word's morpho-syntactic description
    msd = db.Column(db.String(80, convert_unicode=True), default='')

    # the word's frequency in the Aamulehti-1999 corpus
    freq = db.Column(db.Integer, default=0)

    # a boolean indicating if the word is a compound
    is_compound = db.Column(db.Boolean, default=False)

    # a boolean indicating if the word is a non-delimited compound
    is_nondelimited_compound = db.Column(db.Boolean, default=False)

    # a boolean indicating if the syllabifier predicts the word is a compound
    is_test_compound = db.Column(db.Boolean, default=False)

    # a boolean indicating if the word is a stopword -- only if the word's
    # syllabification is lexically marked
    is_stopword = db.Column(db.Boolean, default=False)

    # a boolean indicating if the algorithm has estimated correctly
    is_gold = db.Column(db.Boolean, default=None)

    # a note field to jot down notes about the word
    note = db.Column(db.Text, default='')

    # a temporary boolean to indicate whether Arto had verified the token prior
    # to updating the database to accommodate variation in test syllabifcations
    # (this is likely safe to delete now)
    verified = db.Column(db.Boolean, default=False)

    # a one-to-many relationship with the Variation table (many Variations per
    # one Token)
    variations = db.relationship(
        'Variation',
        backref='t_variation',
        lazy='dynamic',
        )

    __mapper_args__ = {
        'order_by': [is_gold, is_compound, freq.desc()],
        }

    def __init__(self, orth, **kwargs):
        self.orth = orth

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)

        self.inform_base()
        self.detect_is_compound()
        self.syllabify()

    def __repr__(self):
        return self.orth

    def __unicode__(self):
        return self.__repr__()

    def readable_lemma(self):
        '''Return a readable form of the lemma.'''
        return self.lemma.replace('_', ' ')

    def is_lemma(self):
        '''Return True if the word is in its citation form, else False.'''
        return self.orth.lower() == self.readable_lemma().lower()

    # Syllabification methods -------------------------------------------------

    def inform_base(self):
        '''Populate Token.base with a syllabifier-friendly form of the orth.'''
        # syllabifcations do not preserve capitalization or umlauts
        self.base = split(replace_umlauts(self.orth.lower()))

    def detect_is_compound(self):
        '''Populate Token.is_test_compound.'''
        # super fancy programmatic detection
        self.is_test_compound = detect(self.base)

    def syllabify(self):
        '''Programmatically syllabify the Token based on its base form.'''
        syllabifications = list(syllabify(self.base, self.is_test_compound))

        for i, (test_syll, rules) in enumerate(syllabifications, start=1):
            test_syll = replace_umlauts(test_syll, put_back=True)
            rules = rules.translate(None, 'abcdefg')

            setattr(self, 'test_syll' + str(i), test_syll)
            setattr(self, 'rules' + str(i), rules)

        if self.syll1:
            self.update_gold()

    def correct(self, **kwargs):
        '''Save new attributes to the Token and update its gold status.'''
        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)

        self.update_gold()

    def update_gold(self):
        '''Token.is_gold is True iff there is perfect precision and recall.'''
        self.is_gold = self.sylls() == self.test_sylls()

    def test_sylls(self):
        '''Return a set of all of the Token's test syllabifications.'''
        test_sylls = [getattr(self, 'test_syll%s' % n) for n in range(1, 9)]
        test_sylls = set(filter(None, test_sylls))
        # test_sylls = set(test_sylls).remove('')

        return test_sylls

    def sylls(self):
        '''Return a set of all of the Token's correct syllabifications.'''
        sylls = [getattr(self, 'syll%s' % n) for n in range(1, 9)]
        sylls = set(filter(None, sylls))
        # sylls = set(sylls).remove('')

        return sylls

    # Variation methods -------------------------------------------------------

    @hybrid_property
    def is_ambiguous(self):
        '''A boolean indicating if the Token exhibits variation.'''
        return bool(self.test_syll2 or self.syll2)

    @is_ambiguous.expression
    def is_ambiguous(cls):
        '''A boolean indicating if the Token exhibits variation.'''
        return or_(cls.test_syll2 != '', cls.syll2 != '')

    # Evaluation methods ------------------------------------------------------

    @property
    def p_r(self):
        '''A string repr of the Token's precision and recall (P / R).'''
        return '%s / %s' % (round(self.precision, 2), round(self.recall, 2))

    @property
    def precision(self):
        '''See https://en.wikipedia.org/wiki/Precision_and_recall#Precision.'''
        try:
            return round(
                len(self.test_sylls().intersection(self.sylls())) * 1.0 /
                len(self.test_sylls()),
                2)

        except ZeroDivisionError:
            return 0.0

    @property
    def recall(self):
        '''See https://en.wikipedia.org/wiki/Precision_and_recall#Recall.'''
        try:
            return round(
                len(self.test_sylls().intersection(self.sylls())) * 1.0 /
                len(self.sylls()),
                2)

        except ZeroDivisionError:
            return 0.0


class Poem(db.Model):
    __tablename__ = 'Poem'
    id = db.Column(db.Integer, primary_key=True)

    # the title of the poem
    title = db.Column(db.String(80, convert_unicode=True), default='')

    # the name of the poet
    poet = db.Column(db.Enum(
        u'Erkko',        # J. H. Erkko
        u'Hellaakoski',  # Aaro Hellaakoski
        u'Kaatra',       # Kössi Kaatra
        u'Kailas',       # Uuno Kailas
        u'Koskenniemi',  # V. A. Koskenniemi
        u'Kramsu',       # Kaarlo Kramsu
        u'Leino',        # Eino Leino
        u'Lönnrot',      # Elias Lönnrot
        u'Siljo',        # Juhani Siljo
        name='POET',
        convert_unicode=True,
        ))

    # each book of poetry is split into portions of roughly 1600 lines,
    # manually spread across several Poem objects
    portion = db.Column(db.Integer, default=1)

    # the poem's Gutenberg ebook number
    ebook_number = db.Column(db.Integer)

    # the poem's release date
    date_released = db.Column(db.DateTime)

    # the date the poem was last updated on Gutenberg, if different from the
    # the relase date
    last_updated = db.Column(db.DateTime)

    # the poem as a tokenized lists, incl. Variation IDs and strings of words
    tokenized_poem = db.Column(db.PickleType)

    # a boolean indicating if all of the poem's variations have been reviewed
    reviewed = db.Column(db.Boolean, default=False)

    # a one-to-many relationship with the Variation table (many Variations per
    # Poem)
    variations = db.relationship(
        'Variation',
        backref='p_variation',
        lazy='dynamic',
        )

    # the number of variations associated with this poetry ebook
    variation_count = db.Column(db.Integer)

    def __init__(self, **kwargs):
        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)

    def __repr__(self):
        return '%s by %s' % (self.title, self.poet)

    def __unicode__(self):
        return self.__repr__()

    @property
    def ebook(self):
        '''The poem/book of poems' Gutenberg identifier.'''
        return 'EBook #%s' % self.ebook_number

    @property
    def poet_surname(self):
        '''Return the poet's surname.'''
        return self.poet.split()[-1]

    def query_poem(self):
        '''Return a list of Variations and words as they appear in the poem.'''
        variations = {v.id: v for v in self.variations}
        poem = [variations.get(w, w) for w in self.tokenized_poem]

        return poem

    def update_review(self):
        '''Set reviewed to True if all of the variations have been verified.'''
        reviewed = all(variation.verified for variation in self.variations)
        self.reviewed = reviewed

    def get_variation_count(self):
        '''Return a formatted variation count.'''
        return format(self.variation_count, ',d')


class Variation(db.Model):
    __tablename__ = 'Variation'
    id = db.Column(db.Integer, primary_key=True)

    # a one-to-many relationship with the Token table (many Variations per
    # Token)
    token_id = db.Column(db.Integer, db.ForeignKey('Token.id'))

    # a one-to-many relationship with the Poem table (many Variations per
    # Poem)
    poem_id = db.Column(db.Integer, db.ForeignKey('Poem.id'))

    # a one-to-many relationship with the Sequence table (many Sequences per
    # Variation)
    sequences = db.relationship(
        'Sequence',
        backref='v_sequence',
        lazy='dynamic',
        )

    def __init__(self, token, poem):
        self.token_id = token
        self.poem_id = poem

    def __repr__(self):
        return 'Variation %s' % self.id

    def __unicode__(self):
        return self.__repr__()

    @property
    def verified(self):
        '''A boolean indicating if this Variation has been hand-verified.'''
        return all(seq.verified for seq in self.sequences)

    def display(self):
        '''A string represenation of this Variation.'''
        return self.t_variation.orth.lower()

    def get_sequences(self):
        '''Return a list of related Sequence objects.'''
        return [seq for seq in self.sequences]


class Sequence(db.Model):
    __tablename__ = 'Sequence'
    id = db.Column(db.Integer, primary_key=True)

    # a one-to-many relationship with the Variation table (many Sequences per
    # one Variation)
    variation_id = db.Column(db.Integer, db.ForeignKey('Variation.id'))

    # the sequence of vowels under consideration
    sequence = db.Column(db.String(10, convert_unicode=True), default='')

    # the html representation of the related token, highlighting the sequence
    html = db.Column(db.String(80, convert_unicode=True), default='')

    # an enum indicating if this sequence splits or joins
    split = db.Column(db.Enum('split', 'join', 'unknown', name='SPLIT'))

    # the scansion or metric precision of this sequence:
    # S - strong, W - weak, UNK - unknown
    scansion = db.Column(db.Enum(
        'S', 'W', 'SW', 'WS', 'SS', 'WW', 'UNK',
        name='SCANSION',
        ))

    # a boolean indicating if the sequence begins in an odd syllable
    is_odd = db.Column(db.Boolean, default=None)

    # a note field to jot down notes about this sequence
    note = db.Column(db.Text, default='')

    def __init__(self, variation, sequence, **kwargs):
        self.variation_id = variation
        self.sequence = sequence

        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)

    def __repr__(self):
        return self.html.replace('<br>', '{').replace('</br>', '}')

    def __unicode__(self):
        return self.__repr__()

    @hybrid_property
    def verified(self):
        '''A boolean indicating if this Sequence has been hand-verified.'''
        return bool(self.split and self.scansion)

    @verified.expression
    def verified(cls):
        '''A boolean indicating if this Sequence has been hand-verified.'''
        return and_(cls.split.isnot(None), cls.scansion.isnot(None))

    def correct(self, split=None, scansion=None, note=''):
        '''Save new attributes to the Sequence.'''
        self.split = split
        self.scansion = scansion
        self.note = note

    def update_is_odd(self):
        '''Populate Sequence.is_odd.'''
        test_syll = self.v_sequence.t_variation.test_syll1
        start = self.html.find('<')
        dots = [1 for i, j in enumerate(test_syll) if i <= start and j == '.']
        is_odd = sum(dots) % 2 == 0

        self.is_odd = is_odd


class Document(db.Model):
    __tablename__ = 'Document'
    id = db.Column(db.Integer, primary_key=True)

    # the name of the xml file in the Aamulehti-1999 corpus
    filename = db.Column(db.Text, unique=True)

    # a boolean indicating if all of the document's words have been reviewed
    reviewed = db.Column(db.Boolean, default=False)

    # the text as a tokenized list, incl. Token IDs and punctuation strings
    tokenized_text = db.Column(db.PickleType)

    # a list of IDs for each word as they appear in the text
    tokens = db.Column(db.PickleType)

    # number of unique Tokens that appear in the text
    unique_count = db.Column(db.Integer)

    def __init__(self, filename, tokenized_text, tokens):
        self.filename = filename
        self.tokenized_text = tokenized_text
        self.tokens = tokens
        self.unique_count = len(tokens)

    def __repr__(self):
        return self.filename

    def __unicode__(self):
        return self.__repr__()

    def query_document(self):
        '''Return a list of Tokens and puncts as they appear in the text.'''
        tokens = {t.id: t for t in self.get_tokens()}
        doc = [tokens.get(t, t) for t in self.tokenized_text]

        return doc

    def get_tokens(self):
        '''Return a list of the Tokens that appear in the text.'''
        return db.session.query(Token).filter(Token.id.in_(self.tokens)).all()

    def verify_all_unverified_tokens(self):
        '''For all of the text's unverified Tokens, set syll equal to test_syll.

        This function is intended for when all uverified Tokens have been
        correctly syllabified in test_syll. Proceed with caution.
        '''
        tokens = self.get_tokens()

        for token in tokens:
            if token.is_gold is None:
                token.correct(syll=token.test_syll)

        self.reviewed = True
        db.session.commit()

    def update_review(self):
        '''Set reviewed to True if all of the Tokens have been verified.'''
        tokens = self.get_tokens()
        unverified_count = 0

        for t in tokens:
            if t.is_gold is None:
                unverified_count += 1
                break

        # if there are no unverified tokens but the document isn't marked as
        # reviewed, mark the document as reviewed; this would be the case if
        # all of the documents's tokens were verified in previous documents
        if unverified_count == 0:
            self.reviewed = True


# Database functions ----------------------------------------------------------

@manager.command
def detect_compounds():
    '''Detect compounds.'''
    print 'Detecting compounds... ' + datetime.utcnow().strftime('%I:%M')

    count = Token.query.count()
    start = 0
    end = x = 1000

    while start + x < count:
        for token in Token.query.order_by(Token.id).slice(start, end):
            token.inform_base()
            token.detect_is_compound()

        db.session.commit()
        start = end
        end += x

    for token in Token.query.order_by(Token.id).slice(start, count):
        token.inform_base()
        token.detect_is_compound()

    db.session.commit()

    print 'Detection complete. ' + datetime.utcnow().strftime('%I:%M')


@manager.command
def syllabify_tokens():
    '''Syllabify all tokens.'''
    print 'Syllabifying... ' + datetime.utcnow().strftime('%I:%M')

    count = Token.query.count()
    start = 0
    end = x = 1000

    while start + x < count:
        for token in Token.query.order_by(Token.id).slice(start, end):
            token.syllabify()

        db.session.commit()
        start = end
        end += x

    for token in Token.query.order_by(Token.id).slice(start, count):
        token.syllabify()

    db.session.commit()

    print 'Syllabifications complete. ' + datetime.utcnow().strftime('%I:%M')

    # calculate average precision and recall
    update_precision_and_recall()


def find_token(orth):
    '''Retrieve a token by its orthography.'''
    try:
        # ilike queries are case insensitive
        token = Token.query.filter(Token.orth.ilike(orth)).first()
        return token

    except KeyError:
        return None


def update_poems():
    '''Update the reviewed status of each Poem object.'''
    for poem in Poem.query.all():
        poem.update_review()

    db.session.commit()


def update_precision_and_recall():
    with open('_precision_and_recall.txt', 'w') as f:
        VERIFIED = Token.query.filter(Token.is_gold.isnot(None))
        verified = VERIFIED.count()

        # calculate average precision and recall
        P = round(float(sum([t.precision for t in VERIFIED])) / verified, 4)
        R = round(float(sum([t.recall for t in VERIFIED])) / verified, 4)

        f.write('%s\n%s' % (P, R))

        print '%s / %s' % (P, R)


# Baisc queries ---------------------------------------------------------------

def get_bad_tokens():
    '''Return all of the tokens that are incorrectly syllabified.'''
    return Token.query.filter_by(is_gold=False)


def get_good_tokens():
    '''Return all of the tokens that are correctly syllabified.'''
    return Token.query.filter_by(is_gold=True).order_by(Token.lemma)


def get_unverified_tokens():
    '''Return tokens with uncertain syllabifications.'''
    return Token.query.filter_by(is_aamulehti=True).filter_by(is_gold=None)


def get_unseen_lemmas():
    '''Return unseen lemmas with uncertain syllabfications.'''
    tokens = Token.query.filter_by(is_aamulehti=True).filter_by(freq=0)
    tokens = tokens.order_by(Token.lemma)

    return tokens


def get_stopwords():
    '''Return all unverified stopwords.'''
    tokens = Token.query.filter_by(is_stopword=True)

    return tokens


def get_notes():
    '''Return all of the tokens that contain notes.'''
    return Token.query.filter(Token.note != '').order_by(Token.freq.desc())


# Variation queries -----------------------------------------------------------

def get_variation():
    '''Return tokens with alternative test or gold syllabifications.'''
    return Token.query.filter_by(is_aamulehti=True).filter(Token.is_ambiguous)


# Compound queries ------------------------------------------------------------

def get_test_compounds():
    '''Return tokens predicted to be compounds.'''
    return Token.query.filter_by(is_test_compound=True)


def get_unverified_test_compounds():
    '''Return predicted compounds that are not hand-verified compounds.'''
    tokens = get_test_compounds().filter(Token.is_gold.isnot(None))
    tokens = tokens.filter_by(is_compound=False)

    return tokens


def get_uncaptured_gold_compounds():
    '''Return hand-verified compounds that are not predicted compounds.'''
    tokens = Token.query.filter(Token.is_gold.isnot(None))
    tokens = tokens.filter_by(is_compound=True)
    tokens = tokens.filter_by(is_test_compound=False)

    return tokens


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


# @app.context_processor
def serve_docs():
    # Serve documents to navbar
    docs = Document.query.filter_by(reviewed=False)
    docs = docs.order_by(Document.unique_count).limit(10)

    return dict(docs=docs)


# @app.context_processor
def serve_peoms():
    # Serve poems to navbar
    poems = Poem.query.filter_by(reviewed=False).limit(10)

    return dict(poems=poems)


def apply_form(http_form, commit=True):
    # Apply changes to Token instance based on POST request
    try:
        token = Token.query.get(http_form['id'])
        syll1 = http_form['syll1']
        syll2 = http_form.get('syll2', '')
        syll3 = http_form.get('syll3', '')
        syll4 = http_form.get('syll4', '')
        # syll5 = http_form.get('syll5', '')
        # syll6 = http_form.get('syll6', '')
        # syll7 = http_form.get('syll7', '')
        # syll8 = http_form.get('syll8', '')
        note = http_form.get('note', '')

        try:
            is_compound = bool(http_form.getlist('is_compound'))
            # is_stopword = bool(http_form.getlist('is_stopword'))

        except AttributeError:
            is_compound = bool(http_form.get('is_compound'))
            # is_stopword = bool(http_form.get('is_stopword'))

        token.correct(
            syll1=syll1,
            syll2=syll2,
            syll3=syll3,
            syll4=syll4,
            # syll5=syll5,
            # syll6=syll6,
            # syll7=syll7,
            # syll8=syll8,
            is_compound=is_compound,
            # is_stopword=is_stopword,
            note=note,
            verified_again=True,
            )

        if commit:
            db.session.commit()

    except (AttributeError, KeyError, LookupError):
        pass


def apply_bulk_form(http_form):
    # Apply changes to multiple Token instances based on POST request
    forms = {k: {} for k in range(1, 41)}
    attrs = ['id', 'syll1', 'syll2', 'syll3', 'syll4', 'is_compound', 'note']

    for i in range(1, 41):
        for attr in attrs:
            try:
                forms[i][attr] = http_form['%s_%s' % (attr, i)]

            except BadRequestKeyError:
                pass

    for form in forms.itervalues():
        apply_form(form, commit=False)

    db.session.commit()


def apply_sequence_form(http_form):
    # Apply changes to multiple Sequence instances based on POST request
    n = 2 if http_form.get('id_2') else 1
    forms = {k: {} for k in range(1, n + 1)}
    attrs = ['id', 'split', 'scansion', 'note']

    for i in range(1, n + 1):
        for attr in attrs:
            try:
                forms[i][attr] = http_form.get('%s_%s' % (attr, i))

            except BadRequestKeyError:
                pass

    for form in forms.itervalues():
        seq = Sequence.query.get(form['id'])
        seq.correct(
            split=form['split'],
            scansion=form['scansion'],
            note=form['note'],
            )

    db.session.commit()


# Views -----------------------------------------------------------------------

@app.route('/', methods=['GET', 'POST'])
@login_required
def main_view():
    '''List statistics on the syllabifier's performance.'''
    VERIFIED = db.session.query(Token.id).filter(Token.is_gold.isnot(None))
    GOLD = VERIFIED.filter_by(is_gold=True)

    token_count = 991730  # Token.query.filter_by(is_aamulehti=True).count()

    # calculate accuracy excluding compounds
    simplex_gold = GOLD.filter_by(is_compound=False).count()
    simplex_verified = VERIFIED.filter_by(is_compound=False).count()
    simplex_accuracy = (float(simplex_gold) / simplex_verified) * 100

    # calculate accuracy including compounds
    gold = GOLD.count()
    verified = VERIFIED.count()
    accuracy = (float(gold) / verified) * 100

    # calculate compound numbers
    COMPOUNDS = VERIFIED.filter_by(is_compound=True)
    compound_test = COMPOUNDS.filter_by(is_test_compound=True).count()
    compound_gold = COMPOUNDS.count()
    compound_accuracy = (float(compound_test) / compound_gold) * 100

    # read average precision and recall
    with open('_precision_and_recall.txt', 'r') as f:
        precision, recall = f.read().split()

    # # calculate aamulehti numbers
    # doc_count = 61529  # Document.query.count()
    # reviewed = 823  # Document.query.filter_by(reviewed=True).count()

    stats = {
        'token_count': format(token_count, ',d'),
        # 'doc_count': format(doc_count, ',d'),
        'verified': format(verified, ',d'),
        'gold': format(gold, ',d'),
        'simplex_accuracy': round(simplex_accuracy, 2),
        'accuracy': round(accuracy, 2),
        'compound_gold': format(compound_gold, ',d'),
        'compound_test': format(compound_test, ',d'),
        'compound_accuracy': round(compound_accuracy, 2),
        # 'reviewed': format(reviewed, ',d'),
        'precision': precision,
        'recall': recall,
        }

    return render_template('main.html', kw='main', stats=stats)


@app.route('/rules', methods=['GET', ])
@login_required
def rules_view():
    '''List syllabification rules.'''
    return render_template('rules.html', kw='rules')


@app.route('/notes', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/notes/page/<int:page>', methods=['GET', 'POST'])
@login_required
def notes_view(page):
    '''List all tokens that contain notes.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_notes()

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='notes',
        )


@app.route('/poems', methods=['GET', ])
@login_required
def poems_view():
    '''Present an index of poems.'''
    poems = Poem.query.order_by(
        Poem.poet,
        Poem.ebook_number,
        Poem.portion,
        ).all()

    return render_template('main.html', poems=poems, kw='poems')


@app.route('/poems/<id>', methods=['GET', 'POST'])
@login_required
def poem_view(id):
    '''Present detail view of specified doc, composed of editable Tokens.'''
    if request.method == 'POST':
        apply_sequence_form(request.form)

    poem = Poem.query.get_or_404(id)
    POEM = poem.query_poem()

    return render_template('poem.html', poem=poem, POEM=POEM, kw='poem')


@app.route('/poems/update', methods=['GET', ])
@login_required
def poem_update_view():
    '''Call update_poems().'''
    update_poems()

    return redirect(url_for('poem_view', id=1))


@app.route('/doc/<id>', methods=['GET', 'POST'])
@login_required
def doc_view(id):
    '''Present detail view of specified doc, composed of editable Tokens.'''
    if request.method == 'POST':
        apply_form(request.form)

    doc = Document.query.get_or_404(id)
    TEXT = doc.query_document()

    scroll = request.form.get('scroll', None)

    return render_template(
        'doc.html',
        doc=doc,
        TEXT=TEXT,
        kw='doc',
        scroll=scroll,
        )


@app.route('/approve/approve/approve/doc/<id>', methods=['POST', ])
@login_required
def approve_doc_view(id):
    '''For all of the doc's unverified Tokens, set syll equal to test_syll.'''
    doc = Document.query.get_or_404(id)
    doc.verify_all_unverified_tokens()

    return redirect(url_for('doc_view', id=id))


@app.route('/contains', methods=['GET', 'POST'])
@login_required
def contains_view():
    '''Search for tokens by word and/or citation form.'''
    results, find, count = None, None, None

    if request.method == 'POST':
        find = request.form.get('search')

        if request.form.get('syll1'):
            apply_form(request.form)

        if '.' in find:
            results = Token.query.filter_by(is_aamulehti=True).filter(or_(
                Token.test_syll1.contains(find),
                Token.test_syll2.contains(find),
                Token.test_syll3.contains(find),
                Token.test_syll4.contains(find),
                ))

        else:
            results = Token.query.filter(Token.orth.contains(find))

        count = format(results.count(), ',d')

        try:
            results = results[:500]

        except IndexError:
            pass

    return render_template(
        'search.html',
        kw='contains',
        results=results,
        find=find,
        count=count,
        )


@app.route('/find', methods=['GET', 'POST'])
@login_required
def find_view():
    '''Search for tokens by word and/or citation form.'''
    results, find = None, None

    if request.method == 'POST':

        if request.form.get('syll1'):
            apply_form(request.form)

        find = request.form.get('search') or request.form['syll1']
        FIND = find.strip().translate({ord('.'): None, })  # strip periods
        # FIND = find.strip().translate(None, '.')  # strip periods
        results = Token.query.filter(Token.orth.ilike(FIND))
        results = results.filter_by(is_aamulehti=True)
        results = results if results.count() > 0 else None

    return render_template(
        'search.html',
        kw='find',
        results=results,
        find=find,
        )


@app.route(
    '/compounds/unverified',
    defaults={'page': 1},
    methods=['GET', 'POST'],
    )
@app.route('/compounds/unverified/page/<int:page>', methods=['GET', 'POST'])
@login_required
def unverified_compounds_view(page):
    '''List all unverified compounds and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_unverified_test_compounds()
    count = format(tokens.count(), ',d')
    tokens, pagination = paginate(page, tokens)

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='unverified_compounds',
        pagination=pagination,
        count=count,
        description=True,
        )


@app.route(
    '/compounds/uncaptured',
    defaults={'page': 1},
    methods=['GET', 'POST'],
    )
@app.route('/compounds/uncaptured/page/<int:page>', methods=['GET', 'POST'])
@login_required
def uncaptured_compounds_view(page):
    '''List all uncaptured compounds and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_uncaptured_gold_compounds()
    count = format(tokens.count(), ',d')
    tokens, pagination = paginate(page, tokens)

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='uncaptured_compounds',
        pagination=pagination,
        count=count,
        description=True,
        )


@app.route('/unverified', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/unverified/page/<int:page>', methods=['GET', 'POST'])
@login_required
def unverified_view(page):
    '''List all unverified Tokens and process corrections.'''
    if request.method == 'POST':
        apply_bulk_form(request.form)

    tokens = get_unverified_tokens().slice(0, 200)
    tokens, pagination = paginate(page, tokens, per_page=10)

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='unverified',
        pagination=pagination,
        )


@app.route('/bad', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/bad/page/<int:page>', methods=['GET', 'POST'])
@login_required
def bad_view(page):
    '''List all incorrectly syllabified Tokens and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_bad_tokens()
    count = format(tokens.count(), ',d')
    tokens, pagination = paginate(page, tokens)

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='bad',
        pagination=pagination,
        count=count,
        description=True,
        )


@app.route('/lemma', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/lemma/page/<int:page>', methods=['GET', 'POST'])
@login_required
def lemma_view(page):
    '''List all unverified unseen lemmas and process corrections.'''
    if request.method == 'POST':
        apply_bulk_form(request.form)

    tokens = get_unseen_lemmas()
    tokens, pagination = paginate(page, tokens)

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='lemmas',
        pagination=pagination,
        )


@app.route('/variation/', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/variation/page/<int:page>', methods=['GET', 'POST'])
@login_required
def variation_view(page):
    '''List all ambiguous tokens and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = get_variation()
    count = format(tokens.count(), ',d')
    tokens, pagination = paginate(page, tokens)

    return render_template(
        'tokens.html',
        tokens=tokens,
        kw='variation',
        pagination=pagination,
        count=count,
        description=True,
        )


@app.route('/hidden/', defaults={'page': 1}, methods=['GET', 'POST'])
@app.route('/hidden/page/<int:page>', methods=['GET', 'POST'])
@login_required
def hidden_view(page):
    '''List all ambiguous tokens and process corrections.'''
    if request.method == 'POST':
        apply_form(request.form)

    tokens = Token.query.filter(Token.rules1.contains('T4'))
    tokens, pagination = paginate(page, tokens)

    return render_template(
        'tokens.html',
        tokens=tokens,
        pagination=pagination,
        )


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

def goldclass(t):
    gold = t.is_gold
    gold = u'good' if gold else u'unverified' if gold is None else u'bad'
    compound = ' compound' if t.is_compound else ''

    return gold + compound


def variationclass(v):
    return 'variation-verified' if v.verified else 'variation-unverified'


def js_safe(s):
    s = s.replace('\r\n', '&#13;&#10;')
    s = s.replace('(', '&#40;').replace(')', '&#41;')
    s = s.replace('"', '&#34;').replace("'", '&#34;')

    return s

app.jinja_env.filters['goldclass'] = goldclass
app.jinja_env.filters['variationclass'] = variationclass
app.jinja_env.filters['js_safe'] = js_safe
app.jinja_env.tests['token'] = lambda t: hasattr(t, 'syll1')
app.jinja_env.tests['variation'] = lambda v: hasattr(v, 'sequences')


# Pagination ------------------------------------------------------------------

class Pagination(object):

    def __init__(self, page, per_page, total_count):
        self.page = page
        self.per_page = per_page
        self.total_count = total_count

    @property
    def pages(self):
        return int(ceil(self.total_count / float(self.per_page)))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self):
        left_edge, left_current = 2, 2
        right_edge, right_current = 2, 5

        last = 0
        for num in xrange(1, self.pages + 1):

            if num <= left_edge or (
                num > self.page - left_current - 1 and
                num < self.page + right_current
                    ) or num > self.pages - right_edge:

                if last + 1 != num:
                    yield None

                yield num

                last = num


def paginate(page, tokens, per_page=40):
    count = tokens.count()
    start = (page - 1) * per_page or 0
    end = min(start + per_page, count)

    try:
        tokens = tokens[start:end]

    except IndexError:
        if page != 1:
            abort(404)

    pagination = Pagination(page, per_page, count)

    return tokens, pagination


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page

    return url_for(request.endpoint, **args)

app.jinja_env.globals['url_for_other_page'] = url_for_other_page


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    manager.run()
