from operator import itemgetter

from plogram.analysis import anc_freqs, byu_freqs
from plogram import ortho_matching

from plogram.ortho_keys import starts_list, vowels_list, first_ends_list, second_ends_list

TESTEND = 'MO'

freqs = anc_freqs.get_anc_freqs()

def get_group_order(k, n=None):
    algroups = {}
    for f, w in freqs:
        for i in range(0, len(w)-k+1):
            algroup = w[i: i+k]
            if algroup not in algroups:
                algroups[algroup] = 0
            algroups[algroup] += f
    algroups = [(f, w) for w, f in algroups.items()]
    algroups.sort(reverse=True)
    if n is not None:
        algroups = algroups[:n]
    return algroups

def get_change(text, patterns, base_patterns=ortho_matching.default_patterns):
    base_result = ortho_matching.match_text(text.upper(), patterns=base_patterns)
    result = ortho_matching.match_text(text.upper(), patterns=patterns)
    if result is None and base_result is None:
        effect_size = None
    else:
        effect_size = len(result) - len(base_result)
    return effect_size

def get_change_distribution(patterns, base_patterns=ortho_matching.default_patterns,
                            ignore_n=200, consider_n=10000):
    effect_weights = {}
    effect_counts = {}
    total_weight = 0
    for freq, word in freqs[ignore_n: ignore_n+consider_n]:
        effect = get_change(word, patterns, base_patterns)
        total_weight += freq
        if effect not in effect_weights:
            effect_weights[effect] = 0
            effect_counts[effect] = 0
        effect_weights[effect] += freq
        effect_counts[effect] += 1
    for effect in effect_weights:
        effect_weights[effect] /= total_weight
    return (effect_weights, effect_counts)

def distribution_of_improvement(
        patterns, base_patterns=ortho_matching.default_patterns, n=5, removed=False):
    ignore_n = 200
    consider_n = 10000
    top_effects = []
    total_freq = 0
    total_effect = 0
    for freq, word in freqs[ignore_n: ignore_n+consider_n]:
        base_result = ortho_matching.match_text(word.upper(), patterns=base_patterns)
        result = ortho_matching.match_text(word.upper(), patterns=patterns)
        if result is not None and base_result is not None:
            if removed:
                effect_size = (len(result) - len(base_result)) * freq
            else:
                effect_size = (len(base_result) - len(result)) * freq
            if effect_size < 0:
                effect_size = 0
            if len(top_effects) < n:
                top_effects.append((effect_size, freq, word))
            elif effect_size > top_effects[0][0]:
                top_effects[0] = (effect_size, freq, word)
                top_effects.sort()
            total_effect += effect_size
            total_freq += freq
    improvements = []
    for effect_size, freq, word in top_effects:
        improvements.append(float(total_effect)/total_freq)
        total_effect -= effect_size
        total_freq -= freq
    words = [w for e, f, w in top_effects]
    return improvements, words

def get_avg_strokes(patterns=ortho_matching.default_patterns, assume_one_n=200):
    consider_n = 10000
    count = 0
    l_count = 0
    index = 0
    total_count = 0
    fail_count = 0
    for freq, word in freqs[: consider_n]:
        result = ortho_matching.match_text(word.upper(), patterns=patterns)
        old_strokes = ortho_matching.match_text(word.upper())
        if old_strokes is not None:
            for chord in old_strokes:
                if chord['end'] == TESTEND:
                    if len(old_strokes) < len(result):
                        print(word, freq, len(result), len(old_strokes))
        if old_strokes is not None and result is not None:
            if len(old_strokes) > len(result):
                pass
        index += 1
        total_count += freq
        if result is not None:
            if index < assume_one_n:
                n_chords = 1
            else:
                n_chords = len(result)
        else:
            n_chords = None#1000000
            fail_count += freq
        if n_chords is not None:
            count += freq
            l_count += freq * n_chords
    return (float(l_count)/count, float(fail_count)/total_count)

def vowel_effects():
    base = get_avg_strokes()[0]
    pairs = []
    for vowel in vowels_list:
        if len(vowel) > 1:
            updated_vowels_list = [v for v in vowels_list]
            updated_vowels_list.remove(vowel)
            patterns = ortho_matching.make_patterns(starts_list,  updated_vowels_list, first_ends_list, second_ends_list)
            strokes, failure = get_avg_strokes(patterns)
            pairs.append((strokes-base, vowel))
    pairs.sort()
    for x in pairs:
        print(x)

def start_effects():
    data = []
    for start in starts_list:
        updated_starts_list = [v for v in starts_list]
        if start in updated_starts_list:
            updated_starts_list.remove(start)
        patterns = ortho_matching.make_patterns(
            updated_starts_list,  vowels_list, first_ends_list, second_ends_list)
        effects, words = distribution_of_improvement(patterns, removed=True)
        data.append((effects[-1], start, effects, words))
    data.sort(reverse=True)
    for e, start, effects, words in data:
        print('*************************')
        print(start, effects[-1])
        #print(effects)
        #print(words)

def end_effects():
    data = []
    for end in first_ends_list + second_ends_list:
        updated_first_ends_list = [v for v in first_ends_list]
        updated_second_ends_list = [v for v in second_ends_list]
        if end in first_ends_list:
            updated_first_ends_list.remove(end)
        if end in second_ends_list:
            updated_second_ends_list.remove(end)
        patterns = ortho_matching.make_patterns(
            starts_list,  vowels_list, updated_first_ends_list, updated_second_ends_list)
        effects, words = distribution_of_improvement(patterns, removed=True)
        data.append((effects[1], end, effects, words))
        print(end)
    data.sort(reverse=True)
    for e, end, effects, words in data:
        print(end, effects[1])

