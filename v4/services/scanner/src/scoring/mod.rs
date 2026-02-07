//! Scoring engine — replaces V3 engines/scoring.py (290 LOC).
//!
//! CRITICAL: Must produce identical results to Python Oracle scoring
//! for consistency. Shared test vectors required.

use std::collections::HashMap;

/// Default scoring weights (must match V3 scoring.py exactly).
pub struct ScoringWeights {
    pub numerology_weight: f64,
    pub fc60_weight: f64,
    pub math_weight: f64,
    pub pattern_weight: f64,
}

impl Default for ScoringWeights {
    fn default() -> Self {
        Self {
            numerology_weight: 0.3,
            fc60_weight: 0.25,
            math_weight: 0.25,
            pattern_weight: 0.2,
        }
    }
}

/// Score a key/address pair.
pub fn score_key(
    _private_key: &[u8],
    _address: &str,
    _weights: &ScoringWeights,
) -> f64 {
    // TODO: Implement scoring algorithm matching V3
    // - Numerology reduction of key bytes
    // - FC60 element alignment
    // - Mathematical properties (prime factors, digit sums)
    // - Pattern recognition
    0.0
}

/// Top-N score tracker with LRU cache (replaces V3 logic/key_scorer.py).
pub struct TopScoreTracker {
    pub capacity: usize,
    // TODO: Use BinaryHeap for top-N tracking
    pub scores: Vec<(String, f64)>,
}

impl TopScoreTracker {
    pub fn new(capacity: usize) -> Self {
        Self {
            capacity,
            scores: Vec::with_capacity(capacity),
        }
    }

    pub fn submit(&mut self, address: String, score: f64) -> bool {
        // TODO: Maintain sorted top-N
        if self.scores.len() < self.capacity || score > self.min_score() {
            self.scores.push((address, score));
            self.scores.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
            self.scores.truncate(self.capacity);
            return true;
        }
        false
    }

    pub fn min_score(&self) -> f64 {
        self.scores.last().map(|(_, s)| *s).unwrap_or(0.0)
    }

    pub fn top(&self) -> &[(String, f64)] {
        &self.scores
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_weights_sum_to_one() {
        let w = ScoringWeights::default();
        let sum = w.numerology_weight + w.fc60_weight + w.math_weight + w.pattern_weight;
        assert!((sum - 1.0).abs() < 1e-10);
    }
}
