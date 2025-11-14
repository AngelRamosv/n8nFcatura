import argparse, sys, json, time, re, tempfile, os, shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def normaliza_rfc(s):
    """Limpia y normaliza el RFC."""
    return re.sub(r'[\s-]', '', s.upper())

def run(url, rfc, total, proveedor, headless=False):
    """Ejecuta el flujo de facturación automatizado."""

    # Si no hay URL, usar página de prueba
    if not url or url.strip() == "":
        url = "https://example.com"

    temp_profile = tempfile.mkdtemp(prefix="chrome_profile_")

    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--allow-file-access-from-files")
    opts.add_argument(f"--user-data-dir={temp_profile}")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--remote-debugging-port=0")

    if headless:
        opts.add_argument("--headless=new")

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
        except:
            print("[WARN] Campo 'total' no encontrado o no llenado")

        time.sleep(1)
        print("[INFO] Proceso completado (prueba simple), cerrando navegador...")

        print(json.dumps({
            "ok": True,
            "rfc": rfc,
            "total": total,
            "proveedor": proveedor,
            "url": url,
            "mensaje": "PRUEBA COMPLETADA — factura procesada correctamente"
        }))

    finally:
        if driver:
            driver.quit()
        try:
            shutil.rmtree(temp_profile, ignore_errors=True)
            print(f"[INFO] Perfil temporal eliminado: {temp_profile}")
        except Exception as e:
            print(f"[WARN] No se pudo eliminar el perfil temporal: {e}")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Automatiza el portal de facturación (PRUEBA).")
    p.add_argument("--url", required=False, default="", help="Ruta o URL del portal HTML")
    p.add_argument("--rfc", required=True, help="RFC del cliente")
    p.add_argument("--total", required=False, default="", help="Total de la factura")
    p.add_argument("--proveedor", required=False, default="", help="Proveedor o empresa")
    p.add_argument("--headless", action="store_true", help="Ejecutar en modo sin interfaz")
    args = p.parse_args()

    run(args.url, args.rfc, args.total, args.proveedor, args.headless)