def second_to_first_end_effects():
    data = []
    for end in second_ends_list:
        updated_first_ends_list = [v for v in first_ends_list]
        updated_second_ends_list = [v for v in second_ends_list]
        if end in first_ends_list:
            updated_first_ends_list.append(end)
        if end in second_ends_list:
            updated_second_ends_list.remove(end)
        patterns = ortho_matching.make_patterns(
            starts_list,  vowels_list, updated_first_ends_list, updated_second_ends_list)
        effects, words = distribution_of_improvement(patterns)
        data.append((effects[-1], end, effects, words))
    data.sort(reverse=True)
    for e, end, effects, words in data:
        print(end, effects[-1])
        #print(effects)
        #print(words)

alphabet = [chr(o) for o in range(ord('A'), ord('Z')+1)]
alphabet_pairs = []
for a in alphabet:
    for b in alphabet:
        alphabet_pairs.append(a + b)

def add_end_effects():
    groups = []
    base_patterns = ortho_matching.make_patterns(
        starts_list,  vowels_list, first_ends_list, second_ends_list)
    base = get_avg_strokes(base_patterns)[0]
    
    g2 = [g for f, g in get_group_order(k=2, n=200)]
    g3 = [g for f, g in get_group_order(k=3, n=500)]
    g4 = [g for f, g in get_group_order(k=4, n=400)]
    #g5 = [g for f, g in get_group_order(k=5, n=300)]
    #g6 = [g for f, g in get_group_order(k=6, n=200)]
    #g7 = [g for f, g in get_group_order(k=7, n=100)]
    for algroup in alphabet + alphabet_pairs + g3 + g4:# + g5:# + g6 + g7:
    #for algroup in alphabet:
    #for algroup in ('LY', ):
        updated_first_ends_list = [v for v in first_ends_list]
        updated_first_ends_list.append(algroup.upper())
        patterns = ortho_matching.make_patterns(
            starts_list,  vowels_list, updated_first_ends_list, second_ends_list)
        strokes, failure = get_avg_strokes(patterns)
        groups.append((base-strokes, algroup))
        print(algroup, base-strokes)
    groups.sort()
    for x in groups:
        print(x)
    print(base)

def add_start_effects():
    groups = []
    patterns = ortho_matching.make_patterns(starts_list,  vowels_list, first_ends_list, second_ends_list)
    base = get_avg_strokes(patterns)[0]

    g2 = [g for f, g in get_group_order(k=2, n=200)]
    g3 = [g for f, g in get_group_order(k=3, n=500)]
    g4 = [g for f, g in get_group_order(k=4, n=400)]
    for algroup in alphabet + alphabet_pairs + g3:#alphabet + g2 + g3 + g4:
        updated_starts_list = [v for v in starts_list]
        updated_starts_list.append(algroup.upper())
        patterns = ortho_matching.make_patterns(updated_starts_list,  vowels_list, first_ends_list, second_ends_list)
        strokes, failure = get_avg_strokes(patterns)
        groups.append((base-strokes, algroup))
        print(algroup, base-strokes)
    groups.sort()
    for x in groups:
        print(x)
    print(base)

def final_effects():
    base = get_avg_strokes()[0]
    pairs = []
    for final in ('ING', 'ED', 'LY', 'Y'):
        if len(final) > 1:
            finals_list = [final]
            patterns = ortho_matching.make_patterns(
                starts_list,  vowels_list, ends_list, finals_list)
            strokes, failure = get_avg_strokes(patterns)
            pairs.append((base-strokes, final))
    pairs.sort()
    for x in pairs:
        print(x)


def test_first():
    n = 0
    for f, w in freqs[:200]:
        result = ortho_matching.match_text(w.upper())
        if result is None or len(result) > 1:
            print(w)
            n += 1
    print(n)

def find_effect_of_end(end):
    first_ends_list_without = [e for e in first_ends_list]
    second_ends_list_without = [e for e in second_ends_list]
    if end in first_ends_list_without:
        first_ends_list_without.remove(end)
    if end in second_ends_list_without:
        second_ends_list_without.remove(end)
    first_ends_list_with = [e for e in first_ends_list_without]
    first_ends_list_with.append(end)
    second_ends_list_with = [e for e in second_ends_list_without]
    second_ends_list_with.append(end)
    neither_patterns = ortho_matching.make_patterns(
        starts_list, vowels_list, first_ends_list_without,
        second_ends_list_without)
    first_with_patterns = ortho_matching.make_patterns(
        starts_list, vowels_list, first_ends_list_with,
        second_ends_list_without)
    second_with_patterns = ortho_matching.make_patterns(
        starts_list, vowels_list, first_ends_list_without,
        second_ends_list_with)
    first_change_dist = get_change_distribution(
        patterns=first_with_patterns, base_patterns=neither_patterns)
    second_change_dist = get_change_distribution(
        patterns=second_with_patterns, base_patterns=neither_patterns)
    import pdb
    pdb.set_trace()

#end_effects()
#        print('null', start, vowel, end)end_effects()
#second_to_first_end_effects()
#test_first()
#print(len(starts_list))
#print(len(ends_list))

updated_first_ends_list = [v for v in first_ends_list]
updated_second_ends_list = [v for v in second_ends_list]
end = TESTEND
if end in first_ends_list:
    updated_first_ends_list.remove(end)
if end in second_ends_list:
    updated_second_ends_list.remove(end)
patterns = ortho_matching.make_patterns(
    starts_list,  vowels_list, updated_first_ends_list, updated_second_ends_list)
base = get_avg_strokes(patterns)[0]
print(base)


