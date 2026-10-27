from dataclasses import dataclass
import statistics
import time
import dns.message
import dns.query
import dns.rdatatype

@dataclass
class Result:
    ip: str
    samples: list
    attempts: int
    error: str = ''
    @property
    def successes(self): return len(self.samples)
    @property
    def ratio(self): return self.successes / self.attempts if self.attempts else 0
    @property
    def median_ms(self): return statistics.median(self.samples) if self.samples else float('inf')
    @property
    def jitter_ms(self): return statistics.pstdev(self.samples) if self.samples else float('inf')

def rank_key(result):
    return (-result.ratio, result.median_ms, result.jitter_ms, result.ip)

def measure(ip, domains, rounds, timeout, cancel, port=53):
    samples, attempts, error = [], 0, ''
    for _ in range(rounds):
        for domain in domains:
            if cancel.is_set(): return Result(ip, samples, attempts, '已取消')
            attempts += 1
            try:
                query = dns.message.make_query(domain, 'A')
                start = time.perf_counter()
                response, _ = dns.query.udp_with_fallback(query, ip, timeout=timeout, port=port)
                if response.rcode() or not any(rr.rdtype == dns.rdatatype.A for rr in response.answer):
                    raise ValueError('响应没有有效 A 记录')
                samples.append((time.perf_counter() - start) * 1000)
            except Exception as exc:
                error = str(exc) or type(exc).__name__
    return Result(ip, samples, attempts, error)
