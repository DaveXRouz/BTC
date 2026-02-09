//! NPS Scanner Service — High-performance key scanner.
//!
//! Targets 5000+ keys/sec using secp256k1, bip39, and multi-threaded scanning.
//! Exposes a gRPC API for control by the FastAPI gateway.

mod crypto;
mod scanner;
mod balance;
mod scoring;
mod grpc;

use tracing_subscriber;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize structured logging
    tracing_subscriber::fmt()
        .json()
        .init();

    tracing::info!("NPS Scanner Service v4.0.0 starting...");

    // TODO: Load configuration from environment
    let grpc_addr = "0.0.0.0:50051".parse()?;

    // TODO: Start gRPC server
    tracing::info!("gRPC server listening on {}", grpc_addr);
    // grpc::serve(grpc_addr).await?;

    // Placeholder — keep running
    tracing::info!("Scanner service ready (stub mode)");
    tokio::signal::ctrl_c().await?;

    Ok(())
}
