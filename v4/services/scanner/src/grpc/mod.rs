//! gRPC server implementation for the Scanner service.
//!
//! Implements scanner.proto ScannerService.

// TODO: Include generated protobuf code
// pub mod scanner_proto {
//     tonic::include_proto!("nps.scanner");
// }

// TODO: Implement ScannerService trait
// #[tonic::async_trait]
// impl scanner_proto::scanner_service_server::ScannerService for ScannerServiceImpl {
//     async fn start_scan(...) -> ... { }
//     async fn stop_scan(...) -> ... { }
//     async fn pause_scan(...) -> ... { }
//     async fn resume_scan(...) -> ... { }
//     async fn get_stats(...) -> ... { }
//     async fn save_checkpoint(...) -> ... { }
//     async fn resume_from_checkpoint(...) -> ... { }
//     async fn list_sessions(...) -> ... { }
//     type StreamEventsStream = ...;
//     async fn stream_events(...) -> ... { }
// }

/// Start the gRPC server.
pub async fn serve(
    _addr: std::net::SocketAddr,
) -> Result<(), Box<dyn std::error::Error>> {
    // TODO: Build and start tonic server
    // let service = ScannerServiceImpl::new();
    // tonic::transport::Server::builder()
    //     .add_service(scanner_proto::scanner_service_server::ScannerServiceServer::new(service))
    //     .serve(addr)
    //     .await?;
    Ok(())
}
