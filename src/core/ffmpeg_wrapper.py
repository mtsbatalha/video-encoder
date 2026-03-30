import subprocess
import json
import threading
import shutil
from typing import Optional, Dict, List, Any, Callable


class FFmpegWrapper:
    """Wrapper para comandos FFmpeg com suporte a NVENC."""
    
    CODEC_MAP = {
        'hevc_nvenc': {'codec': 'hevc_nvenc', 'pix_fmt': 'yuv420p10le', 'profile': 'main10', 'cq_param': '-cq'},
        'h264_nvenc': {'codec': 'h264_nvenc', 'pix_fmt': 'yuv420p', 'profile': 'high', 'cq_param': '-cq'},
        'av1_nvenc': {'codec': 'av1_nvenc', 'pix_fmt': 'yuv420p10le', 'profile': 'main', 'cq_param': '-cq'},
        'hevc_amf': {'codec': 'hevc_amf', 'pix_fmt': 'yuv420p10le', 'profile': 'main10', 'cq_param': '-qp_i'},
        'h264_amf': {'codec': 'h264_amf', 'pix_fmt': 'yuv420p', 'profile': 'high', 'cq_param': '-qp_i'},
        'hevc_qsv': {'codec': 'hevc_qsv', 'pix_fmt': 'yuv420p10le', 'profile': 'main10', 'cq_param': '-q'},
        'h264_qsv': {'codec': 'h264_qsv', 'pix_fmt': 'yuv420p', 'profile': 'high', 'cq_param': '-q'},
        'libx265': {'codec': 'libx265', 'pix_fmt': 'yuv420p10le', 'profile': 'main10', 'cq_param': '-crf'},
        'libx264': {'codec': 'libx264', 'pix_fmt': 'yuv420p', 'profile': 'high', 'cq_param': '-crf'}
    }
    
    def __init__(self, ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None):
        self.ffmpeg = ffmpeg_path or shutil.which('ffmpeg') or 'ffmpeg'
        self.ffprobe = ffprobe_path or shutil.which('ffprobe') or 'ffprobe'
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        
    def verify_installation(self) -> bool:
        """Verifica se FFmpeg e FFprobe estão disponíveis."""
        try:
            ffmpeg_result = subprocess.run(
                [self.ffmpeg, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            ffprobe_result = subprocess.run(
                [self.ffprobe, '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return ffmpeg_result.returncode == 0 and ffprobe_result.returncode == 0
        except Exception:
            return False
    
    def get_nvenc_codecs(self) -> List[str]:
        """Retorna lista de codecs NVENC disponíveis."""
        try:
            result = subprocess.run(
                [self.ffmpeg, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            codecs = []
            for line in result.stdout.split('\n'):
                if 'nvenc' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        codecs.append(parts[1])
            return codecs
        except Exception:
            return []
    
    def get_all_video_codecs(self) -> List[str]:
        """Retorna todos os codecs de vídeo disponíveis."""
        try:
            result = subprocess.run(
                [self.ffmpeg, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            codecs = []
            target_codecs = ['hevc_nvenc', 'h264_nvenc', 'av1_nvenc', 'hevc_amf', 'h264_amf', 
                           'hevc_qsv', 'h264_qsv', 'libx265', 'libx264']
            for line in result.stdout.split('\n'):
                for codec in target_codecs:
                    if codec in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            codecs.append(parts[1])
                        break
            return codecs
        except Exception:
            return []
    
    def is_codec_available(self, codec: str) -> bool:
        """Verifica se codec específico está disponível."""
        try:
            result = subprocess.run(
                [self.ffmpeg, '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return codec.lower() in result.stdout.lower()
        except Exception:
            return False
    
    def get_media_info(self, input_path: str) -> Dict[str, Any]:
        """Obtém informações detalhadas do arquivo de mídia."""
        try:
            result = subprocess.run(
                [self.ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', input_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {}
        except Exception:
            return {}
    
    def get_video_streams(self, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai streams de vídeo das informações da mídia."""
        streams = info.get('streams', [])
        return [s for s in streams if s.get('codec_type') == 'video']
    
    def get_audio_streams(self, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai streams de áudio das informações da mídia."""
        streams = info.get('streams', [])
        return [s for s in streams if s.get('codec_type') == 'audio']
    
    def get_subtitle_streams(self, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai streams de legenda das informações da mídia."""
        streams = info.get('streams', [])
        return [s for s in streams if s.get('codec_type') == 'subtitle']
    
    def get_duration(self, info: Dict[str, Any]) -> float:
        """Retorna duração em segundos."""
        format_info = info.get('format', {})
        return float(format_info.get('duration', 0))
    
    def get_resolution(self, video_stream: Dict[str, Any]) -> tuple:
        """Retorna resolução (largura, altura)."""
        width = video_stream.get('width', 0)
        height = video_stream.get('height', 0)
        return (width, height)
    
    def get_hdr_info(self, video_stream: Dict[str, Any]) -> bool:
        """Verifica se o vídeo é HDR."""
        color_transfer = video_stream.get('color_transfer', '')
        color_primaries = video_stream.get('color_primaries', '')
        return color_transfer in ['smpte2084', 'arib-std-b67'] or color_primaries in ['bt2020']
    
    def is_interlaced(self, video_stream: Dict[str, Any]) -> bool:
        """Verifica se o vídeo é entrelaçado."""
        field_order = video_stream.get('field_order', 'progressive')
        return field_order not in ['progressive', 'unknown', 'tt', 'bb']
    
    def build_encoding_command(
        self,
        input_path: str,
        output_path: str,
        codec: str = 'hevc_nvenc',
        cq: Optional[str] = None,
        bitrate: Optional[str] = None,
        resolution: Optional[str] = None,
        preset: str = 'p5',
        two_pass: bool = False,
        hdr_to_sdr: bool = False,
        deinterlace: bool = False,
        audio_tracks: Optional[List[int]] = None,
        subtitle_burn: bool = False,
        plex_compatible: bool = True
    ) -> List[str]:
        """Constrói comando FFmpeg para encoding."""
        
        cmd = [self.ffmpeg, '-y', '-i', input_path]
        
        video_params = self.CODEC_MAP.get(codec, self.CODEC_MAP['hevc_nvenc'])
        
        filter_complex = []
        
        if deinterlace:
            filter_complex.append('bwdif=mode=send:par=1')
        
        if resolution:
            filter_complex.append(f'scale=-2:{resolution}')
        
        if hdr_to_sdr:
            filter_complex.append('zscale=t=linear:npl=100')
            filter_complex.append('format=gbrpf32le')
            filter_complex.append('tonemap=hable:desat=0')
            filter_complex.append('zscale=t=bt709:m=bt709:r=tv')
            filter_complex.append('format=yuv420p')
        
        if filter_complex:
            cmd.extend(['-vf', ','.join(filter_complex)])
        
        cmd.extend(['-c:v', video_params['codec']])
        
        if codec in ['hevc_amf', 'h264_amf']:
            preset_map = {'quality': 'quality', 'balanced': 'balanced', 'speed': 'speed'}
            amf_preset = preset_map.get(preset, 'balanced')
            cmd.extend(['-preset', amf_preset])
        elif codec in ['hevc_qsv', 'h264_qsv']:
            qsv_preset = preset if preset in ['fast', 'faster', 'fastest', 'slow', 'slower', 'slowest'] else 'balanced'
            cmd.extend(['-preset', qsv_preset])
        elif codec in ['libx265', 'libx264']:
            cpu_preset = preset if preset in ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow'] else 'medium'
            cmd.extend(['-preset', cpu_preset])
        else:
            cmd.extend(['-preset', preset])
        
        if two_pass and codec in ['h264_nvenc', 'hevc_nvenc']:
            cmd.extend(['-rc', 'twopass'])
        elif cq:
            cq_param = video_params.get('cq_param', '-cq')
            cmd.extend([cq_param, cq])
        elif bitrate:
            cmd.extend(['-b:v', bitrate])
        
        if codec not in ['libx265', 'libx264']:
            cmd.extend(['-pix_fmt', video_params['pix_fmt']])
            cmd.extend(['-profile:v', video_params['profile']])
        
        if plex_compatible:
            cmd.extend(['-tag:v', 'hvc1' if 'hevc' in codec or 'av1' in codec else 'avc1'])
        
        audio_streams = self.get_audio_streams(self.get_media_info(input_path))
        
        if audio_tracks:
            audio_map = []
            for track in audio_tracks:
                if track <= len(audio_streams):
                    audio_map.extend(['-map', f'0:a:{track-1}'])
            cmd.extend(audio_map)
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        elif audio_streams:
            cmd.extend(['-map', '0:a?', '-c:a', 'aac', '-b:a', '192k'])
        
        if subtitle_burn:
            subtitle_streams = self.get_subtitle_streams(self.get_media_info(input_path))
            if subtitle_streams:
                for i, sub in enumerate(subtitle_streams):
                    if sub.get('disposition', {}).get('forced', False):
                        cmd.extend(['-map', f'0:s:{i}'])
                        break
                else:
                    cmd.extend(['-map', '0:s:0?'])
        else:
            cmd.extend(['-map', '0:s?'])
        
        cmd.extend(['-map', '0:v:0'])
        
        cmd.extend(['-movflags', '+faststart'])
        
        cmd.append(output_path)
        
        return cmd
    
    def run_encoding(
        self,
        command: List[str],
        timeout: Optional[int] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> tuple[bool, str]:
        """Executa comando de encoding."""
        with self._lock:
            try:
                self._process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stderr_output = []
                
                while True:
                    if self._process.stderr is None:
                        break
                    output = self._process.stderr.readline()
                    if output == '' and self._process.poll() is not None:
                        break
                    if output:
                        stderr_output.append(output.strip())
                        if callback:
                            callback(output.strip())
                
                returncode = self._process.wait(timeout=timeout)
                self._process = None
                
                if returncode == 0:
                    return (True, 'Encoding completed successfully')
                else:
                    return (False, '\n'.join(stderr_output[-10:]))
                    
            except subprocess.TimeoutExpired:
                if self._process:
                    self._process.terminate()
                self._process = None
                return (False, 'Encoding timeout')
            except Exception as e:
                self._process = None
                return (False, str(e))
    
    def terminate(self):
        """Termina processo de encoding ativo."""
        with self._lock:
            if self._process:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
                finally:
                    self._process = None
