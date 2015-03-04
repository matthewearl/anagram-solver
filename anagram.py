#!/usr/bin/env python

import collections
import re

class _VectorSet(object):
    """
    A vector set represents a set of numeric tuples (vectors).

    A tree-structure is used where each vector set has one child for each
    possible first (head) value in the set. Each child is itself a vector set
    representing the set of tails with the given head. The empty tuple is
    present if the `present` attribute is set.

    """
    def __init__(self):
        self.present = False
        self.children = collections.defaultdict(_VectorSet)

    def _add_vec(self, vec):
        if len(vec) > 0:
            self.children[vec[0]]._add_vec(vec[1:])
        else:
            self.present = True

    def query_lte(self, query_vec, min_vec=()):
        """
        Return vectors that are less than or equal to the query vector.
        
        Returned vectors will be the same length as the query vector, but each
        element will be less than or equal to the corresponding element in the
        query vector.

        If `min_vec` is passed, returned vectors will be lexicographically
        greater than or equal to this value.

        """
        if query_vec == ():
            if self.present and () >= min_vec:
                yield ()
        else:
            for val, child in self.children.items():
                if (val <= query_vec[0] and
                                         (min_vec == () or val >= min_vec[0])):
                    if min_vec == () or val > min_vec[0]:
                        child_min_vec = ()
                    else:
                        child_min_vec = min_vec[1:]
                    for child_vec in child.query_lte(query_vec[1:],
                                                     child_min_vec):
                        yield (val,) + child_vec

def _make_vec(word):
    """Make a letter frequency vector for given word."""
    letters = [chr(ord('A') + i) for i in range(26)]
    counter = collections.Counter(word)
    return tuple(counter[l] for l in letters)

_STRIP_RE = re.compile(r"[^A-Z]")
def _canonicalize_word(word):
    return _STRIP_RE.sub('', word.upper()) 

def _load_words(word_list, min_word_length):
    with open(word_list) as f:
        words = {_canonicalize_word(line) for line in f.readlines()}
    words = {w for w in words if len(w) >= min_word_length}
    return words

def _make_tree(word_list, min_word_length):
    """
    Make a set of frequency vectors and a vector-to-word mapping.

    The input is a list of english language words.

    The mapping maps each frequency vector to a list of canonicalized words
    which have the frequency vector.

    """
    vec_dict = collections.defaultdict(list)
    for word in _load_words(word_list, min_word_length):
        vec_dict[_make_vec(word)].append(word)
    tree = _VectorSet()
    for vec in vec_dict.keys():
        tree._add_vec(vec)
    return tree, vec_dict

def _vec_sub(v1, v2):
    """Subtract two vectors."""
    assert len(v1) == len(v2)
    return tuple(a - b for a, b in zip(v1, v2))

def _find_anagram_vecs(tree, query_vec, min_vec=()):
    """
    Find sets of vectors which sum to a query vector.

    An iterator of tuples of vectors is returned. The tuples are given in
    ascending order.

    If `min_vec` is passed, returned vectors will be lexicographically greater
    than or equal to this vector.

    """
    if sum(query_vec) == 0:
        # The empty set is the only set of non-zero vectors that sum to 0.
        yield ()
    else:
        for vec in tree.query_lte(query_vec, min_vec):
            for anagram in _find_anagram_vecs(tree,
                                              _vec_sub(query_vec, vec),
                                              min_vec=vec):
                yield (vec,) + anagram

def _expand_anagram_vecs(vec_dict, anagram_vecs):
    """
    Expand a tuple of frequency vectors into tuples of words.

    """
    if anagram_vecs == ():
        yield ()
    else:
        for anagram_words in _expand_anagram_vecs(vec_dict, anagram_vecs[1:]):
            for word in vec_dict[anagram_vecs[0]]:
                yield (word,) + anagram_words

def find_anagrams(query_word,
                  word_list='/usr/share/dict/words',
                  min_word_length=1):
    query_vec = _make_vec(_canonicalize_word(query_word))
    tree, vec_dict = _make_tree(word_list,
                                min_word_length)

    for anagram_vecs in _find_anagram_vecs(tree, query_vec):
        for anagram_words in _expand_anagram_vecs(vec_dict, anagram_vecs):
            yield anagram_words

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Find anagrams of a string.')
    parser.add_argument('input', help='String to find anagrams of')
    parser.add_argument('--min-word-length', default=1, type=int,
                        help='Minimum word length')
    parser.add_argument('--word-list', default='/usr/share/dict/words',
                        type=str, help='Word list')

    args = parser.parse_args()

    for anagram in find_anagrams(args.input,
                                 word_list=args.word_list,
                                 min_word_length=args.min_word_length):
        print anagram

