"""News-outlet account detection.

In the export, `Media` is the *platform* (Twitter, News, ...) and `Author` is the account.
Most analyses of "who drives the conversation" want people, not newsrooms, so outlet accounts
posting on social platforms are filtered out first. Every topic notebook carried its own copy
of this list, and the copies had drifted.

`BASE_MEDIA_ACCOUNTS` is the shared list. Project-specific additions go through
`extra_accounts=` rather than edits here, because an account that is noise in one topic can be
a key actor in another (the official Kremlin account is a source for Russia coverage but an
actor in a topic about a state visit to Russia).
"""
import re

import pandas as pd

MEDIA_PLATFORM_ALWAYS = {"news"}
DOMAIN_SUFFIXES = (".com", ".id", ".co", ".net", ".org")
DOMAIN_TEXT_SUFFIXES = ("dotcom", "dotid", "dotco", "dotnet", "dotorg")

BASE_MEDIA_ACCOUNTS = {
    # Indonesia
    "detikcom", "kompascom", "cnnindonesia", "tempodotco", "antaranews",
    "cnbcindonesia", "liputan6dotcom", "liputan6", "sctv", "tvonenews", "kumparan",
    "beritasatu", "metrotvnews", "tribunnews", "republikaonline", "suaradotcom",
    "jawapos", "bbcindonesia", "voaindonesia", "narasitv", "sindonews",
    "vivacoid", "bisniscom", "hariankompas", "tirtoid", "alineadotid",
    "inilahcom", "merdekadotcom", "okezone", "idntimes", "medcomid",
    "rri", "tvri", "jpnndotcom", "grid", "inewsdotid", "fajar",
    "pikiranrakyat", "gatra", "nuonline", "radioelshinta", "mediaindonesia", "setkabgoid",
    # Malaysia
    "awani", "bharianmy", "bernamadotcom", "utusandotcom", "sinarharian",
    "malaysiakini", "thestar", "nst", "theedgemarkets",
    # International
    "rt", "actualidadrt", "rtcom", "sputnik", "sputniknews", "sputnikindonesia",
    "tass", "tassagency", "rianovosti", "ria", "telesur", "telesurtv",
}

# Long words are safe as substrings anywhere in the handle.
MEDIA_KEYWORDS_SUBSTRING = ["news", "media", "redaksi", "newsroom", "official",
                            "humas", "koran", "gazette", "radio"]
# Short words only count at the END of the handle: as substrings, "pers" caught "persib_fans"
# and "tv" caught "tvstreamer", while outlets reliably put them last ("kompastv", "radarpers").
MEDIA_KEYWORDS_SUFFIX = ["tv", "pers", "fm"]


def normalize_account(name) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).strip().lower())


def is_media_account(platform, author, accounts=BASE_MEDIA_ACCOUNTS) -> bool:
    platform = str(platform).strip().lower()
    author_raw = str(author).strip().lower().lstrip("@")
    author_norm = normalize_account(author_raw)

    if platform in MEDIA_PLATFORM_ALWAYS:
        return True
    if author_norm in accounts:
        return True
    if any(kw in author_raw for kw in MEDIA_KEYWORDS_SUBSTRING):
        return True
    if author_norm.endswith(tuple(MEDIA_KEYWORDS_SUFFIX)):
        return True
    return author_raw.endswith(DOMAIN_SUFFIXES) or author_norm.endswith(DOMAIN_TEXT_SUFFIXES)


def split_media_accounts(df: pd.DataFrame, extra_accounts=(), keep_accounts=(),
                         platform_col: str = "Media", author_col: str = "Author"):
    """Return `(people, outlets)` — two frames, nothing dropped silently.

    `keep_accounts` wins over every rule, for the case where a handle trips a keyword
    ("officialpersija") but you want it analysed.
    """
    accounts = BASE_MEDIA_ACCOUNTS | {normalize_account(a) for a in extra_accounts}
    keep = {normalize_account(a) for a in keep_accounts}

    platforms = df[platform_col] if platform_col in df.columns else pd.Series("", index=df.index)
    authors = df[author_col] if author_col in df.columns else pd.Series("", index=df.index)

    mask = pd.Series(
        [is_media_account(p, a, accounts) and normalize_account(a) not in keep
         for p, a in zip(platforms, authors)],
        index=df.index,
    )
    return df[~mask].reset_index(drop=True), df[mask].reset_index(drop=True)
