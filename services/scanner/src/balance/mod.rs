//! Balance checking — replaces V3 engines/balance.py (696 LOC).
//!
//! Uses reqwest for async HTTP to blockchain APIs.

/// Check BTC address balance via Blockstream API.
pub async fn check_btc_balance(_address: &str) -> Result<f64, Box<dyn std::error::Error>> {
    // TODO: Implement with reqwest
    // let url = format!("https://blockstream.info/api/address/{}", address);
    // let resp = reqwest::get(&url).await?.json::<serde_json::Value>().await?;
    Ok(0.0)
}

/// Check ETH address balance via JSON-RPC.
pub async fn check_eth_balance(_address: &str) -> Result<f64, Box<dyn std::error::Error>> {
    // TODO: Implement eth_getBalance RPC call
    Ok(0.0)
}

/// Check ERC-20 token balance.
pub async fn check_token_balance(
    _address: &str,
    _token_contract: &str,
) -> Result<f64, Box<dyn std::error::Error>> {
    // TODO: Implement eth_call with balanceOf selector
    Ok(0.0)
}

/// Batch balance check — only check high-scoring keys to manage rate limits.
pub async fn batch_check(
    _addresses: &[(String, String)], // (address, chain)
    _min_score: f64,
) -> Vec<(String, f64)> {
    // TODO: Implement batched checking with configurable delays
    vec![]
}
