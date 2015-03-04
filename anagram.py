#!/usr/bin/env python

"""

Anagram solver. 

Given an input string this module will generate a list of multi-word anagrams.

Internally words are represented by their frequency vectors. A frequency vector
is a 26-tuple, where each element indicates how many of the corresponding
letter are in the word. For example, a 3 in the 3th element would indicate that
the word contains 3 C's.

The module uses a prefix tree (aka a trie, or radix tree) to hold the set of
frequency vectors corresponding with english words, along with a dictionary
mapping frequency vectors back to the list of words with that frequency vector.

A prefix tree is used as it can be efficiently queried for vectors which are
less than other vectors.

Anagram finding proceeds as follows:
    1) Words are canonicalized and added into the prefix tree as frequency
       vectors. Simultaneously a dictionary from vectors to word lists is
       constructed.
    2) Sets of vectors which sum to the frequency vector of the input string
       are saught. This is done via a simple depth-first search recursion,
       querying the prefix tree at each step.
    3) The vector sets found above are then expanded into words. For each
       vector set the cartesian product of the corresponding word lists is
       computed. The result is a list of multi-word anagrams.

"""

__all__ = (
    'find_anagrams',
)

import collections
import re

class _VectorSet(object):
    """
    A vector set represents a set of numeric tuples (vectors).

    The data structure is that of a prefix tree: Each node has one child for
    each possible first (head) value in the set. Each child is itself a vector
    set representing the set of tails with the given head. The empty tuple is
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

def _make_tree(word_list, min_word_length, query_word=None):
    """
    Make a set of frequency vectors and a vector-to-word mapping.

    The input is a list of english language words.

    The mapping maps each frequency vector to a list of canonicalized words
    which have the frequency vector.

    Optionally take a query word. Only partial-anagrams of this word will be
    added to the dictionary.

    """
    if query_word:
        query_vec = _make_vec(query_word)
    vec_dict = collections.defaultdict(list)
    for word in _load_words(word_list, min_word_length):
        vec = _make_vec(word)
        if query_word is None or _vec_lte(vec, query_vec):
            vec_dict[_make_vec(word)].append(word)
    tree = _VectorSet()
    for vec in vec_dict.keys():
        tree._add_vec(vec)
    return tree, vec_dict

def _vec_sub(v1, v2):
    """Subtract two vectors."""
    assert len(v1) == len(v2)
    return tuple(a - b for a, b in zip(v1, v2))

def _vec_lte(v1, v2):
    """Return true if a vector is universally less than or equal to another."""
    return all(a <= b for a, b in zip(v1, v2))

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
    query_word = _canonicalize_word(query_word)
    query_vec = _make_vec(query_word)
    tree, vec_dict = _make_tree(word_list,
                                min_word_length,
                                query_word=query_word)

    for anagram_vecs in _find_anagram_vecs(tree, query_vec):
        for anagram_words in _expand_anagram_vecs(vec_dict, anagram_vecs):
            yield anagram_words

if __name__ == "__main__":
    def main():
        import sys
        import argparse

        parser = argparse.ArgumentParser(
                            description='Find anagrams of a string.')
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

    import cProfile
#    cProfile.run('main()')
    main()

