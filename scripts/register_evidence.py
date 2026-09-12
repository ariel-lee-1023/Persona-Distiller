"""Observation thresholds and equal-length stability checks for register discovery."""
import math
import statistics

# Provisional effect sizes in the metric's native units. Not population calibration.
ABSOLUTE_MINIMA = {'mean_sentence_len': 3, 'median_sentence_len': 3,
                  'p90_sentence_len': 5, 'long_sentence_share': .10}


def supported_dimensions(a, b, counts_a, counts_b, ratio_threshold, min_events, min_rate_delta):
    dimensions = []
    for dim, x in a.items():
        y = b[dim]
        if x == y:
            continue
        ratio = None if min(x, y) == 0 else max(x, y) / min(x, y)
        absolute = ABSOLUTE_MINIMA.get(dim, min_rate_delta)
        supported = dim in ABSOLUTE_MINIMA or max(counts_a.get(dim, 0), counts_b.get(dim, 0)) >= min_events
        if supported and abs(x - y) >= absolute and (ratio is None or ratio > ratio_threshold):
            dimensions.append(dim)
    return dimensions


def analyze_units(raw, measure, token_pattern, sentence_count, dimensions, ratio_threshold=3,
                  dims_threshold=3, min_tokens=600, min_events=5, min_rate_delta=10,
                  subsamples=3, min_stability=.8):
    """Independent contiguous windows, equal token count across every unit and window."""
    observations, tokens = [], []
    for text in raw:
        spans = list(token_pattern.finditer(text))
        tokens.append(spans)
        feats = measure(text)
        counts = {d: round(feats[d] * len(spans) / 10000) for d in dimensions if d not in ABSOLUTE_MINIMA}
        observations.append({'tokens': len(spans), 'sentences': sentence_count(text), 'events': counts})
    window_size = min((len(t) // subsamples for t in tokens), default=0)
    adequate = len(raw) >= 2 and all(o['tokens'] >= min_tokens and o['sentences'] >= 20 for o in observations) and window_size >= 100
    full = [measure(text) for text in raw]
    def pair_evidence(features, counts):
        return {(i, j): supported_dimensions(features[i], features[j], counts[i], counts[j],
                                             ratio_threshold, min_events, min_rate_delta)
                for i in range(len(raw)) for j in range(i + 1, len(raw))}
    full_pairs = pair_evidence(full, [o['events'] for o in observations])
    window_pairs = []
    windows = []
    if adequate:
        for k in range(subsamples):
            texts = [text[spans[k * window_size].start():spans[(k + 1) * window_size].start()]
                     if (k + 1) * window_size < len(spans) else text[spans[k * window_size].start():]
                     for text, spans in zip(raw, tokens)]
            feats = [measure(t) for t in texts]
            counts = [{d: round(f[d] * window_size / 10000) for d in dimensions if d not in ABSOLUTE_MINIMA} for f in feats]
            window = pair_evidence(feats, counts)
            window_pairs.append(window)
            windows.append((feats, {pair for pair, dims in window.items() if len(dims) >= dims_threshold}))
    stability = []
    forced = set()
    for pair, exceeded in full_pairs.items():
        proposed_split = len(exceeded) >= dims_threshold
        votes = [len(p[pair]) >= dims_threshold for p in window_pairs]
        agreement = sum(v == proposed_split for v in votes) / len(votes) if votes else 0
        stability.append({'indices': list(pair), 'split': proposed_split, 'agreement': agreement})
        if proposed_split:
            forced.add(pair)
    stable = adequate and all(row['agreement'] >= min_stability for row in stability)
    return observations, full_pairs, forced, {'adequate': adequate, 'stable': stable,
        'subsamples': subsamples, 'tokens_per_subsample': window_size, 'minimum_agreement': min_stability,
        'pairs': stability}, windows
