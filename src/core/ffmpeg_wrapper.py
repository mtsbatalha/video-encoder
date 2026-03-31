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
        
        # Copiar todas as legendas sem re-encoding para evitar erros com formatos incompatíveis (SSA/ASS)
        if subtitle_burn:
            # Se burn está habilitado, ainda assim copiar as legendas (não implementar burn por ora)
            cmd.extend(['-map', '0:s?', '-c:s', 'copy'])
        else:
            # Copiar todas as legendas como estão
            cmd.extend(['-map', '0:s?', '-c:s', 'copy'])
        
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
        print(f"🔍 DEBUG: FFmpegWrapper.run_encoding chamado")
        print(f"🔍 DEBUG: Comando completo: {' '.join(command)}")
        try:
            print(f"🔍 DEBUG: Criando subprocess...")
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,  # ✅ DIAGNÓSTICO: Fornecer stdin explícito
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            print(f"🔍 DEBUG: Subprocess criado com PID: {self._process.pid}")
            
            # ✅ DIAGNÓSTICO: Fechar stdin imediatamente para evitar FFmpeg esperando input
            if self._process.stdin:
                print(f"🔍 DEBUG: Fechando stdin do processo FFmpeg...")
                self._process.stdin.close()
            
            print(f"🔍 DEBUG: stdout pipe válido? {self._process.stdout is not None}")
            print(f"🔍 DEBUG: stderr redireccionado para stdout")
            
            output_lines = []
            import time as time_module
            
            start_time = time_module.time()
            last_output_time = start_time
            max_idle_seconds = 300  # 5 minutos sem saída = possível hang
            
            print(f"🔍 DEBUG: Entrando no loop principal de leitura...")
            # Loop principal de leitura da saída do FFmpeg
            loop_iteration = 0
            while True:
                loop_iteration += 1
                if loop_iteration % 10 == 0:  # Log a cada 10 iterações
                    print(f"🔍 DEBUG: Loop iteration {loop_iteration}, processo ainda rodando")
                
                # Verifica se o processo terminou
                poll_result = self._process.poll()
                print(f"🔍 DEBUG: poll_result = {poll_result}")
                if poll_result is not None:
                    print(f"🔍 DEBUG: Processo terminou detectado! returncode = {poll_result}")
                    # Processo terminou - lê qualquer saída restante
                    if self._process.stdout:
                        remaining = self._process.stdout.read()
                        if remaining:
                            for line in remaining.splitlines():
                                if line.strip():
                                    output_lines.append(line.strip())
                                    if callback:
                                        callback(line.strip())
                    break
                
                # ✅ DIAGNÓSTICO CRÍTICO: Verificar estado do stdout
                print(f"🔧 DEBUG CRÍTICO: self._process = {self._process}")
                print(f"🔧 DEBUG CRÍTICO: self._process.stdout = {self._process.stdout}")
                print(f"🔧 DEBUG CRÍTICO: bool(self._process.stdout) = {bool(self._process.stdout if self._process else False)}")
                
                # ✅ DIAGNÓSTICO: Ler com timeout e buffer menor para capturar \r sem \n
                if self._process.stdout:
                    print(f"✅ DEBUG: Entrando no bloco de leitura do stdout")
                    try:
                        # Tentar ler com read() ao invés de readline() - captura \r também
                        import select
                        import sys
                        
                        # Windows não suporta select em pipes, usar readline com timeout simulado
                        if sys.platform == 'win32':
                            # Método alternativo para Windows: non-blocking read
                            print(f"🔍 DEBUG: (Win32) Tentando ler linha do stdout...")
                            output = self._process.stdout.readline()
                            print(f"🔍 DEBUG: readline() retornou: {len(output) if output else 0} caracteres")
                            
                            # ✅ DIAGNÓSTICO: Mostrar representação dos caracteres especiais
                            if output:
                                print(f"🔍 DEBUG: Conteúdo raw (repr): {repr(output[:100])}")
                                print(f"🔍 DEBUG: Contém \\r? {'SIM' if '\\r' in repr(output) else 'NÃO'}")
                                print(f"🔍 DEBUG: Contém \\n? {'SIM' if '\\n' in repr(output) else 'NÃO'}")
                                
                                last_output_time = time_module.time()
                                output_lines.append(output.strip())
                                if callback:
                                    callback(output.strip())
                            else:
                                # Sem saída disponível, espera um pouco antes de tentar novamente
                                print(f"🔍 DEBUG: Nenhuma saída de readline(), aguardando 0.1s...")
                                time_module.sleep(0.1)
                        else:
                            # Unix/Linux: pode usar select
                            output = self._process.stdout.readline()
                            if output:
                                last_output_time = time_module.time()
                                output_lines.append(output.strip())
                                if callback:
                                    callback(output.strip())
                            else:
                                time_module.sleep(0.1)
                    except Exception as e:
                        # Erro na leitura do pipe - continua tentando
                        print(f"⚠️ DEBUG: Exceção ao ler stdout: {type(e).__name__}: {e}")
                        time_module.sleep(0.1)
                
                # Verifica timeout de inatividade (processo pode estar travado)
                idle_time = time_module.time() - last_output_time
                if idle_time > max_idle_seconds:
                    print(f"⚠️ DEBUG: Processo inativo por {idle_time:.0f}s. Verificando status...")
                    # Verifica novamente se o processo terminou
                    if self._process.poll() is not None:
                        print(f"🔍 DEBUG: Processo terminou durante período de inatividade")
                        break
                    # Se ainda rodando, continua aguardando (não quebra o loop)
                    last_output_time = time_module.time()  # Reseta timer para evitar loop infinito de warnings
            
            # Aguarda processo terminar e obtém returncode
            returncode = self._process.wait(timeout=5)
            self._process = None
            
            print(f"🔍 DEBUG: FFmpeg processo finalizado com returncode: {returncode}")
            
            if returncode == 0:
                print(f"✅ DEBUG: Encoding completado com sucesso")
                return (True, 'Encoding completed successfully')
            else:
                error_msg = '\n'.join(output_lines[-20:])
                print(f"❌ DEBUG: Encoding falhou. Últimas linhas de erro:")
                print(error_msg)
                return (False, error_msg)
                
        except subprocess.TimeoutExpired:
            print(f"❌ DEBUG: Timeout no processo FFmpeg")
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=2)
                except:
                    self._process.kill()
            self._process = None
            return (False, 'Encoding timeout')
        except Exception as e:
            print(f"❌ DEBUG: Exceção capturada no run_encoding: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            if self._process:
                try:
                    self._process.terminate()
                except:
                    pass
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
