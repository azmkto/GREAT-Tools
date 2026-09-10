"""Sentiment word clouds built from distinctive TF-IDF terms.

Extracted from `pol_monthly_viz.ipynb` (cells 27-28 and 45-47), where the pipeline was
spread across four cells and `distinctive()` read the TF-IDF matrix off module globals.

The whole thing runs from one call:

    from great.viz import wordcloud
    fig, terms = wordcloud.sentiment_wordclouds(df1)

or step by step, if you want the intermediate frames:

    corpus       = wordcloud.prepare_corpus(df1)
    X, terms     = wordcloud.tfidf_matrix(corpus['clean_text'])
    top          = wordcloud.distinctive_terms(X, terms, corpus['Sentiment'] == 'positive')

Cleaning is not something you pass in -- `prepare_corpus()` always runs the corpus through
`great.text.clean_for_wordcloud()`, which is the cleaner built for this (it keeps the
stopword set that word clouds need stripped, unlike `clean_for_topics`).

Needs the `[viz]` extra: `wordcloud`, `scikit-learn`, `matplotlib`, plus the `[text]`
libraries that `clean_for_wordcloud` uses.
"""
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import WordCloud

from .. import palette
from ..text import clean_for_wordcloud

__all__ = [
    "prepare_corpus", "tfidf_matrix", "distinctive_terms", "ramp",
    "sentiment_wordclouds",
]


def prepare_corpus(data, text_col='Mentions', sentiment_col='Sentiment',
                   media_col='Media', exclude_media=('News',),
                   extra_stopwords=None, progress=False):
    """Drop empties/duplicates, exclude bulk media, and clean the text for word clouds.

    Mirrors what the notebook did across two cells: drop rows with no text, drop
    duplicate texts (syndicated news repeats the same body many times and would
    otherwise dominate the TF-IDF), drop the platforms in `exclude_media`, then clean
    each remaining text with `great.text.clean_for_wordcloud()`.

    `exclude_media` defaults to `('News',)` because news copy is long-form and
    editorially uniform, so it swamps social chatter. Pass `()` to keep everything.

    Returns a copy of `data` with an added `clean_text` column.
    """
    corpus = data.dropna(subset=[text_col]).drop_duplicates(subset=text_col).copy()
    if exclude_media and media_col in corpus.columns:
        corpus = corpus[~corpus[media_col].isin(exclude_media)]

    texts = corpus[text_col]
    if progress:
        try:
            from tqdm.auto import tqdm
            tqdm.pandas()
            corpus['clean_text'] = texts.progress_apply(
                lambda t: clean_for_wordcloud(t, extra_stopwords))
            return corpus
        except ImportError:
            pass
    corpus['clean_text'] = texts.map(lambda t: clean_for_wordcloud(t, extra_stopwords))
    return corpus


def tfidf_matrix(texts, max_features=3000, ngram_range=(1, 3), min_df=5):
    """Fit a TF-IDF matrix over `texts`.

    Returns `(X, terms)` -- the sparse document-term matrix and the vocabulary array.
    Defaults are the notebook's: unigrams through trigrams, terms in at least 5
    documents, capped at 3000 features.
    """
    vectorizer = TfidfVectorizer(max_features=max_features,
                                 ngram_range=ngram_range, min_df=min_df)
    X = vectorizer.fit_transform(texts)
    return X, vectorizer.get_feature_names_out()


def distinctive_terms(X, terms, mask, n=200, pool=280):
    """Terms that lift the `mask` group above the rest of the corpus.

    Scores each term by mean TF-IDF inside the group minus mean TF-IDF outside it, keeps
    the positive ones, then drops any unigram already covered by a surviving bigram or
    trigram -- so a cloud shows "harga beras" rather than "harga" and "beras" competing
    as separate words.

    `X` and `terms` come from `tfidf_matrix()`. The notebook version read both from
    module globals; they are explicit arguments here.

    Returns a Series of the top `n` terms, scored, highest first.
    """
    mask = np.asarray(mask, dtype=bool)
    inside = np.asarray(X[mask].mean(axis=0)).ravel()
    outside = np.asarray(X[~mask].mean(axis=0)).ravel()

    top = pd.Series(inside - outside, index=terms).nlargest(pool)
    top = top[top > 0]

    # drop unigrams already covered by a surviving bigram
    bigrams = [t for t in top.index if ' ' in t]
    covered = {w for b in bigrams for w in b.split()}
    keep = [t for t in top.index if ' ' in t or t not in covered]

    return top[keep].head(n)


