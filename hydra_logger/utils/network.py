"""
Network Utility Functions for Hydra-Logger

This module provides comprehensive network utility functions including
connection testing, URL processing, IP validation, and network monitoring.
It supports various protocols and provides detailed network diagnostics.

ARCHITECTURE:
- SyncNetworkUtils: Synchronous network utility functions
- AsyncNetworkUtils: Asynchronous network utility functions
- URLProcessor: URL parsing, building, and validation (sync/async)
- IPValidator: IP address validation and analysis
- ConnectionTester: Connection testing and diagnostics (sync/async)
- NetworkMonitor: Network monitoring and performance tracking (sync/async)

FEATURES:
- Both synchronous and asynchronous implementations
- Concurrent connection testing and monitoring
- Batch operations for multiple endpoints
- Connection pooling and management
- Comprehensive error handling and retry mechanisms
- Performance metrics and monitoring
- URL processing and validation
- IP address analysis and validation

SYNC USAGE:
    from hydra_logger.utils import SyncNetworkUtils, URLProcessor, IPValidator
    
    # Synchronous network utilities
    local_ip = SyncNetworkUtils.get_local_ip()
    hostname = SyncNetworkUtils.get_hostname()
    is_open = SyncNetworkUtils.is_port_open("example.com", 80)
    
    # Connection testing
    from hydra_logger.utils import ConnectionTester
    tester = ConnectionTester(timeout=10.0)
    result = tester.test_tcp_connection("example.com", 80)

ASYNC USAGE:
    from hydra_logger.utils import AsyncNetworkUtils, AsyncConnectionTester
    
    # Asynchronous network utilities
    local_ip = await AsyncNetworkUtils.get_local_ip()
    hostname = await AsyncNetworkUtils.get_hostname()
    is_open = await AsyncNetworkUtils.is_port_open("example.com", 80)
    
    # Concurrent connection testing
    tester = AsyncConnectionTester(timeout=10.0)
    results = await tester.test_multiple_connections([
        ("example.com", 80),
        ("google.com", 443),
        ("github.com", 22)
    ])
    
    # URL processing (works with both sync and async)
    parsed = URLProcessor.parse_url("https://example.com/path?param=value")
    domain = URLProcessor.extract_domain("https://example.com/path")
    
    # IP validation
    is_valid = IPValidator.is_valid_ip("192.168.1.1")
    is_private = IPValidator.is_private_ip("192.168.1.1")
"""

import socket
import urllib.parse
import ipaddress
import re
import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
import ssl
import time
import os

# Optional async dependencies
try:
    import aiohttp  # type: ignore[import-untyped]
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import aiofiles  # type: ignore[import-untyped]
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False


class Protocol(Enum):
    """Network protocols."""

    HTTP = "http"   # Hypertext Transfer Protocol
    HTTPS = "https" # Hypertext Transfer Protocol Secure
    FTP = "ftp"     # File Transfer Protocol
    SFTP = "sftp"   # Secure File Transfer Protocol
    SSH = "ssh"     # Secure Shell
    TCP = "tcp"     # Transmission Control Protocol
    UDP = "udp"     # User Datagram Protocol
    ICMP = "icmp"   # Internet Control Message Protocol


class ConnectionStatus(Enum):
    """Connection status values."""

    SUCCESS = "success"
    TIMEOUT = "timeout"
    REFUSED = "refused"
    UNREACHABLE = "unreachable"
    INVALID = "invalid"
    ERROR = "error"


@dataclass
class NetworkEndpoint:
    """Network endpoint information."""

    host: str
    port: int
    protocol: Protocol

    def __str__(self) -> str:
        """String representation of endpoint."""
        return f"{self.protocol.value}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert endpoint to dictionary."""
        return {"host": self.host, "port": self.port, "protocol": self.protocol.value}


@dataclass
class ConnectionResult:
    """Result of a connection test."""

    endpoint: NetworkEndpoint
    status: ConnectionStatus
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "endpoint": self.endpoint.to_dict(),
            "status": self.status.value,
            "response_time": self.response_time,
            "error_message": self.error_message,
            "details": self.details,
        }


