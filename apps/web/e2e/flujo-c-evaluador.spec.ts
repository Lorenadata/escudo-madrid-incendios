import { expect, test, type Locator, type Page } from "@playwright/test";

// Flujo C del PRD §3.2 (evaluador DATAMAD, sin credenciales) + comprobaciones de lenguaje seguro.
// Requiere API (datos cargados con escudo_api.etl_load) y web en ejecución.

const FORBIDDEN_CLAIMS = [/vidas salvadas/i, /vivienda segura/i, /vivienda insegura/i, /hect[aá]reas protegidas efectivamente/i];

/** Polígonos dibujados de verdad en el mapa (no basta con que exista el lienzo: MapLibre puede fallar sin pintar nada). */
async function renderedFeatures(map: Locator): Promise<number> {
  return Number((await map.getAttribute("data-rendered-features")) ?? 0);
}

async function assertSafeLanguage(page: Page) {
  const text = await page.locator("body").innerText();
  for (const re of FORBIDDEN_CLAIMS) expect(text, `afirmación prohibida ${re}`).not.toMatch(re);
  await expect(page.getByText("No sustituye a ASEM 112, AEMET, INFOMA", { exact: false })).toBeVisible();
}

test("explorador: mapa regional real, ficha municipal trazable y capa oficial literal", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  // 5.1: la política de contenidos (CSP) no debe bloquear nada de la propia aplicación (mapa, teselas, API)
  page.on("console", (m) => { if (/Content Security Policy|Refused to/i.test(m.text())) errors.push(m.text()); });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Explorador regional" })).toBeVisible();
  await expect(page.locator("canvas.maplibregl-canvas")).toBeVisible();
  await expect(page.getByText("179 municipios")).toBeVisible();
  const map = page.getByRole("region", { name: "Mapa de municipios de la Comunidad de Madrid" });
  await expect.poll(() => renderedFeatures(map), { timeout: 30_000 }).toBeGreaterThan(100);
  // filtrar marca en el mapa los municipios que cumplen y lo dice con su número
  await page.getByLabel("Densidad máx. (hab/km²)").fill("50");
  await expect(page.getByText(/^\d+ de 179 municipios cumplen el filtro$/)).toBeVisible();
  await page.getByRole("button", { name: "Quitar filtro" }).click();
  await expect(page.getByText(/^\d+ de 179 municipios cumplen el filtro$/)).toHaveCount(0);
  await expect(page.getByText("Instituto Geográfico Nacional", { exact: false })).toBeVisible();

  await page.getByLabel("Buscar municipio").fill("San Lorenzo");
  await page.getByRole("button", { name: /San Lorenzo de El Escorial/ }).click();
  await expect(page.getByRole("heading", { name: "San Lorenzo de El Escorial" })).toBeVisible();
  await expect(page.getByText("escala MUNICIPAL", { exact: false }).first()).toBeVisible();
  // dato CAM-01 con estado y año; la superficie forestal municipal NO se inventa
  await expect(page.getByText("Población censada").first()).toBeVisible();
  await expect(page.getByText("Superficie forestal del municipio")).toBeVisible();
  // 2.6: áreas quemadas por satélite (EFFIS) en la ficha y como capa activable
  await expect(page.getByRole("heading", { name: /Áreas quemadas cartografiadas por satélite/ })).toBeVisible();
  await page.getByLabel(/Áreas quemadas cartografiadas por satélite \(EFFIS\)/).check();
  await expect(page.getByText("Áreas quemadas por satélite · EFF-01")).toBeVisible();
  // 2.3: Plan Anual 2026 — ZAR y siniestros municipales (DOC-01), literales y con página
  await expect(page.getByRole("heading", { name: "Plan Anual de incendios forestales 2026" })).toBeVisible();
  await expect(page.getByText("Término municipal declarado Zona de Alto Riesgo (ZAR)")).toBeVisible();
  await expect(page.getByText("Siniestros forestales con origen en el municipio, 2015–2024")).toBeVisible();
  // Fase 2: vivienda y ocupación (CAM-09/10/11, Censo 2021) con su advertencia de escala
  await expect(page.getByRole("heading", { name: /Vivienda y ocupación \(Censo 2021\)/ })).toBeVisible();
  await expect(page.getByText("Proporción de viviendas no principales")).toBeVisible();
  await expect(page.getByText("Fuentes: CAM-09, CAM-10, CAM-11", { exact: false })).toBeVisible();
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
  await expect(page.getByRole("heading", { name: "Actualización verificable" })).toBeVisible();
  await expect(page.getByText("Última comprobación contra el origen", { exact: false })).toBeVisible();
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
  // otros tests crean ámbitos: se selecciona explícitamente el ámbito ficticio de la demo
  await page.getByRole("button", { name: /Urbanización Ejemplo Los Pinos \(FICTICIA\)/ }).click();
  await expect(page.getByRole("heading", { name: /Urbanización Ejemplo Los Pinos \(FICTICIA\)/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Indicadores de gestión" })).toBeVisible();
  // el ámbito de la organización B no aparece
  await expect(page.getByText("organización B", { exact: false })).toHaveCount(0);
  await assertSafeLanguage(page);
  // M15: expediente de autoprotección con cita literal del INFOMA; nunca aprueba
  await page.getByRole("tab", { name: "Expediente" }).click();
  await expect(page.getByRole("heading", { name: "Expediente de autoprotección" })).toBeVisible();
  await expect(page.getByText("no redacta, no aprueba, no registra y no certifica", { exact: false })).toBeVisible();
  await expect(page.getByText("Anexo 6, ap. 1.2.1.b · BOCM pág. 75", { exact: false })).toBeVisible();
  // M17: registro de decisiones del ámbito, inmutable y con autor
  await page.getByRole("tab", { name: "Decisiones" }).click();
  await expect(page.getByRole("heading", { name: "Registro de decisiones" })).toBeVisible();
  await page.getByText("Comentarios y decisiones sobre el ámbito").click();
  await page.getByLabel(/Nueva entrada \(Comentarios y decisiones sobre el ámbito\)/).fill("Decisión e2e: revisar la faja en primavera (ficticio)");
  await page.getByLabel("Tipo de entrada").selectOption("decision");
  await page.getByRole("button", { name: "Añadir entrada", exact: true }).click();
  await page.getByRole("button", { name: "Actualizar registro" }).click();
  await expect(page.getByText("Decisión e2e: revisar la faja en primavera (ficticio)").first()).toBeVisible();
  // M16: calendario preventivo con épocas de peligro oficiales y exportación iCal
  await expect(page.getByRole("heading", { name: "Calendario preventivo" })).toBeVisible();
  await expect(page.getByText("Época de peligro", { exact: false }).first()).toBeVisible();
  const [dl] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: /Exportar a calendario/ }).click()]);
  expect(dl.suggestedFilename()).toBe("escudo-calendario.ics");
});

