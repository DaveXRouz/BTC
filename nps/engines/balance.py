"""
Multi-chain balance checking for NPS.

BTC via Blockstream API, ETH via public RPC endpoints,
ERC-20 tokens via eth_call with balanceOf selector.
All network calls have timeout=10 and fail gracefully.
"""

import http.client
import json
import logging
import ssl
import time
import urllib.request
import urllib.error
import urllib.parse

# SSL context — macOS Python often lacks system CA certs
try:
    import certifi

    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _ssl_ctx = ssl._create_unverified_context()

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# BTC Balance Checking (Blockstream API)
# ════════════════════════════════════════════════════════════

_BTC_API = "https://blockstream.info/api"
_btc_last_call = 0.0


def _fetch_json(endpoint, timeout=10):
    """Fetch JSON from a URL. Returns dict or None on error."""
    try:
        req = urllib.request.Request(endpoint, headers={"User-Agent": "NPS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.debug(f"Fetch failed: {endpoint}: {e}")
        return None


def _btc_rate_limit():
    """Enforce BTC API rate limit."""
    global _btc_last_call
    try:
        from engines.config import get

        delay = get("balance_check.btc_delay", 0.5)
    except Exception:
        delay = 0.5
    elapsed = time.time() - _btc_last_call
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _btc_last_call = time.time()


def check_balance(address):
    """Check BTC balance for an address. Returns result dict."""
    _btc_rate_limit()
    data = _fetch_json(f"{_BTC_API}/address/{address}")
    if data is None:
        return {"success": False, "error": "API request failed", "address": address}

    funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
    spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
    balance_sat = funded - spent
    balance_btc = balance_sat / 1e8

    tx_count = data.get("chain_stats", {}).get("tx_count", 0)

    return {
        "success": True,
        "address": address,
        "balance_sat": balance_sat,
        "balance_btc": balance_btc,
        "has_balance": balance_sat > 0,
        "tx_count": tx_count,
        "funded_sum": funded,
        "spent_sum": spent,
        "funded_sum_sat": funded,
        "spent_sum_sat": spent,
        "has_history": tx_count > 0,
        "error": None,
    }


def check_balance_batch(addresses, delay=None):
    """Check balances for a list of BTC addresses."""
    results = []
    for addr in addresses:
        results.append(check_balance(addr))
    return results


def has_any_activity(address):
    """Quick check if address has ever had any transactions."""
    _btc_rate_limit()
    data = _fetch_json(f"{_BTC_API}/address/{address}")
    if data is None:
        return False
    tx_count = data.get("chain_stats", {}).get("tx_count", 0)
    return tx_count > 0


def get_utxos(address):
    """Get unspent transaction outputs for an address."""
    _btc_rate_limit()
    data = _fetch_json(f"{_BTC_API}/address/{address}/utxo")
    if data is None:
        return []
    return data


# ════════════════════════════════════════════════════════════
# ETH Balance Checking (Public RPC)
# ════════════════════════════════════════════════════════════

ETH_RPC_ENDPOINTS = [
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
]

# ERC-20 token contracts (Ethereum mainnet)
ERC20_TOKENS = {
    "USDT": {
        "contract": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "name": "Tether USD",
        "decimals": 6,
    },
    "USDC": {
        "contract": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "name": "USD Coin",
        "decimals": 6,
    },
    "DAI": {
        "contract": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "name": "Dai Stablecoin",
        "decimals": 18,
    },
    "WBTC": {
        "contract": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "name": "Wrapped BTC",
        "decimals": 8,
    },
    "WETH": {
        "contract": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "name": "Wrapped Ether",
        "decimals": 18,
    },
    "UNI": {
        "contract": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "name": "Uniswap",
        "decimals": 18,
    },
    "LINK": {
        "contract": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
        "name": "Chainlink",
        "decimals": 18,
    },
    "SHIB": {
        "contract": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
        "name": "Shiba Inu",
        "decimals": 18,
    },
}

# ════════════════════════════════════════════════════════════
# BSC Balance Checking (BNB Smart Chain)
# ════════════════════════════════════════════════════════════

BSC_RPC_ENDPOINTS = [
    "https://bsc-dataseed.binance.org",
    "https://bsc-dataseed1.defibit.io",
    "https://bsc.publicnode.com",
]

BSC_TOKENS = {
    "BUSD": {
        "contract": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
        "name": "Binance USD",
        "decimals": 18,
    },
    "CAKE": {
        "contract": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        "name": "PancakeSwap",
        "decimals": 18,
    },
}

# ════════════════════════════════════════════════════════════
# Polygon Balance Checking
# ════════════════════════════════════════════════════════════

POLYGON_RPC_ENDPOINTS = [
    "https://polygon-rpc.com",
    "https://polygon.publicnode.com",
    "https://rpc.ankr.com/polygon",
]

_eth_rpc_index = 0
_eth_last_call = 0.0


def _eth_rate_limit(delay_key="balance_check.eth_delay", default=0.3):
    """Enforce ETH RPC rate limit."""
    global _eth_last_call
    try:
        from engines.config import get

        delay = get(delay_key, default)
    except Exception:
        delay = default
    elapsed = time.time() - _eth_last_call
    if elapsed < delay:
        time.sleep(delay - elapsed)
    _eth_last_call = time.time()


def _eth_rpc_call(method, params, timeout=10):
    """Make an ETH JSON-RPC call with round-robin endpoint selection."""
    global _eth_rpc_index

    try:
        from engines.config import get

        endpoints = get("balance_check.eth_rpc_endpoints", ETH_RPC_ENDPOINTS)
    except Exception:
        endpoints = ETH_RPC_ENDPOINTS

    if not endpoints:
        return None

    endpoint = endpoints[_eth_rpc_index % len(endpoints)]
    _eth_rpc_index += 1

    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "NPS/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("result")
    except Exception as e:
        logger.debug(f"ETH RPC failed ({endpoint}): {e}")
        return None


def check_eth_balance(address):
    """Check ETH balance for an address. Returns result dict."""
    _eth_rate_limit()
    result = _eth_rpc_call("eth_getBalance", [address, "latest"])

    if result is None:
        return {"success": False, "error": "RPC request failed", "address": address}

    try:
        balance_wei = int(result, 16)
        balance_eth = balance_wei / 1e18
    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid response", "address": address}

    return {
        "success": True,
        "address": address,
        "balance_wei": balance_wei,
        "balance_eth": balance_eth,
        "has_balance": balance_wei > 0,
        "error": None,
    }


def check_erc20_balance(address, token_symbol):
    """Check ERC-20 token balance for an address."""
    token_info = ERC20_TOKENS.get(token_symbol.upper())
    if not token_info:
        return {
            "success": False,
            "error": f"Unknown token: {token_symbol}",
            "address": address,
        }

    contract = token_info["contract"]
    _eth_rate_limit("balance_check.erc20_delay", 0.2)

    # balanceOf(address) selector: 0x70a08231
    # Pad address to 32 bytes (remove 0x prefix, left-pad to 64 hex chars)
    addr_stripped = address.lower().replace("0x", "").zfill(64)
    call_data = "0x70a08231" + addr_stripped

    result = _eth_rpc_call(
        "eth_call",
        [
            {"to": contract, "data": call_data},
            "latest",
        ],
    )

    if result is None:
        return {
            "success": False,
            "error": "RPC request failed",
            "address": address,
            "token": token_symbol,
        }

    try:
        balance_raw = int(result, 16)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": "Invalid response",
            "address": address,
            "token": token_symbol,
        }

    decimals = token_info.get("decimals", 18)
    balance = balance_raw / (10**decimals)

    return {
        "success": True,
        "address": address,
        "token": token_symbol.upper(),
        "balance_raw": balance_raw,
        "balance": balance,
        "balance_human": balance,
        "token_name": token_info.get("name", token_symbol.upper()),
        "has_balance": balance_raw > 0,
        "error": None,
    }


# ════════════════════════════════════════════════════════════
# Multi-Chain Combined Check
# ════════════════════════════════════════════════════════════


def _evm_rpc_call(method, params, endpoints, timeout=10):
    """Make a JSON-RPC call to an EVM-compatible chain."""
    if not endpoints:
        return None

    endpoint = endpoints[0]
    payload = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    ).encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "NPS/1.0"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("result")
    except Exception as e:
        logger.debug(f"EVM RPC failed ({endpoint}): {e}")
        return None


