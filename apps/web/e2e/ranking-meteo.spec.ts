import { expect, test } from "@playwright/test";

// Ranking de atención preventiva y meteorología AEMET. Requiere API con datos cargados y web en ejecución.

test("ranking: puntuación explicada, cruce oficial, filtros y pesos modificables", async ({ page }) => {
  await page.goto("/ranking");
  await expect(page.getByRole("heading", { name: "Dónde mirar primero" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "El ranking" })).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("municipios obligados figuran con su plan", { exact: false })).toBeVisible();
  await expect(page.getByText(/^179 municipios$/)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Por qué está aquí" })).toBeVisible();

  const map = page.getByRole("region", { name: "Mapa de municipios por puntuación de atención" });
  await expect.poll(async () => Number((await map.getAttribute("data-rendered-features")) ?? 0), { timeout: 30_000 }).toBeGreaterThan(100);

  await page.getByRole("button", { name: "Más de la mitad en riesgo, fuera de esas zonas" }).click();
  await expect(page.getByText(/^38 municipios$/)).toBeVisible();
  await page.getByRole("button", { name: "Obligados sin plan aprobado" }).click();
  await expect(page.getByText(/^30 municipios$/)).toBeVisible();
  await page.getByRole("button", { name: "Los 179" }).click();

  const ranking = page.getByRole("region", { name: "El ranking" });
  const first = ranking.locator("ol button[aria-pressed]").first();
  const before = await first.innerText();
  await page.getByText("Cambiar los pesos de la puntuación").click();
  await page.getByLabel(/^Territorio/).fill("0");
  await expect.poll(() => first.innerText()).not.toBe(before);
  await page.getByRole("button", { name: "Restablecer pesos" }).click();
  await expect.poll(() => first.innerText()).toBe(before);

  await ranking.getByText("Ver método y fuentes").click();
  await expect(page.getByText("No es riesgo de incendio ni una probabilidad", { exact: false })).toBeVisible();
});

test("riesgo estimado hoy: rotulado como estimación, con motivos o estado no disponible", async ({ page }) => {
  await page.goto("/ranking");
  const section = page.getByRole("region", { name: "Riesgo estimado hoy", exact: true });
  await expect(section).toBeVisible({ timeout: 30_000 });
  await expect(section.getByText("no un dato oficial", { exact: false }).first()).toBeVisible();
  const why = section.getByRole("heading", { name: "Por qué hoy" });
  const unavailable = section.getByText("no se muestran valores de sustitución", { exact: false });
  await expect(why.or(unavailable).first()).toBeVisible({ timeout: 60_000 });
  if (await why.isVisible()) {
    await section.locator("ol button[aria-pressed]").nth(1).click();
    await expect(section.locator("ol button[aria-pressed]").nth(1)).toHaveAttribute("aria-pressed", "true");
    await section.getByText("Ver método y fuentes de la estimación").click();
    await expect(section.getByText("no es una probabilidad de incendio", { exact: false }).or(section.getByText("No es una probabilidad de incendio", { exact: false })).first()).toBeVisible();
  }
});

test("meteorología: datos de AEMET o estado no disponible, nunca valores inventados", async ({ page }) => {
  await page.goto("/meteo");
  await expect(page.getByRole("heading", { name: "Viento y lluvia, hora a hora" })).toBeVisible();
  const charts = page.getByRole("img", { name: /Rachas y viento medio/ });
  const unavailable = page.getByText("No se muestran valores de sustitución", { exact: false });
  await expect(charts.or(unavailable).first()).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("no es un índice de peligro de incendio", { exact: false })).toBeVisible();
});