test("análisis municipal: filtros sobre datos CAM y capa oficial, sin índice propio", async ({ page }) => {
  await page.goto("/analisis");
  await expect(page.getByRole("heading", { name: "Análisis municipal" })).toBeVisible();
  const count = page.getByText(/^\d+ municipios cumplen los filtros$/);
  await expect(count).toBeVisible();
  const before = Number((await count.innerText()).split(" ")[0]);
  await page.getByLabel("Máx. densidad (hab/km²)").fill("20");
  await expect.poll(async () => Number((await count.innerText()).split(" ")[0])).toBeLessThan(before);
  const afterDensity = Number((await count.innerText()).split(" ")[0]);
  await page.getByLabel("Mín. % viviendas no principales").fill("40");
  await expect.poll(async () => Number((await count.innerText()).split(" ")[0])).toBeLessThan(afterDensity);
  await page.getByLabel("Mín. % viviendas no principales").fill("");
  await page.getByLabel("Máx. densidad (hab/km²)").fill("");
  await page.getByLabel("Mín. % en clases altas").fill("");
  await page.getByLabel("Solo municipios declarados Zona de Alto Riesgo").check();
  await expect(count).toHaveText("59 municipios cumplen los filtros");
  // el mapa del análisis colorea los municipios filtrados
  const amap = page.getByRole("region", { name: "Mapa de los municipios que cumplen los filtros" });
  await expect.poll(() => renderedFeatures(amap), { timeout: 30_000 }).toBeGreaterThan(100);
  await expect(page.getByText("No cumple el filtro")).toBeVisible();
  await page.getByText("Ver método y fuentes").click();
  await expect(page.getByText("No es un índice de riesgo propio", { exact: false })).toBeVisible();
  // 2.5: histórico regional (CAM-05, CAM-06) siempre rotulado como regional
  await expect(page.getByRole("heading", { name: "Contexto regional" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Superficie repoblada, \d{4}–\d{4}/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /Superficie afectada por incendios forestales/ })).toBeVisible();
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
  await page.getByRole("button", { name: /Urbanización Ejemplo Los Pinos \(FICTICIA\)/ }).click();
  await page.getByRole("tab", { name: "Inspecciones" }).click();
  // dentro de UNA inspección (puede haber varias, p. ej. las creadas en campo por otros e2e)
  const ins = page.locator("article").filter({ hasText: "Registrar revisión técnica" }).first();
  await ins.getByText("Registrar revisión técnica").click();
  await ins.getByRole("button", { name: "Registrar revisión" }).click();
  await expect(ins.getByText("cualificación verificada", { exact: false }).last()).toBeVisible();
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

test("M19 normativa: búsqueda extractiva con fragmentos literales, página y evaluación visible", async ({ page }) => {
  await page.goto("/normativa");
  await expect(page.getByRole("heading", { name: "Normativa con citas" })).toBeVisible();
  await page.getByRole("button", { name: "¿Cuándo es la época de peligro alto?" }).click();
  await expect(page.getByText("15 de junio hasta el 30 de septiembre", { exact: false }).first()).toBeVisible();
  await expect(page.getByText("no se redactan respuestas", { exact: false }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Abrir el documento en esa página" }).first()).toHaveAttribute("href", /#page=\d+/);
  await expect(page.getByText(/Cómo se ha evaluado: \d+ de 20 preguntas/)).toBeVisible();
  await assertSafeLanguage(page);
});

test("M18 avance público: agregados con umbral de privacidad y sin datos privados", async ({ page }) => {
  await page.goto("/avance");
  await expect(page.getByRole("heading", { name: "Avance público de la prevención" })).toBeVisible();
  await expect(page.getByRole("row", { name: /Collado Villalba/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "No se publican (umbral de privacidad)" })).toBeVisible();
  await expect(page.getByText("Los Pinos")).toHaveCount(0);
  await expect(page.getByText("no de riesgo", { exact: false }).first()).toBeVisible();
  await assertSafeLanguage(page);
});