def check_bsc_balance(address):
    """Check BNB balance on BSC. Returns result dict."""
    _eth_rate_limit()
    raw = _evm_rpc_call("eth_getBalance", [address, "latest"], BSC_RPC_ENDPOINTS)
    if raw is None:
        return {"success": False, "error": "BSC RPC failed", "address": address}

    try:
        balance_wei = int(raw, 16)
        balance_bnb = balance_wei / 1e18
        return {
            "success": True,
            "address": address,
            "balance_wei": balance_wei,
            "balance_bnb": balance_bnb,
            "has_balance": balance_wei > 0,
            "error": None,
        }
    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid response", "address": address}


def check_polygon_balance(address):
    """Check MATIC/POL balance on Polygon. Returns result dict."""
    _eth_rate_limit()
    raw = _evm_rpc_call("eth_getBalance", [address, "latest"], POLYGON_RPC_ENDPOINTS)
    if raw is None:
        return {"success": False, "error": "Polygon RPC failed", "address": address}

    try:
        balance_wei = int(raw, 16)
        balance_matic = balance_wei / 1e18
        return {
            "success": True,
            "address": address,
            "balance_wei": balance_wei,
            "balance_matic": balance_matic,
            "has_balance": balance_wei > 0,
            "error": None,
        }
    except (ValueError, TypeError):
        return {"success": False, "error": "Invalid response", "address": address}


