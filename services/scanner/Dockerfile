# NPS V4 Scanner Service — Multi-stage Rust build
# Stage 1: Build
FROM rust:1.75 AS build
WORKDIR /app

# Copy proto files for build
COPY ../../proto/ /proto/

# Copy and build
COPY . .
# TODO: Fix proto path for Docker context
RUN cargo build --release

# Stage 2: Run
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /app/target/release/nps-scanner /app/nps-scanner

EXPOSE 50051

CMD ["/app/nps-scanner"]
