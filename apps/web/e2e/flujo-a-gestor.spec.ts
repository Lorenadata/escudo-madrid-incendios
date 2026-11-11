import { expect, test } from "@playwright/test";

// Flujo A (PRD §3.2) de punta a punta en la UI, desde cero y cronometrado (ROADMAP 1.4: < 3 min).
// login → ámbito → contexto oficial → inspección + foto → medidas → presupuesto → optimizar → comparar
// → confirmar plan → asignar → evidencia → informe PDF.

const PNG_1PX = Buffer.from("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6390b3d6ff0f00028b0188aca22bc10000000049454e44ae426082", "hex");

test("Flujo A completo del gestor en menos de 3 minutos", async ({ page }) => {
  test.setTimeout(240_000);
  const t0 = Date.now();

  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill("gestor@demo.escudo.local");
  await page.getByLabel("Contraseña").fill("demo-escudo-2026");
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page).toHaveURL(/\/app/, { timeout: 30_000 });

  // ámbito nuevo
  await page.getByRole("button", { name: "Añadir ámbito" }).click();
  const name = `Ámbito Flujo A e2e ${Date.now()} (ficticio)`;
  await page.getByLabel("Nombre del ámbito").fill(name);
  await page.getByLabel("Municipio").selectOption({ label: "San Lorenzo de El Escorial" });
  await page.getByRole("button", { name: "Guardar ámbito" }).click();
  await expect(page.getByRole("heading", { name })).toBeVisible({ timeout: 20_000 });

  // contexto oficial y meteorológico
  await expect(page.getByText("Población censada").first()).toBeVisible();
  await expect(page.getByText("Contexto meteorológico AEMET")).toBeVisible();

  // inspección con evidencia
  await page.getByRole("tab", { name: "Inspecciones" }).click();
  await page.getByLabel("Persona que inspecciona").fill("Inspectora e2e (ficticia)");
  const groups = page.getByRole("radiogroup");
  const n = await groups.count();
  for (let i = 0; i < n; i++) await groups.nth(i).getByLabel("No", { exact: true }).check();
  await page.getByRole("button", { name: "Guardar inspección" }).click();
  await expect(page.getByText("Pendiente de revisión técnica").first()).toBeVisible({ timeout: 15_000 });
  await page.locator('input[type="file"]').first().setInputFiles({ name: "foto-e2e.png", mimeType: "image/png", buffer: PNG_1PX });
  await expect(page.getByText("foto-e2e.png").first()).toBeVisible({ timeout: 15_000 });

  // escenario: medidas, presupuesto, optimizar, comparar
  await page.getByRole("tab", { name: "Escenarios y plan" }).click();
  const newBtn = page.getByRole("button", { name: "Nuevo escenario" });
  if (await newBtn.isVisible()) await newBtn.click();
  await page.getByLabel("Nombre", { exact: true }).fill("Escenario Flujo A e2e");
  await page.getByLabel("Presupuesto disponible (€)").fill("1000");
  for (const code of ["HIDR-REV", "INFO-POB", "SENAL-CALLES"]) {
    await page.getByLabel("Añadir actuación del catálogo").selectOption(code);
  }
  const qty = ["4", "1", "2"];
  const cost = ["100", "500", "300"];
  for (let i = 0; i < 3; i++) {
    await page.getByLabel("Cantidad").nth(i).fill(qty[i]);
    await page.getByLabel("Coste unitario").nth(i).fill(cost[i]);
  }
  await page.getByRole("button", { name: "Guardar escenario" }).click();
  await page.getByRole("button", { name: "Resolver escenario" }).click();
  for (const s of ["Priorización manual", "Menor coste primero", "Optimizado (CP-SAT)"]) {
    await expect(page.getByRole("cell", { name: s })).toBeVisible({ timeout: 30_000 });
  }

  // plan: confirmar, asignar, evidencia
  await page.getByRole("button", { name: "Confirmar plan" }).click();
  const status = page.getByLabel(/^Estado de /).first();
  await expect(status).toBeVisible({ timeout: 15_000 });
  await status.selectOption("in_progress");
  const resp = page.getByLabel("Responsable").first();
  await resp.fill("Empresa ejemplo (ficticia)");
  await resp.blur();
  const planFile = page.locator('section[aria-labelledby="plan-h"] input[type="file"]').first();
  await planFile.setInputFiles({ name: "evidencia-plan.png", mimeType: "image/png", buffer: PNG_1PX });

  // informe PDF
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 30_000 }),
    page.getByRole("button", { name: "Descargar informe PDF" }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/\.pdf$/);

  const seconds = (Date.now() - t0) / 1000;
  console.log(`Flujo A completado en ${seconds.toFixed(1)} s`);
  expect(seconds).toBeLessThan(180);
});