def check_all_balances(btc_address=None, eth_address=None, tokens=None, chains=None):
    """Check balances across all configured chains. Returns combined result dict."""
    if tokens is None:
        try:
            from engines.config import get

            tokens = get("balance_check.tokens_to_check", ["USDT", "USDC"])
        except Exception:
            tokens = ["USDT", "USDC"]

    if chains is None:
        chains = ["btc", "eth"]

    result = {
        "success": True,
        "btc": None,
        "eth": None,
        "bsc": None,
        "polygon": None,
        "tokens": {},
        "has_any_balance": False,
    }

    if btc_address and "btc" in chains:
        btc_result = check_balance(btc_address)
        result["btc"] = btc_result
        if btc_result.get("has_balance"):
            result["has_any_balance"] = True

    if eth_address and "eth" in chains:
        eth_result = check_eth_balance(eth_address)
        result["eth"] = eth_result
        if eth_result.get("has_balance"):
            result["has_any_balance"] = True

        # Check ERC-20 tokens
        for token in tokens:
            token_result = check_erc20_balance(eth_address, token)
            result["tokens"][token] = token_result
            if token_result.get("has_balance"):
                result["has_any_balance"] = True

    if eth_address and "bsc" in chains:
        bsc_result = check_bsc_balance(eth_address)
        result["bsc"] = bsc_result
        if bsc_result.get("has_balance"):
            result["has_any_balance"] = True

    if eth_address and "polygon" in chains:
        polygon_result = check_polygon_balance(eth_address)
        result["polygon"] = polygon_result
        if polygon_result.get("has_balance"):
            result["has_any_balance"] = True

    return result


# ════════════════════════════════════════════════════════════
# Batch Balance Checking with Connection Reuse
# ════════════════════════════════════════════════════════════


def _fetch_with_retry(host, path, max_retries=3, timeout=10):
    """Fetch JSON using persistent HTTP connection with exponential backoff retry.

    Parameters
    ----------
    host : str
        Hostname to connect to (e.g. 'blockstream.info').
    path : str
        URL path (e.g. '/api/address/1A...').
    max_retries : int
        Maximum number of retry attempts.
    timeout : int
        Connection and read timeout in seconds.

    Returns
    -------
    dict or None
        Parsed JSON response, or None on failure.
    """
    conn = None
    for attempt in range(max_retries):
        try:
            conn = http.client.HTTPSConnection(host, timeout=timeout, context=_ssl_ctx)
            conn.request("GET", path, headers={"User-Agent": "NPS/1.0"})
            resp = conn.getresponse()
            body = resp.read().decode("utf-8")
            if resp.status == 200:
                return json.loads(body)
            logger.debug(
                f"_fetch_with_retry {host}{path} status={resp.status} attempt={attempt + 1}"
            )
        except Exception as e:
            logger.debug(
                f"_fetch_with_retry {host}{path} error={e} attempt={attempt + 1}"
            )
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None

        # Exponential backoff: 1s, 2s, 4s
        if attempt < max_retries - 1:
            time.sleep(2**attempt)

    return None