class SyncNetworkUtils:
    """Synchronous network utility functions."""

    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address."""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def get_hostname() -> str:
        """Get local hostname."""
        return socket.gethostname()

    @staticmethod
    def resolve_hostname(hostname: str) -> List[str]:
        """Resolve hostname to IP addresses."""
        try:
            return [addr[4][0] for addr in socket.getaddrinfo(hostname, None)]
        except Exception:
            return []

    @staticmethod
    def reverse_dns_lookup(ip_address: str) -> Optional[str]:
        """Perform reverse DNS lookup."""
        try:
            return socket.gethostbyaddr(ip_address)[0]
        except Exception:
            return None

    @staticmethod
    def is_port_open(host: str, port: int, timeout: float = 5.0) -> bool:
        """Check if a port is open on a host."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((host, port))
                return result == 0
        except Exception:
            return False

    @staticmethod
    def scan_ports(
        host: str, start_port: int = 1, end_port: int = 1024, timeout: float = 1.0
    ) -> List[int]:
        """Scan a range of ports on a host."""
        open_ports = []

        for port in range(start_port, end_port + 1):
            if SyncNetworkUtils.is_port_open(host, port, timeout):
                open_ports.append(port)

        return open_ports

    @staticmethod
    def ping_host(host: str, count: int = 4, timeout: float = 5.0) -> Dict[str, Any]:
        """Ping a host and return statistics."""
        import subprocess
        import platform

        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(int(timeout)), host]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout + 5
            )

            if result.returncode == 0:
                # Parse ping output
                lines = result.stdout.split("\n")
                times = []

                for line in lines:
                    if "time=" in line or "time<" in line:
                        time_match = re.search(r"time[=<>](\d+(?:\.\d+)?)", line)
                        if time_match:
                            times.append(float(time_match.group(1)))

                if times:
                    return {
                        "host": host,
                        "success": True,
                        "packets_sent": count,
                        "packets_received": len(times),
                        "packet_loss": (count - len(times)) / count * 100,
                        "min_time": min(times),
                        "max_time": max(times),
                        "avg_time": sum(times) / len(times),
                    }

            return {
                "host": host,
                "success": False,
                "error": result.stderr or "Unknown error",
            }

        except subprocess.TimeoutExpired:
            return {"host": host, "success": False, "error": "Timeout"}
        except Exception as e:
            return {"host": host, "success": False, "error": str(e)}

    @staticmethod
    def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
        """Get information about network interfaces."""
        interfaces = {}

        try:
            for interface_name, interface_addresses in socket.getaddrinfo("", None):
                if interface_name[0] not in interfaces:
                    interfaces[interface_name[0]] = {
                        "family": interface_name[0],
                        "addresses": [],
                    }

                interfaces[interface_name[0]]["addresses"].append(
                    {"address": interface_addresses[0], "port": interface_addresses[1]}
                )
        except Exception:
            pass

        return interfaces

    @staticmethod
    def is_valid_hostname(hostname: str) -> bool:
        """Check if a hostname is valid."""
        if not hostname or len(hostname) > 253:
            return False
        
        # Check if it's a valid IP address first
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass
        
        # Check hostname format
        if hostname.startswith('.') or hostname.endswith('.'):
            return False
        
        # Check each label
        labels = hostname.split('.')
        for label in labels:
            if not label or len(label) > 63:
                return False
            if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', label):
                return False
        
        return True

    @staticmethod
    def is_valid_port(port: int) -> bool:
        """Check if a port number is valid."""
        return isinstance(port, int) and 1 <= port <= 65535

    @staticmethod
    def test_connection(endpoint: NetworkEndpoint, timeout: float = 5.0) -> ConnectionResult:
        """Test connection to a network endpoint."""
        start_time = time.time()
        
        try:
            if endpoint.protocol in [Protocol.HTTP, Protocol.HTTPS]:
                # Test HTTP/HTTPS connection
                try:
                    response = requests.head(
                        f"{endpoint.protocol.value}://{endpoint.host}:{endpoint.port}",
                        timeout=timeout,
                        allow_redirects=False
                    )
                    response_time = time.time() - start_time
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.SUCCESS,
                        response_time=response_time,
                        details={"status_code": response.status_code}
                    )
                except requests.exceptions.Timeout:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.TIMEOUT,
                        response_time=timeout,
                        error_message="Connection timeout"
                    )
                except requests.exceptions.ConnectionError:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.REFUSED,
                        response_time=time.time() - start_time,
                        error_message="Connection refused"
                    )
                except Exception as e:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.ERROR,
                        response_time=time.time() - start_time,
                        error_message=str(e)
                    )
            
            elif endpoint.protocol in [Protocol.TCP, Protocol.UDP]:
                # Test TCP/UDP connection
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(timeout)
                        result = s.connect_ex((endpoint.host, endpoint.port))
                        response_time = time.time() - start_time
                        
                        if result == 0:
                            return ConnectionResult(
                                endpoint=endpoint,
                                status=ConnectionStatus.SUCCESS,
                                response_time=response_time
                            )
                        else:
                            return ConnectionResult(
                                endpoint=endpoint,
                                status=ConnectionStatus.REFUSED,
                                response_time=response_time,
                                error_message=f"Connection failed with error code {result}"
                            )
                except socket.timeout:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.TIMEOUT,
                        response_time=timeout,
                        error_message="Socket timeout"
                    )
                except Exception as e:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.ERROR,
                        response_time=time.time() - start_time,
                        error_message=str(e)
                    )
            
            else:
                # Unsupported protocol
                return ConnectionResult(
                    endpoint=endpoint,
                    status=ConnectionStatus.INVALID,
                    response_time=time.time() - start_time,
                    error_message=f"Unsupported protocol: {endpoint.protocol.value}"
                )
                
        except Exception as e:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.ERROR,
                response_time=time.time() - start_time,
                error_message=str(e)
            )


