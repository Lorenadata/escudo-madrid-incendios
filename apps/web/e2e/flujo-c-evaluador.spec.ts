import { expect, test, type Page } from "@playwright/test";

// Flujo C del PRD §3.2 (evaluador DATAMAD, sin credenciales) + comprobaciones de lenguaje seguro.
// Requiere API (datos cargados con escudo_api.etl_load) y web en ejecución.

const FORBIDDEN_CLAIMS = [/vidas salvadas/i, /vivienda segura/i, /vivienda insegura/i, /hect[aá]reas protegidas efectivamente/i];

async function assertSafeLanguage(page: Page) {
  const text = await page.locator("body").innerText();
  for (const re of FORBIDDEN_CLAIMS) expect(text, `afirmación prohibida ${re}`).not.toMatch(re);
  await expect(page.getByText("No sustituye a ASEM 112, AEMET, INFOMA", { exact: false })).toBeVisible();
}

test("explorador: mapa regional real, ficha municipal trazable y capa oficial literal", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Explorador regional" })).toBeVisible();
  await expect(page.locator("canvas.maplibregl-canvas")).toBeVisible();
  await expect(page.getByText("179 municipios")).toBeVisible();
  await expect(page.getByText("Instituto Geográfico Nacional", { exact: false })).toBeVisible();

  await page.getByLabel("Buscar municipio").fill("San Lorenzo");
  await page.getByRole("button", { name: /San Lorenzo de El Escorial/ }).click();
  await expect(page.getByRole("heading", { name: "San Lorenzo de El Escorial" })).toBeVisible();
  await expect(page.getByText("escala MUNICIPAL", { exact: false }).first()).toBeVisible();
  // dato CAM-01 con estado y año; la superficie forestal municipal NO se inventa
  await expect(page.getByText("Población censada").first()).toBeVisible();
  await expect(page.getByText("Superficie forestal del municipio")).toBeVisible();
  // clases literales de GEO-01
  await expect(page.getByText("Riesgo muy alto").first()).toBeVisible();

  await page.getByRole("radio", { name: /Riesgo por incendios forestales/ }).check();
  await expect(page.getByText("Generalización web a 200 m", { exact: false })).toBeVisible();
  await assertSafeLanguage(page);
  expect(errors).toEqual([]);
});

test("caso guiado: datos ficticios etiquetados, tres estrategias y método visible", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText("FICTICIOS").first()).toBeVisible();
  await expect(page.getByText("Ficticio").first()).toBeVisible();
  for (const s of ["Priorización manual", "Menor coste primero", "Optimizado (CP-SAT)"]) {
    await expect(page.getByRole("cell", { name: s })).toBeVisible();
  }
  await expect(page.getByText("No mide reducción de riesgo", { exact: false })).toBeVisible();
  await expect(page.getByText("Presupuesto de demostración", { exact: false }).first()).toBeVisible();
  await assertSafeLanguage(page);

  // informe reproducible descargable (T09/T10)
  const link = page.getByRole("link", { name: "Descargar informe PDF" });
  const href = await link.getAttribute("href");
  expect(href).toBeTruthy();
  const res = await page.request.get(href!);
  expect(res.status()).toBe(200);
  expect((await res.body()).subarray(0, 4).toString()).toBe("%PDF");
});

test("fuentes: procedencia con licencia y SHA-256, export CSV", async ({ page }) => {
  await page.goto("/fuentes");
  await expect(page.getByRole("heading", { name: "Fuentes y procedencia" })).toBeVisible();
  const row = page.getByRole("row", { name: /CAM-01/ });
  await expect(row).toContainText("CC-BY");
  await expect(row).toContainText(/[0-9a-f]{10}/);
  const csv = page.getByRole("link", { name: /CSV/ });
  const res = await page.request.get((await csv.getAttribute("href"))!);
  expect(res.status()).toBe(200);
  expect((await res.text()).split("\n").filter(Boolean).length).toBe(180); // cabecera + 179 municipios
});

test("comparador: dos municipios a la misma escala", async ({ page }) => {
  await page.goto("/comparar");
  const selects = page.locator("select");
  await selects.nth(0).selectOption({ label: "Madrid" });
  await selects.nth(1).selectOption({ label: "San Lorenzo de El Escorial" });
  await expect(page.getByRole("heading", { name: "Madrid" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "San Lorenzo de El Escorial" })).toBeVisible();
});

test("área privada: login demo y aislamiento visible del ámbito ficticio", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill("gestor@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/app/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: /Urbanización Ejemplo Los Pinos \(FICTICIA\)/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Indicadores de gestión" })).toBeVisible();
  // el ámbito de la organización B no aparece
  await expect(page.getByText("organización B", { exact: false })).toHaveCount(0);
  await assertSafeLanguage(page);
});
