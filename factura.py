# facturar.py
import argparse, sys, json, time, re, tempfile, os, shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def normaliza_rfc(s):
    """Limpia y normaliza el RFC."""
    return re.sub(r'[\s-]', '', s.upper())

def run(url, rfc, total, proveedor):
    """Ejecuta el flujo de facturación automatizado."""
    # Crear un perfil temporal único para evitar conflictos
    temp_profile = tempfile.mkdtemp(prefix="chrome_profile_")

    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--allow-file-access-from-files")
    opts.add_argument(f"--user-data-dir={temp_profile}")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--remote-debugging-port=0")
    opts.add_argument("--headless=new")  # Ejecuta en segundo plano (headless)

    driver = None
    try:
        print(f"[INFO] Iniciando navegador Chrome...")
        driver = webdriver.Chrome(options=opts)
        print(f"[INFO] Abriendo URL: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # --- RFC ---
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#rfc")))
            el.clear()
            el.send_keys(normaliza_rfc(rfc))
            print(f"[INFO] RFC ingresado: {rfc}")
        except Exception as e:
            print(json.dumps({"ok": False, "error": "rfc_field_not_found", "e": str(e)}))
            return

        # --- Total ---
        try:
            el = driver.find_element(By.CSS_SELECTOR, "input#total")
            el.clear()
            el.send_keys(str(total))
            print(f"[INFO] Total ingresado: {total}")
        except Exception:
            print("[WARN] Campo 'total' no encontrado o no llenado")

        # --- Captcha falso ---
        try:
            cb = driver.find_element(By.CSS_SELECTOR, "#fake-recaptcha input[type='checkbox']")
            if not cb.is_selected():
                cb.click()
            print("[INFO] Captcha marcado correctamente")
        except Exception:
            print("[WARN] Captcha no encontrado")

        # --- Enviar formulario ---
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "#submit")
            btn.click()
            print("[INFO] Botón 'Enviar Factura' presionado")
        except Exception as e:
            print(json.dumps({"ok": False, "error": "submit_not_found", "e": str(e)}))
            return

        time.sleep(1)
        print("[INFO] Proceso completado, cerrando navegador...")

        print(json.dumps({
            "ok": True,
            "rfc": rfc,
            "total": total,
            "proveedor": proveedor,
            "url": url,
            "mensaje": "Factura procesada correctamente"
        }))
    finally:
        if driver:
            driver.quit()
        # Limpiar el perfil temporal
        try:
            shutil.rmtree(temp_profile, ignore_errors=True)
            print(f"[INFO] Perfil temporal eliminado: {temp_profile}")
        except Exception as e:
            print(f"[WARN] No se pudo eliminar el perfil temporal: {e}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Automatiza el portal de facturación.")
    p.add_argument("--url", required=True, help="Ruta o URL del portal HTML")
    p.add_argument("--rfc", required=True, help="RFC del cliente")
    p.add_argument("--total", required=False, default="", help="Total de la factura")
    p.add_argument("--proveedor", required=False, default="", help="Proveedor o empresa")
    args = p.parse_args()

    run(args.url, args.rfc, args.total, args.proveedor)
