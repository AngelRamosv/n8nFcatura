import argparse, sys, json, time, re, tempfile, os, shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------
# Log seguro para n8n (stderr)
# -------------------------
def log(msg):
    print(msg, file=sys.stderr)

# -------------------------
# Normalizar RFC
# -------------------------
def normaliza_rfc(s):
    return re.sub(r'[\s-]', '', s.upper()).strip()

# -------------------------
# Proceso principal
# -------------------------
def run(url, rfc, total, proveedor, headless=False):
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
        # -------------------------
        # Inicio
        # -------------------------
        log("[INFO] Iniciando navegador Chrome…")
        log(f"[INFO] Abriendo URL: {url}")

        driver = webdriver.Chrome(options=opts)
        driver.get(url)

        wait = WebDriverWait(driver, 10)

        # -------------------------
        # RFC
        # -------------------------
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#rfc")))
            el.clear()
            el.send_keys(normaliza_rfc(rfc))
            log(f"[INFO] RFC ingresado: {rfc}")
        except Exception as e:
            print(json.dumps({
                "ok": False,
                "error": "rfc_field_not_found",
                "detail": str(e)
            }))
            return

        # -------------------------
        # Total
        # -------------------------
        try:
            el = driver.find_element(By.CSS_SELECTOR, "input#total")
            el.clear()
            el.send_keys(str(total))
            log(f"[INFO] Total ingresado: {total}")
        except:
            log("[WARN] Campo 'total' no encontrado…")

        # -------------------------
        # Captcha falso
        # -------------------------
        try:
            cb = driver.find_element(By.CSS_SELECTOR, "#fake-recaptcha input[type='checkbox']")
            if not cb.is_selected():
                cb.click()
            log("[INFO] Captcha marcado correctamente")
        except:
            log("[WARN] No se encontró captcha…")

        # -------------------------
        # Enviar formulario
        # -------------------------
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "#submit")
            btn.click()
            log("[INFO] Botón 'Enviar Factura' presionado")
        except Exception as e:
            print(json.dumps({
                "ok": False,
                "error": "submit_not_found",
                "detail": str(e)
            }))
            return

        # Pequeña espera
        time.sleep(1)

        # -------------------------
        # ÉXITO JSON (solo esto usa n8n)
        # -------------------------
        print(json.dumps({
            "ok": True,
            "mensaje": "Factura procesada correctamente",
            "rfc": rfc,
            "total": total,
            "proveedor": proveedor,
            "url": url
        }))

        log("[INFO] Proceso completado correctamente")

    finally:
        if driver:
            driver.quit()
        try:
            shutil.rmtree(temp_profile, ignore_errors=True)
            log(f"[INFO] Perfil temporal eliminado: {temp_profile}")
        except:
            log("[WARN] No se pudo limpiar perfil temporal")

# -------------------------
# Parser
# -------------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Automatiza el portal de facturación.")
    p.add_argument("--url", required=True, help="URL del portal de facturación")
    p.add_argument("--rfc", required=True, help="RFC del cliente")
    p.add_argument("--total", required=False, default="", help="Monto total")
    p.add_argument("--proveedor", required=False, default="", help="Nombre del proveedor")
    p.add_argument("--headless", action="store_true", help="Ejecutar sin abrir ventana")

    args = p.parse_args()

    run(args.url, args.rfc, args.total, args.proveedor, args.headless)