def batch_check_balances(addresses, chains=None):
    """Check balances for multiple addresses using connection reuse.

    Parameters
    ----------
    addresses : list[dict]
        Each dict has optional keys: 'btc', 'eth'. E.g. [{"btc": "1A...", "eth": "0x..."}, ...]
    chains : list[str] or None
        Chains to check. Default: ["btc", "eth"]

    Returns
    -------
    list[dict]
        Results for each address dict. Each result dict has keys 'btc' and/or 'eth'
        matching the requested chains.
    """
    if chains is None:
        chains = ["btc", "eth"]

    chains = [c.lower() for c in chains]
    results = []

    # Process BTC addresses using persistent connection via _fetch_with_retry
    btc_host = "blockstream.info"
    btc_path_prefix = "/api/address/"

    # Pre-extract ETH RPC endpoint info
    eth_host = None
    eth_path = "/"
    eth_use_ssl = True
    if "eth" in chains:
        try:
            from engines.config import get as cfg_get

            endpoints = cfg_get("balance_check.eth_rpc_endpoints", ETH_RPC_ENDPOINTS)
        except Exception:
            endpoints = ETH_RPC_ENDPOINTS

        if endpoints:
            parsed = urllib.parse.urlparse(endpoints[0])
            eth_host = parsed.hostname
            eth_path = parsed.path or "/"
            eth_use_ssl = parsed.scheme == "https"

    for addr_dict in addresses:
        entry = {}

        # ── BTC ──
        if "btc" in chains and "btc" in addr_dict and addr_dict["btc"]:
            _btc_rate_limit()
            btc_addr = addr_dict["btc"]
            data = _fetch_with_retry(btc_host, f"{btc_path_prefix}{btc_addr}")
            if data is None:
                entry["btc"] = {
                    "success": False,
                    "error": "API request failed",
                    "address": btc_addr,
                }
            else:
                funded = data.get("chain_stats", {}).get("funded_txo_sum", 0)
                spent = data.get("chain_stats", {}).get("spent_txo_sum", 0)
                balance_sat = funded - spent
                balance_btc = balance_sat / 1e8
                tx_count = data.get("chain_stats", {}).get("tx_count", 0)
                entry["btc"] = {
                    "success": True,
                    "address": btc_addr,
                    "balance_sat": balance_sat,
                    "balance_btc": balance_btc,
                    "has_balance": balance_sat > 0,
                    "tx_count": tx_count,
                    "funded_sum_sat": funded,
                    "spent_sum_sat": spent,
                    "has_history": tx_count > 0,
                    "error": None,
                }

        # ── ETH ──
        if "eth" in chains and "eth" in addr_dict and addr_dict["eth"] and eth_host:
            _eth_rate_limit()
            eth_addr = addr_dict["eth"]
            payload = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [eth_addr, "latest"],
                    "id": 1,
                }
            ).encode("utf-8")

            eth_result = None
            conn = None
            for attempt in range(3):
                try:
                    if eth_use_ssl:
                        conn = http.client.HTTPSConnection(
                            eth_host, timeout=10, context=_ssl_ctx
                        )
                    else:
                        conn = http.client.HTTPConnection(eth_host, timeout=10)
                    conn.request(
                        "POST",
                        eth_path,
                        body=payload,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "NPS/1.0",
                        },
                    )
                    resp = conn.getresponse()
                    body = resp.read().decode("utf-8")
                    if resp.status == 200:
                        eth_result = json.loads(body).get("result")
                        break
                except Exception as e:
                    logger.debug(
                        f"batch ETH {eth_addr} error={e} attempt={attempt + 1}"
                    )
                finally:
                    if conn is not None:
                        try:
                            conn.close()
                        except Exception:
                            pass
                        conn = None

                if attempt < 2:
                    time.sleep(2**attempt)

            if eth_result is None:
                entry["eth"] = {
                    "success": False,
                    "error": "RPC request failed",
                    "address": eth_addr,
                }
            else:
                try:
                    balance_wei = int(eth_result, 16)
                    balance_eth = balance_wei / 1e18
                    entry["eth"] = {
                        "success": True,
                        "address": eth_addr,
                        "balance_wei": balance_wei,
                        "balance_eth": balance_eth,
                        "has_balance": balance_wei > 0,
                        "error": None,
                    }
                except (ValueError, TypeError):
                    entry["eth"] = {
                        "success": False,
                        "error": "Invalid response",
                        "address": eth_addr,
                    }

        results.append(entry)

    return results
