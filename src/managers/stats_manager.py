import json
import threading
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict


class StatsManager:
    """Gerenciador de estatísticas de encoding."""
    
    def __init__(self, stats_dir: Optional[str] = None):
        self.stats_dir = Path(stats_dir) if stats_dir else Path(__file__).parent.parent.parent / "stats"
        self.stats_dir.mkdir(parents=True, exist_ok=True)
        self._stats_file = self.stats_dir / "statistics.json"
        self._stats: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """Carrega estatísticas do arquivo."""
        if self._stats_file.exists():
            try:
                with open(self._stats_file, 'r', encoding='utf-8') as f:
                    self._stats = json.load(f)
            except Exception:
                self._stats = self._get_default_stats()
        else:
            self._stats = self._get_default_stats()
            self.save()
        
        return self._stats.copy()
    
    def _get_default_stats(self) -> Dict[str, Any]:
        """Retorna estrutura padrão de estatísticas."""
        return {
            "total_encodes": 0,
            "successful_encodes": 0,
            "failed_encodes": 0,
            "total_duration_processed_seconds": 0,
            "total_input_size_bytes": 0,
            "total_output_size_bytes": 0,
            "average_cq_by_profile": {},
            "encode_history": [],
            "peak_hours": defaultdict(int),
            "failure_reasons": defaultdict(int),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def save(self) -> bool:
        """Salva estatísticas no arquivo."""
        try:
            with open(self._stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def record_encode(
        self,
        profile_id: str,
        profile_name: str,
        success: bool,
        duration_seconds: float,
        input_size: int,
        output_size: int,
        cq_used: Optional[str] = None,
        failure_reason: Optional[str] = None,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None
    ):
        """Registra novo encode nas estatísticas."""
        with self._lock:
            now = datetime.now()
            
            self._stats["total_encodes"] += 1
            
            if success:
                self._stats["successful_encodes"] += 1
                self._stats["total_duration_processed_seconds"] += duration_seconds
                self._stats["total_input_size_bytes"] += input_size
                self._stats["total_output_size_bytes"] += output_size
                
                if cq_used and profile_id:
                    if profile_id not in self._stats["average_cq_by_profile"]:
                        self._stats["average_cq_by_profile"][profile_id] = {"sum": 0, "count": 0}
                    self._stats["average_cq_by_profile"][profile_id]["sum"] += float(cq_used)
                    self._stats["average_cq_by_profile"][profile_id]["count"] += 1
            else:
                self._stats["failed_encodes"] += 1
                if failure_reason:
                    self._stats["failure_reasons"][failure_reason] = self._stats["failure_reasons"].get(failure_reason, 0) + 1
            
            hour_key = now.strftime("%Y-%m-%d %H:00")
            self._stats["peak_hours"][hour_key] = self._stats["peak_hours"].get(hour_key, 0) + 1
            
            history_entry = {
                "timestamp": now.isoformat(),
                "profile_id": profile_id,
                "profile_name": profile_name,
                "success": success,
                "duration_seconds": duration_seconds,
                "input_size": input_size,
                "output_size": output_size,
                "cq_used": cq_used,
                "failure_reason": failure_reason,
                "input_path": input_path,
                "output_path": output_path
            }
            
            self._stats["encode_history"].append(history_entry)
            
            # Manter apenas últimos 1000 registros
            if len(self._stats["encode_history"]) > 1000:
                self._stats["encode_history"] = self._stats["encode_history"][-1000:]
            
            self._stats["updated_at"] = now.isoformat()
            self.save()
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo das estatísticas."""
        with self._lock:
            total = self._stats["total_encodes"]
            successful = self._stats["successful_encodes"]
            
            avg_cq_by_profile = {}
            for profile_id, data in self._stats["average_cq_by_profile"].items():
                if data["count"] > 0:
                    avg_cq_by_profile[profile_id] = round(data["sum"] / data["count"], 2)
            
            return {
                "total_encodes": total,
                "successful_encodes": successful,
                "failed_encodes": self._stats["failed_encodes"],
                "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
                "total_duration_hours": round(self._stats["total_duration_processed_seconds"] / 3600, 2),
                "total_input_size_gb": round(self._stats["total_input_size_bytes"] / (1024 ** 3), 2),
                "total_output_size_gb": round(self._stats["total_output_size_bytes"] / (1024 ** 3), 2),
                "compression_ratio": round(
                    (self._stats["total_output_size_bytes"] / self._stats["total_input_size_bytes"])
                    if self._stats["total_input_size_bytes"] > 0 else 0, 2
                ),
                "average_cq_by_profile": avg_cq_by_profile,
                "created_at": self._stats["created_at"],
                "updated_at": self._stats["updated_at"]
            }
    
    def get_failure_reasons(self) -> Dict[str, int]:
        """Retorna razões de falha."""
        with self._lock:
            return dict(self._stats["failure_reasons"])
    
    def get_peak_hours(self, last_days: int = 7) -> Dict[str, int]:
        """Retorna horas de pico nos últimos N dias."""
        cutoff = datetime.now() - timedelta(days=last_days)
        
        with self._lock:
            peak_hours = {}
            for hour, count in self._stats["peak_hours"].items():
                try:
                    hour_dt = datetime.strptime(hour, "%Y-%m-%d %H:00")
                    if hour_dt >= cutoff:
                        peak_hours[hour] = count
                except Exception:
                    pass
            return peak_hours
    
    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna histórico recente."""
        with self._lock:
            return self._stats["encode_history"][-limit:]
    
    def export_to_json(self, output_path: str) -> bool:
        """Exporta estatísticas para arquivo JSON."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "summary": self.get_summary(),
                    "failure_reasons": self.get_failure_reasons(),
                    "recent_history": self.get_recent_history(100)
                }, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def reset_statistics(self) -> bool:
        """Reseta todas as estatísticas."""
        with self._lock:
            self._stats = self._get_default_stats()
            self.save()
            return True
