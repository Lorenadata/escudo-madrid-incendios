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

test("análisis municipal: filtros sobre datos CAM y capa oficial, sin índice propio", async ({ page }) => {
  await page.goto("/analisis");
  await expect(page.getByRole("heading", { name: "Análisis municipal" })).toBeVisible();
  const count = page.getByText(/^\d+ municipios$/);
  await expect(count).toBeVisible();
  const before = Number((await count.innerText()).split(" ")[0]);
  await page.getByLabel("Máx. densidad (hab/km²)").fill("20");
  await expect.poll(async () => Number((await count.innerText()).split(" ")[0])).toBeLessThan(before);
  await page.getByText("Ver método y fuentes").click();
  await expect(page.getByText("No es un índice de riesgo propio", { exact: false })).toBeVisible();
  await assertSafeLanguage(page);
});

test("Flujo B: responsable municipal ve solo ámbitos autorizados y abre el expediente", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill("municipal@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/app/, { timeout: 30_000 });
  await expect(page.getByRole("heading", { name: "San Lorenzo de El Escorial" })).toBeVisible();
  await expect(page.getByText("únicamente los ámbitos cuya organización ha autorizado", { exact: false })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: /Urbanización Ejemplo Los Pinos/ })).toBeVisible();
  await expect(page.getByText("no compartido", { exact: false })).toHaveCount(0);
  await page.getByRole("button", { name: "Abrir expediente" }).first().click();
  await expect(page.getByRole("heading", { name: "Expediente (solo lectura)" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Descargar informe PDF" })).toBeVisible();
  await assertSafeLanguage(page);
});

test("revisión técnica: bloqueada sin cualificación verificada, con el motivo visible", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill("tecnico@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/app/, { timeout: 30_000 });
  await page.getByRole("tab", { name: "Inspecciones" }).click();
  await page.getByText("Registrar revisión técnica").first().click();
  await page.getByRole("button", { name: "Registrar revisión" }).first().click();
  await expect(page.getByText("cualificación verificada", { exact: false }).last()).toBeVisible();
  await expect(page.getByText("Pendiente de revisión técnica").first()).toBeVisible();
});

test("M05: dibujar el ámbito en el mapa y ver sus clases oficiales orientativas (derivado)", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill("gestor@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/app/, { timeout: 30_000 });
  await page.getByRole("button", { name: "Añadir ámbito" }).click();
  const name = `Ámbito dibujado e2e ${Date.now()} (ficticio)`;
  await page.getByLabel("Nombre del ámbito").fill(name);
  await page.getByLabel("Municipio").selectOption({ label: "San Lorenzo de El Escorial" });
  await page.getByLabel("Dibujar el perímetro del ámbito (opcional)").check();
  const map = page.getByRole("region", { name: "Mapa para dibujar el ámbito" });
  await expect(map.locator("canvas")).toBeVisible();
  await page.waitForTimeout(1500); // encuadre al municipio
  const box = (await map.boundingBox())!;
  for (const [fx, fy] of [[0.45, 0.45], [0.58, 0.45], [0.58, 0.58], [0.45, 0.58]]) {
    await page.mouse.click(box.x + box.width * fx, box.y + box.height * fy);
  }
  await page.getByRole("button", { name: "Cerrar polígono" }).click();
  await expect(page.getByText("Polígono cerrado (4 vértices)")).toBeVisible();
  await page.getByRole("button", { name: "Guardar ámbito" }).click();
  await expect(page.getByRole("heading", { name })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("heading", { name: "Clases oficiales dentro del ámbito dibujado" })).toBeVisible();
  await expect(page.getByText("no para consultar una parcela", { exact: false })).toBeVisible();
});