class AsyncNetworkUtils:
    """Asynchronous network utility functions."""
    
    @staticmethod
    async def get_local_ip() -> str:
        """Get local IP address asynchronously."""
        try:
            # Use asyncio to run the socket operation in a thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.get_local_ip)
        except Exception:
            return "127.0.0.1"
    
    @staticmethod
    async def get_hostname() -> str:
        """Get local hostname asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.get_hostname)
        except Exception:
            return "localhost"
    
    @staticmethod
    async def resolve_hostname(hostname: str) -> List[str]:
        """Resolve hostname to IP addresses asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.resolve_hostname, hostname)
        except Exception:
            return []
    
    @staticmethod
    async def reverse_dns_lookup(ip_address: str) -> Optional[str]:
        """Perform reverse DNS lookup asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.reverse_dns_lookup, ip_address)
        except Exception:
            return None
    
    @staticmethod
    async def is_port_open(host: str, port: int, timeout: float = 5.0) -> bool:
        """Check if a port is open on a host asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.is_port_open, host, port, timeout)
        except Exception:
            return False
    
    @staticmethod
    async def scan_ports(
        host: str, start_port: int = 1, end_port: int = 1024, timeout: float = 1.0
    ) -> List[int]:
        """Scan a range of ports on a host asynchronously."""
        open_ports = []
        
        # Create tasks for concurrent port scanning
        tasks = []
        for port in range(start_port, end_port + 1):
            task = AsyncNetworkUtils.is_port_open(host, port, timeout)
            tasks.append((port, task))
        
        # Execute all port checks concurrently
        for port, task in tasks:
            try:
                is_open = await task
                if is_open:
                    open_ports.append(port)
            except Exception:
                continue
        
        return open_ports
    
    @staticmethod
    async def ping_host(host: str, count: int = 4, timeout: float = 5.0) -> Dict[str, Any]:
        """Ping a host and return statistics asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.ping_host, host, count, timeout)
        except Exception as e:
            return {"host": host, "success": False, "error": str(e)}
    
    @staticmethod
    async def get_network_interfaces() -> Dict[str, Dict[str, Any]]:
        """Get information about network interfaces asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.get_network_interfaces)
        except Exception:
            return {}
    
    @staticmethod
    async def is_valid_hostname(hostname: str) -> bool:
        """Check if a hostname is valid asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, SyncNetworkUtils.is_valid_hostname, hostname)
        except Exception:
            return False
    
    @staticmethod
    async def is_valid_port(port: int) -> bool:
        """Check if a port number is valid asynchronously."""
        return SyncNetworkUtils.is_valid_port(port)
    
    @staticmethod
    async def test_connection(endpoint: NetworkEndpoint, timeout: float = 5.0) -> ConnectionResult:
        """Test connection to a network endpoint asynchronously."""
        try:
            if endpoint.protocol in [Protocol.HTTP, Protocol.HTTPS]:
                # Test HTTP/HTTPS connection asynchronously
                if not HAS_AIOHTTP:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.ERROR,
                        response_time=time.time() - time.time(),
                        error_message="aiohttp not available - install with: pip install aiohttp"
                    )
                
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                        url = f"{endpoint.protocol.value}://{endpoint.host}:{endpoint.port}"
                        start_time = time.time()
                        
                        async with session.head(url, allow_redirects=False) as response:
                            response_time = time.time() - start_time
                            return ConnectionResult(
                                endpoint=endpoint,
                                status=ConnectionStatus.SUCCESS,
                                response_time=response_time,
                                details={"status_code": response.status}
                            )
                except asyncio.TimeoutError:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.TIMEOUT,
                        response_time=timeout,
                        error_message="Connection timeout"
                    )
                except aiohttp.ClientError as e:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.REFUSED,
                        response_time=time.time() - time.time(),
                        error_message=f"Connection error: {str(e)}"
                    )
                except Exception as e:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.ERROR,
                        response_time=time.time() - time.time(),
                        error_message=str(e)
                    )
            
            elif endpoint.protocol in [Protocol.TCP, Protocol.UDP]:
                # Test TCP/UDP connection asynchronously
                try:
                    loop = asyncio.get_event_loop()
                    start_time = time.time()
                    
                    # Use asyncio to create socket connection
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(endpoint.host, endpoint.port),
                        timeout=timeout
                    )
                    
                    response_time = time.time() - start_time
                    writer.close()
                    await writer.wait_closed()
                    
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.SUCCESS,
                        response_time=response_time
                    )
                except asyncio.TimeoutError:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.TIMEOUT,
                        response_time=timeout,
                        error_message="Connection timeout"
                    )
                except ConnectionRefusedError:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.REFUSED,
                        response_time=time.time() - time.time(),
                        error_message="Connection refused"
                    )
                except Exception as e:
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.ERROR,
                        response_time=time.time() - time.time(),
                        error_message=str(e)
                    )
            
            else:
                # Unsupported protocol
                return ConnectionResult(
                    endpoint=endpoint,
                    status=ConnectionStatus.INVALID,
                    response_time=time.time() - time.time(),
                    error_message=f"Unsupported protocol: {endpoint.protocol.value}"
                )
                
        except Exception as e:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.ERROR,
                response_time=time.time() - time.time(),
                error_message=str(e)
            )


class URLProcessor:
    """URL processing utilities."""

    @staticmethod
    def parse_url(url: str) -> Dict[str, Any]:
        """Parse URL into components."""
        try:
            parsed = urllib.parse.urlparse(url)
            return {
                "scheme": parsed.scheme,
                "netloc": parsed.netloc,
                "path": parsed.path,
                "params": parsed.params,
                "query": parsed.query,
                "fragment": parsed.fragment,
                "username": parsed.username,
                "password": parsed.password,
                "hostname": parsed.hostname,
                "port": parsed.port,
            }
        except Exception:
            return {}

    @staticmethod
    def build_url(components: Dict[str, Any]) -> str:
        """Build URL from components."""
        try:
            return urllib.parse.urlunparse(
                (
                    components.get("scheme", ""),
                    components.get("netloc", ""),
                    components.get("path", ""),
                    components.get("params", ""),
                    components.get("query", ""),
                    components.get("fragment", ""),
                )
            )
        except Exception:
            return ""

    @staticmethod
    def join_urls(base: str, *parts: str) -> str:
        """Join URL parts."""
        try:
            result = base.rstrip("/")
            for part in parts:
                result += "/" + part.lstrip("/")
            return result
        except Exception:
            return base

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL by removing default ports and normalizing path."""
        try:
            parsed = urllib.parse.urlparse(url)

            # Remove default ports
            if parsed.port:
                if (parsed.scheme == "http" and parsed.port == 80) or (
                    parsed.scheme == "https" and parsed.port == 443
                ):
                    netloc = parsed.hostname
                else:
                    netloc = f"{parsed.hostname}:{parsed.port}"
            else:
                netloc = parsed.hostname

            # Normalize path
            path = os.path.normpath(parsed.path)
            if path.startswith("//"):
                path = "/" + path[2:]

            return urllib.parse.urlunparse(
                (
                    parsed.scheme,
                    netloc,
                    path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        except Exception:
            return url

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urllib.parse.urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.hostname
        except Exception:
            return None

    @staticmethod
    def extract_path(url: str) -> Optional[str]:
        """Extract path from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.path
        except Exception:
            return None

    @staticmethod
    def extract_query_params(url: str) -> Dict[str, List[str]]:
        """Extract query parameters from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return urllib.parse.parse_qs(parsed.query)
        except Exception:
            return {}

    @staticmethod
    def add_query_param(url: str, key: str, value: str) -> str:
        """Add query parameter to URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            query_dict = urllib.parse.parse_qs(parsed.query)
            query_dict[key] = [value]

            new_query = urllib.parse.urlencode(query_dict, doseq=True)
            return urllib.parse.urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )
        except Exception:
            return url


class IPValidator:
    """IP address validation utilities."""

    @staticmethod
    def is_valid_ip(ip_address: str) -> bool:
        """Check if string is a valid IP address."""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_ipv4(ip_address: str) -> bool:
        """Check if string is a valid IPv4 address."""
        try:
            ipaddress.IPv4Address(ip_address)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_ipv6(ip_address: str) -> bool:
        """Check if string is a valid IPv6 address."""
        try:
            ipaddress.IPv6Address(ip_address)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_private_ip(ip_address: str) -> bool:
        """Check if IP address is private."""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private
        except ValueError:
            return False

    @staticmethod
    def is_public_ip(ip_address: str) -> bool:
        """Check if IP address is public."""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_global
        except ValueError:
            return False

    @staticmethod
    def is_loopback_ip(ip_address: str) -> bool:
        """Check if IP address is loopback."""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_loopback
        except ValueError:
            return False

    @staticmethod
    def is_multicast_ip(ip_address: str) -> bool:
        """Check if IP address is multicast."""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_multicast
        except ValueError:
            return False

    @staticmethod
    def get_ip_info(ip_address: str) -> Dict[str, Any]:
        """Get comprehensive information about an IP address."""
        try:
            ip = ipaddress.ip_address(ip_address)

            return {
                "address": str(ip),
                "version": ip.version,
                "is_private": ip.is_private,
                "is_global": ip.is_global,
                "is_loopback": ip.is_loopback,
                "is_multicast": ip.is_multicast,
                "is_link_local": ip.is_link_local,
                "is_unspecified": ip.is_unspecified,
                "is_reserved": ip.is_reserved,
                "reverse_pointer": ip.reverse_pointer,
            }
        except ValueError:
            return {"address": ip_address, "error": "Invalid IP address"}

    @staticmethod
    def ip_to_int(ip_address: str) -> Optional[int]:
        """Convert IP address to integer."""
        try:
            ip = ipaddress.ip_address(ip_address)
            return int(ip)
        except ValueError:
            return None

    @staticmethod
    def int_to_ip(integer: int, version: int = 4) -> Optional[str]:
        """Convert integer to IP address."""
        try:
            if version == 4:
                ip = ipaddress.IPv4Address(integer)
            elif version == 6:
                ip = ipaddress.IPv6Address(integer)
            else:
                return None

            return str(ip)
        except ValueError:
            return None


class ConnectionTester:
    """Connection testing utilities."""

    def __init__(self, timeout: float = 10.0):
        """Initialize connection tester."""
        self.timeout = timeout

    def test_tcp_connection(self, host: str, port: int) -> ConnectionResult:
        """Test TCP connection to host:port."""
        endpoint = NetworkEndpoint(host, port, Protocol.TCP)
        start_time = time.time()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((host, port))

                response_time = time.time() - start_time

                return ConnectionResult(
                    endpoint=endpoint,
                    status=ConnectionStatus.SUCCESS,
                    response_time=response_time,
                )

        except socket.timeout:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.TIMEOUT,
                error_message="Connection timeout",
            )
        except ConnectionRefusedError:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.REFUSED,
                error_message="Connection refused",
            )
        except Exception as e:
            return ConnectionResult(
                endpoint=endpoint, status=ConnectionStatus.ERROR, error_message=str(e)
            )

    def test_http_connection(self, url: str) -> ConnectionResult:
        """Test HTTP connection to URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            protocol = Protocol.HTTPS if parsed.scheme == "https" else Protocol.HTTP

            endpoint = NetworkEndpoint(host, port, protocol)
            start_time = time.time()

            response = requests.get(url, timeout=self.timeout, allow_redirects=False)

            response_time = time.time() - start_time

            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.SUCCESS,
                response_time=response_time,
                details={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                },
            )

        except requests.exceptions.Timeout:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.TIMEOUT,
                error_message="Request timeout",
            )
        except requests.exceptions.ConnectionError:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.REFUSED,
                error_message="Connection error",
            )
        except Exception as e:
            return ConnectionResult(
                endpoint=endpoint, status=ConnectionStatus.ERROR, error_message=str(e)
            )

    def test_ssl_certificate(self, host: str, port: int = 443) -> Dict[str, Any]:
        """Test SSL certificate for host:port."""
        try:
            context = ssl.create_default_context()

            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()

                    return {
                        "host": host,
                        "port": port,
                        "success": True,
                        "subject": dict(x[0] for x in cert["subject"]),
                        "issuer": dict(x[0] for x in cert["issuer"]),
                        "version": cert["version"],
                        "serial_number": cert["serialNumber"],
                        "not_before": cert["notBefore"],
                        "not_after": cert["notAfter"],
                        "san": cert.get("subjectAltName", []),
                        "expires_in_days": (
                            ssl.cert_time_to_seconds(cert["notAfter"]) - time.time()
                        )
                        / 86400,
                    }

        except Exception as e:
            return {"host": host, "port": port, "success": False, "error": str(e)}

    def test_multiple_endpoints(
        self, endpoints: List[NetworkEndpoint]
    ) -> List[ConnectionResult]:
        """Test multiple endpoints."""
        results = []

        for endpoint in endpoints:
            if endpoint.protocol in [Protocol.HTTP, Protocol.HTTPS]:
                url = f"{endpoint.protocol.value}://{endpoint.host}:{endpoint.port}"
                result = self.test_http_connection(url)
            else:
                result = self.test_tcp_connection(endpoint.host, endpoint.port)

            results.append(result)

        return results


