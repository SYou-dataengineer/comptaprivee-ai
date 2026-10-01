"""Point d'entrée du prototype Windows, sans logique GUI dupliquée."""
import sys


def startup_error(error):
    """Diagnostic sans contenu de dossier fiscal ni message d'exception sensible."""
    message = "ComptaPrivée AI ne peut pas démarrer. Consultez logs/startup.log dans le profil utilisateur."
    try:
        from src.comptaprivee import app_paths
        from datetime import datetime, timezone
        app_paths.logs_dir().mkdir(parents=True, exist_ok=True)
        with (app_paths.logs_dir() / 'startup.log').open('a', encoding='utf-8') as log:
            log.write(f'{datetime.now(timezone.utc).isoformat()} startup_error={type(error).__name__}\n')
    except Exception:
        message = "ComptaPrivée AI ne peut pas démarrer ni écrire son journal. Vérifiez LOCALAPPDATA et les permissions."
    if sys.argv[1:] == ['--prototype-check']:
        return
    try:
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, 'ComptaPrivée AI — démarrage', 0x10)
        else:
            from tkinter import messagebox
            messagebox.showerror('ComptaPrivée AI', message)
    except Exception:
        pass


def main():
    try:
        if sys.argv[1:] == ['--prototype-check']:
            from scripts.prototype_check import run
            run()
        else:
            from src.comptaprivee.gui import lancer_interface
            lancer_interface()
        return 0
    except Exception as error:
        startup_error(error)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
