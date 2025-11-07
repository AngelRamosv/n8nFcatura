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

    # Si estás en un servidor (n8n / Grok), deja esto activado:
    opts.add_argument("--headless=new")

    # Si lo pruebas localmente y quieres ver la ventana de Chrome,
    # comenta la línea anterior:
    # opts.add_argument("--headless=new")

    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # --- RFC ---
        try:
            el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#rfc")))
            el.clear()
            el.send_keys(normaliza_rfc(rfc))
        except Exception as e:
            print(json.dumps({"ok": False, "error": "rfc_field_not_found", "e": str(e)}))
            return

        # --- Total ---
        try:
            el = driver.find_element(By.CSS_SELECTOR, "input#total")
            el.clear()
            el.send_keys(str(total))
        except Exception:
            pass

        # --- Captcha falso ---
        try:
            cb = driver.find_element(By.CSS_SELECTOR, "#fake-recaptcha input[type='checkbox']")
            if not cb.is_selected():
                cb.click()
        except Exception:
            pass

        # --- Enviar formulario ---
        try:
            btn = driver.find_element(By.CSS_SELECTOR, "#submit")
            btn.click()
        except Exception as e:
            print(json.dumps({"ok": False, "error": "submit_not_found", "e": str(e)}))
            return

        time.sleep(1)
        print(json.dumps({
            "ok": True,
            "rfc": rfc,
            "total": total,
            "url": url,
            "mensaje": "Factura procesada correctamente"
        }))
    finally:
        if driver:
            driver.quit()
        # Limpiar el perfil temporal
        try:
            shutil.rmtree(temp_profile, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Automatiza el portal de facturación.")
    p.add_argument("--url", required=True, help="Ruta o URL del portal HTML")
    p.add_argument("--rfc", required=True, help="RFC del cliente")
    p.add_argument("--total", required=False, default="", help="Total de la factura")
    p.add_argument("--proveedor", required=False, default="", help="Proveedor o empresa")
    args = p.parse_args()

    run(args.url, args.rfc, args.total, args.proveedor)