class AsyncConnectionTester:
    """Asynchronous connection testing utilities."""
    
    def __init__(self, timeout: float = 10.0):
        """Initialize async connection tester."""
        self.timeout = timeout
    
    async def test_tcp_connection(self, host: str, port: int) -> ConnectionResult:
        """Test TCP connection to host:port asynchronously."""
        endpoint = NetworkEndpoint(host, port, Protocol.TCP)
        start_time = time.time()
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            writer.close()
            await writer.wait_closed()
            
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.SUCCESS,
                response_time=response_time,
            )
            
        except asyncio.TimeoutError:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.TIMEOUT,
                error_message="Connection timeout",
            )
        except ConnectionRefusedError:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.REFUSED,
                error_message="Connection refused",
            )
        except Exception as e:
            return ConnectionResult(
                endpoint=endpoint, status=ConnectionStatus.ERROR, error_message=str(e)
            )
    
    async def test_http_connection(self, url: str) -> ConnectionResult:
        """Test HTTP connection to URL asynchronously."""
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            protocol = Protocol.HTTPS if parsed.scheme == "https" else Protocol.HTTP
            
            endpoint = NetworkEndpoint(host, port, protocol)
            
            if not HAS_AIOHTTP:
                return ConnectionResult(
                    endpoint=endpoint,
                    status=ConnectionStatus.ERROR,
                    response_time=time.time() - time.time(),
                    error_message="aiohttp not available - install with: pip install aiohttp"
                )
            
            start_time = time.time()
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, allow_redirects=False) as response:
                    response_time = time.time() - start_time
                    
                    return ConnectionResult(
                        endpoint=endpoint,
                        status=ConnectionStatus.SUCCESS,
                        response_time=response_time,
                        details={
                            "status_code": response.status,
                            "headers": dict(response.headers),
                        },
                    )
                    
        except asyncio.TimeoutError:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.TIMEOUT,
                error_message="Request timeout",
            )
        except aiohttp.ClientError:
            return ConnectionResult(
                endpoint=endpoint,
                status=ConnectionStatus.REFUSED,
                error_message="Connection error",
            )
        except Exception as e:
            return ConnectionResult(
                endpoint=endpoint, status=ConnectionStatus.ERROR, error_message=str(e)
            )
    
    async def test_ssl_certificate(self, host: str, port: int = 443) -> Dict[str, Any]:
        """Test SSL certificate for host:port asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._test_ssl_cert_sync, host, port)
        except Exception as e:
            return {"host": host, "port": port, "success": False, "error": str(e)}
    
    def _test_ssl_cert_sync(self, host: str, port: int) -> Dict[str, Any]:
        """Synchronous SSL certificate test (run in executor)."""
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    
                    return {
                        "host": host,
                        "port": port,
                        "success": True,
                        "subject": dict(x[0] for x in cert["subject"]),
                        "issuer": dict(x[0] for x in cert["issuer"]),
                        "version": cert["version"],
                        "serial_number": cert["serialNumber"],
                        "not_before": cert["notBefore"],
                        "not_after": cert["notAfter"],
                        "san": cert.get("subjectAltName", []),
                        "expires_in_days": (
                            ssl.cert_time_to_seconds(cert["notAfter"]) - time.time()
                        ) / 86400,
                    }
                    
        except Exception as e:
            return {"host": host, "port": port, "success": False, "error": str(e)}
    
    async def test_multiple_connections(
        self, endpoints: List[Tuple[str, int]]
    ) -> List[ConnectionResult]:
        """Test multiple endpoints concurrently."""
        tasks = []
        for host, port in endpoints:
            task = self.test_tcp_connection(host, port)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def test_multiple_endpoints(
        self, endpoints: List[NetworkEndpoint]
    ) -> List[ConnectionResult]:
        """Test multiple NetworkEndpoint objects concurrently."""
        tasks = []
        for endpoint in endpoints:
            if endpoint.protocol in [Protocol.HTTP, Protocol.HTTPS]:
                url = f"{endpoint.protocol.value}://{endpoint.host}:{endpoint.port}"
                task = self.test_http_connection(url)
            else:
                task = self.test_tcp_connection(endpoint.host, endpoint.port)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)


class SyncNetworkMonitor:
    """Synchronous network monitoring utilities."""

    def __init__(self):
        """Initialize network monitor."""
        self._connection_history = []
        self._performance_metrics = {}

    def monitor_endpoint(
        self, endpoint: NetworkEndpoint, interval: float = 60.0
    ) -> Dict[str, Any]:
        """Monitor network endpoint performance."""
        tester = ConnectionTester()

        # Test connection
        result = tester.test_tcp_connection(endpoint.host, endpoint.port)

        # Store in history
        self._connection_history.append(
            {
                "timestamp": time.time(),
                "endpoint": endpoint.to_dict(),
                "result": result.to_dict(),
            }
        )

        # Keep only last 1000 entries
        if len(self._connection_history) > 1000:
            self._connection_history = self._connection_history[-1000:]

        # Calculate performance metrics
        self._update_performance_metrics(endpoint, result)

        return {
            "current_status": result.to_dict(),
            "performance_metrics": self._performance_metrics.get(str(endpoint), {}),
            "history_summary": self._get_history_summary(endpoint),
        }

    def _update_performance_metrics(
        self, endpoint: NetworkEndpoint, result: ConnectionResult
    ):
        """Update performance metrics for endpoint."""
        endpoint_key = str(endpoint)

        if endpoint_key not in self._performance_metrics:
            self._performance_metrics[endpoint_key] = {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "total_response_time": 0.0,
                "min_response_time": float("inf"),
                "max_response_time": 0.0,
                "last_status": None,
                "last_check": None,
            }

        metrics = self._performance_metrics[endpoint_key]
        metrics["total_tests"] += 1
        metrics["last_check"] = time.time()
        metrics["last_status"] = result.status.value

        if result.status == ConnectionStatus.SUCCESS:
            metrics["successful_tests"] += 1
            if result.response_time:
                metrics["total_response_time"] += result.response_time
                metrics["min_response_time"] = min(
                    metrics["min_response_time"], result.response_time
                )
                metrics["max_response_time"] = max(
                    metrics["max_response_time"], result.response_time
                )
        else:
            metrics["failed_tests"] += 1

        # Calculate averages
        if metrics["successful_tests"] > 0:
            metrics["avg_response_time"] = (
                metrics["total_response_time"] / metrics["successful_tests"]
            )

        # Calculate success rate
        metrics["success_rate"] = (
            metrics["successful_tests"] / metrics["total_tests"] * 100
        )

    def _get_history_summary(self, endpoint: NetworkEndpoint) -> Dict[str, Any]:
        """Get summary of connection history for endpoint."""
        recent_results = [
            entry
            for entry in self._connection_history[-100:]
            if entry["endpoint"] == endpoint.to_dict()
        ]

        if not recent_results:
            return {}

        status_counts = {}
        for entry in recent_results:
            status = entry["result"]["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "recent_tests": len(recent_results),
            "status_distribution": status_counts,
            "last_24h_tests": len(
                [e for e in recent_results if time.time() - e["timestamp"] < 86400]
            ),
        }

    def get_network_summary(self) -> Dict[str, Any]:
        """Get summary of all monitored endpoints."""
        summary = {
            "total_endpoints": len(self._performance_metrics),
            "total_tests": sum(
                m["total_tests"] for m in self._performance_metrics.values()
            ),
            "overall_success_rate": 0.0,
            "endpoint_details": {},
        }

        if summary["total_tests"] > 0:
            total_successful = sum(
                m["successful_tests"] for m in self._performance_metrics.values()
            )
            summary["overall_success_rate"] = (
                total_successful / summary["total_tests"] * 100
            )

        for endpoint_key, metrics in self._performance_metrics.items():
            summary["endpoint_details"][endpoint_key] = {
                "total_tests": metrics["total_tests"],
                "success_rate": metrics["success_rate"],
                "avg_response_time": metrics.get("avg_response_time", 0.0),
                "last_status": metrics["last_status"],
                "last_check": metrics["last_check"],
            }

        return summary

    def export_monitoring_data(
        self, format_type: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """Export monitoring data."""
        export_data = {
            "performance_metrics": self._performance_metrics,
            "connection_history": self._connection_history[-1000:],  # Last 1000 entries
            "summary": self.get_network_summary(),
        }

        if format_type.lower() == "json":
            import json

            return json.dumps(export_data, indent=2, default=str)
        elif format_type.lower() == "dict":
            return export_data
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


class AsyncNetworkMonitor:
    """Asynchronous network monitoring utilities."""
    
    def __init__(self):
        """Initialize async network monitor."""
        self._connection_history = []
        self._performance_metrics = {}
    
    async def monitor_endpoint(
        self, endpoint: NetworkEndpoint, interval: float = 60.0
    ) -> Dict[str, Any]:
        """Monitor network endpoint performance asynchronously."""
        tester = AsyncConnectionTester()
        
        # Test connection
        result = await tester.test_tcp_connection(endpoint.host, endpoint.port)
        
        # Store in history
        self._connection_history.append(
            {
                "timestamp": time.time(),
                "endpoint": endpoint.to_dict(),
                "result": result.to_dict(),
            }
        )
        
        # Keep only last 1000 entries
        if len(self._connection_history) > 1000:
            self._connection_history = self._connection_history[-1000:]
        
        # Calculate performance metrics
        self._update_performance_metrics(endpoint, result)
        
        return {
            "current_status": result.to_dict(),
            "performance_metrics": self._performance_metrics.get(str(endpoint), {}),
            "history_summary": self._get_history_summary(endpoint),
        }
    
    def _update_performance_metrics(
        self, endpoint: NetworkEndpoint, result: ConnectionResult
    ):
        """Update performance metrics for endpoint."""
        endpoint_key = str(endpoint)
        
        if endpoint_key not in self._performance_metrics:
            self._performance_metrics[endpoint_key] = {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0,
                "total_response_time": 0.0,
                "min_response_time": float("inf"),
                "max_response_time": 0.0,
                "last_status": None,
                "last_check": None,
            }
        
        metrics = self._performance_metrics[endpoint_key]
        metrics["total_tests"] += 1
        metrics["last_check"] = time.time()
        metrics["last_status"] = result.status.value
        
        if result.status == ConnectionStatus.SUCCESS:
            metrics["successful_tests"] += 1
            if result.response_time:
                metrics["total_response_time"] += result.response_time
                metrics["min_response_time"] = min(
                    metrics["min_response_time"], result.response_time
                )
                metrics["max_response_time"] = max(
                    metrics["max_response_time"], result.response_time
                )
        else:
            metrics["failed_tests"] += 1
        
        # Calculate averages
        if metrics["successful_tests"] > 0:
            metrics["avg_response_time"] = (
                metrics["total_response_time"] / metrics["successful_tests"]
            )
        
        # Calculate success rate
        metrics["success_rate"] = (
            metrics["successful_tests"] / metrics["total_tests"] * 100
        )
    
    def _get_history_summary(self, endpoint: NetworkEndpoint) -> Dict[str, Any]:
        """Get summary of connection history for endpoint."""
        recent_results = [
            entry
            for entry in self._connection_history[-100:]
            if entry["endpoint"] == endpoint.to_dict()
        ]
        
        if not recent_results:
            return {}
        
        status_counts = {}
        for entry in recent_results:
            status = entry["result"]["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "recent_tests": len(recent_results),
            "status_distribution": status_counts,
            "last_24h_tests": len(
                [e for e in recent_results if time.time() - e["timestamp"] < 86400]
            ),
        }
    
    async def get_network_summary(self) -> Dict[str, Any]:
        """Get summary of all monitored endpoints."""
        summary = {
            "total_endpoints": len(self._performance_metrics),
            "total_tests": sum(
                m["total_tests"] for m in self._performance_metrics.values()
            ),
            "overall_success_rate": 0.0,
            "endpoint_details": {},
        }
        
        if summary["total_tests"] > 0:
            total_successful = sum(
                m["successful_tests"] for m in self._performance_metrics.values()
            )
            summary["overall_success_rate"] = (
                total_successful / summary["total_tests"] * 100
            )
        
        for endpoint_key, metrics in self._performance_metrics.items():
            summary["endpoint_details"][endpoint_key] = {
                "total_tests": metrics["total_tests"],
                "success_rate": metrics["success_rate"],
                "avg_response_time": metrics.get("avg_response_time", 0.0),
                "last_status": metrics["last_status"],
                "last_check": metrics["last_check"],
            }
        
        return summary
    
    async def export_monitoring_data(
        self, format_type: str = "json"
    ) -> Union[str, Dict[str, Any]]:
        """Export monitoring data asynchronously."""
        export_data = {
            "performance_metrics": self._performance_metrics,
            "connection_history": self._connection_history[-1000:],  # Last 1000 entries
            "summary": await self.get_network_summary(),
        }
        
        if format_type.lower() == "json":
            import json
            return json.dumps(export_data, indent=2, default=str)
        elif format_type.lower() == "dict":
            return export_data
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def monitor_multiple_endpoints(
        self, endpoints: List[NetworkEndpoint], interval: float = 60.0
    ) -> List[Dict[str, Any]]:
        """Monitor multiple endpoints concurrently."""
        tasks = []
        for endpoint in endpoints:
            task = self.monitor_endpoint(endpoint, interval)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)


# Backward compatibility aliases
NetworkUtils = SyncNetworkUtils
NetworkMonitor = SyncNetworkMonitor
