//! Scanner loop — replaces V3 solvers/unified_solver.py (546 LOC).
//!
//! Multi-threaded key generation and balance checking.

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;

/// Scan session state.
pub struct ScanSession {
    pub session_id: String,
    pub running: Arc<AtomicBool>,
    pub paused: Arc<AtomicBool>,
    pub keys_tested: Arc<AtomicU64>,
    pub seeds_tested: Arc<AtomicU64>,
    pub hits: Arc<AtomicU64>,
}

impl ScanSession {
    pub fn new(session_id: String) -> Self {
        Self {
            session_id,
            running: Arc::new(AtomicBool::new(false)),
            paused: Arc::new(AtomicBool::new(false)),
            keys_tested: Arc::new(AtomicU64::new(0)),
            seeds_tested: Arc::new(AtomicU64::new(0)),
            hits: Arc::new(AtomicU64::new(0)),
        }
    }

    pub fn start(&self) {
        self.running.store(true, Ordering::SeqCst);
        // TODO: Spawn worker threads for key generation
        // TODO: Worker loop: generate key -> derive addresses -> score -> check balance
    }

    pub fn stop(&self) {
        self.running.store(false, Ordering::SeqCst);
    }

    pub fn pause(&self) {
        self.paused.store(true, Ordering::SeqCst);
    }

    pub fn resume(&self) {
        self.paused.store(false, Ordering::SeqCst);
    }

    pub fn keys_per_second(&self) -> f64 {
        // TODO: Calculate from elapsed time
        0.0
    }
}

/// Checkpoint data for resume capability.
pub struct Checkpoint {
    pub session_id: String,
    pub keys_tested: u64,
    pub last_key: Vec<u8>,
    // TODO: Add range tracking, coverage data
}

impl Checkpoint {
    /// Save checkpoint to disk or DB.
    pub fn save(&self) -> Result<(), Box<dyn std::error::Error>> {
        // TODO: Serialize and save
        Ok(())
    }

    /// Load checkpoint from disk or DB.
    pub fn load(_checkpoint_id: &str) -> Result<Self, Box<dyn std::error::Error>> {
        // TODO: Deserialize and load
        Err("Not implemented".into())
    }
}
