#!/usr/bin/env python3
import time
import re
import subprocess
import sys
import os


class ClienteADB:

    def __init__(self):
        self.dispositivo = None

    def pegar_dispositivo_lista(self):
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        print(result.stdout)
        return result.stdout

    def pegar_dispositivo_alvo(self):
        output = self.pegar_dispositivo_lista()
        devices = [line.split()[0] for line in output.splitlines() 
                  if "\tdevice" in line and "List" not in line]

        if not devices:
            print("❌ Nenhum dispositivo encontrado!")
            sys.exit(1)

        elif len(devices) == 1:
            self.dispositivo = devices[0]
        else:
            print(f"\nMúltiplos dispositivos ({len(devices)}):")
            for i, d in enumerate(devices):
                print(f"  {i+1}. {d}")
            choice = input("\nEscolha o número: ").strip()
            try:
                self.dispositivo = devices[int(choice) - 1]
            except:
                self.dispositivo = devices[0]

        print(f"✅ Dispositivo: {self.dispositivo}")

    def executar_shell(self, comando):
        if not self.dispositivo:
            return ""
        cmd = f"adb -s {self.dispositivo} shell {comando} 2>/dev/null"
        return subprocess.getoutput(cmd)

    def conectar(self, ip="127.0.0.1", porta="5555"):
        endereco = f"{ip}:{porta}"
        print(f"🔌 Conectando em {endereco}...")
        result = subprocess.getoutput(f"adb connect {endereco}")
        print(result)


class DaemonEric:

    def __init__(self):
        self.adb = ClienteADB()

        ip = input("IP [ENTER = 127.0.0.1]: ").strip() or "127.0.0.1"
        porta = input("Porta: ").strip() or "5555"

        self.adb.conectar(ip, porta)
        self.adb.pegar_dispositivo_alvo()

    def reduzir_prioridade(self):
        try:
            pid = os.getpid()
            subprocess.run(["renice", "-n", "19", "-p", str(pid)], capture_output=True)
            subprocess.run(["chrt", "-i", "-p", "0", str(pid)], capture_output=True)
            print(f"[{time.strftime('%H:%M:%S')}] ⚙️ Daemon em baixa prioridade")
        except:
            pass

    def pegar_foreground(self):
        """Detecção avançada multi-método (ótima para Motorola e outros)"""
        
        metodos = [
            # Method 1: Mais confiável
            "dumpsys activity 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp|mResumedActivity|topResumedActivity|mFocusedActivity'",
            
            # Method 2: Activity Stack
            "cmd activity stack list 2>/dev/null | grep -m1 '0,0.*=true'",
            
            # Method 3: Top Activity
            "dumpsys activity top 2>/dev/null | grep -m1 'ACTIVITY '",
            
            # Method 4: Window
            "dumpsys window windows 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp'",
            
            # Method 5: Recents
            "dumpsys activity recents 2>/dev/null | grep -m1 'Recent #0' -A 10"
        ]

        for comando in metodos:
            output = self.adb.executar_shell(comando)

            # Extrai pacote
            match = re.search(r'([a-zA-Z0-9_]+\.[a-zA-Z0-9._]+)', output)
            if match:
                pkg = match.group(1)
                
                # Validação: pacote real (não sistema)
                if (pkg.count('.') >= 2 and
                    not pkg.startswith('android') and
                    not pkg.startswith('com.android') and
                    not pkg.startswith('com.google')):
                    return pkg

        return None

    def pegar_apps_pesados(self, current_fg=""):
        high_cpu = []
        output = self.adb.executar_shell("top -n 1 -b -o %CPU | head -n 40")

        for line in output.splitlines():
            line = line.strip()
            if not line or '%' not in line:
                continue

            try:
                parts = re.split(r'\s+', line)
                if len(parts) < 4:
                    continue

                cpu = float(parts[2].replace('%', ''))
                if cpu > 5.0:
                    proc = parts[-1]
                    if current_fg and current_fg in proc:
                        continue
                    if proc.count('.') >= 2 and "com." in proc:
                        high_cpu.append(proc)
            except:
                continue

        return list(set(high_cpu))

    def deboost_app(self, pkg):
        print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Deboost → {pkg}")

        comandos = [
            f"am set-standby-bucket {pkg} restricted",
            f"cmd activity set-bg-restriction-level --user 0 {pkg} restricted",
            f"cmd appops set {pkg} RUN_IN_BACKGROUND deny",
            f"cmd appops set {pkg} RUN_ANY_IN_BACKGROUND deny"
        ]

        for cmd in comandos:
            self.adb.executar_shell(cmd)

    def iniciar(self):
        print(f"[{time.strftime('%H:%M:%S')}] 🚀 Daemon iniciado com detecção avançada!\n")
        self.reduzir_prioridade()

        last_app = None

        while True:
            app = self.pegar_foreground()

            if app and app != last_app:
                print(f"[{time.strftime('%H:%M:%S')}] 📱 Foreground → {app}")
                last_app = app

            heavy = self.pegar_apps_pesados(app or "")

            for pkg in heavy:
                self.deboost_app(pkg)

            time.sleep(8)


if __name__ == "__main__":
    try:
        daemon = DaemonEric()
        daemon.iniciar()
    except KeyboardInterrupt:
        print(f"\n[{time.strftime('%H:%M:%S')}] 🛑 Daemon encerrado.")
    except Exception as e:
        print(f"Erro: {e}")