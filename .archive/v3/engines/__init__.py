"""NPS Engine Layer — FC60, Numerology, Math Analysis, Crypto, Scoring, Learning."""

# Re-export key functions for convenient access
from engines.fc60 import token60, encode_fc60, format_full_output, parse_input, self_test
from engines.numerology import life_path, name_to_number, numerology_reduce, personal_year
from engines.math_analysis import math_profile, entropy
from engines.scoring import hybrid_score, score_batch