def ramp(base_hex, lo=0.75):
    """A light-to-saturated colormap built from one hex color.

    `lo` sets how pale the light end is: 0 is white, 1 is the base color flat.
    Used to tint each word cloud with its sentiment's color from `great.palette`.
    """
    base = np.array(mcolors.to_rgb(base_hex))
    light = base + (1 - base) * (1 - lo)
    return mcolors.LinearSegmentedColormap.from_list('r', [light, base])


def sentiment_wordclouds(data, sentiments=('positive', 'negative'),
                         sent_colors=None, text_col='Mentions',
                         sentiment_col='Sentiment', media_col='Media',
                         exclude_media=('News',), extra_stopwords=None,
                         n=200, pool=280, max_words=100,
                         width=1600, height=1200, panel_width=8, panel_height=12,
                         max_features=3000, ngram_range=(1, 3), min_df=5,
                         progress=False, show=True):
    """One word cloud per sentiment, side by side, from distinctive TF-IDF terms.

    Runs the whole pipeline: clean with `great.text.clean_for_wordcloud()`, fit TF-IDF,
    score each sentiment's distinctive terms against the rest of the corpus, and render
    each cloud tinted with that sentiment's color from `great.palette`.

    Defaults to positive and negative only -- neutral has no distinctive vocabulary
    worth plotting, which is why the notebook skipped it too.

    Parameters
    ----------
    data : the prepared frame, i.e. the output of `great.viz.prep.prepare_data()`.
    sentiments : which sentiment classes to draw, one panel each.
    sent_colors : sentiment -> hex; defaults to `great.palette.sent_colors`.
    exclude_media : platforms to drop before building the corpus, see `prepare_corpus`.
    n, pool : passed to `distinctive_terms`.
    show : call `plt.show()` before returning.

    Returns
    -------
    (fig, terms_by_sentiment) -- the figure, and a dict mapping each sentiment to its
    scored term Series, so you can inspect what drove the picture.
    """
    sent_colors = palette.sent_colors if sent_colors is None else sent_colors

    corpus = prepare_corpus(data, text_col=text_col, sentiment_col=sentiment_col,
                            media_col=media_col, exclude_media=exclude_media,
                            extra_stopwords=extra_stopwords, progress=progress)
    if corpus.empty:
        raise ValueError('no rows left after cleaning -- check text_col and exclude_media')

    X, terms = tfidf_matrix(corpus['clean_text'], max_features=max_features,
                            ngram_range=ngram_range, min_df=min_df)
    sent = corpus[sentiment_col].str.strip().str.lower().values

    fig, axes = plt.subplots(1, len(sentiments),
                             figsize=(panel_width * len(sentiments), panel_height))
    terms_by_sentiment = {}

    for ax, s in zip(np.atleast_1d(axes), sentiments):
        mask = sent == s
        if mask.sum() == 0:
            ax.set_title(f'{s.capitalize()} (no data)')
            ax.axis('off')
            terms_by_sentiment[s] = pd.Series(dtype=float)
            continue

        scored = distinctive_terms(X, terms, mask, n=n, pool=pool)
        terms_by_sentiment[s] = scored

        cloud = WordCloud(width=width, height=height, background_color='white',
                          collocations=False, prefer_horizontal=0.9,
                          max_words=max_words,
                          colormap=ramp(sent_colors[s])
                          ).generate_from_frequencies(scored.to_dict())
        ax.imshow(cloud, interpolation='bilinear')
        ax.set_title(f'{s.capitalize()}  (n={mask.sum():,})',
                     fontsize=36, fontweight='bold')
        ax.axis('off')

    plt.tight_layout()
    if show:
        plt.show()

    return fig, terms_by_sentiment
